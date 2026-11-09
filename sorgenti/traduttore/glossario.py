"""Il glossario: le voci che il traduttore conosce gia'.

Un glossario non e' un elenco di parole. Ogni voce porta con se' da dove
arriva, quanto e' sicura, e in quali condizioni vale. Una voce senza fonte
non entra: e' il principio che gia' vale per «I cinque duchi» e vale qui
perche' il rischio e' identico, solo che l'errore non si vede a occhio.

I tipi di attendibilita' sono gli stessi del gioco:

- ``D`` documentato   - cito una fonte che si puo' aprire e controllare
- ``I`` interpretato  - la ricavo da un contesto, ma non c'e' la fonte
- ``M`` memoria       - la so, ma nessuno l'ha messa per iscritto
- ``L`` leggenda      - forma proverbiale, non lessicale
- ``C`` collettivo    - risposta condivisa da piu' informatori

La regola che il codice fa rispettare e' che il valore ` attendibilita`
non puo' essere `D` senza una fonte che nomini un archivio o un libro. Non e'
una convinzione: e' un controllo in `verifica_dati`.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field

from . import grafia, normalizza
from .varieta import codice_valido

ATTENDIBILITA = ("D", "I", "M", "L", "C")

# Direzioni supportate.
IT_FE = "it-fe"
FE_IT = "fe-it"


@dataclass
class Voce:
    """Una voce del glossario."""

    id: str
    ferrarese: str
    italiano: str
    # Le varianti sono forme che la stessa fonte scrive in modo diverso.
    # Non sono errori: sono la norma in una lingua senza ortografia codificata.
    varianti: list = field(default_factory=list)
    # `campo` e' la categoria funzionale, quando la voce e' una parola
    # funzionale. Serve al traduttore per non scambiare un pronome con un
    # avverbio solo perche' suonano vicini.
    campo: str = ""
    # `varieta` dice in quale delle cinque varieta' del ferrarese la voce e'
    # attestata. Non e' un dettaglio: una parola di Bondeno data a uno
    # studente di Ferrara citta' e' una parola sbagliata, e senza questo campo
    # non c'e' modo di accorgersene. Percio' e' obbligatoria e il controllo G8
    # la chiede. Se una voce vale in piu' varieta' la si mette due volte, con
    # due id e due note: un glossario che finge che una parola sia di un posto
    # solo e' peggio di uno che non ce l'ha.
    varieta: str = ""
    # `note` e' il posto dove finisce tutto cio' che non sta in nessun
    # altro campo: il dubbio, il contraffatto, il doppio uso.
    note: str = ""
    # I due campi `principale_*` sono la forma singola da usare in una frase,
    # quando `italiano` o `ferrarese` contengono piu' resi separati da virgola.
    principale_italiano: str = ""
    principale_ferrarese: str = ""
    fonte: str = ""
    attendibilita: str = "M"
    # `registro` dichiara se una variante e' popolare, arcaica o ironica.
    # Serve al gioco, che lavora con adolescenti: una voce ironica etichettata
    # solo come "variante" arriva in bocca come se fosse neutra.
    registro: str = ""
    # `da_verificare` e' il campo che rende onesto il file di partenza. Una
    # voce appena raccolta e non ancora controllata su un vocabolario
    # stampato lo dichiara, e il motore la tratta come voce di seconda.
    da_verificare: bool = False
    # `moderno` e' il significato che la parola ha in italiano di oggi, preso
    # da una fonte dichiarata e non scritto di testa. Serve perche' una voce
    # come «ardiglione» arriva a uno studente con un italiano che non usa piu'
    # e che lui non puo' indovinare. Il campo e' vuoto quando la fonte non ha
    # l'articolo: e' un buco dichiarato, non un campo da riempire a piacere.
    # `sinonimi` e' l'alternativa, quando la fonte la dà. I due campi non si
    # escludono: spesso il significato e' chiaro e i sinonimi aiutano.
    #
    # `sinonimi` e' una lista come `varianti`, perche' la fonte ne dà dieci e
    # uno studente ne legge tre. Tutti e dieci restano nel file, dove sono il
    # dato; la colonna ne mostra tre e **dichiara** il taglio, perche' una
    # colonna che mostra tre pezzi senza dire che sono tre sembra mostrare
    # tutti.
    #
    # `moderno` porta **sempre** con se' `fonte_moderno`, l'indirizzo
    # dell'articolo da cui e' stato preso. Una riga con il significato e
    # senza la fonte non entra: e' il controllo G10, e senza di esso questa
    # sarebbe l'unica colonna del progetto che puo' inventare.
    moderno: str = ""
    fonte_moderno: str = ""
    sinonimi: list = field(default_factory=list)
    # L'id della voce che questa corregge: la scrive `correzioni applica`
    # quando un parlante corregge una voce. La voce corretta resta (e' quello
    # che la fonte scrive), e questa viene prima di lei in ogni ricerca.
    corregge: str = ""
    # La forma come la scrive la fonte, quando non e' quella che si legge
    # (0.42): le voci di Bigoni sono scritte nel suo alfabeto fonetico e il
    # glossario le legge all'italiana (`grafia.py`). Questa resta, si cerca e
    # da' la pronuncia.
    grafia_fonte: str = ""
    # Le voci di **altre fonti** che danno la stessa parola con lo stesso
    # significato (0.45, `_conferme`). Non e' un dato del file: si calcola
    # quando il glossario si legge, e cambia quando entra una fonte.
    conferme: list = field(default_factory=list)
    # La verifica di un parlante (0.46): «data, chi (fonte, varieta')», e la
    # riga che la registra e' in `dati/verifiche/verifiche.jsonl`.
    verificata: str = ""
    # L'alfabeto di `grafia_fonte` quando non e' quello di Bigoni: "treb" per
    # il Tréb dal Tridèl (0.47). Serve alla pagina per la pronuncia.
    alfabeto: str = ""

    def _chiavi_resi(self, testo: str, principale: str) -> list:
        """Le chiavi con cui una voce si trova cercando una delle sue forme.

        Una voce puo' avere piu' resi separati da virgola: «Maledire,
        esacràre», «con calma, senza fretta». Indicizzando solo l'intero
        campo, chi scrive «maledire» non trova niente e la voce che il libro
        scrive e' proprio quella che serviva. Percio' ogni resi e' una chiave
        sua, piu' `principale` quando c'e'.

        Si divide su virgola e punto e virgola, **non sugli spazi**:
        «con calma, senza fretta» deve trovarsi con «con calma» e con
        «senza fretta», ma non con «calma» da sola, che e' un'altra voce
        (V0025) e che perderebbe il suo contesto.

        Il testo intero resta una chiave sua: chi incolla dal libro la voce
        per come e' scritta, cioe' «con calma, senza fretta», deve trovarla.
        Dividere i pezzi senza lasciare la frase intera e' il modo di
        perdere la voce esattamente dove si cerca di ritrovarla.

        I pezzi vuoti si scartano e i duplicati si eliminano: la stessa voce
        non deve occupare due volte lo stesso slot dell'indice.

        **Un pezzo di una lettera sola non e' un resi** (0.38). Nel Ferri la
        virgola separa anche la desinenza: «Trincato, e» vuol dire «trincato,
        trincate», e la «e» diventava una chiave, cosi' ogni congiunzione «e»
        si traduceva `Trinca`. Le altre nove voci con un pezzo di una lettera
        sono sporcizia dell'OCR («Inaugurare, I», «Bastòn: t, di
        calligrafia»). Il campo intero resta una chiave, quindi una voce il cui
        italiano e' davvero una lettera sola si trova lo stesso.
        """
        pezzi = []
        if (testo or "").strip():
            pezzi.append(testo.strip())
        pezzi += [p.strip() for p in re.split(r"[,;]", testo or "")
                  if len(normalizza.chiave(p)) > 1]
        if (principale or "").strip():
            pezzi.append(principale.strip())
        chiavi = []
        for pezzo in pezzi:
            k = normalizza.chiave(pezzo)
            if k and k not in chiavi:
                chiavi.append(k)
        return chiavi

    def chiavi_ferrarese(self) -> list:
        # I pezzi del lato ferrarese vengono dai `varianti` dichiarati a mano
        # e dai resi multipli: stesso ragionamento del lato italiano.
        chiavi = self._chiavi_resi(self.ferrarese, self.principale_ferrarese)
        if self.grafia_fonte:
            for k in self._chiavi_resi(self.grafia_fonte, ""):
                if k not in chiavi:
                    chiavi.append(k)
        for v in self.varianti:
            k = normalizza.chiave(v)
            if k and k not in chiavi:
                chiavi.append(k)
        return chiavi

    def chiavi_italiano(self) -> list:
        return self._chiavi_resi(self.italiano, self.principale_italiano)

    def varieta_valida(self) -> bool:
        return codice_valido(self.varieta)

    def principale(self, direzione: str) -> str:
        """La forma singola da mettere nel testo tradotto.

        Una voce puo' avere piu' resi: «ci (particella enclitica)», «niente,
        nulla». Queste sono **glosse per chi cerca**, non traduzioni da usare
        in una frase: rimetterle nel testo tradotto produce «an ghe niente,
        nulla pane», che non e' italiano e non e' ferrarese. Per questo i due
        campi `principale_*` esistono, e quando mancano si cade sul lato della
        voce, che e' la scelta giusta solo se la voce ha un reso solo.
        """
        if direzione == "it-fe":
            return self.principale_ferrarese or self.ferrarese
        return self.principale_italiano or self.italiano


class Glossario:
    """Le voci del glossario, indicizzate per direzione."""

    def __init__(self, voci=None):
        self.voci = _prima_le_correzioni(list(voci or []))
        _senza_maiuscole_del_lemma(self.voci)
        _conferme(self.voci)
        self._per_ferrarese = {}
        self._per_italiano = {}
        self.indizza()

    # --- costruzione -----------------------------------------------------

    @classmethod
    def da_file(cls, percorso: str) -> "Glossario":
        estensione = os.path.splitext(percorso)[1].lower()
        if estensione == ".jsonl":
            voci = []
            with open(percorso, "r", encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if riga and not riga.startswith("//"):
                        voci.append(_voce_da_dict(json.loads(riga)))
            return cls(voci)
        if estensione == ".csv":
            voci = []
            with open(percorso, "r", encoding="utf-8", newline="") as f:
                for riga in csv.DictReader(f):
                    voci.append(_voce_da_dict(dict(riga)))
            return cls(voci)
        if estensione == ".json":
            with open(percorso, "r", encoding="utf-8") as f:
                grezzo = json.load(f)
            return cls([_voce_da_dict(v) for v in grezzo.get("voci", grezzo)])
        raise ValueError("Formato glossario non riconosciuto: %s" % percorso)

    def indizza(self) -> None:
        self._per_ferrarese = {}
        self._per_italiano = {}
        for voce in self.voci:
            for k in voce.chiavi_ferrarese():
                if k:
                    self._per_ferrarese.setdefault(k, []).append(voce)
            for k in voce.chiavi_italiano():
                if k:
                    self._per_italiano.setdefault(k, []).append(voce)
        # Dentro ogni chiave, prima le correzioni dei parlanti e poi le voci
        # confermate da piu' fonti (0.45). L'ordinamento e' stabile: a parita'
        # resta l'ordine del file, che e' quello di prima.
        for indice in (self._per_ferrarese, self._per_italiano):
            for chiave_indice, gruppo in indice.items():
                if len(gruppo) > 1:
                    indice[chiave_indice] = sorted(gruppo, key=priorita)

    # --- interrogazioni --------------------------------------------------

    def __len__(self) -> int:
        return len(self.voci)

    def cerca_ferrarese(self, forma: str) -> list:
        """Voci che hanno questa forma ferrarese, esatta o per chiave.

        Deduplicato per id: una voce che si raggiunge sia per la forma
        principale sia per una variante che si normalizza allo stesso modo
        («brisà» e «brisa») compare una volta sola, altrimenti il motore
        annuncerebbe «altre voci» che sono la stessa voce che ha gia' risposto.
        """
        return _uniche_per_id(self._per_ferrarese.get(normalizza.chiave(forma), []))

    def cerca_italiano(self, forma: str) -> list:
        return list(self._per_italiano.get(normalizza.chiave(forma), []))

    def cerca(self, forma: str, direzione: str = IT_FE) -> list:
        if direzione == IT_FE:
            return self.cerca_italiano(forma)
        return self.cerca_ferrarese(forma)

    def vicine(self, forma: str, direzione: str = IT_FE, soglia: float = 0.72,
               limite: int = 8) -> list:
        """Voci vicine ma non identiche, per la ricerca di una parola che
        il glossario non ha ancora.

        La soglia e' alta di proposito. Una corrispondenza sbagliata data
        per buona e' peggio di un vuoto dichiarato, e un vuoto dichiarato
        si vede.
        """
        risultati = []
        k = normalizza.chiave(forma)
        if not k:
            return risultati
        indice = self._per_italiano if direzione == IT_FE else self._per_ferrarese
        for k_indice, voci in indice.items():
            punteggio = normalizza.somiglianza(k, k_indice)
            if punteggio >= soglia:
                for voce in voci:
                    risultati.append((punteggio, voce))
        risultati.sort(key=lambda p: (-p[0], p[1].id))
        # Una voce con piu' forme equivalenti non deve occupare piu' slot.
        visti = set()
        uniche = []
        for punteggio, voce in risultati:
            if voce.id in visti:
                continue
            visti.add(voce.id)
            uniche.append((punteggio, voce))
            if len(uniche) >= limite:
                break
        return uniche

    def per_id(self, identificatore: str):
        for voce in self.voci:
            if voce.id == identificatore:
                return voce
        return None


def _prima_le_correzioni(voci: list) -> list:
    """Le voci nell'ordine del file, con ogni correzione subito prima della
    voce che corregge.

    L'ordine e' quello che decide quale voce risponde quando piu' voci hanno
    la stessa parola, e una correzione di un parlante viene scritta in fondo
    al file. Spostarla qui, e non nell'indice, fa si' che la pagina — che
    riceve le voci in questo stesso ordine — risponda come il motore senza
    una seconda copia della regola.
    """
    presenti = {v.id for v in voci}
    correzioni = {}
    for voce in voci:
        if voce.corregge and voce.corregge in presenti and \
                voce.corregge != voce.id:
            correzioni.setdefault(voce.corregge, []).append(voce)
    if not correzioni:
        return voci
    spostate = {id(v) for gruppo in correzioni.values() for v in gruppo}
    ordinate = []
    for voce in voci:
        if id(voce) in spostate:
            continue
        ordinate.extend(correzioni.get(voce.id, []))
        ordinate.append(voce)
    return ordinate


def _uniche_per_id(voci: list) -> list:
    visti = set()
    uniche = []
    for voce in voci:
        if voce.id in visti:
            continue
        visti.add(voce.id)
        uniche.append(voce)
    return uniche


# --- la conferma fra fonti (0.45) --------------------------------------------
#
# Quando due fonti indipendenti — il Nannini (1805), il Ferri (1889), Bigoni,
# Musacchi — danno per la stessa parola italiana la stessa forma ferrarese, la
# voce non e' piu' la lettura di una fonte sola. Non diventa `D`: nessuno l'ha
# confrontata col libro. Ma fra due voci per «aiutare» quella che tre fonti
# confermano e' quella da dare, e il motore la mette prima.
#
# Il confronto e' severo: la forma deve essere **uguale** dopo la grafia unica
# (`grafia.py`), a meno degli accenti, delle consonanti doppie e di j/i
# (`Biànch` e `bianch`, `Ajùt` e `aiut`). Due forme solo simili non si
# confermano: e' il caso in cui una delle due e' una lettura sbagliata.

def famiglia_della_fonte(fonte: str) -> str:
    """La fonte di una voce, come identificativo: `S004`, `S006`..."""
    m = re.search(r"\((S\d{3})\)", fonte or "")
    if m:
        return m.group(1)
    for inizio, codice in (("Luigi Ferri", "S004"), ("Francesco Nannini", "S005"),
                           ("Roberto Bigoni", "S006"),
                           ("Maurizio Musacchi", "S020")):
        if (fonte or "").startswith(inizio):
            return codice
    return (fonte or "")[:40]


def forma_confrontabile(forma: str) -> str:
    k = normalizza.chiave(forma or "").replace("j", "i").replace("h", "")
    return re.sub(r"(.)\1+", r"\1", k)


def _conferme(voci: list) -> None:
    gruppi = {}
    for v in voci:
        if v.corregge:
            continue
        it = normalizza.chiave(v.principale_italiano or
                               (v.italiano or "").split(",")[0])
        fe = forma_confrontabile(v.principale_ferrarese or
                                 (v.ferrarese or "").split(",")[0])
        if it and fe:
            gruppi.setdefault((it, fe), []).append(v)
    for gruppo in gruppi.values():
        if len(gruppo) < 2:
            continue
        for v in gruppo:
            mia = famiglia_della_fonte(v.fonte)
            altre, viste = [], {mia}
            for w in gruppo:
                f = famiglia_della_fonte(w.fonte)
                if f not in viste:
                    viste.add(f)
                    altre.append(w.id)
            v.conferme = altre


def priorita(voce) -> tuple:
    """L'ordine fra voci con la stessa chiave: correzioni, poi conferme."""
    return (0 if voce.corregge else 1, -len(voce.conferme))


def _senza_maiuscole_del_lemma(voci: list) -> None:
    """Toglie la maiuscola tipografica dei lemmi del Ferri e di Musacchi.

    I nomi propri si riconoscono da Bigoni, che scrive minuscolo e mette la
    maiuscola solo a loro: una voce del Ferri il cui italiano e' quello di una
    voce maiuscola di Bigoni resta maiuscola (`grafia.py`).
    """
    propri = {normalizza.chiave(v.italiano) for v in voci
              if v.grafia_fonte and v.grafia_fonte[:1].isupper()}
    for v in voci:
        if not grafia.lemma_maiuscolo(v.fonte):
            continue
        if normalizza.chiave(v.italiano) in propri:
            continue
        v.ferrarese = grafia.senza_maiuscola(v.ferrarese)
        v.principale_ferrarese = grafia.senza_maiuscola(v.principale_ferrarese)
        v.italiano = grafia.senza_maiuscola(v.italiano)
        v.principale_italiano = grafia.senza_maiuscola(v.principale_italiano)


def _voce_da_dict(grezzo: dict) -> Voce:
    """Costruisce una voce da un dizionario, senza perdere i campi ignoti.

    Un campo che non si conosce non viene buttato: viene tenuto nelle note.
    Meglio una nota sporca che una voce senza meta'.
    """
    noto = {"id", "ferrarese", "italiano", "varianti", "campo", "note",
            "fonte", "attendibilita", "registro", "da_verificare",
            "principale_italiano", "principale_ferrarese", "varieta",
            "moderno", "fonte_moderno", "sinonimi", "corregge", "grafia_fonte",
            "verificata",
            # Il segno lasciato da `correzioni promuovi`: quale elemento e da
            # quali correzioni. Si legge dal file, non serve alla voce.
            "elemento", "da_correzioni"}
    grezzo = dict(grezzo)
    varianti = grezzo.pop("varianti", []) or []
    if isinstance(varianti, str):
        varianti = [v.strip() for v in varianti.split("|") if v.strip()]
    da_verificare = grezzo.pop("da_verificare", False)
    if isinstance(da_verificare, str):
        da_verificare = da_verificare.strip().lower() in ("1", "true", "si", "sì")
    sinonimi = grezzo.pop("sinonimi", []) or []
    if isinstance(sinonimi, str):
        sinonimi = [s.strip() for s in sinonimi.split(";") if s.strip()]
    sconosciuti = {k: grezzo.pop(k) for k in list(grezzo) if k not in noto}
    nota = grezzo.get("note", "") or ""
    if sconosciuti:
        nota = (nota + " " if nota else "") + "[campi non noti: %s]" % json.dumps(
            sconosciuti, ensure_ascii=False
        )
    ferrarese = str(grezzo.get("ferrarese", "")).strip()
    principale_fe = str(grezzo.get("principale_ferrarese", "") or "").strip()
    grafia_fonte = str(grezzo.get("grafia_fonte", "") or "").strip()
    fonte = str(grezzo.get("fonte", "") or "").strip()
    if grafia.e_di_bigoni(fonte) and not grafia_fonte:
        # L'alfabeto di Bigoni letto all'italiana (0.42): il file resta come
        # la fonte lo scrive, la voce si legge in una grafia sola.
        grafia_fonte = ferrarese
        facoltative = [grafia.da_bigoni(f) for f in grafia.facoltative(ferrarese)]
        ferrarese = grafia.da_bigoni(ferrarese)
        principale_fe = grafia.da_bigoni(principale_fe) if principale_fe else ""
        varianti = [grafia.da_bigoni(v) for v in varianti] + [
            f for f in facoltative if f not in varianti]
        if grafia_fonte == ferrarese:
            grafia_fonte = ""
    alfabeto = ""
    if grafia.e_del_treb(fonte) and not grafia_fonte:
        # L'alfabeto del Tréb dal Tridèl (0.47): si porta in quello di Bigoni
        # e da li' nella grafia unica; la forma della fonte resta.
        grafia_fonte = ferrarese
        alfabeto = "treb"
        ferrarese = grafia.da_bigoni(grafia.treb_a_bigoni(ferrarese))
        principale_fe = (grafia.da_bigoni(grafia.treb_a_bigoni(principale_fe))
                         if principale_fe else "")
        varianti = [grafia.da_bigoni(grafia.treb_a_bigoni(v)) for v in varianti]
        if grafia_fonte == ferrarese:
            grafia_fonte, alfabeto = "", ""
    return Voce(
        id=str(grezzo.get("id", "")).strip(),
        ferrarese=ferrarese,
        italiano=str(grezzo.get("italiano", "")).strip(),
        varianti=varianti,
        campo=str(grezzo.get("campo", "") or "").strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        note=nota.strip(),
        principale_italiano=str(grezzo.get("principale_italiano", "") or "").strip(),
        principale_ferrarese=principale_fe,
        fonte=fonte,
        attendibilita=str(grezzo.get("attendibilita", "M") or "M").strip().upper()[:1],
        registro=str(grezzo.get("registro", "") or "").strip(),
        da_verificare=bool(da_verificare),
        moderno=str(grezzo.get("moderno", "") or "").strip(),
        fonte_moderno=str(grezzo.get("fonte_moderno", "") or "").strip(),
        sinonimi=[str(s).strip() for s in sinonimi if str(s).strip()],
        corregge=str(grezzo.get("corregge", "") or "").strip(),
        grafia_fonte=grafia_fonte,
        verificata=str(grezzo.get("verificata", "") or "").strip(),
        alfabeto=alfabeto,
    )