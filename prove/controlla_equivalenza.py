#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le due copie della logica devono dare lo stesso risultato.

`AGENTS.md` lo dice: il motore esiste in Python e in JavaScript, e se le due
divergono la pagina mente, perche' chi legge la pagina ha ragione di crederle.
Fin qui la regola era scritta ma non controllata: nessuno guardava se le due
copie davano la stessa risposta. Questo file guarda.

Il confronto e' sulle **risposte**, non sul codice: le due copie possono
essere scritte diversamente e vanno bene finche' dicono la stessa cosa. Il
che' e' quello che conta, perche' e' quello che l'utente della pagina vede.

Come funziona: prende la pagina generata (che contiene i dati veri dentro un
`<script>`), la esegue con Node facendo finta che `document` esista, e chiama
le stesse funzioni che chiama il browser. Poi confronta con il motore Python
frase per frase.

Se Node non c'e', lo dice e esce con 0: un controllo che non puo' girare
non deve far fallire la CI su una macchina che non ce l'ha. Sulla macchina
che ce l'ha, ed e' `ubuntu-latest` su GitHub, gira.

Uso:  python3 prove/controlla_equivalenza.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.cli import PERCORSI  # noqa: E402
from traduttore.corpora import Corpus  # noqa: E402
from traduttore.glossario import Glossario  # noqa: E402
from traduttore.motore import Motore  # noqa: E402
from traduttore.varieta import Varieta  # noqa: E402

# Frasi con locuzioni dentro, parole sole, e una frase che il corpus
# conosce per intero. Se manca uno di questi tre casi il confronto non
# dice niente.
FRASI = [
    ("it-fe", "a braccia aperte"),
    ("it-fe", "non a caso, ma a braccia aperte"),
    ("it-fe", "a poco a poco"),
    ("it-fe", "non c'è pane"),
    ("it-fe", "andare di pari passo"),
    ("it-fe", "raccogliere il guanto"),
    ("it-fe", "pesce d'aprile"),
    ("fe-it", "a brazz avèrti"),
    ("fe-it", "a crepapànza"),
    ("fe-it", "an ghè brisa pan"),
    ("fe-it", "gagà spudà"),
    ("fe-it", "nat e spudà"),
]

# Il codice che avvolge la pagina e' tutto quello che tocca il DOM: si
# dichiarano finte le funzioni e si lascia che `document` restituisca un
# oggetto che accetta qualunque cosa. L'unica eccezione e' il blocco dei
# dati, che va restituito vero, altrimenti la pagina non ha niente da dire.
INCOLLANCI = """
var DATI_GREZZI = %s;
var document = {
  getElementById: function (id) { return {
    value: "", textContent: (id === "dati") ? DATI_GREZZI : "",
    innerHTML: "", setAttribute: function () {},
    addEventListener: function () {}, appendChild: function () {},
    createElement: function () { return {}; }
  }; },
  createElement: function () { return { appendChild: function () {} }; },
  addEventListener: function () {}
};
var window = { addEventListener: function () {} };
"""


def estrae_script(pagina: str) -> str:
    blocchi = re.findall(r"<script>(.*?)</script>", pagina, re.S)
    if not blocchi:
        raise SystemExit("la pagina non ha blocchi <script>: non c'e' niente da confrontare")
    return "\n".join(blocchi)


def estrae_dati(pagina: str) -> str:
    m = re.search(r'<script id="dati"[^>]*>(.*?)</script>', pagina, re.S)
    if not m:
        raise SystemExit("la pagina non ha il blocco dei dati: non c'e' niente da confrontare")
    return m.group(1)


def apre_lo_script(script: str, dati: str) -> str:
    """Il codice della pagina, con una porta per guardarlo da fuori.

    Lo script e' tutto dentro una funzione anonima — e deve restarlo, perche'
    una pagina non deve sporcare la finestra di chi la guarda. Per il confronto
    si usa lo stesso trucco che si usa per il `json.loads` di un file JSON:
    gli si mette dentro una `return` cheportsi fuori quello che serve, senza
    toccare il sorgente.
    """
    if "})();" not in script:
        raise SystemExit("lo script della pagina non ha la forma attesa: manca il `})();`")
    dentro = script.rsplit("})();", 1)[0]
    # La IIFE della pagina ha gia' la sua apertura: si toglie, e al suo posto
    # se ne mette una uguale che restituisce quello che il confronto guarda.
    aperta = "(function () {"
    if dentro.lstrip().startswith(aperta):
        dentro = dentro.lstrip()[len(aperta):]
    else:
        raise SystemExit("lo script della pagina non comincia come una IIFE: "
                         "il confronto va aggiornato insieme alla pagina")
    porta = """
  return { accorpa: accorpa, accorpaTutto: accorpaTutto, tokenizza: tokenizza,
           risolvi: risolvi, chiave: chiave, fraseGemella: fraseGemella };
"""
    return (INCOLLANCI % json.dumps(dati)) + "\n" + (
        "var PAGINA = (function () {" + dentro + porta + "})();")


def risposta_js(script: str, dati: str, direzione: str, frase: str) -> dict:
    """Il risultato della pagina, riga per riga."""
    programma = apre_lo_script(script, dati) + """
// La pagina ha un caso che il motore ha e che qui va riprodotto: se tutta la
// frase e' gia' nel corpus, non la si smembra e si risponde con lei intera.
var g = PAGINA.fraseGemella(%s, %s);
if (g) {
  console.log(JSON.stringify([{ testo: %s, tradotto: (%s === "it-fe") ? g.fe : g.it, origine: "corpo" }]));
} else {
  var fuori = PAGINA.accorpaTutto(PAGINA.tokenizza(%s), %s).map(function (t) {
    var r = PAGINA.risolvi(t, %s, %s);
    return { testo: t, tradotto: r.testo, origine: r.origine };
  });
  console.log(JSON.stringify(fuori));
}
""" % (json.dumps(frase), json.dumps(direzione), json.dumps(frase),
       json.dumps(direzione),
       json.dumps(frase), json.dumps(direzione),
       json.dumps(direzione), json.dumps(frase))
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(programma)
        percorso = f.name
    try:
        esito = subprocess.run(["node", percorso], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(percorso)
    if esito.returncode != 0:
        raise SystemExit("node ha fallito su %r: %s" % (frase, esito.stderr.strip()[:400]))
    return json.loads(esito.stdout.strip().splitlines()[-1])


def risposta_python(motore: Motore, direzione: str, frase: str) -> list:
    risposta = motore.traduci(frase, direzione)
    return [{"testo": t, "tradotto": tr, "origine": o}
            for t, tr, o, _, _ in risposta.per_corrispondenza]


def main() -> int:
    if not shutil.which("node"):
        print("node non e' installato: il confronto delle due copie e' saltato.")
        print("Su GitHub gira, perche' ubuntu-latest ce l'ha.")
        return 0

    pagina = os.path.join(RADICE, "web", "index.html")
    if not os.path.exists(pagina):
        raise SystemExit("manca web/index.html: lancia `python3 -m traduttore.cli web`")
    testo_pagina = open(pagina, encoding="utf-8").read()
    script = estrae_script(testo_pagina)
    dati = estrae_dati(testo_pagina)

    glossario = Glossario.da_file(PERCORSI["glossario"])
    corpus = Corpus.da_file(PERCORSI["coppie"], PERCORSI["proverbi"])
    regole = []
    if os.path.exists(PERCORSI["regole"]):
        grezzo = json.load(open(PERCORSI["regole"], encoding="utf-8"))
        regole = grezzo.get("regole", [])
    varieta = Varieta.da_file(PERCORSI["varieta"])
    motore = Motore(glossario, corpus, regole)

    problemi = 0
    for direzione, frase in FRASI:
        atteso = risposta_python(motore, direzione, frase)
        try:
            trovato = risposta_js(script, dati, direzione, frase)
        except SystemExit:
            raise
        if atteso != trovato:
            problemi += 1
            print("DIVERGENZA su %r (%s)" % (frase, direzione))
            print("  python: %s" % json.dumps(atteso, ensure_ascii=False))
            print("  pagina: %s" % json.dumps(trovato, ensure_ascii=False))

    print("%d frasi confrontate, %d divergenze" % (len(FRASI), problemi))
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())