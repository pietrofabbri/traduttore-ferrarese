#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porta dentro i candidati di Ferri rimasti, senza sceglierli uno a uno.

`lettura_ferri.py` ha scelto 210 voci a mano. Il vocabolario del Ferri ne
contiene altre 11101 che nessuno ha mai guardato, e 8253 di queste sono
parole singole: il glossario attivo ne aveva 28. E' la ragione per cui
«sedia» non c'era e «scarana» nemmeno.

Qui la scelta non la prende una persona: la prende il filtro, che butta via
quello che l'OCR ha storpiato (vedi `filtra_candidati.py --pulito`), e tutto
il resto entra con `attendibilita: I` e `da_verificare: true`. Ogni riga porta
la pagina del libro, quindi chiunque puo' aprirlo e controllarla: la riga non
si presenta come verificata, si presenta come trascritta.

Le regole, in ordine:

- la chiave della voce non deve esserci gia': due righe con la stessa voce
  sono due versioni dello stesso fatto, e il progetto ne vuole una;
- la glossa si pulisce del simbolo della categoria («sm - Appoggiatóio»
  diventa «Appoggiatóio») e si prende l'ultimo pezzo, perche' il Ferri mette
  la definizione prima e la resa italiana dopo;
- una glossa che non diventa una resa leggibile non entra. Non si butta
  dentro una parola perche' era li' e basta: una voce non verificabile e'
  peggio di una voce che manca, perche' la motor la usa;
- la pagina deve esserci. Una pagina inventata in un campo `fonte` e' la
  cosa piu' grave che questo script potrebbe fare, quindi se non c'e', la voce
  non entra e il numero si vede.

Uso:
    python3 costruisci_meccanico.py --prova    # dice i numeri, non scrive
    python3 costruisci_meccanico.py            # scrive
    python3 costruisci_meccanico.py --limite 300   # scrive solo le prime 300
"""
from __future__ import annotations

import json
import os
import re
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.glossario import normalizza  # noqa: E402

# Solo i candidati gia' passati da `filtra_candidati.py --pulito`: il
# generatore non rifiltra niente, perche' un filtro dentro un generatore si
# riusa solo finche' nessuno lo tocca.
CANDIDATI = os.path.join(RADICE, "raccolta", "lavorato", "ferri_puliti.tsv")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")

AUTORE = "Luigi Ferri"
OPERA = "Vocabolario ferrarese-italiano"
ANNO = 1889

# Le parole funzionali non entrano, e il motivo **non** e' quello che era
# scritto qui prima.
#
# La versione precedente di questo commento attribuiva gli articoli e le
# preposizioni a `morfologia.py`, e dava per scontato che il motore li sapesse.
# L'ho verificato e **non e' vero**: in quel modulo non c'e' nessun elenco di
# articoli o preposizioni — quello impara desinenze dal corpus — e il motore
# non li traduce: `il -> il` con confidenza 0, `ho -> ho` con confidenza 0. Su
# 131 parole funzionali dell'elenco di `copertura.py`, 38 sono nel glossario e
# 93 passano invariate.
#
# Quindi lo scarto **non** e' una conseguenza di una capacita' che il motore ha:
# e' una **scelta**, e va tenuta per quello che e'. La scelta ha due motivi
# buoni, entrambi verificati: (1) una voce di glossario per «La» riscrive la
# parola con la grafia della fonte, e «La» diventa «La» anche quando il
# soggetto e' un nome proprio — e' il caso che fa scrivere «La portàr» a chi
# chiede «la porta»; (2) il vocabolario si riempirebbe di voci che non
# distinguono le due lingue perche' sono la stessa parola.
#
# Il costo della scelta e' **un buco**, ed e' il buco che rende inutilizzabile
# una frase: di 118 righe scartate da questo filtro, 98 hanno il capoverso
# `Per` — che nel Ferri e' il marchio del rinvio per traslazione, non la
# preposizione, e infatti sono sottentrate come «— Per dim - Laghetto» senza
# capoverso proprio: scartarle e' giusto — e le altre 20 sono forme
# funzionali che il Ferri **dichiara** e che qui vengono buttate via:
# `Sòra` (sopra, pag. 386), `Fora` (fuori, pag. 150), `Còl` (col e collo,
# pag. 92), `Fra` (frate e fra/tra, pag. 151), `Con` (pag. 94), `In` (pag. 187),
# `Tra` (pag. 439), `La` (pag. 213), `Se` (pag. 364), `Che` (pag. 87),
# `Un` (pag. 450).
#
# Quel costo e' dichiarato in `README.md` e nel punto 6 di `AGENTS.md`, e
# cambiare questa scelta e' una decisione di Pietro, non un refuso da correggere
# qui. Se un giorno le si toglie, il filtro va con lei: sono la stessa cosa.
FUNZIONALI = {
    # articoli
    "il", "lo", "la", "i", "gli", "le", "un", "una", "uno", "l", "lo'", "l'",
    # preposizioni
    "a", "al", "alla", "ai", "agli", "alle", "da", "dal", "dla", "di", "dal",
    "in", "nel", "nella", "nei", "negli", "nelle", "con", "col", "cun",
    "per", "pur", "tra", "fra", "sora", "su", "sul", "sula", "sui", "sopra",
    "soto", "sot", "dint", "dentro", "fora", "ontra", "senza", "sensa",
    # congiunzioni e avverbi che il Ferri registra come voce
    "e", "ed", "o", "od", "ma", "che", "come", "se", "quando", "perche",
    "perché", "poi", "ancora", "anco", "inanca", "inante", "dopo", "sora",
    # ausiliari. Nello stesso scarto, per lo stesso motivo: sono forme
    # funzionali e il motore non le tratta. `essere` e `avere` non ci
    # sono, e il glossario non li ha: e' un buco dichiarato, non una
    # parola risolta altrove.
    "essere", "aesse", "aessar", "aera", "avei", "avere", "avar", "aveva",
    "star", "stare", "stava", "ghere", "jere",
}

# Breve per una ragione che e' diventata misurabile: questa nota finisce in
# ogni voce e nella pagina, e a 10000 voci una frase lunga costa 1,4 MB di
# pagina scaricata per dire la stessa cosa 10000 volte. Il testo lungo
# intero sta in questo file e nel registro, non dentro ogni riga.
NOTA = "Trascritta dall'OCR, non confrontata col libro: vedi la pagina."

# Le abbreviazioni del Ferri sono le sue, e il filtro `--pulito` ha gia'
# buttato via quelle che l'OCR aveva rese irriconoscibili. Quelle che restano
# dicono il campo della parola, ed e' la stessa informazione che il campo
# `campo` del glossario si aspetta.
# Solo le abbreviazioni di cui siamo certi. Una categoria indovinata non e'
# un dettaglio innocuo: il motore usa `campo` per non scambiare un pronome
# con un avverbio, quindi una parola etichettata come la classe sbagliata
# e' una parola che il traduttore usa male. Fuori da questo elenco il campo
# resta vuoto, che e' la verita.
CAMPI = {
    "sm": "sostantivo", "sost": "sostantivo", "sf": "sostantivo",
    "agg": "aggettivo", "ag": "aggettivo", "avv": "avverbio",
    "va": "verbo", "vn": "verbo", "vr": "verbo", "v": "verbo",
    "pp": "participio passato", "pron": "pronome", "cong": "congiunzione",
    "prep": "preposizione", "art": "articolo", "num": "numerale",
    "dim": "diminutivo", "loc": "locuzione",
}

# Una categoria rimasta dentro la resa significa che la riga del Ferri
# conteneva un sotto-elenco e l'estrattore ha messo dentro anche quello.
CATEGORIA_NEL_MEZZO = re.compile(
    r"\b(?:sm|sf|agg|ag|avv|aw|va|vn|vr|pp|pron|cong|prep|art|num|dim|loc|int)"
    r"\.\s", re.I)

# Una categoria dentro la resa, senza punto e senza niente che la separi: e'
# una riga che raccoglie piu' sotto-voci («Testìcolo sm granèllo, Fàss sm
# ' Fàssdo»). Di questa riga non si puo' fare una voce sola senza scegliere,
# e scegliere qui sarebbe scegliere al posto di chi legge: quindi la riga
# non entra.

# La stessa abbreviazione, ma in fondo alla resa: e' li' che il Ferri chiude
# la voce, e chi la lascia dentro mette in bocca a chi legge una parola che il
# libro non scrive in quel modo («Arista sf» invece di «Arista»).
CATEGORIA_IN_FONDO = re.compile(
    r"\s+(?:sm|sf|sost|agg|ag|avv|aw|m\.avv|va|vn|vr|pp|pron|cong|prep|art|"
    r"num|dim|loc|int|m)\.?\s*$", re.I)

# Tutte le abbreviazioni che il Ferri usa, con o senza punto. Sono in una lista
# e non in un'espressione libera perche' una lista non puo' mangiare
# l'inizio di una parola vera: «sm» da solo e' una categoria, «sma» e' l'inizio
# di «smerigliato».
TUTTE_LE_ABBREVIAZIONI = ("sm", "sf", "sost", "agg", "ag", "avv", "aw", "va",
                          "vn", "vr", "v", "pp", "pron", "cong", "prep", "art",
                          "num", "dim", "loc", "int", "inter", "pegg", "pl", "m")
ABBREVIAZIONE = "|".join(TUTTE_LE_ABBREVIAZIONI)

# All'inizio della riga: l'estrattore delle sotto-voci lascia la categoria
# attaccata davanti («sm ' Ginòcchio», «agg Solènne»).
CATEGORIA_DAVANTI = re.compile(r"^(?:%s)\.?\s+" % ABBREVIAZIONE, re.I)

# La categoria, come la stampa il Ferri: all'inizio, sola o fra parentesi
# quadre, e seguita dal trattino che la separa dalla resa.
CATEGORIA = re.compile(r"^\[?\s*([a-z]{1,5}\s?\.\s?[a-z]{0,4})\s?\]?\s*(?:[-–]\s*)?", re.I)
SPAZI = re.compile(r"\s+")
# I simboli che l'OCR usa per le colonne e che nel libro sono un segno di
# richiamo: «sf ■ Vernice» e' «sf. Vernice» con un quadratino di mezzo.
SIMBOLI = re.compile(r"[■□▪►▸◄·•]")
# Una glossa che ha dentro uno di questi non e' una resa, e' un Pezzo di
# pagina: tagliarla a meta' produrrebbe una parola che il Ferri non ha scritto.
SPAZZO_MENO = re.compile(r"\s*[-–]\s*$")


def chiave(s: str) -> str:
    return normalizza.chiave(s)


def solo_resa(glossa: str, categoria: str) -> str:
    """Dalla riga del candidat alla resa italiana.

    Il Ferri scrive la definizione e poi la resa: «agg - detto di albero e
    simili - Pièno». Prendere il primo pezzo darebbe a chi legge
    «addentare, azzannare» al posto di «battere i denti», che e' la voce
    giusta. Percio' si prende l'ultimo, e si butta via la categoria che
    talvolta resta attaccata in fondo («Bizzina sf»).
    """
    testo = glossa.strip()
    # La categoria all'inizio, con o senza parentesi quadre e con o senza
    # trattino: e' rumore rispetto alla resa.
    testo = re.sub(r"^\[?\s*", "", testo)
    testo = CATEGORIA_DAVANTI.sub("", testo)
    m = CATEGORIA.match(testo)
    if m:
        testo = testo[m.end():]
    # Tolta la categoria resta il trattino che la divideva dalla resa:
    # senza questo la resa comincia con un trattino e finisce nel glossario
    # come una voce che il Ferri non ha scritto («- Soldato»).
    testo = re.sub(r"^\s*[-–]\s*", "", testo)
    # Le virgolette del libro non sono parte della resa.
    testo = testo.strip(" ,.;'\"")
    if categoria:
        testo = re.sub(r"\s+%s\.?$" % re.escape(categoria.strip()), "", testo, flags=re.I)
    pezzi = [p.strip() for p in testo.split(" - ")]
    pezzi = [p for p in pezzi if p]
    if not pezzi:
        return ""
    testo = SPAZI.sub(" ", pezzi[-1]).strip(" ,.;")
    testo = SPAZZO_MENO.sub("", testo)
    testo = SIMBOLI.sub(" ", testo)
    testo = SPAZI.sub(" ", testo).strip()
    # Un punto dentro la parola e' un punto messo li' dall'OCR: «Tro.vare»
    # e' «Trovare». Fuori dalla parola il punto e' l'abbreviazione della
    # categoria, e quella la togliamo sotto.
    testo = re.sub(r"(?<=[a-zà-ÿ])\.(?=[a-zà-ÿ])", "", testo)
    # La categoria in fondo, anche quando non e' quella dichiarata a capo:
    # «Arista sf», «Rovinio sm», «Velocemente aw».
    testo = CATEGORIA_IN_FONDO.sub("", testo).strip()
    # Un apostrofo o una virgoletta rimasta dentro non e' parte della parola.
    testo = re.sub(r"^[\s'\"]+|[\s'\"]+$", "", testo)
    return testo


def voce_pulita(voce: str) -> str:
    """La voce di testa, senza la categoria che ci si e' attaccata.

    «Tundìn sm» non e' una voce che il Ferri scrive: e' una voce con
    l'etichetta di categoria attaccata dall'estrattore delle sotto-voci.
    """
    testo = SPAZI.sub(" ", voce.strip())
    testo = re.sub(r"^[\s'\"]+|[\s'\"]+$", "", testo)
    return CATEGORIA_IN_FONDO.sub("", testo).strip()


def resa_legibile(resa: str) -> bool:
    """Una resa che non si puo' copiare nel glossario non ci va.

    Non e' un controllo di correttezza: e' il punto in cui la meccanica
    dice di no. Sotto questa soglia non c'e' piu' niente che si possa
    verificare confrontando la riga con il libro, e una voce non verificabile
    e' peggio di una voce che manca, perche' la motor la usa.
    """
    if len(resa) < 2 or len(resa) > 70:
        return False
    if re.search(r"[:;!?—]", resa):
        return False
    # Una riga che continua nella successiva non e' una voce intera: si
    # fermerebbe a meta' parola. Lo dichiara il trattino in fondo.
    if resa.endswith("-"):
        return False
    if CATEGORIA_NEL_MEZZO.search(resa):
        return False
    # Una resa senza vocali non e' una parola: e' un pezzo di riga in cui
    # l'OCR ha perso un pezzo («sso» al posto di «fisso»). Una parola senza
    # vocali in italiano non esiste.
    if not re.search(r"[aeiouàèìòùAEIOUÀÈÌÒÙ]", resa):
        return False
    if not re.search(r"[a-zà-ÿ]{2}", resa, re.I):
        return False
    return True


def voci_esistenti(percorso: str) -> set:
    esistenti = set()
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.startswith("//"):
                continue
            esistenti.add(chiave(json.loads(riga)["ferrarese"]))
    return esistenti


def prossimo_id(percorso: str, prefisso: str) -> int:
    maggiore = 0
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.startswith("//"):
                continue
            ident = json.loads(riga).get("id", "")
            if ident.startswith(prefisso) and ident[1:].isdigit():
                maggiore = max(maggiore, int(ident[1:]))
    return maggiore + 1


def principale(resa: str) -> str:
    """La resa singola, per il campo che il gioco usa."""
    return resa.split(",")[0].split(";")[0].strip()


def main() -> int:
    solo_prova = "--prova" in sys.argv
    limite = None
    for i, a in enumerate(sys.argv):
        if a == "--limite" and i + 1 < len(sys.argv):
            limite = int(sys.argv[i + 1])

    if not os.path.exists(CANDIDATI):
        print("manca %s: lancia prima filtra_candidati.py --pulito" % CANDIDATI)
        return 1

    esistenti = voci_esistenti(GLOSSARIO)
    prossimo = prossimo_id(GLOSSARIO, "V")

    righe = []
    viste = set()
    scartate = {"gia": 0, "senza_resa": 0, "resa_illeggibile": 0,
                "senza_pagina": 0, "troppe_parole": 0, "funzionale": 0}

    with open(CANDIDATI, encoding="utf-8") as f:
        for riga_letta in f:
            campi = riga_letta.rstrip("\n").split("\t")
            if len(campi) < 4:
                continue
            pagina, voce_grezza, cat, glossa = campi[0], campi[1], campi[2], "\t".join(campi[3:])
            categoria = cat.strip().strip("[]").strip()
            voce = voce_pulita(voce_grezza)

            k = chiave(voce)
            if not k or k in esistenti or k in viste:
                scartate["gia"] += 1
                continue
            if k in FUNZIONALI:
                scartate["funzionale"] += 1
                continue
            # Una voce che non sta in nessuna parte e' un pezzo di frasi
            # spezzato dall'OCR: non entra.
            if not voce or len(voce.split()) > 6 or len(voce) > 60:
                scartate["troppe_parole"] += 1
                continue
            if not pagina.isdigit() or int(pagina) <= 0:
                scartate["senza_pagina"] += 1
                continue

            resa = solo_resa(glossa, categoria)
            if not resa:
                scartate["senza_resa"] += 1
                continue
            if not resa_legibile(resa):
                scartate["resa_illeggibile"] += 1
                continue

            # La chiave di deduplicazione e' quella della voce ripulita: due
            # righe che differiscono solo per la categoria attaccata sono la
            # stessa voce, e dentro il glossario devono restare una.
            k = chiave(voce)
            if k in esistenti or k in viste:
                scartate["gia"] += 1
                continue

            viste.add(k)
            righe.append({
                "id": "V%04d" % prossimo,
                "varieta": "cittadino",
                "ferrarese": voce,
                "italiano": resa,
                "principale_italiano": principale(resa),
                "varianti": [],
                "campo": CAMPI.get(categoria.lower().replace(".", ""),
                                   "locuzione" if " " in voce else ""),
                "note": NOTA,
                "fonte": "%s, %s, %d, pag. %s" % (AUTORE, OPERA, ANNO, pagina),
                "attendibilita": "I",
                "da_verificare": True,
            })
            prossimo += 1
            if limite and len(righe) >= limite:
                break

    singole = sum(1 for r in righe if " " not in r["ferrarese"])
    locuzioni = len(righe) - singole
    print("nuove voci: %d (%d parole singole, %d locuzioni)"
          % (len(righe), singole, locuzioni))
    print("scartate: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(scartate.items())))
    if solo_prova:
        for r in righe[:8]:
            print(json.dumps(r, ensure_ascii=False))
        return 0

    with open(GLOSSARIO, "a", encoding="utf-8") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("scritte %d voci in dati/glossario.jsonl" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())