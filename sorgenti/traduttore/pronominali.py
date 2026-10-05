# -*- coding: utf-8 -*-
"""Le particelle non sono parole, e questo modulo fa in modo che non lo diventino.

**Il difetto, e la sua forma esatta.** Scrivendo «lei si siede» il motore
rispondeva `lei`, poi `si → oj`, poi `siede` intatta. La seconda risposta è la
peggiore delle tre: non è un buco, è una **parola sbagliata**. `oj` è una voce
vera del glossario e il motore l'ha restituita come se fosse la traduzione di
una particella pronominale — che in italiano si scrive `si`, e in ferrarese è
attaccata dentro il verbo (`saŋtàrs`, `Acanirss`).

**Cosa fa qui, e cosa non fa.** Riconosce che una parola è una particella, la
**non traduce**, e la attacca al verbo che segue: il risultato è un buco
dichiarato che nomina la costruzione e il numero di verbi pronominali che il
glossario contiene. Non coniuga e non riconosce la forma verbale: rispondere a
«siede» richiederebbe di sapere che «siede» viene da «sedere», e quel passaggio
è una morfologia dell'italiano che nessuna fonte del repository dichiara.

**Perché la risposta non è «non so».** Un buco che nomina la costruzione e dice
quanti verbi ci sono è un posto dove intervenire. Un trattino è un segnale che
qualcosa non va, e non dice dove.

Uso:
    from traduttore import pronominali
    pronominali.particella("si")        # True
    pronominali.unita(["si", "siede"])  # ('si siede', 2)
    pronominali.buco("si siede")        # la frase che spiega
"""
from __future__ import annotations

import io
import json
import os

from . import normalizza

# Che costruzione induce la particella, quando lo sappiamo. La chiave è la
# particella come sta scritta, e il valore è il nome che va detto a chi legge.
# `si` induce un verbo pronominale: è la sola particella che il glossario
# attesta attaccata a un verbo, e sono 109 voci su 109. Per le altre il
# modulo **non dichiara niente**: la chiave non c'è, e il buco parla di «una
# particella pronominale» senza scegliere una costruzione al posto di chi legge.
COSTRUZIONI = {
    "si": "verbo pronominale",
}

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "pronominali.jsonl")

_cache = None


def leggi(percorso: str = PERCORSO) -> tuple:
    """(sistema, righe)."""
    if not os.path.exists(percorso):
        return {}, []
    sistema = {}
    righe = []
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            if riga.startswith("// SISTEMA"):
                sistema = json.loads(riga[len("// SISTEMA"):].strip())
                continue
            if riga.startswith("//"):
                continue
            righe.append(json.loads(riga))
    return sistema, righe


def carica(percorso: str = PERCORSO) -> dict:
    global _cache
    if _cache is not None and percorso == PERCORSO:
        return _cache
    sistema, righe = leggi(percorso)
    risultato = {"sistema": sistema, "righe": righe}
    if percorso == PERCORSO:
        _cache = risultato
    return risultato


def particelle(percorso: str = PERCORSO) -> tuple:
    """Le particelle che il file dichiara — non una lista scritta qui."""
    return tuple(carica(percorso)["sistema"].get("particelle") or ())


def particella(parola: str, percorso: str = PERCORSO) -> bool:
    """True se `parola` è una particella pronominale, e non una parola.

    **Il confronto è sulla forma scritta, non sulla chiave.** È il punto più
    sottile di questo modulo, e il primo tentativo lo ha sbagliato: `chiave()`
    toglie gli accenti, perché serve a fare confronti fra testi di fonti
    diverse, e quindi `chiave("sì") == chiave("si")`. Con quel confronto la
    particella dell'affermazione — `Sì`, che il glossario scrive come voce
    separata (V8171) — sarebbe stata trattata come particella del verbo
    pronominale, e `Sì va` sarebbe diventato un buco dichiarato invece di
    cercare `sì` nel glossario. Due parole che la pagina distingue già (V0026
    `si → oj`, V8171 `Sì → Sì`) non possono diventare la stessa qui: se
    l'indice le distingue, l'accorpamento le deve distinguere.

    `normale()` conserva l'accento e toglie solo la punteggiatura, ed è la
    forma giusta per chiedere «è la particella?».
    """
    k = normalizza.normale(parola)
    return bool(k) and any(k == normalizza.normale(p)
                           for p in particelle(percorso))


def unita(token: list, i: int = 0) -> tuple:
    """`(testo, quante)` se `token[i]` apre un verbo pronominale, altrimenti None.

    Si prende **due** token e non tre: in italiano la particella si attacca al
    verbo e niente altro, e un accorpamento che si mangia la parola dopo
    trasformerebbe «si siede qui» in un errore di sillaba. Se la particella
    e' ultima, non c'e' verbo da attaccarle e il ritorno e' `None`: una
    particella sciolta non e' un verbo pronominale, e' quello che il glossario
    potrebbe o non potrebbe conoscere — la decisione la prende il glossario,
    non questo modulo.
    """
    if i < 0 or i + 1 >= len(token):
        return None
    if not particella(token[i]):
        return None
    return (" ".join(token[i:i + 2]), 2)


def buco(testo: str, percorso: str = PERCORSO) -> dict:
    """La risposta onesta per un verbo pronominale che il progetto non coniuga.

    Contiene tre cose e non una: **che cos'e'**, **quanti** verbi pronominali ci
    sono, e **che cosa manca** per rispondere. Una risposta che dicesse solo
    «non lo so» lascerebbe chi legge senza sapere se il progetto non sa o se la
    fonte non c'e'.
    """
    sistema, righe = leggi(percorso)
    verbi = len(righe)
    if not sistema:
        return {"testo": testo, "origine": "nessuna",
                "confidenza": 0.0,
                "dettaglio": ("verbo pronominale, e dati/pronominali.jsonl non "
                              "dichiara nulla: senza la riga SISTEMA non si sa "
                              "nemmeno quante particelle sono particelle")}
    particella_usata = testo.split(" ", 1)[0]
    # Il nome della costruzione lo decide **la particella che c'è**, non il
    # modulo: `si` davanti a qualcosa dà un verbo pronominale, `ci` e `ne`
    # davanti a un verbo danno un pronome. Dichiararlo qui — «è un verbo
    # pronominale» — sarebbe un'affermazione che nessuna fonte del repository
    # fa, e che cambia da particella a particella.
    costruzione = COSTRUZIONI.get(normalizza.normale(particella_usata),
                                  "particella pronominale")
    return {
        "testo": testo,
        "origine": "nessuna",
        "confidenza": 0.0,
        "dettaglio": (
            "%s: %s è una particella pronominale, non una parola, e in "
            "ferrarese si attacca al verbo (il glossario ha %d verbi con la "
            "particella dentro la voce, per esempio %s). Il progetto non "
            "coniuga, quindi della forma coniugata non c'è niente: qui la "
            "particella non viene tradotta e «%s» resta com'è. E il progetto "
            "non distingue un verbo da un nome: che cosa segue la particella "
            "non lo sa, e non lo dichiara."
            % (costruzione, particella_usata, verbi,
               ", ".join(r["ferrarese"] for r in righe[:3]),
               testo.split(" ", 1)[-1])),
    }
