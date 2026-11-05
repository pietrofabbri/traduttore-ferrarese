# -*- coding: utf-8 -*-
"""Le regole di frase: una parola funzionale e la parola che la segue.

«il cane» e' `al can`, «il uomo» non si dice e «l'uomo» e' `l'òman`: l'articolo
ferrarese dipende da quello che viene dopo. Il glossario non lo sa dire, perche'
una voce e' una parola sola. Queste regole lo dicono, e vengono **solo** dalle
correzioni dei parlanti promosse da `correzioni promuovi` (una regola per
parola italiana e contesto, con le correzioni che la sostengono).

Il contesto e' la prima lettera della parola **ferrarese** che segue
(`vocale`, `consonante`), o `fine` se non c'e' (0.41). Il motore la conosce nel
secondo passaggio (`grammatica.py`), quando la frase e' gia' tradotta; se la
parola che segue non ha traduzione si guarda quella italiana, l'unica che c'e'.
La copia nella pagina e' `regolaDiFrase` in `modello.html`.
"""
from __future__ import annotations

import io
import json
import os

from . import normalizza

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "regole_frase.json")
VOCALI = "aeiouàèéìíòóùúh"

_cache = {}


def contesto(seguente: str) -> str:
    testo = normalizza.normale(seguente or "").strip()
    if not testo:
        return "fine"
    return "vocale" if testo[0] in VOCALI else "consonante"


def carica(percorso: str = None) -> dict:
    """{(parola, contesto): regola}. Un file che non c'e' e' vuoto."""
    percorso = percorso or PERCORSO
    if percorso in _cache:
        return _cache[percorso]
    regole = {}
    if os.path.exists(percorso):
        with io.open(percorso, encoding="utf-8") as f:
            for r in json.load(f).get("regole", []):
                regole[(normalizza.normale(r["italiano"]), r["contesto"])] = r
    _cache[percorso] = regole
    return regole


def cerca_contesto(parola: str, ctx: str, percorso: str = None):
    """La regola per una parola in un contesto gia' calcolato."""
    return carica(percorso).get((normalizza.normale(parola or ""), ctx))


def cerca(parola: str, seguente: str, percorso: str = None):
    return carica(percorso).get((normalizza.normale(parola or ""),
                                 contesto(seguente)))
