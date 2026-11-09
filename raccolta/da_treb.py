#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le parole del Tréb dal Tridèl (S011, S025) nel glossario.

**Le fonti.** Due testi dell'associazione Al Tréb dal Tridèl, allegati dal titolare
del progetto il 2026-11-09 (copia in `raccolta/grezzi/s011/` e `s025/`, non
tracciata):

- S011, «Scrìvar e lèźar al fraréś – dó o tré pìlul ad gramàtica»: la grafia del
  ferrarese proposta da chi ha compilato i lavori di Baiolini e Guidetti;
- S025, «Tréb dal tridèl – Storie dei nostri dialetti», a cura di Floriana
  Guidetti: origini ed evoluzione del dialetto.

**Che cosa entra.** Solo le parole che il testo scrive **con la traduzione
accanto** («àśan asino», «cuóśar cuocere»). Le parole citate come esempio di un
suono senza dire che cosa vogliono dire («sćich», «chèrla») non entrano, e
nemmeno le forme verbali coniugate («curéva»), che non sono voci. Le forme sono
scritte come le scrive la fonte, con il suo alfabeto (ś ź ć ǵ η î): il glossario
le legge nella grafia unica (`grafia.treb_a_bigoni`), e la forma della fonte resta.

Uso:
    python3 raccolta/da_treb.py --prova
    python3 raccolta/da_treb.py
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

from traduttore import grafia  # noqa: E402
from traduttore.normalizza import chiave  # noqa: E402
from da_bigoni import (id_in_attesa, prossimo_id, varieta_dichiarata,  # noqa: E402
                       voci_attive)

GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")
FONTI = {
    "S011": "Al Tréb dal Tridèl, «Scrìvar e lèźar al fraréś – dó o tré pìlul ad "
            "gramàtica» (S011), %s",
    "S025": "Floriana Guidetti (a cura di), «Tréb dal tridèl – Storie dei nostri "
            "dialetti» (S025), %s",
}

# (fonte, sezione, ferrarese come la fonte lo scrive, italiano)
VOCI = [
    # S011, 1) la S
    ("S011", "1) la S", "os", "osso"),
    ("S011", "1) la S", "sal", "sale"),
    ("S011", "1) la S", "pasàr", "passare"),
    ("S011", "1) la S", "siàr", "sciare"),
    ("S011", "1) la S", "sém", "scemo"),
    ("S011", "1) la S", "pés", "pesce"),
    ("S011", "1) la S", "sìmia", "scimmia"),
    ("S011", "1) la S", "àśan", "asino"),
    ("S011", "1) la S", "śèrb", "acerbo"),
    ("S011", "1) la S", "fuś", "fuso"),
    # 2) la Z
    ("S011", "2) la Z", "zùcar", "zucchero"),
    ("S011", "2) la Z", "zucàr", "campo di zucche"),
    ("S011", "2) la Z", "zént", "cento"),
    ("S011", "2) la Z", "piz", "pizzo"),
    ("S011", "2) la Z", "mazàr", "ammazzare"),
    ("S011", "2) la Z", "źént", "gente"),
    ("S011", "2) la Z", "rùźan", "sporco"),
    ("S011", "2) la Z", "mèź", "mezzo"),
    # 3) la C
    ("S011", "3) la C", "cà", "casa"),
    ("S011", "3) la C", "scòla", "scuola"),
    ("S011", "3) la C", "cuna", "culla"),
    ("S011", "3) la C", "cépa", "scappellotto"),
    ("S011", "3) la C", "cino", "cinema"),
    ("S011", "3) la C", "póc", "poco"),
    ("S011", "3) la C", "séc", "secco"),
    ("S011", "3) la C", "patéć", "ciabatte"),
    ("S011", "3) la C", "cuć", "urto"),
    ("S011", "3) la C", "sćèt", "schietto"),
    ("S011", "3) la C", "sćirlàr", "cigolare"),
    ("S011", "3) la C", "sćiàr", "secchiaio"),
    ("S011", "3) la C", "misćiàr", "mescolare"),
    ("S011", "3) la C", "masć", "maschio"),
    # 4) la G
    ("S011", "4) la G", "gat", "gatto"),
    ("S011", "4) la G", "góz", "goccio"),
    ("S011", "4) la G", "gucia", "ago"),
    ("S011", "4) la G", "gèst", "gesto"),
    ("S011", "4) la G", "gir", "giro"),
    ("S011", "4) la G", "mag", "mago"),
    ("S011", "4) la G", "fóg", "fuoco"),
    ("S011", "4) la G", "maǵ", "maggio"),
    ("S011", "4) la G", "curàǵ", "coraggio"),
    # 5) la N
    ("S011", "5) la N", "cuna", "culla"),
    ("S011", "5) la N", "nav", "nave"),
    ("S011", "5) la N", "nona", "nonna"),
    ("S011", "5) la N", "pan", "panno"),
    ("S011", "5) la N", "paη", "pane"),
    ("S011", "5) la N", "putìη", "bambino"),
    ("S011", "5) la N", "maη", "mano"),
    ("S011", "5) la N", "béη", "bene"),
    ("S011", "5) la N", "savóη", "sapone"),
    ("S011", "5) la N", "iηnamurà", "innamorato"),
    ("S011", "5) la N", "pann", "lentiggini"),
    ("S011", "5) la N", "putìnn", "bambine"),
    ("S011", "5) la N", "paròl", "paiolo"),
    ("S011", "5) la N", "paròll", "parole"),
    # le vocali
    ("S011", "le vocali e, o", "stéla", "stella"),
    ("S011", "le vocali e, o", "pél", "pelo"),
    ("S011", "le vocali e, o", "fóra", "fuori"),
    ("S011", "le vocali e, o", "fió", "figli"),
    ("S011", "le vocali e, o", "èrba", "erba"),
    ("S011", "le vocali e, o", "pèl", "pelle"),
    ("S011", "le vocali e, o", "fiòl", "figlio"),
    ("S011", "le vocali e, o", "còmad", "comodo"),
    # Trascrizione dei vocaboli
    ("S011", "Trascrizione dei vocaboli", "fòs", "fosso"),
    ("S011", "Trascrizione dei vocaboli", "mètar", "metro"),
    ("S011", "Trascrizione dei vocaboli", "tòr", "toro"),
    ("S011", "Trascrizione dei vocaboli", "fóś", "foce"),
    ("S011", "Trascrizione dei vocaboli", "métar", "mettere"),
    ("S011", "Trascrizione dei vocaboli", "sól", "sole"),
    ("S011", "Trascrizione dei vocaboli", "tór", "prendere"),
    ("S011", "Trascrizione dei vocaboli", "cafè", "caffè"),
    ("S011", "Trascrizione dei vocaboli", "lugà", "nascosto"),
    ("S011", "Trascrizione dei vocaboli", "purtàr", "portare"),
    ("S011", "Trascrizione dei vocaboli", "santìr", "sentire"),
    ("S011", "Trascrizione dei vocaboli", "sustégn", "sostegno"),
    ("S011", "Trascrizione dei vocaboli", "amór", "amore"),
    ("S011", "Trascrizione dei vocaboli", "córar", "correre"),
    ("S011", "Trascrizione dei vocaboli", "cavàl", "cavallo"),
    ("S011", "Trascrizione dei vocaboli", "àltar", "altro"),
    ("S011", "Trascrizione dei vocaboli", "altàr", "altare"),
    ("S011", "Trascrizione dei vocaboli", "càvar", "capre"),
    ("S011", "Trascrizione dei vocaboli", "cavàr", "levare"),
    ("S011", "Trascrizione dei vocaboli", "sacà", "quanto sta in un sacco"),
    ("S011", "Trascrizione dei vocaboli", "ssacà", "colpo dato con un sacco"),
    ("S011", "Trascrizione dei vocaboli", "balìnn", "palline"),
    ("S011", "Trascrizione dei vocaboli", "madònn", "madonne"),
    ("S011", "Trascrizione dei vocaboli", "mòll", "molle"),
    ("S011", "Trascrizione dei vocaboli", "sbavźòll", "folate di vento"),
    ("S011", "Trascrizione dei vocaboli", "biétul", "bietole"),
    ("S011", "Trascrizione dei vocaboli", "fràgul", "fragole"),
    ("S011", "Trascrizione dei vocaboli", "màśan", "macine"),
    ("S011", "Trascrizione dei vocaboli", "zìlî", "ciglio"),
    ("S011", "Trascrizione dei vocaboli", "cuηsòrzî", "consorzio"),
    ("S011", "Trascrizione dei vocaboli", "priηzìpî", "principio"),
    ("S011", "Trascrizione dei vocaboli", "ebrèî", "ebreo"),
    ("S011", "Trascrizione dei vocaboli", "àj", "aglio"),
    ("S011", "Trascrizione dei vocaboli", "formàj", "formaggio"),
    ("S011", "Trascrizione dei vocaboli", "tàj", "taglio"),
    ("S011", "Trascrizione dei vocaboli", "bùjar", "bollire"),
    ("S011", "Trascrizione dei vocaboli", "majóη", "maglione"),
    ("S011", "Trascrizione dei vocaboli", "mujér", "moglie"),
    ("S011", "Trascrizione dei vocaboli", "paja", "paglia"),
    ("S011", "Trascrizione dei vocaboli", "braja", "braglia"),
    ("S011", "Trascrizione dei vocaboli", "maja", "maglia"),
    ("S011", "Trascrizione dei vocaboli", "barbiér", "barbiere"),
    ("S011", "Trascrizione dei vocaboli", "cuóśar", "cuocere"),
    # simboli
    ("S011", "Trascrizione fonetica, simboli", "cuèrć", "coperchio"),
    ("S011", "Trascrizione fonetica, simboli", "camìśa", "camicia"),
    ("S011", "Trascrizione fonetica, simboli", "viljàch", "vigliacco"),
    # le sillabe
    ("S011", "Le sillabe", "fundàr", "affondare"),
    ("S011", "Le sillabe", "ròśla", "rosolaccio"),
    ("S011", "Le sillabe", "mźéta", "mezzetta"),
    ("S011", "Le sillabe", "mrénda", "merenda"),
    ("S011", "Le sillabe", "puśizióη", "posizione"),
    # osservazioni
    ("S011", "Osservazioni", "fiéza", "feccia"),
    ("S011", "Osservazioni", "quèl", "cosa"),
    ("S011", "Osservazioni", "tór", "torre"),
    # S025, i dittonghi
    ("S025", "i dittonghi ié e uó", "famié", "famiglia"),
    ("S025", "i dittonghi ié e uó", "vié", "via"),
    ("S025", "i dittonghi ié e uó", "fradié", "fratelli"),
    ("S025", "i dittonghi ié e uó", "liévar", "lepre"),
    ("S025", "i dittonghi ié e uó", "fiévra", "febbre"),
    ("S025", "i dittonghi ié e uó", "spiéra", "piccolo raggio di luce"),
    ("S025", "i dittonghi ié e uó", "piégura", "pecora"),
    ("S025", "i dittonghi ié e uó", "buóra", "bora"),
    ("S025", "i dittonghi ié e uó", "stuóra", "stuoia"),
    ("S025", "i dittonghi ié e uó", "buó", "buoi"),
    ("S025", "i dittonghi ié e uó", "cuósa", "coscia"),
    # le zone
    ("S025", "le zone; un papavero", "papàvar", "papavero"),
    ("S025", "le zone; un papavero", "pupla", "papavero"),
    # altri elementi
    ("S025", "altri elementi caratteristici", "adménga", "domenica"),
    ("S025", "altri elementi caratteristici", "sgnór", "signore"),
    ("S025", "altri elementi caratteristici", "sgnùr", "signori"),
    ("S025", "altri elementi caratteristici", "bóη", "buono"),
    ("S025", "altri elementi caratteristici", "buη", "buoni"),
    ("S025", "altri elementi caratteristici", "póm", "mela"),
    ("S025", "altri elementi caratteristici", "pum", "mele"),
    ("S025", "altri elementi caratteristici", "caplét", "cappelletto"),
    ("S025", "altri elementi caratteristici", "caplìt", "cappelletti"),
    ("S025", "la metatesi", "cranvàl", "carnevale"),
    ("S025", "la metatesi", "falìva", "favilla"),
    ("S025", "la metatesi", "grilànda", "ghirlanda"),
    ("S025", "la metatesi", "alvàr", "levare"),
    ("S025", "la metatesi", "armór", "rumore"),
    ("S025", "la metatesi", "ruvìna", "rovina"),
    ("S025", "la metatesi", "arvinàz", "rovinaccio"),
    ("S025", "la metatesi", "ardùśar", "ridurre"),
    ("S025", "la metatesi", "lèźar", "leggere"),
    ("S025", "la metatesi", "amdàia", "medaglia"),
    ("S025", "la metatesi", "anvód", "nipote"),
    ("S025", "la metatesi", "admàη", "domani"),
    ("S025", "la metatesi", "iηquó", "oggi"),
    ("S025", "e nel Medio Evo", "àib", "trogolo"),
    ("S025", "e nel Medio Evo", "vita", "schiena"),
    ("S025", "storie di parole, stlà", "stuf stlà", "stanco morto"),
    ("S025", "storie di parole, stlà", "stlàr", "rompere"),
    ("S025", "storie di parole, stlà", "stlà", "rotto"),
    ("S025", "storie di parole, stlà", "màgar stlà", "magro stellato"),
    ("S025", "storie di parole, stlà", "stèla", "listella"),
    ("S025", "storie di parole, stlà", "stéla", "stella"),
    ("S025", "storie di parole, manì", "manì", "costretto"),
    ("S025", "cartina di mela-pom", "pér", "pere"),
]


def costruisci(attive: list, varieta: dict) -> tuple:
    def k(fe, it):
        return (chiave(grafia.da_bigoni(grafia.treb_a_bigoni(fe))), chiave(it))
    gia = set()
    for v in attive:
        fe = v.get("ferrarese", "")
        if grafia.e_del_treb(v.get("fonte", "")):
            fe = grafia.da_bigoni(grafia.treb_a_bigoni(fe))
        elif grafia.e_di_bigoni(v.get("fonte", "")):
            fe = grafia.da_bigoni(fe)
        gia.add((chiave(fe), chiave(v.get("principale_italiano") or
                                     v.get("italiano", "").split(",")[0])))
    nostre = {(chiave(v.get("ferrarese", "")), chiave(v.get("italiano", "")))
              for v in attive if grafia.e_del_treb(v.get("fonte", ""))}
    prossimo = max(prossimo_id(attive), id_in_attesa() + 1)
    righe, concordanze, viste = [], [], set()
    for fonte, sezione, fe, it in VOCI:
        if (chiave(fe), chiave(it)) in nostre or (fe, it) in viste:
            continue
        viste.add((fe, it))
        # Una parola che un'altra fonte da' uguale **entra lo stesso**: e' una
        # fonte in piu' che la attesta, e la conferma fra fonti
        # (`glossario._conferme`) la conta. Il conto dice quante sono.
        if k(fe, it) in gia:
            concordanze.append("%s = %s" % (fe, it))
        righe.append({
            "id": "V%04d" % prossimo, "varieta": varieta[fonte],
            "ferrarese": fe, "italiano": it, "principale_italiano": it,
            "varianti": [], "campo": "",
            "note": "Scritta nell'alfabeto della fonte (ś ź ć ǵ η sono s, z, c, "
                    "g dolci e n velare): il glossario la legge nella grafia "
                    "del progetto.",
            "fonte": FONTI[fonte] % ("sezione «%s»" % sezione),
            "attendibilita": "I", "da_verificare": True,
        })
        prossimo += 1
    return righe, concordanze


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Il Tréb dal Tridèl (S011, S025).")
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args(argv)
    varieta = {f: varieta_dichiarata(VARIETA, f).get("varieta") for f in FONTI}
    righe, concordanze = costruisci(voci_attive(GLOSSARIO), varieta)
    print("righe della fonte   %d" % len(VOCI))
    print("gia' date da un'altra fonte (entrano e la confermano)  %d"
          % len(concordanze))
    print("nuove               %d" % len(righe))
    if args.prova or not righe:
        return 0
    with io.open(GLOSSARIO, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
