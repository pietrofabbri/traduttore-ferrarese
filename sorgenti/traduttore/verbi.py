# -*- coding: utf-8 -*-
"""Le forme verbali attestate, e **nient'altro**.

**Perché questo modulo esiste e cosa rifiuta di fare.** Il traduttore non sa
coniugare e potrebbe sembrare che gli manchi il codice: gli manca il **paradigma**.
Nel repository non c'è una fonte che tabelli la coniugazione ferrarese, e un
coniugatore che la ricava dalle desinenze italiane produrrebbe forme ferraresi
che nessuno ha mai scritto. Il progetto non mette in `dati/` niente che non
sia in una fonte, quindi qui non si ricava niente.

Quindi `coniuga()` ha due possibili esiti e sono entrambi onesti: la forma che la
fonte scrive, oppure un **buco che dice quale parte manca**. Non c'è una terza
risposta, e non c'è un ripiego.

**Il buco è più utile del silenzio.** Uno studente che scrive «andammo» oggi
 riceve un trattino e non sa se il progetto non sa o se non c'è. Qui la risposta
è: il progetto ha 18 forme attestate su 12 verbi, questa casella non è fra
quelle, e le due fonti che parlano di verbi sono S015 e S001.

**Il clitico fa parte della chiave.** S015 dichiara (R036) che `avér` cambia
forma con la `ɣ`: «mi aj ò» e «mi a ɣ o» sono la stessa persona e lo stesso
tempo con due forme diverse. Una chiave che non tiene conto del clitico
restituirebbe una delle due per tutte e due le frasi.

Uso:

    from traduttore import verbi
    verbi.coniuga("aŋdàr", "1sing", "passato")
    # {'forma': 'andò', 'fonte': 'S001', ...}
    verbi.coniuga("aŋdàr", "2sing", "presente")
    # {'forma': '', 'problema': 'nessuna fonte documenta il 2sing presente'}
"""
from __future__ import annotations

import io
import json
import os
import re
import unicodedata

from . import grafia, normalizza

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "verbi.jsonl")

_cache = None


def _riga_sistema(testo: str) -> dict:
    """La riga `// SISTEMA` del file: il vocabolario del modulo."""
    for riga in testo.split("\n"):
        if riga.startswith("// SISTEMA"):
            return json.loads(riga[len("// SISTEMA"):].strip())
    return {}


def leggi(percorso: str = PERCORSO) -> tuple:
    """(sistema, righe). Il sistema e' vuoto se la riga non c'e'."""
    if not os.path.exists(percorso):
        return {}, []
    righe = []
    sistema = {}
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            if riga.startswith("// SISTEMA"):
                sistema = _riga_sistema(riga)
                continue
            if riga.startswith("//"):
                continue
            righe.append(json.loads(riga))
    return sistema, righe


def carica(percorso: str = PERCORSO) -> dict:
    """Il sistema e l'indice, una volta sola.

    L'indice e' su quattro chiavi — lemma, persona, tempo, clitico — e su un
    quinto, il lemma italiano, che serve al traduttore per la domanda che fa
    uno studente: «questa parola italiana e' una di quelle che le fonti
    coniugano?».
    """
    global _cache
    if _cache is not None and percorso == PERCORSO:
        return _cache
    sistema, righe = leggi(percorso)
    per_forma = {}
    per_italiano = {}
    for riga in righe:
        chiave = chiave_forma(riga["lemma"], riga["persona"], riga["tempo"],
                              riga.get("clitico", ""))
        per_forma.setdefault(chiave, []).append(riga)
        # Un omografo di una parola funzionale («dai», «sia») non si cerca:
        # il motore traduce parola per parola, e ogni «dai» diventerebbe un
        # verbo. La riga resta nel file, con il campo che lo dice.
        if riga.get("omografo"):
            continue
        k = chiave_italiano(riga.get("italiano") or "")
        if k:
            per_italiano.setdefault(k, []).append(riga)
    for k in per_italiano:
        per_italiano[k] = ordina(per_italiano[k], sistema)
    risultato = {"sistema": sistema, "righe": righe, "per_forma": per_forma,
                 "per_italiano": per_italiano}
    if percorso == PERCORSO:
        _cache = risultato
    return risultato


_ACCENTI_APOSTROFO = {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù"}


def chiave_italiano(parola: str) -> str:
    """La chiave di una parola italiana coniugata: **con** l'accento.

    `normalizza.chiave()` toglie gli accenti, e per i verbi e' sbagliato: «è» e
    «e», «dà» e «da» diventerebbero la stessa parola, e ogni congiunzione «e»
    si tradurrebbe `l'è`. Qui l'accento resta, e l'accento scritto con
    l'apostrofo («e'», «puo'», come lo scrive chi non ha la tastiera italiana)
    diventa l'accento grave. Una parola senza accento non trova la forma
    accentata, ed e' voluto: «da» non e' «dà».
    """
    testo = unicodedata.normalize("NFC", normalizza.normale(parola or ""))
    testo = testo.strip(" .,;:!?«»\"")
    if len(testo) > 1 and testo.endswith("'") and \
            testo[-2] in _ACCENTI_APOSTROFO:
        testo = testo[:-2] + _ACCENTI_APOSTROFO[testo[-2]]
    return testo


def ordina(righe: list, sistema: dict) -> list:
    """Le righe di una stessa parola italiana, dalla piu' probabile.

    Una parola italiana puo' essere piu' caselle: «canti» e' il presente e il
    congiuntivo, «sono» e' la prima singolare e la terza plurale. L'ordine e'
    dichiarato e non e' un'opinione sulla frase: il tempo nell'ordine della riga
    di sistema (l'indicativo presente per primo), poi la persona nello stesso
    modo, poi le righe con la proclitica (quelle dei paradigmi) prima delle
    forme sparse, poi la forma principale prima delle varianti.
    """
    tempi = list(sistema.get("tempi") or [])
    persone = list(sistema.get("persone") or [])

    def posto(valore, elenco):
        return elenco.index(valore) if valore in elenco else len(elenco)

    return sorted(righe, key=lambda r: (
        posto(r.get("tempo"), tempi), posto(r.get("persona"), persone),
        0 if r.get("proclitica") else 1, 1 if r.get("variante_di") else 0,
        r.get("id", "")))


# Il pronome soggetto italiano dice la persona del verbo che lo segue. Non e'
# un dato del ferrarese: e' la grammatica italiana, e serve solo a scegliere
# fra due caselle che la stessa parola italiana occupa («loro sono»).
PRONOMI_SOGGETTO = {
    "io": "1sing", "tu": "2sing", "lui": "3sing", "lei": "3sing",
    "egli": "3sing", "ella": "3sing", "esso": "3sing", "essa": "3sing",
    "noi": "1plur", "voi": "2plur", "loro": "3plur", "essi": "3plur",
    "esse": "3plur",
}


def accentata(parola: str) -> bool:
    """True se la parola italiana porta un accento (anche scritto con «'»)."""
    return any(unicodedata.combining(c) for c in
               unicodedata.normalize("NFD", chiave_italiano(parola)))


def prima_del_glossario(attestata: dict, parola: str, persona: str) -> bool:
    """La forma della tabella vince sul glossario? Solo in due casi dichiarati.

    Il glossario resta il primo livello, e una parola come «canto» o «sei» e'
    davvero anche un nome («cantòn», «sié»). Ma due indizi dicono che la parola
    e' il verbo:

    - un **pronome soggetto** della stessa persona subito prima («io canto»,
      «tu sei»): il pronome non sta davanti a un nome;
    - l'**accento**: il glossario si cerca senza accenti, quindi «è» vi trova le
      voci di «e»; la tabella di coniugazione scrive «è» esattamente cosi'.
    """
    if not attestata.get("forma"):
        return False
    if persona and attestata["riga"].get("persona") == persona:
        return True
    return accentata(parola)


def persona_del_soggetto(parola: str) -> str:
    """La persona che un pronome soggetto italiano annuncia, o ''."""
    return PRONOMI_SOGGETTO.get(normalizza.chiave(parola or ""), "")


def con_soggetto(riga: dict) -> str:
    """La forma come si dice in una frase: con la proclitica davanti.

    «a cant», «at cànti», «al cànta», e «l'è» senza spazio, perche' la fonte
    scrive attaccata la proclitica elisa. Una riga senza proclitica (le forme
    sparse, l'imperativo) esce com'e'.
    """
    forma = riga.get("forma", "")
    proclitica = riga.get("proclitica") or ""
    if not proclitica:
        return forma
    if proclitica.endswith("'"):
        return proclitica + forma
    return proclitica + " " + forma


def chiave_forma(lemma: str, persona: str, tempo: str, clitico: str = "") -> str:
    return "|".join([normalizza.chiave(lemma), persona, tempo,
                     normalizza.chiave(clitico or "")])


def _dichiara(problema: str) -> dict:
    """Il buco, nella stessa forma in cui lo restituisce ogni altra risposta."""
    return {"forma": "", "problema": problema, "fonte": "", "nota": ""}


def coniuga(lemma: str, persona: str, tempo: str,
            clitico: str = "", percorso: str = PERCORSO) -> dict:
    """La forma attestata, o il buco che dice che cosa manca.

    L'ordine dei controlli è dichiarato perché il buco nomini **la** cosa che
    manca, non la prima che capita: un lemma assente è un buco diverso da una
    persona non documentata, e per chi legge sono due lavori diversi.
    """
    dati = carica(percorso)
    sistema = dati["sistema"]
    persone = sistema.get("persone") or []
    tempi = sistema.get("tempi") or []
    if not sistema or not persone:
        return _dichiara("dati/verbi.jsonl non dichiara il sistema: senza la "
                         "riga SISTEMA non si sa che persone e tempi esistono")
    if tempo not in tempi:
        return _dichiara("«%s» non è fra i tempi dichiarati (%s)"
                         % (tempo, ", ".join(tempi)))
    if persona and persona not in persone:
        return _dichiara("«%s» non è fra le persone dichiarate (%s)"
                         % (persona, ", ".join(persone)))

    righe = dati["per_forma"].get(
        chiave_forma(lemma, persona, tempo, clitico))
    if righe:
        return {"forma": righe[0]["forma"], "problema": "",
                "fonte": "%s, %s" % (righe[0]["fonte"], righe[0]["dove"]),
                "nota": righe[0].get("nota", ""), "riga": righe[0]}

    # Lo stesso lemma e lo stesso tempo, con un'altra persona: la casella esiste
    # nella fonte ma non per chi si chiede. E' una notizia diversa da «il verbo
    # non c'è».
    dello_stesso_verbo = [r for r in dati["righe"]
                          if normalizza.chiave(r["lemma"]) ==
                          normalizza.chiave(lemma)
                          and r["tempo"] == tempo
                          and normalizza.chiave(r.get("clitico") or "") ==
                          normalizza.chiave(clitico or "")]
    if dello_stesso_verbo:
        hanno = ", ".join("%s %s" % (r["persona"] or "senza persona", r["forma"])
                          for r in dello_stesso_verbo)
        return _dichiara("nessuna fonte scrive %s %s di %s: della fonte si ha "
                         "solo %s" % (persona or "la forma senza persona",
                                      tempo, lemma, hanno))
    conosce = sorted({normalizza.chiave(r["lemma"]) for r in dati["righe"]})
    if normalizza.chiave(lemma) not in conosce:
        return _dichiara("il verbo %s non è fra i %d che le fonti coniugano "
                         "(%s)" % (lemma, len(conosce), ", ".join(conosce)))
    return _dichiara("nessuna fonte scrive %s %s di %s"
                     % (persona or "la forma senza persona", tempo, lemma))


def dall_italiano(parola: str, percorso: str = PERCORSO,
                  persona: str = "") -> dict:
    """Dalla parola **italiana** coniugata alla forma ferrarese attestata.

    Non e' il inverso di `coniuga()` e non pretende di esserlo: qui la parola
    italiana e' una di quelle che una fonte ha messo accanto alla forma
    ferrarese, quindi la risposta esiste per definizione. Se non c'e', la risposta
    e' il buco — e il buco non dice «non so tradurre» ma «questa forma non è
    fra quelle documentate», che è una cosa che si può correggere.

    `persona` e' quella che annuncia il pronome che precede («loro sono»): se
    una delle caselle della parola e' di quella persona, vince quella. `testo` e'
    la forma con la proclitica davanti, come si dice in una frase.
    """
    dati = carica(percorso)
    righe = dati["per_italiano"].get(chiave_italiano(parola))
    if not righe:
        quante = len(dati["per_italiano"])
        return {"forma": "", "testo": "", "problema": "nessuna fonte coniuga "
                "«%s»: le forme italiane documentate sono %d"
                % (parola, quante), "fonte": "", "nota": ""}
    scelta = righe[0]
    if persona:
        della_persona = [r for r in righe if r.get("persona") == persona]
        if della_persona:
            scelta = della_persona[0]
    return {"forma": scelta["forma"], "testo": con_soggetto(scelta),
            "problema": "",
            "fonte": "%s, %s" % (scelta["fonte"], scelta["dove"]),
            "nota": scelta.get("nota", ""), "riga": scelta}


def cosa_sa(percorso: str = PERCORSO) -> dict:
    """Il conto, per chi chiede al progetto quanto sa — e cosa non sa.

    `vuoto` è la parte importante: è la lista delle caselle che nessuna fonte
    documenta, presa dalla riga `SISTEMA` e non calcolata, perché il progetto
    non deduce un buco, lo dichiara.
    """
    dati = carica(percorso)
    sistema = dati["sistema"]
    verbi = sorted({r["lemma"] for r in dati["righe"]})
    return {
        "forme": len(dati["righe"]),
        "verbi": len(verbi),
        "lemmi": verbi,
        "persone": sistema.get("persone", []),
        "tempi": sistema.get("tempi", []),
        "vuoto": [tuple(v) for v in sistema.get("vuoto", [])],
        "citato_da": sistema.get("citato_da", []),
        "paradigmi": sistema.get("paradigmi", []),
    }


def spiega_buco(parola: str = "", percorso: str = PERCORSO) -> str:
    """La frase che va accanto ai buchi: corta, e con i numeri dentro.

    Il parametro `parola` **non** viene usato per accusare nessuno, e il
    motivo sta in un caso reale: i buchi di una traduzione sono parole che il
    motore non sa tradurre, e `il` o `di` sono due di quelle. Una frase che
    dicesse «questa parola non è una forma verbale attestata» sarebbe falsa
    per metà dei buchi, quindi la frase parla **del progetto** e non della
    parola: è vero in ogni caso, e il lettore fa il confronto da sé.
    """
    sa = cosa_sa(percorso)
    if not sa["forme"]:
        return ""
    return ("il progetto coniuga solo quello che le fonti scrivono: %d forme "
            "verbali di %d verbi, e per intero i %d verbi modello di S015 (%s). "
            "Una forma di un altro verbo resta un buco dichiarato, non una "
            "forma indovinata."
            % (sa["forme"], sa["verbi"], len(sa["paradigmi"]),
               ", ".join(sa["paradigmi"])))


# --- la coniugazione per analogia con i verbi modello (0.41) -----------------
#
# S015 coniuga per intero un verbo modello per ciascuna delle quattro
# coniugazioni (`kaŋtàr`, `tašér`, `lèžar`, `kapìr`) e dice che le coniugazioni
# regolari sono quattro (R035). Un verbo regolare che il glossario ha
# all'infinito si coniuga quindi sul modello della sua coniugazione. La forma e'
# **ricavata**, non attestata: ha l'origine `analogia` e una confidenza bassa.
#
# Il riconoscimento dell'italiano usa le desinenze italiane dei modelli (le
# righe `italiano` dei paradigmi). Le forme ferraresi si fanno cosi':
#
# - quando l'accento cade sulla **desinenza** (`magnén`, `magnàva`, `magnarò`)
#   la radice dell'infinito resta com'e' e la desinenza e' quella del modello;
# - quando cade sulla **radice** (`màgna`) la vocale accentata si sa per `a`,
#   `i`, `u`; se l'italiano ha *e* dove il ferrarese ha *a*, la tonica e' `é`
#   (S015: «zarkàr = cercare, nu a zarkéŋ ma mi a zérk»); se la vocale e' `e` o
#   `o` non si sa se e' aperta o chiusa, e la forma **non si fa**: resta un buco.

CLASSI = (
    # lemma della fonte, infinito italiano, desinenza italiana, desinenza ferrarese
    ("kaŋtàr", "cantare", "are", "àr"),
    ("tašér", "tacere", "ere", "ér"),
    ("lèžar", "leggere", "ere", "ar"),
    ("kapìr", "capire", "ire", "ìr"),
)
_VOCALI_IT = "aeiouàèéìòóù"


def _senza_accenti(testo: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", testo or "")
                   if not unicodedata.combining(c))


def modelli(percorso: str = PERCORSO) -> list:
    """Le celle dei verbi modello, ridotte a desinenze italiane e ferraresi.

    E' la tabella che usano il motore e la pagina (che la riceve nei dati): una
    copia sola del calcolo, in Python.
    """
    dati = carica(percorso)
    sistema = dati["sistema"]
    risultato = []
    for lemma_fonte, inf_it, fine_it, fine_fe in CLASSI:
        # Dalla 0.50 anche il participio (persona vuota): «kaŋtà», «tašù», «kapì».
        righe = [r for r in dati["righe"] if r.get("lemma_fonte") == lemma_fonte
                 and (r.get("persona") in ("1sing", "2sing", "3sing", "1plur",
                                           "2plur", "3plur")
                      or (r.get("tempo") == "participio" and not r.get("persona")))
                 and not r.get("variante_di") and not r.get("clitico")]
        if not righe:
            continue
        radice_it = inf_it[:-len(fine_it)]
        lemma = righe[0]["lemma"]
        radice_fe = _senza_accenti(lemma[:-len(fine_fe)].lower()) \
            if _senza_accenti(lemma.lower()).endswith(_senza_accenti(fine_fe)) \
            else ""
        celle = []
        for r in ordina(righe, sistema):
            italiano = r["italiano"]
            if not italiano.startswith(radice_it):
                continue
            desinenza_it = italiano[len(radice_it):]
            # Le forme irregolari dell'italiano («taccio», «tacciono») non
            # sono una desinenza: non si usano per riconoscere.
            if not desinenza_it or desinenza_it[0] not in _VOCALI_IT:
                continue
            forma = r["forma"].lower()
            if not _senza_accenti(forma).startswith(radice_fe):
                continue
            desinenza_fe = forma[len(radice_fe):]
            sulla_radice = not any(c in "àèéìíòóùú" for c in desinenza_fe)
            cella = {"tempo": r["tempo"], "persona": r["persona"],
                     "it": desinenza_it, "fe": desinenza_fe,
                     "radice": sulla_radice,
                     "proclitica": r.get("proclitica", ""),
                     "riga": r["id"]}
            celle.append(cella)
            celle.extend(_celle_derivate(cella))
        risultato.append({"lemma_fonte": lemma_fonte, "infinito": inf_it,
                          "fine_it": fine_it, "fine_fe": fine_fe,
                          "celle": celle})
    return risultato


def _celle_derivate(cella: dict) -> list:
    """Le altre desinenze italiane che portano alla stessa forma ferrarese (0.50).

    Non sono forme nuove del ferrarese: sono altri modi in cui l'**italiano**
    scrive la stessa casella, perche' il motore la riconosca.

    - il futuro e il condizionale sincopati: «andrò», «vedrò», «potrei» hanno la
      stessa casella di «canterò», «tacerò», senza la e;
    - il participio di «taciuto» si riconosce anche come -uto («creduto»), che e'
      la grafia dell'italiano e non un'altra desinenza;
    - il participio maschile plurale («cantati») ha la forma del singolare: in
      S015 nessuna regola del plurale tocca le parole tronche in -à, -ù, -ì, e
      «maschile con il plurale uguale al singolare» e' la sua regola generale.
    """
    it, tempo = cella["it"], cella["tempo"]
    altre = []
    if tempo in ("futuro", "condizionale") and it.startswith("er") and len(it) > 2:
        altre.append("r" + it[2:])
    if tempo == "participio":
        if it.startswith("iu"):
            altre.append(it[1:])
        for forma in [it] + list(altre):
            if forma.endswith("o"):
                altre.append(forma[:-1] + "i")
    return [dict(cella, it=a, derivata=True) for a in altre]


def _accentua(radice: str, radice_it: str):
    """La radice con l'accento sull'ultima vocale, e se e' un'alternanza.

    Torna `(radice, alternanza)` o None se non si sa quale vocale. La «i» di
    «mangi-are», «baci-are» e' grafia dell'italiano e non una vocale: si toglie
    prima di confrontare.
    """
    posizioni = [i for i, c in enumerate(radice.lower()) if c in "aeiou"]
    if not posizioni:
        return None
    i = posizioni[-1]
    vocale = radice[i].lower()
    base_it = radice_it.lower()
    if base_it.endswith(("ci", "gi", "sci")):
        base_it = base_it[:-1]
    vocali_it = [c for c in base_it if c in "aeiou"]
    vocale_it = vocali_it[-1] if vocali_it else ""
    if vocale == "a" and vocale_it == "e":
        return radice[:i] + "é" + radice[i + 1:], True
    if vocale == vocale_it and vocale in "aiu":
        nuova = {"a": "à", "i": "ì", "u": "ù"}[vocale]
        return radice[:i] + nuova + radice[i + 1:], False
    return None


def _sillabe(parola: str) -> int:
    return len(re.findall(r"[aeiouàèéìíòóùú]+", parola.lower()))


def per_analogia(parola: str, glossario, persona: str = "",
                 tabella: list = None) -> dict:
    """La forma di un verbo regolare, coniugato sul modello della sua classe."""
    w = chiave_italiano(parola)
    candidati = []
    for modello in (tabella if tabella is not None else modelli()):
        for cella in modello["celle"]:
            if not w.endswith(cella["it"]) or len(w) <= len(cella["it"]) + 1:
                continue
            radice_it = w[:-len(cella["it"])]
            # «mangi», «mangerò»: l'italiano toglie la i di -giare/-ciare
            # davanti a i ed e; «cerchi»: aggiunge la h di -care/-gare.
            prove = [radice_it]
            # «cerchiamo»: prima «cercare» (la h e' grafia dell'italiano), poi
            # «cerchiare», che e' un altro verbo (0.49).
            if radice_it.endswith(("ch", "gh")):
                prove.append(radice_it[:-1])
            if cella["it"][:1] in "ie":
                prove.append(radice_it + "i")
            for radice in prove:
                infinito = radice + modello["fine_it"]
                voci = glossario.cerca_italiano(infinito)
                if not voci:
                    continue
                forma = (voci[0].principale("it-fe") or "").strip()
                if " " in forma or "," in forma or not \
                        _senza_accenti(forma.lower()).endswith(
                            _senza_accenti(modello["fine_fe"])):
                    continue
                if modello["fine_fe"] == "ar" and forma.lower().endswith(
                        ("àr", "ár")):
                    continue
                candidati.append((modello, cella, radice, forma, voci[0]))
                break
    if not candidati:
        return {"forma": "", "testo": ""}
    if persona:
        della = [c for c in candidati if c[1]["persona"] == persona]
        candidati = della or candidati
    for modello, cella, radice_it, infinito_fe, voce in candidati:
        radice_fe = infinito_fe[:-len(modello["fine_fe"])]
        seguito = infinito_fe[len(radice_fe):]
        if cella["radice"] and modello["fine_fe"] != "ar":
            accentata = _accentua(radice_fe, radice_it)
            if accentata is None:
                continue
            radice_tonica, alternanza = accentata
            forma = grafia.giunta(radice_tonica, seguito,
                                  cella["fe"])
            # Una sillaba sola non porta l'accento («a magn», come «a kaŋt»),
            # tranne l'alternanza, che e' una vocale diversa («a zérk»).
            if _sillabe(forma) < 2 and not alternanza:
                forma = grafia.giunta(radice_fe, seguito,
                                      cella["fe"])
        else:
            # Nella terza coniugazione l'accento e' gia' sulla radice
            # dell'infinito («lèžar»), e la radice resta com'e'.
            # La c e la g si riscrivono per la vocale che segue (0.42):
            # «zarcàr» → «nu a zarchén».
            forma = grafia.giunta(radice_fe, seguito, cella["fe"])
        riga = {"forma": forma, "proclitica": cella["proclitica"],
                "persona": cella["persona"], "tempo": cella["tempo"]}
        return {"forma": forma, "testo": con_soggetto(riga),
                "fonte": "S015", "riga": riga,
                "nota": "per analogia con «%s» (%s, %s %s, riga %s): "
                        "infinito %s «%s» (%s)" % (
                            modello["lemma_fonte"], modello["infinito"],
                            cella["tempo"], cella["persona"], cella["riga"],
                            radice_it + modello["fine_it"], infinito_fe,
                            voce.id)}
    return {"forma": "", "testo": ""}
