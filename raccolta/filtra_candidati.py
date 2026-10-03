#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtra l'elenco dei candidati di Ferri a quelli leggibili.

Il filtro non decide se una voce e' giusta: decide solo se si capisce cosa
l'OCR ha scritto. Una voce che si capisce puo' comunque essere sbagliata,
e quella decisione la prende una persona.

Con `--pulito` applica anche i criteri di rumore dell'OCR: i 13257 candidati
leggibili diventano 11101, di cui 2848 locuzioni. La differenza fra i due
elenchi e' tutta roba che l'OCR ha storpiato — «Assaltamént / Assaltameiy:o»,
«Sprii / fip», «Union / l'nióne» — e che nessuno deve rileggere a mano.

Uso:  python3 filtra_candidati.py lavorato/ferri_candidati.tsv [lettera] [--pulito]
"""
from __future__ import annotations

import re
import sys

VOCE = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*(?: [A-Za-zÀ-ÿ'’\-]+){0,5}$")
# Una sillaba spezzata a fine riga lascia «Ran- care»; l'unico trattino che
# si accetta e' quello fra due parole («ciao- la» non capita, ma «a- un» si).
PEZZO = re.compile(r"[a-zà-ÿ]{2,}- [a-zà-ÿ]")
RUMORE = re.compile(r"[«»*?¿¡•#%&/\\|<>^~¬°]")
# I cinque segni dell'OCR rotto, misurati sui 13257 candidati leggibili. Sono
# i punti in cui la riga contiene qualcosa che nel libro non c'era e che
# nessuno riescirebbe a indovinare: due punti e punti interrogativi dentro la
# glossa, le cifre delle note a pie' di pagina, e le lettere isolate che sono
# un'abbreviazione della categoria rimasta attaccata al testo («fip» invece
# di «pp», «sm» isolata). Ogniuno di questi scarta un pezzo di pagina, non
# una parola: e' per questo che il filtro le guarda tutte e cinque.
PUNTI = re.compile(r"[:;!?|]")
CIFRE = re.compile(r"[0-9]")
VIRGOLETTE = re.compile(r"[“”„]")
LETTERA_ISOLATA = re.compile(r"(?:^|\s)[a-zA-Z]\s")
PAROLA_RIPETUTA = re.compile(r"\b(\w{3,})\s+\1\b")


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


def pulita(glossa: str) -> bool:
    """Secondo filtro: scarta quello che l'OCR ha storpiato.

    Diversamente da `leggibile`, questo non guarda la forma della voce ma i
    segni che nel libro stampato non ci sono. «Assaltamént / Assaltameiy:o sm, ;
    aggressióne sf, secondo ideasi» e' una voce che si indovina e non si puo'
    copiare: entrare nel glossario cosi' significa mettere dentro una parola
    che nessuno ha mai scritto.

    Non e' un controllo di correttezza: una voce che passa qui puo' essere
    sbagliata lo stesso. Serve a togliere il fondo di rumore, non a garantire
    che sopra ci sia solo roba buona.
    """
    return not any(rx.search(glossa) for rx in
                   (PUNTI, CIFRE, VIRGOLETTE, LETTERA_ISOLATA, PAROLA_RIPETUTA))


def main() -> int:
    resto = [a for a in sys.argv[2:] if not a.startswith("--")]
    opzioni = {a for a in sys.argv[2:] if a.startswith("--")}
    lettera = resto[0] if resto else ""
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
            if "--pulito" in opzioni and not pulita(glossa):
                continue
            print("\t".join((pagina, voce, cat, glossa)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
