#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le mutazioni: i test devono prenderle tutte, non qualcuna.

Un test puo' essere vero, passare, e non guardare niente. Il modo per accorgersene
non e' leggerlo, e' rompere il codice apposta e vedere se qualcuno se ne accorge:
qui si prende `raccolta/da_modi.py`, che decide quali frasi della pagina
entrano in `dati/coppie.jsonl`, e si cambiano una alla volta sei decisioni. Ogni
mutazione deve far fallire almeno un test.

**Perche' un solo file, e non tutto il codice.** Il file scelto e' quello che
scrive: un suo difetto non si vede nei dati, perche' i dati sono gia' scritti
bene, e la difetta si vedrebbe solo alla prossima esecuzione, quando ormai la
riga sbagliata e' dentro `coppie.jsonl` e nessuno la riconosce. Il resto del
codice ha altri controlli che parlano dei suoi numeri.

**Perche' tutta la suite e non una classe sola.** Una prima versione di questo
file girava una sola classe di test e concludeva che due regole non fossero
protette: era il banco a essere parziale, non i test a essere ciechi. Le due
regole erano prese, da un'altra classe. Un controllo che misura meno di quello
che dichiara produce un difetto che sembra un difetto del codice, e questo
programma non accetterebbe un simile scambio.

Il controllo **non indovina**: se un pattern smette di corrispondere, o se una
mutazione sopravvive, esce con 1 e lo dice. E non parte con un file tracciato
gia' modificato, perche' riscrive proprio un file tracciato e un'interruzione
li' perderebbe lavoro: il riscatto e' che `git diff` resta leggibile per
ricostruire. I file non tracciati non lo fermano, perche' questo programma non li
tocca e non puo' perderli.

Costo dichiarato: una suite completa per mutazione. Costa qualche minuto, ed e'
percio' questo controllo sta fra le prove e non in ogni giro dei test.
"""
import glob
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORGENTE = os.path.join(RADICE, "raccolta", "da_modi.py")
SUITE = "prove.test_traduttore"
COPIA = SORGENTE + ".prima_delle_mutazioni"

# Le sei mutazioni: ogni nome dice che decisione e' stata rotta, non che
# riga e' stata toccata. Una decisione senza nome e' un commento.
MUTAZIONI = [
    ("la regola che scarta le spiegazioni mozzate torna a guardare la parola",
     'r"|^(?:o|e|a|ed|ma|pero\')\\s+[A-ZÀ-Ü][a-zà-ÿ]+,"',
     'r"^[\\s,;:.\\-–—]*(?:o|e|a|ed|in|con|per|ma|che|come|dove)\\b"'),
    ("il lettore conta tutti i <dd>, annidati compresi",
     "    esterni, profondita, inizio = [], 0, None",
     '    esterni = re.findall(r"<dd\\b[^>]*>", segmento)\n'
     "    return esterni\n"
     "    esterni, profondita, inizio = [], 0, None"),
    ("il tipo torna ad essere quello di prima",
     'TIPO = "narrativa"',
     'TIPO = "attestato"'),
    ("le spiegazioni mozzate non vengono piu' scartate",
     "        if _mozzata(spiegazione):",
     "        if False:"),
    ("una voce senza spiegazione entra fra le nuove",
     "        if not spiegazione:",
     "        if False:"),
    ("la nota che dichiara da dove viene la spiegazione sparisce",
     '            "nota": "La spiegazione e\' della pagina',
     '            "nota": "" if True else "La spiegazione e\' della pagina'),
    ("le righe della pagina si dichiarano verificate da un parlante",
     '            "attendibilita": "I",',
     '            "attendibilita": "D",'),
    ("la varieta' e' indovinata invece che dichiarata",
     '            "varieta": varieta,',
     '            "varieta": "centrale",'),
]


def _albero_sporco():
    """I file tracciati che non sono come git li tiene.

    Restituisce la stringa, vuota se l'albero e' pulito, e `None` se git non ha
    risposto: in quel caso non si puo' affermare che l'albero sia pulito, e
    questa funzione non ha niente da dire. Il `None` non si confonde con
    «albero pulito» perche' il chiamante lo tratta come un motivo per fermarsi:
    una guardia che, quando non sa, risponde «va tutto bene» non e' una guardia.
    `--untracked-files=no` perche' questo controllo riscrive
    `raccolta/da_modi.py` e nient'altro, quindi un file nuovo non tracciato non
    e' a rischio e non deve impedire la misura.
    """
    esito = subprocess.run(["git", "status", "--porcelain",
                            "--untracked-files=no"],
                          cwd=RADICE, capture_output=True, text=True)
    if esito.returncode != 0:
        return None
    return esito.stdout.strip()


def _via_cache() -> None:
    for cartella in glob.glob(os.path.join(RADICE, "**", "__pycache__"),
                              recursive=True):
        shutil.rmtree(cartella, ignore_errors=True)


def _impronta(percorso: str) -> str:
    with open(percorso, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _nomi_dei_test_rotti(esito) -> list:
    nomi = []
    for riga in (esito.stderr or "").splitlines():
        if riga.startswith(("FAIL:", "ERROR:")):
            nomi.append(riga.split()[1])
    return nomi


def _scrivi(testo: str) -> None:
    with io.open(SORGENTE, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)


def main() -> int:
    if not os.path.exists(SORGENTE):
        print("non c'e' %s: questo controllo non ha niente da dire e non puo' "
              "passare." % SORGENTE)
        return 1
    sporco = _albero_sporco()
    if sporco is None:
        print("git non ha risposto e questo controllo non puo' sapere se "
              "l'albero e' pulito. Su un albero pulito riscrive un file "
              "tracciato: senza questa certezza non parte.")
        return 1
    if sporco:
        print("ci sono file tracciati gia' modificati e non committati:")
        print(sporco)
        print(" questo controllo riscrive un file tracciato: con modificazioni "
              "non committate un'interruzione perderebbe lavoro.")
        return 1

    with io.open(SORGENTE, encoding="utf-8") as f:
        originale = f.read()
    prima = _impronta(SORGENTE)

    non_agganciate, sopravvissute, prese = [], [], []
    try:
        for nome, vecchio, nuovo in MUTAZIONI:
            if originale.count(vecchio) != 1:
                non_agganciate.append(nome)
                print("%-58s NON AGGIANCATO" % nome[:58])
                continue
            _scrivi(originale.replace(vecchio, nuovo))
            _via_cache()
            esito = subprocess.run(
                ["python3", "-m", "unittest", SUITE],
                cwd=RADICE, capture_output=True, text=True,
                env=dict(os.environ, PYTHONPATH="sorgenti"))
            _scrivi(originale)
            _via_cache()
            rotte = _nomi_dei_test_rotti(esito)
            if rotte:
                prese.append(nome)
                print("%-58s PRESO da %s" % (nome[:58], rotte[0]))
            else:
                sopravvissute.append(nome)
                print("%-58s NON PRESO: nessun test se ne e' accorto" %
                      nome[:58])
    finally:
        _scrivi(originale)
        _via_cache()
        if os.path.exists(COPIA):
            os.remove(COPIA)

    if _impronta(SORGENTE) != prima:
        print("\nATTENZIONE: %s non e' stato ripristinato come era. Il file "
              "e' in git: controlla `git diff` prima di fare qualcos'altro."
              % os.path.relpath(SORGENTE, RADICE))
        return 1

    print()
    print("%d mutazioni, %d prese, %d sopravvissute, %d non agganciate"
          % (len(MUTAZIONI), len(prese), len(sopravvissute),
             len(non_agganciate)))
    if sopravvissute:
        print("Una mutazione sopravvissuta vuol dire che la regola e' vera "
              "sulla carta e non guardata dai test.")
        for nome in sopravvissute:
            print("  %s" % nome)
    if non_agganciate:
        print("Un pattern che non aggancia vuol dire che il controllo ha "
              "smesso di guardare il codice: va riagganciato, non rimosso.")
        for nome in non_agganciate:
            print("  %s" % nome)
    if not sopravvissute and not non_agganciate:
        print("Ogni decisione rotta e' stata presa da un test. Il file e' "
              "stato ripristinato.")
    return 1 if (sopravvissute or non_agganciate) else 0


if __name__ == "__main__":
    sys.exit(main())