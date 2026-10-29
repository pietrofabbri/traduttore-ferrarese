# -*- coding: utf-8 -*-
"""La verifica a campione: quanto ci si puo' fidare di una fonte.

**Perche' esiste.** Il titolare del progetto ha dichiarato il 2026-10-08 due
cose che vanno tenute insieme: il progetto deve diventare il punto di accesso a
tutta la conoscenza disponibile sul ferrarese, e la verifica umana deve essere
**a campione e la minima possibile** (`AGENTS.md` §6 punto 11). Con 17370 voci e
quasi tutte `attendibilita: I`, verificare voce per voce non succedera' mai.
Quello che si puo' fare e' rispondere a una domanda diversa: **su cento voci di
questa fonte, quante sono sbagliate?** E a quella domanda risponde un campione,
non un censimento.

**Che cosa si chiede alla persona.** Non di aprire il libro: di dire, da
parlante, se la voce **si dice**. Gli esiti sono tre, e il terzo non e' un
ripiego:

- `si_dice` — la voce e' ferrarese e vuol dire quello che il glossario dice
  (la grafia puo' essere diversa: si scrive in `come_si_dice`);
- `non_si_dice` — la voce e' sbagliata: la forma o il significato;
- `non_la_conosco` — il parlante non la conosce. Non entra nel tasso di
  errore, perche' non e' un giudizio sulla voce; ma e' un dato, ed e' il
  primo segnale che il progetto ha su quali parole non si usano piu'
  (`AGENTS.md` §6 punto 5).

**Perche' l'estrazione e' dichiarata e non scelta.** Un campione scelto a mano
e' un campione che conferma quello che chi sceglie gia' pensa. Le voci si
estraggono con un **seme** scritto in `dati/campioni/estrazioni.json`, e un
giudizio su una voce che non e' nell'estrazione e' un errore (controllo K5):
non si puo' «verificare a campione» le voci che si sa gia' essere giuste.

**Che cosa non fa.** Non cambia il glossario. Una voce giudicata `si_dice` resta
`attendibilita: I`: il giudizio vive in `dati/campioni/giudizi.jsonl`, con chi,
quando e su quale estrazione, e il glossario non lo sa. Se e come un giudizio
debba promuovere una voce e' una decisione aperta, non un effetto collaterale.
"""
from __future__ import annotations

import io
import json
import math
import os
import random
import re
from dataclasses import dataclass, field

ESITI = ("si_dice", "non_si_dice", "non_la_conosco")

# Le voci del glossario non portano un campo `fonte_id`: portano il testo della
# fonte. Le fonti nuove lo scrivono fra parentesi, «(S006)»; le prime voci no,
# e per quelle basta l'autore, che e' scritto per esteso. Una voce che non si
# riesce ad attribuire va in `altro` e non viene estratta: un campione di una
# fonte che contiene voci di un'altra misura la cosa sbagliata.
AUTORI = (("Ferri", "S004"), ("Biondelli", "S001"),
          ("wikipedia.org/wiki/Dialetto_ferrarese", "S002"),
          ("Nannini", "S005"))
ALTRO = "altro"

# Il livello di confidenza dell'intervallo. 95% e' la convenzione; e' scritto
# qui per non doverlo indovinare dal numero 1.96.
Z_95 = 1.959963984540054


def fonte_della_voce(voce) -> str:
    """Il codice della fonte da cui la voce viene, o `altro`."""
    testo = getattr(voce, "fonte", "") or ""
    trovata = re.search(r"\((S\d{3})\)", testo)
    if trovata:
        return trovata.group(1)
    for autore, codice in AUTORI:
        if autore in testo:
            return codice
    return ALTRO


def _ordine(identificatore: str):
    """`V0012` prima di `V10400`: l'ordine dei numeri, non delle stringhe."""
    numero = re.sub(r"\D", "", identificatore)
    return (int(numero) if numero else -1, identificatore)


def popolazione(glossario, fonte: str) -> list:
    """Gli id delle voci di una fonte, in ordine numerico.

    L'ordine e' fissato qui perche' l'estrazione dipende da lui: lo stesso seme
    su un elenco in un altro ordine da' un altro campione.
    """
    return sorted((v.id for v in glossario.voci
                   if fonte_della_voce(v) == fonte), key=_ordine)


def estrai(glossario, fonte: str, n: int, seme: str) -> list:
    """`n` id estratti a caso dalla fonte, riproducibili con `seme`.

    `random.Random` con un seme stringa e' deterministico fra versioni di
    Python (dalla 3.2 il seme passa per SHA-512), quindi chiunque rilanci
    l'estrazione con lo stesso glossario ottiene le stesse voci.
    """
    tutte = popolazione(glossario, fonte)
    if n > len(tutte):
        raise ValueError("la fonte %s ha %d voci, non se ne estraggono %d"
                         % (fonte, len(tutte), n))
    scelte = random.Random(seme).sample(tutte, n)
    return sorted(scelte, key=_ordine)


def wilson(errori: int, giudicate: int) -> tuple:
    """L'intervallo di Wilson al 95% per una proporzione.

    Non l'intervallo «normale» `p ± 1,96·√(p(1-p)/n)`: con zero errori su venti
    quello dice [0, 0], cioe' «la fonte non sbaglia mai», che e' esattamente la
    frase che un campione piccolo non autorizza. Wilson con 0 su 20 dice che il
    tasso vero puo' arrivare al 16%, ed e' la cosa onesta da scrivere.
    Ritorna `(stima, minimo, massimo)`, oppure `(None, None, None)` se non c'e'
    nessun giudizio utile.
    """
    if giudicate <= 0:
        return (None, None, None)
    p = errori / giudicate
    z2 = Z_95 * Z_95
    centro = (p + z2 / (2 * giudicate)) / (1 + z2 / giudicate)
    ampiezza = (Z_95 * math.sqrt(p * (1 - p) / giudicate
                                 + z2 / (4 * giudicate * giudicate))
                / (1 + z2 / giudicate))
    return (p, max(0.0, centro - ampiezza), min(1.0, centro + ampiezza))


@dataclass
class Estrazione:
    id: str
    fonte: str
    n: int
    seme: str
    data: str
    popolazione: int
    voci: list
    motivo: str = ""

    def come_dict(self) -> dict:
        return {"id": self.id, "fonte": self.fonte, "n": self.n,
                "seme": self.seme, "data": self.data,
                "popolazione": self.popolazione, "motivo": self.motivo,
                "voci": list(self.voci)}


@dataclass
class Giudizio:
    id: str
    estrazione: str
    voce: str
    esito: str
    chi: str
    data: str
    come_si_dice: str = ""
    nota: str = ""

    def come_dict(self) -> dict:
        d = {"id": self.id, "estrazione": self.estrazione, "voce": self.voce,
             "esito": self.esito, "chi": self.chi, "data": self.data}
        if self.come_si_dice:
            d["come_si_dice"] = self.come_si_dice
        if self.nota:
            d["nota"] = self.nota
        return d


@dataclass
class Campioni:
    estrazioni: list = field(default_factory=list)
    giudizi: list = field(default_factory=list)
    nota: str = ""

    @classmethod
    def da_file(cls, cartella: str) -> "Campioni":
        """Legge `estrazioni.json` e `giudizi.jsonl`. File assenti = vuoti."""
        estrazioni, nota = [], ""
        percorso = os.path.join(cartella, "estrazioni.json")
        if os.path.exists(percorso):
            with io.open(percorso, encoding="utf-8") as f:
                grezzo = json.load(f)
            nota = grezzo.get("_nota", "")
            for e in grezzo.get("estrazioni", []):
                estrazioni.append(Estrazione(
                    id=e.get("id", ""), fonte=e.get("fonte", ""),
                    n=int(e.get("n", 0)), seme=e.get("seme", ""),
                    data=e.get("data", ""),
                    popolazione=int(e.get("popolazione", 0)),
                    voci=list(e.get("voci", [])), motivo=e.get("motivo", "")))
        giudizi = []
        percorso = os.path.join(cartella, "giudizi.jsonl")
        if os.path.exists(percorso):
            with io.open(percorso, encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if not riga or riga.startswith("//"):
                        continue
                    g = json.loads(riga)
                    giudizi.append(Giudizio(
                        id=g.get("id", ""), estrazione=g.get("estrazione", ""),
                        voce=g.get("voce", ""), esito=g.get("esito", ""),
                        chi=g.get("chi", ""), data=g.get("data", ""),
                        come_si_dice=g.get("come_si_dice", ""),
                        nota=g.get("nota", "")))
        return cls(estrazioni, giudizi, nota)

    def scrivi_estrazioni(self, cartella: str) -> None:
        percorso = os.path.join(cartella, "estrazioni.json")
        with io.open(percorso, "w", encoding="utf-8") as f:
            json.dump({"_nota": self.nota,
                       "estrazioni": [e.come_dict() for e in self.estrazioni]},
                      f, ensure_ascii=False, indent=2)
            f.write("\n")

    def aggiungi_giudizi(self, cartella: str, nuovi: list) -> None:
        """Appende in coda: un giudizio scritto non si riscrive."""
        percorso = os.path.join(cartella, "giudizi.jsonl")
        with io.open(percorso, "a", encoding="utf-8") as f:
            for g in nuovi:
                f.write(json.dumps(g.come_dict(), ensure_ascii=False) + "\n")
        self.giudizi.extend(nuovi)

    def estrazione(self, identificatore: str):
        for e in self.estrazioni:
            if e.id == identificatore:
                return e
        return None

    def prossimo_id(self, prefisso: str, esistenti: list) -> str:
        numeri = [int(re.sub(r"\D", "", x) or 0) for x in esistenti]
        return "%s%04d" % (prefisso, (max(numeri) if numeri else 0) + 1)

    def giudicate(self) -> dict:
        """`(estrazione, voce)` -> giudizio. L'ultimo vince, ma K8 lo segnala."""
        return {(g.estrazione, g.voce): g for g in self.giudizi}

    def riepilogo(self) -> list:
        """Per fonte: quante estratte, giudicate, errate, sconosciute, e il tasso.

        Le estrazioni della stessa fonte si sommano: sono campioni casuali
        indipendenti della stessa popolazione, e insieme stringono l'intervallo.
        """
        giudicate = self.giudicate()
        per_fonte = {}
        for e in self.estrazioni:
            r = per_fonte.setdefault(e.fonte, {
                "fonte": e.fonte, "estratte": 0, "si_dice": 0,
                "non_si_dice": 0, "non_la_conosco": 0, "popolazione": 0})
            r["estratte"] += len(e.voci)
            r["popolazione"] = max(r["popolazione"], e.popolazione)
            for voce in e.voci:
                g = giudicate.get((e.id, voce))
                if g and g.esito in ESITI:
                    r[g.esito] += 1
        uscita = []
        for fonte in sorted(per_fonte):
            r = per_fonte[fonte]
            utili = r["si_dice"] + r["non_si_dice"]
            r["giudicate"] = utili + r["non_la_conosco"]
            r["stima"], r["minimo"], r["massimo"] = wilson(r["non_si_dice"], utili)
            uscita.append(r)
        return uscita


def leggi_giudizi_incollati(testo: str) -> list:
    """Le righe JSON che la pagina di verifica produce, come dizionari.

    Righe vuote e righe che non cominciano con `{` si saltano: chi incolla da
    un messaggio porta con se' anche il testo intorno.
    """
    righe = []
    for riga in testo.splitlines():
        riga = riga.strip()
        if riga.startswith("{"):
            righe.append(json.loads(riga))
    return righe


def percento(x) -> str:
    return "—" if x is None else ("%.0f%%" % (100 * x))
