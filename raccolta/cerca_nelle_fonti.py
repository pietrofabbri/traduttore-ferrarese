#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Il ciclo di ricerca: parole italiane frequenti non coperte, e dove sono.

Il problema che questo script risolve e' di **ordine**, non di ricerca: il
glossario si riempie di parole che arrivano in ordine di fortuna — cioe' nell'ordine
in cui le fonti si incontrano. Il risultato e' un vocabolario pieno di
`scaranna` e `majàl` e senza `anno`, `giorno`, `casa`, `mangiare`, e un
gioco che chiede di far ripetere le parole di tutti i giorni si trova con un
buco proprio li'.

Quindi il ciclo parte dall'altra parte: prende le parole italiane **piu'
frequenti** e si chiede, per ognuna, se una fonte le ha gia' tradotte. Il
quadro che esce dice tre cose, e sono le tre che servono per decidere il
giro dopo:

- quante parole del metro non sono coperte, e quante sono state trovate
  adesso: il numero che si muove a ogni giro;
- **dove** e stata trovata ciascuna, per fonte: una parola trovata in una sola
  fonte e' fragile, in due fonti e' un fatto che regge;
- quali parole sono in Musacchi, che e' l'unica fonte che va dall'italiano al
  ferrarese: quelle si possono prendere subito, senza nessuna decisione.

**Quello che questo script NON fa e non puo' fare.** Non traduce e non sceglie.
Un lemma che trova in un vocabolario ferrarese-italiano non ha la traduzione
dall'italiano: ha una voce che *da* quella parola ferrarese arriva al lemma, e
le due direzioni non sono la stessa cosa. Per questo il ciclo non scrive niente
in `dati/`: lascia un conto, e la scelta la fa una persona guardando la fonte
citata accanto a ogni parola.

Uso:
    python3 raccolta/cerca_nelle_fonti.py                # il quadro
    python3 raccolta/cerca_nelle_fonti.py --limite 200   # le prime 200
    python3 raccolta/cerca_nelle_fonti.py --json         # per un altro script
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import unicodedata

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))
sys.path.insert(0, RADICE)

from traduttore.normalizza import chiave  # noqa: E402

GREZZI = os.path.join(RADICE, "raccolta", "grezzi")

# Le fonti che si possono **leggere** nel grezzo, e cioe' quelle acquisite. Una
# fonte non acquisita non si cerca qui: si cerca sul sito, e la decisione la
# prende chi guarda.
#
# `da_dire` e' l'unica direzione utile per il ciclo: le altre fonti sono
# ferrarese-italiano, quindi trovano la parola ma non la sua traduzione.
FONTI = [
    {"id": "S020", "nome": "Musacchi, italiano-ferrarese",
     "file": "musacchi_italiano_ferrarese.txt", "da_dire": True},
    {"id": "S006", "nome": "Bigoni, ferrarese-italiano",
     "file": "bigoni_ferrarese_italiano.jsonl", "da_dire": False},
    {"id": "S001", "nome": "Biondelli 1853",
     "file": "biondelli_1853.txt", "da_dire": False},
    {"id": "S005", "nome": "Ferri 1889", "file": "ferri.txt", "da_dire": False},
    {"id": "S012", "nome": "Azzi 1857", "file": "azzi_1857.txt", "da_dire": False},
    {"id": "S009", "nome": "Nannini", "file": "nannini.txt", "da_dire": False},
    {"id": "S010", "nome": "«Scrìvar e l'èàr»",
     "file": "scrivear_frares.txt", "da_dire": False},
]

# Le fonti che si consultano ma non si copiano. Qui non c'entrano i file: si
# mettono qui solo perche' il conto finale dica che sono state guardate e che
# non hanno dato niente, e un numero che non dice perche' e' un numero che
# si legge male.
CONSULTE = [
    {"id": "S021", "nome": "Al Tréb dal Tridèl (sito)",
     "perche": "le pagine si rendono con JavaScript e il sito chiede "
               "Crawl-delay 30: va consultato a mano, non a raffica"},
    {"id": "S016", "nome": "AR.PA.DIA. 2007",
     "perche": "tutti i diritti riservati: in biblioteca, non copiabile"},
]


def _testo(percorso: str) -> str:
    try:
        with io.open(percorso, encoding="utf-8") as f:
            return f.read()
    except (IOError, OSError, UnicodeDecodeError):
        return ""


def _chiavi_in(testo: str) -> set:
    """Le chiavi di tutte le parole di un testo.

    Il confronto e' fatto **sulla chiave**, cioe' senza accenti e senza
    maiuscole: `città` e `citta` sono la stessa parola per il motore, e
    cercarle come diverse produrrebbe un conto falso.
    """
    parole = re.findall(r"[A-Za-zÀ-ÿ]+", testo)
    return set(chiave(p) for p in parole if len(p) > 2)


def _copertura() -> list:
    """(lemma, frequenza) dei lemmi che il glossario non trova, per ordine.

    Il metro lo calcola `copertura.py`, che e' uno script e non un modulo del
    pacchetto: si importa dalla sua cartella e si chiamano le sue funzioni,
    `analizza` compresa, invece di riscrivere qui un metro che gia' esiste. Un
    secondo metro sarebbe un secondo numero che non combacia col primo.
    """
    sys.path.insert(0, os.path.join(RADICE, "raccolta"))
    import copertura  # noqa: E402
    glossario = copertura.Glossario.da_file(copertura.GLOSSARIO)
    if not hasattr(copertura, "carica_metro") or not hasattr(copertura,
                                                              "analizza"):
        raise SystemExit("copertura.py non ha piu' `carica_metro` e `analizza`: "
                         "questo script va aggiornato con lei.")
    esito = copertura.analizza(glossario, copertura.carica_metro())
    return [(v["lemma"], v["frequenza"]) for v in esito["mancanti"]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite", type=int, default=100,
                    help="quante parole mancanti mostrare (default 100)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(GREZZI):
        print("manca raccolta/grezzi/: le fonti si raccolgono prima.")
        return 1

    # Una volta sola per fonte: il conto e' fatto sulle chiavi, non sulle righe.
    repertori = {}
    mancanti_sul_disco = []
    for fonte in FONTI:
        testo = _testo(os.path.join(GREZZI, fonte["file"]))
        if not testo:
            mancanti_sul_disco.append(fonte["id"])
            repertori[fonte["id"]] = set()
            continue
        repertori[fonte["id"]] = _chiavi_in(testo)

    mancanti = _copertura()
    if not mancanti:
        print("Il metro non e' disponibile: mancano gli elenchi ItWaC in "
              "raccolta/grezzi/.")
        return 1

    righe = []
    for lemma, frequenza in mancanti:
        k = chiave(lemma)
        trovata_in = [f["id"] for f in FONTI if k in repertori[f["id"]]]
        righe.append({"lemma": lemma, "frequenza": frequenza,
                      "in": trovata_in,
                      "da_dire": any(f["id"] in trovata_in and f["da_dire"]
                                    for f in FONTI)})

    # L'ordine e' quello che chiede la domanda: prima le piu' frequenti. Fra due
    # parole con la stessa frequenza viene prima quella che si puo' prendere
    # subito, perche' e' lavoro gia' fatto.
    righe.sort(key=lambda r: (-r["frequenza"], not r["da_dire"]))

    if args.json:
        print(json.dumps({"mancanti": righe}, ensure_ascii=False, indent=2))
        return 0

    quante = len(mancanti)
    coperte = sum(1 for r in righe if r["in"])
    da_dire = [r for r in righe if r["da_dire"]]
    sole = [r for r in righe if len(r["in"]) == 1]

    print("parole del metro non coperte   %5d" % quante)
    print("trovate in una fonte           %5d   di cui %d in Musacchi, "
          "che si possono prendere subito" % (coperte, len(da_dire)))
    print("trovate in una sola fonte      %5d   fragili: una sola voce le "
          "porta" % len(sole))
    print()
    if mancanti_sul_disco:
        print("fonti assenti dal grezzo: %s (il conto su quelle e' zero e va "
              "dichiarato, non nascosto)" % ", ".join(mancanti_sul_disco))
        print()
    print("%-24s %9s  %s" % ("parola", "frequenza", "dove si trova"))
    for riga in righe[:args.limite]:
        dove = ", ".join(riga["in"]) if riga["in"] else "-"
        if riga["da_dire"]:
            dove = "**%s** (dall'italiano)" % dove
        print("%-24s %9d  %s" % (riga["lemma"], riga["frequenza"], dove))
    if len(righe) > args.limite:
        print("... e altre %d" % (len(righe) - args.limite))
    print()
    print("Fonti consultate a mano, senza copiare:")
    for fonte in CONSULTE:
        print("  %-9s %s" % (fonte["id"], fonte["nome"]))
        print("            %s" % fonte["perche"])
    print()
    print("Nessuna di queste righe scrive in `dati/`: il ciclo conta, e la "
          "decisione la prende")
    print("chi guarda la fonte citata accanto alla parola.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())