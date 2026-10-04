#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le forme verbali **attestate** nelle fonti, e nient'altro.

**Il problema.** Il traduttore non coniuga, e il motivo non e' che manca il
codice: e' che **manca il paradigma**. Nel repository non c'e' nessuna fonte che
documenti la coniugazione ferrarese tabellata. Quello che c'e' e' sparse in due
fonti che il progetto ha gia', e sono poche forme vere:

- **S015**, R. Bigoni «Il Ferrarese», note linguistiche, sezione 4: il soggetto
  con la proclitica, la negazione `aŋ`, il `noi` in `-ŋ`, gli ausiliari. Le sue
  frasi sono gia' in `dati/regole_grammaticali.json`, quindi sono **una seconda
  copia** della fonte dentro il repository, e il generatore le verifica la' per
  la': ogni forma che entra deve trovarsi in un esempio che quel file contiene
  davvero.
- **S001**, G. Biondelli «Saggio sui dialetti gallo-italici», 1853: le forme
  finite del ferrarese nelle tavole di confronto con il bolognese e il
  parmigiano. Il grezzo e' in `raccolta/grezzi/biondelli_1853.txt` e ogni riga
  qui porta il numero di riga: se il testo cambia, il generatore si ferma.

**Perche' una tabella scritta a mano e non una regex sul testo.** Perche' una
regex aggiunge forme che la fonte non scrive e perde forme che scrive, e il
progetto non accetta nessuna delle due cose senza accorgersene. Qui ogni riga
e' una **citazione**: la frase, la regola in cui compare e la forma che se ne
ricava. Il generatore non indovina niente, controlla.

**Quello che non c'e' e che resta dichiarato.** Il presente dei verbi regolari
per le quattro coniugazioni, il tu, il voi, il terzo plurale, il futuro, il
condizionale, l'imperativo delle altre persone. Nessuna fonte del repository li
dichiara, quindi nessuna riga li inventa. Il buco e' scritto nel file che
questo generatore produce, e `verifica` lo controlla.

Uso:
    python3 raccolta/da_verbi.py --prova    # mostra, non scrive
    python3 raccolta/da_verbi.py            # scrive in dati/verbi.jsonl
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.normalizza import chiave  # noqa: E402

REGOLE = os.path.join(RADICE, "dati", "regole_grammaticali.json")
GREZZO_BIONDELLI = os.path.join(RADICE, "raccolta", "grezzi",
                                "biondelli_1853.txt")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VERBI = os.path.join(RADICE, "dati", "verbi.jsonl")

# Le persone e i tempi che il progetto sa nominare. Non e' una scelta estetica:
# una forma con una persona che non e' in questa lista non si puo' cercare, e
# quindi non deve poter entrare.
PERSONE = ("1sing", "2sing", "3sing", "1plur", "2plur", "3plur",
           "imperativo", "infinito")
TEMPI = ("presente", "passato", "gerundio", "participio")
# Le due forme non finite non hanno persona: un gerundio e un participio sono
# gli stessi per tutti. Una riga senza persona e' ammessa **solo** con questi
# due tempi, e il controllo F16 lo verifica: una riga senza persona con un
# tempo finito sarebbe una casella inventata.
TEMPI_SENZA_PERSONA = ("gerundio", "participio")

# Le forme che le fonti dichiarano e che il progetto NON ha. Sono scritte qui e
# nel file prodotto, perche' un buco dichiarato e' un lavoro da fare e un buco
# taciuto e' un lavoro che si crede fatto.
VUOTO = (
    ("2sing", "presente"), ("2plur", "presente"), ("3plur", "presente"),
    ("2sing", "passato"), ("2plur", "passato"), ("3plur", "passato"),
    ("futuro", "presente"), ("condizionale", "presente"),
)

# Ogni riga e' una citazione. `dove` dice dove la fonte scrive la frase, e la
# verifica e' dentro `controlla()`: nessuna forma entra senza.
PEROLE = [
    # --- S015, Bigoni, sezione 4 (gia' in dati/regole_grammaticali.json) ---
    {"lemma": "pjóvar", "persona": "3sing", "tempo": "presente",
     "forma": "pióv", "clitico": "", "italiano": "piove",
     "fonte": "S015", "dove": "§4", "regola": "R030", "frase": "a pióv",
     "nota": "Terza persona singolare. Il soggetto e' la proclitica «a»."},
    {"lemma": "vlér", "persona": "1sing", "tempo": "presente",
     "forma": "vój", "clitico": "", "italiano": "voglio",
     "fonte": "S015", "dove": "§4", "regola": "R031",
     "frase": "aŋ vój brìša",
     "nota": "La negazione e' «aŋ» attaccata alla proclitica: non e' parte "
             "del verbo."},
    {"lemma": "avér", "persona": "1sing", "tempo": "presente",
     "forma": "ò", "clitico": "aj", "italiano": "ho",
     "fonte": "S015", "dove": "§4", "regola": "R036", "frase": "mi aj ò",
     "nota": "Ausiliare. Il clitico «aj» precede il verbo e ne cambia la "
             "forma: la stessa persona e lo stesso tempo hanno due forme "
             "diverse, quindi il clitico fa parte della chiave."},
    {"lemma": "avér", "persona": "1sing", "tempo": "presente",
     "forma": "o", "clitico": "ɣ", "italiano": "ne ho",
     "fonte": "S015", "dove": "§4", "regola": "R036", "frase": "mi a ɣ o",
     "nota": "Stessa persona, forma diversa: e' quello che dichiara R036, "
             "«avér» si raddoppia con una «ɣ» quando e' dimostrativo."},
    {"lemma": "kaŋtàr", "persona": "1plur", "tempo": "presente",
     "forma": "kaŋtéŋ", "clitico": "", "italiano": "cantiamo",
     "fonte": "S015", "dove": "§4", "regola": "R035",
     "frase": "nu a kaŋtéŋ",
     "nota": "Il noi plurale in «-ŋ», dove l'italiano ha la «m»."},
    {"lemma": "sér", "persona": "1plur", "tempo": "presente",
     "forma": "séŋ", "clitico": "", "italiano": "siamo",
     "fonte": "S015", "dove": "§4", "regola": "R035", "frase": "nu a séŋ",
     "nota": "Ausiliare «èsar» di R036, scritto «sér» nel glossario. Il nome "
             "e' diverso fra la regola e il glossario e il progetto non li "
             "concilia: entrambe le forme sono dichiarate."},
    {"lemma": "aŋdàr", "persona": "", "tempo": "participio",
     "forma": "aŋdà", "clitico": "", "italiano": "sono andato, andai",
     "fonte": "S015", "dove": "§4", "regola": "R032",
     "frase": "a són aŋdà",
     "nota": "La frase porta anche l'ausiliare «són», che e' una forma finita "
             "di essere; l'italiano non ha soggetto in «sono andato» e quindi "
             "**la persona e' vuota**, perche' determinarne una sarebbe "
             "inventarla. Nessuna coniugazione regolare e' ipotizzata per il "
             "passato prossimo."},
    {"lemma": "Caminàr", "persona": "imperativo", "tempo": "presente",
     "forma": "kamìna", "clitico": "", "italiano": "cammina!",
     "fonte": "S015", "dove": "§4", "regola": "R030", "frase": "kamìna!",
     "nota": "All'imperativo il soggetto si omette: e' quello che dichiara "
             "R030."},

    # --- S001, Biondelli 1853, tavole di confronto sul ferrarese ----------
    {"lemma": "aŋdàr", "persona": "1sing", "tempo": "passato",
     "forma": "andò", "clitico": "", "italiano": "andai",
     "fonte": "S001", "dove": "pag. 497, riga 15815",
     "riga": 15815, "frase": "Ferrarese    andò",
     "nota": "Biondelli: il passato finisce in «-ò», come il bolognese. "
             "«andai» e' l'italiano della stessa casella."},
    {"lemma": "bašàr", "persona": "1sing", "tempo": "passato",
     "forma": "basò", "clitico": "", "italiano": "baciò",
     "fonte": "S001", "dove": "pag. 497, riga 15815",
     "riga": 15815, "frase": "Ferrarese    andò",
     "nota": "Stessa riga della precedente: Biondelli elenca i tre esempi "
             "nella stessa tabella."},
    {"lemma": "portàr", "persona": "1sing", "tempo": "passato",
     "forma": "purtò", "clitico": "", "italiano": "portò",
     "fonte": "S001", "dove": "pag. 497, riga 15815",
     "riga": 15815, "frase": "Ferrarese    andò",
     "nota": "Stessa riga: terzo esempio della tabella."},
    {"lemma": "aŋdàr", "persona": "1plur", "tempo": "passato",
     "forma": "i andò", "clitico": "i", "italiano": "andammo",
     "fonte": "S001", "dove": "pag. 497, riga 15815",
     "riga": 15815, "frase": "Ferrarese    andò",
     "nota": "**In disaccordo con S015.** Bigoni scrive il noi plurale in "
             "«-ŋ» (R035), Biondelli lo scrive con una proclitica «i» "
             "davanti: «i andò» contro «nu a kaŋtéŋ». Il progetto non sceglie, "
             "le due forme restano e il disaccordo e' dichiarato qui e dal "
             "controllo F16."},
    {"lemma": "portàr", "persona": "1plur", "tempo": "passato",
     "forma": "i purtò", "clitico": "i", "italiano": "portammo",
     "fonte": "S001", "dove": "pag. 497, riga 15815",
     "riga": 15815, "frase": "Ferrarese    andò",
     "nota": "Secondo esempio del noi plurale, stesso disaccordo con S015."},
    {"lemma": "sér", "persona": "infinito", "tempo": "gerundio",
     "forma": "essènd", "clitico": "", "italiano": "essendo",
     "fonte": "S001", "dove": "pag. 499, riga 15897",
     "riga": 15897, "frase": "Ferrarese    essènd",
     "nota": "Gerundio in «-ènd»."},
    {"lemma": "Dir", "persona": "infinito", "tempo": "gerundio",
     "forma": "disènd", "clitico": "", "italiano": "dicendo",
     "fonte": "S001", "dove": "pag. 499, riga 15897",
     "riga": 15897, "frase": "Ferrarese    essènd",
     "nota": "Stessa riga: cinque verbi nella stessa tabella."},
    {"lemma": "Far", "persona": "infinito", "tempo": "gerundio",
     "forma": "fasènd", "clitico": "", "italiano": "facendo",
     "fonte": "S001", "dove": "pag. 499, riga 15897",
     "riga": 15897, "frase": "Ferrarese    essènd",
     "nota": "Stessa riga."},
    {"lemma": "Tgnìr", "persona": "infinito", "tempo": "gerundio",
     "forma": "tulènd", "clitico": "", "italiano": "togliendo",
     "fonte": "S001", "dove": "pag. 499, riga 15897",
     "riga": 15897, "frase": "Ferrarese    essènd",
     "nota": "Il glossario scrive «Tgnìr» per il lemma di «tenere» "
             "(V9350) e qui Biondelli elenca «togliendo»: e' la stessa voce "
             "solo se si accetta che il glossario e la tavola dicano cose "
             "diverse. La riga resta, e il nome del lemma e' quello del "
             "glossario."},
    {"lemma": "vñir", "persona": "infinito", "tempo": "gerundio",
     "forma": "vegnènd", "clitico": "", "italiano": "venendo",
     "fonte": "S001", "dove": "pag. 499, riga 15897",
     "riga": 15897, "frase": "Ferrarese    essènd",
     "nota": "Stessa riga."},
]

TESTATA = """\
// --- IL SISTEMA, dichiarato perché si possa controllarlo -----------------------------
//
// **Che cosa è questo file.** Le forme verbali **finite e non finite** che le fonti
// del repository attestano per iscritto, con la fonte accanto a ogni riga. Non è un
// coniugatore e nonvuole esserlo: è un indice di ciò che è documentato.
//
// **Che cosa non è.** Non c'è il paradigma. Nel repository non esiste una fonte che
// tabelli la coniugazione ferrarese: non la prima, né la seconda, né la terza, né
// l'imperativo oltre la seconda persona, né il futuro, né il condizionale. Quello
// che si trova è sparso in due fonti che il progetto ha già, e sono poche forme vere.
//
// **Perché questo file esiste comunque.** Perché il traduttore smetta di fallire in
// silenzio. Una parola coniugata che il motore non sa tradurre è un buco; un buco
// dichiarato è un lavoro da fare, e questa riga è il posto dove il lavoro è scritto.
//
// Le forme entrano solo da `raccolta/da_verbi.py`, che cita la frase della fonte e
// la verifica: per S015 dentro `dati/regole_grammaticali.json`, per S001 dentro il
// grezzo di Biondelli, con il numero di riga. Una forma che non si trova nella fonte
// non entra.
//
// Personas: {persone}.
// Tempi: {tempi}.
// Tempi che non hanno persona, perché sono gli stessi per tutti: {senza_persona}.
//
// **I buchi dichiarati.** Non c'è nessuna fonte che scriva queste caselle, quindi
// nessuna riga le riempe e nessun codice le ricava:
//
// {vuoto}
//
// **Un disaccordo fra due fonti, non risolto.** Il noi plurale: S015 (R035) lo
// scrive in «-ŋ» — «nu a kaŋtéŋ» — e S001 lo scrive con una proclitica «i»
// — «i andò». Le due forme sono in questo file e il controllo F16 lo segnala.
// Sceglierefra le due è una decisione che spetta a un parlante, non a un programma.
// ---------------------------------------------------------------------------------
"""


def _spazi(testo: str) -> str:
    return " ".join(testo.split())


def regole_verbi() -> dict:
    """Le regole di `regole_grammaticali.json` con i loro esempi, per id."""
    with io.open(REGOLE, encoding="utf-8") as f:
        grezzo = json.load(f)
    return {r["id"]: r for r in grezzo.get("regole", [])
            if r.get("categoria") == "verbi"}


def righe_grezzo() -> dict:
    """Il grezzo di Biondelli, riga per riga: numero 1 com'era nel file."""
    with io.open(GREZZO_BIONDELLI, encoding="utf-8") as f:
        return {n: _spazi(riga) for n, riga in enumerate(f, 1)}


def glossario_per_ferrarese() -> dict:
    """Le voci del glossario indicizzate dalla forma ferrarese."""
    per_ferrarese = {}
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.lstrip().startswith("//"):
                continue
            voce = json.loads(riga)
            per_ferrarese.setdefault(chiave(voce.get("ferrarese") or ""), voce)
    return per_ferrarese


def controlla(perole: list, regole: dict, righe: dict) -> list:
    """Le forme che **non** trovano la frase nella fonte. Una lista, non un errore.

    Il motivo per cui una forma rotta va stampata e non sollevata e' che la fonte
    puo' cambiare sotto i piedi del progetto — Biondelli e' una trascrizione
    OCR — e in quel caso chi legge deve vedere «questa forma non e' piu' nella
    fonte» e decidere, non trovarsi un programma fermo senza sapere perche'.
    """
    problemi = []
    for forma in perole:
        if forma.get("regola"):
            regola = regole.get(forma["regola"])
            if regola is None:
                problemi.append("%s: la regola %s non c'e' fra quelle sui "
                                "verbi" % (forma["forma"], forma["regola"]))
                continue
            frasi = [e.get("fe", "") for e in regola.get("esempi", [])]
            if forma["frase"] not in frasi:
                problemi.append(
                    "%s: la frase %r non e' un esempio della regola %s"
                    % (forma["forma"], forma["frase"], forma["regola"]))
                continue
            if forma["forma"] not in forma["frase"]:
                problemi.append("%s: la forma non sta nella frase %r"
                                % (forma["forma"], forma["frase"]))
                continue
        elif forma.get("riga"):
            riga = righe.get(forma["riga"], "")
            if _spazi(forma["frase"]) not in riga:
                problemi.append("%s: la riga %d del grezzo non contiene piu' %r"
                                % (forma["forma"], forma["riga"],
                                   _spazi(forma["frase"])))
                continue
            if forma["forma"] not in riga:
                problemi.append("%s: la forma non sta piu' nella riga %d"
                                % (forma["forma"], forma["riga"]))
                continue
        else:
            problemi.append("%s: non dice dove si verifica" % forma["forma"])
    return problemi


def forma_chiave(forma: dict) -> str:
    return "|".join([chiave(forma["lemma"]), forma["persona"], forma["tempo"],
                     chiave(forma.get("clitico") or "")])


def righe_prodotte(perole: list, glossario: dict) -> list:
    righe = []
    for numero, forma in enumerate(perole, 1):
        voce = glossario.get(chiave(forma["lemma"]))
        riga = {
            "id": "C%04d" % numero,
            "lemma": forma["lemma"],
            "lemma_id": voce["id"] if voce else "",
            "persona": forma["persona"],
            "tempo": forma["tempo"],
            "forma": forma["forma"],
            "clitico": forma.get("clitico", ""),
            "italiano": forma["italiano"],
            "fonte": forma["fonte"],
            "dove": forma["dove"],
            "nota": forma["nota"],
            "attendibilita": "I",
            "da_verificare": True,
        }
        if voce is None:
            # Il lemma e' scritto qui, ma il glossario non ce l'ha: la riga
            # entra lo stesso perche' la forma e' attestata, e il vuoto si
            # dichiara invece di nascondersi dietro una riga senza lemma.
            riga["lemma_nel_glossario"] = False
            riga["nota"] += (" Il lemma non e' nel glossario: la riga porta "
                             "solo la forma attestata e il nome che le ha "
                             "dato questa fonte.")
        else:
            riga["lemma_nel_glossario"] = True
        righe.append(riga)
    return righe


def esistente() -> list:
    if not os.path.exists(VERBI):
        return []
    righe = []
    with io.open(VERBI, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.lstrip().startswith("//"):
                righe.append(json.loads(riga))
    return righe


def main() -> int:
    ap = argparse.ArgumentParser(description="Le forme verbali attestate.")
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args()

    regole = regole_verbi()
    grezzo = righe_grezzo()
    glossario = glossario_per_ferrarese()

    problemi = controlla(PEROLE, regole, grezzo)
    righe = righe_prodotte(PEROLE, glossario)

    gia = {forma_chiave(r): r["id"] for r in esistente()}
    nuove = [r for r in righe if forma_chiave(r) not in gia]
    ripetute = [r for r in righe if forma_chiave(r) in gia]

    print("forme citate nelle fonti   %4d" % len(PEROLE))
    print("gia' in dati/verbi.jsonl   %4d" % len(ripetute))
    print("da scrivere                %4d" % len(nuove))
    print("non verificabili           %4d   la fonte non contiene piu' la "
          "frase" % len(problemi))
    print("senza lemma nel glossario  %4d   la forma e' attestata, il nome "
          "no" % len([r for r in righe if not r["lemma_nel_glossario"]]))
    print("buchi dichiarati           %4d   persona/tempo che nessuna "
          "fonte scrive" % len(VUOTO))
    print()
    for problema in problemi:
        print("  ATTENZIONE %s" % problema)
    print()
    for riga in righe:
        print("  %-6s %-10s %-9s %-10s %-22s %s"
              % (riga["id"], riga["lemma"], riga["persona"], riga["forma"],
                 riga["italiano"], riga["fonte"]))
    if args.prova:
        return 0

    if problemi:
        raise SystemExit("una forma non e' piu' nella sua fonte: non scrivo "
                         "niente, perche' il file deve dire solo cio' che le "
                         "fonti scrivono")
    if not nuove:
        print("niente da scrivere.")
        return 0

    if not os.path.exists(VERBI):
        with io.open(VERBI, "w", encoding="utf-8", newline="\n") as f:
            f.write(TESTATA.format(persone=", ".join(PERSONE),
                                   tempi=", ".join(TEMPI),
                                   senza_persona=", ".join(
                                       TEMPI_SENZA_PERSONA),
                                   vuoto="\n".join(
                                       "//   - %s %s" % (p, t)
                                       for p, t in VUOTO)))
            f.write('// SISTEMA %s\n'
                    % json.dumps({"persone": list(PERSONE),
                                  "tempi": list(TEMPI),
                                  "senza_persona": list(TEMPI_SENZA_PERSONA),
                                  "vuoto": [list(v) for v in VUOTO],
                                  "forme": len(righe)},
                               ensure_ascii=False))
    with io.open(VERBI, "a", encoding="utf-8", newline="\n") as f:
        for riga in nuove:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d forme da %s a %s" % (len(nuove), nuove[0]["id"],
                                            nuove[-1]["id"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
