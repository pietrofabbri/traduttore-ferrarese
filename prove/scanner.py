#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scanner: nessun file tracciato da git contiene caratteri sbagliati.

Un progetto che scrive una lingua romagnola non deve avere un ideogramma
scambiato per un accento, e succede perche' il carattere giusto e' spesso
quello giusto anche a occhio: `λ` e `l` si somigliano, `с` e `c` si
somigliano, `а` e `a` si somigliano. Il controllo e' meccanico e gira su ogni
macchina, quindi gira su ogni macchina.

**Le eccezioni sono dichiarate qui e solo qui**, e sono tre, e ognuna ha un
motivo:

1. `χ` e `β` sono simboli **IPA** e compaiono nell'insieme dei simboli ammessi
   in `sorgenti/traduttore/fonetica.py`. Non sono greco: sono l'alfabeto della
   trascrizione, e senza loro `ipa_valida` non potrebbe accettare niente;
2. `λ` compare in due voci del glossario, `biλjét` e `biλjêtàri`, e li' e' la
   **fonte** a scriverlo: Bigoni (S006) usa la lambda per il suono che
   l'italiano scrive `gl`, quindi `biλjét` e' quello che la fonte ha scritto,
   non quello che un errore di battitura avrebbe prodotto. Il progetto lo sa:
   la chiave di ricerca di quelle due voci e' `bijét`, cioe' senza lambda;
3. `ɣ` e' la **gamma IPA** (U+0263), non la greca (U+03B3), e non e' quindi
   nemmeno un'eccezione: sta fuori dall'intervallo greco e qui e' elencata
   solo perche' qualcuno la cerca.

Tutto il resto e' un errore. Il numero che esce e' quello che va nel registro,
e va detto con le sue parole: «115 file tracciati, 0 ideogrammi» e' una
dichiarazione vera solo se lo scanner e' passato.

Uso:
    python3 prove/scanner.py            # dentro questa cartella
    python3 prove/scanner.py /percorso  # dentro un altro repository
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

# I caratteri che il progetto ammette e che somigliano a qualcosa di sbagliato.
# `perche'` sono ammessi: la chiave le toglie, e il glossario le dichiara.
AMMESSI = {
    "χ": "chi IPA, in SIMBOLI_IPA",
    "β": "beta IPA, in SIMBOLI_IPA",
    "λ": "lambda della fonte S006 (Bigoni, voci 701 e 702)",
}

INTERESSANTI = (
    ("ideogramma cinese", "[一-鿿㐀-䶿]"),
    ("punteggiatura CJK", "[　-〿]"),
    ("kana giapponese", "[぀-ヿ]"),
    ("scrittura coreana", "[가-힯]"),
    ("cirillico", "[Ѐ-ӿ]"),
    ("greco", "[Ͱ-Ͽ]"),
    ("larghezza piena", "[＀-￯]"),
)

NON_TESTO = (".wav", ".mp3", ".ogg", ".m4a", ".png", ".jpg", ".jpeg", ".gz",
             ".pdf", ".zip")


def _file_sospetti(percorso: str, espressioni) -> list:
    """Le righe sospette di un file, con il motivo."""
    if not os.path.isfile(percorso) or percorso.endswith(NON_TESTO):
        return []
    try:
        with io.open(percorso, encoding="utf-8") as f:
            testo = f.read()
    except (UnicodeDecodeError, ValueError):
        return []
    trovate = []
    for numero, riga in enumerate(testo.split("\n"), 1):
        for motivo, casella in espressioni:
            for carattere in re.findall(casella, riga):
                if carattere in AMMESSI:
                    continue
                trovate.append("%s:%d  %s (%s)"
                               % (percorso, numero, carattere, motivo))
    return trovate


def main() -> int:
    dentro = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    espressioni = [(motivo, re.compile(casella)) for motivo, casella
                   in INTERESSANTI]
    tracciati = subprocess.run(["git", "-C", dentro, "ls-files"],
                               stdout=subprocess.PIPE, check=True
                               ).stdout.decode("utf-8").split()
    trovate = []
    for nome in tracciati:
        trovate += _file_sospetti(os.path.join(dentro, nome), espressioni)
    for riga in trovate:
        print(riga)
    print("%d file tracciati, %d righe sospette" % (len(tracciati), len(trovate)))
    print("ammessi: %s" % ", ".join("%s (%s)" % (c, m)
                                    for c, m in sorted(AMMESSI.items())))
    return 1 if trovate else 0


if __name__ == "__main__":
    sys.exit(main())