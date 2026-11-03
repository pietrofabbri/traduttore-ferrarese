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
import unicodedata

from . import normalizza

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
