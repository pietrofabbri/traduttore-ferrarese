"""Normalizzazione del testo: la base su cui ogni confronto si regge.

Il ferrarese non ha un'ortografia unica. Gli stessi testi scrivono `l'e`,
`l'è` e `l'é` per la stessa cosa, e `un` e `vun` per la stessa cosa. Qui
vivono due livelli di normalizzazione, ed è importante sapere quando si usa
l'uno e quando l'altro:

- `chiave()` e' aggressivo: tiene solo le lettere, senza accenti, senza
  punteggiatura. Serve a costruire gli indici e a fare i confronti, e serve
  anche alle coppie e ai proverbi, che arrivano da fonti diverse e non
  concordano mai sull'accento.
- `normale()` e' conservativo: scioglie solo la punteggiatura che non
  cambia la parola e unifica l'apostrofo. Serve quando la risposta torna
  addosso al lettore, e non si vuole che la risposta perda l'accento.

La regola che vale sempre: **la normalizzazione non inventa e non cancella**.
Tutto ciò che la normalizzazione perde deve restare recuperabile dal
dizionario di ripristino che essa restituisce.
"""

from __future__ import annotations

import re
import unicodedata

# L'apostrofo arriva in tre forme diverse e in un progetto con le fonti
# prese da tre editori diversi arriva in almeno cinque.
APOSTROFI = "'’ʼ´`"

_SPAZI = re.compile(r"\s+")
# Difetto vero, di questa sessione: le due espressioni erano scritte con
# l'intervallo `\u00c0-\u024f`, che finisce a U+024F. Ma l'alfabeto ferrarese
# dichiarato in `dati/regole_grammaticali.json` (fonte S015) contiene due
# lettere **fuori** da quell'intervallo: `\u0273` (U+0263) e `\u028e` (U+028E),
# la gutturale e la laterale palatale. Erano quindi trattate come
# punteggiatura e **cancellate**, e una cancellazione silenziosa in una
# chiave di confronto e' la cosa piu' pericolosa che ci sia: `\u00e0\u0273ar` e
# `\u00e0ar` diventavano la stessa chiave `aar`, quindi la ricerca del
# glossario restituiva la voce sbagliata senza dire niente.
#
# Il numero non e' un dettaglio: **908 occorrenze** di queste due lettere
# sulle 7307 coppie raccolte da S006. Sui dati gia' presenti la differenza
# e' zero, perche' il glossario del 1889 non le usa: la correzione non
# riscrive niente di esistente, smette solo di perdere quello che arriva.
#
# La forma e' `\W` con il flag unicode: tiene **qualsiasi** lettera e butta
# solo quello che non e' lettera ne' cifra. Una lista di lettere ammesse
# funziona finche' nessuno aggiunge un carattere, e il progetto perde una
# lettera dell'alfabete ogni volta che qualcuno lo fa.
_NON_PAROLA = re.compile(r"[\W_]+", re.UNICODE)
_TOKEN = re.compile(r"[^\W_]+(?:[" + APOSTROFI + r"][^\W_]+)*", re.UNICODE)

# Sostituzioni che valgono solo per il confronto. `gh'` cade, perche' il
# ferrarese scrive `ghe` e `gh'e` per la stessa cosa, ma non e' una regola
# della lingua: e' una regola della raccolta.
_SOSTITUZIONI_CONFRONTO = (
    ("gh'", "g"),
    ("ch'", "c"),
)


def _sciogli(text: str) -> str:
    for primo, secondo in _SOSTITUZIONI_CONFRONTO:
        text = text.replace(primo, secondo)
    return text


def normale(testo: str) -> str:
    """Conserva accenti e apostrofi, toglie solo la punteggiatura esterna."""
    testo = testo.strip().lower()
    for apostrofo in APOSTROFI[1:]:
        testo = testo.replace(apostrofo, APOSTROFI[0])
    testo = _sciogli(testo)
    testo = _SPAZI.sub(" ", testo)
    return testo


def chiave(testo: str) -> str:
    """Chiave di confronto: solo lettere e cifre, senza accenti."""
    testo = normale(testo)
    testo = unicodedata.normalize("NFKD", testo)
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    return _NON_PAROLA.sub("", testo)


def tokenizza(testo: str) -> list:
    """Divide in parole. L'apostrofo interno resta, perche' in ferrarese e'
    grammaticale (`l'a`, `gh'e`, `doman l'a`)."""
    testo = normale(testo)
    return _TOKEN.findall(testo)


def tokenizza_chiave(testo: str) -> list:
    """Come `tokenizza`, ma ogni token ridotto a chiave di confronto."""
    return [chiave(t) for t in tokenizza(testo) if chiave(t)]


def ripristina(token: str, originale: str) -> str:
    """Rende un token normalizzato nella forma che il lettore si aspetta."""
    if not originale:
        return token
    if any(c in unicodedata.normalize("NFKD", originale) for c in "\u00c0\u00c8\u00c9\u00d2\u00f9"):
        return originale
    return token


def frasi(testo: str) -> list:
    """Divide in frasi su `.`, `!`, `?`, `;`, seguendo i ritorni a capo."""
    parti = re.split(r"(?<=[.!?;])\s+|\n+", testo)
    return [p.strip() for p in parti if p and p.strip()]


def somiglianza(a: str, b: str) -> float:
    """Somiglianza fra due chiavi, da 0 a 1. Usa la distanza di Levenshtein
    con soglia di taglio, che per parole brevi e' piu' affidabile del solo
    prefisso comune."""
    ka, kb = chiave(a), chiave(b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    distanza = _levenshtein(ka, kb, soglia=max(1, len(kb) // 2))
    if distanza is None:
        return 0.0
    return 1.0 - distanza / max(len(ka), len(kb))


def _levenshtein(a: str, b: str, soglia: int):
    """Distanza di Levenshtein con taglio: `None` se supera `soglia`.

    Il taglio serve perche' il glossario sara' grande e il confronto
    esaustivo su tutte le coppie non scala.
    """
    if abs(len(a) - len(b)) > soglia:
        return None
    precedente = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        corrente = [i]
        minimo = i
        for j, cb in enumerate(b, 1):
            costo = 0 if ca == cb else 1
            corrente.append(
                min(precedente[j] + 1, corrente[j - 1] + 1, precedente[j - 1] + costo)
            )
            minimo = min(minimo, corrente[-1])
        if minimo > soglia:
            return None
        precedente = corrente
    return precedente[-1]