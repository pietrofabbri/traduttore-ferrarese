#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La grammatica di Beniamino Biolcati (S027) entra nei dati: verbi e regole.

**La fonte.** Beniamino Biolcati, «Lèzar e scrìvar. Grammatica del dialetto
ferrarese», Casa Editrice ALBA, Ferrara 1980 (finito di stampare nell'ottobre
1980). L'autore, nato a Codigoro nel 1910 e da vent'anni a Ferrara, dichiara di
essersi «attenuto alla parlata delle zone più vicine a Ferrara e in particolare
al vocabolario del Ferri» (pag. 9): e' ferrarese cittadino.

**Che cosa se ne prende, e che cosa no.** Il libro e' protetto (tutti i diritti
riservati) e non entra nel repository. Come per S016 (`dati/fonti.json`): si
consulta e si cita. Entrano i **fatti linguistici** — le forme dei paradigmi
verbali, i participi passati, le preposizioni articolate, la regola della
negazione e le forme interrogative — ognuno con la pagina, e con una citazione
breve quanto basta a ritrovarlo sul libro. Il testo del libro no.

**Come e' stato letto.** La copia e' una scansione (92 immagini di pagine
doppie, consegnata dal titolare del progetto il 2026-11-17). Le tabelle sono
state trascritte guardando le immagini, non dall'OCR, che sulle tabelle sbaglia
(«vuasi» per «vu a si»). Ogni casella qui sotto e' scritta come la stampa la
scrive, con le parentesi: il generatore la scompone e non la corregge.

**Le scelte dichiarate.**

- «lav(i)»: la desinenza fra parentesi della seconda singolare. L'autore dice
  (pag. 109) che nel contado si usa la forma in consonante e «nell'area
  cittadina e nelle zone limitrofe al Veneto» quella in -i: il progetto e'
  cittadino, quindi la forma principale e' quella in -i e l'altra e' la
  variante.
- «Mi a jò (a j-ho)»: le forme fra parentesi staccate sono le varianti meno
  usate (pag. 52 e 97, «tra parentesi le forme meno usate»). Entrano come
  varianti; quelle con il trattino («j-ho»), che sono un modo di scrivere e non
  un'altra forma, no.
- I verbi irregolari (pag. 145-150) sono elencati senza persona e solo nelle
  forme che cambiano: «Andàr: Indicativo Presente = vagh, va, andén, andè, va».
  Le persone si leggono dall'ordine della tabella completa di «vlér» (sei forme:
  «vói, vo', vòl, vlén, vli, vòl»); quando le forme sono meno di sei la riga
  dice quali persone porta, nel campo `persone` di `IRREGOLARI`, e non ne
  aggiunge altre. La proclitica e' quella dei paradigmi (pag. 104).
- Un refuso evidente non si corregge: «nu a pertén» (pag. 128, presente di
  «partìr»; l'imperativo della stessa pagina scrive «partén») resta fuori, come
  buco dichiarato (`FUORI`).

Uso:
    python3 raccolta/da_biolcati.py --prova    # mostra, non scrive
    python3 raccolta/da_biolcati.py            # scrive in dati/verbi.jsonl
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.normalizza import chiave  # noqa: E402

VERBI = os.path.join(RADICE, "dati", "verbi.jsonl")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
ID_FONTE = "S027"
LIBRO = "Biolcati, «Lèzar e scrìvar», 1980"

PRONOMI = {"mi": "1sing", "ti": "2sing", "lu": "3sing", "nu": "1plur",
           "vu": "2plur", "lór": "3plur"}
PERSONE = ("1sing", "2sing", "3sing", "1plur", "2plur", "3plur")
PROCLITICHE = ("a", "at", "al", "i", "la")
# La proclitica di ogni persona, per le forme che la fonte elenca senza (pag.
# 104: «le particelle a, at, al, la, l', a, a, i, il, gli, corrispondenti alle
# diverse persone soggetto, sono elementi essenziali»).
PROCLITICA_DI = {"1sing": "a", "2sing": "at", "3sing": "al", "1plur": "a",
                 "2plur": "a", "3plur": "i"}
VOCALI = "aeiouàèéìíòóùú"

NOMI_TEMPI = {
    "presente": "indicativo presente", "imperfetto": "indicativo imperfetto",
    "futuro": "indicativo futuro", "condizionale": "condizionale presente",
    "congiuntivo_presente": "congiuntivo presente",
    "congiuntivo_imperfetto": "congiuntivo imperfetto",
}

OMOGRAFI = {
    "dai": "e' anche la preposizione articolata «dai»",
    "sia": "e' anche la congiunzione «sia… sia»",
}

FUORI = {
    ("partìr", "presente", "1plur"):
        "la stampa scrive «nu a pertén», con la e, mentre l'imperativo della "
        "stessa pagina scrive «partén»: quasi certamente un refuso, e il "
        "progetto non scrive al suo posto una forma che la fonte non scrive",
}


def _it(testo: str) -> list:
    return testo.split()


# --- i paradigmi interi (pag. 112-131) ----------------------------------------
# Ogni tempo: (pagina, le sei caselle come le stampa il libro, l'italiano).

PARADIGMI = [
    {"lemma": "èssar", "italiano": "essere", "gruppo": "verbo ausiliare",
     "gerundio": (114, "essénd", "essendo"), "participio": (114, "stà", "stato"),
     "tempi": {
         "presente": (112, ["Mi a són", "ti at jé", "lu l'è", "nu a sén",
                            "vu a si", "lór i è"],
                      _it("sono sei è siamo siete sono")),
         "imperfetto": (112, ["Mi a jéra", "ti at jér (jéri)", "lu al jéra",
                              "nu a jéran", "vu a jéri", "lór i jéra"],
                        _it("ero eri era eravamo eravate erano")),
         "futuro": (112, ["Mi a sarò", "ti at sarà", "lu al sarà",
                          "nu a sarén", "vu a sarì", "lór i sarà"],
                    _it("sarò sarai sarà saremo sarete saranno")),
         "congiuntivo_presente": (113, ["Mi a sia", "ti at sìi", "lu al sia",
                                        "nu a ségna", "vu a sìi", "lór i sia"],
                                  _it("sia sia sia siamo siate siano")),
         "congiuntivo_imperfetto": (113, ["Mi a fuss", "ti at fuss(i)",
                                          "lu al fuss", "nu a fùssan",
                                          "vu a fussi", "lór i fuss"],
                                    _it("fossi fossi fosse fossimo foste "
                                        "fossero")),
         "condizionale": (113, ["Mi a sarév (sarìa)", "ti at sarév",
                                "lu al sarév", "nu a saréssan",
                                "vu a sarissi", "lór i sarév"],
                          _it("sarei saresti sarebbe saremmo sareste "
                              "sarebbero")),
     }},
    {"lemma": "avér", "italiano": "avere", "gruppo": "verbo ausiliare",
     "gerundio": (117, "avénd", "avendo"), "participio": (117, "avù", "avuto"),
     "tempi": {
         "presente": (115, ["Mi a jò (a j-ho)", "ti at à (a t'ha)",
                            "lu l'à (l'ha)", "nu avén (a jén)",
                            "vu avì (vu a i)", "lór i à (i ha)"],
                      _it("ho hai ha abbiamo avete hanno")),
         "imperfetto": (115, ["Mi avéva (a jéva)", "ti at avév(i) (at év(i))",
                              "lu l'avéva (l'éva)", "nu avévan (a jévan)",
                              "vu avévi (a jévi)", "lór i avéva (i éva)"],
                        _it("avevo avevi aveva avevamo avevate avevano")),
         "futuro": (115, ["Mi avrò (arò)", "ti at avrà (arà)",
                          "lu l'avrà (arà)", "nu avrén (arén)",
                          "vu avrì (arì)", "lór i avrà (arà)"],
                    _it("avrò avrai avrà avremo avrete avranno")),
         "congiuntivo_presente": (116, ["Mi àbia (ava, aba)", "ti at abi",
                                        "lu l'àbia", "nu avégna", "vu avìi",
                                        "lór i àbia"],
                                  _it("abbia abbia abbia abbiamo abbiate "
                                      "abbiano")),
         "congiuntivo_imperfetto": (116, ["Mi avéss (a jéss)",
                                          "ti at avéss (at éss)",
                                          "lu l'avéss (l'éss)",
                                          "nu avéssan (éssan)",
                                          "vu avissi (issi)",
                                          "lór i avéss (i éss)"],
                                    _it("avessi avessi avesse avessimo aveste "
                                        "avessero")),
         "condizionale": (116, ["Mi avrév (avrìa)", "ti at avrév (avréssi)",
                                "lu l'avrév (avrìa)",
                                "nu avréssan (avrìssan)", "vu avrissi",
                                "lór i avrév (avrìa)"],
                          _it("avrei avresti avrebbe avremmo avreste "
                              "avrebbero")),
     }},
    {"lemma": "lavàr", "italiano": "lavare", "gruppo": "prima coniugazione",
     "gerundio": (121, "lavànd", "lavando"), "participio": (121, "lavà", "lavato"),
     "tempi": {
         "presente": (119, ["Mi a lav", "ti at lav(i)", "lu al lava",
                            "nu a lavén", "vu a lavè", "lór i lava"],
                      _it("lavo lavi lava laviamo lavate lavano")),
         "imperfetto": (119, ["Mi a lavava", "ti at lavàv(i)", "lu al lavava",
                              "nu a lavàvan", "vu a lavavi", "lór i lavava"],
                        _it("lavavo lavavi lavava lavavamo lavavate "
                            "lavavano")),
         "futuro": (119, ["Mi a lavarò", "ti at lavarà", "lu al lavarà",
                          "nu a lavarén", "vu a lavarì", "lór i lavarà"],
                    _it("laverò laverai laverà laveremo laverete "
                        "laveranno")),
         "congiuntivo_presente": (120, ["Mi a lava", "ti at lav(i)",
                                        "lu al lava", "nu a lavégna",
                                        "vu a lavèi", "lór i lava"],
                                  _it("lavi lavi lavi laviamo laviate "
                                      "lavino")),
         "congiuntivo_imperfetto": (120, ["Mi a lavàss", "ti at lavàss(i)",
                                          "lu al lavàss", "nu a lavàssan",
                                          "vu a lavàssi", "lór i lavàss"],
                                    _it("lavassi lavassi lavasse lavassimo "
                                        "lavaste lavassero")),
         "condizionale": (120, ["Mi a lavarév (lavarìa)",
                                "ti at lavarév (lavariss(i))",
                                "lu al lavarév (lavarìa)",
                                "nu a lavaréssan (lavarissan)",
                                "vu a lavarissi (lavarissi)",
                                "lór i lavarév (lavarìa)"],
                          _it("laverei laveresti laverebbe laveremmo "
                              "lavereste laverebbero")),
     }},
    {"lemma": "rìdar", "italiano": "ridere", "gruppo": "seconda coniugazione",
     "gerundio": (124, "ridénd", "ridendo"), "participio": (124, "ridèst", "riso"),
     "tempi": {
         "presente": (122, ["Mi a rid", "ti at rid(i)", "lu al rid",
                            "nu a ridén", "vu a ridì", "lór i rid"],
                      _it("rido ridi ride ridiamo ridete ridono")),
         "imperfetto": (122, ["Mi a ridéva", "ti at ridév(i)", "lu al ridéva",
                              "nu a ridévan", "vu a ridévi", "lór i ridéva"],
                        _it("ridevo ridevi rideva ridevamo ridevate "
                            "ridevano")),
         "futuro": (122, ["Mi a ridrò", "ti at ridrà", "lu al ridrà",
                          "nu a ridrén", "vu a ridrì", "lór i ridrà"],
                    _it("riderò riderai riderà rideremo riderete "
                        "rideranno")),
         "congiuntivo_presente": (123, ["Mi a rida", "ti at rid(i)",
                                        "lu al rida", "nu a ridégna",
                                        "vu a ridìi", "lór i rida"],
                                  _it("rida rida rida ridiamo ridiate "
                                      "ridano")),
         "congiuntivo_imperfetto": (123, ["Mi a ridéss", "ti at ridéss(i)",
                                          "lu al ridéss", "nu a ridéssan",
                                          "vu a ridissi", "lór i ridéss"],
                                    _it("ridessi ridessi ridesse ridessimo "
                                        "rideste ridessero")),
         "condizionale": (123, ["Mi a ridrév (ridrìa)",
                                "ti at ridrév (ridriss(i))",
                                "lu al ridrév (ridrìa)",
                                "nu a ridréssan (ridrìssan)",
                                "vu a ridrissi (ridrissi)",
                                "lór i ridrév (ridrìa)"],
                          _it("riderei rideresti riderebbe rideremmo "
                              "ridereste riderebbero")),
     }},
    {"lemma": "finìr", "italiano": "finire",
     "gruppo": "terza coniugazione (ausiliare avere)",
     "gerundio": (127, "finénd", "finendo"), "participio": (127, "finì", "finito"),
     "tempi": {
         "presente": (125, ["Mi a finìss", "ti at finìss(i)", "lu al finìss",
                            "nu a finén", "vu a finì", "lór i finìss"],
                      _it("finisco finisci finisce finiamo finite "
                          "finiscono")),
         "imperfetto": (125, ["Mi a finiva", "ti at finìv(i)", "lu al finiva",
                              "nu a finivan", "vu a finivi", "lór i finiva"],
                        _it("finivo finivi finiva finivamo finivate "
                            "finivano")),
         "futuro": (125, ["Mi a finirò", "ti at finirà", "lu al finirà",
                          "nu a finirén", "vu a finirì", "lór i finirà"],
                    _it("finirò finirai finirà finiremo finirete "
                        "finiranno")),
         "congiuntivo_presente": (126, ["Mi a finissa", "ti at finiss(i)",
                                        "lu al finissa", "nu finégna",
                                        "vu finìi", "lór i finissa"],
                                  _it("finisca finisca finisca finiamo "
                                      "finiate finiscano")),
         "congiuntivo_imperfetto": (126, ["Mi a finìss", "ti at finìss(i)",
                                          "lu al finìss", "nu a finìssan",
                                          "vu a finìssi", "lór i finìss"],
                                    _it("finissi finissi finisse finissimo "
                                        "finiste finissero")),
         "condizionale": (126, ["Mi a finirév (finirìa)", "ti at finirév",
                                "lu al finirév", "nu a finiréssan",
                                "vu a finirissi", "lór i finirév"],
                          _it("finirei finiresti finirebbe finiremmo "
                              "finireste finirebbero")),
     }},
    {"lemma": "partìr", "italiano": "partire",
     "gruppo": "terza coniugazione (ausiliare essere)",
     "participio": (130, "partì", "partito"),
     "tempi": {
         "presente": (128, ["Mi a partìss", "ti at partìss(i)",
                            "lu al partìss", "nu a pertén", "vu a partì",
                            "lór i partìss"],
                      _it("parto parti parte partiamo partite partono")),
         "imperfetto": (128, ["Mi a partiva", "ti at partiv(i)",
                              "lu al partiva", "nu a partivan",
                              "vu a partivi", "lór i partiva"],
                        _it("partivo partivi partiva partivamo partivate "
                            "partivano")),
         "futuro": (128, ["Mi a partirò", "ti at partirà", "lu al partirà",
                          "nu a partirén", "vu a partirì", "lór i partirà"],
                    _it("partirò partirai partirà partiremo partirete "
                        "partiranno")),
         "congiuntivo_presente": (129, ["Mi a partìssa", "ti at partìss(i)",
                                        "lu al partissa", "nu a partégna",
                                        "vu a partìi", "lór i partissa"],
                                  _it("parta parta parta partiamo partiate "
                                      "partano")),
         "congiuntivo_imperfetto": (129, ["Mi a partìss", "ti at partiss(i)",
                                          "lu al partìss", "nu a partissan",
                                          "vu a partissi", "lór i partìss"],
                                    _it("partissi partissi partisse "
                                        "partissimo partiste partissero")),
         "condizionale": (129, ["Mi a partirév (partirìa)", "ti at partirév",
                                "lu al partirév", "nu a partiréssan",
                                "vu a partirissi", "lór i partirév"],
                          _it("partirei partiresti partirebbe partiremmo "
                              "partireste partirebbero")),
     }},
]

# --- i verbi irregolari (pag. 145-150) ----------------------------------------
# (lemma, infinito italiano, pagina, tempo, forme come le stampa il libro,
#  persone a cui vanno, italiano). Le persone sono dichiarate riga per riga:
#  quando la fonte elenca meno di sei forme, si scrivono solo quelle che si
#  leggono senza dubbio.

IRREGOLARI = [
    ("andàr", "andare", 145, "presente", "vagh, va, andén, andè, va",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("vado vai andiamo andate vanno")),
    ("andàr", "andare", 145, "presente", "va", ["3sing"], ["va"]),
    ("andàr", "andare", 145, "imperfetto", "andava (andaseva)", ["1sing"],
     ["andavo"]),
    ("andàr", "andare", 145, "futuro", "andrò", ["1sing"], ["andrò"]),
    ("andàr", "andare", 145, "congiuntivo_presente",
     "vaga, vagh, vaga, andégna, andèi, vaga", list(PERSONE),
     _it("vada vada vada andiamo andiate vadano")),
    ("andàr", "andare", 145, "congiuntivo_imperfetto", "andàss (andéss)",
     ["1sing"], ["andassi"]),
    ("andàr", "andare", 145, "gerundio", "andànd (andasénd)", [""],
     ["andando"]),
    ("dar", "dare", 145, "presente", "dagh, dà, dén, dè, dà",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("do dai diamo date danno")),
    ("dar", "dare", 145, "presente", "dà", ["3sing"], ["dà"]),
    ("dar", "dare", 145, "imperfetto", "dava (daséva)", ["1sing"], ["davo"]),
    ("dar", "dare", 145, "congiuntivo_presente", "daga, dagh, dégna, dèi",
     ["1sing", "2sing", "1plur", "2plur"], _it("dia dia diamo diate")),
    ("dar", "dare", 145, "congiuntivo_imperfetto", "déss, déssan",
     ["1sing", "1plur"], _it("dessi dessimo")),
    ("dar", "dare", 145, "gerundio", "dand (dasénd)", [""], ["dando"]),
    ("star", "stare", 145, "presente", "stagh, stà, stén, stè",
     ["1sing", "2sing", "1plur", "2plur"], _it("sto stai stiamo state")),
    ("star", "stare", 145, "presente", "stà", ["3sing"], ["sta"]),
    ("star", "stare", 145, "imperfetto", "stava (staséva)", ["1sing"],
     ["stavo"]),
    ("star", "stare", 145, "congiuntivo_presente",
     "staga, stagh, stégna, stèi, staga",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("stia stia stiamo stiate stiano")),
    ("star", "stare", 145, "congiuntivo_imperfetto", "stéss, stéssan",
     ["1sing", "1plur"], _it("stessi stessimo")),
    ("star", "stare", 145, "gerundio", "stand (stasénd)", [""], ["stando"]),
    ("duvér", "dovere", 147, "presente", "dév, duvén, duvì, dév",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("devo dobbiamo dovete devono")),
    ("duvér", "dovere", 147, "presente", "dév", ["3sing"], ["deve"]),
    ("duvér", "dovere", 147, "congiuntivo_presente", "déva, duvégna",
     ["1sing", "1plur"], _it("debba dobbiamo")),
    ("parér", "parere", 147, "presente", "par, parén, parì, par",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("paio pariamo parete paiono")),
    ("parér", "parere", 147, "presente", "par", ["3sing"], ["pare"]),
    ("parér", "parere", 147, "condizionale", "parrév, parréssan",
     ["1sing", "1plur"], _it("parrei parremmo")),
    ("putér", "potere", 147, "presente", "póss, po', pòl, putén (pssén), "
     "putì (pssì)", ["1sing", "2sing", "3sing", "1plur", "2plur"],
     _it("posso puoi può possiamo potete")),
    ("putér", "potere", 147, "imperfetto", "putéva (pudéva, psséva)",
     ["1sing"], ["potevo"]),
    ("putér", "potere", 147, "futuro", "putrò (pudrò, prò)", ["1sing"],
     ["potrò"]),
    ("putér", "potere", 147, "condizionale", "putrév (pudrév, pudrìa)",
     ["1sing"], ["potrei"]),
    ("putér", "potere", 147, "congiuntivo_presente",
     "póssa, póss, putégna, putì", ["1sing", "2sing", "1plur", "2plur"],
     _it("possa possa possiamo possiate")),
    ("putér", "potere", 147, "congiuntivo_imperfetto", "putéss (psséss)",
     ["1sing"], ["potessi"]),
    ("savér", "sapere", 147, "presente", "sò, sa, savén (sén), savì (sì)",
     ["1sing", "2sing", "1plur", "2plur"],
     _it("so sai sappiamo sapete")),
    ("savér", "sapere", 147, "presente", "sa", ["3sing"], ["sa"]),
    ("savér", "sapere", 147, "imperfetto", "savéva (séva)", ["1sing"],
     ["sapevo"]),
    ("savér", "sapere", 147, "congiuntivo_presente", "sapia (sava), savégna",
     ["1sing", "1plur"], _it("sappia sappiamo")),
    ("savér", "sapere", 147, "congiuntivo_imperfetto", "savéss", ["1sing"],
     ["sapessi"]),
    ("valér", "valere", 147, "presente", "val, vali, val, valén, valì, val",
     list(PERSONE), _it("valgo vali vale valiamo valete valgono")),
    ("valér", "valere", 147, "futuro", "varò", ["1sing"], ["varrò"]),
    ("valér", "valere", 147, "congiuntivo_presente",
     "vàla, vàli, valégna, valì, vala",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("valga valga valiamo valiate valgano")),
    ("valér", "valere", 147, "condizionale", "varév", ["1sing"], ["varrei"]),
    ("vlér", "volere", 148, "presente", "vói, vo', vòl, vlén, vli, vòl",
     list(PERSONE), _it("voglio vuoi vuole vogliamo volete vogliono")),
    ("vlér", "volere", 148, "imperfetto", "vléva", ["1sing"], ["volevo"]),
    ("vlér", "volere", 148, "futuro", "vrò", ["1sing"], ["vorrò"]),
    ("vlér", "volere", 148, "condizionale", "vrév, vréss, vréssan (vria)",
     ["1sing", "2sing", "1plur"], _it("vorrei vorresti vorremmo")),
    ("bévar", "bere", 148, "presente", "bév, bvén, bvi, bév",
     ["1sing", "1plur", "2plur", "3plur"], _it("bevo beviamo bevete bevono")),
    ("bévar", "bere", 148, "presente", "bév", ["3sing"], ["beve"]),
    ("bévar", "bere", 148, "imperfetto", "bvéva", ["1sing"], ["bevevo"]),
    ("bévar", "bere", 148, "futuro", "bivrò (bavrò)", ["1sing"], ["berrò"]),
    ("far", "fare", 148, "presente", "fagh (fazz), fa, fén, fè, fa",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("faccio fai facciamo fate fanno")),
    ("far", "fare", 148, "presente", "fa", ["3sing"], ["fa"]),
    ("far", "fare", 148, "imperfetto", "faséva (fava)", ["1sing"],
     ["facevo"]),
    ("far", "fare", 148, "congiuntivo_presente",
     "faga (fazza), fagh, fégna, fèi (fasì)",
     ["1sing", "2sing", "1plur", "2plur"],
     _it("faccia faccia facciamo facciate")),
    ("far", "fare", 148, "congiuntivo_imperfetto", "féss (fass)", ["1sing"],
     ["facessi"]),
    ("far", "fare", 148, "condizionale", "farév (faréss)", ["1sing"],
     ["farei"]),
    ("far", "fare", 148, "gerundio", "fasénd (fagànd)", [""], ["facendo"]),
    ("vìvar", "vivere", 148, "presente", "viv, vivén, vivì, viv",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("vivo viviamo vivete vivono")),
    ("vìvar", "vivere", 148, "presente", "viv", ["3sing"], ["vive"]),
    ("vìvar", "vivere", 148, "futuro", "vivrò", ["1sing"], ["vivrò"]),
    ("védar", "vedere", 148, "presente", "véd, vdén, vdi",
     ["1sing", "1plur", "2plur"], _it("vedo vediamo vedete")),
    ("védar", "vedere", 148, "imperfetto", "vdéva", ["1sing"], ["vedevo"]),
    ("védar", "vedere", 148, "gerundio", "vdénd", [""], ["vedendo"]),
    ("cóiar", "cogliere", 149, "presente", "cói (cùi), cuién, cuì, cói (cùi)",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("colgo cogliamo cogliete colgono")),
    ("cóiar", "cogliere", 149, "imperfetto", "cuiéva", ["1sing"],
     ["coglievo"]),
    ("cóiar", "cogliere", 149, "futuro", "cuirò", ["1sing"], ["coglierò"]),
    ("tór", "togliere", 149, "presente", "tógh, tó, tòl, tulén, tulì, tòl",
     list(PERSONE), _it("tolgo togli toglie togliamo togliete tolgono")),
    ("tór", "togliere", 149, "imperfetto", "tuléva", ["1sing"],
     ["toglievo"]),
    ("tór", "togliere", 149, "futuro", "turò", ["1sing"], ["toglierò"]),
    ("tór", "togliere", 149, "congiuntivo_presente",
     "tóga, tógh, tulégna, tulìi, tóga",
     ["1sing", "2sing", "1plur", "2plur", "3plur"],
     _it("tolga tolga togliamo togliate tolgano")),
    ("tór", "togliere", 149, "congiuntivo_imperfetto", "tuléss, tuléssan",
     ["1sing", "1plur"], _it("togliessi togliessimo")),
    ("dir", "dire", 149, "presente",
     "digh, di, dis, dgén (gén, dsén), dgi (gi, dsi), dis", list(PERSONE),
     _it("dico dici dice diciamo dite dicono")),
    ("dir", "dire", 149, "imperfetto", "dgéva (géva, dséva)", ["1sing"],
     ["dicevo"]),
    ("dir", "dire", 149, "congiuntivo_presente",
     "diga, digh, diga, dgégna (dségna, gégna), dgi (dsi, gi), diga",
     list(PERSONE), _it("dica dica dica diciamo diciate dicano")),
    ("dir", "dire", 149, "congiuntivo_imperfetto", "dgéss (dséss, géss)",
     ["1sing"], ["dicessi"]),
    ("dir", "dire", 149, "gerundio", "dgénd (dsénd, génd, digànd)", [""],
     ["dicendo"]),
    ("vgnir", "venire", 149, "presente", "vién, vgnén (jén, gnén), "
     "vgni (gni)", ["1sing", "1plur", "2plur"],
     _it("vengo veniamo venite")),
    ("vgnir", "venire", 149, "presente", "vién", ["3sing"], ["viene"]),
    ("vgnir", "venire", 149, "imperfetto", "vgnéva (gnéva, gniséva)",
     ["1sing"], ["venivo"]),
    ("vgnir", "venire", 149, "futuro", "vgnirò (gnirò)", ["1sing"],
     ["verrò"]),
    ("vgnir", "venire", 149, "condizionale", "vgnirév (gnirév)", ["1sing"],
     ["verrei"]),
    ("vgnir", "venire", 150, "congiuntivo_presente",
     "viéna, vgnégna (vgnéna), vgni (jéna, gnéna, gni)",
     ["1sing", "1plur", "2plur"], _it("venga veniamo veniate")),
    ("vgnir", "venire", 150, "congiuntivo_imperfetto", "vgnéss (gnéss)",
     ["1sing"], ["venissi"]),
    ("vgnir", "venire", 150, "gerundio", "vgnénd (gnénd)", [""],
     ["venendo"]),
    ("durmìr", "dormire", 150, "presente", "dòram, durmén, durmì, dòram",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("dormo dormiamo dormite dormono")),
    ("durmìr", "dormire", 150, "presente", "dòram", ["3sing"], ["dorme"]),
    ("ufrìr", "offrire", 150, "presente", "òfar, ufrén, ufrì, òfar",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("offro offriamo offrite offrono")),
    ("sufrìr", "soffrire", 150, "presente", "sòfar, sufrén, sufrì, sòfar",
     ["1sing", "1plur", "2plur", "3plur"],
     _it("soffro soffriamo soffrite soffrono")),
]

# --- i participi passati irregolari (pag. 151-154) -----------------------------
# (infinito ferrarese come lo scrive la tabella, participio come lo scrive la
#  tabella, participio italiano, pagina). Solo i verbi di cui il participio
#  italiano e' sicuro; quelli che non lo sono restano fuori, e la tabella
#  e' sul libro.

PARTICIPI = [
    ("acòrzar", "acòrt", "accorto", 151), ("amétar", "améss, amìss", "ammesso", 151),
    ("andàr", "andà", "andato", 151), ("assòlvar", "assòlt", "assolto", 151),
    ("assùmar", "assùnt, assumèst", "assunto", 151),
    ("avrìr", "avèrt", "aperto", 151), ("azùnzar", "azùnt", "aggiunto", 151),
    ("bévar", "bvu, bvèst", "bevuto", 151), ("còiar", "cuièst", "colto", 151),
    ("córar", "córss, curèst", "corso", 151),
    ("crédar", "cardù, cardèst", "creduto", 151),
    ("créssar", "carssù, carssèst", "cresciuto", 151),
    ("cumparìr", "cumparì, cumpàrss", "comparso", 151),
    ("cumpór", "cumpòst", "composto", 151), ("cundùr", "cundót", "condotto", 151),
    ("cunfóndar", "cunfùs, cunfundèst", "confuso", 151),
    ("cunvgnìr", "cunvgnù", "convenuto", 151),
    ("cunvìnzzar", "cunvìnt", "convinto", 151),
    ("cunzzèdar", "cunzzèss", "concesso", 151),
    ("cunzùnzar", "cunzùnt", "congiunto", 151), ("cuósar", "còt", "cotto", 151),
    ("cùsar", "cusì", "cucito", 151), ("dir", "dit", "detto", 151),
    ("diféndar", "difés", "difeso", 151), ("dsténdar", "dstés", "disteso", 151),
    ("duvér", "duvù, duvèst", "dovuto", 151), ("far", "fat", "fatto", 151),
    ("frìzar", "frit", "fritto", 151),
    ("gòdar", "gudèst, gudù", "goduto", 152),
    ("imprìmar", "imprimèst", "impresso", 152),
    ("indùsar", "indót, indùt", "indotto", 152),
    ("inténdar", "intés", "inteso", 152),
    ("lèzar", "lèt, l(i)zèst, alzèst", "letto", 152),
    ("maladìr", "maladì, maladét", "maledetto", 152),
    ("mantgnìr", "mantgnù", "mantenuto", 152), ("métar", "miss", "messo", 152),
    ("mónzar", "mónt, munzèst", "munto", 152),
    ("móvar", "mòss, muvèst", "mosso", 152), ("murìr", "mòrt", "morto", 152),
    ("parér", "parèst, parss", "parso", 152),
    ("parmétar", "parméss", "permesso", 152),
    ("piànzar", "piànt", "pianto", 152),
    ("piasér", "piasù (piasèst)", "piaciuto", 152),
    ("pióvar", "piuvù, (piuvèst)", "piovuto", 152),
    ("pónar", "pòst", "posto", 152), ("preténdar", "pretés", "preteso", 152),
    ("prevédar", "prevìst", "previsto", 152),
    ("prodùr", "prodót (prudót)", "prodotto", 152),
    ("pùnzar", "punt", "punto", 152), ("putér", "putù, putèst", "potuto", 152),
    ("racògliar", "racòlt", "raccolto", 152),
    ("resìstar", "resistì", "resistito", 152),
    ("rìdar", "ridèst (ridù)", "riso", 152),
    ("ridùr", "ridót, ardót, ardùt", "ridotto", 152),
    ("riflètar", "rifletù, riflèss", "riflesso", 152),
    ("rimétar", "riméss", "rimesso", 153), ("risòlvar", "risòlt", "risolto", 153),
    ("rispóndar", "rispòst", "risposto", 153), ("rómpar", "rót", "rotto", 153),
    ("savér", "savù (savèst)", "saputo", 153),
    ("sbàtar", "sbatù", "sbattuto", 153), ("scrìvar", "scrit", "scritto", 153),
    ("scumétar", "scuméss", "scommesso", 153),
    ("scunfìzar", "scunfìt", "sconfitto", 153),
    ("scuòtar", "scòss", "scosso", 153),
    ("spìnzar", "spint", "spinto", 153), ("spéndar", "spés", "speso", 153),
    ("star", "stà", "stato", 153),
    ("sudisfàr", "sudisfàt", "soddisfatto", 153),
    ("suzzèdar", "suzzèst", "successo", 153),
    ("svgnir", "svgnù", "svenuto", 153), ("tasér", "tasù (tasèst)", "taciuto", 153),
    ("tgnir", "tgnù, tgnèst", "tenuto", 153),
    ("tgnóssar", "tgnussù, tgnussèst", "conosciuto", 153),
    ("tìnzar", "tint", "tinto", 153), ("tór", "tòlt", "tolto", 153),
    ("uféndar", "ufés", "offeso", 153), ("ufrìr", "ufèrt", "offerto", 153),
    ("ùnzar", "unt", "unto", 153), ("utgnìr", "utgnù", "ottenuto", 153),
    ("valér", "valss (valèst)", "valso", 153), ("védar", "vist", "visto", 153),
    ("véndar", "vandù", "venduto", 154), ("vgnir", "vgnù (gnù)", "venuto", 154),
    ("vìnzzar", "vint", "vinto", 154), ("vìvar", "vissù", "vissuto", 154),
    ("vlér", "vlù (viù) vlèst", "voluto", 154),
]


# --- le regole della frase (pag. 104-105, 142-144, 160-163) --------------------

# Le preposizioni articolate (pag. 160-163): la forma davanti a consonante e
# quella davanti a vocale, prese dalla tabella («tra parentesi abbiamo messo le
# forme meno usate»: non entrano) e dagli esempi della stessa pagina.
PREPOSIZIONI = [
    ("del", "dal", "dl'", 160, "del, dello = dal, dl' ... La vita dl'òm."),
    ("dello", "dal", "dl'", 160, "del, dello = dal, dl'"),
    ("della", "dla", "dl'", 160, "della = dla, dl' ... La fin dl'ultma pagina."),
    ("dei", "di", "di", 160, "dei, degli = di"),
    ("degli", "di", "di", 160, "dei, degli = di"),
    ("delle", "dil", "dgl'", 160, "delle = dil, dgli, dgl' ... Al gh'ha dgl'idèi."),
    ("al", "al", "a l'", 161, "al = al ... allo = al, a l' ... A l'òm."),
    ("allo", "al", "a l'", 161, "allo = al, a l'"),
    ("alla", "a la", "a l'", 161, "alla = a la, a l', ala, al' ... A l'ho dit "
     "a l'amiga."),
    ("ai", "ai", "ai", 161, "ai, agli = ai, a i"),
    ("agli", "ai", "ai", 161, "ai, agli = ai, a i"),
    ("alle", "a il", "a gl'", 161, "alle = a il, al, a gli, a gl' ... A "
     "gl'inglési."),
    ("dal", "dal", "da l'", 161, "dal = dal ... dallo = dal, da l'"),
    ("dallo", "dal", "da l'", 161, "dallo = dal, da l'"),
    ("dalla", "dala", "da l'", 161, "dalla = dala, dal', da la, da l' ... A "
     "són andà da l'amiga."),
    ("dai", "dai", "dai", 162, "dai = dai, da i ... dagli = dai, da i"),
    ("dagli", "dai", "dai", 162, "dagli = dai, da i"),
    ("dalle", "da il", "da gl'", 162, "dalle = da il, dal, da gli (dagli), da "
     "gl' ... Da gl'inglési."),
    ("nel", "int al", "int l'", 162, "nel, nello = int al, int l' ... Int "
     "l'òm."),
    ("nello", "int al", "int l'", 162, "nel, nello = int al, int l'"),
    ("nella", "int la", "int l'", 162, "nella = int la, int l' ... Int "
     "l'anima."),
    ("nei", "int i", "int i", 162, "nei, negli = int i ... Int i òman."),
    ("negli", "int i", "int i", 162, "nei, negli = int i"),
    ("nelle", "int il", "int gli", 162, "nelle = int il, int gli ... Int gli "
     "urécc."),
    ("sul", "sul", "su l'", 162, "sul, sullo = sul, su l', ssl', s'al, sal"),
    ("sullo", "sul", "su l'", 162, "sul, sullo = sul, su l'"),
    ("sulla", "su la", "su l'", 162, "sulla = su la, su l', ssla ... Su l'asta."),
    ("sui", "sui", "sui", 163, "sui, sugli = sui, su i"),
    ("sugli", "sui", "sui", 163, "sui, sugli = sui, su i"),
    ("sulle", "su il", "su gl'", 163, "sulle = su il, sil, su gli, su gl' ... "
     "Su gl'ìsul."),
    ("col", "cól", "co' l'", 163, "con il, con lo, col = cón al, cón l', cól, "
     "co' l' ... Co' l'ànim cuntént."),
]

# Le preposizioni semplici che la tabella da' con una forma sola (pag. 163).
PAROLE = [
    ("con", "cón", "preposizione", 163, "con = cón, co'"),
    ("per", "par", "preposizione", 163, "per = par, pr'"),
]

# La negazione (pag. 142-144). La proclitica del verbo si fonde con «an»:
# «(in pratica = an, a n', n'; al n', la n', l'an, in', in, il n', t'an, mi
# an, nu an, vu an)». Davanti a consonante e davanti a vocale, dagli esempi:
# «Mi an véi brisa partir», «A n'al véd più», «Lu al n'ha gnént», «Ti t'an vo'
# gnént», «Ti an t'ha brisa vist», «Lór i n'...», «A n'è brisa véra».
NEGAZIONE = {
    "fonte": ID_FONTE, "dove": "pag. 142-144, «Forma negativa»",
    "regola": "«an...brisa = non... mica» ... il suo corrispondente «an, a n'» "
              "vuole di solito essere accompagnato da «brisa» o da un altro "
              "avverbio negativo ... fra i due elementi negativi «an... brisa» "
              "s'interpone una sola voce verbale, anche se questa è un tempo "
              "composto.",
    "esempi": ["Mi an véi brisa partir.", "Ti an t'ha brisa vist.",
               "Lu al n'ha gnént.", "A n'al véd più.", "Mi an l'ho più vist.",
               "A n'è brisa véra.", "Ti t'an vo' gnént.", "Nu an vlén gnént."],
    # la proclitica del verbo → la forma negativa, davanti a consonante e a
    # vocale (della parola che segue: il clitico o il verbo)
    "proclitiche": {
        "a": {"consonante": "an", "vocale": "a n'"},
        "aj": {"consonante": "an", "vocale": "a n'"},
        "at": {"consonante": "t'an", "vocale": "an t'"},
        "al": {"consonante": "al n'", "vocale": "al n'"},
        "l'": {"consonante": "al n'", "vocale": "al n'"},
        "la": {"consonante": "la n'", "vocale": "la n'"},
        "i": {"consonante": "i n'", "vocale": "i n'"},
        "j": {"consonante": "i n'", "vocale": "i n'"},
    },
    "brisa": "brisa",
    # le parole italiane che fanno gia' la negazione: con loro «brisa» non si
    # aggiunge («Mi an véi gnént», «A n'al véd più», «An vién nissùn»)
    "parole_negative": ["niente", "nulla", "mai", "nessuno", "nessuna",
                        "più", "piu'", "neanche", "nemmeno", "neppure",
                        "affatto", "mica", "né", "ne'"],
    # i pronomi atoni che stanno fra «non» e il verbo («non lo so»)
    "clitici": ["lo", "la", "li", "le", "l'", "mi", "ti", "ci", "vi", "si",
                "ne", "gli", "me", "te", "ce", "ve", "se", "glielo",
                "gliela", "me lo", "te lo"],
}

# I pronomi atoni davanti al verbo (pag. 94-97, «Particelle pronominali
# semplici»), e come si uniscono alla particella soggetto. Quattro forme:
#   a_cons, a_voc   quando la particella del verbo e' «a» (mi, nu, vu): la
#                   particella si fonde col pronome («Mi al véd», «Am dit al
#                   parché?», «A l'ho vist», «A m'arcòrd», «A la véd», «A i véd
#                   bén», «Mi a il véd», «A t'ho dit»)
#   dopo_cons, dopo_voc   dopo un'altra particella o dopo la negazione («Lu al
#                   m'dis», «Lór i t'véd», «Ti at l'ha vist», «Al s'è malà», «I
#                   al véd», «A n'al véd più», «Mi an l'ho più vist»)
# «le» non c'e': e' «a lei» (agh) o «loro» femminile (il), e una parola per
# volta non si distinguono. Nemmeno «ci» e «vi»: sono «a noi», «a voi» (as, av)
# ma anche particelle di luogo («Nota. Ci, vi = particelle avverbiali», pag. 96),
# e «ci vado» non e' «as vagh».
PRONOMI_ATONI = {
    "fonte": ID_FONTE, "dove": "pag. 94-97, «Particelle pronominali semplici»",
    "forme": {
        "mi": {"a_cons": "am", "a_voc": "a m'", "dopo_cons": "m'", "dopo_voc": "m'"},
        "ti": {"a_cons": "at", "a_voc": "a t'", "dopo_cons": "t'", "dopo_voc": "t'"},
        "lo": {"a_cons": "al", "a_voc": "a l'", "dopo_cons": "al", "dopo_voc": "l'"},
        "l'": {"a_cons": "al", "a_voc": "a l'", "dopo_cons": "al", "dopo_voc": "l'"},
        "la": {"a_cons": "a la", "a_voc": "a l'", "dopo_cons": "la", "dopo_voc": "l'"},
        "li": {"a_cons": "a i", "a_voc": "a i", "dopo_cons": "i", "dopo_voc": "i"},
        "gli": {"a_cons": "agh", "a_voc": "a gh'", "dopo_cons": "gh'", "dopo_voc": "gh'"},
        "si": {"a_cons": "as", "a_voc": "a s'", "dopo_cons": "s'", "dopo_voc": "s'"},
        "ne": {"a_cons": "in", "a_voc": "a n'", "dopo_cons": "in", "dopo_voc": "n'"},
    },
    "esempi": ["Mi al véd bén.", "A l'ho vist.", "Am dit al parché?",
               "A m'arcòrd (am arcòrd).", "Lu al m'dis.", "Lór i t'véd.",
               "A t'ho dit la vrità.", "A la véd.", "A i véd bén.",
               "Agh vói bén.", "Al s'è malà.", "Lu al v'dis.",
               "I n'ha dscórss."],
    # le particelle soggetto che restano davanti al pronome, e come si scrivono
    "particelle": {"at": "at", "al": "al", "l'": "al", "la": "la", "i": "i",
                   "j": "i"},
}

# La domanda diretta (pag. 94-97, 104-105): la particella soggetto va dopo il
# verbo e si fonde con lui. Entrano solo le forme che il libro scrive.
DOMANDE = [
    ("sono", "1sing", "", "sónia", 105, "Mi a són bón. → Sónia bón?"),
    ("ho", "1sing", "", "hòia", 94, "Hòia rasón o no?"),
    ("sei", "2sing", "", "jét", 105, "Ti at jé bón. → Jét bón?"),
    ("hai", "2sing", "", "hat", 94, "Hat fam?"),
    ("vuoi", "2sing", "", "vót", 94, "Còsa vót?"),
    ("puoi", "2sing", "", "póssat", 104, "Póssat dirl'a mié fradèl?"),
    ("è", "3sing", "m", "èl", 105, "L'è véra. → Èl véra?"),
    ("è", "3sing", "f", "èla", 95, "Èla bòna o cativa?"),
    ("ha", "3sing", "m", "hal", 105, "Mario hal dit la vrità?"),
    ("ha", "3sing", "f", "hàla", 105, "Maria hàla dit la vrità?"),
    ("dice", "3sing", "m", "dìsal", 105, "Gigi dìsal la vrità?"),
    ("dice", "3sing", "f", "dìsla", 105, "Luisa dìsla la vrità?"),
    ("parliamo", "1plur", "", "parlégna", 105, "Nu parlégna (parlénia) bén?"),
    ("mangiate", "2plur", "", "magnèv", 105, "Vu a magnè. → Magnèv?"),
    ("volete", "2plur", "", "vliv", 105, "Vu a vli partìr. → Vliv partìr?"),
    ("avete", "2plur", "", "iv", 96, "Iv vist? Iv santì?"),
    ("venite", "2plur", "", "gniv", 96, "Gniv o no?"),
    ("hanno", "3plur", "", "hai", 105, "Lór i ha magnà. → Hai magnà?"),
    ("sono", "3plur", "", "èi", 97, "Èi stà lór?"),
]


# --- la scomposizione delle caselle -------------------------------------------

def espandi(parola: str) -> list:
    """«lav(i)» → ['lavi', 'lav']: la forma in -i e' quella cittadina (pag. 109)."""
    m = re.match(r"^(.*?)\(([^()]*)\)(.*)$", parola)
    if not m:
        return [parola]
    lunga = m.group(1) + m.group(2) + m.group(3)
    corta = m.group(1) + m.group(3)
    return [lunga, corta]


_GRUPPO = r"\s\(((?:[^()]|\([^()]*\))*)\)"


def _parti(testo: str):
    """La proclitica e la forma di un pezzo di casella senza pronome."""
    t = testo.split()
    if t and t[0].lower() in PRONOMI:
        t = t[1:]
    proclitica = ""
    if len(t) == 1 and t[0].startswith("l'") and len(t[0]) > 2:
        proclitica, t = "l'", [t[0][2:]]
    elif len(t) > 1 and t[0] in PROCLITICHE:
        proclitica, t = t[0], t[1:]
    return proclitica, t


def scomponi(casella: str) -> dict:
    """«ti at avév(i) (at év(i))» → persona, proclitica, forme, varianti."""
    testo = " ".join(casella.split())
    gruppi = re.findall(_GRUPPO, testo)
    base = re.sub(_GRUPPO, "", testo).strip()
    pronome = base.split()[0].lower()
    if pronome not in PRONOMI:
        raise ValueError("casella senza pronome: %r" % casella)
    proclitica, resto = _parti(base)
    if len(resto) != 1:
        raise ValueError("casella con piu' parole: %r" % casella)
    varianti = []
    for gruppo in gruppi:
        for alternativa in gruppo.split(","):
            p, t = _parti(alternativa)
            if len(t) != 1 or "-" in t[0]:
                continue
            for forma in espandi(t[0]):
                # una variante senza proclitica propria prende quella della
                # forma principale: «lu l'avrà (arà)» → «l'arà» (pag. 110)
                varianti.append((p or proclitica, forma))
    return {"pronome": pronome, "persona": PRONOMI[pronome],
            "proclitica": proclitica, "forme": espandi(resto[0]),
            "varianti": varianti}


def _elenco(testo: str) -> list:
    """«dgén (gén, dsén)» → [('dgén', ['gén', 'dsén'])], senza spezzare le parentesi."""
    pezzi, profondita, corrente = [], 0, ""
    for c in testo:
        if c == "(":
            profondita += 1
        elif c == ")":
            profondita -= 1
        if c == "," and profondita == 0:
            pezzi.append(corrente.strip())
            corrente = ""
        else:
            corrente += c
    if corrente.strip():
        pezzi.append(corrente.strip())
    risultato = []
    for pezzo in pezzi:
        m = re.match(r"^(\S+)\s*\((.*)\)\s*(\S*)$", pezzo)
        if m and not re.match(r"^\S*\(", pezzo):
            varianti = [v.strip() for v in re.split(r"[,\s]+", m.group(2))
                        if v.strip()]
            principale = m.group(1)
            if m.group(3):
                varianti.append(m.group(3))
            risultato.append((principale, varianti))
        else:
            parole = pezzo.split()
            risultato.append((parole[0], parole[1:]))
    return risultato


def _proclitica(persona: str, forma: str) -> str:
    if not persona:
        return ""
    if persona == "3sing" and forma[:1].lower() in VOCALI:
        return "l'"
    return PROCLITICA_DI[persona]


# --- le righe -----------------------------------------------------------------

def _glossario() -> dict:
    per_forma = {}
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            if riga.startswith("{"):
                v = json.loads(riga)
                for forma in [v.get("ferrarese") or ""] + (v.get("varianti") or []):
                    per_forma.setdefault(chiave(forma), v["id"])
    return per_forma


def _riga(lemma, persona, tempo, forma, proclitica, italiano, casella, dove,
          nota, glossario, pronome="", variante_di=""):
    voce = glossario.get(chiave(lemma), "")
    riga = {"lemma": lemma, "lemma_fonte": lemma, "lemma_id": voce,
            "lemma_nel_glossario": bool(voce), "persona": persona,
            "tempo": tempo, "forma": forma, "forma_fonte": forma,
            "proclitica": proclitica, "clitico": "", "pronome": pronome,
            "italiano": italiano, "scritto_dalla_fonte": casella,
            "fonte": ID_FONTE, "dove": dove, "nota": nota,
            "attendibilita": "I", "da_verificare": True}
    if variante_di:
        riga["variante_di"] = variante_di
    if italiano in OMOGRAFI and persona:
        riga["omografo"] = OMOGRAFI[italiano]
    return riga


def righe_prodotte(glossario: dict) -> tuple:
    righe, fuori = [], []
    for p in PARADIGMI:
        for tempo, (pagina, caselle, italiani) in p["tempi"].items():
            assert len(caselle) == 6 and len(italiani) == 6, (p["lemma"], tempo)
            for casella, italiano in zip(caselle, italiani):
                parti = scomponi(casella)
                chiave_fuori = (p["lemma"], tempo, parti["persona"])
                if chiave_fuori in FUORI:
                    fuori.append(chiave_fuori + (casella, FUORI[chiave_fuori]))
                    continue
                dove = "pag. %d, %s, %s" % (pagina, p["lemma"], NOMI_TEMPI[tempo])
                nota = ("%s, «%s», %s: la fonte scrive «%s» (%s, pag. %d)."
                        % (p["gruppo"].capitalize(), p["lemma"],
                           NOMI_TEMPI[tempo], casella, LIBRO, pagina))
                if len(parti["forme"]) > 1:
                    nota += (" La desinenza fra parentesi: la forma in -i e' "
                             "quella dell'area cittadina (pag. 109), l'altra "
                             "e' del contado.")
                principale = parti["forme"][0]
                righe.append(_riga(p["lemma"], parti["persona"], tempo,
                                   principale, parti["proclitica"], italiano,
                                   casella, dove, nota, glossario,
                                   pronome=parti["pronome"]))
                altre = [(parti["proclitica"], f) for f in parti["forme"][1:]]
                for proclitica, forma in altre + parti["varianti"]:
                    if forma == principale:
                        continue
                    righe.append(_riga(p["lemma"], parti["persona"], tempo,
                                       forma, proclitica, italiano, casella,
                                       dove, nota + " Variante della forma "
                                       "principale.", glossario,
                                       pronome=parti["pronome"],
                                       variante_di=principale))
        for tempo in ("gerundio", "participio"):
            if not p.get(tempo):
                continue
            pagina, forma, italiano = p[tempo]
            righe.append(_riga(p["lemma"], "", tempo, forma, "", italiano, forma,
                               "pag. %d, %s, %s" % (pagina, p["lemma"], tempo),
                               "%s, «%s»: la fonte scrive «%s» per il %s (%s, "
                               "pag. %d)." % (p["gruppo"].capitalize(),
                                             p["lemma"], forma, tempo, LIBRO,
                                             pagina), glossario))
    for lemma, inf_it, pagina, tempo, elenco, persone, italiani in IRREGOLARI:
        forme = _elenco(elenco)
        if len(forme) < len(persone):
            raise ValueError("%s %s: %d forme per %d persone"
                             % (lemma, tempo, len(forme), len(persone)))
        assert len(persone) == len(italiani), (lemma, tempo)
        dove = "pag. %d, verbi irregolari, %s, %s" % (
            pagina, lemma, NOMI_TEMPI.get(tempo, tempo))
        for (principale, varianti), persona, italiano in zip(forme, persone,
                                                              italiani):
            nota = ("Verbo irregolare «%s» (%s), %s: la fonte scrive «%s» "
                    "(%s, pag. %d). La fonte elenca le forme senza la persona; "
                    "questa e' la %s, letta dall'ordine della tabella. La "
                    "proclitica e' quella dei paradigmi (pag. 104)."
                    % (lemma, inf_it, NOMI_TEMPI.get(tempo, tempo), elenco,
                       LIBRO, pagina, persona or "forma senza persona"))
            righe.append(_riga(lemma, persona, tempo, principale,
                               _proclitica(persona, principale), italiano,
                               elenco, dove, nota, glossario))
            for v in varianti:
                righe.append(_riga(lemma, persona, tempo, v,
                                   _proclitica(persona, v), italiano, elenco,
                                   dove, nota + " Variante meno usata.",
                                   glossario, variante_di=principale))
    for lemma, scritto, italiano, pagina in PARTICIPI:
        forme = re.findall(r"[^\s,()]+(?:\([^()]*\)[^\s,()]*)*", scritto)
        for numero, forma in enumerate(forme):
            for f in espandi(forma) if "(" in forma else [forma]:
                righe.append(_riga(
                    lemma, "", "participio", f, "", italiano, scritto,
                    "pag. %d, participi passati irregolari, %s" % (pagina, lemma),
                    "Participio passato di «%s»: la tabella scrive «%s» (%s, "
                    "pag. %d)." % (lemma, scritto, LIBRO, pagina), glossario,
                    variante_di=forme[0] if (numero or f != forma) else ""))
    return righe, fuori


def _chiave_riga(riga: dict) -> str:
    return "|".join([chiave(riga["lemma"]), riga["persona"], riga["tempo"],
                     chiave(riga["forma"]), riga.get("proclitica", ""),
                     riga["italiano"]])


def leggi_file() -> tuple:
    commenti, righe = [], []
    with io.open(VERBI, encoding="utf-8") as f:
        for linea in f:
            linea = linea.rstrip("\n")
            if linea.startswith("//"):
                commenti.append(linea)
            elif linea.strip():
                righe.append(json.loads(linea))
    return commenti, righe


def unisci(esistenti: list, nuove: list) -> tuple:
    """Le righe di S027 si rifanno da capo; gli id restano quelli di prima."""
    vecchie = {_chiave_riga(r): r["id"] for r in esistenti
               if r.get("fonte") == ID_FONTE}
    altre = [r for r in esistenti if r.get("fonte") != ID_FONTE]
    maggiore = max(int(r["id"][1:]) for r in esistenti) if esistenti else 0
    risultato, viste = list(altre), set()
    for riga in nuove:
        k = _chiave_riga(riga)
        if k in viste:
            continue
        viste.add(k)
        if k in vecchie:
            identita = vecchie[k]
        else:
            maggiore += 1
            identita = "C%04d" % maggiore
        risultato.append({"id": identita, **riga})
    return risultato, len(viste)


def main() -> int:
    ap = argparse.ArgumentParser(description="La grammatica di Biolcati (S027).")
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args()
    righe, fuori = righe_prodotte(_glossario())
    commenti, esistenti = leggi_file()
    risultato, quante = unisci(esistenti, righe)
    print("paradigmi interi            %4d" % len(PARADIGMI))
    print("righe di verbi irregolari   %4d" % len(IRREGOLARI))
    print("participi irregolari        %4d" % len(PARTICIPI))
    print("righe di S027               %4d" % quante)
    print("caselle lasciate fuori      %4d" % len(fuori))
    for f in fuori:
        print("  fuori: %s %s %s «%s»: %s" % f)
    print("righe nel file, prima %d, dopo %d" % (len(esistenti), len(risultato)))
    if args.prova:
        return 0
    sistema = None
    for linea in commenti:
        if linea.startswith("// SISTEMA"):
            sistema = json.loads(linea[len("// SISTEMA"):].strip())
    if sistema is None:
        raise SystemExit("dati/verbi.jsonl non ha la riga SISTEMA")
    sistema["forme"] = len(risultato)
    sistema["paradigmi_S027"] = sorted({p["lemma"] for p in PARADIGMI})
    sistema["fuori_S027"] = [[l, t, p] for l, t, p, _, _ in fuori]
    commenti = [("// SISTEMA " + json.dumps(sistema, ensure_ascii=False))
                if c.startswith("// SISTEMA") else c for c in commenti]
    with io.open(VERBI, "w", encoding="utf-8", newline="\n") as f:
        for c in commenti:
            f.write(c + "\n")
        for riga in risultato:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritto %s" % os.path.relpath(VERBI, RADICE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
