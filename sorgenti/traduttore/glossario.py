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

from . import normalizza
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
        """
        pezzi = []
        if (testo or "").strip():
            pezzi.append(testo.strip())
        pezzi += [p.strip() for p in re.split(r"[,;]", testo or "") if p.strip()]
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
        self.voci = list(voci or [])
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


def _uniche_per_id(voci: list) -> list:
    visti = set()
    uniche = []
    for voce in voci:
        if voce.id in visti:
            continue
        visti.add(voce.id)
        uniche.append(voce)
    return uniche


def _voce_da_dict(grezzo: dict) -> Voce:
    """Costruisce una voce da un dizionario, senza perdere i campi ignoti.

    Un campo che non si conosce non viene buttato: viene tenuto nelle note.
    Meglio una nota sporca che una voce senza meta'.
    """
    noto = {"id", "ferrarese", "italiano", "varianti", "campo", "note",
            "fonte", "attendibilita", "registro", "da_verificare",
            "principale_italiano", "principale_ferrarese", "varieta",
            "moderno", "fonte_moderno", "sinonimi"}
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
    return Voce(
        id=str(grezzo.get("id", "")).strip(),
        ferrarese=str(grezzo.get("ferrarese", "")).strip(),
        italiano=str(grezzo.get("italiano", "")).strip(),
        varianti=varianti,
        campo=str(grezzo.get("campo", "") or "").strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        note=nota.strip(),
        principale_italiano=str(grezzo.get("principale_italiano", "") or "").strip(),
        principale_ferrarese=str(grezzo.get("principale_ferrarese", "") or "").strip(),
        fonte=str(grezzo.get("fonte", "") or "").strip(),
        attendibilita=str(grezzo.get("attendibilita", "M") or "M").strip().upper()[:1],
        registro=str(grezzo.get("registro", "") or "").strip(),
        da_verificare=bool(da_verificare),
        moderno=str(grezzo.get("moderno", "") or "").strip(),
        fonte_moderno=str(grezzo.get("fonte_moderno", "") or "").strip(),
        sinonimi=[str(s).strip() for s in sinonimi if str(s).strip()],
    )