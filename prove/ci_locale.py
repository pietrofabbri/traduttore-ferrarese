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
    """I comandi `run:` del file, uno alla volta.

    **I due difetti che questo lettore aveva, e la loro natura.** Riconosceva
    solo i blocchi `run: |` e ignorava i passi scritti su una riga sola come
    `run: python3 prove/test_traduttore.py`: il passo piu' importante del
    workflow non girava mai in locale. E un blocco aperto negli ultimi byte del
    file non veniva mai chiuso, perche' la fine del file non e' una riga che ne
    chiude un'altra. In entrambi i casi il conto stampato era semplicemente
    sbagliato, e il file prometteva di eseguire «i passi del workflow, in
    locale»: prometteva una copertura che non aveva. E' la stessa cosa che questo
    repository vieta altrove — un controllo che dichiara piu' di quello che fa.

    Percio' ora la forma del comando non conta: un passo e' un passo. E
    `prove/test_traduttore.py` confronta i due numeri, i passi trovati e le
    righe `run:` del file, cosi' un passo nuovo non puo' sparire in silenzio.
    """
    righe = testo.split("\n")
    i = 0
    while i < len(righe):
        riga = righe[i].strip()
        if riga == "run: |":
            i += 1
            blocco = []
            while i < len(righe) and (not righe[i].strip()
                                      or righe[i].startswith("          ")):
                blocco.append(righe[i][10:])
                i += 1
            if blocco:
                yield "\n".join(blocco)
            continue
        if riga.startswith("run: "):
            yield riga[len("run:"):].strip()
        i += 1


def valida_yaml() -> int:
    """Ogni workflow deve essere YAML valido, prima ancora di eseguirne i passi.

    Difetto vero, del 2026-10-05: il nome di un passo di `verifica.yml`
    conteneva «: », e GitHub scartava il file in zero secondi senza eseguire
    niente. Questo script lo passava, perche' `passi()` legge le righe `run:`
    con un lettore suo e non chiede mai se il file sia YAML. Tre giorni di CI
    rossa, e il sito fermo a una versione vecchia, per due apici mancanti.

    PyYAML non e' una dipendenza del progetto, quindi se manca il controllo lo
    dice e non finge di averlo fatto. Ritorna il numero di file non validi.
    """
    try:
        import yaml
    except ImportError:
        print("PyYAML non c'e': la sintassi dei workflow NON e' controllata "
              "(pip install pyyaml)")
        return 0
    rotti = 0
    for nome in sorted(os.listdir(FLUSSI)):
        if not nome.endswith(".yml"):
            continue
        try:
            with io.open(os.path.join(FLUSSI, nome), encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as errore:
            rotti += 1
            print("FALLITO %s non e' YAML valido: GitHub lo scarterebbe "
                  "senza eseguirlo\n%s" % (nome, errore))
    return rotti


def main() -> int:
    if valida_yaml():
        return 1
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