#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'analisi grammaticale dell'italiano, presa da un corpus annotato.

Il progetto ha una regola che riguarda tutti i dati: nessuna risposta senza
fonte. E ha una regola che riguarda la traduzione: prima di riscrivere una
parola si deve sapere **che cos'e'**. Le due cose si incontrano qui, e quindi
questo modulo chiede a una fonte che classifica l'italiano gia' scritto, senza
chiedere a nessuno di classificare niente a memoria.

**La fonte.** Il corpus annotato italiano di Universal Dependencies
(`UniversalDependencies/Italian-UD`), nella versione che il file scaricato
dichiara. E' scelto perche' annota parole **in frasi**: e' la domanda che si
pone un traduttore, che non mette mai una parola isolata. Licenza CC BY-SA 4.0,
dichiarata dalla fonte stessa e riportata in ogni riga, perche' una riga senza
licenza non si puo' pubblicare.

**Che cosa viene preso.** Solo due colonne del file: la forma della parola e la
sua categoria universale (UPOS). Nient'altro: non la definizione, non la
traduzione, non la frequenza come misura di importanza. Il file di partenza non
entra nel repository — sono megabytes di frasi di terzi — e nel repository
finisce **solo** l'analisi delle parole che al progetto servono, con la frase
che le contiene come prova, troncata e dichiarata.

**Che cosa non viene fatto, e perche'.**

- Non si sceglie una classe quando le annotazioni non concordano: la riga porta
  tutte le classi e il loro conto, e `sorgenti/traduttore/italiano.py` prende la
  prima solo dichiarando quante ce n'erano. Un tag sbagliato scelto da un
  programma e' un'invenzione con il timbro di una fonte.
- Non si deduplica per frequenza: una parola che due volte e' un nome e una
  volta un verbo resta con tutte e tre le voci, e il lettore vede il dissenso.
- Non si riempiono le caselle vuote. Una forma assente dal corpus resta
  assente, e il progetto continua a dire `ignota`: e' la differenza fra un
  glossario che sa e uno che finge.

**Lo stato di questa raccolta.** Da questa macchina i file del treebank **non
si scaricano**: GitHub e HuggingFace rispondono 404 sui percorsi dei dati, e
`dati/italiano.jsonl` quindi non esiste ancora. Il modulo e' dichiarato e
pronto, e quando la rete lascia passare quei file il file si genera senza
toccare n'altro: `raccolta/moderni.py` ha gia' fatto questo per Wiktionary.

Uso:

    python3 raccolta/italiano.py --file percorso/it-ud-train.conllu
    python3 raccolta/italiano.py --file ... --versione r2.13
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
USCITA = os.path.join(RADICE, "dati", "italiano.jsonl")

LICENZA = "CC BY-SA 4.0"
# L'annotazione e' manuale e pubblicata, quindi e' documentata: `D`.
ATTENDIBILITA = "D"

# Una parola che si puo' analizzare: lettere, apostrofo e trattino. Niente
# numeri, niente punteggiatura, niente formule: quelle non sono nomi e verbi e
# analizzarle significherebbe inventare una classe per un simbolo.
PAROLA = re.compile(r"^[a-zA-ZÀ-ÿ'][a-zA-Zà-ÿ'-]+$")


def _chiave(forma: str) -> str:
    return forma.strip().lower()


def serve_il_progetto(forma: str, richieste: set) -> bool:
    """Il progetto tiene l'analista delle parole che almeno chiede.

    Il filtro e' dichiarato perche' e' una scelta, non un dettaglio: si tiene
    solo cio' che il glossario usa. Il resto del corpus non e' di nessuna
    utilita' per questo progetto e occuperebbe spazio per essere guardato da
    nessuno.
    """
    return _chiave(forma) in richieste


def parole_richieste() -> set:
    richieste = set()
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("//"):
                continue
            voce = json.loads(riga)
            for parte in (voce.get("italiano") or "").split():
                if PAROLA.match(parte):
                    richieste.add(_chiave(parte))
            for parte in (voce.get("principale_italiano") or "").split():
                if PAROLA.match(parte):
                    richieste.add(_chiave(parte))
    return richieste


def leggi(percorso: str, richieste: set) -> dict:
    """Raggruppa per forma le classi che il corpus annota.

    Tiene anche **una** frase per forma, la prima in cui compare, perche' una
    classe senza contesto e' una classe che nessuno puo' controllare. La frase
    e' troncata a `MAX_FRASE` caratteri e il troncamento e' dichiarato nella
    riga: una prova tagliata a meta' senza dirlo sembra una prova intera.
    """
    MAX_FRASE = 140
    raccolte = {}
    frase = ""
    numero = 0
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.rstrip("\n")
            if riga.startswith("# text = "):
                frase = riga[len("# text = "):]
                numero += 1
                continue
            if not riga or riga.startswith("#"):
                continue
            colonne = riga.split("\t")
            if len(colonne) < 4:
                continue
            forma, tag = colonne[1], colonne[3]
            if not PAROLA.match(forma):
                continue
            chiave = _chiave(forma)
            if not serve_il_progetto(forma, richieste):
                continue
            voce = raccolte.setdefault(chiave, {"classi": collections.Counter(),
                                                "frase": "", "frasi": numero})
            voce["classi"][tag] += 1
            if not voce["frase"] and frase:
                voce["frase"] = frase[:MAX_FRASE]
    return raccolte


def scrivi(raccolte: dict, versione: str, nome_file: str) -> int:
    if not raccolte:
        print("nessuna forma del glossario e' stata trovata nel corpus: "
              "non si scrive un file vuoto, perche' un file vuoto sembra "
              "una raccolta fatta.")
        return 1
    with io.open(USCITA, "w", encoding="utf-8", newline="\n") as f:
        for chiave in sorted(raccolte):
            voce = raccolte[chiave]
            classi = [{"tag": tag, "conteggio": n}
                      for tag, n in voce["classi"].most_common()]
            f.write(json.dumps({
                "forma": chiave,
                "classi": classi,
                "frase": voce["frase"],
                "frase_troncata": len(voce["frase"]) >= 140,
                "fonte": ("Universal Dependencies, corpus annotato italiano, "
                          "release %s, file %s, frase %d"
                          % (versione, nome_file, voce["frasi"])),
                "licenza": LICENZA,
                "attendibilita": ATTENDIBILITA,
            }, ensure_ascii=False) + "\n")
    print("scritte %d analisi in %s" % (len(raccolte), os.path.relpath(USCITA, RADICE)))
    print()
    print("Il file di partenza non entra nel repository e non e' copiato da "
          "nessuna parte: qui finisce solo l'analisi delle parole che il "
          "glossario chiede, con la frase che le contiene come prova.")
    print("Le forme che il corpus non ha restano ignote: %s"
          % os.path.relpath(os.path.join("dati", "italiano.jsonl"), RADICE))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", required=True,
                    help="il file .conllu del corpus annotato, scaricato a mano")
    ap.add_argument("--versione", default="dichiarata-dal-file",
                    help="la release del treebank, che finisce in ogni riga")
    args = ap.parse_args()
    if not os.path.exists(args.file):
        print("non c'e' %s." % args.file)
        print("Il treebank si scarica a mano e non e' una cosa che questo "
              "programma faccia da solo: il progetto scarica solo da una fonte "
              "alla volta, e questa raccolta la dichiara.")
        return 1
    richieste = parole_richieste()
    print("parole italiane richieste dal glossario %d" % len(richieste))
    raccolte = leggi(args.file, richieste)
    return scrivi(raccolte, args.versione, os.path.basename(args.file))


if __name__ == "__main__":
    raise SystemExit(main())