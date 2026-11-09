#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porta nel glossario le «Lezioni di ferrarese-italiano» di FEdetails.net (S024).

**La fonte.** Due articoli del blog FEdetails.net, firmati Franco Colla, con un
elenco di parole ferraresi e la loro traduzione: lettera A (2 febbraio 2014) e
lettera B (22 febbraio 2014). Il blog dichiara in fondo a ogni pagina la licenza
Creative Commons Attribuzione - Non commerciale - Condividi allo stesso modo 3.0;
ogni articolo scrive «Fonte: Calendario Frarès», quindi le parole vengono da
un calendario a stampa di cui il blog e' la trascrizione (vedi `dati/fonti.json`).

**Perche' le righe sono scritte qui.** La rete della macchina di lavoro non
raggiunge il blog; le pagine sono state lette il 2026-11-09 e le righe sono
trascritte qui sotto **come la pagina le scrive**, una per riga. La divisione in
voci e' l'unica cosa fatta a mano, ed e' dichiarata nella tabella: «o» separa due
forme della stessa parola («ardanzàr o arsgianzàr»), e la riga «alta = altura.
Alta dal pozz = parapetto del pozzo» sono due voci.

Uso:
    python3 raccolta/da_fedetails.py --prova
    python3 raccolta/da_fedetails.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traduttore.normalizza import chiave  # noqa: E402
from da_bigoni import (id_in_attesa, prossimo_id, varieta_dichiarata,  # noqa: E402
                       voci_attive)

ID_FONTE = "S024"
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")
PAGINE = {
    "A": "https://www.fedetails.net/2014/02/lezioni-di-ferrarese-italiano-a.html",
    "B": "https://www.fedetails.net/2014/02/lezioni-ferarese-italiano-dialetto-ferrarese-b-ferrara.html",
}
FONTE = ("Franco Colla, «Lezioni di ferrarese-italiano», lettera %s, FEdetails.net, "
         "2014, dal Calendario Frarès (S024), %s")
NOTA = ("Trascritta dalla pagina del blog; il blog dichiara come fonte il "
        "Calendario Frarès, che non e' stato visto.")

# (lettera, riga della pagina, ferrarese, varianti, italiano)
VOCI = [
    ("A", "a bunora = di buon mattino", "a bunora", [], "di buon mattino"),
    ("A", "adaquaròla =  innaffiatoio", "adaquaròla", [], "innaffiatoio"),
    ("A", "agliadga = uva lugliatica", "agliadga", [], "uva lugliatica"),
    ("A", "aibi = abbeveratoio, beccatoio, beverino,truogolo", "aibi", [],
     "abbeveratoio, beccatoio, beverino, truogolo"),
    ("A", "alta = altura. Alta dal pozz= parapetto del pozzo", "alta", [],
     "altura"),
    ("A", "alta = altura. Alta dal pozz= parapetto del pozzo", "alta dal pozz",
     [], "parapetto del pozzo"),
    ("A", "alvadùr = lievito", "alvadùr", [], "lievito"),
    ("A", "ampulina = ampolla", "ampulina", [], "ampolla"),
    ("A", "anma = anima, seme, fondello, nocciolo, midollo", "anma", [],
     "anima, seme, fondello, nocciolo, midollo"),
    ("A", "arènt = vicino", "arènt", [], "vicino"),
    ("A", "argai = rauco", "argai", [], "rauco"),
    ("A", "armetar = rimettere", "armetar", [], "rimettere"),
    ("A", "armòcia = al riparo", "armòcia", [], "al riparo"),
    ("A", "ardanzàr o arsgianzàr = risciacquare", "ardanzàr", ["arsgianzàr"],
     "risciacquare"),
    ("A", "arsià = arso dalla sete", "arsià", [], "arso dalla sete"),
    ("A", "arslà = sellato", "arslà", [], "sellato"),
    ("A", "arsurarars = raffreddarsi", "arsurarars", [], "raffreddarsi"),
    ("A", "articiòch = carciofo", "articiòch", [], "carciofo"),
    ("A", "arzdòra = massaia", "arzdòra", [], "massaia"),
    ("A", "argùr = ramarro", "argùr", [], "ramarro"),
    ("B", "bàbi= labbro", "bàbi", [], "labbro"),
    ("B", "bacaiàr = cicalare", "bacaiàr", [], "cicalare"),
    ("B", "bach e pandon = gioco della lippa con bastoni di legno",
     "bach e pandon", [], "gioco della lippa con bastoni di legno"),
    ("B", "badèch = accidente, malore", "badèch", [], "accidente, malore"),
    ("B", "bagài = bagaglio, coso, persona meschina, stentino", "bagài", [],
     "bagaglio, coso, persona meschina, stentino"),
    ("B", "bagatela = minuzia", "bagatela", [], "minuzia"),
    ("B", "bagular = traballare", "bagular", [], "traballare"),
    ("B", "bala = palla, balla, frottola, sbornia", "bala", [],
     "palla, balla, frottola, sbornia"),
    ("B", "balòsa = ballotta", "balòsa", [], "ballotta"),
    ("B", "balòta = bulbo, tuorlo", "balòta", [], "bulbo, tuorlo"),
    ("B", "baratàr = barattare, cambiare", "baratàr", [], "barattare, cambiare"),
    ("B", "barbàgul e barabàgul = bargiglio", "barbàgul", ["barabàgul"],
     "bargiglio"),
    ("B", "barbastèl = pipistrello", "barbastèl", [], "pipistrello"),
    ("B", "barsacca = borsa, cartella", "barsacca", [], "borsa, cartella"),
    ("B", "barsò = pergolato", "barsò", [], "pergolato"),
    ("B", "bataìzza = tafferuglio", "bataìzza", [], "tafferuglio"),
    ("B", "batciòsa o batciòsla = lucciola", "batciòsa", ["batciòsla"],
     "lucciola"),
    ("B", "batmur = gioco del ristornino", "batmur", [], "gioco del ristornino"),
    ("B", "batòcc = battaglio", "batòcc", [], "battaglio"),
    ("B", "bcar = macellaio", "bcar", [], "macellaio"),
    ("B", "bchin =becchino", "bchin", [], "becchino"),
    ("B", "bdòcc = pidocchio", "bdòcc", [], "pidocchio"),
]


def costruisci(attive: list, varieta: str) -> tuple:
    gia = {(chiave(v.get("ferrarese", "")),
            chiave(v.get("principale_italiano") or v.get("italiano", "").split(",")[0]))
           for v in attive}
    nostre = {chiave(v.get("ferrarese", "")) for v in attive
              if "(S024)" in v.get("fonte", "")}
    prossimo = max(prossimo_id(attive), id_in_attesa() + 1)
    righe, concordanze = [], []
    for lettera, riga, fe, varianti, it in VOCI:
        principale = it.split(",")[0].strip()
        k = (chiave(fe), chiave(principale))
        if chiave(fe) in nostre:
            continue
        if k in gia:
            concordanze.append(fe)
            continue
        righe.append({
            "id": "V%04d" % prossimo, "varieta": varieta, "ferrarese": fe,
            "italiano": it, "principale_italiano": principale,
            "varianti": varianti, "campo": "",
            "note": NOTA + " Riga della pagina: «%s»." % riga,
            "fonte": FONTE % (lettera, PAGINE[lettera]),
            "attendibilita": "I", "da_verificare": True,
        })
        prossimo += 1
    return righe, concordanze


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="FEdetails.net, lettere A e B.")
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args(argv)
    varieta = varieta_dichiarata(VARIETA, ID_FONTE).get("varieta")
    righe, concordanze = costruisci(voci_attive(GLOSSARIO), varieta)
    print("righe della fonte        %d" % len(VOCI))
    print("concordanze              %d  %s" % (len(concordanze), ", ".join(concordanze)))
    print("nuove                    %d" % len(righe))
    if args.prova or not righe:
        return 0
    with io.open(GLOSSARIO, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
