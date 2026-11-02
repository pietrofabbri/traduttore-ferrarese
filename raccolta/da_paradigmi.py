#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le tabelle di coniugazione di S015 entrano in `dati/verbi.jsonl`.

**Che cosa c'e' nella fonte.** La sezione 4 («Verbi») delle note linguistiche di
Roberto Bigoni (S015) tabella per intero dodici paradigmi: i due ausiliari
(`èsar`, `avér`, e `avér` rafforzato con la proclitica `ɣ`), un verbo modello per
ciascuna delle quattro coniugazioni regolari (`kaŋtàr`, `tašér`, `lèžar`,
`kapìr`) e cinque irregolari (`dar`, `far`, `dir`, `putér`, `vlér`). Per ognuno:
indicativo presente, futuro e imperfetto, congiuntivo presente e imperfetto,
condizionale presente, gerundio e participio passato. Fino alla 0.36 ne erano
entrate trenta forme, il presente di cinque verbi, scritte a mano.

**Perche' una tabella scritta qui e non una lettura della pagina.** Come in
`da_verbi.py`: ogni riga di `PARADIGMI` e' una **citazione**, la casella come la
fonte la scrive — pronome, proclitica e verbo, «mi a kaŋt» — e il generatore la
scompone, non la indovina. La trascrizione e' stata confrontata casella per
casella con la pagina il 2026-11-02 (`REGISTRO.md`, 0.37), e se la fonte c'e' in
`raccolta/grezzi/bigoni_ilferrarese.txt` il generatore rifa' il confronto e si
ferma su ogni casella che non trova.

**Che cosa si scompone.** «mi a kaŋt» e' il pronome `mi`, la **proclitica** `a` e
il verbo `kaŋt`. La proclitica non e' un ornamento: la fonte dice che il verbo
finito «richiede, tranne che all'imperativo, l'espressione del soggetto» con la
proclitica, quindi la riga la porta in un campo suo e il motore la scrive
davanti al verbo («canto» → `a cant`). Il pronome resta fuori: «io» lo traduce
il glossario.

**Che cosa si scrive come la fonte, e che cosa no.**

- le **varianti** («ti at dìši / di») diventano due righe, la prima con il peso
  di forma principale e la seconda con `variante_di`;
- le **parti facoltative** fra parentesi quadre («nu a [av]éŋ») si tengono e si
  dichiarano nella nota: la fonte dice che si possono omettere, e la riga non
  sceglie per lei;
- la forma passa nella grafia del progetto con `dati/conversione_bigoni.json`, e
  la forma della fonte resta in `forma_fonte`; le perdite della conversione
  (`š`, `ž`, le atone aperte e chiuse) e le letture che l'italiano renderebbe in
  un altro modo (`dàɣi` → `dàgi`, che si legge con la g dolce) sono nominate
  nella nota della riga;
- **una casella e' lasciata fuori**: il futuro di `tašér` alla seconda plurale,
  che la fonte scrive «vu a kaŋtarì», cioe' la forma di `kaŋtàr`. E' quasi certo
  un refuso, ma correggerlo sarebbe scrivere una forma che la fonte non scrive:
  la casella resta un buco dichiarato (`FUORI`).

**Gli omografi.** Alcune forme italiane sono anche parole funzionali: «dai» (dare
e la preposizione), «sia» (essere e la congiunzione). Il motore le cerca parola
per parola e senza contesto, quindi una riga per «dai» tradurrebbe ogni «dai»
come un verbo. Le righe ci sono, con il campo `omografo` che lo dice, e il motore
non le usa per tradurre.

Uso:
    python3 raccolta/da_paradigmi.py --prova    # mostra, non scrive
    python3 raccolta/da_paradigmi.py            # scrive in dati/verbi.jsonl
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

from traduttore.normalizza import chiave  # noqa: E402

VERBI = os.path.join(RADICE, "dati", "verbi.jsonl")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
CONVERSIONE = os.path.join(RADICE, "dati", "conversione_bigoni.json")
GREZZO = os.path.join(RADICE, "raccolta", "grezzi", "bigoni_ilferrarese.txt")
SITO = "https://www.robertobigoni.it/Servizi/Ferrarese/ilFerrarese.html"
ID_FONTE = "S015"

PERSONE = ("1sing", "2sing", "3sing", "1plur", "2plur", "3plur")
# I tempi nell'ordine in cui il motore li preferisce quando una parola italiana
# e' di piu' tempi («canti» e' presente e congiuntivo): l'indicativo prima,
# perche' e' il tempo che una frase senza «che» vuole.
TEMPI = ("presente", "imperfetto", "futuro", "condizionale",
         "congiuntivo_presente", "congiuntivo_imperfetto")
NOMI_TEMPI = {
    "presente": "indicativo presente",
    "futuro": "indicativo futuro",
    "imperfetto": "indicativo imperfetto",
    "congiuntivo_presente": "congiuntivo presente",
    "congiuntivo_imperfetto": "congiuntivo imperfetto",
    "condizionale": "condizionale presente",
}
PRONOMI = {"mi": "1sing", "ti": "2sing", "lu": "3sing", "nu": "1plur",
           "vu": "2plur", "lór": "3plur"}

# Le forme italiane che sono anche parole funzionali frequenti. Il motore cerca
# parola per parola e non distingue «dai» verbo da «dai» preposizione.
OMOGRAFI = {
    "dai": "e' anche la preposizione articolata «dai»",
    "sia": "e' anche la congiunzione «sia… sia»",
}

# La casella che la fonte scrive con la forma di un altro verbo.
FUORI = {
    ("tašér", "futuro", "2plur"):
        "la fonte scrive «vu a kaŋtarì», che e' la forma di kaŋtàr: quasi "
        "certamente un refuso, e il progetto non scrive al suo posto una forma "
        "che la fonte non scrive",
}


def _it(testo: str) -> list:
    return testo.split()


# Ogni paradigma: il lemma come lo scrive la fonte, il suo italiano, il gruppo,
# gerundio e participio, e per ogni tempo le sei caselle **come la fonte le
# scrive** e le sei forme italiane nello stesso ordine.
PARADIGMI = [
    {"lemma": "èsar", "italiano": "essere", "gruppo": "verbo ausiliare",
     "gerundio": ("séŋd", "essendo"), "participio": ("sta", "stato"),
     "tempi": {
         "presente": (["mi a sóŋ", "ti at jé", "lu l'è", "nu a séŋ",
                       "vu a si", "lór i jè"],
                      _it("sono sei è siamo siete sono")),
         "futuro": (["mi a sarò", "ti at sarà", "lu al sarà", "nu a saréŋ",
                     "vu a sarì", "lór i sarà"],
                    _it("sarò sarai sarà saremo sarete saranno")),
         "imperfetto": (["mi a jéra", "ti at jéri", "lu al jéra",
                         "nu a jéraŋ", "vu a jéri", "lór i jéra"],
                        _it("ero eri era eravamo eravate erano")),
         "congiuntivo_presente": (["ke mi a sìa", "ke ti at sìi",
                                   "ke lu al sìa", "ke nu a séña",
                                   "ke vu a sìi", "ke lór i sìa"],
                                  _it("sia sia sia siamo siate siano")),
         "congiuntivo_imperfetto": (["ke mi a fus", "ke ti at fùsi",
                                     "ke lu al fus", "ke nu a fùsaŋ",
                                     "ke vu a fùsi", "ke lór i fus"],
                                    _it("fossi fossi fosse fossimo foste "
                                        "fossero")),
         "condizionale": (["mi a saré", "ti at saré", "lu al saré",
                           "nu a sarésaŋ", "vu a sarési", "lór i saré"],
                          _it("sarei saresti sarebbe saremmo sareste "
                              "sarebbero")),
     }},
    {"lemma": "avér", "italiano": "avere", "gruppo": "verbo ausiliare",
     "gerundio": ("avénd", "avendo"), "participio": ("avù", "avuto"),
     "tempi": {
         "presente": (["mi aj ò", "ti at a", "lu al a", "nu a [av]éŋ",
                       "vu a avì", "lór j a"],
                      _it("ho hai ha abbiamo avete hanno")),
         "futuro": (["mi aj avrò", "ti at avrà", "lu al avrà", "nu a avréŋ",
                     "vu a avrì", "lór j avrà"],
                    _it("avrò avrai avrà avremo avrete avranno")),
         "imperfetto": (["mi aj éva", "ti at évi", "lu al éva", "nu a évaŋ",
                         "vu a évi", "lór j éva"],
                        _it("avevo avevi aveva avevamo avevate avevano")),
         "congiuntivo_presente": (["ke mi aj àva", "ke ti at àvi",
                                   "ke lu al àva", "ke nu a [av]éña",
                                   "ke vu a avì", "ke lór j àva"],
                                  _it("abbia abbia abbia abbiamo abbiate "
                                      "abbiano")),
         "congiuntivo_imperfetto": (["ke mi aj [av]és", "ke ti at [av]ési",
                                     "ke lu al [av]és", "ke nu a [av]ésaŋ",
                                     "ke vu a avésì", "ke lór j [av]és"],
                                    _it("avessi avessi avesse avessimo "
                                        "aveste avessero")),
         "condizionale": (["mi [aj] avré", "ti at avré", "lu al avré",
                           "nu a avrésaŋ", "vu a avrési", "lór j avré"],
                          _it("avrei avresti avrebbe avremmo avreste "
                              "avrebbero")),
     }},
    # «avér» rafforzato dalla proclitica ɣ (R036): l'italiano e' quello con «ci»,
    # che il motore non cerca parola per parola. Le righe ci sono perche' la
    # fonte le scrive e il gioco le puo' usare.
    {"lemma": "avér", "italiano": "averci", "gruppo": "verbo ausiliare, "
     "rafforzato dalla proclitica ɣ", "clitico": "ɣ",
     "tempi": {
         "presente": (["mi a ɣ o", "ti at ɣ a", "lu al ɣ a", "nu a ɣ [av]éŋ",
                       "vu a ɣ avì", "lór i ɣ a"],
                      ["ci ho", "ci hai", "ci ha", "ci abbiamo", "ci avete",
                       "ci hanno"]),
         "futuro": (["mi a ɣ avrò", "ti at ɣ avrà", "lu al ɣ avrà",
                     "nu a ɣ avréŋ", "vu a ɣ avrì", "lór i ɣ avrà"],
                    ["ci avrò", "ci avrai", "ci avrà", "ci avremo",
                     "ci avrete", "ci avranno"]),
         "imperfetto": (["mi a ɣ éva", "ti at ɣ évi", "lu al ɣ éva",
                         "nu a ɣ évaŋ", "vu a ɣ évi", "lór i ɣ éva"],
                        ["ci avevo", "ci avevi", "ci aveva", "ci avevamo",
                         "ci avevate", "ci avevano"]),
         "congiuntivo_presente": (["ke mi a ɣ àva", "ke ti at ɣ àvi",
                                   "ke lu al ɣ àva", "ke nu a ɣ [av]éña",
                                   "ke vu a ɣ avì", "ke lór i ɣ àva"],
                                  ["ci abbia", "ci abbia", "ci abbia",
                                   "ci abbiamo", "ci abbiate", "ci abbiano"]),
         "congiuntivo_imperfetto": (["ke mi a ɣ [av]és", "ke ti at ɣ [av]ési",
                                     "ke lu al ɣ [av]és",
                                     "ke nu a ɣ [av]ésaŋ", "ke vu a ɣ avésì",
                                     "ke lór i ɣ [av]és"],
                                    ["ci avessi", "ci avessi", "ci avesse",
                                     "ci avessimo", "ci aveste",
                                     "ci avessero"]),
         "condizionale": (["mi a ɣ avré", "ti at ɣ avré", "lu al ɣ avré",
                           "nu a ɣ avrésaŋ", "vu a ɣ avrési", "lór i ɣ avré"],
                          ["ci avrei", "ci avresti", "ci avrebbe",
                           "ci avremmo", "ci avreste", "ci avrebbero"]),
     }},
    {"lemma": "kaŋtàr", "italiano": "cantare", "gruppo": "prima coniugazione",
     "gerundio": ("kaŋtàŋd", "cantando"), "participio": ("kaŋtà", "cantato"),
     "tempi": {
         "presente": (["mi a kaŋt", "ti at kàŋti", "lu al kàŋta",
                       "nu a kaŋtéŋ", "vu a kaŋté", "lór i kaŋta"],
                      _it("canto canti canta cantiamo cantate cantano")),
         "futuro": (["mi a kaŋtarò", "ti at kaŋtarà", "lu al kaŋtarà",
                     "nu a kaŋtaréŋ", "vu a kaŋtarì", "lór i kaŋtarà"],
                    _it("canterò canterai canterà canteremo canterete "
                        "canteranno")),
         "imperfetto": (["mi a kaŋtàva", "ti at kaŋtàvi", "lu al kaŋtàva",
                         "nu a kaŋtàvaŋ", "vu a kaŋtàvi", "lór i kaŋtàva"],
                        _it("cantavo cantavi cantava cantavamo cantavate "
                            "cantavano")),
         "congiuntivo_presente": (["ke mi a kàŋta", "ke ti at kàŋti",
                                   "ke lu al kàŋta", "ke nu a kaŋtéña",
                                   "ke vu a kaŋté", "ke lór i kaŋta"],
                                  _it("canti canti canti cantiamo cantiate "
                                      "cantino")),
         "congiuntivo_imperfetto": (["ke mi a kaŋtés", "ke ti at kaŋtési",
                                     "ke lu al kaŋtés", "ke nu a kaŋtésaŋ",
                                     "ke vu a kaŋtési", "ke lór i kaŋtés"],
                                    _it("cantassi cantassi cantasse "
                                        "cantassimo cantaste cantassero")),
         "condizionale": (["mi a kaŋtaré", "ti at kaŋtaré", "lu al kaŋtaré",
                           "nu a kaŋtarésaŋ", "vu a kaŋtarési",
                           "lór i kaŋtaré"],
                          _it("canterei canteresti canterebbe canteremmo "
                              "cantereste canterebbero")),
     }},
    {"lemma": "tašér", "italiano": "tacere", "gruppo": "seconda coniugazione",
     "gerundio": ("tašéŋd", "tacendo"), "participio": ("tašù", "taciuto"),
     "tempi": {
         "presente": (["mi a taš", "ti at tàši", "lu al taš", "nu a tašéŋ",
                       "vu a tašì", "lór i taš"],
                      _it("taccio taci tace taciamo tacete tacciono")),
         "futuro": (["mi a tašrò", "ti at tašrà", "lu al tašrà",
                     "nu a tašréŋ", "vu a kaŋtarì", "lór i tašrà"],
                    _it("tacerò tacerai tacerà taceremo tacerete taceranno")),
         "imperfetto": (["mi a tašéva", "ti at tašévi", "lu al tašéva",
                         "nu a tašévaŋ", "vu a tašévi", "lór i tašéva"],
                        _it("tacevo tacevi taceva tacevamo tacevate "
                            "tacevano")),
         "congiuntivo_presente": (["ke mi a tàša", "ke ti at tàši",
                                   "ke lu al tàša", "ke nu a tašéña",
                                   "ke vu a tašì", "ke lór i tàša"],
                                  _it("taccia taccia taccia taciamo taciate "
                                      "tacciano")),
         "congiuntivo_imperfetto": (["ke mi a tašés", "ke ti at tašési",
                                     "ke lu al tašés", "ke nu a tašésaŋ",
                                     "ke vu a tašìsi", "ke lór i tašés"],
                                    _it("tacessi tacessi tacesse tacessimo "
                                        "taceste tacessero")),
         "condizionale": (["mi a tašré", "ti at tašré", "lu al tašré",
                           "nu a tašrésaŋ", "vu a tašrési", "lór i tašré"],
                          _it("tacerei taceresti tacerebbe taceremmo "
                              "tacereste tacerebbero")),
     }},
    {"lemma": "lèžar", "italiano": "leggere", "gruppo": "terza coniugazione",
     "gerundio": ("lèžéŋd", "leggendo"), "participio": ("lèt", "letto"),
     "tempi": {
         "presente": (["mi a lèž", "ti at lèži", "lu al lèž", "nu a lèžéŋ",
                       "vu a lěžì", "lór i lèž"],
                      _it("leggo leggi legge leggiamo leggete leggono")),
         "futuro": (["mi a lěžarò", "ti at lěžarà", "lu al lěžarà",
                     "nu a lěžaréŋ", "vu a lěžarì", "lór i lèžarà"],
                    _it("leggerò leggerai leggerà leggeremo leggerete "
                        "leggeranno")),
         "imperfetto": (["mi a lěžéva", "ti at lěžévi", "lu al lěžéva",
                         "nu a lěžévaŋ", "vu a lěžévi", "lór i lěžéva"],
                        _it("leggevo leggevi leggeva leggevamo leggevate "
                            "leggevano")),
         "congiuntivo_presente": (["ke mi a lèža", "ke ti at lèži",
                                   "ke lu al lèža", "ke nu a lěžéña",
                                   "ke vu a lěžì", "ke lór i lèža"],
                                  _it("legga legga legga leggiamo leggiate "
                                      "leggano")),
         "congiuntivo_imperfetto": (["ke mi a lěžés", "ke ti at lěžési",
                                     "ke lu al lèžés", "ke nu a lěžésaŋ",
                                     "ke vu a lěžìsi", "ke lór i lěžés"],
                                    _it("leggessi leggessi leggesse "
                                        "leggessimo leggeste leggessero")),
         "condizionale": (["mi a lěžré", "ti at lěžré", "lu al lěžré",
                           "nu a lěžrésaŋ", "vu a lěžrési", "lór i lěžré"],
                          _it("leggerei leggeresti leggerebbe leggeremmo "
                              "leggereste leggerebbero")),
     }},
    {"lemma": "kapìr", "italiano": "capire", "gruppo": "quarta coniugazione",
     "gerundio": ("kapéŋd", "capendo"), "participio": ("kapì", "capito"),
     "tempi": {
         "presente": (["mi a kapìs", "ti at kapìsi", "lu al kapìs",
                       "nu a kapéŋ", "vu a kapì", "lór i kapìs"],
                      _it("capisco capisci capisce capiamo capite "
                          "capiscono")),
         "futuro": (["mi a kapirò", "ti at kapirà", "lu al kapirà",
                     "nu a kapiréŋ", "vu a kapirì", "lór i kapirà"],
                    _it("capirò capirai capirà capiremo capirete "
                        "capiranno")),
         "imperfetto": (["mi a kapìva", "ti at kapìvi", "lu al kapìva",
                         "nu a kapìvaŋ", "vu a kapìvi", "lór i kapìva"],
                        _it("capivo capivi capiva capivamo capivate "
                            "capivano")),
         "congiuntivo_presente": (["ke mi a kapìsa", "ke ti at kapìsi",
                                   "ke lu al kapìsa", "ke nu a kapéña",
                                   "ke vu a kapìsi", "ke lór i kapìsa"],
                                  _it("capisca capisca capisca capiamo "
                                      "capiate capiscano")),
         "congiuntivo_imperfetto": (["ke mi a kapés", "ke ti at kapés",
                                     "ke lu al kapés", "ke nu a kapésaŋ",
                                     "ke vu a kapési", "ke lór i kapés"],
                                    _it("capissi capissi capisse capissimo "
                                        "capiste capissero")),
         "condizionale": (["mi a kapiré", "ti at kapiré", "lu al kapiré",
                           "nu a kapirésaŋ", "vu a kapirési",
                           "lór i kapiré"],
                          _it("capirei capiresti capirebbe capiremmo "
                              "capireste capirebbero")),
     }},
    {"lemma": "dar", "italiano": "dare", "gruppo": "verbo irregolare",
     "gerundio": ("daŋd", "dando"), "participio": ("da", "dato"),
     "tempi": {
         "presente": (["mi a daɣ", "ti at da", "lu al da", "nu a déŋ",
                       "vu a dè", "lór i da"],
                      _it("do dai dà diamo date danno")),
         "futuro": (["mi a darò", "ti at darà", "lu al darà", "nu a daréŋ",
                     "vu a darì", "lór i darà"],
                    _it("darò darai darà daremo darete daranno")),
         "imperfetto": (["mi a dàva", "ti at dàvi", "lu al dàva",
                         "nu a dàvaŋ", "vu a dàvi", "lór i dàva"],
                        _it("davo davi dava davamo davate davano")),
         "congiuntivo_presente": (["ke mi a dàɣa", "ke ti at dàɣi",
                                   "ke lu al dàɣa", "ke nu a déña",
                                   "ke vu a dèj", "ke lór i dàɣa"],
                                  _it("dia dia dia diamo diate diano")),
         "congiuntivo_imperfetto": (["ke mi a dés", "ke ti at dési",
                                     "ke lu al dés", "ke nu a désaŋ",
                                     "ke vu a dési", "ke lór i dés"],
                                    _it("dessi dessi desse dessimo deste "
                                        "dessero")),
         "condizionale": (["mi a daré", "ti at daré", "lu al daré",
                           "nu a darésaŋ", "vu a darési", "lór i daré"],
                          _it("darei daresti darebbe daremmo dareste "
                              "darebbero")),
     }},
    {"lemma": "far", "italiano": "fare", "gruppo": "verbo irregolare",
     "gerundio": ("fašéŋd", "facendo"), "participio": ("fat", "fatto"),
     "tempi": {
         "presente": (["mi a faɣ", "ti at fa", "lu al fa", "nu a féŋ",
                       "vu a fè", "lór i fa"],
                      _it("faccio fai fa facciamo fate fanno")),
         "futuro": (["mi a farò", "ti at farà", "lu al farà", "nu a faréŋ",
                     "vu a farì", "lór i farà"],
                    _it("farò farai farà faremo farete faranno")),
         "imperfetto": (["mi a fašéva", "ti at fašévi", "lu al fašéva",
                         "nu a fašévaŋ", "vu a fašévi", "lór i fašéva"],
                        _it("facevo facevi faceva facevamo facevate "
                            "facevano")),
         "congiuntivo_presente": (["ke mi a fàɣa", "ke ti at fàɣi",
                                   "ke lu al fàɣa", "ke nu a féña",
                                   "ke vu a fèj", "ke lór i fàɣa"],
                                  _it("faccia faccia faccia facciamo "
                                      "facciate facciano")),
         "congiuntivo_imperfetto": (["ke mi a fašés / fés",
                                     "ke ti at fašési / fési",
                                     "ke lu al fašés / fés",
                                     "ke nu a fašésaŋ / fésaŋ",
                                     "ke vu a fašési / fési",
                                     "ke lór i fašés / fés"],
                                    _it("facessi facessi facesse facessimo "
                                        "faceste facessero")),
         "condizionale": (["mi a faré", "ti at faré", "lu al faré",
                           "nu a farésaŋ", "vu a farési", "lór i faré"],
                          _it("farei faresti farebbe faremmo fareste "
                              "farebbero")),
     }},
    {"lemma": "dir", "italiano": "dire", "gruppo": "verbo irregolare",
     "gerundio": ("dšéŋd / géŋd", "dicendo"), "participio": ("dit", "detto"),
     "tempi": {
         "presente": (["mi a diɣ", "ti at dìši / di", "lu al diš",
                       "nu a dšéŋ / géŋ", "vu a dšì / gi", "lór i diš"],
                      _it("dico dici dice diciamo dite dicono")),
         "futuro": (["mi a dirò", "ti at dirà", "lu al dirà", "nu a diréŋ",
                     "vu a dirì", "lór i dirà"],
                    _it("dirò dirai dirà diremo direte diranno")),
         "imperfetto": (["mi a dšéva / géva", "ti at dšévi / gévi",
                         "lu al dšéva / géva", "nu a dšévaŋ / gévaŋ",
                         "vu a dšévi / gévi", "lór i dšéva / géva"],
                        _it("dicevo dicevi diceva dicevamo dicevate "
                            "dicevano")),
         "congiuntivo_presente": (["ke mi a dìɣa", "ke ti at dìɣi",
                                   "ke lu al dìɣa", "ke nu a dšéña / géña",
                                   "ke vu a dši / gi", "ke lór i dìɣa"],
                                  _it("dica dica dica diciamo diciate "
                                      "dicano")),
         "congiuntivo_imperfetto": (["ke mi a dšés /gés",
                                     "ke ti at dšési / gési",
                                     "ke lu al dšés / gés",
                                     "ke nu a dšésaŋ / gésan",
                                     "ke vu a dšési / gési",
                                     "ke lór i dšés / gés"],
                                    _it("dicessi dicessi dicesse dicessimo "
                                        "diceste dicessero")),
         "condizionale": (["mi a diré", "ti at diré", "lu al diré",
                           "nu a dirésaŋ", "vu a dirési", "lór i diré"],
                          _it("direi diresti direbbe diremmo direste "
                              "direbbero")),
     }},
    {"lemma": "putér", "italiano": "potere", "gruppo": "verbo irregolare",
     "gerundio": ("putéŋd", "potendo"), "participio": ("putù", "potuto"),
     "tempi": {
         "presente": (["mi a pós", "ti at pó", "lu al pòl", "nu a putéŋ",
                       "vu a putì", "lór i pòl"],
                      _it("posso puoi può possiamo potete possono")),
         "futuro": (["mi a putrò", "ti at putrà", "lu al putrà",
                     "nu a putréŋ", "vu a putrì", "lór i putrà"],
                    _it("potrò potrai potrà potremo potrete potranno")),
         "imperfetto": (["mi a putéva", "ti at putévi", "lu al putéva",
                         "nu a putévaŋ", "vu a putévi", "lór i putéva"],
                        _it("potevo potevi poteva potevamo potevate "
                            "potevano")),
         "congiuntivo_presente": (["ke mi a pósa", "ke ti at pósi",
                                   "ke lu al pósa", "ke nu a putéña",
                                   "ke vu a putì", "ke lór i pósa"],
                                  _it("possa possa possa possiamo possiate "
                                      "possano")),
         "congiuntivo_imperfetto": (["ke mi a putés", "ke ti at putési",
                                     "ke lu al putés", "ke nu a putésaŋ",
                                     "ke vu a putési", "ke lór i putés"],
                                    _it("potessi potessi potesse potessimo "
                                        "poteste potessero")),
         "condizionale": (["mi a putré", "ti at putré", "lu al putré",
                           "nu a putrésaŋ", "vu a putrési", "lór i putré"],
                          _it("potrei potresti potrebbe potremmo potreste "
                              "potrebbero")),
     }},
    {"lemma": "vlér", "italiano": "volere", "gruppo": "verbo irregolare",
     "gerundio": ("vléŋd", "volendo"), "participio": ("vlu", "voluto"),
     "tempi": {
         "presente": (["mi a vój", "ti at vó", "lu al vòl", "nu a vléŋ",
                       "vu a vlì", "lór i vòl"],
                      _it("voglio vuoi vuole vogliamo volete vogliono")),
         "futuro": (["mi a vrò", "ti at vrà", "lu al vrà", "nu a vréŋ",
                     "vu a vrì", "lór i vrà"],
                    _it("vorrò vorrai vorrà vorremo vorrete vorranno")),
         "imperfetto": (["mi a vléva", "ti at vlévi", "lu al vléva",
                         "nu a vlévaŋ", "vu a vlévi", "lór i vléva"],
                        _it("volevo volevi voleva volevamo volevate "
                            "volevano")),
         "congiuntivo_presente": (["ke mi a vója", "ke ti at vója",
                                   "ke lu al vója", "ke nu a vléña",
                                   "ke vu a vlì", "ke lór i vója"],
                                  _it("voglia voglia voglia vogliamo "
                                      "vogliate vogliano")),
         "congiuntivo_imperfetto": (["ke mi a vlés", "ke ti at vlési",
                                     "ke lu al vlés", "ke nu a vlésaŋ",
                                     "ke vu a vlési", "ke lór i vlés"],
                                    _it("volessi volessi volesse volessimo "
                                        "voleste volessero")),
         "condizionale": (["mi a vré", "ti at vré", "lu al vré",
                           "nu a vrésaŋ", "vu a vrési", "lór i vré"],
                          _it("vorrei vorresti vorrebbe vorremmo vorreste "
                              "vorrebbero")),
     }},
]


# --- la conversione, dichiarata in dati/conversione_bigoni.json -------------

def _tabella() -> dict:
    with io.open(CONVERSIONE, encoding="utf-8") as f:
        grezzo = json.load(f)
    return {r["segno"]: r["lettera"]
            for r in grezzo["consonanti"] + grezzo["vocali"]}


# Le perdite che la conversione dichiara: il segno, e che cosa si perde.
PERDITE = {
    "š": "la «š» (s sonora) e' resa «s», che non porta la sonorita'",
    "ž": "la «ž» (z sonora) e' resa «z», che non porta la sonorita'",
    "ě": "la «ě» (e atona aperta) e' resa con l'accento, che la fonte non mette",
    "ê": "la «ê» (e atona chiusa) e' resa con l'accento, che la fonte non mette",
    "ǒ": "la «ǒ» (o atona aperta) e' resa con l'accento, che la fonte non mette",
    "ô": "la «ô» (o atona chiusa) e' resa con l'accento, che la fonte non mette",
}


def converti(forma: str, tabella: dict) -> tuple:
    """La forma nella grafia del progetto, e le cose che la conversione perde.

    La conversione e' lettera per lettera, come la tabella la dichiara. Le
    letture che l'italiano farebbe in un altro modo — una `k` o una `ɣ` davanti
    a `e` o `i`, che in italiano si leggerebbero dolci — non si correggono: la
    tabella non dichiara un `ch` o un `gh`, e la riga lo nomina.
    """
    resa = "".join(tabella.get(c, c) for c in forma.replace("[", "")
                   .replace("]", ""))
    perdite = [testo for segno, testo in PERDITE.items() if segno in forma]
    if re.search(r"[kɣ][eiéèìěê]", forma):
        perdite.append("la «k» o la «ɣ» davanti a e/i e' resa «c» o «g», che "
                       "in italiano si leggerebbe dolce: la fonte la vuole dura")
    if "[" in forma:
        tolta = re.findall(r"\[([^\]]*)\]", forma)
        perdite.append("la fonte mette fra parentesi quadre «%s»: si puo' "
                       "omettere, e la riga la scrive" % "», «".join(tolta))
    return unicodedata.normalize("NFC", resa), perdite


def _trascrizione(forma_fonte: str, forma: str) -> str:
    """La frase che dichiara la conversione, come la scrivevano le righe a mano."""
    return ("Trascrizione della fonte: «%s», resa «%s» con la tabella "
            "dichiarata in dati/conversione_bigoni.json." % (forma_fonte, forma))


# --- la scomposizione di una casella ------------------------------------------

def scomponi(casella: str) -> dict:
    """«ke lu al ɣ àva» → pronome, proclitica, clitico, forme.

    La scomposizione segue quello che la fonte dichiara: il congiuntivo comincia
    con «ke», poi viene il pronome, poi la proclitica (`a`, `at`, `al`, `aj`,
    `i`, `j`, oppure `l'` attaccata al verbo in «lu l'è»), poi il rafforzativo
    `ɣ` se c'e', poi il verbo, con le varianti separate da «/».
    """
    testo = " ".join(casella.split())
    congiuntivo = testo.startswith("ke ")
    if congiuntivo:
        testo = testo[3:]
    pronome, resto = testo.split(" ", 1)
    if pronome not in PRONOMI:
        raise ValueError("casella senza pronome: %r" % casella)
    facoltativa = False
    if resto.startswith("l'"):
        proclitica, resto = "l'", resto[2:]
    else:
        proclitica, resto = resto.split(" ", 1)
        if proclitica.startswith("[") and proclitica.endswith("]"):
            proclitica, facoltativa = proclitica[1:-1], True
    clitico = ""
    if resto.startswith("ɣ "):
        clitico, resto = "ɣ", resto[2:]
    forme = [f.strip() for f in resto.split("/") if f.strip()]
    return {"pronome": pronome, "persona": PRONOMI[pronome],
            "proclitica": proclitica, "proclitica_facoltativa": facoltativa,
            "clitico": clitico, "forme": forme, "congiuntivo": congiuntivo}


# --- le righe ------------------------------------------------------------------

def _glossario() -> dict:
    per_chiave = {}
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("//"):
                continue
            voce = json.loads(riga)
            per_chiave.setdefault(chiave(voce.get("ferrarese") or ""), voce)
    return per_chiave


def _voce_del_lemma(lemma_fonte: str, lemma: str, glossario: dict):
    for candidato in (lemma_fonte, lemma):
        voce = glossario.get(chiave(candidato))
        if voce is not None:
            return voce
    return None


def righe_prodotte(tabella: dict, glossario: dict) -> tuple:
    """Le righe, e le caselle lasciate fuori con il loro motivo."""
    righe, fuori = [], []
    for p in PARADIGMI:
        lemma, _ = converti(p["lemma"], tabella)
        voce = _voce_del_lemma(p["lemma"], lemma, glossario)
        comune = {"lemma": lemma, "lemma_fonte": p["lemma"],
                  "lemma_id": voce["id"] if voce else "",
                  "lemma_nel_glossario": voce is not None}
        for tempo in TEMPI:
            caselle, italiani = p["tempi"][tempo]
            assert len(caselle) == 6 and len(italiani) == 6, (p["lemma"], tempo)
            for casella, italiano in zip(caselle, italiani):
                parti = scomponi(casella)
                if (p["lemma"], tempo, parti["persona"]) in FUORI:
                    fuori.append((p["lemma"], tempo, parti["persona"], casella,
                                  FUORI[(p["lemma"], tempo, parti["persona"])]))
                    continue
                for numero, forma_fonte in enumerate(parti["forme"]):
                    forma, perdite = converti(forma_fonte, tabella)
                    proclitica, _ = converti(parti["proclitica"], tabella)
                    nota = ["%s, «%s», %s: la fonte scrive «%s»."
                            % (p["gruppo"].capitalize(), p["lemma"],
                               NOMI_TEMPI[tempo], casella)]
                    nota.append("Il soggetto e' il pronome «%s» con la "
                                "proclitica «%s»: il pronome lo traduce il "
                                "glossario, la proclitica va davanti al verbo."
                                % (parti["pronome"], parti["proclitica"]))
                    if parti["proclitica_facoltativa"]:
                        nota.append("La fonte mette la proclitica fra "
                                    "parentesi quadre: si puo' omettere.")
                    if forma != forma_fonte:
                        nota.append(_trascrizione(forma_fonte, forma))
                    nota.extend(x[0].upper() + x[1:] + "." for x in perdite)
                    riga = dict(comune)
                    riga.update({
                        "persona": parti["persona"], "tempo": tempo,
                        "forma": forma, "forma_fonte": forma_fonte,
                        "proclitica": proclitica,
                        "clitico": parti["clitico"],
                        "pronome": parti["pronome"],
                        "italiano": italiano,
                        "scritto_dalla_fonte": casella,
                        "fonte": ID_FONTE,
                        "dove": "§4 «Verbi», %s, %s" % (p["lemma"],
                                                        NOMI_TEMPI[tempo]),
                        "nota": " ".join(nota),
                        "attendibilita": "I",
                        "da_verificare": True,
                    })
                    if numero:
                        riga["variante_di"] = parti["forme"][0]
                    if italiano in OMOGRAFI:
                        riga["omografo"] = OMOGRAFI[italiano]
                    righe.append(riga)
        for tempo, coppia in (("gerundio", p.get("gerundio")),
                              ("participio", p.get("participio"))):
            if not coppia:
                continue
            casella, italiano = coppia
            varianti = [f.strip() for f in casella.split("/")]
            for numero, forma_fonte in enumerate(varianti):
                forma, perdite = converti(forma_fonte, tabella)
                nota = ["%s, «%s»: la fonte scrive «%s» per il %s."
                        % (p["gruppo"].capitalize(), p["lemma"], casella,
                           "gerundio" if tempo == "gerundio"
                           else "participio passato")]
                if forma != forma_fonte:
                    nota.append(_trascrizione(forma_fonte, forma))
                nota.extend(x[0].upper() + x[1:] + "." for x in perdite)
                riga = dict(comune)
                riga.update({
                    "persona": "", "tempo": tempo, "forma": forma,
                    "forma_fonte": forma_fonte, "proclitica": "",
                    "clitico": "", "pronome": "", "italiano": italiano,
                    "scritto_dalla_fonte": casella, "fonte": ID_FONTE,
                    "dove": "§4 «Verbi», %s, %s" % (p["lemma"], tempo),
                    "nota": " ".join(nota), "attendibilita": "I",
                    "da_verificare": True,
                })
                if numero:
                    riga["variante_di"] = varianti[0]
                righe.append(riga)
    return righe, fuori


def caselle_citate() -> list:
    """Tutte le stringhe che il generatore attribuisce alla fonte."""
    citate = []
    for p in PARADIGMI:
        for tempo in TEMPI:
            citate.extend(p["tempi"][tempo][0])
        for chiave_tempo in ("gerundio", "participio"):
            if p.get(chiave_tempo):
                citate.append(p[chiave_tempo][0])
    return citate


def controlla_grezzo() -> list:
    """Le caselle che non si trovano nel testo della fonte, se il testo c'e'."""
    if not os.path.exists(GREZZO):
        return []
    with io.open(GREZZO, encoding="utf-8") as f:
        testo = " ".join(unicodedata.normalize("NFC", f.read()).split())
    return [c for c in caselle_citate()
            if " ".join(unicodedata.normalize("NFC", c).split()) not in testo]


# --- la scrittura ---------------------------------------------------------------

def _chiave_riga(riga: dict) -> str:
    return "|".join([chiave(riga["lemma"]), riga["persona"], riga["tempo"],
                     chiave(riga.get("clitico") or ""), chiave(riga["forma"])])


def leggi_file() -> tuple:
    """Le righe di commento e le righe di dati, nell'ordine del file."""
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
    """Le righe del file con quelle dei paradigmi.

    Una riga di S015 **scritta a mano** (senza `forma_fonte`) che ha la stessa
    casella e la stessa forma di una riga dei paradigmi viene sostituita da
    quella, **tenendo il suo id**: e' la stessa forma della stessa fonte, e
    adesso porta la proclitica e la citazione. Le righe che vengono da altre
    citazioni (S015 negli esempi delle regole, S001) restano come sono.
    """
    per_chiave = {}
    for riga in nuove:
        per_chiave.setdefault(_chiave_riga(riga), riga)
    usate, risultato = set(), []
    for riga in esistenti:
        k = _chiave_riga(riga)
        if (riga.get("fonte") == ID_FONTE and k in per_chiave
                and k not in usate
                and (riga.get("forma_fonte") or riga["id"] >= "C0019")):
            nuova = dict(per_chiave[k])
            nuova = {"id": riga["id"], **nuova}
            risultato.append(nuova)
            usate.add(k)
        else:
            risultato.append(riga)
    maggiore = max(int(r["id"][1:]) for r in esistenti) if esistenti else 0
    aggiunte = 0
    for riga in nuove:
        k = _chiave_riga(riga)
        if k in usate:
            continue
        usate.add(k)
        aggiunte += 1
        risultato.append({"id": "C%04d" % (maggiore + aggiunte), **riga})
    return risultato, aggiunte


def main() -> int:
    ap = argparse.ArgumentParser(description="I paradigmi di S015.")
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args()

    tabella = _tabella()
    righe, fuori = righe_prodotte(tabella, _glossario())
    mancanti = controlla_grezzo()
    commenti, esistenti = leggi_file()
    risultato, aggiunte = unisci(esistenti, righe)

    print("paradigmi                   %4d" % len(PARADIGMI))
    print("caselle citate              %4d" % len(caselle_citate()))
    print("righe dai paradigmi         %4d" % len(righe))
    print("caselle lasciate fuori      %4d" % len(fuori))
    print("omografi (non si cercano)   %4d"
          % sum(1 for r in righe if r.get("omografo")))
    print("righe nel file, prima       %4d" % len(esistenti))
    print("righe nel file, dopo        %4d  (%d nuove)"
          % (len(risultato), aggiunte))
    if os.path.exists(GREZZO):
        print("caselle non trovate nella fonte %d" % len(mancanti))
    else:
        print("il testo della fonte non e' in %s: il confronto con la "
              "pagina non si rifa'" % os.path.relpath(GREZZO, RADICE))
    for lemma, tempo, persona, casella, motivo in fuori:
        print("  fuori: %s %s %s «%s»: %s" % (lemma, tempo, persona, casella,
                                              motivo))
    for casella in mancanti:
        print("  NON NELLA FONTE: %s" % casella)
    if args.prova:
        return 0
    if mancanti:
        raise SystemExit("delle caselle non sono nella fonte: non scrivo")

    sistema = None
    for linea in commenti:
        if linea.startswith("// SISTEMA"):
            sistema = json.loads(linea[len("// SISTEMA"):].strip())
    if sistema is None:
        raise SystemExit("dati/verbi.jsonl non ha la riga SISTEMA")
    for tempo in TEMPI:
        if tempo not in sistema["tempi"]:
            sistema["tempi"].append(tempo)
    sistema["forme"] = len(risultato)
    sistema["paradigmi"] = sorted({p["lemma"] for p in PARADIGMI})
    sistema["fuori"] = [[l, t, p] for l, t, p, _, _ in fuori]
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
    raise SystemExit(main())
