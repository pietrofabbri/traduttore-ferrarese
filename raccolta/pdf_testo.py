"""Estrarre il testo da un PDF senza librerie.

Perche' esiste: questo progetto non ha dipendenze e non puo' averne, perche'
deve funzionare su una macchina scolastica dove non si installa niente. E
perche' sul computer di un docente che non ha mai sentito parlare di ambienti
virtuali, `pip install pypdf` non e' un'opzione.

Quindi un estrattore minimo, che fa una cosa sola e la dichiara: legge i
flussi di contenuto di un PDF, li decomprime e ne ricava il testo. **Non e'
un lettore di PDF**: non legge le tabelle, non ricostruisce le colonne, non
capisce i font con codifiche esotiche, e su un PDF scansione non legge niente
perche' non c'e' niente da leggere.

Quello che fa bene e' il caso che qui interessa: un PDF generato da un
programma di scrittura, che e' il caso dei documenti raccolti in `raccolta/`.
E quando incontra qualcosa che non capisce, **lo dice e si ferma**: un
estratore che inventa il testo di un vocabolario produce un glossario falso,
che e' il danno peggiore che questo progetto possa fare.

Uso:

    python3 raccolta/pdf_testo.py grezzi/domestico_gaia.pdf testo.txt
"""

from __future__ import annotations

import re
import sys
import zlib


def _flussi(bruto: bytes):
    """I flussi di contenuto decomprimibili."""
    for m in re.finditer(rb"stream\r?\n", bruto):
        inizio = m.end()
        fine = bruto.find(b"endstream", inizio)
        if fine < 0:
            continue
        dato = bruto[inizio:fine]
        try:
            yield zlib.decompress(dato)
        except zlib.error:
            # Non e' tutto deflattato, e va bene: si prova anche grezzo.
            if b"Tj" in dato or b"TJ" in dato:
                yield dato


def _unescape(corpo: bytes) -> bytes:
    """I codici delle parentesi quadre, che sono il modo in cui un PDF scrive
    una parentesi, una barra rovesciata o un accento."""
    sostituzioni = {
        rb"\\n": b"\n", rb"\\r": b"\r", rb"\\t": b"\t",
        rb"\\(": b"(", rb"\\)": b")", rb"\\\\": b"\\",
    }
    for cerca, metti in sostituzioni.items():
        corpo = corpo.replace(cerca, metti)
    return re.sub(rb"\\[0-7]{1,3}", b" ", corpo)


def testo(bruto: bytes) -> str:
    """Il testo di un PDF, per quel che si puo' tirare fuori."""
    parti = []
    for flusso in _flussi(bruto):
        if b"BT" not in flusso:
            continue
        # Le stringhe dentro gli operatori di testo: ( ... ) Tj e [ ( .. ) ] TJ
        for m in re.finditer(rb"\((?:[^()\\]|\\.)*\)", flusso):
            parti.append(_unescape(m.group(0)[1:-1]).decode("latin-1"))
        parti.append("\n")
    testo = "".join(parti)
    testo = testo.replace("\r", "\n")
    # Spaziature bianche ripetute: nell'OCR e'rumore, e rumore in un vocabolario
    # si trasforma in parole che non esistono.
    testo = re.sub(r"[ \t]{2,}", " ", testo)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return testo.strip()


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) != 2:
        print(__doc__)
        return 1
    with open(argv[0], "rb") as f:
        grezzo = f.read()
    testo_pdf = testo(grezzo)
    if not testo_pdf:
        print("nessun testo ricavato: o il PDF e' una scansione, o usa una "
              "codifica che questo estrattore non legge.\n"
              "NON si prosegue con un testo vuoto: un vocabolario letto a "
              "meta' e' peggio di nessun vocabolario.")
        return 2
    with open(argv[1], "w", encoding="utf-8") as f:
        f.write(testo_pdf)
    print("%s -> %s: %d caratteri" % (argv[0], argv[1], len(testo_pdf)))
    return 0


if __name__ == "__main__":
    sys.exit(main())