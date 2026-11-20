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
            "irregolari": {}, "negazione": {}, "domande": {},
            "pronomi_atoni": {}}
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
        dati["negazione"] = grezzo.get("negazione") or {}
        dati["pronomi_atoni"] = grezzo.get("pronomi_atoni") or {}
        for r in grezzo.get("domande", []):
            dati["domande"].setdefault(r["italiano"], []).append(r)
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
        return riga["ferrarese"], "%s di %s (%s)" % (
            riga["categoria"], riga.get("fonte", "S015"), riga["dove"])
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


# --- i nomi propri (0.50) -----------------------------------------------------
#
# «mi chiamo Luca» usciva `a lùsa`, «vado a Ferrara» `a ferrara`: il motore
# riduce tutto in minuscolo e cerca nel glossario anche i nomi. Una parola che
# nella frase italiana comincia con la maiuscola e **non** e' la prima di una
# frase e' un nome proprio: resta com'e', con la sua maiuscola.

_PAROLA = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")


def nomi_propri(testo: str) -> dict:
    """{parola in minuscolo: parola come e' scritta} dei nomi propri."""
    propri = {}
    for m in _PAROLA.finditer(testo or ""):
        parola = m.group(0)
        if not parola[:1].isupper():
            continue
        prima = testo[:m.start()].rstrip()
        if not prima or prima[-1] in ".!?":
            continue
        propri[parola.lower()] = parola
    return propri


# --- la negazione e la domanda diretta (0.53, S027) ----------------------------
#
# Biolcati, «Lèzar e scrìvar» (1980), pag. 142-144: «non» e' «an», che si fonde
# con la particella soggetto del verbo («mi an», «ti t'an», «lu al n'», «lór i
# n'»), e «di solito» vuole «brisa» o un'altra parola negativa; fra i due «s'in-
# terpone una sola voce verbale, anche se questa e' un tempo composto». Pag.
# 104-105: nella domanda la particella va dopo il verbo («Ti at jé bón» → «Jét
# bón?»). Le due regole lavorano sulle unita' gia' tradotte, dopo il secondo
# passaggio, e si leggono in `dati/grammatica.json` (`negazione`, `domande`).

ORIGINI_VERBO = ("verbo", "analogia")
# La confidenza di un buco, come `ORIGINE["nessuna"]` in `motore.py`.
ORIGINE_BUCO = 0.0
_PRONOMI_DOMANDA = {"io": ("1sing", ""), "tu": ("2sing", ""),
                    "lui": ("3sing", "m"), "egli": ("3sing", "m"),
                    "lei": ("3sing", "f"), "ella": ("3sing", "f"),
                    "noi": ("1plur", ""), "voi": ("2plur", ""),
                    "loro": ("3plur", ""), "essi": ("3plur", ""),
                    "esse": ("3plur", "")}
_ACCENTO_APOSTROFO = {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù"}


def _parola_it(testo: str) -> str:
    """La parola italiana come chiave, con l'accento («e'» → «è»)."""
    t = _chiave(testo).strip(" .,;:!?«»\"")
    if len(t) > 1 and t.endswith("'") and t[-2] in _ACCENTO_APOSTROFO:
        t = t[:-2] + _ACCENTO_APOSTROFO[t[-2]]
    return t


def _proclitica(testo: str, tabella: dict):
    """(proclitica, resto) se la forma ferrarese comincia con una particella."""
    for p in sorted(tabella, key=len, reverse=True):
        if p.endswith("'"):
            if testo.startswith(p) and len(testo) > len(p):
                return p, testo[len(p):]
        elif testo.startswith(p + " "):
            return p, testo[len(p) + 1:]
    return None


def negazione(risultati: list, confidenza: float) -> list:
    """Il verbo con quello che gli sta davanti: «non» e i pronomi atoni.

    Per ogni verbo che porta la particella soggetto («a véd», «al dis»), si
    guarda indietro: un pronome atono italiano («lo», «mi», «si»...) e prima
    ancora «non». Il pronome prende la forma di S027 (pag. 94-97) secondo la
    particella e la lettera che segue; «non» diventa la particella negativa
    (pag. 142-144) e «brisa» va dopo il verbo, se la frase non ha gia' una
    parola negativa. Due pronomi di fila («me lo») restano come sono: la fonte
    li tabella a parte e il motore non li compone.
    """
    dati = carica()
    neg, atoni = dati["negazione"], dati["pronomi_atoni"]
    if not neg or not risultati:
        return risultati
    forme = (atoni or {}).get("forme", {})
    particelle = (atoni or {}).get("particelle", {})
    parole = [w for testo, *_ in risultati for w in _parola_it(testo).split()]
    gia_negativa = any(w in neg["parole_negative"] for w in parole)
    nuovi = list(risultati)
    for j, (v_testo, v_tradotto, v_origine, v_conf, v_dettaglio) in \
            enumerate(risultati):
        if v_origine not in ORIGINI_VERBO:
            continue
        k = j - 1
        pronome = None
        if k >= 0 and _parola_it(risultati[k][0]) in forme:
            pronome, k = k, k - 1
        if k >= 0 and _parola_it(risultati[k][0]) in forme:
            continue
        nega = k >= 0 and _parola_it(risultati[k][0]) == "non"
        if pronome is None and not nega:
            continue
        trovata = _proclitica(v_tradotto, neg["proclitiche"])
        if trovata is None:
            continue
        particella, verbo = trovata
        dettagli = []
        if pronome is not None:
            f = forme[_parola_it(risultati[pronome][0])]
            ctx = "voc" if contesto(verbo) == "vocale" else "cons"
            if not nega and particella in ("a", "aj"):
                atono = f["a_" + ctx]
            elif nega:
                atono = f["dopo_" + ctx]
            else:
                atono = particelle.get(particella, particella) + " " + \
                    f["dopo_" + ctx]
            pezzi = atono.split()
            if len(pezzi) == 2 and pezzi[0] == pezzi[1]:
                # «nessuno lo sa» dava `nissùn al al sa` (0.56): la tabella
                # applicata a una combinazione che la fonte non scrive. Negli
                # esempi di pag. 94-97 il pronome segue la particella «a» («Mi
                # al véd») o e' diverso da lei («Lu al m'dis»): la particella
                # ripetuta non c'e', e non si indovina. Resta un buco.
                nuovi[pronome] = (
                    risultati[pronome][0], risultati[pronome][0], "nessuna",
                    ORIGINE_BUCO, "pronome atono con la particella «%s» del "
                    "verbo: %s (%s) non scrive questa combinazione, e la "
                    "tabella darebbe «%s»" % (particella, atoni["fonte"],
                                              atoni["dove"], atono))
                # La particella resta al verbo: senza pronome e' sua.
                verbo = v_tradotto
            else:
                nuovi[pronome] = (risultati[pronome][0], atono, "grammatica",
                                  confidenza, "pronome atono di %s (%s), con "
                                  "la particella «%s» del verbo: «%s»"
                                  % (atoni["fonte"], atoni["dove"], particella,
                                     atono))
                dettagli.append("pronome")
        if nega:
            seguente = nuovi[pronome][1] if pronome is not None else verbo
            ctx = "vocale" if contesto(seguente) == "vocale" else "consonante"
            forma = neg["proclitiche"][particella][ctx]
            dettaglio = ("negazione di %s (%s): la particella «%s» del verbo "
                         "diventa «%s»" % (neg["fonte"], neg["dove"],
                                            particella, forma))
            if not gia_negativa:
                verbo = verbo + " " + neg["brisa"]
                dettaglio += ", e «%s» va dopo il verbo" % neg["brisa"]
            nuovi[k] = (risultati[k][0], forma, "grammatica", confidenza,
                        dettaglio)
        nuovi[j] = (v_testo, verbo, v_origine, v_conf, v_dettaglio)
    return nuovi


def domanda(risultati: list, testo: str, confidenza: float) -> list:
    """Una domanda diretta: il verbo prende la forma interrogativa attestata.

    Solo le forme che la fonte scrive (`domande`), e solo quando la persona e'
    certa: dal pronome italiano che precede, o perche' la parola italiana ha
    una persona sola. «sono» senza pronome (io o loro?) resta com'e'. Una
    domanda negativa resta com'e': la fonte non ne da' la regola.
    """
    domande = carica()["domande"]
    if not domande or not (testo or "").rstrip().endswith("?"):
        return risultati
    if any(_parola_it(t) == "non" for t, *_ in risultati):
        return risultati
    nuovi = list(risultati)
    for j, (t, _, _, _, _) in enumerate(risultati):
        righe = domande.get(_parola_it(t))
        if not righe:
            continue
        persona, genere = _PRONOMI_DOMANDA.get(
            _parola_it(risultati[j - 1][0]) if j else "", ("", ""))
        scelte = [r for r in righe if not persona or r["persona"] == persona]
        if not persona and len({r["persona"] for r in scelte}) > 1:
            return risultati
        if genere:
            scelte = [r for r in scelte if r["genere"] in (genere, "")] or scelte
        else:
            scelte = [r for r in scelte if r["genere"] != "f"] or scelte
        if not scelte:
            return risultati
        r = scelte[0]
        nuovi[j] = (t, r["ferrarese"], "grammatica", confidenza,
                    "domanda di %s (%s): la particella va dopo il verbo, "
                    "«%s»" % (r["fonte"], r["dove"], r["scritto_dalla_fonte"]))
        return nuovi
    return risultati
