# -*- coding: utf-8 -*-
"""Le forme verbali attestate, e **nient'altro**.

**Perché questo modulo esiste e cosa rifiuta di fare.** Il traduttore non sa
coniugare e potrebbe sembrare che gli manchi il codice: gli manca il **paradigma**.
Nel repository non c'è una fonte che tabelli la coniugazione ferrarese, e un
coniugatore che la ricava dalle desinenze italiane produrrebbe forme ferraresi
che nessuno ha mai scritto. Il progetto non mette in `dati/` niente che non
sia in una fonte, quindi qui non si ricava niente.

Quindi `coniuga()` ha due possibili esiti e sono entrambi onesti: la forma che la
fonte scrive, oppure un **buco che dice quale parte manca**. Non c'è una terza
risposta, e non c'è un ripiego.

**Il buco è più utile del silenzio.** Uno studente che scrive «andammo» oggi
 riceve un trattino e non sa se il progetto non sa o se non c'è. Qui la risposta
è: il progetto ha 18 forme attestate su 12 verbi, questa casella non è fra
quelle, e le due fonti che parlano di verbi sono S015 e S001.

**Il clitico fa parte della chiave.** S015 dichiara (R036) che `avér` cambia
forma con la `ɣ`: «mi aj ò» e «mi a ɣ o» sono la stessa persona e lo stesso
tempo con due forme diverse. Una chiave che non tiene conto del clitico
restituirebbe una delle due per tutte e due le frasi.

Uso:

    from traduttore import verbi
    verbi.coniuga("aŋdàr", "1sing", "passato")
    # {'forma': 'andò', 'fonte': 'S001', ...}
    verbi.coniuga("aŋdàr", "2sing", "presente")
    # {'forma': '', 'problema': 'nessuna fonte documenta il 2sing presente'}
"""
from __future__ import annotations

import io
import json
import os

from . import normalizza

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "verbi.jsonl")

_cache = None


def _riga_sistema(testo: str) -> dict:
    """La riga `// SISTEMA` del file: il vocabolario del modulo."""
    for riga in testo.split("\n"):
        if riga.startswith("// SISTEMA"):
            return json.loads(riga[len("// SISTEMA"):].strip())
    return {}


def leggi(percorso: str = PERCORSO) -> tuple:
    """(sistema, righe). Il sistema e' vuoto se la riga non c'e'."""
    if not os.path.exists(percorso):
        return {}, []
    righe = []
    sistema = {}
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            if riga.startswith("// SISTEMA"):
                sistema = _riga_sistema(riga)
                continue
            if riga.startswith("//"):
                continue
            righe.append(json.loads(riga))
    return sistema, righe


def carica(percorso: str = PERCORSO) -> dict:
    """Il sistema e l'indice, una volta sola.

    L'indice e' su quattro chiavi — lemma, persona, tempo, clitico — e su un
    quinto, il lemma italiano, che serve al traduttore per la domanda che fa
    uno studente: «questa parola italiana e' una di quelle che le fonti
    coniugano?».
    """
    global _cache
    if _cache is not None and percorso == PERCORSO:
        return _cache
    sistema, righe = leggi(percorso)
    per_forma = {}
    per_italiano = {}
    for riga in righe:
        chiave = chiave_forma(riga["lemma"], riga["persona"], riga["tempo"],
                              riga.get("clitico", ""))
        per_forma.setdefault(chiave, []).append(riga)
        per_italiano.setdefault(normalizza.chiave(riga.get("italiano") or ""),
                                []).append(riga)
    risultato = {"sistema": sistema, "righe": righe, "per_forma": per_forma,
                 "per_italiano": per_italiano}
    if percorso == PERCORSO:
        _cache = risultato
    return risultato


def chiave_forma(lemma: str, persona: str, tempo: str, clitico: str = "") -> str:
    return "|".join([normalizza.chiave(lemma), persona, tempo,
                     normalizza.chiave(clitico or "")])


def _dichiara(problema: str) -> dict:
    """Il buco, nella stessa forma in cui lo restituisce ogni altra risposta."""
    return {"forma": "", "problema": problema, "fonte": "", "nota": ""}


def coniuga(lemma: str, persona: str, tempo: str,
            clitico: str = "", percorso: str = PERCORSO) -> dict:
    """La forma attestata, o il buco che dice che cosa manca.

    L'ordine dei controlli è dichiarato perché il buco nomini **la** cosa che
    manca, non la prima che capita: un lemma assente è un buco diverso da una
    persona non documentata, e per chi legge sono due lavori diversi.
    """
    dati = carica(percorso)
    sistema = dati["sistema"]
    persone = sistema.get("persone") or []
    tempi = sistema.get("tempi") or []
    if not sistema or not persone:
        return _dichiara("dati/verbi.jsonl non dichiara il sistema: senza la "
                         "riga SISTEMA non si sa che persone e tempi esistono")
    if tempo not in tempi:
        return _dichiara("«%s» non è fra i tempi dichiarati (%s)"
                         % (tempo, ", ".join(tempi)))
    if persona and persona not in persone:
        return _dichiara("«%s» non è fra le persone dichiarate (%s)"
                         % (persona, ", ".join(persone)))

    righe = dati["per_forma"].get(
        chiave_forma(lemma, persona, tempo, clitico))
    if righe:
        return {"forma": righe[0]["forma"], "problema": "",
                "fonte": "%s, %s" % (righe[0]["fonte"], righe[0]["dove"]),
                "nota": righe[0].get("nota", ""), "riga": righe[0]}

    # Lo stesso lemma e lo stesso tempo, con un'altra persona: la casella esiste
    # nella fonte ma non per chi si chiede. E' una notizia diversa da «il verbo
    # non c'è».
    dello_stesso_verbo = [r for r in dati["righe"]
                          if normalizza.chiave(r["lemma"]) ==
                          normalizza.chiave(lemma)
                          and r["tempo"] == tempo
                          and normalizza.chiave(r.get("clitico") or "") ==
                          normalizza.chiave(clitico or "")]
    if dello_stesso_verbo:
        hanno = ", ".join("%s %s" % (r["persona"] or "senza persona", r["forma"])
                          for r in dello_stesso_verbo)
        return _dichiara("nessuna fonte scrive %s %s di %s: della fonte si ha "
                         "solo %s" % (persona or "la forma senza persona",
                                      tempo, lemma, hanno))
    conosce = sorted({normalizza.chiave(r["lemma"]) for r in dati["righe"]})
    if normalizza.chiave(lemma) not in conosce:
        return _dichiara("il verbo %s non è fra i %d che le fonti coniugano "
                         "(%s)" % (lemma, len(conosce), ", ".join(conosce)))
    return _dichiara("nessuna fonte scrive %s %s di %s"
                     % (persona or "la forma senza persona", tempo, lemma))


def dall_italiano(parola: str, percorso: str = PERCORSO) -> dict:
    """Dalla parola **italiana** coniugata alla forma ferrarese attestata.

    Non e' il inverso di `coniuga()` e non pretende di esserlo: qui la parola
    italiana e' una di quelle che una fonte ha messo accanto alla forma
    ferrarese, quindi la risposta esiste per definizione. Se non c'e', la risposta
    e' il buco — e il buco non dice «non so tradurre» ma «questa forma non è
    fra quelle documentate», che è una cosa che si può correggere.
    """
    dati = carica(percorso)
    righe = dati["per_italiano"].get(normalizza.chiave(parola))
    if not righe:
        quante = len(dati["per_italiano"])
        esempi = ", ".join(sorted({r["italiano"] for r in dati["righe"]})[:8])
        return {"forma": "", "problema": "nessuna fonte coniuga «%s»: le "
                       "forme italiane documentate sono %d (%s)"
                       % (parola, quante, esempi), "fonte": "", "nota": ""}
    righe = sorted(righe, key=lambda r: (r["tempo"], r["persona"]))
    return {"forma": righe[0]["forma"], "problema": "",
            "fonte": "%s, %s" % (righe[0]["fonte"], righe[0]["dove"]),
            "nota": righe[0].get("nota", ""), "riga": righe[0]}


def cosa_sa(percorso: str = PERCORSO) -> dict:
    """Il conto, per chi chiede al progetto quanto sa — e cosa non sa.

    `vuoto` è la parte importante: è la lista delle caselle che nessuna fonte
    documenta, presa dalla riga `SISTEMA` e non calcolata, perché il progetto
    non deduce un buco, lo dichiara.
    """
    dati = carica(percorso)
    sistema = dati["sistema"]
    verbi = sorted({r["lemma"] for r in dati["righe"]})
    return {
        "forme": len(dati["righe"]),
        "verbi": len(verbi),
        "lemmi": verbi,
        "persone": sistema.get("persone", []),
        "tempi": sistema.get("tempi", []),
        "vuoto": [tuple(v) for v in sistema.get("vuoto", [])],
        "citato_da": sistema.get("citato_da", []),
    }


def spiega_buco(parola: str = "", percorso: str = PERCORSO) -> str:
    """La frase che va accanto ai buchi: corta, e con i numeri dentro.

    Il parametro `parola` **non** viene usato per accusare nessuno, e il
    motivo sta in un caso reale: i buchi di una traduzione sono parole che il
    motore non sa tradurre, e `il` o `di` sono due di quelle. Una frase che
    dicesse «questa parola non è una forma verbale attestata» sarebbe falsa
    per metà dei buchi, quindi la frase parla **del progetto** e non della
    parola: è vero in ogni caso, e il lettore fa il confronto da sé.
    """
    sa = cosa_sa(percorso)
    if not sa["forme"]:
        return ""
    vuoto = ", ".join("%s %s" % (p, t) for p, t in sa["vuoto"])
    return ("il progetto non coniuga: le fonti del repository attestano %d "
            "forme verbali su %d verbi, e le caselle che nessuna fonte scrive "
            "sono %s. Una parola coniugata che non è fra quelle resta un buco "
            "dichiarato, non una forma indovinata."
            % (sa["forme"], sa["verbi"], vuoto))
