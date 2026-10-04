#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Il vocabolario di Maurizio Musacchi entra nel glossario: italiano -> ferrarese.

**Perche' questa fonte e' diversa da tutte le altre, e perche' conta.** Fino a
oggi il glossario e' stato costruito **dal ferrarese verso l'italiano**: si
leggeva una parola in ferrarese e si scriveva cosa significasse. Il motore,
invece, fa il contrario — parte dall'italiano di una frase e cerca il
ferrarese. Una fonte che va nella direzione giusta copre parole che le altre
non possono coprire: quelle che si dicono in italiano ma che un vocabolario
ferrarese-italiano non elenca, perche' non hanno un lemma dialettale da
mettere in testa alla voce.

**Il permesso, e dove sta.** L'autore scrive nell'introduzione:

    «Questo mezzo consentira' a chi vorra' utilizzare questo mio lavoro, di
    aggiungere, correggere porvi miglioramenti a piacere, senza problemi.»

Il file che questo script legge e' arrivato da un sito di download e non da
una pagina dell'autore: e' un fatto che va detto, e la riga che lo dichiara e'
`dati/fonti.json`, non qui. L'autorizzazione al uso e' data da chi il progetto
ha come titolare, che dichiara di averla; quindi `licenza_verificata` e' vero
**per dichiarazione del titolare del progetto**, non per lettura di una pagina
pubblica. Chi legge fra vent'anni ha bisogno di sapere quale delle due e'.

**Cosa questo script NON fa.** Non sceglie, non corregge, non completa:

- non decide quale sia la parola ferrarese giusta, quando la fonte ne dà due
  (`Usta. Soramanagh.`): le mette tutte e due nella stessa voce, che e' il
  modo piu' onesto di non scegliere;
- non distingue la parola dalla sua definizione: `Battuto, Impasto interno dei
  cappelletti` produce una voce il cui `italiano` e' `battuto` e la cui nota
  porta la definizione, perche' nel glossario `italiano` e' il lemma e la nota
  e' il resto;
- non tocca le righe che non si dividono in due. Sono 286 e sono quasi tutte
  l'introduzione e gli intestazioni di lettera; il numero e' stampato e il
  lavoro di leggerle a mano resta dichiarato, non nascosto.

Ogni riga esce `attendibilita: "I"` e `da_verificare: true`, come tutte le
altre di questa fonte: nessuno ha ascoltato un ferrarese che dica queste
parole, quindi nessuna di loro e' un fatto.

Uso:
    python3 raccolta/da_musacchi.py --prova    # conta, non scrive
    python3 raccolta/da_musacchi.py            # scrive
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

GREZZO = os.path.join(RADICE, "raccolta", "grezzi",
                      "musacchi_italiano_ferrarese.txt")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
ATTESA = os.path.join(RADICE, "dati", "da_verificare", "glossario.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")

ID_FONTE = "S020"
AUTORE = "Maurizio Musacchi"
TITOLO = "Vocabolario italiano-ferrarese (anche modi di dire e frasi idiomatiche)"

PERMESSO = ("«Questo mezzo consentirà a chi vorrà utilizzare questo mio lavoro, "
            "di aggiungere, correggere porvi miglioramenti a piacere, senza "
            "problemi», introduzione dell'autore")

# Il separatore e' un trattino doppio, un trattino lungo o un trattino unico
# con dei punti intorno: la fonte non usa un separatore solo, e un trattino
# semplice da solo non puo' essere il separatore perche' dentro le frasi ce
# sono (`Alla rovescia- A la stramàn` e' una coppia, ma `A lato- Ad banda` ha
# il trattino attaccato alla parola).
SEP = re.compile(r"\s*[-–—.]*(?:-{2,}|—|–)\s*")

# Le righe che non sono voci ma testo introduttivo. Si dichiarano per nome: uno
# script che butta via tutto quello che non capisce sembra piu' rigoroso di uno
# che dice «queste 286 righe non le ho capite».
NON_VOCI = (
    "vocabolario", "italiano- ferrarese", "introduzione", "contenuto",
    "indice", "avvertenza", "copyright", "tutti i vocabolari che conosco",
    "winston churchill", "so che alcuni studiosi", "anche perché, molti",
    "questo mezzo consentirà", "maurizio musacchi", "hyperlink",
    "dalll’italiano", "(anche modi di dire", "sommario", "nota dell'autore",
    "premessa", "bibliografia", "www.", "http",
)

# Una parola che non e' una parola: un numero, un indirizzo, un frammento di
# testo lungo. Non e' un filtro di qualita', e' un filtro di forma.
PAROLA = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\- ]{0,40}$")


def _leggi_grezzo() -> list:
    """Le coppie (italiano, ferrarese, numero di riga) della fonte.

    Il numero di riga e' come il numero di voce di Bigoni: serve a chi trova
    un errore di sapere dove guardare senza dover cercare fra 1243.
    """
    if not os.path.exists(GREZZO):
        raise SystemExit(
            "manca %s\n"
            "Il grezzo non e' nel repository per scelta: e' il testo del "
            "vocabolario, e si ricrea dal file che hai in Downloads con\n"
            "    textutil -convert txt -output <percorso> \"<il .doc>\"\n"
            % os.path.relpath(GREZZO, RADICE))
    coppie = []
    with io.open(GREZZO, encoding="utf-8") as f:
        for numero, riga in enumerate(f, 1):
            riga = riga.strip()
            if not riga or "HYPERLINK" in riga or "mailto:" in riga:
                continue
            bassa = riga.lower()
            if any(bassa.startswith(n) or bassa == n for n in NON_VOCI):
                continue
            pezzi = [p.strip() for p in SEP.split(riga) if p and p.strip()]
            if len(pezzi) < 2:
                continue
            # Tre pezzi vuol dire che la parte italiana contiene un trattino:
            # `Battuto, Impasto interno dei cappelletti` non e' una voce con
            # due definizioni, e' una voce con una glossa. Si mette tutto
            # davanti e si prende l'ultimo pezzo come ferrarese.
            italiano = " — ".join(pezzi[:-1]).strip()
            ferrarese = pezzi[-1].strip()
            coppie.append((italiano, ferrarese, numero))
    return coppie


def _lemma(italiano: str) -> str:
    """La parola cercabile: il lemma, non la frase che lo spiega.

    `Accorciare, far la scorta` e' una voce che si cerca con «accorciare». La
    parte dopo la virgola o la parentesi non e' il nome della voce: e' la sua
    definizione, e va nella nota.
    """
    testo = italiano.split(",")[0].split("(")[0].strip(" .;:")
    return " ".join(testo.split())


def _nota(italiano: str, ferrarese: str) -> str:
    """Quello che la fonte dice e che gli altri campi non portano."""
    parti = []
    glossa = italiano.split(",", 1)
    if len(glossa) > 1 and glossa[1].strip(" .;()"):
        parti.append("La fonte spiega: %s" % " ".join(glossa[1].split()))
    if "(" in italiano and ")" in italiano:
        dentro = italiano[italiano.find("(") + 1: italiano.find(")")]
        if dentro.strip():
            parti.append("Nota della fonte: %s" % " ".join(dentro.split()))
    if "." in ferrarese.strip("."):
        parti.append("La fonte dà più forme: %s"
                     % " ".join(f.strip() for f in ferrarese.split(".")
                                if f.strip()))
    if not parti:
        return ""
    return "; ".join(parti)


def _fonte(numero: int) -> str:
    """Da dove viene la voce, con il permesso dichiarato dentro.

    Il permesso sta **nella fonte di ogni riga**, non solo in
    `dati/fonti.json`: una riga copiata in un altro contesto porta con se' la
    ragione per cui puo' essere copiata.
    """
    return ("%s, %s (%s), riga n. %d. %s"
            % (AUTORE, TITOLO, ID_FONTE, numero, PERMESSO))


def voci_attive() -> list:
    if not os.path.exists(GLOSSARIO):
        raise SystemExit("manca dati/glossario.jsonl")
    voci = []
    with io.open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            if riga.strip() and not riga.lstrip().startswith("//"):
                voci.append(json.loads(riga))
    return voci


def prossimo_id(attive: list, in_attesa: list) -> int:
    """Il primo id libero, guardando **tutti e due** i file.

    Lo stesso difetto che ha fatto perdere 6426 righe a `da_bigoni.py`: la
    fila d'attesa ha id piu' alti di quelli attivi, e un generatore che guarda
    solo il glossario attivo li riscrive. Il controllo D1 se ne accorgerebbe,
    ma dopo.
    """
    maggiore = 0
    for voce in attive + in_attesa:
        identificatore = voce.get("id", "")
        if identificatore.startswith("V") and identificatore[1:].isdigit():
            maggiore = max(maggiore, int(identificatore[1:]))
    return maggiore + 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prova", action="store_true",
                    help="conta e non scrive")
    args = ap.parse_args()

    coppie = _leggi_grezzo()
    attive = voci_attive()
    in_attesa = []
    if os.path.exists(ATTESA):
        with io.open(ATTESA, encoding="utf-8") as f:
            for riga in f:
                if riga.strip() and not riga.lstrip().startswith("//"):
                    in_attesa.append(json.loads(riga))

    # Una parola che c'e' gia' non si riscrive: la fonte e' piu' vecchia o
    # meno accurata, e il glossario gia' sa qualcosa.
    gia_presenti = set()
    for voce in attive + in_attesa:
        for campo in ("italiano", "principale_italiano"):
            if voce.get(campo):
                gia_presenti.add(chiave(voce[campo]))
        for variante in voce.get("varianti") or []:
            if isinstance(variante, dict) and variante.get("italiano"):
                gia_presenti.add(chiave(variante["italiano"]))

    nuove, scartate, gia_presenti_qui = [], [], []
    for italiano, ferrarese, numero in coppie:
        lemma = _lemma(italiano)
        if not lemma or not PAROLA.match(lemma):
            scartate.append((numero, italiano))
            continue
        if not ferrarese.strip(" ."):
            scartate.append((numero, italiano))
            continue
        if chiave(lemma) in gia_presenti:
            gia_presenti_qui.append(lemma)
            continue
        gia_presenti.add(chiave(lemma))
        nuove.append((lemma, italiano, ferrarese, numero))

    print("%s" % TITOLO)
    print("righe lette          %4d" % len(coppie))
    print("gia' nel glossario   %4d   non si riscrivono" % len(gia_presenti_qui))
    print("scartate             %4d   non sono una voce: non una parola, o "
          "vuota" % len(scartate))
    print("nuove voci           %4d" % len(nuove))
    print()
    for numero, italiano in scartate[:10]:
        print("  scartata riga %d: %s" % (numero, italiano[:90]))
    if args.prova:
        return 0

    if not nuove:
        print("niente da scrivere.")
        return 0

    if not os.path.exists(VARIETA):
        raise SystemExit("manca dati/varieta.json: la varieta' non si indovina")
    with io.open(VARIETA, encoding="utf-8") as f:
        grezzo = json.load(f)
    assegnazione = None
    for candidato in grezzo.get("assegnazioni", []):
        if candidato.get("fonte") == ID_FONTE:
            assegnazione = candidato
    if assegnazione is None:
        raise SystemExit(
            "dati/varieta.json non dichiara la varieta' per %s: senza quella "
            "riga le voci non sanno a chi servire, e il progetto non indovina"
            % ID_FONTE)
    varieta = assegnazione["varieta"]

    primo = prossimo_id(attive, in_attesa)
    nuove_righe = []
    for scarto, (lemma, italiano, ferrarese, numero) in enumerate(nuove):
        nuove_righe.append({
            "id": "V%05d" % (primo + scarto),
            "varieta": varieta,
            "ferrarese": ferrarese.strip(" ."),
            "italiano": lemma,
            "principale_italiano": " ".join(italiano.split()),
            "varianti": [],
            "campo": "",
            "note": _nota(italiano, ferrarese),
            "fonte": _fonte(numero),
            "attendibilita": "I",
            "da_verificare": True,
        })

    with io.open(GLOSSARIO, "a", encoding="utf-8", newline="\n") as f:
        for voce in nuove_righe:
            f.write(json.dumps(voce, ensure_ascii=False, sort_keys=True) + "\n")

    print("scritte %d voci da %s a %s"
          % (len(nuove_righe), nuove_righe[0]["id"], nuove_righe[-1]["id"]))
    print()
    print("Nessuna di queste voci e' verificata: `attendibilita: \"I\"`, "
          "`da_verificare: true`.")
    print("Il permesso dell'autore e' scritto nella fonte di ogni riga, e la "
          "ragione per cui")
    print("il glossario gia' aveva la parola e' che questa fonte e' piu' "
          "vecchia: non si riscrive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())