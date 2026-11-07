#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porta il vocabolario del Nannini (1805, S005) dentro `dati/glossario.jsonl`.

**La fonte.** Francesco Nannini, «Vocabolario portatile ferrarese-italiano»,
Ferrara 1805, scansione di archive.org (`vocabolarioporta00nannuoft`), pubblico
dominio. E' il vocabolario ferrarese piu' antico del progetto, e l'unico che
dichiara per iscritto il suo territorio: «il Dialetto della Citta' di Ferrara».

**La lettura.** Il testo incorporato nel PDF e' un OCR del 2009 inservibile
(«Bluii» per «Bluin»). Il testo si rilegge con tesseract (lingua `ita`) sulla
scansione a 300 dpi, una colonna alla volta: lo fa la prima parte di questo
script (`--ocr`), e scrive `raccolta/grezzi/s005/ocr/pNNN.txt`, che non e'
tracciato perche' si rifa' con un comando. La seconda parte legge quei file e
scrive le voci.

**Che cosa entra.** Una voce del Nannini e' «Lemma , categoria , italiano ,
italiano : per altro senso , altro». Entra il lemma, con l'italiano fino ai due
punti (il primo senso) e il primo reso come `principale_italiano`. Non entrano,
e il conto lo dice:

- i rimandi («Blisgar , v. Sblìsgar»): non sono una traduzione;
- le voci in cui il primo reso contiene il lemma stesso: e' una locuzione
  ferrarese seguita dalla spiegazione, e senza leggere il libro non si sa dove
  finisce l'una e comincia l'altra;
- le voci in cui il lemma o il primo reso non hanno la forma di una parola
  (cifre, segni, lettere sole): e' l'OCR che ha letto male;
- le voci che il glossario ha gia', con la stessa forma e lo stesso primo
  significato: si contano come **concordanze** (due fonti che dicono la stessa
  cosa) e non si duplicano.

Ogni voce e' `I` e `da_verificare`, con la pagina stampata del libro: e' una
lettura automatica, non un confronto con la pagina. E' la stessa condizione
delle diecimila voci del Ferri.

Uso:
    python3 raccolta/da_nannini.py --ocr       # rilegge le scansioni (lento)
    python3 raccolta/da_nannini.py --prova     # dice cosa farebbe
    python3 raccolta/da_nannini.py             # scrive
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traduttore.normalizza import chiave  # noqa: E402
from copertura import FUNZIONALI as _FUNZIONALI  # noqa: E402
from da_bigoni import (id_in_attesa, prossimo_id, varieta_dichiarata,  # noqa: E402
                       voci_attive)

FUNZIONALI_PROGETTO = {chiave(f) for f in _FUNZIONALI} | {
    "il", "lo", "la", "i", "gli", "le", "un", "una", "a", "al", "da", "di",
    "in", "con", "per", "e", "o", "che", "se", "ma", "come"}

ID_FONTE = "S005"
PDF = os.path.join(RADICE, "raccolta", "grezzi", "s005", "nannini_1805.pdf")
OCR = os.path.join(RADICE, "raccolta", "grezzi", "s005", "ocr")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")
FONTE = ("Francesco Nannini, Vocabolario portatile ferrarese-italiano, 1805, "
         "pag. %d (S005)")
NOTA = ("Letta con OCR (tesseract) dalla scansione di archive.org, non "
        "confrontata col libro: vedi la pagina.")

# Le categorie che il Nannini scrive dopo il lemma, e le loro letture sbagliate
# piu' frequenti («egg.» per «agg.»).
CATEGORIE = {"agg", "egg", "add", "sost", "sust", "sest", "v", "verb", "avv",
             "prep", "cong", "pron", "part", "num", "sing", "plur", "pl", "n",
             "m", "f", "s", "att", "neut", "pass", "dim", "accr", "pegg",
             "interj", "int", "inter", "voc", "volg", "fig", "e", "g", "anche",
             "agg.", "sost.", "verbo", "significa", "voce contadinesca"}
# La pronuncia della vocale tonica, che il Nannini scrive dopo il lemma («Bo ,
# larga , bue»; «Cavell' , stretto , capello»): non e' un reso, ma e' un dato
# sul suono, e va nella nota della voce.
TIMBRI = {"larga", "largo", "stretta", "stretto"}
# Le parole che possono stare dentro un reso ma non esserlo da sole.
FUNZIONALI = {"di", "a", "da", "in", "con", "su", "per", "il", "lo", "la", "i",
              "gli", "le", "un", "una", "uno", "e", "o", "del", "della",
              "dei", "delle", "al", "alla", "alle", "ai", "che", "non", "si",
              "ne", "come", "piu", "più", "ed", "od", "nel", "nella", "dal"}
LETTERE = "a-zàèéìíòóùúâêîôûäëïöü"
LEMMA = re.compile(r"^[^A-Za-zÀ-ÿ]{0,3}([A-ZÀ-Ý][%s'’]{1,24})\s*[,.]\s*(.*)$" % LETTERE)
RESO = re.compile(r"^[%s'’ ]{2,40}$" % LETTERE)
PAROLA_LEMMA = re.compile(r"^[A-ZÀ-Ý][%s'’]+$" % LETTERE)
PAGINA_STAMPATA = re.compile(r"(\d{1,3})")


# --- la lettura delle scansioni ----------------------------------------------

def leggi_scansioni(processi: int = 2) -> None:
    """tesseract su ogni pagina, colonna per colonna."""
    import subprocess
    import tempfile
    from concurrent.futures import ThreadPoolExecutor

    import numpy as np
    from PIL import Image

    os.makedirs(OCR, exist_ok=True)

    def png(immagine):
        b = io.BytesIO()
        immagine.save(b, format="PNG")
        return b.getvalue()

    def tesseract(immagine):
        return subprocess.run(["tesseract", "-", "-", "-l", "ita", "--psm", "6"],
                              input=png(immagine), capture_output=True,
                              check=True).stdout.decode("utf-8")

    def pagina(n):
        destinazione = os.path.join(OCR, "p%03d.txt" % n)
        if os.path.exists(destinazione):
            return
        with tempfile.TemporaryDirectory() as cartella:
            base = os.path.join(cartella, "p")
            subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-r", "300",
                            "-gray", "-singlefile", PDF, base], check=True)
            immagine = Image.open(base + ".pgm")
            larghezza, altezza = immagine.size
            # Il solco fra le colonne e' la striscia piu' bianca del terzo
            # centrale della pagina.
            centro = np.array(immagine)[int(altezza * .08):int(altezza * .95),
                                        int(larghezza * .35):int(larghezza * .65)]
            solco = int(larghezza * .35) + int(centro.mean(axis=0).argmax())
            testata = tesseract(immagine.crop((0, 0, larghezza, int(altezza * .07))))
            sinistra = tesseract(immagine.crop((0, int(altezza * .06), solco, altezza)))
            destra = tesseract(immagine.crop((solco, int(altezza * .06),
                                              larghezza, altezza)))
        with io.open(destinazione, "w", encoding="utf-8") as f:
            f.write("## TESTATA\n%s\n## SINISTRA\n%s\n## DESTRA\n%s"
                    % (testata, sinistra, destra))

    import subprocess as _s
    pagine = int(re.search(r"Pages:\s+(\d+)", _s.run(
        ["pdfinfo", PDF], capture_output=True, text=True).stdout).group(1))
    with ThreadPoolExecutor(processi) as esecutore:
        list(esecutore.map(pagina, range(1, pagine + 1)))


# --- dalle pagine alle voci --------------------------------------------------

def scarto_delle_pagine(testate: dict) -> int:
    """Quante pagine del PDF vengono prima della pagina 1 del libro.

    Il numero in testa alla pagina l'OCR lo legge spesso male («36» diventa
    «56» o sparisce); lo scarto fra pagina del PDF e pagina stampata invece e'
    lo stesso per tutto il libro. Si prende quello che la maggior parte delle
    testate dice, e la pagina stampata e' il numero del PDF meno lo scarto.
    """
    voti = collections.Counter()
    for numero_pdf, testata in testate.items():
        for m in PAGINA_STAMPATA.finditer(testata):
            differenza = numero_pdf - int(m.group(1))
            if 0 < differenza < 12:
                voti[differenza] += 1
    if not voti:
        raise SystemExit("nessuna testata leggibile: la pagina del libro non "
                         "si puo' citare")
    return voti.most_common(1)[0][0]


def righe_delle_colonne(testo: str) -> list:
    colonne = re.split(r"^## (?:SINISTRA|DESTRA)\s*$", testo, flags=re.M)[1:]
    righe = []
    for colonna in colonne:
        righe.extend(r.strip() for r in colonna.splitlines() if r.strip())
    return righe


def voci_della_pagina(righe: list) -> list:
    """Le voci: una riga che comincia con un lemma apre una voce nuova."""
    voci, corrente = [], None
    for riga in righe:
        m = LEMMA.match(riga)
        if m and (corrente is None or corrente.rstrip().endswith((".", ";", ")"))
                  or riga[:1] in "ABCDEFGHILMNOPQRSTUVZ"):
            if corrente:
                voci.append(corrente)
            corrente = riga
        elif corrente is not None:
            if corrente.endswith("-"):
                corrente = corrente[:-1] + riga
            else:
                corrente += " " + riga
    if corrente:
        voci.append(corrente)
    return voci


def lessico_italiano() -> set:
    """Le parole italiane che il progetto conosce gia', per riconoscere un reso.

    Sono le parole dei campi `italiano` del glossario (il Ferri, Bigoni,
    Musacchi: l'italiano dell'Ottocento compreso) e di `dati/italiano.jsonl`.
    Un reso del Nannini entra solo se ogni sua parola e' fra queste: l'OCR
    che legge «le vare» per «levare» o «a nitra» per «anitra» produce parole
    che nessuna fonte ha, e una voce con un italiano inventato dall'OCR e'
    peggio di nessuna voce. Il prezzo e' dichiarato: un reso raro e giusto
    che nessun'altra fonte usa resta fuori.
    """
    parole = set()
    for v in voci_attive(GLOSSARIO):
        if "(S005)" in v.get("fonte", ""):
            continue
        for p in re.findall(r"[^\W\d_]+", (v.get("italiano") or "").lower()):
            parole.add(chiave(p))
    percorso = os.path.join(RADICE, "dati", "italiano.jsonl")
    if os.path.exists(percorso):
        with io.open(percorso, encoding="utf-8") as f:
            for riga in f:
                if riga.startswith("{"):
                    parole.add(chiave(json.loads(riga).get("forma", "")))
    return parole


def _riconosciuto(reso: str, lessico) -> bool:
    if lessico is None:
        return True
    parole = [chiave(p) for p in reso.split() if p]
    return bool(parole) and all(p in lessico for p in parole)


def leggi_voce(testo: str, lessico=None):
    """`(lemma, italiano, principale, motivo, timbro)`; motivo e' None se entra."""
    m = LEMMA.match(testo)
    if not m:
        return None, None, None, "senza lemma", ""
    lemma, resto = m.group(1).replace("’", "'"), m.group(2)
    # x, k, w, y non sono lettere della grafia del Nannini: un lemma che le
    # contiene e' una lettura sbagliata («Capplazx» per «Capplazz»).
    if not PAROLA_LEMMA.match(lemma) or len(lemma) < 2 or \
            re.search(r"[xkwy]", lemma.lower()):
        return lemma, None, None, "lemma illeggibile", ""
    resto = re.sub(r"\s+", " ", resto)
    resto = resto.split(":")[0]
    pezzi = [p.strip(" .;»«'‘’\"") for p in resto.split(",")]
    # «Blisgar , v. Sblìsgar»: un rimando, anche dopo la categoria.
    for primo in pezzi[:2]:
        if re.match(r"^(?:[vV]\.?|vedi)\s+\S", primo):
            return lemma, None, None, "rimando", ""
    # «sost. fuso», «agg. bollato»: la categoria attaccata al primo reso.
    while pezzi:
        m = re.match(r"^([A-Za-z]{1,6})\.?\s+(.+)$", pezzi[0])
        if m and m.group(1).lower() in CATEGORIE | TIMBRI:
            pezzi[0:1] = [m.group(1), m.group(2)]
            break
        break
    timbro = ""
    while pezzi and (pezzi[0].lower().rstrip(".") in CATEGORIE | TIMBRI
                     or not pezzi[0]):
        if pezzi[0].lower().rstrip(".") in TIMBRI:
            timbro = pezzi[0].lower().rstrip(".")
        pezzi.pop(0)
    if not pezzi:
        return lemma, None, None, "senza italiano", ""
    if re.match(r"^[vV]\.?\s", pezzi[0] + " ") or pezzi[0].lower() in ("v", "vedi"):
        return lemma, None, None, "rimando", ""
    pezzi = [re.sub(r"^(?:per|anche|e|o)\s+", "", p) for p in pezzi]
    buoni = []
    for p in pezzi:
        p = p.strip(" .")
        # il timbro puo' venire dopo il primo reso («Loi , stretta , loglio»)
        # o attaccato a lui («capello stretto»)
        ultima = p.lower().split()[-1] if p.split() else ""
        if ultima in TIMBRI:
            timbro = timbro or ultima
            p = p[:len(p) - len(ultima)].strip()
            if not p:
                continue
        if not RESO.match(p.lower()):
            break
        parole = p.lower().split()
        if not _riconosciuto(p, lessico):
            continue
        if any(len(w) < 3 and w not in FUNZIONALI for w in parole):
            continue
        if not any(len(w) >= 4 and w not in FUNZIONALI for w in parole):
            continue
        buoni.append(p)
    if not buoni:
        return lemma, None, None, "reso illeggibile", ""
    principale = buoni[0]
    # Le parole funzionali non sono voci (la regola e' in `copertura.py` e nel
    # test `TestVociMeccaniche`): «Al , egli» non entra, ne' dal lato
    # ferrarese ne' da quello italiano.
    if chiave(lemma) in FUNZIONALI_PROGETTO or any(
            chiave(b) in FUNZIONALI_PROGETTO for b in buoni):
        return lemma, None, None, "funzionale", ""
    if chiave(lemma) and chiave(lemma) in [chiave(w) for w in principale.split()]:
        return lemma, None, None, "locuzione", ""
    if any(len(w) < 2 and w not in ("a", "e", "o", "i") for w in principale.split()):
        return lemma, None, None, "reso illeggibile", ""
    return lemma, ", ".join(buoni), principale, None, timbro


def raccogli() -> tuple:
    voci, scartate = [], collections.Counter()
    testi = {}
    for nome in sorted(os.listdir(OCR)):
        with io.open(os.path.join(OCR, nome), encoding="utf-8") as f:
            testi[int(nome[1:4])] = f.read()
    scarto = scarto_delle_pagine(
        {n: t.split("## SINISTRA")[0] for n, t in testi.items()})
    lessico = lessico_italiano()
    for numero_pdf, testo in sorted(testi.items()):
        stampata = numero_pdf - scarto
        if stampata < 1:
            continue
        for grezza in voci_della_pagina(righe_delle_colonne(testo)):
            lemma, italiano, principale, motivo, timbro = leggi_voce(grezza, lessico)
            if motivo:
                scartate[motivo] += 1
                continue
            voci.append({"ferrarese": lemma, "italiano": italiano,
                         "principale": principale, "pagina": stampata,
                         "pagina_pdf": numero_pdf, "timbro": timbro})
    return voci, scartate


def confronta(raccolte: list, attive: list) -> dict:
    def _k(v):
        return (chiave(v.get("ferrarese", "")),
                chiave(v.get("principale_italiano") or
                       v.get("italiano", "").split(",")[0]))
    nostre = {_k(v) for v in attive if "(S005)" in v.get("fonte", "")}
    gia = {_k(v) for v in attive if "(S005)" not in v.get("fonte", "")}
    esiti = {"nuove": [], "concordanze": [], "doppie": 0, "gia_scritte": 0}
    viste = set()
    for v in raccolte:
        k = (chiave(v["ferrarese"]), chiave(v["principale"]))
        if k in viste:
            esiti["doppie"] += 1
            continue
        viste.add(k)
        if k in nostre:
            esiti["gia_scritte"] += 1
        if k in gia:
            esiti["concordanze"].append(v)
        elif k not in nostre:
            esiti["nuove"].append(v)
    return esiti


def costruisci(nuove: list, prossimo: int, varieta: str) -> list:
    righe = []
    for v in nuove:
        righe.append({
            "id": "V%04d" % prossimo,
            "varieta": varieta,
            "ferrarese": v["ferrarese"],
            "italiano": v["italiano"],
            "principale_italiano": v["principale"],
            "varianti": [],
            "campo": "",
            "note": NOTA + (" La fonte scrive dopo il lemma «%s»: e' la vocale "
                            "tonica %s." % (v["timbro"], "aperta" if v["timbro"]
                                            .startswith("larg") else "chiusa")
                            if v.get("timbro") else ""),
            "fonte": FONTE % v["pagina"],
            "attendibilita": "I",
            "da_verificare": True,
        })
        prossimo += 1
    return righe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Il vocabolario del Nannini (S005).")
    ap.add_argument("--ocr", action="store_true", help="rilegge le scansioni")
    ap.add_argument("--prova", action="store_true", help="non scrive")
    args = ap.parse_args(argv)
    if args.ocr:
        leggi_scansioni()
    if not os.path.isdir(OCR) or not os.listdir(OCR):
        raise SystemExit("manca %s: lancia prima --ocr" % OCR)
    dichiarazione = varieta_dichiarata(VARIETA, ID_FONTE)
    varieta = dichiarazione.get("varieta")
    attive = voci_attive(GLOSSARIO)
    # Le voci gia' scritte da questo script non si riscrivono: lo script e'
    # idempotente, come quello di Bigoni.
    raccolte, scartate = raccogli()
    esiti = confronta(raccolte, attive)
    prossimo = max(prossimo_id(attive), id_in_attesa() + 1)
    righe = costruisci(esiti["nuove"], prossimo, varieta)
    print("voci lette                     %d" % len(raccolte))
    for motivo, quante in scartate.most_common():
        print("scartate, %-20s %d" % (motivo, quante))
    print("doppie nella fonte             %d" % esiti["doppie"])
    print("concordanze con il glossario   %d" % len(esiti["concordanze"]))
    print("nuove                          %d" % len(righe))
    print("gia' scritte da questo script  %d" % esiti["gia_scritte"])
    if args.prova or not righe:
        return 0
    with io.open(GLOSSARIO, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci in dati/glossario.jsonl" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
