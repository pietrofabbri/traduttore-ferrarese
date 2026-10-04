#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""I modi di dire di Wikiquote entrano nelle coppie: S019.

**Perche' qui e non nel glossario.** I modi di dire della pagina sono
frasi — «andare a zonzo», «buttare le carte in tavola» — e non parole. Il
glossario e' fatto di voci che il gioco fa **ripetere**, e ripetere una frase
intera non e' un esercizio di pronuncia: e' un esercizio di memoria. Quindi
queste righe vanno in `dati/coppie.jsonl`, che e' il corpus delle frasi, e non
in `dati/glossario.jsonl`, che e' quello delle parole. E' una distinzione che il
progetto ha gia' e che qui viene esercitata per la prima volta su una fonte
interamente nuova.

**Il perche' di Wikiquote, che e' la fonte piu' semplice che esista per il
progetto.** La pagina e' CC BY-SA 4.0 dichiarata dalla pagina stessa, quindi non
e' una licenza dedotta da un sito di terzi; l'indirizzo e' dichiarato in
`dati/fonti.json` come S019; e il testo si rilegge con un comando e senza rete,
perche' il grezzo e' in `raccolta/grezzi/wikt/`.

**Cosa c'e' dentro la pagina, e perche' la pagina e' difficile da leggere.**
Ogni modo di dire e' un `<dd>` che contiene due cose: la **parola ferrarese**,
in corsivo, e la **spiegazione italiana**, che arriva da un modello di Wikiquote
(`Template:Spiegazione`) ed e' quindi dentro un `<dl>` annidato. Contare i `<dd>`
senza distinguere quelli esterni da quelli annidati dà un numero falso — 37,
che include le spiegazioni — quindi il lettore conta la **profondita'** e prende
solo i 35 esterni. E un numero che viene dalla struttura del documento, non da una
regex che arriva a una conclusione fortunata.

Quattro delle 35 non entrano, e il motivo va detto perche' e' un motivo che si
riconosce: due non hanno spiegazione (la pagina rimanda e basta) e due hanno la
spiegazione tagliata — «, andare a zonzo», «o Dai, picchia e martella» — cioe'
la coda di una frase, non una frase. Una coppia con l'italiano mozzato
insegnerebbe a tradurre il nulla. La regola che le riconosce guarda il **segno**
iniziale e non la prima parola: una regola che guardava la parola scartava
anche «Come viene viene, alla grossa» e «Furbo come l'oca di Fergnani», che sono
frasi intere. Il numero degli scarti e' stampato ogni volta, cosi' chi decide puo'
vederli.

**Il tipo e' `narrativa`, non `attestato`.** `attestato` vuol dire «voce di
dizionario con frase d'esempio»; un modo di dire e' un proverbio sciolto, e il
corpus mette quelli sotto `narrativa`. Il tipo decide a chi la frase viene
offerta, quindi la scelta non e' cosmetica e viene dichiarata.

**Ogni riga esce `attendibilita: "I"`.** Una pagina
collaborativa non e' una fonte documentata: nessuno ha ascoltato un ferrarese
che dica queste frasi. Sono interpretazioni, e il progetto le chiama cosi'.

Uso:
    python3 raccolta/da_modi.py --prova    # mostra, non scrive
    python3 raccolta/da_modi.py            # scrive in dati/coppie.jsonl
"""
from __future__ import annotations

import argparse
import html
import io
import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.corpora import TIPI  # noqa: E402
from traduttore.normalizza import chiave  # noqa: E402

GREZZO = os.path.join(RADICE, "raccolta", "grezzi", "wikt",
                      "modi_di_dire_ferraresi.html")
COPPIE = os.path.join(RADICE, "dati", "coppie.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")

ID_FONTE = "S019"
SITO = "https://it.wikiquote.org/wiki/Modi_di_dire_ferraresi"
# `narrativa`, non `attestato`: `attestato` vuol dire «voce di dizionario con
# frase d'esempio» e queste non lo sono — sono modi di dire, cioe' proverbi
# sciolti, che il corpus mette sotto `narrativa` accanto ai proverbi. La scelta
# e' dichiarata qui perche' il tipo decide a chi la frase viene offerta.
TIPO = "narrativa"


def _pulito(testo: str) -> str:
    """Il testo di un frammento HTML, senza spazi doppi ne' citazioni."""
    testo = re.sub(r"<sup[^>]*>.*?</sup>", " ", testo, flags=re.S)
    testo = re.sub(r"<[^>]+>", " ", testo)
    testo = html.unescape(testo)
    testo = testo.replace("’", "'")
    return " ".join(testo.split())


def _esterni(segmento: str) -> list:
    """I `<dd>` **esterni**, e non quelli annidati dentro un altro `<dd>`.

    Il motivo per cui serve: la pagina mette la spiegazione italiana dentro un
    `<dl>` dentro il `<dd>` della voce, quindi contando i `<dd>` si contano
    anche le spiegazioni. Si conta la profondita': un `<dd>` che si apre dentro
    un altro `<dd>` appartiene a quell'altro e non e' una voce.
    """
    # Un `<dd>` esterno e' quello che non e' dentro un altro: si tiene la
    # profondita' e si prende solo il testo che si chiude a profondita' zero.
    esterni, profondita, inizio = [], 0, None
    for m in re.finditer(r"<(/?)dd\b[^>]*>", segmento):
        if m.group(1):
            profondita -= 1
            if profondita == 0 and inizio is not None:
                esterni.append(segmento[inizio:m.start()])
                inizio = None
        else:
            if profondita == 0:
                inizio = m.end()
            profondita += 1
    return esterni


def voci() -> list:
    """(ferrarese, spiegazione) dalla pagina salvata, nell'ordine in cui
    vengono: l'ordine e' quello della pagina, che raggruppa per lettera."""
    if not os.path.exists(GREZZO):
        raise SystemExit(
            "manca %s\nIl grezzo e' la pagina salvata; si rilava con:\n"
            "    curl -sL -A 'Mozilla/5.0' \\\n"
            "      -o raccolta/grezzi/wikt/modi_di_dire_ferraresi.html \\\n"
            "      '%s'\n" % (os.path.relpath(GREZZO, RADICE), SITO))
    with io.open(GREZZO, encoding="utf-8") as f:
        testo = f.read()
    i = testo.find('mw-content-text')
    if i < 0:
        raise SystemExit("la pagina salvata non ha il contenuto: e' cambiata "
                         "la struttura, e va riletta a mano")
    segmento = testo[i:]
    trovate = []
    for blocco in _esterni(segmento):
        corsivo = re.search(r"<i\b[^>]*>(.*?)</i>", blocco, re.S)
        if not corsivo:
            continue
        ferrarese = _pulito(corsivo.group(1)).strip(" .")
        resto = blocco[corsivo.end():]
        spiegazione = _pulito(resto).strip(" .")
        if not ferrarese:
            continue
        trovate.append((ferrarese, spiegazione))
    return trovate


# Una spiegazione mozzata e' riconoscibile dal **segno** con cui comincia, non
# dalla parola: «, andare a zonzo» e' la coda di una frase, e lo si vede dalla
# virgola; «Come viene viene, alla grossa» comincia pure con una congiunzione ma
# e' una frase intera. La prima regola che avevo provato guardava la parola e
# buttava via quattro voci buone per due scarti giusti: qui la prova e' che il
# testo non comincia con una lettera, oppure che una congiunzione stretta e
# minuscola e' incollata a una maiuscola seguita da virgola («o Dai, picchia»),
# che e' il segno di due frasi unite male.
_MOZZATA = re.compile(r"^[^\w\s]"          # segno di punteggazione
                      r"|^(?:o|e|a|ed|ma|pero')\s+[A-ZÀ-Ü][a-zà-ÿ]+,")


def _mozzata(spiegazione: str) -> bool:
    """True se la spiegazione e' unpezzo, non una frase."""
    return bool(_MOZZATA.match(spiegazione))


def classifica(trovate: list, gia: set) -> dict:
    """Divide le voci della pagina in quattro mucchi, e dice perche'.

    La funzione non scrive niente: decide, e lascia che `main()` scriva. Serve
    perche' una decisione che si puo' provare e' una decisione che si puo'
    correggere, e i quattro mucchi sono tutti e quattro visibili: quello che
    entra, quello che c'e' gia', quello che la pagina non spiega e quello che
    la pagina spiega a meta'.
    """
    nuovo, duplicate, senza, mozzate = [], [], [], []
    for ferrarese, spiegazione in trovate:
        if not spiegazione:
            # La pagina rimanda e basta: non c'e' niente da imparare da una voce
            # senza significato, quindi non entra.
            senza.append(ferrarese)
            continue
        if _mozzata(spiegazione):
            # Non e' una spiegazione: e' la coda di una frase che il lettore ha
            # tagliato dove la pagina mette il rinvio. Una coppia con l'italiano
            # mozzato insegnerebbe a tradurre il nulla, quindi lo scarto e' qui e
            # viene stampato perche' chi decide debba poterlo vedere.
            mozzate.append((ferrarese, spiegazione))
            continue
        if chiave(ferrarese) in gia:
            duplicate.append(ferrarese)
            continue
        gia.add(chiave(ferrarese))
        nuovo.append((ferrarese, spiegazione))
    return {"nuovo": nuovo, "gia": duplicate, "senza": senza,
            "mozzate": mozzate}


def coppie_esistenti() -> list:
    """Le coppie gia' scritte, e zero se il file non c'e' ancora.

    Il file esiste sempre nel progetto — e' tracciato da git — quindi questa
    riga non serve al lavoro di tutti i giorni. Serve a chi ci mette dentro un
    file nuovo, che e' un caso reale: il primo giro su un corpus vuoto non puo'
    fallire perche' il file che deve leggere non e' stato creato. Un
    `FileNotFoundError` su un file che non esiste non e' un difetto del
    generatore, e' un crash.
    """
    coppie = []
    if not os.path.exists(COPPIE):
        return coppie
    with io.open(COPPIE, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.lstrip().startswith("//"):
                coppie.append(json.loads(riga))
    return coppie


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args()

    trovate = voci()
    esistenti = coppie_esistenti()
    gia = set()
    for coppia in esistenti:
        gia.add(chiave(coppia.get("ferrarese") or ""))
        gia.add(chiave(coppia.get("italiano") or ""))

    mucchi = classifica(trovate, gia)
    nuovo = mucchi["nuovo"]
    duplicate = mucchi["gia"]
    senza = mucchi["senza"]
    mozzate = mucchi["mozzate"]

    print("modi di dire nella pagina   %4d" % len(trovate))
    print("gia' nelle coppie           %4d" % len(duplicate))
    print("senza spiegazione           %4d   la pagina non dice cosa "
          "vogliono dire" % len(senza))
    print("spiegazione mozzata         %4d   coda di frase, non "
          "significato" % len(mozzate))
    print("da scrivere                 %4d" % len(nuovo))
    print()
    for ferrarese, spiegazione in mozzate:
        print("  scartata %-38s %r" % (ferrarese[:38], spiegazione[:40]))
    for ferrarese, spiegazione in nuovo:
        print("  %-44s %s" % (ferrarese[:44], spiegazione[:60]))
    if args.prova:
        return 0

    if not nuovo:
        print("niente da scrivere.")
        return 0

    if TIPO not in TIPI:
        raise SystemExit("il tipo %r non e' fra quelli che il corpus "
                         "accetta: %s" % (TIPO, ", ".join(TIPI)))
    with io.open(VARIETA, encoding="utf-8") as f:
        grezzo = json.load(f)
    assegnazione = None
    for candidato in grezzo.get("assegnazioni", []):
        if candidato.get("fonte") == ID_FONTE:
            assegnazione = candidato
    if assegnazione is None:
        raise SystemExit(
            "dati/varieta.json non dichiara la varieta' per %s: senza quella "
            "riga le coppie non sanno a chi servire, e il progetto non indovina"
            % ID_FONTE)
    varieta = assegnazione["varieta"]

    maggiore = 0
    for coppia in esistenti:
        identificatore = coppia.get("id", "")
        if identificatore.startswith("F") and identificatore[1:].isdigit():
            maggiore = max(maggiore, int(identificatore[1:]))

    righe = []
    for scarto, (ferrarese, spiegazione) in enumerate(nuovo):
        righe.append({
            "id": "F%04d" % (maggiore + 1 + scarto),
            "varieta": varieta,
            "italiano": spiegazione,
            "ferrarese": ferrarese,
            "tipo": TIPO,
            "fonte": "%s (%s)" % (SITO, ID_FONTE),
            "nota": "La spiegazione e' della pagina: non e' una traduzione "
                    "letterale e non e' stata verificata da un parlante.",
            "attendibilita": "I",
            "ricorrenze": 1,
        })

    with io.open(COPPIE, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")

    print("scritte %d coppie da %s a %s"
          % (len(righe), righe[0]["id"], righe[-1]["id"]))
    print()
    print("Nessuna di queste frasi e' verificata: `attendibilita: \"I\"`.")
    print("La pagina e' collaborativa e le spiegazioni sono interpretazioni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())