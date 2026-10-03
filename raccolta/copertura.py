#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Misura quanto italiano copre il glossario, e dice le parole da cercare.

Il problema che risolve: il glossario puo' essere grande e coprire comunque
poco dell'italiano che qualcuno scrive. Il numero delle voci non dice niente
sulla copertura, e senza copertura non si sa dove cercare.

**Il metro e' fatto di lemmi, e questa e' la parte che conta.** La prima
versione di questo script usava una lista di frequenza ricavata dai
sottotitoli, e il numero che dava era falso: diceva che al glossario mancava
il 89% dell'italiano, ma le parole piu' frequenti «mancanti» erano
`sono`, `ho`, `stato`, `mangi`. Quelle non mancano: il glossario contiene
`essere`, `avere`, `stato`, `mangiare`, cioe' i **lemmi**, e un vocabolario
e' fatto di lemmi. Confrontare un lemma con una coniugazione e' come
confrontare «cane» con «cani» e concludere che manca il cane.

Adesso il metro sono i tre elenchi **lemmatizzati** dell'ItWaC (Baroni,
Bernardini, Ferraresi, Zanchetta 2009), via `franfranz/Word_Frequency_Lists_ITA`,
licenza MIT. Sono gia' lemmi: nel file dei sostantivi la riga `"anni"` porta
il lemma `anno`, e il project's glossario e' costruito su lemmi.

Quello che la copertura NON dice, e va detto insieme al numero:

- **l'ItWaC viene dal web italiano**, non da un vocabolario scolastico e non
  dai sottotitoli: e' la lingua di come si scrive, non di come si parla a
  scuola. Un progetto didattico ci trovera' parole che un insegnante non
  userebbe e ne mancheranno altre che userebbe tutti i giorni;
- **una parola e' coperta solo se il glossario la trova cercandola dall'italiano**
  (`cerca_italiano`), non per vicinanza e non per traduzione inversa. Se
  scrivi «sedia» e il glossario non ha una voce che si chiami «sedia», per il
  motore quella parola non c'e', e il numero la conta come mancante. E' il
  conteggio severo, ed e' quello giusto.

Le parole funzionali sono contate a parte e non sono mancanze: articoli,
preposizioni e congiunzioni stanno in `morfologia.py` e nel glossario non ci
devono stare (vedi `TestVociMeccaniche` in `prove/test_traduttore.py`).

Uso:
    python3 copertura.py                 # il quadro
    python3 copertura.py --limite 300   # le prime 300 da cercare
    python3 copertura.py --json         # per un altro programma
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.glossario import Glossario  # noqa: E402

GREZZI = os.path.join(RADICE, "raccolta", "grezzi")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")

# I tre elenchi. `verb` e' gia' una lista di soli lemmi con due colonne;
# `noun` e `adj` hanno forma, frequenza e lemma, e vanno presi per lemma.
ITWAC = {
    "sostantivi": ("itwac_noun.csv", "lemma"),
    "aggettivi": ("itwac_adj.csv", "lemma"),
    "verbi": ("itwac_verb.csv", "Lemma"),
}

# Sotto questa frequenza l'elenco parla del web e non della lingua: nomi
# propri, sigle, parole di una volta. Non sono parole da cercare: sono rumore.
SOGLIA_FREQUENZA = 2000

# Le parole che il motore tratta come regole e non come voci. Non sono
# mancanze, e contarle come tali direbbe che il glossario e' piu' vuoto di
# quanto sia. Elenco dichiarato a mano: sono poche parole note, e un elenco
# dichiarato si puo' discutere, cosa che non si puo' fare con una formula.
FUNZIONALI = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "l",
    "a", "al", "alla", "ai", "agli", "alle", "da", "dal", "dalla", "dai",
    "dagli", "dalle", "di", "del", "dello", "della", "dei", "degli", "delle",
    "in", "nel", "nella", "nei", "negli", "nelle", "con", "col", "cui",
    "per", "pur", "tra", "fra", "contro", "su", "sul", "sulla", "sui",
    "sugli", "sulle", "sotto", "sopra", "dentro", "fuori", "senza", "dopo",
    "e", "ed", "o", "od", "ma", "che", "come", "se", "quando", "perché",
    "perche", "dove", "mentre", "quindi", "però", "pero", "oppure", "cioè",
    "cioe", "anche", "ancora", "solo", "soltanto", "non", "né", "ne",
    "quel", "quella", "quelle", "quelli", "questo", "questa", "queste",
    "questi", "ci", "vi", "si", "mi", "ti", "lui", "lei", "loro", "me",
    "te", "può", "puo", "più", "piu", "già", "gia", "sì", "no",
    # Le forme del verbo essere e avere. Non sono funzionali in senso stretto,
    # ma hanno la stessa proprietà per questo calcolo: sono forme, non lemmi,
    # e il glossario contiene `essere`, non `sono`. Senza questa riga la
    # copertura si abbassa di qualche punto perche' `sono` risulta mancante
    # mentre il motore la traduce. E' la riga che distingue un metro giusto
    # da un metro che premia il conteggio.
    "sono", "sei", "è", "era", "erano", "ero", "siamo", "siete", "stata",
    "stato", "stati", "state", "essere", "ho", "hai", "ha", "abbiamo",
    "avete", "hanno", "avevo", "avevi", "aveva", "avevamo", "avere",
}

# Una parola che contiene una cifra o un segno non e' una parola: e' rumore.
NON_PAROLA = re.compile(r"[0-9@#$%^&*+=|\\/<>~`{}\[\]]")

PAROLA = re.compile(r"^[a-zà-ÿ][a-zà-ÿ'\-]*$", re.I)


def leggi_elenco(percorso: str, colonna_lemma: str) -> list:
    """(lemma, frequenza) dalla colonna indicata, sopra la soglia.

    I CSV sono in **latin-1**, non in UTF-8: `attività` c'è` come due byte
    `0xe0`. Non e' un dettaglio, e' il motivo per cui leggere questi file
    con `encoding="utf-8"` fa fallire lo script a meta' dell'elenco, su una
    riga che sembra normale. Il file e' dichiarato cosi' dal suo autore e
    gli accenti italiani ci sono tutti, quindi va letto nella sua lingua.
    """
    coppie = []
    with open(percorso, encoding="latin-1", newline="") as f:
        lettore = csv.DictReader(f)
        for riga in lettore:
            lemma = (riga.get(colonna_lemma) or "").strip().strip('"')
            grezzo = riga.get("Freq") or ""
            if not lemma or not grezzo:
                continue
            try:
                numero = int(float(grezzo))
            except ValueError:
                continue
            if numero < SOGLIA_FREQUENZA:
                continue
            coppie.append((lemma, numero))
    return coppie


def carica_metro() -> dict:
    metro = {}
    mancanti_file = []
    for nome, (file, colonna) in ITWAC.items():
        percorso = os.path.join(GREZZI, file)
        if not os.path.exists(percorso):
            mancanti_file.append(file)
            continue
        metro[nome] = leggi_elenco(percorso, colonna)
    if mancanti_file:
        print("Mancano questi elenchi in raccolta/grezzi/:")
        for f in mancanti_file:
            print("  %s" % f)
        print()
        print("Si scaricano da "
              "https://github.com/franfranz/Word_Frequency_Lists_ITA (MIT):")
        print("  curl -sL -o raccolta/grezzi/itwac_noun.csv \\")
        print("    https://raw.githubusercontent.com/franfranz/"
              "Word_Frequency_Lists_ITA/master/"
              "itwac_nouns_lemmas_notail_2_0_0.csv")
        sys.exit(1)
    return metro


def analizza(glossario: Glossario, metro: dict) -> dict:
    coperte, mancanti, funzionali, scartate = [], [], 0, 0
    visti = set()
    for categoria, coppie in metro.items():
        for lemma, numero in coppie:
            if NON_PAROLA.search(lemma) or not PAROLA.match(lemma):
                scartate += 1
                continue
            if lemma.lower() in FUNZIONALI:
                funzionali += 1
                continue
            # Lo stesso lemma puo' comparire in piu' categorie: si conta una
            # volta sola, altrimenti il totale non e' un totale.
            if lemma.lower() in visti:
                continue
            visti.add(lemma.lower())
            voce = {"lemma": lemma, "frequenza": numero, "categoria": categoria}
            if glossario.cerca_italiano(lemma):
                coperte.append(voce)
            else:
                mancanti.append(voce)
    mancanti.sort(key=lambda v: -v["frequenza"])
    return {"coperte": coperte, "mancanti": mancanti,
            "funzionali": funzionali, "scartate": scartate}


def main() -> int:
    limite = None
    for i, a in enumerate(sys.argv):
        if a == "--limite" and i + 1 < len(sys.argv):
            limite = int(sys.argv[i + 1])
    come_json = "--json" in sys.argv

    glossario = Glossario.da_file(GLOSSARIO)
    metro = carica_metro()
    esito = analizza(glossario, metro)

    n_coperte = len(esito["coperte"])
    n_mancanti = len(esito["mancanti"])
    totale = n_coperte + n_mancanti
    percentuale = (100.0 * n_coperte / totale) if totale else 0.0

    if come_json:
        print(json.dumps({
            "metro": "ItWaC lemmi (Baroni 2009), via franfranz, MIT",
            "soglia_frequenza": SOGLIA_FREQUENZA,
            "funzionali_esclusi": esito["funzionali"],
            "non_parole_scartate": esito["scartate"],
            "coperte": n_coperte,
            "mancanti": n_mancanti,
            "percentuale": round(percentuale, 2),
            "da_cercare": esito["mancanti"][:limite or len(esito["mancanti"])],
        }, ensure_ascii=False, indent=2))
        return 0

    print("metro: %d lemmi italiani con frequenza sopra %d (ItWaC, MIT)"
          % (totale, SOGLIA_FREQUENZA))
    print("  sostantivi, aggettivi e verbi: i tre elenchi sono gia' lemmatizzati.")
    print()
    print("funzionali esclusi     %6d   articoli, preposizioni, congiunzioni: il" % esito["funzionali"])
    print("                              motore li tratta a parte")
    print("non-parole scartate    %6d   nomi propri, sigle, rumore" % esito["scartate"])
    print("coperte dal glossario  %6d   %.1f%%" % (n_coperte, percentuale))
    print("da cercare             %6d   %.1f%%" % (n_mancanti, 100.0 - percentuale))
    print()
    print("Una parola e' coperta solo se il glossario la trova cercandola")
    print("dall'italiano. E' il conteggio severo: e' quello che il motore")
    print("risponde davvero a chi scrive una frase.")
    print()
    quante = limite or 60
    print("le %d piu' frequenti da cercare:" % min(quante, n_mancanti))
    for voce in esito["mancanti"][:quante]:
        print("  %-24s %9d  %s" % (voce["lemma"], voce["frequenza"], voce["categoria"]))
    if not limite:
        print()
        print("Per tutto l'elenco: --limite 20000 | --json")
    return 0


if __name__ == "__main__":
    sys.exit(main())