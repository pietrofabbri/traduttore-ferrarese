#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtra l'elenco dei candidati di Ferri a quelli leggibili.

Il filtro non decide se una voce e' giusta: decide solo se si capisce cosa
l'OCR ha scritto. Una voce che si capisce puo' comunque essere sbagliata,
e quella decisione la prende una persona.

Uso:  python3 filtra_candidati.py lavorato/ferri_candidati.tsv [lettera]
"""
from __future__ import annotations

import re
import sys

VOCE = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*(?: [A-Za-zÀ-ÿ'’\-]+){0,5}$")
# Una sillaba spezzata a fine riga lascia «Ran- care»; l'unico trattino che
# si accetta e' quello fra due parole («ciao- la» non capita, ma «a- un» si).
PEZZO = re.compile(r"[a-zà-ÿ]{2,}- [a-zà-ÿ]")
RUMORE = re.compile(r"[«»*?¿¡•#%&/\\|<>^~¬°]")


def leggibile(voce: str, glossa: str) -> bool:
    if not VOCE.match(voce):
        return False
    if PEZZO.search(glossa):
        return False
    if RUMORE.search(glossa):
        return False
    # La glossa non deve essere una frase del libro («si usa col verbo...»).
    if re.search(r"\b(che |quando |perche |come |dicesi |per lo |la quale|dove si)\b", glossa):
        return False
    return 3 <= len(glossa) <= 90


def main() -> int:
    lettera = sys.argv[2] if len(sys.argv) > 2 else ""
    with open(sys.argv[1], encoding="utf-8") as f:
        for riga in f:
            campi = riga.rstrip("\n").split("\t")
            if len(campi) < 4:
                continue
            pagina, voce, cat, glossa = campi[0], campi[1], campi[2], "\t".join(campi[3:])
            if not voce.lower().startswith(lettera):
                continue
            if not leggibile(voce, glossa):
                continue
            print("\t".join((pagina, voce, cat, glossa)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
