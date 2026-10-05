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

**Quale pagina.** Il sito ha piu' pagine e il confronto legge
`web/traduttore.html`, che e' l'unica che porta il motore e il glossario
ridotto ai campi che il motore usa. Le altre pagine non hanno il codice da
confrontare: e' lo stesso codice, senza i dati che servono a esercitarlo. Il
confronto potrebbe passare su una pagina che non contiene niente, quindi il
test verifica anche che la pagina scelta abbia davvero il glossario dentro.

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

# L'unica pagina che porta il motore e i dati che il motore usa. Tutte le
# altre hanno lo stesso codice e meno dati, quindi confrontarle non
# significa niente: il confronto passa quando le due copie rispondono uguale,
# e rispondono tutte «non lo so» anche quando sono sbagliate.
PAGINA_CON_MOTORE = "traduttore.html"
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.cli import PERCORSI  # noqa: E402
from traduttore.corpora import Corpus  # noqa: E402
from traduttore.glossario import Glossario  # noqa: E402
from traduttore import italiano as analisi_italiana, morfologia, verbi
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
    # I proverbi: sono nell'indice dal lavoro sui proverbi, e il ramo della
    # frase intera ha una regola di confidenza che dipende dall'
    # attendibilita' della riga. Senza queste due frasi il confronto passava
    # senza mai guardare quel ramo, e la divergenza che c'era — la pagina
    # dava `corpo_frase` sempre, il motore solo per le righe `D` — sarebbe
    # tornata senza che nessuno se ne accorgesse.
    ("it-fe", "Se nevica sulla foglia, d'inverno non se n'ha voglia."),
    ("fe-it", "Se a neva in sla foia, d'inveran an s' na voia."),
    # E la frase del parlante nativo, che è la riga `D` per eccellenza: senza
    # di lei il confronto non guarderebbe la parte alta della scala.
    ("it-fe", "lei si siede"),
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


# Le regole che il confronto passa alle due copie. Non sono le regole del
# progetto: `dati/regole.json` e' vuoto, e un confronto che usa solo quello non
# controllerebbe niente del cancello, perche' il cancello agisce sulle regole e
# non ce ne sono. Sono regole dichiarate qui, con la classe che porta, e servono
# a una cosa sola: dire se le due copie applicano e rifiutano le stesse regole
# sugli stessi confronti.
REGOLE_DICHIARATE = [
    {"prefisso": "", "suffisso_italiano": "are", "suffisso_ferrarese": "ar",
     "classe": "verbo", "etichetta": "are > ar", "accordo": 1.0, "supporto": 4},
    {"prefisso": "", "suffisso_italiano": "e", "suffisso_ferrarese": "i",
     "classe": "nominale", "etichetta": "e > i", "accordo": 1.0, "supporto": 4},
    {"prefisso": "", "suffisso_italiano": "are", "suffisso_ferrarese": "ar",
     "classe": "", "etichetta": "are > ar, senza classe", "accordo": 1.0,
     "supporto": 4},
]

# Tre parole per ogni rifiuto possibile: una della classe della regola, una di
# una classe dichiarata diversa che **finisce come** la regola, e una che nessuna
# fonte dichiara. Il caso che conta e' il secondo: `campanare` finisce in `-are`
# come `mangiare`, e senza il cancello diventerebbe un verbo.
PAROLE = ["mangiare", "campanare", "cane", "cercare"]


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
           risolvi: risolvi, chiave: chiave, fraseGemella: fraseGemella,
           perRegola: perRegola, classeDi: classeDi };
"""
    return (INCOLLANCI % json.dumps(dati)) + "\n" + (
        "var PAGINA = (function () {" + dentro + porta + "})();")


def risposta_js(script: str, dati: str, direzione: str, frase: str) -> dict:
    """Il risultato della pagina, riga per riga."""
    # **Il ramo della frase intera passa da `risolvi`, non da `fraseGemella`.**
    # Prima il confronto riscriveva il ramo a mano — `g.fe`, `g.it`,
    # `origine: "corpo"` — quindi verificava una **ricostruzione** del codice
    # della pagina e non il codice: la regola della confidenza stava proprio
    # dentro quel ramo, e il confronto la saltava. E' la lezione che il progetto
    # ha gia' scritta due volte, per la normalizzazione: «le due copie devono
    # essere identiche» non basta, e qui si trattava di due copie *del confronto*.
    programma = apre_lo_script(script, dati) + """
function tonda(x) { return Math.round(x * 100) / 100; }
var g = PAGINA.risolvi(%s, %s, %s);
if (g.origine === "corpo" && PAGINA.fraseGemella(%s, %s)) {
  console.log(JSON.stringify([{ testo: %s, tradotto: g.testo,
                                origine: g.origine,
                                confidenza: tonda(g.confidenza) }]));
} else {
  var fuori = PAGINA.accorpaTutto(PAGINA.tokenizza(%s), %s).map(function (t) {
    var r = PAGINA.risolvi(t, %s, %s);
    return { testo: t, tradotto: r.testo, origine: r.origine,
             confidenza: tonda(r.confidenza) };
  });
  console.log(JSON.stringify(fuori));
}
""" % (json.dumps(frase), json.dumps(direzione), json.dumps(frase),
       json.dumps(frase), json.dumps(direzione), json.dumps(frase),
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
    # **La confidenza entra nel confronto.** Prima non c'era, e il confronto
    # passava verde anche quando le due copie davano numeri diversi sulla
    # stessa riga: verificava *che cosa* dicevano, non *quanto* lo dicevano con
    # sicurezza. Il difetto vero era nel ramo della frase intera — Python dava
    # `corpo` a una riga non documentata e `corpo_frase` a una documentata, la
    # pagina dava `corpo_frase` sempre — e nessuno dei due programmi si
    # sbagliava su che cosa rispondessero.
    #
    # Si arrotonda a due cifre perche' Python e JavaScript arrotondano i
    # decimali in modo diverso, e un confronto che fallisce sul quarto posto
    # decimale costringerebbe a riformulare il dato invece di correggere il
    # codice.
    return [{"testo": t, "tradotto": tr, "origine": o,
             "confidenza": round(c, 2)}
            for t, tr, o, c, _ in risposta.per_corrispondenza]


def regola_js(script: str, dati: str, parola: str, direzione: str) -> dict:
    """Che cosa fa la pagina di questa parola quando applica una regola.

    Le regole sono quelle dichiarate in questo file, non quelle del progetto: il
    confronto del cancello deve funzionare anche quando `dati/regole.json` e'
    vuoto, altrimenti confronterebbe due copie che non applicano niente e
    chiamerebbe quello un controllo.
    """
    dentro = json.loads(dati)
    dentro["regole"] = REGOLE_DICHIARATE
    programma = apre_lo_script(script, json.dumps(dentro, ensure_ascii=False)) + """
var r = PAGINA.perRegola(%s, %s);
console.log(JSON.stringify({ classe: PAGINA.classeDi(%s), testo: r ? r.testo : null }));
""" % (json.dumps(parola), json.dumps(direzione), json.dumps(parola))
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as f:
        f.write(programma)
        percorso = f.name
    try:
        esito = subprocess.run(["node", percorso], capture_output=True, text=True,
                               timeout=60)
    finally:
        os.unlink(percorso)
    if esito.returncode != 0:
        raise SystemExit("node ha fallito su %r: %s"
                         % (parola, esito.stderr.strip()[:400]))
    return json.loads(esito.stdout.strip().splitlines()[-1])


def regola_python(parola: str, direzione: str, analizzatore) -> dict:
    regole = []
    for riga in REGOLE_DICHIARATE:
        regola = morfologia.Regola(riga["prefisso"], riga["suffisso_italiano"],
                                   riga["suffisso_ferrarese"],
                                   riga["supporto"] * [{}])
        regola.classe = riga["classe"]
        regole.append(regola)
    analisi = analizzatore.analizza(parola)
    testo = morfologia.applica(parola, regole, direzione, analizzatore)
    return {"classe": analisi.classe if analisi.nota else "",
            "testo": None if testo == parola else testo}


def confronto_cancello(script: str, dati: str, analizzatore) -> int:
    """Le due copie applicano e rifiutano le stesse regole, parola per parola.

    Il difetto che questo confronto prende e' l'asimmetria fra le due copie: il
    motore in Python filtra le regole per classe, la pagina no. Le due rispondevano
    uguale solo perche' non c'e' nessuna regola da applicare — cioe' perche' il
    caso non esisteva, non perche' fosse giusto.
    """
    problemi = 0
    confronti = 0
    for direzione in ("it-fe", "fe-it"):
        for parola in PAROLE:
            confronti += 1
            atteso = regola_python(parola, direzione, analizzatore)
            trovato = regola_js(script, dati, parola, direzione)
            if atteso != trovato:
                problemi += 1
                print("DIVERGENZA DEL CANCELLO su %r (%s)" % (parola, direzione))
                print("  python: %s" % json.dumps(atteso, ensure_ascii=False))
                print("  pagina: %s" % json.dumps(trovato, ensure_ascii=False))
    print("%d confronti del cancello, %d divergenze" % (confronti, problemi))
    return problemi


def main() -> int:
    if not shutil.which("node"):
        print("node non e' installato: il confronto delle due copie e' saltato.")
        print("Su GitHub gira, perche' ubuntu-latest ce l'ha.")
        return 0

    pagina = os.path.join(RADICE, "web", PAGINA_CON_MOTORE)
    if not os.path.exists(pagina):
        raise SystemExit("manca web/%s: lancia `python3 -m traduttore.cli web`"
                         % PAGINA_CON_MOTORE)
    testo_pagina = open(pagina, encoding="utf-8").read()
    script = estrae_script(testo_pagina)
    dati = estrae_dati(testo_pagina)

    # Il confronto puo' passare su una pagina che non contiene niente: se il
    # glossario manca, il codice non trova una parola e risponde «non lo so»,
    # che e' una risposta legittima. Quindi si verifica che la pagina scelta
    # abbia davvero dentro il glossario, e che sia la forma compatta che il
    # codice sa leggere.
    dentro = json.loads(dati)
    serie = dentro.get("glossario")
    if not isinstance(serie, dict) or not serie.get("voci"):
        raise SystemExit("web/%s non contiene il glossario: il confronto "
                         "confronterebbe due motori che non sanno niente"
                         % PAGINA_CON_MOTORE)

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
    problemi += confronto_cancello(
        script, dati,
        analisi_italiana.Italiano.da_file(glossario=glossario,
                                          verbi=verbi.carica()))
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())