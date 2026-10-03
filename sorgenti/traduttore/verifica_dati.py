"""I controlli sui dati.

Il glossario e' una base di dati che qualcuno riempie a mano, e una base di
dati riempita a mano si rovina in tre modi: con le voci duplicate, con le
voci senza fonte e con le voci che dicono una cosa e il glossario dice
un'altra. I controlli qui sotto cercanoono esattamente questi tre guasti e
nient'altro: non un controllo che puo' fallire per un motivo estetico.

Un controllo che segnala un problema che non c'e' e' peggio di nessun
controllo, perche' quando smette di essere credibile nessuno lo legge piu'.

**I controlli non correggono:** segnalano. La correzione la fa una persona,
perche' il glossario e' un fatto e i fatti non si correggono in automatico.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpora import TIPI
from .fonetica import ipa_valida
from .glossario import ATTENDIBILITA
from .varieta import VARIETA, _nome_valido, codice_valido


@dataclass
class Problema:
    codice: str
    dove: str
    messaggio: str
    gravita: str = "errore"  # `errore` o `avviso`

    def riga(self) -> str:
        marchio = "ERRORE" if self.gravita == "errore" else "avviso"
        return "[%s] %s %s - %s" % (marchio, self.codice, self.dove, self.messaggio)


def controlla_varieta(varieta) -> list:
    """Le cinque varieta' ci sono, sono cinque e sappiamo da dove vengono.

    Una tassonomia che perde una varieta' non perde una riga: perde la meta'
    del territorio. E' il controllo che rende impossibile dimenticare
    l'occidentale o il transpadano perche' nel frattempo il glossario si
    riempie di parole cittadine.
    """
    problemi = []
    visti = []
    for voce in varieta.voci:
        codice = voce.get("codice", "")
        dove = codice or "(senza codice)"
        if codice in visti:
            problemi.append(Problema("V1", dove, "varieta' dichiarata due volte"))
        visti.append(codice)
        if not codice_valido(codice):
            problemi.append(Problema(
                "V2", dove, "codice %r fuori dall'insieme %s"
                % (codice, ", ".join(VARIETA))))
            continue
        if not _nome_valido(voce.get("nome", "")):
            problemi.append(Problema(
                "V3", dove, "il nome %r non nomina nessuna delle cinque varieta'"
                % voce.get("nome", "")))
        if not voce.get("territori"):
            # Senza territorio la varieta' e' una parola. Non e' un errore da
            # cui non si possa uscire, ma e' un errore da non dimenticare.
            problemi.append(Problema(
                "V4", dove, "varieta' senza territorio: non si sa dove si parla",
                gravita="avviso"))
        if voce.get("attendibilita") == "D" and not voce.get("fonte"):
            problemi.append(Problema("V5", dove, "varieta' documentata senza fonte"))
    mancanti = [c for c in VARIETA if c not in visti]
    if mancanti:
        problemi.append(Problema(
            "V6", ", ".join(mancanti),
            "le varieta' assenti da dati/varieta.json: dichiarale anche vuote"))
    return problemi


def controlla_glossario(glossario) -> list:
    problemi = []
    visti = set()
    # Una voce senza la sua parte ferrarese o italiana non e' una voce: e' un
    # appunto. Si segnala e non si indice, perche' un indice con dentro una
    # voce a meta' fa tradurre cose a caso.
    for voce in glossario.voci:
        dove = voce.id or "(senza id)"
        if not voce.id:
            problemi.append(Problema("G1", dove, "voce senza id"))
        elif voce.id in visti:
            problemi.append(Problema("G2", dove, "id duplicato nel glossario"))
        visti.add(voce.id)

        if not voce.ferrarese or not voce.italiano:
            problemi.append(Problema(
                "G3", dove, "voce con un lato solo: %r / %r" % (voce.ferrarese, voce.italiano)))
            continue

        # Il controllo piu' importante del progetto: nessuna voce si dichiara
        # documentata se non dice da dove viene.
        if voce.attendibilita == "D" and not voce.fonte:
            problemi.append(Problema(
                "G4", dove,
                "attendibilita D senza fonte: o si mette la fonte, o "
                "l'attendibilita scende a I o M"))
        if voce.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "G5", dove, "attendibilita %r fuori dall'insieme %s"
                % (voce.attendibilita, ", ".join(ATTENDIBILITA))))
        if voce.fonte and len(voce.fonte) < 6:
            problemi.append(Problema(
                "G6", dove, "fonte troppo breve per essere controllabile: %r" % voce.fonte))
        # Una voce dichiarata `da verificare` che si dichiara anche `D` e' una
        # contraddizione: si sta affermando un fatto che non e' ancora stato
        # controllato. Non e' un errore che blocca, ma e' il tipo di errore che
        # si propaga di voce in voce e dopo venti passaggi sembra un fatto.
        if voce.da_verificare and voce.attendibilita == "D":
            problemi.append(Problema(
                "G7", dove,
                "voce non verificata ma dichiarata documentata: o si verifica, "
                "o l'attendibilita scende", gravita="avviso"))
        # La varieta' e' obbligatoria perche' una parola senza varieta' e' una
        # parola che non si sa a chi servire. Non e' un campo che si riempie
        # «per completezza»: e' quello che distingue una parola di Bondeno da
        # una parola che si dice anche a Ferrara.
        if not voce.varieta:
            problemi.append(Problema(
                "G8", dove,
                "voce senza varieta': dichiara in quale delle cinque vale "
                "(%s)" % ", ".join(VARIETA)))
        elif not codice_valido(voce.varieta):
            problemi.append(Problema(
                "G9", dove, "varieta' %r fuori dall'insieme %s"
                % (voce.varieta, ", ".join(VARIETA))))
    return problemi


def controlla_fonetica(fonetica, glossario, corpus, varieta=None) -> list:
    """Le trascrizioni IPA: quattro cose, e sono tutte verificabili.

    Una trascrizione e' un documento che si mette accanto a una parola e che
    qualcuno, magari fra vent'anni, leggerà per far dire a uno studente come
    si dice. Quindi deve dire **di cosa sta parlando** (F1), **come si
    scrive** (F2), **a chi si riferisce** (F4) e **quanto e' sicura** (F3).

    Il controllo F2 e' l'unico puramente meccanico, e serve a prendere la
    disattenzione piu' comune: mettere la parola italianaaccentata dentro il
    campo IPA e credere di aver trascritto qualcosa.
    """
    problemi = []
    visti = set()
    conosciute = {v.id for v in glossario.voci} | {c.id for c in corpus.coppie}
    coppie_varieta = {c.id: c.varieta for c in corpus.coppie}
    voci_varieta = {v.id: v.varieta for v in glossario.voci}
    for t in fonetica.trascrizioni:
        dove = t.id or "(senza id)"
        if not t.id:
            problemi.append(Problema("F1", dove, "trascrizione senza id"))
        elif t.id in visti:
            problemi.append(Problema("F2", dove, "id duplicato nelle trascrizioni"))
        visti.add(t.id)

        if not t.forma:
            problemi.append(Problema("F3", dove, "trascrizione senza la forma scritta"))
        if not t.ipa:
            problemi.append(Problema("F4", dove, "trascrizione senza IPA"))
        else:
            valida, sospetti = ipa_valida(t.ipa)
            if not valida:
                problemi.append(Problema(
                    "F5", dove,
                    "campi IPA con caratteri che non sono simboli IPA: %s. "
                    "Probabilmente la grafia rimessa al suo posto."
                    % " ".join(sospetti)))
        if not t.riferimento:
            problemi.append(Problema("F6", dove, "trascrizione senza riferimento"))
        elif t.riferimento not in conosciute:
            problemi.append(Problema(
                "F7", dove,
                "riferimento %r che non e' nel glossario ne' nel corpus: la "
                "trascrizione non descrive niente" % t.riferimento))
        if t.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "F8", dove, "attendibilita %r non valida" % t.attendibilita))
        if t.attendibilita == "D" and not t.fonte:
            problemi.append(Problema(
                "F9", dove,
                "trascrizione documentata senza fonte: per `D` la fonte deve "
                "dire chi ha ascoltato, dove e quando"))
        if t.da_verificare and t.attendibilita == "D":
            problemi.append(Problema(
                "F10", dove,
                "trascrizione non verificata ma dichiarata documentata",
                gravita="avviso"))
        if not codice_valido(t.varieta):
            problemi.append(Problema(
                "F11", dove, "varieta' %r fuori dall'insieme %s"
                % (t.varieta or "", ", ".join(VARIETA))))
        # La stessa parola in due varieta' ha due trascrizioni, e non una:
        # e' la ragione per cui questa tabella esiste.
        attesa = voci_varieta.get(t.riferimento) or coppie_varieta.get(t.riferimento)
        if attesa and t.varieta and attesa != t.varieta:
            problemi.append(Problema(
                "F12", dove,
                "trascrizione %s in varieta' %r, ma %s e' dichiarata %r"
                % (t.forma, t.varieta, t.riferimento, attesa), gravita="avviso"))
    # F13 cerca **due trascrizioni della stessa forma scritta**, non due
    # forme simili: `brisa` e `brisà` sono due scelte di scrittura e hanno
    # due suoni diversi, e non e' un conflitto. Il conflitto e' quando la
    # stessa scrittura ha due risposte, e allora bisogna sapere quale vale.
    per_forma = {}
    for t in fonetica.trascrizioni:
        chiave = (t.riferimento,
                  (t.forma or "").strip().lower().replace("'", "").replace("’", ""))
        per_forma.setdefault(chiave, []).append(t)
    for (riferimento, forma), trovate in per_forma.items():
        if len(trovate) > 1:
            problemi.append(Problema(
                "F13", riferimento or "(senza riferimento)",
                "la forma scritta %r ha %d trascrizioni (%s): due persone hanno "
                "scritto due suoni per la stessa scrittura, e va deciso quale "
                "dei due vale"
                % (trovate[0].forma, len(trovate),
                   ", ".join("%s %s" % (t.id, t.ipa) for t in trovate)),
                gravita="avviso"))
    if varieta is not None:
        problemi += _controlla_varieta_delle_trascrizioni(fonetica, glossario, varieta)
    return problemi


def _controlla_varieta_delle_trascrizioni(fonetica, glossario, varieta) -> list:
    """Le varieta' che hanno parole ma non suoni.

    E' il controllo che rende utile la parte audio: senza di esso si puo'
    avere un glossario con trenta parole e venti suoni e l'idea che si stia
    coprendo il territorio. In realta' una varieta' puo' avere parole e
    nessun suono, e quello e' un buco che va detto.

    Una varieta' **senza parole** non si segnala: e' un vuoto noto,
    dichiarato dalla tassonomia, e un controllo che segnala sempre e' un
    controllo che dopo tre settimane nessuno legge piu'.
    """
    problemi = []
    con_suono = {t.varieta for t in fonetica.trascrizioni}
    conteggi = varieta.conteggi(glossario=glossario)
    for codice in VARIETA:
        if codice in con_suono:
            continue
        if conteggi.get(codice, {}).get("glossario", 0) > 0:
            problemi.append(Problema(
                "F14", codice,
                "%d voci in questa varieta' e nessuna trascrizione: le parole ci "
                "sono, i suoni no" % conteggi[codice]["glossario"],
                gravita="avviso"))
    return problemi


def controlla_corpora(corpus) -> list:
    problemi = []
    visti = set()
    for coppia in corpus.coppie:
        dove = coppia.id or "(senza id)"
        if not coppia.id:
            problemi.append(Problema("C1", dove, "coppia senza id"))
        elif coppia.id in visti:
            problemi.append(Problema("C2", dove, "id duplicato nel corpus"))
        visti.add(coppia.id)

        if not coppia.ferrarese or not coppia.italiano:
            problemi.append(Problema("C3", dove, "coppia con un lato solo"))
            continue
        if not coppia.fonte:
            # Non e' un errore che blocca: e' un errore che isola. La coppia
            # resta nel file ma non entra nel motore, e `Corpus.coppie_valide`
            # fa gia' questo lavoro. Lo segnaliamo perche' il file e' la
            # promessa di una collezione e una voce senza fonte e' una promessa
            # non mantenuta.
            problemi.append(Problema(
                "C4", dove,
                "coppia senza fonte: resta nel file ma il motore non la usa",
                gravita="avviso"))
        if coppia.tipo not in TIPI:
            problemi.append(Problema(
                "C5", dove, "tipo %r fuori dall'insieme %s" % (coppia.tipo, ", ".join(TIPI))))
        if coppia.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "C6", dove, "attendibilita %r non valida" % coppia.attendibilita))
        if not coppia.varieta:
            problemi.append(Problema(
                "C7", dove,
                "coppia senza varieta': una frase raccolta fuori citta' insegnerebbe "
                "il dialetto di un posto solo a chi e' di un altro"))
        elif not codice_valido(coppia.varieta):
            problemi.append(Problema(
                "C8", dove, "varieta' %r fuori dall'insieme %s"
                % (coppia.varieta, ", ".join(VARIETA))))
    for proverbio in corpus.proverbi:
        dove = proverbio.id or "(senza id)"
        if not proverbio.id:
            problemi.append(Problema("P1", dove, "proverbio senza id"))
        if not proverbio.italiano:
            problemi.append(Problema("P2", dove, "proverbio senza il lato italiano"))
        if not proverbio.ferrarese and not proverbio.popolare:
            problemi.append(Problema(
                "P3", dove, "proverbio senza forma ferrarese: due lati vuoti"))
        if proverbio.ferrarese and proverbio.popolare and proverbio.ferrarese == proverbio.popolare:
            problemi.append(Problema(
                "P4", dove,
                "forma letteraria e popolare uguali: o una delle due e' messa a "
                "torto, o il campo letterario e' inutile qui"))
        if proverbio.attendibilita == "D" and not proverbio.fonte:
            problemi.append(Problema("P5", dove, "proverbio documentato senza fonte"))
    return problemi


def controlla_regole(regole, soglia: float = 0.70) -> list:
    problemi = []
    for regola in regole:
        if regola.accordo < soglia:
            problemi.append(Problema(
                "R1", regola.etichetta(),
                "accordo %0.2f sotto la soglia %0.2f: questa regola non dovrebbe "
                "esistere" % (regola.accordo, soglia), gravita="avviso"))
        if regola.supporto < 2:
            problemi.append(Problema(
                "R2", regola.etichetta(),
                "un solo esempio: non e' una regola, e' un caso"))
    return problemi


def riepilogo(problemi: list) -> dict:
    errori = [p for p in problemi if p.gravita == "errore"]
    return {
        "errori": len(errori),
        "avvisi": len(problemi) - len(errori),
        "ok": not errori,
    }