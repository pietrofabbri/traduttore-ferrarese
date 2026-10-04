"""Il sito statico: una pagina, nessuna richiesta di rete, nessun account.

Le stesse regole che valgono per il gioco valgono qui, perche' e' lo stesso
pubblico: la pagina si apre da un file sul disco o da GitHub Pages, funziona
senza connessione e non chiede nulla a nessuno.

Cosa fa la pagina, in tutto:

1. traduce una frase parola per parola, colorando **da quale parte viene**
   ogni parola (glossario, corpus, regola, modello, nessuna);
2. lascia **sporco** quello che non sa: la parola non tradotta resta nella
   riga e si vede;
3. permette di cercare il glossario e di leggere la fonte di ogni voce;
4. dice in **quale varieta'** e' ogni voce, e dice anche quali varieta' sono
   vuote;
5. mostra il **riproduttore**: la trascrizione IPA accanto alla parola, e
   l'audio quando - e solo quando - esiste, ha il consenso e la licenza.

Il colore non e' decorazione: e' l'informazione. Chi usa questa pagina in
classe deve poter dire «questa parola l'ha data il glossario» e «questa
non l'ha data nessuno» senza chiedere.

Il glossario viaggia dentro la pagina, in un blocco `<script>`. Non e' una
scelta elegante: e' la scelta che rende la pagina apribile da `file://` senza
server, che e' la condizione con cui la si distribuisce. L'audio non puo'
fare la stessa cosa - un file audio da solo pesa qualche decimo di
meggabyte - quindi viene copiato in `web/audio/` e li' resta, e il permesso di
copiarlo e' chiesto tre volte prima (vedi `audio/README.md`).
"""

from __future__ import annotations

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traduttore import morfologia  # noqa: E402
from traduttore.audio import Archivio  # noqa: E402
from traduttore.corpora import Corpus  # noqa: E402
from traduttore.fonetica import Fonetica  # noqa: E402
from traduttore import verifica_dati  # noqa: E402
from traduttore.glossario import Glossario  # noqa: E402
from traduttore.motore import ORIGINE  # noqa: E402
from traduttore.varieta import NOMI, Varieta  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modello.html")


def _dati_per_la_pagina(glossario: Glossario, corpus: Corpus, regole: list,
                        varieta: Varieta = None, fonetica: Fonetica = None,
                        archivio: Archivio = None, audio_disponibili=None) -> dict:
    """Raccoglie tutto quello che la pagina deve sapere, in un solo JSON."""
    varieta = varieta or Varieta([])
    fonetica = fonetica or Fonetica([])
    archivio = archivio or Archivio([])
    audio_disponibili = set(audio_disponibili or [])
    conteggi = varieta.conteggi(glossario=glossario, coppie=corpus.coppie,
                                audio=list(archivio))
    # I buchi dichiarati entrano nei dati della pagina e non sono calcolati in
    # JavaScript: se la pagina e il terminale contassero gli stessi numeri per
    # conto loro, un giorno avrebbero detto cose diverse e nessuno avrebbe la
    # certezza di quale delle due quella giusta.
    return {
        "glossario": [
            {
                "id": v.id,
                "fe": v.ferrarese,
                "it": v.italiano,
                "varianti": v.varianti,
                "campo": v.campo,
                "varieta": v.varieta,
                "note": v.note,
                "fonte": v.fonte,
                "attendibilita": v.attendibilita,
                "registro": v.registro,
                "principale_it": v.principale_italiano,
                "principale_fe": v.principale_ferrarese,
                "da_verificare": v.da_verificare,
                "moderno": v.moderno,
                "fonte_moderno": v.fonte_moderno,
                "sinonimi": v.sinonimi,
            }
            for v in glossario.voci
        ],
        "coppie": [
            {
                "id": c.id,
                "it": c.italiano,
                "fe": c.ferrarese,
                "tipo": c.tipo,
                "varieta": c.varieta,
                "fonte": c.fonte,
                "nota": c.nota,
            }
            for c in corpus.coppie
        ],
        "proverbi": [
            {
                "id": p.id,
                "it": p.italiano,
                "fe": p.ferrarese,
                "letterario": p.letterario,
                "popolare": p.popolare,
                "fonte": p.fonte,
                "significato": p.significato,
            }
            for p in corpus.proverbi
        ],
        "regole": [
            {
                "etichetta": r.etichetta(),
                "accordo": round(r.accordo, 3),
                "supporto": r.supporto,
                "prefisso": r.prefisso,
                "suffisso_italiano": r.suffisso_italiano,
                "suffisso_ferrarese": r.suffisso_ferrarese,
            }
            for r in regole
        ],
        # Le varieta' con quello che c'e' dentro: la pagina deve poter dire
        # «quattro varieta' su cinque sono vuote» senza chiedere al terminale.
        "varieta": dict(varieta.come_dict(), conteggi=conteggi,
                        vuote=varieta.vuote(conteggi)),
        "fonetica": [t.come_dict() for t in fonetica.trascrizioni],
        "audio": [
            dict(b.come_dict(),
                 # `file` diventa il percorso dentro la pagina, e vale solo se
                 # il brano e' davvero pronto. Se non c'e' resta vuoto e la
                 # pagina non mette un tasto che non suona niente.
                 file_playable="audio/" + b.file
                 if b.id in audio_disponibili else "")
            for b in archivio.brani
        ],
        "nomi_varieta": NOMI,
        "origine": ORIGINE,
        "buchi": verifica_dati.buchi_dichiarati(glossario, corpus, fonetica),
        # Le voci a cui la fonte non ha dato un significato moderno. La pagina
        # non puo' contarli da sola: i dati sono gia' filtrati per varieta' e
        # per ricerca, e il numero che mostra la tabella non e' quello del
        # glossario intero. Il conteggio e' fatto qui, una volta sola.
        "moderno_buchi": sum(1 for v in glossario.voci if not v.moderno),
        "moderno_con_sinonimi": sum(1 for v in glossario.voci if v.sinonimi),
    }


def carica_tutto(radice: str):
    dati = os.path.join(radice, "dati")
    glossario = Glossario.da_file(os.path.join(dati, "glossario.jsonl"))
    corpus = Corpus.da_file(os.path.join(dati, "coppie.jsonl"), os.path.join(dati, "proverbi.jsonl"))
    varieta = Varieta.da_file(os.path.join(dati, "varieta.json"))
    fonetica = Fonetica.da_file(os.path.join(dati, "fonetica.jsonl"))
    archivio = Archivio.da_file(os.path.join(dati, "audio.jsonl"))
    percorso_regole = os.path.join(dati, "regole.json")
    regole = []
    if os.path.exists(percorso_regole):
        with open(percorso_regole, "r", encoding="utf-8") as f:
            regole = [morfologia.Regola(**r) for r in json.load(f).get("regole", [])]
    return glossario, corpus, regole, varieta, fonetica, archivio


def copia_audio(archivio: Archivio, radice_audio: str, web_dir: str) -> list:
    """Copia in `web/audio/` solo i brani che si possono davvero pubblicare.

    Copiare un brano e' pubblicarlo: e' il punto in cui una registrazione
    fatta in una cucina finisce su un sito pubblico. Per questo la copia non
    guarda il flag `pubblicabile` da solo, e pretende anche il consenso, la
    licenza e il file sul disco. Un brano che non passa non viene copiato e
    la pagina non lo annuncia: non si promette un suono che non c'e'.
    """
    destinazione = os.path.join(web_dir, "audio")
    copiati = []
    for brano in archivio.brani:
        if not brano.publicabile():
            continue
        if not brano.esiste(radice_audio):
            continue
        os.makedirs(destinazione, exist_ok=True)
        shutil.copyfile(brano.percorso(radice_audio),
                        os.path.join(destinazione, os.path.basename(brano.file)))
        copiati.append(brano.id)
    return copiati


def costruisci(radice: str = None, destinazione: str = None) -> str:
    radice = radice or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destinazione = destinazione or os.path.join(radice, "web", "index.html")
    glossario, corpus, regole, varieta, fonetica, archivio = carica_tutto(radice)
    copiati = copia_audio(archivio, os.path.join(radice, "audio"),
                          os.path.dirname(destinazione))
    dati = _dati_per_la_pagina(glossario, corpus, regole, varieta, fonetica,
                               archivio, copiati)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        modello = f.read()
    grezzo = json.dumps(dati, ensure_ascii=False, indent=1)
    # Il JSON va in un elemento di tipo non eseguibile, perche' una voce con
    # la sequenza `</script>` dentro romperebbe la pagina. Il carattere di
    # escape e' la barra rovesciata, che JSON accetta e il browser no dentro
    # un elemento script: e' il modo piu' semplice per non doverlo sostituire.
    grezzo = grezzo.replace("</", "<\\/")
    pagina = modello.replace("/*DATI*/null", grezzo)
    os.makedirs(os.path.dirname(destinazione), exist_ok=True)
    with open(destinazione, "w", encoding="utf-8") as f:
        f.write(pagina)
    return destinazione


if __name__ == "__main__":
    print(costruisci())