# -*- coding: utf-8 -*-
"""I token che non sono parole, letti da un file dichiarato e non da una lista.

**Che cosa è cambiato, e perché è stato fatto così.** Le particelle erano in
due liste scritte a mano: le candidate in `raccolta/da_pronominali.py`, e il
nome della costruzione in `pronominali.py` più una copia nella pagina. Tre
posti, e in ognuno la stessa conoscenza della lingua scritta dentro il codice.

Ora c'è un file solo — `dati/tokeni.jsonl` — dove ogni particella porta il suo
ruolo, a che cosa si attacca, **la fonte che la documenta** e **la ragione per
cui è dichiarata oppure no**. Il codice non sa niente: legge. E la ragione
serve a chi legge dopo, perché «perché `ci` non è una particella?» è una
domanda che il progetto deve saper rispondere per iscritto.

**Il pericolo che questo modulo evita.** Una lista di particelle scritta in un
sorgente è una regola che nessuno ha verificato: si allunga, e ogni elemento
nuovo entra come se fosse stato documentato. Il file dati porta invece la
prova accanto — il numero di voci, la fonte, e il motivo della mancata
dichiarazione — e il controllo **F18** rifiuta una particella dichiarata senza
testimoni.

Uso:
    from traduttore import tokeni
    tokeni.dichiarate()             # ('si',)
    tokeni.costruzione("si")        # 'verbo pronominale'
    tokeni.costruzione("ne")        # '' — nessuna fonte lo dice
    tokeni.motivo("ci")             # perché `ci` non è dichiarata
"""
from __future__ import annotations

import io
import json
import os

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "tokeni.jsonl")

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
    risultato = {
        "sistema": sistema,
        "righe": righe,
        "per_token": {r.get("token", ""): r for r in righe},
    }
    if percorso == PERCORSO:
        _cache = risultato
    return risultato


def esaminate(percorso: str = PERCORSO) -> tuple:
    """Tutti i token che il file guarda, dichiarati o no."""
    car = carica(percorso)
    if car["sistema"].get("esaminate"):
        return tuple(car["sistema"]["esaminate"])
    # Senza la riga SISTEMA l'ordine delle righe basta: e' comunque il file a
    # dire quali sono, e non una lista scritta qui.
    return tuple(r.get("token", "") for r in car["righe"])


def dichiarate(percorso: str = PERCORSO) -> tuple:
    """I token che il file dichiara, e per i quali c'e' una prova."""
    return tuple(t for t in esaminate(percorso)
                 if carica(percorso)["per_token"].get(t, {}).get("dichiarata"))


def _riga(token: str, percorso: str = PERCORSO) -> dict:
    """La riga di questo token, cercata sulla **forma scritta**.

    Come in `pronominali`, il confronto non passa dalla `chiave()`: `chiave()`
    toglie gli accenti e «sì» diventerebbe «si». Qui la domanda è ancora più
    semplice — è la particella o no — ma la risposta sbagliata costa una
    traduzione falsa.
    """
    from . import normalizza
    return carica(percorso)["per_token"].get(normalizza.normale(token), {})


def dichiarata(token: str, percorso: str = PERCORSO) -> bool:
    return bool(_riga(token, percorso).get("dichiarata"))


def costruzione(token: str, percorso: str = PERCORSO) -> str:
    """Il nome della costruzione, o **stringa vuota** se nessuna fonte lo dice.

    La stringa vuota è la risposta giusta e non un errore: dichiarare un nome
    per una particella che nessuna fonte documenta sarebbe fare al posto di
    chi legge, e il progetto non lo fa ne' coi dati ne' coi messaggi.
    """
    riga = _riga(token, percorso)
    if not riga.get("dichiarata"):
        return ""
    return riga.get("costruzione", "")


def motivo(token: str, percorso: str = PERCORSO) -> str:
    """Perché il token è dichiarato, o perché non lo è. Stringa vuota se ignoto."""
    return _riga(token, percorso).get("motivo", "")


def per_la_pagina(percorso: str = PERCORSO) -> dict:
    """Ciò che la pagina deve sapere: le particelle e le loro costruzioni.

    Le particelle viaggiano **come sono scritte** e non come chiavi già
    normalizzate: la pagina le confronta con il proprio `normale()`, e se qui
    si mandasse la chiave le due copie potrebbero divergere e il confronto
    fallirebbe in silenzio — il modo peggiore in cui può fallire una pagina.
    """
    tutte = list(esaminate(percorso))
    dichiarate_ = [t for t in tutte if _riga(t, percorso).get("dichiarata")]
    return {
        "particelle": dichiarate_,
        "esaminate": tutte,
        "costruzioni": {t: _riga(t, percorso).get("costruzione", "")
                        for t in dichiarate_},
        "motivi": {t: _riga(t, percorso).get("motivo", "") for t in tutte},
    }
