#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""I verbi pronominali, e la prova che la particella non è una parola.

**Il difetto che questo file viene a togliere.** Scrivendo «lei si siede» il
motore rispondeva `lei`, poi `si → oj`, poi `siede` intatta. Il `si` è la
peggiore delle tre risposte: non è un buco, è una **parola sbagliata**. `oj` è
una cosa che il glossario contiene, e il motore l'ha restituita come se fosse
la traduzione di una particella pronominale. Il progetto ha una regola su
questo — meglio nessuna riga che una riga falsa — e il motore la stava
violando senza accorgersene, perché non sapeva che `si` fosse una particella.

**La prova che in ferrarese la particella si attacca al verbo è nel glossario,
non in una grammatica.** Il Ferri scrive i verbi pronominali con il clitico
scritto dentro la voce: `Accanirsi → Acanirss`, `Affacciarsi → Afazzars`,
`sedersi → saŋtàrs` (V14857). Sono **109** voci, tutte con `si`, e tutte con
il clitico in `-rs` o `-rss`. Nessuna fonte dichiara una regola grammaticale su
questo, e non serve: il dato c'è, è numerabile e porta l'id della voce che lo
scrive.

**Che cosa questo file non è.** Non è il paradigma: qui ci sono solo infiniti,
non terze persone né participi. E non è un coniugatore. Se lo si usa per
rispondere a «siede» bisognerebbe riconoscere la forma, che è esattamente ciò
che le fonti non documentano.

Uso:
    python3 raccolta/da_pronominali.py --prova    # i conti, non scrive
    python3 raccolta/da_pronominali.py            # scrive dati/pronominali.jsonl
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
PRONOMINALI = os.path.join(RADICE, "dati", "pronominali.jsonl")

# Le particelle da esaminare **non sono scritte qui**: sono in
# `dati/tokeni.jsonl`, che è l'unico posto dove si dichiara che cosa è una
# particella e perché. La prima versione di questo file le aveva in una lista
# scritta a mano, tutte e quattro, e il risultato era una regola inventata: `ci`
# diventava una particella e il motore smetteva di rispondere `ghe`, che è una
# voce vera del glossario (V0014). Il progetto ha una regola su questo — meglio
# nessuna riga che una riga falsa — e la si applica anche a se stessi.
from traduttore import tokeni  # noqa: E402  (il percorso è sistemato sopra)


def candidate() -> tuple:
    """Le particelle da esaminare, come le dichiara il file dei token."""
    return tokeni.esaminate()


def dichiarate(conto: dict) -> list:
    """Le candidate che il glossario attesta: nessuna, se non ce n'e' una."""
    return [p for p in candidate() if conto.get(p)]

# Il clitico: la ferrarese scrive la `r` dell'infinito e poi la `s` della
# particella, a volte raddoppiata. `Acanirss`, `Afazzars`, `saŋtàrs`.
CLITICO = re.compile(r"[a-zà-ù]rss?$")

TESTATA = """\
// --- IL SISTEMA, dichiarato perché si possa controllarlo -----------------------------
//
// **Che cosa è questo file.** I verbi **pronominali** che il glossario già contiene:
// la voce italiana finisce con una particella e la ferrarese porta la particella
// **attaccata dentro la parola**, in `-rs` o `-rss`.
//
// **Perché esiste.** Perché il motore non traducesse una particella come se fosse
// una parola. Scrivendo «si siede» rispondeva `oj`, che è una voce vera del
// glossario e la risposta sbagliata: `si` qui non è la particella dell'affermazione
// ma quella del verbo pronominale, e in italiano le due cose si scrivono uguale:
// la prima si scrive `sì`, con l'accento, ed è una voce del glossario separata
// (V8171), e qui le due non si confondono.
//
// **Che cosa è dichiarato e che cosa no.** Solo `si`. Le altre tre particelle
// dell'italiano sono esaminate e **non dichiarate**: il glossario non le porta
// attaccata a nessun verbo, e `ci` è già una parola del glossario (`ghe`,
// V0014). Dichiararle avrebbe tolto al motore una risposta vera per mettergli
// un buco.
//
// **Come sono state trovate.** Dal glossario, non da una grammatica: si prende ogni
// voce la cui parte italiana è una sola parola che finisce con una delle
// particelle elencate e la cui parte ferrarese è una sola parola che finisce con il
// clitico. Ogni riga porta l'id della voce che la scrive, quindi ogni riga si può
// controllare aprendola.
//
// **Che cosa non è.** Non è un paradigma: qui ci sono solo **infiniti**. Nessuna
// terza persona, nessun participio, nessuna coniugazione. E non è un coniugatore:
// rispondere a «siede» richiederebbe riconoscere la forma verbale, e riconoscere la
// forma è proprio ciò che le fonti non documentano. La risposta del motore a un
// verbo pronominale coniugato è quindi un **buco dichiarato**, non una forma.
//
// **Un conto che non c'è.** Quanti di questi verbi hanno anche il lemma semplice
// accanto non si sa e non si dichiara: `sedersi` senza `si` fa `seder`, e per
// arrivare a `sedere` serve la morfologia dell'italiano, che nessuna fonte del
// repository dichiara. Meglio un numero che manca che uno che mente.
//
// Particelle dichiarate: {particelle}.
// Candidate esaminate: {candidate}; scartate perché il glossario non le
// porta attaccata a nessun verbo: {scartate}. Una candidata non attestata è
// una parola che il glossario conosce — `ci` è `ghe`, V0014 — e che qui
// diventerebbe un buco: meglio nessuna regola che una regola inventata.
// Verbi pronominali trovati: {totale} ({per_particella}).
// ---------------------------------------------------------------------------------
"""


def _principale(riga: dict) -> str:
    return (riga.get("principale_italiano") or riga.get("italiano") or "").strip()


def voci() -> list:
    righe = []
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.lstrip().startswith("//"):
                righe.append(json.loads(riga))
    return righe


def trova(righe: list) -> list:
    """(voce, particella) per ogni verbo pronominale col clitico."""
    trovate = []
    for riga in righe:
        italiano = _principale(riga).lower()
        ferrarese = (riga.get("ferrarese") or "").strip()
        if " " in italiano or " " in ferrarese or not italiano or not ferrarese:
            continue
        for particella in candidate():
            if (italiano.endswith(particella) and len(italiano) > len(particella)
                    and CLITICO.search(ferrarese.lower())):
                trovate.append((riga, particella))
                break
    return trovate


def esistente() -> list:
    if not os.path.exists(PRONOMINALI):
        return []
    righe = []
    with io.open(PRONOMINALI, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.lstrip().startswith("//"):
                righe.append(json.loads(riga))
    return righe


def main() -> int:
    ap = argparse.ArgumentParser(description="I verbi pronominali del glossario.")
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args()

    righe = voci()
    trovate = trova(righe)
    conto = collections.Counter(p for _, p in trovate)

    # **Un conto che non faccio, e perché.** Sarebbe naturale chiedersi quanti di
    # questi verbi hanno anche il lemma semplice accanto, e la risposta sembra
    # facile: togliere la particella. Non lo e'. `sedersi` senza `si` fa
    # `seder`, e il lemma semplice e' `sedere` — la differenza e' la vocale
    # finale dell'infinito, e per ricostruirla serve la morfologia
    # dell'italiano, che il progetto non ha e che nessuna fonte del repository
    # dichiara. Quindi il conto non si fa e il numero non si dichiara: un 0
    # qui sarebbe un numero falso, e un numero falso in una dichiarazione e' la
    # cosa piu' cara che questo progetto puo' sbagliare.

    gia = {r["voce_id"] for r in esistente()}
    nuove = [r for r, _ in trovate if r["id"] not in gia]

    print("verbi pronominali col clitico  %4d" % len(trovate))
    print("gia' in dati/                  %4d" % (len(trovate) - len(nuove)))
    print("da scrivere                    %4d" % len(nuove))
    for particella, numero in sorted(conto.items()):
        print("  %-4s %4d" % (particella, numero))
    print("particelle dichiarate           %4d   %s"
          % (len(dichiarate(conto)), ", ".join(dichiarate(conto)) or "-"))
    print("candidate scartate              %4d   %s"
          % (len([p for p in candidate() if p not in conto]),
             "; ".join("%s: nessuna voce la porta attaccata a un verbo" % p
                       for p in candidate() if p not in conto) or "-"))
    print()
    print("Nessuna di queste forme e' coniugata: sono infiniti. Le terze "
          "persone non ci sono.")
    if args.prova:
        return 0
    if not nuove:
        print("niente da scrivere.")
        return 0

    if not os.path.exists(PRONOMINALI):
        with io.open(PRONOMINALI, "w", encoding="utf-8", newline="\n") as f:
            f.write(TESTATA.format(
                candidate=", ".join(candidate()),
                particelle=", ".join(dichiarate(conto)) or "nessuna",
                scartate=", ".join(
                    "%s (nessuna voce la porta attaccata a un verbo)" % p
                    for p in candidate() if not conto.get(p)) or "nessuna",
                totale=len(trovate),
                per_particella=", ".join("%s %d" % (p, n)
                                         for p, n in sorted(conto.items()))))
            f.write("// SISTEMA %s\n"
                    % json.dumps({"particelle": dichiarate(conto),
                                  "candidate": list(candidate()),
                                  "verbi": len(trovate),
                                  "per_particella": dict(conto),
                                  "tempi": ["infinito"]},
                                 ensure_ascii=False))
    with io.open(PRONOMINALI, "a", encoding="utf-8", newline="\n") as f:
        numero = 0
        for voce, particella in trovate:
            if voce["id"] in gia:
                continue
            numero += 1
            riga = {
                "id": "P%04d" % numero,
                "particella": particella,
                "italiano": _principale(voce),
                "ferrarese": voce["ferrarese"].strip(),
                "voce_id": voce["id"],
                "fonte": voce.get("fonte", ""),
                "campo": voce.get("campo", ""),
                "attendibilita": voce.get("attendibilita", "I"),
                "da_verificare": True,
                "tempo": "infinito",
            }
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci" % numero)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
