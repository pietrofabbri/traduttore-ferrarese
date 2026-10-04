"""Le trascrizioni fonetiche: cosa suona, in simboli.

Una lingua senza alfabeto si scrive a orecchio. Il ferrarese si scrive a
orecchio da sempre, e questo vuol dire che **la grafia non dice la
pronuncia**: `magnàr` e `magnar` nella stessa fonte sono la stessa parola con
due scelte di scrittura, non due suoni.

Il gioco ha bisogno di una traccia di pronuncia per far ascoltare e far
ripetere, e la traccia piu' economica e piu' onesta e' la trascrizione IPA.
Quindi `dati/fonetica.jsonl` tiene, per ogni forma che si vuole far ascoltare,
la forma scritta e la sua resa.

Tre regole che tengono insieme tutto il file, e che i controlli fanno
rispettare:

1. **La trascrizione non e' una fonte.** Il campo `fonte` dice da dove
   viene la *scrittura*, non il suono. Una riga con `attendibilita: "D"`
   significa che qualcuno ha ascoltato e ha scritto, e in quel caso `fonte`
   nomina la persona, il luogo e la data. Tutto il resto e' `I`
   (interpretato): una lettura della grafia secondo le regole dichiarate in
   testa al file.
2. **Nessuna regola fonetica che nessuna fonte dichiari.** Le regole che il
   file usa sono poche e sono nella sua intestazione. Dove la fonte non dice
   niente - la z intervocalica, la s intervocalica - il file non sceglie: la
   voce porta la nota e resta `da_verificare`.
3. **La verifica la fa un parlante.** L'unica cosa che porta una riga da `I`
   a `D` e' una persona che ha detto «si' e' cosi'», con nome, luogo e data
   nel campo `fonte`. Non un dizionario, non un modello, non il progetto.

Il simbolo di non corrispondenza fra scrittura e suono e' l'assenza
dell'accento tonico nella fonte: se la fonte non marca l'accento, la
trascrizione non lo mette, e la nota lo dice. Si inventa cosi' una meta'
trascrizione, non una intera.
"""

from __future__ import annotations

import json
import os
import unicodedata
from dataclasses import dataclass, field

# I simboli ammessi in una trascrizione. E' un insieme chiuso perche' una
# trascrizione con le vocali accentate italiane (`magnàr` dentro il campo IPA)
# non e' una trascrizione: e' la grafia rimessa al suo posto, e succede.
SIMBOLI_IPA = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ɐɑɒɓɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɢɣɤɥɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸœɶɹɺɻɽɾʀʁʂʃʈʊʋⱱʌʍχʎʏʐʑʒʔʡʕʢǀǁǂǃ"
    "ˈˌːˑʰʱʲʴʷʼˈ"
)
# Quello che non e' un simbolo ma e' lecito: stacchi, parentesi, il punto che
# separa i gruppi sillabici, gli slash che racchiudono la trascrizione.
PERMESSI = set("/-().[] \u2016\u2015")

PREDEFINITO = "ferrarese, trascrizione fonematica di comodo"

# L'unica riga di `dati/fonetica.jsonl` che il codice legge invece di
# ignorarla come un commento. Porta dentro una riga sola la dichiarazione di
# **come** si suona — il riproduttore vocale, la velocita' e l'elenco dei
# voti — e la mette li' perche' le regole di questo progetto stanno tutte
# nello stesso file: una voce scelta in un altro file sarebbe una regola che
# nessuno apre, quindi una regola che non c'e'.
MARCATORE_SISTEMA = "// SISTEMA "


def percorso_fonetica() -> str:
    """Il percorso di `dati/fonetica.jsonl`, preso dalla radice del progetto."""
    radice = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    return os.path.join(radice, "dati", "fonetica.jsonl")


def leggi_sistema(percorso: str = "") -> dict:
    """Che cosa il file dichiara di se' stesso: la voce, la velocita', i voti.

    Ritorna sempre un dizionario, anche quando la dichiarazione non c'e' o e'
    rotta: in quel caso `dichiarata` resta falso e `problema` dice perche'.
    **Non si indovina**: se il file non dichiara la voce, questa funzione non ne
    sceglie una, e chi la cerca deve poter vedere che non c'e'.
    """
    percorso = percorso or percorso_fonetica()
    esito = {"voce": "", "velocita": 0, "voti": [],
             "dichiarata": False, "problema": ""}
    if not (percorso and os.path.exists(percorso)):
        esito["problema"] = "il file delle trascrizioni non c'e': %r" % percorso
        return esito

    dichiarazione = ""
    with open(percorso, "r", encoding="utf-8") as f:
        for riga in f:
            if riga.startswith(MARCATORE_SISTEMA):
                dichiarazione = riga[len(MARCATORE_SISTEMA):].strip()
                break
    if not dichiarazione:
        esito["problema"] = ("nessuna riga `%s` con la dichiarazione della voce"
                             % MARCATORE_SISTEMA.strip())
        return esito
    try:
        grezzo = json.loads(dichiarazione)
    except ValueError as errore:
        esito["problema"] = ("la dichiarazione della voce non e' JSON leggibile: "
                             "%s" % errore)
        return esito
    voti = grezzo.get("voti")
    if not isinstance(voti, list):
        esito["problema"] = "`voti` non e' un elenco di nomi di voce"
        return esito
    try:
        velocita = int(grezzo.get("velocita", 0) or 0)
    except (TypeError, ValueError):
        esito["problema"] = "`velocita` non e' un numero di parole al minuto"
        return esito

    esito["voce"] = str(grezzo.get("voce", "") or "").strip()
    esito["velocita"] = velocita
    esito["voti"] = [str(v).strip() for v in voti if str(v).strip()]
    esito["dichiarata"] = bool(esito["voce"] and esito["voti"])
    if not esito["dichiarata"]:
        esito["problema"] = ("la dichiarazione non dice quale voce suona, o non "
                             "elenca nessun voto fra cui scegliere")
    return esito


def ipa_valida(ipa: str) -> tuple:
    """Dice se una trascrizione usa solo simboli che le si puo' dare.

    Restituisce `(valida, caratteri_sospetti)`. Non decide se la trascrizione
    e' *giusta*: quello e' affare di un parlante. Decide solo se e' una
    trascrizione, e questo e' un controllo meccanico che puo' fare una macchina
    senza rischiare niente.
    """
    sospetti = []
    for carattere in (ipa or ""):
        if carattere in SIMBOLI_IPA or carattere in PERMESSI:
            continue
        if carattere not in sospetti:
            sospetti.append(carattere)
    return (not sospetti), sospetti


@dataclass
class Trascrizione:
    """Una forma scritta e come suona."""

    id: str
    # Il riferimento e' l'id di una voce del glossario o di una coppia. Non e'
    # un campo libero: se non combacia con nessuno, la trascrizione non
    # descrive niente e i controlli lo segnalano (F4).
    riferimento: str
    forma: str
    ipa: str
    varieta: str = ""
    fonte: str = ""
    attendibilita: str = "I"
    nota: str = ""
    da_verificare: bool = True
    # Il riproduttore vocale che suona **questa** parola, quando e' diverso da
    # quello dichiarato per il sistema. Vuoto vuol dire «quello dichiarato in
    # testa al file»: una riga non sceglie una voce, la eredita.
    voce: str = ""

    def come_dict(self) -> dict:
        return {
            "id": self.id,
            "riferimento": self.riferimento,
            "forma": self.forma,
            "ipa": self.ipa,
            "varieta": self.varieta,
            "fonte": self.fonte,
            "attendibilita": self.attendibilita,
            "nota": self.nota,
            "da_verificare": self.da_verificare,
            "voce": self.voce,
        }


@dataclass
class Fonetica:
    """Le trascrizioni, indicizzate per riferimento e per forma."""

    trascrizioni: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.trascrizioni)

    @classmethod
    def da_file(cls, percorso: str) -> "Fonetica":
        elementi = []
        if percorso and os.path.exists(percorso):
            with open(percorso, "r", encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if riga and not riga.startswith("//"):
                        elementi.append(_trascrizione_da_dict(json.loads(riga)))
        return cls(elementi)

    def per_riferimento(self, riferimento: str) -> list:
        return [t for t in self.trascrizioni if t.riferimento == riferimento]

    def per_id(self, identificatore: str):
        for t in self.trascrizioni:
            if t.id == identificatore:
                return t
        return None

    def cerca_forma(self, forma: str) -> list:
        """Trascrizioni di una forma scritta, per confronto esatto.

        Il confronto e' sulle lettere e sul segno diacritico accentante,
        pero' tollera l'apostrofo e i due accenti della stessa vocale: `gh'e`
        e `gh'è` sono la stessa scelta di scrittura.
        """
        k = _chiave_forma(forma)
        if not k:
            return []
        return [t for t in self.trascrizioni if _chiave_forma(t.forma) == k]

    def per_varieta(self, varieta: str) -> list:
        return [t for t in self.trascrizioni if t.varieta == varieta]

    def quante_verificate(self) -> int:
        """Quante sono state fatte verificare da qualcuno che parla.

        Il numero che conta piu' di tutti gli altri: e' la misura di quanto
        questo progetto sia onesto, e almeno finche' vale zero la parte piu'
        delicata - la pronuncia - non e' documentata, e va detto in pagina.
        """
        return sum(1 for t in self.trascrizioni
                   if t.attendibilita == "D" and not t.da_verificare)


def _chiave_forma(forma: str) -> str:
    """La chiave di una forma scritta: senza apostrofi e senza accenti.

    `gh'e` e `gh'è` sono due scelte di scrittura della stessa scelta, e chi
    cerca con la tastiera senza accenti deve trovare la trascrizione lo
    stesso. La chiave non tocca nient'altro: `gh` resta `gh`, perche' qui la
    distinzione fra `ghe` e `gh'è` conta ed e' dichiarata nelle forme.
    """
    testo = (forma or "").strip().lower().replace("'", "").replace("’", "")
    return "".join(c for c in unicodedata.normalize("NFD", testo)
                   if not unicodedata.combining(c))


def _trascrizione_da_dict(grezzo: dict) -> Trascrizione:
    da_verificare = grezzo.get("da_verificare", True)
    if isinstance(da_verificare, str):
        da_verificare = da_verificare.strip().lower() in ("1", "true", "si", "sì")
    return Trascrizione(
        id=str(grezzo.get("id", "")).strip(),
        riferimento=str(grezzo.get("riferimento", "")).strip(),
        forma=str(grezzo.get("forma", "")).strip(),
        ipa=str(grezzo.get("ipa", "")).strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        fonte=str(grezzo.get("fonte", "") or "").strip(),
        attendibilita=str(grezzo.get("attendibilita", "I") or "I").strip().upper()[:1],
        nota=str(grezzo.get("nota", "") or "").strip(),
        da_verificare=bool(da_verificare),
        voce=str(grezzo.get("voce", "") or "").strip(),
    )