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

**Cosa c'e' dentro la pagina: tre righe per ogni modo di dire.**

    <ul><li><b>La gh'à ill gàmb a ciupéta.</b></li></ul>     il ferrarese
    <dl><dd><i>Ha le gambe a coppietta.</i>                  la traduzione letterale
            <dl><dd>Ha le gambe a x.</dd></dl></dd></dl>     il significato

Il **ferrarese** e' il grassetto dell'elenco che sta subito prima della
definizione; il **corsivo** e' l'italiano parola per parola; il `<dl>` annidato
(il `Template:Spiegazione` di Wikiquote) e' il significato. Una coppia del corpus
e' una traduzione, quindi `italiano` e' il corsivo e il significato va nel campo
`significato`.

**Il difetto che questo lettore corregge (0.36).** Fino alla 0.35 il lettore
prendeva il **corsivo** come se fosse il ferrarese e il significato come se fosse
l'italiano: tutte e 31 le coppie di S019 avevano l'italiano su tutti e due i lati
(`ferrarese: "Ha le gambe a coppietta"`), e il traduttore ne ricavava frammenti
come `ha → ha`. Nessun controllo se ne accorgeva, perche' i controlli guardavano
che i campi ci fossero, non che il ferrarese fosse ferrarese. Le due «spiegazioni
mozzate» che il lettore scartava («, andare a zonzo», «o Dai, picchia e
martella») erano lo stesso errore visto da un'altra parte: erano la seconda
traduzione letterale, letta come significato.

**Il conto, dalla struttura del documento.** Le definizioni esterne sono 37 (il
lettore conta la **profondita'** dei `<dd>`, perche' quelli annidati sono
significati, non voci). Due non hanno la traduzione letterale («Gnêc gnêc»,
«Ziràr la martufàia»: la pagina da' solo il significato) e non entrano, perche' un
significato non e' una traduzione. Una definizione porta **due** modi di dire
(«Picia e dài» o «Dài, picia e martèla») con le due traduzioni nello stesso
ordine, e da' due coppie. Le coppie sono quindi **36**. Una definizione con un
modo di dire e due corsivi («Andar a vaiun») tiene il primo e dichiara il
secondo nella nota.

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
    # Un tag dentro una frase («un <b>martùf</b>, ossia») lascia uno spazio
    # davanti alla virgola: si toglie, perche' non e' nel testo della pagina.
    return re.sub(r"\s+([,.;:!?])", r"\1", " ".join(testo.split()))


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


def _grassetti(blocco: str) -> list:
    """I testi in grassetto di un elenco, senza i rinvii alle note."""
    blocco = re.sub(r"<sup\b.*?</sup>", " ", blocco, flags=re.S)
    return [_pulito(b).strip(" .") for b in
            re.findall(r"<b\b[^>]*>(.*?)</b>", blocco, re.S)]


def _elenco_prima(testo: str, fine: int) -> str:
    """L'elenco `<ul>` che finisce **subito** prima di `fine`, o ''.

    «Subito» vuol dire che fra la chiusura dell'elenco e la definizione c'e'
    solo spazio: un elenco piu' lontano (l'indice, i collegamenti in fondo alla
    pagina) non e' il modo di dire di questa definizione, e prenderlo darebbe a
    una traduzione il ferrarese di un'altra.
    """
    prima = testo[:fine]
    chiusura = prima.rfind("</ul>")
    if chiusura < 0 or prima[chiusura + len("</ul>"):].strip():
        return ""
    apertura = prima.rfind("<ul", 0, chiusura)
    return prima[apertura:chiusura] if apertura >= 0 else ""


def _definizioni(segmento: str) -> list:
    """I `<dl>` esterni, con la posizione in cui cominciano."""
    trovate, profondita, inizio = [], 0, None
    for m in re.finditer(r"<(/?)dl\b[^>]*>", segmento):
        if m.group(1):
            profondita -= 1
            if profondita == 0 and inizio is not None:
                trovate.append((inizio, segmento[inizio:m.end()]))
                inizio = None
        else:
            if profondita == 0:
                inizio = m.start()
            profondita += 1
    return trovate


def voci() -> list:
    """I modi di dire della pagina salvata, nell'ordine della pagina.

    Ogni voce e' un dizionario con `ferrarese`, `letterale`, `significato` e
    `altre` (i corsivi in piu', quando la pagina ne da' piu' di uno per un modo
    di dire solo). Una definizione con due modi di dire e due corsivi da' due
    voci, accoppiate nell'ordine della pagina.
    """
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
    return voci_da(testo[i:])


def voci_da(segmento: str) -> list:
    """Le voci di un pezzo di pagina: `voci()` senza il file, per le prove."""
    trovate = []
    for inizio, definizione in _definizioni(segmento):
        ferraresi = [f for f in _grassetti(_elenco_prima(segmento, inizio)) if f]
        if not ferraresi:
            # Una definizione senza il suo modo di dire in grassetto non e' una
            # voce: e' un'altra parte della pagina.
            continue
        esterni = _esterni(definizione)
        dentro = esterni[0] if esterni else ""
        annidato = dentro.find("<dl")
        testa = dentro if annidato < 0 else dentro[:annidato]
        letterali = [_pulito(c).strip(" .") for c in
                     re.findall(r"<i\b[^>]*>(.*?)</i>", testa, re.S)]
        letterali = [c for c in letterali if c]
        significato = ("" if annidato < 0 else
                       _pulito(dentro[annidato:]).strip(" ."))
        if len(ferraresi) == len(letterali):
            accoppiate = [(f, l, []) for f, l in zip(ferraresi, letterali)]
        elif len(ferraresi) == 1:
            accoppiate = [(ferraresi[0], letterali[0] if letterali else "",
                           letterali[1:])]
        else:
            # Piu' modi di dire e un numero diverso di corsivi: accoppiarli
            # sarebbe scegliere, e il lettore non sceglie.
            accoppiate = [(f, "", []) for f in ferraresi]
        for ferrarese, letterale, altre in accoppiate:
            trovate.append({"ferrarese": ferrarese, "letterale": letterale,
                            "significato": significato, "altre": altre})
    return trovate


def classifica(trovate: list, gia: set) -> dict:
    """Divide le voci della pagina in tre mucchi, e dice perche'.

    La funzione non scrive niente: decide, e lascia che `main()` scriva. Serve
    perche' una decisione che si puo' provare e' una decisione che si puo'
    correggere, e i mucchi sono tutti visibili: quello che entra, quello che
    c'e' gia' e quello che la pagina non traduce.
    """
    nuovo, duplicate, senza = [], [], []
    for voce in trovate:
        if not voce["letterale"]:
            # La pagina da' il significato e non la traduzione: un significato
            # non e' una traduzione, e una coppia del corpus si', quindi la voce
            # non entra. Si stampa, perche' chi decide la deve poter vedere.
            senza.append(voce)
            continue
        if chiave(voce["ferrarese"]) in gia:
            duplicate.append(voce)
            continue
        gia.add(chiave(voce["ferrarese"]))
        nuovo.append(voce)
    return {"nuovo": nuovo, "gia": duplicate, "senza": senza}


NOTA = ("La traduzione italiana e' quella letterale che la pagina mette "
        "accanto al modo di dire; il significato, quando la pagina lo da', e' "
        "nel campo `significato`. Non e' stata verificata da un parlante.")


def riga_coppia(voce: dict, identificatore: str, varieta: str) -> dict:
    """La riga di `dati/coppie.jsonl` per una voce della pagina."""
    nota = NOTA
    if voce["altre"]:
        nota += (" La pagina da' anche un'altra traduzione: %s."
                 % "; ".join("«%s»" % a for a in voce["altre"]))
    scritta = {
        "id": identificatore,
        "varieta": varieta,
        "italiano": voce["letterale"],
        "ferrarese": voce["ferrarese"],
        "tipo": TIPO,
        "fonte": "%s (%s)" % (SITO, ID_FONTE),
        "nota": nota,
        "attendibilita": "I",
        "ricorrenze": 1,
    }
    if voce["significato"]:
        scritta["significato"] = voce["significato"]
    return scritta


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

    print("modi di dire nella pagina   %4d" % len(trovate))
    print("gia' nelle coppie           %4d" % len(duplicate))
    print("senza traduzione letterale  %4d   la pagina da' solo il "
          "significato" % len(senza))
    print("da scrivere                 %4d" % len(nuovo))
    print()
    for voce in senza:
        print("  scartata %-38s %r" % (voce["ferrarese"][:38],
                                       voce["significato"][:40]))
    for voce in nuovo:
        print("  %-44s %s" % (voce["ferrarese"][:44], voce["letterale"][:60]))
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

    righe = [riga_coppia(voce, "F%04d" % (maggiore + 1 + scarto), varieta)
             for scarto, voce in enumerate(nuovo)]

    with io.open(COPPIE, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")

    print("scritte %d coppie da %s a %s"
          % (len(righe), righe[0]["id"], righe[-1]["id"]))
    print()
    print("Nessuna di queste frasi e' verificata: `attendibilita: \"I\"`.")
    print("La pagina e' collaborativa e le traduzioni sono interpretazioni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())