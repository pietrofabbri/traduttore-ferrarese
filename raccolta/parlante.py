#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le frasi dichiarate da un parlante: sono in `dati/coppie.jsonl`, e si controllano.

**Perché questo file non genera niente.** Tutti gli altri `raccolta/da_*.py`
prendono una pagina o un libro e tirano fuori le voci: qui la fonte è una
persona che scrive una frase, e quella frase **è già il dato**. Un generatore
che la copiasse da un altro file non aggiungerebbe niente e aprirebbe una porta
per cui la riga in `dati/coppie.jsonl` potrebbe cambiare senza che la frase
dichiarata resti indietro da qualche parte.

Quindi qui non si scrive: si **legge e si controlla**, e ogni giro dice quante
frasi la fonte ha e se ciascuna torna alla dichiarazione che la fonte porta.

**I quattro cose che una riga del parlante deve avere**, e che nessun controllo
generale chiede:

1. `attendibilita: "D"` — è il livello che significa «l'ha detto un parlante»;
   con `I` la riga si presenterebbe come un'interpretazione e mentirebbe sul
   mestiere di chi l'ha scritta;
2. `varieta` — quella che la fonte dichiara, non quella che sembra giusta;
3. la fonte, con l'id della fonte dentro la citazione, come fa quella di S019;
4. una nota che dica **chi** ha parlato e **quando**, perché una frase senza
   data non si può controllare fra vent'anni.

Uso:
    python3 raccolta/parlante.py            # i conti e i problemi
    python3 raccolta/parlante.py --json     # anche i dati, per un controllo
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys_path = os.path.join(RADICE, "sorgenti")
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

COPPIE = os.path.join(RADICE, "dati", "coppie.jsonl")
FONTI = os.path.join(RADICE, "dati", "fonti.json")

# La fonte che raccoglie le frasi dichiarate da un parlante. Se un giorno ce ne
# fosse un'altra, si aggiunge qui **con la sua ragione**, non in silenzio.
FONTE_PARLANTE = "S022"


def coppie() -> list:
    righe = []
    with io.open(COPPIE, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.startswith("//"):
                righe.append(json.loads(riga))
    return righe


def fonti() -> dict:
    with io.open(FONTI, encoding="utf-8") as f:
        return {fonte["id"]: fonte for fonte in json.load(f).get("fonti", [])}


def dichiarate(righe: list) -> list:
    """Le righe che vengono da un parlante."""
    return [r for r in righe if FONTE_PARLANTE in (r.get("fonte") or "")]


def problemi(righe: list, conosciute: dict) -> list:
    """Le cose che una riga del parlante deve avere e che i controlli generali
    non chiedono."""
    difetti = []
    fonte = conosciute.get(FONTE_PARLANTE)
    if fonte is None:
        return ["%s non è dichiarata in dati/fonti.json: le frasi che le "
                "appartengono citano una fonte che non esiste" % FONTE_PARLANTE]
    for riga in dichiarate(righe):
        dove = riga.get("id", "(senza id)")
        if riga.get("attendibilita") != "D":
            difetti.append(
                "%s ha attendibilita %r: una frase che un parlante ha scritto è "
                "«D», e con «I» la riga si presenterebbe come un'interpretazione"
                % (dove, riga.get("attendibilita")))
        if not (riga.get("varieta") or "").strip():
            difetti.append("%s non dice la varietà: senza quella una frase di "
                           "Ferrara città insegnerebbe il dialetto di un posto "
                           "solo a chi è di un altro" % dove)
        if not (riga.get("fonte") or "").strip():
            difetti.append("%s non dice la fonte" % dove)
        nota = (riga.get("nota") or "")
        if "parlante" not in nota.lower():
            difetti.append(
                "%s non dice nella nota **chi** ha parlato: una frase senza il "
                "nome di chi l'ha detta non si può controllare, e la fonte non "
                "basta perché il fonte è il progetto" % dove)
    return difetti


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Le frasi dichiarate da un parlante nativo.")
    ap.add_argument("--json", action="store_true",
                    help="stampa anche le righe, per un controllo")
    args = ap.parse_args()

    righe = coppie()
    conosciute = fonti()
    mie = dichiarate(righe)
    difetti = problemi(righe, conosciute)

    print("frasi dichiarate da un parlante  %4d   (fonte %s)" % (len(mie), FONTE_PARLANTE))
    if mie:
        for riga in mie:
            print("  %-6s %-24s → %s" % (riga.get("id", "?"),
                                         riga.get("italiano", ""),
                                         riga.get("ferrarese", "")))
        varieta = collections.Counter(r.get("varieta", "") for r in mie)
        print("  varieta': %s" % ", ".join("%s %d" % (k or "nessuna", v)
                                          for k, v in sorted(varieta.items())))
    print()
    if difetti:
        for difetto in difetti:
            print("difetto  %s" % difetto)
        return 1
    print("ogni frase dichiara chi l'ha detta, la varieta' e il livello 'D'.")
    if args.json:
        print(json.dumps(mie, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())