#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porta il lotto di `lettura_ferri.py` dentro `dati/glossario.jsonl`.

Lo script fa tre cose e non una quarta: cerca il numero di pagina della voce
nel file dei candidati, controlla che la voce non ci sia gia', e scrive la
riga. Non corregge, non deduce, non sceglie: se la chiave non la trova,
la segnala e si ferma, perche' una pagina inventata in un campo `fonte` e'
peggio di una voce che non entra.

Uso:
    python3 costruisci_da_ferri.py            # controlla e scrive
    python3 costruisci_da_ferri.py --prova    # controlla e non scrive
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lettura_ferri import LOCUZIONI  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATI = os.path.join(RADICE, "raccolta", "lavorato", "ferri_candidati.tsv")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")

AUTORE = "Luigi Ferri"
OPERA = "Vocabolario ferrarese-italiano"
ANNO = 1889

# Come si cerca una voce nel file dei candidati: minuscole, spazi ridotti a uno,
# accenti tenuti. Serve a non litigare con la grafia dell'OCR.
SPAZI = re.compile(r"\s+")


def chiave(s: str) -> str:
    return SPAZI.sub(" ", s.strip().lower())


def carica_pagine(percorso: str) -> dict:
    """Voce normalizzata -> numero di pagina."""
    pagine = {}
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            campi = riga.rstrip("\n").split("\t")
            if len(campi) < 4:
                continue
            pagina, voce = campi[0], campi[1]
            if not pagina.isdigit() or int(pagina) <= 0:
                continue
            pagine.setdefault(chiave(voce), int(pagina))
    return pagine


def voci_esistenti(percorso: str) -> set:
    esistenti = set()
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.startswith("//"):
                continue
            esistenti.add(chiave(json.loads(riga)["ferrarese"]))
    return esistenti


def prossimo_id(percorso: str, prefisso: str) -> int:
    maggiore = 0
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.startswith("//"):
                continue
            ident = json.loads(riga).get("id", "")
            if ident.startswith(prefisso) and ident[1:].isdigit():
                maggiore = max(maggiore, int(ident[1:]))
    return maggiore + 1


def principale(italiano: str) -> str:
    """La resa singola, per il campo che il gioco usa."""
    return italiano.split(",")[0].split(";")[0].strip()


def main() -> int:
    solo_prova = "--prova" in sys.argv
    pagine = carica_pagine(CANDIDATI)
    esistenti = voci_esistenti(GLOSSARIO)
    prossimo = prossimo_id(GLOSSARIO, "V")

    problemi = []
    righe = []
    viste = set()

    for riga_letta in LOCUZIONI:
        chiave_voce, ferrarese, italiano, campo, attendibilita, nota = riga_letta[:6]
        varianti = riga_letta[6] if len(riga_letta) > 6 else []
        k = chiave(chiave_voce)
        pagina = pagine.get(k)
        if pagina is None:
            problemi.append("pagina non trovata per %r" % chiave_voce)
            continue
        if k in esistenti or k in viste:
            problemi.append("voce gia' presente: %r" % ferrarese)
            continue
        viste.add(k)
        fonte = "%s, %s, %d, pag. %d" % (AUTORE, OPERA, ANNO, pagina)
        riga = {
            "id": "V%04d" % prossimo,
            "varieta": "cittadino",
            "ferrarese": ferrarese,
            "italiano": italiano,
            "principale_italiano": principale(italiano),
            "varianti": list(varianti),
            "campo": campo,
            "note": nota,
            "fonte": fonte,
            "attendibilita": attendibilita,
            "da_verificare": attendibilita != "D",
        }
        prossimo += 1
        righe.append(riga)

    for problema in problemi:
        print("PROBLEMA: %s" % problema)
    print("candide %d, nuove %d, scartate %d"
          % (len(LOCUZIONI), len(righe), len(LOCUZIONI) - len(righe) - len(problemi)))
    if problemi:
        return 1
    if solo_prova:
        for riga in righe[:5]:
            print(json.dumps(riga, ensure_ascii=False))
        return 0

    with open(GLOSSARIO, "a", encoding="utf-8") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci in dati/glossario.jsonl" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())