#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le parole della grammatica di S015 entrano in `dati/grammatica.json`.

**Che cosa sono.** Le parole che il glossario non aveva quasi mai e che stanno
in ogni frase: gli articoli, i pronomi personali, i possessivi, i dimostrativi, i
numeri, i giorni e i mesi. S015 (Bigoni, «Il Ferrarese», §4 «Grammatica») le
tabella, e sono la risposta a gran parte del buco di `AGENTS.md` §6 punto 8:
«il cane è a casa» usciva con due buchi.

**Perché un file a parte e non il glossario.** Perché un articolo non è una
voce: «il» è `al` davanti a consonante e `l'` davanti a vocale (S015, §4
«Articoli»), e una voce del glossario è una parola sola, senza la parola che
segue. Il motore usa questo file in un **secondo passaggio**, quando la parola
ferrarese che segue è già tradotta (`grammatica.py`).

**Come entrano.** Come in `da_paradigmi.py`: ogni riga di questo file è una
citazione — la forma come la fonte la scrive, la sezione e la tabella — e la
forma passa nella grafia del progetto con `dati/conversione_bigoni.json`. La
forma della fonte resta in `forma_fonte`. Dove la fonte dà due forme («lié /
ela», «óŋdaš / óŋg») la prima è la forma principale e l'altra una variante.

**Che cosa resta fuori, e perché.**

- «loro» possessivo (`sò`): la stessa parola italiana è il pronome «loro»
  (`lór`), e una parola per volta non si distinguono. Entra il pronome, perché
  il possessivo «il loro» ha già l'articolo davanti e si traduce `al sò` solo
  quando qualcuno lo correggerà;
- l'articolo indeterminativo femminile davanti a vocale («un'amica»): la fonte
  dice che «una» si riduce a «na» e non dice niente davanti a vocale;
- le preposizioni articolate («del», «nel», «al»): la fonte non le tabella.

Uso:
    python3 raccolta/da_grammatica.py --prova
    python3 raccolta/da_grammatica.py
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))
sys.path.insert(0, os.path.join(RADICE, "raccolta"))

from da_paradigmi import _tabella, converti  # noqa: E402

USCITA = os.path.join(RADICE, "dati", "grammatica.json")
FONTE = "S015"

# Gli articoli: S015, §4 «Articoli». La forma davanti a consonante e quella
# davanti a vocale, e la frase della fonte da cui vengono.
ARTICOLI = [
    {"italiano": "il", "genere": "m", "numero": "s",
     "consonante": "al", "vocale": "l'",
     "scritto_dalla_fonte": "L'articolo determinativo singolare maschile è l "
     "che davanti a parola iniziante per consonante si vocalizza in al."},
    {"italiano": "lo", "genere": "m", "numero": "s",
     "consonante": "al", "vocale": "l'",
     "scritto_dalla_fonte": "L'articolo determinativo singolare maschile è l "
     "che davanti a parola iniziante per consonante si vocalizza in al."},
    {"italiano": "la", "genere": "f", "numero": "s",
     "consonante": "la", "vocale": "l'",
     "scritto_dalla_fonte": "L'articolo determinativo singolare femminile è la "
     "con elisione davanti a parola iniziante per vocale."},
    # «l'» davanti a una parola ferrarese che comincia per consonante («l'arancia»
    # → `naràŋz`): la fonte non lo dice, perche' in italiano non succede. Il
    # motore sceglie «il» o «la» dalla desinenza italiana (vedi grammatica.py).
    {"italiano": "l'", "genere": "", "numero": "s",
     "consonante": "", "vocale": "l'",
     "scritto_dalla_fonte": "l'òman = l'uomo; l'amìɣa = l'amica"},
    {"italiano": "i", "genere": "m", "numero": "p",
     "consonante": "i", "vocale": "j",
     "scritto_dalla_fonte": "Il plurale è i davanti a consonante, j davanti a "
     "vocale."},
    {"italiano": "gli", "genere": "m", "numero": "p",
     "consonante": "i", "vocale": "j",
     "scritto_dalla_fonte": "Il plurale è i davanti a consonante, j davanti a "
     "vocale. ... j òman = gli uomini."},
    {"italiano": "le", "genere": "f", "numero": "p",
     "consonante": "il", "vocale": "j",
     "scritto_dalla_fonte": "Il plurale è il davanti a consonante, j davanti a "
     "vocale. ... il kavàli = le cavalle; ... j amìɣi = le amiche."},
    {"italiano": "un", "genere": "m", "numero": "s",
     "consonante": "un", "vocale": "n'",
     "scritto_dalla_fonte": "L'articolo indeterminativo singolare maschile è "
     "un spesso ridotto semplicemente a n davanti a vocale. Esempi: un can = un "
     "cane, n'àrbul = un albero."},
    {"italiano": "uno", "genere": "m", "numero": "s",
     "consonante": "un", "vocale": "n'",
     "scritto_dalla_fonte": "L'articolo indeterminativo singolare maschile è "
     "un spesso ridotto semplicemente a n davanti a vocale."},
    {"italiano": "una", "genere": "f", "numero": "s",
     "consonante": "na", "vocale": "",
     "scritto_dalla_fonte": "L'articolo indeterminativo singolare femminile è "
     "una spesso ridotto semplicemente a na."},
]

# Le parole che non cambiano con la parola che segue: (italiano, forma della
# fonte, categoria, dove). Le forme sono scritte come le scrive la fonte.
PAROLE = [
    # §4 «Pronomi», tabella «Pronomi personali»
    ("io", "mi", "pronome personale", "Pronomi personali"),
    ("me", "mi", "pronome personale", "Pronomi personali"),
    ("tu", "ti", "pronome personale", "Pronomi personali"),
    ("lui", "lu", "pronome personale", "Pronomi personali"),
    ("lei", "lié / ela", "pronome personale", "Pronomi personali"),
    ("noi", "nu", "pronome personale", "Pronomi personali"),
    ("voi", "vu", "pronome personale", "Pronomi personali"),
    ("loro", "lór", "pronome personale", "Pronomi personali"),
    # §4 «Sostantivi e aggettivi», tabella «Aggettivi possessivi»
    ("mio", "mjé", "possessivo", "Aggettivi possessivi"),
    ("mia", "mjé", "possessivo", "Aggettivi possessivi"),
    ("miei", "mjé", "possessivo", "Aggettivi possessivi"),
    ("mie", "mjé", "possessivo", "Aggettivi possessivi"),
    ("tuo", "tò", "possessivo", "Aggettivi possessivi"),
    ("tua", "tò", "possessivo", "Aggettivi possessivi"),
    ("tuoi", "tò", "possessivo", "Aggettivi possessivi"),
    ("tue", "tò", "possessivo", "Aggettivi possessivi"),
    ("suo", "sò", "possessivo", "Aggettivi possessivi"),
    ("sua", "sò", "possessivo", "Aggettivi possessivi"),
    ("suoi", "sò", "possessivo", "Aggettivi possessivi"),
    ("sue", "sò", "possessivo", "Aggettivi possessivi"),
    ("nostro", "nòstar", "possessivo", "Aggettivi possessivi"),
    ("nostra", "nòstar", "possessivo", "Aggettivi possessivi"),
    ("nostri", "nòstar", "possessivo", "Aggettivi possessivi"),
    ("nostre", "nòstar", "possessivo", "Aggettivi possessivi"),
    ("vostro", "vòstar", "possessivo", "Aggettivi possessivi"),
    ("vostra", "vòstar", "possessivo", "Aggettivi possessivi"),
    ("vostri", "vòstar", "possessivo", "Aggettivi possessivi"),
    ("vostre", "vòstar", "possessivo", "Aggettivi possessivi"),
    # tabella «Aggettivi e pronomi dimostrativi»
    ("questo", "quést", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("questa", "quésta", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("questi", "quìsti", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("queste", "quésti", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("quello", "quél", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("quella", "quéla", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("quelli", "quéj", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    ("quelle", "quéli", "dimostrativo", "Aggettivi e pronomi dimostrativi"),
    # §4 «Numeri», tabella «Numeri» («uno, una» sono gli articoli sopra)
    ("quattro", "quàtar", "numero", "Numeri"),
    ("cinque", "ziŋk", "numero", "Numeri"),
    ("sei", "sjé", "numero", "Numeri"),
    ("sette", "sèt", "numero", "Numeri"),
    ("otto", "òt", "numero", "Numeri"),
    ("nove", "nóv", "numero", "Numeri"),
    ("dieci", "djéš", "numero", "Numeri"),
    ("undici", "óŋdaš / óŋg", "numero", "Numeri"),
    ("dodici", "dódaš / dóg", "numero", "Numeri"),
    ("tredici", "trédaš / trég", "numero", "Numeri"),
    ("quattordici", "quatòrdaš / quatòrg", "numero", "Numeri"),
    ("quindici", "quìŋdaš / quiŋg", "numero", "Numeri"),
    ("sedici", "sédaš / ség", "numero", "Numeri"),
    ("diciassette", "darsét", "numero", "Numeri"),
    ("diciotto", "darždòt / ždòt", "numero", "Numeri"),
    ("diciannove", "daržnóv / žnóv", "numero", "Numeri"),
    ("venti", "viŋt", "numero", "Numeri"),
    ("trenta", "tréŋta", "numero", "Numeri"),
    ("quaranta", "quaràŋta", "numero", "Numeri"),
    ("cinquanta", "ziŋquàŋta", "numero", "Numeri"),
    ("sessanta", "sàŋta", "numero", "Numeri"),
    ("settanta", "stàŋta", "numero", "Numeri"),
    ("ottanta", "utàŋta", "numero", "Numeri"),
    ("novanta", "nuvàŋta", "numero", "Numeri"),
    ("cento", "zéŋt", "numero", "Numeri"),
    ("duecento", "dušéŋt", "numero", "Numeri"),
    ("trecento", "taršéŋt", "numero", "Numeri"),
    ("quattrocento", "quatarzéŋt", "numero", "Numeri"),
    ("cinquecento", "ziŋkzéŋt", "numero", "Numeri"),
    ("seicento", "sjêzéŋt", "numero", "Numeri"),
    ("settecento", "sětzéŋt", "numero", "Numeri"),
    ("ottocento", "ǒtzéŋt", "numero", "Numeri"),
    ("novecento", "nôvzéŋt", "numero", "Numeri"),
    ("mille", "mil", "numero", "Numeri"),
    ("duemila", "dômìla", "numero", "Numeri"),
    # §4 «Giorni e mesi»
    ("lunedì", "lùni", "giorno", "Giorni"),
    ("martedì", "màrti", "giorno", "Giorni"),
    ("mercoledì", "mèrkul", "giorno", "Giorni"),
    ("giovedì", "žòbja", "giorno", "Giorni"),
    ("venerdì", "vènar", "giorno", "Giorni"),
    ("sabato", "sàbat", "giorno", "Giorni"),
    ("domenica", "dméŋɣa", "giorno", "Giorni"),
    ("gennaio", "žnar", "mese", "Mesi"),
    ("febbraio", "favràr", "mese", "Mesi"),
    ("marzo", "marz", "mese", "Mesi"),
    ("aprile", "avrìl", "mese", "Mesi"),
    ("maggio", "mag", "mese", "Mesi"),
    ("giugno", "žuñ", "mese", "Mesi"),
    ("luglio", "lùj", "mese", "Mesi"),
    ("agosto", "aɣóst", "mese", "Mesi"),
    ("settembre", "sêtémbar", "mese", "Mesi"),
    ("ottobre", "utòbar", "mese", "Mesi"),
    ("novembre", "nuvémbar", "mese", "Mesi"),
    ("dicembre", "dicémbar", "mese", "Mesi"),
]

# I numeri che cambiano con il genere (S015: «I numeri cardinali per due e tre
# hanno maschile e femminile: du màsc, dó féman, tri màsc, tré féman»). Il
# genere lo dice la parola **italiana** che segue: un plurale in -e e'
# femminile («due case»), uno in -i maschile («due cani»).
SECONDO_GENERE = [
    {"italiano": "due", "m": "du", "f": "dó",
     "scritto_dalla_fonte": "du màsc, dó féman"},
    {"italiano": "tre", "m": "tri", "f": "tré",
     "scritto_dalla_fonte": "tri màsc, tré féman"},
]


# I plurali dei nomi e degli aggettivi: S015, §4 «Sostantivi e aggettivi». Ogni
# regola e' una desinenza del singolare ferrarese e quella del plurale; le
# desinenze sono scritte due volte, nella grafia della fonte e in quella del
# progetto, perche' il glossario le ha tutte e due (S006 scrive `-óŋ`, il Ferri
# `-ón`). Quello che nessuna regola tocca resta uguale: «I sostantivi e gli
# aggettivi maschili singolari ... hanno il plurale invariato».
PLURALI = [
    {"fine": "éš", "plurale": "ìš", "scritto_dalla_fonte":
     "un fraréš, du frarìš; un buluñéš, du buluñìš"},
    {"fine": "és", "plurale": "ìs", "scritto_dalla_fonte":
     "un fraréš, du frarìš (nella grafia del progetto)"},
    {"fine": "óŋ", "plurale": "ùŋ", "scritto_dalla_fonte":
     "un padrón, du padrùn; un pitón, du pitùn"},
    {"fine": "ón", "plurale": "ùn", "scritto_dalla_fonte":
     "un padrón, du padrùn; un pitón, du pitùn"},
    {"fine": "àl", "plurale": "àj", "scritto_dalla_fonte":
     "un kavàl, du kavàj; un grumbiàl, du grumbiàj"},
    {"fine": "èl", "plurale": "jé", "scritto_dalla_fonte":
     "un fradèl, du fradjé; un ušèl, du ušjé"},
    # Il femminile in -a: S015 scrive -i («dó putìni») ma aggiunge che «la i
    # finale risulta spesso molto evanescente e ... viene elisa». Dalla 0.49 la
    # regola e' quella del Tréb dal Tridèl (S011, S025, verificata dal titolare):
    # la -a cade, e la n o la l finale si raddoppia se l'accento cade
    # sull'ultima sillaba che resta. E' in PLURALI_S011, qui sotto.
]
PLURALI_S011 = [
    {"fine": "a", "plurale": "", "raddoppia_finale": ["n", "l"],
     "fonte": "S011", "dove": "«Scrìvar e lèźar al fraréś», Trascrizione dei "
     "vocaboli; S025, «Quali altri elementi caratterizzano»",
     "scritto_dalla_fonte": "si raddoppiano la L e la N finale solo nei "
     "femminili plurali con accento sull'ultima sillaba ... balìnn, putìnn, "
     "madònn ... ma biétul, fràgul, màśan; (S025) porta-port, fràgula-fràgul, "
     "frida-frid, scarpa-scarp, tumpèsta-tumpèst"},
]
# I plurali che la fonte scrive e che nessuna regola da'.
PLURALI_IRREGOLARI = [
    {"singolare": "òm", "plurale": "òman", "scritto_dalla_fonte":
     "un òm débul, du òman débul; l'òman = l'uomo; j òman = gli uomini"},
]


# Dalla 0.47: quello che «Scrìvar e lèźar al fraréś» (S011, Tréb dal Tridèl)
# aggiunge agli articoli di S015. Le forme sono gia' nella grafia del progetto
# (sono le stesse lettere). Una riga di qui con lo stesso italiano di una di
# S015 la sostituisce: «una» di S015 non dice la forma davanti a vocale, S011 si'.
ARTICOLI_S011 = [
    {"italiano": "di", "genere": "", "numero": "",
     "consonante": "ad", "vocale": "d'",
     "scritto_dalla_fonte": "la preposizione 'di', in ferrarese d (dal lat. de), "
     "che si appoggia alla parola seguente: d'èrba d'erba ... se la parola "
     "successiva cominci per consonante ... subentra davanti una a eufonica ... "
     "ad Gino di Gino, ad córsa di corsa."},
    {"italiano": "una", "genere": "f", "numero": "s",
     "consonante": "na", "vocale": "n'",
     "scritto_dalla_fonte": "il femminile una è praticamente sempre pronunciato "
     "na davanti a consonante (na scarpa una scarpa, na vòlta una volta) e "
     "davanti a vocale è n' (n'èrba un'erba, n'idèa un'idea)."},
    # «un'» italiano e' «una» elisa davanti a vocale
    {"italiano": "un'", "genere": "f", "numero": "s",
     "consonante": "na", "vocale": "n'",
     "scritto_dalla_fonte": "davanti a vocale è n' (n'èrba un'erba, n'idèa "
     "un'idea)."},
]
DOVE_S011 = "«Scrìvar e lèźar al fraréś», Osservazioni"


def costruisci() -> dict:
    tabella = _tabella()

    def resa(forma):
        return converti(forma, tabella)[0]

    parole = []
    for italiano, forma, categoria, tabella_fonte in PAROLE:
        forme = [f.strip() for f in forma.split("/")]
        riga = {"italiano": italiano, "ferrarese": resa(forme[0]),
                "forma_fonte": forme[0], "categoria": categoria,
                "dove": "§4, tabella «%s»" % tabella_fonte}
        if len(forme) > 1:
            riga["varianti"] = [resa(f) for f in forme[1:]]
        parole.append(riga)
    articoli = [dict(a, fonte=FONTE, dove="§4 «Articoli»") for a in ARTICOLI]
    sostituiti = {a["italiano"] for a in ARTICOLI_S011}
    articoli = [a for a in articoli if a["italiano"] not in sostituiti] + [
        dict(a, fonte="S011", dove=DOVE_S011) for a in ARTICOLI_S011]
    genere = [dict(g, m=resa(g["m"]), f=resa(g["f"]), fonte=FONTE,
                   dove="§4 «Sostantivi e aggettivi»") for g in SECONDO_GENERE]
    return {
        "_nota": "Le parole della grammatica di S015 (Bigoni, «Il Ferrarese», "
                 "§4): articoli, pronomi, possessivi, dimostrativi, numeri, "
                 "giorni e mesi. File GENERATO da raccolta/da_grammatica.py, "
                 "non si modifica a mano. Le forme sono nella grafia del "
                 "progetto (dati/conversione_bigoni.json); quella della fonte "
                 "e' in forma_fonte. Gli articoli dipendono dalla parola "
                 "ferrarese che segue: il motore li sceglie in un secondo "
                 "passaggio (sorgenti/traduttore/grammatica.py).",
        "fonte": FONTE,
        "articoli": articoli,
        "secondo_genere": genere,
        "parole": [dict(p, fonte=FONTE) for p in parole],
        "plurali": [dict(p, fonte=FONTE, dove="§4 «Sostantivi e aggettivi»")
                    for p in PLURALI] + PLURALI_S011,
        "plurali_irregolari": [dict(p, fonte=FONTE,
                                    dove="§4 «Sostantivi e aggettivi»")
                               for p in PLURALI_IRREGOLARI],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args()
    dati = costruisci()
    print("articoli %d, numeri con il genere %d, parole %d"
          % (len(dati["articoli"]), len(dati["secondo_genere"]),
             len(dati["parole"])))
    if args.prova:
        for p in dati["parole"][:12]:
            print("  %-10s %-10s %s" % (p["italiano"], p["ferrarese"],
                                        p["categoria"]))
        return 0
    with io.open(USCITA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("scritto %s" % os.path.relpath(USCITA, RADICE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
