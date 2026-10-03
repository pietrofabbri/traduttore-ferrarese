#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estrae i candidati da «Vocabolario ferrarese-italiano» (Ferri, 1889).

Lo script NON scrive nel glossario: produce un elenco di candidati da leggere.
Il testo e' l'OCR del testo di archive.org, quindi ogni candidato porta un
giudizio di leggibilita' e va rivisto da una persona prima di entrare nei dati.

Uso:  python3 estrai_ferri.py grezzi/ferri.txt > lavorato/ferri_candidati.tsv
"""
from __future__ import annotations

import re
import sys
import unicodedata

# Le abbreviazioni sono quelle stampate dal Ferri nella sua pagina delle
# abbreviazioni. L'OCR le rovina («sm.» diventa «snt.» o «sm,»), quindi il
# confronto e' tollerante di due errori, non esatto.
CATEGORIE = [
    "sens. fig", "sens. prop", "m. avv", "t.ecc", "t.gram", "vsemp",
    "acc", "agg", "ariL", "arn", "avv", "avvil", "com", "cong", "dim",
    "dispr", "ecc", "esc", "franc", "geog", "geom", "gram", "int", "lett",
    "pegg", "pl", "pp", "prep", "pron", "prov", "sens", "sf", "sing",
    "sm", "sost", "sup", "t", "va", "vdif", "vezz", "vn", "vr",
]

PULISCI = re.compile(r"[ \t]+")
INIZIO = re.compile(r"^(?:»|«|—|\*|/|\d+|\.\s)?\s*([A-ZÀ-Þ][^=]*?)\s+[-–]\s+")
# Sotto-elenco dentro una voce:  » Abitante di città - Cittadino
SOTTOLISTA = re.compile(r"(?:^|\.\s|,\s)\s*(?:»|«|—|\*|\d+[.)]?)\s+([A-ZÀ-Þ][\w'À-ÿ\- ]{1,40}?)\s+[-–]\s+")
PRIMO_TOKEN = re.compile(r"^\**\s*([A-Za-z][A-Za-z\.]{0,9})[.,]\s")
APPENDICE = re.compile(r"^APPENDICE$|CORREZIONI\s+ED\s+A", re.IGNORECASE)
SPAZZO = re.compile(r"[\*\^•#¡¿¬°©®]+")


def distanza(a: str, b: str) -> int:
    """Distanza di Levenshtein, solo per stringhe corte."""
    if a == b:
        return 0
    precedente = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        corrente = [i]
        for j, cb in enumerate(b, 1):
            corrente.append(min(corrente[-1] + 1, precedente[j] + 1,
                                precedente[j - 1] + (ca != cb)))
        precedente = corrente
    return precedente[-1]


def categoria_vera(token: str):
    """La categoria piu' vicina, se il token e' abbastanza simile.

    Il punto dopo l'abbreviazione e' obbligatorio: e' lui che distingue
    «sm.» (sostantivo) da una parola che comincia per «sm» come «smuovere».
    Senza il punto la vicinaza' sbaglia di mezzo passo e parola un aggettivo.
    """
    t = token.lower().rstrip(".")
    if len(t) < 2:
        return None
    migliore = None
    for cat in CATEGORIE:
        d = distanza(t, cat)
        if d <= (2 if len(t) >= 5 else 1) and (migliore is None or (d, len(cat)) < (migliore[1], len(migliore[0]))):
            migliore = (cat, d)
    return migliore[0] if migliore else None


def stacca_categoria(testo: str):
    m = PRIMO_TOKEN.match(testo)
    if m:
        cat = categoria_vera(m.group(1))
        if cat:
            resto = testo[m.end():].lstrip("-–—•* ").strip()
            if resto:
                return cat, resto
    return "", testo.strip()


def intestazione(riga: str):
    m = INIZIO.match(riga)
    if not m:
        return None
    voce = m.group(1).strip()
    if len(voce) > 40 or re.search(r"\d", voce) or not re.search(r"[a-zà-ÿ]", voce):
        return None
    return voce, riga[m.end():].strip()


def ripulisci(t: str) -> str:
    t = SPAZZO.sub(" ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .,;:")


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as f:
        righe = PULISCI.sub(" ", f.read().replace("\r", "\n")).split("\n")

    # Il numero di pagina stampato arriva da solo, e ogni tanto l'OCR lo
    # sbaglia («241» letto «541»). Si prende l'ultimo numero incontrato e non
    # il massimo: il massimo sbaglierebbe tutto il resto del libro. E' una
    # stima dichiarata, non una certezza.
    #
    # Il libro finisce con l'«Appendice correzioni ed aggiunte», dove il
    # Ferri lascia il significato in bianco («(aggiungi)»): da li' in poi non
    # c'e' niente da prendere, e il numero di pagina finisce con «48;».
    grezzi = []
    corrente = None
    pagina = 0
    for riga in righe:
        if not riga.strip():
            continue
        if APPENDICE.search(riga):
            break
        m = re.fullmatch(r"\s*(\d{1,3})\s*", riga)
        if m:
            n = int(m.group(1))
            # Il libro avanza di poche pagine per volta: un numero che salta
            # in avanti di trenta non e' una pagina, e' una lettura sbagliata
            # dell'OCR. Fuori da quella finestra il numero si ignora e la
            # pagina resta quella dichiarata prima.
            if pagina <= n <= pagina + 12:
                pagina = n
            continue
        cand = intestazione(riga)
        if cand:
            corrente = [cand[0], cand[1], pagina]
            grezzi.append(corrente)
        elif corrente is not None:
            corrente[1] += " " + riga.strip()

    for voce, corpo, pagina in grezzi:
        parti = [(voce, corpo)]
        for m in SOTTOLISTA.finditer(" " + corpo):
            if m.start() > 0:
                parti[-1] = (parti[-1][0], corpo[:m.start()])
                parti.append((m.group(1), corpo[m.end():]))
        for v, c in parti:
            cat, glossa = stacca_categoria(c)
            glossa = ripulisci(glossa)
            v = ripulisci(v)
            if not glossa or not v:
                continue
            print("\t".join((str(pagina), v, cat, glossa)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
