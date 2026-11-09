#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registra una verifica di un parlante su un insieme di voci, e la applica.

**Che cos'e' una verifica.** Un parlante ferrarese dichiara che un insieme di voci
e' ferrarese corretto. La dichiarazione si scrive in `dati/verifiche/verifiche.jsonl`,
una riga per voce, con chi, che varieta' parla, quando e **come** l'ha detto; poi la
voce nel glossario passa da `I` e `da_verificare` a `D` e verificata, e porta il
campo `verificata` che rimanda alla riga. E' l'unica strada da `I` a `D` che non
passi da un libro: una persona che dice «si', e' cosi'», con il nome e la data
(`AGENTS.md`, regola della fonetica, che qui vale per le parole).

**Gli insiemi.** Una verifica si fa su un insieme dichiarato, fissato nel momento
in cui si registra (gli id sono scritti uno per uno, quindi l'insieme non cambia se
domani cambiano le conferme):

- `conferme`: le voci confermate da un'altra fonte (`glossario._conferme`);
- `S024`: le voci di FEdetails.net.

Uso:
    python3 raccolta/registra_verifica.py --insieme conferme --chi "Pietro Fabbri" \\
        --fonte S022 --varieta cittadino --data 2026-11-09 \\
        --come "dichiarazione in blocco nella conversazione con l'assistente"
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.glossario import Glossario  # noqa: E402

GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VERIFICHE = os.path.join(RADICE, "dati", "verifiche", "verifiche.jsonl")


def insieme(nome: str) -> list:
    glossario = Glossario.da_file(GLOSSARIO)
    if nome == "conferme":
        return [v.id for v in glossario.voci if v.conferme]
    if nome.startswith("S") and nome[1:].isdigit():
        return [v.id for v in glossario.voci if "(%s)" % nome in v.fonte]
    raise SystemExit("insieme sconosciuto: %s" % nome)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Registra una verifica di un parlante.")
    ap.add_argument("--insieme", required=True)
    ap.add_argument("--chi", required=True)
    ap.add_argument("--fonte", required=True, help="la fonte che registra il parlante")
    ap.add_argument("--varieta", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--come", required=True)
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args(argv)

    ids = insieme(args.insieme)
    gia = set()
    if os.path.exists(VERIFICHE):
        with io.open(VERIFICHE, encoding="utf-8") as f:
            for riga in f:
                if riga.startswith("{"):
                    gia.add(json.loads(riga)["voce"])
    nuove = [i for i in ids if i not in gia]
    print("voci nell'insieme %s: %d, gia' verificate %d, da registrare %d"
          % (args.insieme, len(ids), len(ids) - len(nuove), len(nuove)))
    if args.prova or not nuove:
        return 0

    firma = "%s, %s (%s, %s)" % (args.data, args.chi, args.fonte, args.varieta)
    os.makedirs(os.path.dirname(VERIFICHE), exist_ok=True)
    nuovo_file = not os.path.exists(VERIFICHE)
    with io.open(VERIFICHE, "a", encoding="utf-8", newline="\n") as f:
        if nuovo_file:
            f.write("// Le verifiche dei parlanti: una riga per voce. Le scrive "
                    "raccolta/registra_verifica.py; si leggono in dati/verifiche/README.md.\n")
        for i in nuove:
            f.write(json.dumps({"voce": i, "esito": "corretta", "chi": args.chi,
                                "fonte": args.fonte, "varieta": args.varieta,
                                "data": args.data, "insieme": args.insieme,
                                "come": args.come}, ensure_ascii=False) + "\n")

    da_cambiare = set(nuove)
    righe = io.open(GLOSSARIO, encoding="utf-8").read().splitlines(True)
    cambiate = 0
    with io.open(GLOSSARIO, "w", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            if riga.startswith("{"):
                voce = json.loads(riga)
                if voce.get("id") in da_cambiare:
                    voce["attendibilita"] = "D"
                    voce["da_verificare"] = False
                    voce["verificata"] = firma
                    riga = json.dumps(voce, ensure_ascii=False) + "\n"
                    cambiate += 1
            f.write(riga)
    print("registrate %d verifiche, %d voci passate a D" % (len(nuove), cambiate))
    return 0


if __name__ == "__main__":
    sys.exit(main())
