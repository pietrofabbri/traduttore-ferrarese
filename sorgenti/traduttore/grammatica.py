# -*- coding: utf-8 -*-
"""La grammatica di S015 nel motore: articoli, pronomi, numeri, e il contesto.

**Il problema che risolve.** Una parola funzionale ferrarese dipende dalla
parola che la segue: «il cane» e' `al can`, «l'uomo» e' `l'òm` (S015, §4
«Articoli»). Il motore traduce da sinistra a destra, quindi quando arriva
all'articolo la parola ferrarese che segue non c'e' ancora. Guardare la parola
**italiana** che segue funziona quasi sempre, ma non sempre: S015 stesso scrive
che il prefisso latino *re-* in ferrarese diventa *ar-* (`ardùšar`), e
«il ritorno» comincia per consonante in italiano e per vocale in ferrarese.

Percio' il motore fa **due passaggi** (0.41): nel primo traduce tutte le parole
e da' all'articolo una forma provvisoria; nel secondo, quando la parola
ferrarese che segue e' gia' scritta, sceglie l'articolo — e le regole di frase
delle correzioni — guardando **lei**. Se la parola che segue non ha traduzione,
si guarda quella italiana, che e' l'unica che c'e'.

**Gli altri due indizi, dichiarati.**

- «le», «gli», «lo», «la», «l'» davanti a un **verbo** non sono articoli ma
  pronomi («le dico», «lo vedo»): se la parola che segue e' una forma verbale
  che le fonti coniugano, l'articolo non si applica;
- «due» e «tre» hanno maschile e femminile (`du`/`dó`, `tri`/`tré`): il genere
  lo dice la desinenza della parola italiana che segue, -e per il femminile
  plurale («due case»), -i per il maschile («due cani»). E' grammatica
  dell'italiano, non un dato del ferrarese; senza desinenza utile resta il
  maschile, e il dettaglio lo dice.

La copia nella pagina e' in `modello.html` (`grammaticaPrimo`,
`secondoPassaggio`, `separaElisioni`, `unisci`), e il confronto fra le due e'
`prove/controlla_equivalenza.py`.
"""
from __future__ import annotations

import io
import json
import os
import re

from . import grafia, normalizza

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "grammatica.json")
# Le vocali del ferrarese scritto. La «j» iniziale e' una semiconsonante
# (`jéra`, `jé`) e conta come consonante.
VOCALI = "aeiouàèéìíòóùú"
# Gli articoli che, davanti a un verbo, sono pronomi.
PRONOMI_ATONI = ("le", "gli", "lo", "la", "l'")
# Le elisioni italiane che il motore separa: «l'uomo» e' due parole, l'articolo
# e il nome, e il glossario conosce il nome.
ELISIONI = re.compile(r"^(l|un|quell|quest)['’](.+)$")

_cache = {}


def carica(percorso: str = None) -> dict:
    percorso = percorso or PERCORSO
    if percorso in _cache:
        return _cache[percorso]
    dati = {"articoli": {}, "parole": {}, "genere": {}, "plurali": [],
            "irregolari": {}}
    if os.path.exists(percorso):
        with io.open(percorso, encoding="utf-8") as f:
            grezzo = json.load(f)
        dati["articoli"] = {r["italiano"]: r for r in grezzo.get("articoli", [])}
        dati["parole"] = {r["italiano"]: r for r in grezzo.get("parole", [])}
        dati["genere"] = {r["italiano"]: r
                          for r in grezzo.get("secondo_genere", [])}
        dati["plurali"] = grezzo.get("plurali", [])
        dati["irregolari"] = {r["singolare"]: r
                              for r in grezzo.get("plurali_irregolari", [])}
    _cache[percorso] = dati
    return dati


def separa_elisioni(token: list) -> list:
    """«l'uomo» → «l'», «uomo»; «un'amica» → «un'», «amica»."""
    risultato = []
    for t in token:
        m = ELISIONI.match(t)
        if m:
            risultato.extend([m.group(1) + "'", m.group(2)])
        else:
            risultato.append(t)
    return risultato


def contesto(parola: str) -> str:
    """`vocale`, `consonante` o `fine`, dalla prima lettera della parola."""
    testo = normalizza.normale(parola or "").strip()
    if not testo:
        return "fine"
    return "vocale" if testo[0] in VOCALI else "consonante"


def genere(seguente_italiano: str) -> str:
    t = normalizza.normale(seguente_italiano or "").strip()
    if t.endswith("e"):
        return "f"
    return "m"


def _chiave(parola: str) -> str:
    return normalizza.normale(parola or "").replace("’", "'")


def e_articolo(parola: str, seguente_italiano: str, e_verbo) -> bool:
    """La parola e' un articolo qui? Non lo e' davanti a una forma verbale."""
    k = _chiave(parola)
    if k not in carica()["articoli"]:
        return False
    if k in PRONOMI_ATONI and seguente_italiano and e_verbo(seguente_italiano):
        return False
    return True


def articolo(parola: str, ctx: str, seguente_italiano: str = ""):
    """La forma dell'articolo nel contesto, o None se la fonte non la dice.

    Un caso a parte: «l'» italiano davanti a una parola che in ferrarese
    comincia per consonante («l'arancia» → `naràŋz`). In italiano non succede e
    la fonte non lo dice; il genere lo da' la desinenza italiana (-a femminile,
    -o maschile) e l'articolo diventa quello di «la» o di «il». Senza una
    desinenza utile la risposta e' None, e resta la scelta del primo passaggio.
    """
    articoli = carica()["articoli"]
    riga = articoli.get(_chiave(parola))
    if riga is None:
        return None
    if _chiave(parola) == "l'" and ctx != "vocale":
        fine = normalizza.normale(seguente_italiano or "").strip()[-1:]
        riga = articoli.get({"a": "la", "o": "il"}.get(fine, ""))
        if riga is None:
            return None
    forma = riga["vocale"] if ctx == "vocale" else riga["consonante"]
    if not forma:
        return None
    return forma, ("articolo di %s (%s), davanti a %s: «%s»"
                   % (riga.get("fonte", "S015"), riga["dove"], ctx,
                      riga["scritto_dalla_fonte"]))


def parola_fissa(parola: str, seguente_italiano: str):
    """Pronomi, possessivi, dimostrativi, numeri, giorni, mesi."""
    dati = carica()
    k = _chiave(parola)
    riga = dati["parole"].get(k)
    if riga is not None:
        return riga["ferrarese"], "%s di S015 (%s)" % (riga["categoria"],
                                                       riga["dove"])
    riga = dati["genere"].get(k)
    if riga is not None:
        g = genere(seguente_italiano)
        return riga[g], ("numero di S015 (%s): %s, %s perche' la parola "
                         "italiana che segue %s" % (
                             riga["dove"], riga["scritto_dalla_fonte"],
                             "femminile" if g == "f" else "maschile",
                             "finisce in -e" if g == "f" else
                             "non finisce in -e"))
    return None


def unisci(parole: list) -> str:
    """Le parole tradotte in una frase, senza spazio dopo un'elisione."""
    testo = ""
    for p in parole:
        if not p:
            continue
        if testo and not testo.endswith("'"):
            testo += " "
        testo += p
    return testo


# --- i plurali (0.41) --------------------------------------------------------
#
# Una parola italiana che il glossario non ha puo' essere il plurale di una che
# ha: «case» di «casa», «amiche» di «amica», «uomini» di «uomo». Il motore cerca
# il singolare con la grammatica dell'italiano e fa il plurale ferrarese con le
# regole di S015 (`plurali` in `dati/grammatica.json`). La forma e' **ricavata**,
# non attestata: ha la sua origine, `plurale`, e una confidenza piu' bassa.

# Le preposizioni articolate e le altre parole che finiscono in -i o -e senza
# essere plurali di un nome: «nei» non e' il plurale di «neo».
NON_PLURALI = {
    "dei", "degli", "delle", "nei", "negli", "nelle", "ai", "agli", "alle",
    "dai", "dagli", "dalle", "sui", "sugli", "sulle", "coi", "cogli", "colle",
    "pei", "tra", "fra", "che", "se", "me", "te", "ce", "ne", "ci", "vi", "si",
    "mi", "ti", "li", "le", "gli", "i", "e", "poi", "lei", "lui", "noi", "voi",
    "costei", "colui", "qui", "lì", "là", "oggi", "ieri", "mai", "dove",
    "come", "sempre", "forse", "bene", "male", "pure", "fine", "sotto",
    "sopra", "dentro", "fuori", "dietro", "davanti", "mentre", "oltre",
}
# I plurali italiani irregolari: grammatica dell'italiano.
SINGOLARI_IRREGOLARI = {"uomini": "uomo", "buoi": "bue", "mogli": "moglie",
                        "dita": "dito", "uova": "uovo", "braccia": "braccio",
                        "ossa": "osso", "paia": "paio"}


def singolari(parola: str) -> list:
    """I singolari italiani possibili, nell'ordine in cui si provano."""
    w = normalizza.normale(parola or "").strip()
    if len(w) < 3 or w in NON_PLURALI or "'" in w:
        return []
    fuori = []
    if w in SINGOLARI_IRREGOLARI:
        fuori.append(SINGOLARI_IRREGOLARI[w])
    if w.endswith("hi"):
        fuori.append(w[:-2] + "o")            # laghi → lago, fuochi → fuoco
    if w.endswith("he"):
        fuori.append(w[:-2] + "a")            # amiche → amica
    if w.endswith("i"):
        fuori.extend([w[:-1] + "o", w[:-1] + "e", w[:-1] + "a"])
    if w.endswith("e"):
        fuori.append(w[:-1] + "a")            # case → casa
    visti, ordinati = set(), []
    for s in fuori:
        if s not in visti and s != w:
            visti.add(s)
            ordinati.append(s)
    return ordinati


def plurale_ferrarese(singolare: str):
    """Il plurale ferrarese di una forma singolare, e la regola che lo da'."""
    dati = carica()
    basso = normalizza.normale(singolare)
    irregolare = dati["irregolari"].get(basso)
    if irregolare is not None:
        forma = irregolare["plurale"]
        if singolare[:1].isupper():
            forma = forma[:1].upper() + forma[1:]
        return forma, irregolare
    # Una parola di una sillaba sola («ca», casa) o tronca («cà», «putìη») non
    # cambia al plurale: gli esempi di S015 sono tutti di due sillabe o piu', e
    # «le case» non e' `chi` (0.48).
    if len(re.findall(r"[aeiouàèéìíòóùú]+", basso)) < 2 or \
            basso[-1:] in "àèéìíòóùú":
        return singolare, None
    for regola in dati["plurali"]:
        fine = regola["fine"]
        if basso.endswith(fine) and len(basso) > len(fine):
            radice = singolare[:-len(fine)]
            # «putìna» → «putìnn», «madòna» → «madònn», ma «fràgula» →
            # «fràgul» (0.49, S011): si raddoppia se l'accento cade sull'ultima
            # sillaba della radice, scritto o (senza accento scritto) piana.
            if regola.get("raddoppia_finale") and \
                    radice[-1:].lower() in regola["raddoppia_finale"] and \
                    _tonica_in_fondo(radice):
                radice += radice[-1]
            # «amìga» → «amìgh»: la g resta dura (0.42, `grafia.giunta`).
            return grafia.giunta(radice, singolare[-len(fine):],
                                 regola["plurale"]), regola
    return singolare, None


def _tonica_in_fondo(radice: str) -> bool:
    gruppi = re.findall(r"[aeiouàèéìíòóùú]+", radice.lower())
    if not gruppi:
        return False
    if any(c in "àèéìíòóùú" for g in gruppi for c in g):
        return any(c in "àèéìíòóùú" for c in gruppi[-1])
    return True


def plurale(parola: str, glossario):
    """`(forma, dettaglio)` se la parola e' il plurale di una voce, o None."""
    for singolare in singolari(parola):
        voci = glossario.cerca_italiano(singolare)
        if not voci:
            continue
        voce = voci[0]
        forma = voce.principale("it-fe")
        if not forma or " " in forma.strip() or "," in forma:
            continue
        resa, regola = plurale_ferrarese(forma.strip())
        if regola is None:
            spiegazione = ("maschile con il plurale uguale al singolare "
                           "(S015, §4 «Sostantivi e aggettivi»)")
        else:
            spiegazione = "%s, %s: «%s»" % (regola.get("fonte", "S015"),
                                             regola["dove"],
                                              regola["scritto_dalla_fonte"])
        return resa, ("plurale di «%s» (%s %s), %s" % (
            singolare, voce.id, forma.strip(), spiegazione))
    return None
