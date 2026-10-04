#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esegue in locale i passi di `.github/workflows/*.yml`.

Non e' un sostituto del workflow: e' il modo di non scoprire alla fine che una
riga di un passo e' rotta solo su GitHub. Ogni passo viene eseguito con la
shell e il codice di uscita che avrebbe li', e il primo che fallisce ferma
tutto e dice quale.
"""
import glob
import io
import os
import shutil
import subprocess
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLUSSI = os.path.join(RADICE, ".github", "workflows")


def pulisci_cache() -> int:
    """Butta via i bytecode gia' compilati. Ritorna quanti ne ha trovati.

    La cache di Python accetta un file quando **dimensione e data al secondo**
    coincidono, quindi una correzione che cambia un carattere per uno la
    convince che il bytecode sia ancora valido. Il sintomo e' un traceback che
    mostra il sorgente nuovo e un errore che parla del vecchio. Non e' un
    difetto che si puo' correggere altrove: si previene cancellando.
    """
    trovate = 0
    for cartella in glob.glob(os.path.join(RADICE, "**", "__pycache__"),
                              recursive=True):
        shutil.rmtree(cartella, ignore_errors=True)
        trovate += 1
    return trovate


def passi(testo: str):
    """I blocchi `run:` del file, uno alla volta."""
    dentro = False
    blocco = []
    for riga in testo.split("\n"):
        if riga.strip() == "run: |":
            dentro = True
            blocco = []
            continue
        if dentro:
            if riga.startswith("          ") or not riga.strip():
                blocco.append(riga[10:])
                continue
            dentro = False
            if blocco:
                yield "\n".join(blocco)


def main() -> int:
    cache = pulisci_cache()
    if cache:
        print("cache dei bytecode buttate: %d cartelle" % cache)
    # Ogni workflow, in ordine di nome: quello che si rompe per primo e' quello
    # che gira prima, quindi l'ordine dei file e' l'ordine dei fallimenti.
    numero = 0
    for nome in sorted(os.listdir(FLUSSI)):
        if not nome.endswith(".yml"):
            continue
        with io.open(os.path.join(FLUSSI, nome), encoding="utf-8") as f:
            testo = f.read()
        for corpo in passi(testo):
            numero += 1
            print("=" * 72)
            print("%s, passo %d" % (nome, numero))
            print("=" * 72)
            fatto = subprocess.run(["bash", "-c", corpo], cwd=RADICE)
            if fatto.returncode != 0:
                print("FALLITO %s passo %d (codice %d)"
                      % (nome, numero, fatto.returncode))
                return fatto.returncode
    # E lo scanner, che non e' un passo di workflow ma una regola del progetto.
    numero += 1
    print("=" * 72)
    print("scanner.py")
    print("=" * 72)
    fatto = subprocess.run(
        [sys.executable, os.path.join(RADICE, "prove", "scanner.py")],
        cwd=RADICE)
    if fatto.returncode != 0:
        print("FALLITO lo scanner (codice %d)" % fatto.returncode)
        return fatto.returncode
    print("=" * 72)
    print("%d passi, tutti usciti con zero" % numero)
    return 0


if __name__ == "__main__":
    sys.exit(main())