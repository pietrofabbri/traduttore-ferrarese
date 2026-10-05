"""Il motore: quattro livelli, e una-fifth che non risponde.

Il percorso di una parola attraverso il motore e' sempre lo stesso, e va
dichiarato perche' e' la parte che rende il risultato leggibile:

1. **glossario** - la voce c'e', la risposta e' quella e si ferma li';
2. **corpo** - il corpus parallelo ha la frase o un pezzo di frase;
3. **regola** - una regola morfologica imparata produce qualcosa;
4. **modello** - l'IA ha risposto, con il glossario e il corpus nel contesto.

E poi c'e' il quinto caso, che e' il piu' importante: **non so**. Quando
nessuno dei quattro arriva a una confidenza sufficiente, il motore non
tira a indovinare: restituisce la parola di partenza e lo dichiara. E'
la stessa regola che vale in «I cinque duchi» per un vuoto, ed e' l'unica
regola che rende affidabile un traduttore di una lingua che sta morendo:
una lingua piccola non si puo' tradurre inventando, si puo' solo tradurre
dentro un perimetro dichiarato.

Ogni risposta porta con se' quattro cose: il testo tradotto, da dove viene
(`origine`), quanto si e' sicuri (`confidenza`, da 0 a 1) e che cosa non si
sa (`buchi`). Il testo da solo non basta: chi legge deve poter sapere se
quella riga gliela puo' dare a uno studente.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import italiano, morfologia, normalizza, pronominali, verbi
from .glossario import IT_FE

# Le quattro origini, e la confidenza che portano con se'.
ORIGINE = {
    "glossario": 0.95,
    # `corpo` e' il frammento dentro una coppia simile: senza il contesto che
    # circonda la parola, il frammento e' un pezzo staccato e vale meno della
    # voce di un dizionario.
    "corpo": 0.80,
    # `corpo_frase` e' la frase intera, trovata identica. E' il caso forte del
    # livello 2 e puo' superare la soglia di pubblicazione, ma solo se la
    # coppia che la contiene e' dichiarata documentata con una fonte: una
    # frase intera che qualcuno ha scritto a memoria non vale piu' di un
    # frammento.
    "corpo_frase": 0.92,
    # `verbo` e' una forma verbale coniugata che una fonte scrive per iscritto.
    # Vale meno di una voce di dizionario, perche' copre una persona sola e non
    # la parola, e vale piu' di una regola imparata, perche' qualcuno l'ha
    # scritta: e' un'attestazione, non un calcolo.
    "verbo": 0.75,
    "regola": 0.55,
    "modello": 0.50,
    "nessuna": 0.0,
}

# Sopra questa confidenza il motore mostra la risposta senza avvisi.
# Sotto, la mostra con l'avviso. Sopra il `rifiuto`, non la mostra affatto.
SOGLIA_PULITA = 0.90
SOGLIA_RIFIUTO = 0.50

# Quanto lunga puo' essere una locuzione che il glossario riconosce tutta
# insieme. Sei parole e' il massimo reale del glossario attuale: la piu'
# lunga, «esser tr al lancùzan el martèl», ne ha cinque, e il numero e'
# dichiarato perche' un limite piu' alto costa un confronto in piu' per ogni
# parola di ogni frase, e un limite piu' basso lascerebbe fuori delle voci
# che ci sono.
LUNGHEZZA_MAX_LOCUZIONE = 6


@dataclass
class Risposta:
    """Il risultato di una traduzione, per un certo testo."""

    testo_originale: str
    testo: str
    direzione: str
    # `per_corrispondenza` e' la lista di (originale, tradotto, origine,
    # confidenza, dettaglio). E' la traccia completa: senza di lei non si puo'
    # controllare niente.
    per_corrispondenza: list = field(default_factory=list)
    # `buchi` e' la lista di cio' che il motore non ha tradotto.
    buchi: list = field(default_factory=list)

    @property
    def confidenza(self) -> float:
        """Confidenza media, pesata per lunghezza. Una parola corta conta
        quanto una lunga: in una lingua che scrive stretto, sbagliare
        `ghe` e' grave quanto sbagliare `amministrazione`."""
        if not self.per_corrispondenza:
            return 0.0
        totale = 0.0
        peso = 0
        for originale, tradotto, origine, confidenza, _ in self.per_corrispondenza:
            n = max(1, len(normalizza.chiave(originale)))
            totale += confidenza * n
            peso += n
        return totale / peso if peso else 0.0

    @property
    def da_pubblicare(self) -> bool:
        """Il gioco usa questo risultato cosi' com'e', o no."""
        return not self.buchi and self.confidenza >= SOGLIA_PULITA

    def spiega(self) -> str:
        righe = ["%s -> %s  [%s %0.2f]%s" % (
            originale, tradotto, origine, confidenza,
            ("  " + dettaglio) if dettaglio else "",
        ) for originale, tradotto, origine, confidenza, dettaglio in self.per_corrispondenza]
        if self.buchi:
            righe.append("buchi: " + ", ".join(self.buchi))
        righe.append("confidenza media %0.2f - %s" % (
            self.confidenza, "pubblicabile" if self.da_pubblicare else "da rivedere"))
        return "\n".join(righe)

    def come_json(self) -> dict:
        return {
            "originale": self.testo_originale,
            "traduzione": self.testo,
            "direzione": self.direzione,
            "confidenza": round(self.confidenza, 3),
            "pubblicabile": self.da_pubblicare,
            "corrispondenze": [
                {"originale": o, "traduzione": t, "origine": g,
                 "confidenza": round(c, 3), "dettaglio": d}
                for o, t, g, c, d in self.per_corrispondenza
            ],
            "buchi": self.buchi,
        }


class Motore:
    """Il traduttore. Non ha stato proprio: e' una funzione dei dati."""

    def __init__(self, glossario, corpus, regole=None, modello=None,
                 soglia_rifiuto: float = SOGLIA_RIFIUTO, italiano_analisi=None):
        self.glossario = glossario
        self.corpus = corpus
        self.regole = regole or []
        # L'analizzatore grammaticale dell'italiano. Senza di lui il livello 3
        # lavora come ha sempre lavorato, per desinenza; con lui una regola
        # vale solo per la classe che dichiara. `None` non e' un difetto: e' il
        # modo in cui il motore si costruisce quando non gli si e' passato
        # l'analizzatore, e i test lo costruiscono cosi' apposta.
        self.italiano = italiano_analisi
        # `modello` e' un oggetto con un metodo `traduci(richiesta)`. Se e'
        # None il livello 4 non esiste e il motore si ferma al terzo.
        self.modello = modello
        self.soglia_rifiuto = soglia_rifiuto

    def traduci(self, testo: str, direzione: str = IT_FE) -> Risposta:
        testo = (testo or "").strip()
        if not testo:
            return Risposta("", "", direzione)
        token = normalizza.tokenizza(testo)
        if not token:
            return Risposta(testo, testo, direzione, buchi=[testo])

        # Una frase che il corpus contiene per intero non viene smembrata
        # parola per parola: si restituisce come e' stata trovata. E' il caso
        # forte del livello 2, e smembrarla produrrebbe una traduzione piu'
        # incerta di quella che si aveva gia' in mano.
        gemella = self.corpus.frase_gemella(testo, direzione)
        if gemella is not None:
            tradotto = gemella.ferrarese if direzione == IT_FE else gemella.italiano
            dettaglio = "frase intera dal corpus, %s: %s" % (
                gemella.id, gemella.fonte or "senza fonte")
            confidenza = ORIGINE["corpo_frase"] if (
                gemella.fonte and gemella.attendibilita == "D") else ORIGINE["corpo"]
            corrispondenze = [(testo, tradotto, "corpo", confidenza, dettaglio)]
            return Risposta(testo, tradotto, direzione, corrispondenze, [])

        corrispondenze = self._risolvi_token(token, direzione)
        tradotto = " ".join(t for _, t, _, _, _ in corrispondenze)
        # Il buco e' la parola che resta senza risposta: o il motore non ha
        # trovato nulla, o il modello ha risposto sotto soglia. Una risposta
        # da rivedere resta nel testo, ma non e' pubblicabile.
        buchi = [
            t for _, t, origine, _, _ in corrispondenze
            if origine == "nessuna" or origine == "modello"
        ]
        # Il buco dei verbi e' **uno solo per traduzione** e non uno per parola:
        # dodici parole non tradotte danno dodici frasi uguali, e un elenco di
        # frasi uguali nasconde l'unica informazione che serve, che e' «quante
        # forme e su quanti verbi stanno scritte, e quali caselle mancano».
        if direzione == IT_FE and buchi:
            spiegazione = verbi.spiega_buco(buchi[0])
            if spiegazione:
                buchi = buchi + [spiegazione]
        return Risposta(testo, tradotto, direzione, corrispondenze, buchi)

    # --- i quattro livelli ------------------------------------------------

    def _risolvi_token(self, token: list, direzione: str) -> list:
        """Risolve ogni token, nell'ordine dei quattro livelli.

        L'ordine e' quello che conta: si parte dalla fonte piu' forte e si
        scende, e si smette al primo livello che risponde. Il livello 4 e'
        costoso e fallibile, quindi non lo si usa mai quando gli altri tre
        hanno gia' detto.

        Prima di tutto pero' si accorpa: il glossario contiene locuzioni
        («a brazz avèrti» e' una voce sola, non tre), e smembrarle farebbe
        peggio di non tradurre. Il passaggio e' avido — prova la frase piu'
        lunga e, se il glossario non la conosce, accorcia di una parola — e
        questa e' la stessa cosa che fa chi legge il vocabolario: cerca
        l'espressione intera prima delle parole che la compongono.
        """
        risultati = []
        # Il contesto di frase serve al livello 2 e al 4: e' la frase intera,
        # non il token, e per questo si calcola una volta sola.
        frase = " ".join(token)
        contesto = self._contesto_modello(frase, direzione)
        i = 0
        while i < len(token):
            # Prima di ogni accorpamento c'e' quello dei **verbi pronominali**,
            # perche' e' l'unico accorpamento che il motore fa e che il
            # glossario non contiene: «si» non e' una parola e quindi cercarla
            # nel glossario dava `oj`, una risposta vera e sbagliata. La
            # particella viene attaccata al verbo e l'unita' va a `risolvi()`
            # come una sola cosa.
            pronominale = (pronominali.unita(token, i)
                           if direzione == IT_FE else None)
            if pronominale is not None:
                testo, quante = pronominale
                esito = pronominali.buco(testo)
                risultati.append((testo, esito["testo"], esito["origine"],
                                  esito["confidenza"], esito["dettaglio"]))
                i += quante
                continue
            accorpata = self._accorpa(token, i, direzione)
            if accorpata is not None:
                testo, quante = accorpata
                tradotto, origine, confidenza, dettaglio = self._risolvi_una(
                    testo, frase, direzione, contesto)
                risultati.append((testo, tradotto, origine, confidenza, dettaglio))
                i += quante
                continue
            parola = token[i]
            tradotto, origine, confidenza, dettaglio = self._risolvi_una(
                parola, frase, direzione, contesto)
            risultati.append((parola, tradotto, origine, confidenza, dettaglio))
            i += 1
        return risultati

    def _accorpa(self, token: list, i: int, direzione: str):
        """La locuzione piu' lunga che comincia in `token[i]`, se c'e'.

        Torna `(testo, quante_parole)` o `None`. Una parola sola non e' mai
        un accorpamento: sotto i due token si comincia al livello 1 normale,
        che e' gia' il caso piu' forte.
        """
        for quante in range(min(LUNGHEZZA_MAX_LOCUZIONE, len(token) - i), 1, -1):
            testo = " ".join(token[i:i + quante])
            if self.glossario.cerca(testo, direzione):
                return testo, quante
        return None

    def _risolvi_una(self, parola: str, frase: str, direzione: str, contesto) -> tuple:
        """Risolve un token e restituisce (tradotto, origine, confidenza, dettaglio)."""

        # Livello 1: il glossario. Vince sempre.
        voci = self.glossario.cerca(parola, direzione)
        if voci:
            voce = voci[0]
            tradotto = voce.principale(direzione)
            dettaglio = "%s (%s) %s" % (
                voce.id, voce.attendibilita, voce.fonte or "senza fonte")
            if voce.varieta:
                dettaglio += " | varieta': %s" % voce.varieta
            if len(voci) > 1:
                dettaglio += " | altre voci: " + ", ".join(v.id for v in voci[1:4])
            return tradotto, "glossario", ORIGINE["glossario"], dettaglio

        # Livello 2: il corpus parallelo. Prima la frase gemella, che e' il
        # caso forte, poi il frammento dentro una coppia simile.
        gemella = self.corpus.frase_gemella(frase, direzione)
        if gemella is not None:
            tradotto = gemella.ferrarese if direzione == IT_FE else gemella.italiano
            dettaglio = "frase intera, %s: %s" % (
                gemella.id, gemella.fonte or "senza fonte")
            confidenza = ORIGINE["corpo_frase"] if (
                gemella.fonte and gemella.attendibilita == "D") else ORIGINE["corpo"]
            return tradotto, "corpo", confidenza, dettaglio

        cercate = self.corpus.corrispondenze(parola, direzione, soglia=0.62)
        if cercate:
            punteggio, coppia = cercate[0]
            pezzo = self.corpus.frammento(coppia, parola, direzione)
            if pezzo is not None:
                frammento, punteggio_pezzo = pezzo
                confidenza = ORIGINE["corpo"] * min(1.0, punteggio_pezzo + 0.15)
                dettaglio = "%s, frammento %r: %s" % (
                    coppia.id, frammento, coppia.fonte or "senza fonte")
                return frammento, "corpo", confidenza, dettaglio
            # La coppia somiglia ma nessun suo pezzo combacia con questa parola:
            # la coppia e' un esempio, non una traduzione. Si dice, e si passa
            # oltre. E' il punto in cui molti traduttori sbagliano e restituiscono
            # la frase intera al posto della parola.

        # Livello 3: le regole morfologiche imparate.
        regola, prodotto = morfologia.spiega(parola, self.regole, direzione,
                                              self.italiano)
        if regola is not None:
            confidenza = ORIGINE["regola"] * regola.accordo
            dettaglio = "%s (%d esempi, accordo %0.2f)" % (
                regola.etichetta(), regola.supporto, regola.accordo)
            if confidenza >= self.soglia_rifiuto:
                return prodotto, "regola", confidenza, dettaglio

        # Livello 3 bis: le forme verbali attestate. Sta **prima** del modello
        # perche' e' una fonte e il modello e' un calcolo, e **dopo** le regole
        # imparate perche' una regola che ha visto venti esempi non vale meno di
        # una forma che qualcuno ha scritto una volta sola.
        #
        # Il verso e' uno solo: si cerca dall'italiano al ferrarese. Dall'altra
        # parte la domanda sarebbe «quale forma ferrarese e' questa?», e per
        # rispondere servirebbe riconoscere la forma, che e' esattamente cio'
        # che le fonti non documentano.
        if direzione == IT_FE:
            attestata = verbi.dall_italiano(parola)
            if attestata["forma"]:
                dettaglio = "forma attestata da %s: %s" % (
                    attestata["fonte"], attestata["nota"] or "senza nota")
                return (attestata["forma"], "verbo", ORIGINE["verbo"], dettaglio)

        # Livello 4: il modello, solo se c'e' e solo se non ha gia' risposto
        # nessuno dei precedenti.
        if self.modello is not None:
            risposta_modello = self.modello.traduci(parola, direzione, contesto)
            if risposta_modello and risposta_modello.get("traduzione"):
                confidenza = ORIGINE["modello"] * float(
                    risposta_modello.get("confidenza", 0.5))
                dettaglio = risposta_modello.get("dettaglio", "")
                if confidenza >= self.soglia_rifiuto:
                    return risposta_modello["traduzione"], "modello", confidenza, dettaglio
                # Sotto soglia il motore **non indovina**: restituisce la
                # parola di partenza e registra il buco.
                return parola, "nessuna", 0.0, "modello sotto soglia: %s" % dettaglio

        # Livello 5: non so.
        return parola, "nessuna", 0.0, "nessuna fonte nel glossario, nel corpus o fra le regole"

    def _contesto_modello(self, frase: str, direzione: str) -> dict:
        """Costruisce il contesto che si da' al modello: glossario vicino,
        coppie simili, e le regole disponibili.

        Il contesto e' tutto locale. Un modello che riceve mezzo glossario e
        un paio di frasi vere puo' sbagliare; un modello che riceve tutto il
        glossario e non riceve nessuna fonte puo' peggiorare.
        """
        vicine = self.glossario.vicine(frase, direzione, soglia=0.6, limite=6)
        coppie = self.corpus.cerca(frase, direzione, soglia=0.45, limite=4)
        return {
            "glossario": [
                {"italiano": v.italiano, "ferrarese": v.ferrarese,
                 "varianti": v.varianti, "attendibilita": v.attendibilita}
                for _, v in vicine
            ],
            "coppie": [
                {"italiano": c.italiano, "ferrarese": c.ferrarese, "fonte": c.fonte}
                for _, c in coppie
            ],
            "regole": [r.etichetta() for r in self.regole[:12]],
        }

    # --- interrogazioni di stato -----------------------------------------

    def cosa_sa(self) -> dict:
        """Che cosa sa il motore, in numeri. Serve al pannello del gioco."""
        return {
            "voci_glossario": len(self.glossario),
            "coppie": len(self.corpus.coppie_valide()),
            "coppie_senza_fonte": sum(1 for c in self.corpus.coppie if not c.valida()),
            "proverbi": len(self.corpus.proverbi),
            "regole": len(self.regole),
            # Le varieta' coperte: un numero solo che dica «tutte le voci» mente
            # per omissione, perche' nasconde che sono tutte di un posto solo.
            "varieta_coperte": ", ".join(sorted({v.varieta for v in self.glossario.voci if v.varieta})),
            "con_modello": self.modello is not None,
        }