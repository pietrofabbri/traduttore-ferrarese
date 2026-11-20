# -*- coding: utf-8 -*-
"""La revisione: le domande per chi parla ferrarese, e le risposte proposte.

`dati/revisione/domande.json` contiene **solo l'italiano**: frasi, parole
frequenti, plurali, preposizioni, pronomi e verbi in tutti i tempi. La
traduzione proposta la calcola il motore quando si genera la pagina
(`per_la_pagina`), quindi la pagina `web/revisione.html` mostra sempre quello
che il traduttore risponde oggi, e non quello che rispondeva quando la domanda
e' stata scritta.

Le risposte non passano da qui: la pagina le manda come **correzioni**
(`dati/correzioni/`), una riga per risposta, con le stesse regole di quelle del
traduttore. Un «si'» e' una correzione uguale alla proposta (una conferma), un
«no» e' una correzione con la forma giusta, «non so» non manda niente.
"""
from __future__ import annotations

import io
import json
import os

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERCORSO = os.path.join(RADICE, "dati", "revisione", "domande.json")


def leggi(percorso: str = PERCORSO) -> dict:
    if not os.path.exists(percorso):
        return {"gruppi": []}
    with io.open(percorso, encoding="utf-8") as f:
        return json.load(f)


def proposta(motore, italiano: str) -> dict:
    """La traduzione di oggi, e se dentro c'e' una parola che il motore non sa."""
    from .motore import IT_FE
    risposta = motore.traduci(italiano, IT_FE)
    buchi = [testo for testo, _, origine, _, _ in risposta.per_corrispondenza
             if origine == "nessuna"]
    return {"proposta": risposta.testo, "buchi": buchi}


# Il gruppo delle letture dubbie (0.56). Le parole frequenti la cui risposta
# viene **solo** da una lettura OCR non verificata e non confermata (il Ferri e
# il Nannini), e la cui forma somiglia poco alla parola italiana. Non e' una
# prova che siano sbagliate: `zó` per «giù» e `dré` per «dietro» sono giuste e
# ci sono. E' il punto in cui un errore costa di piu' (una parola frequente
# sbagliata rovina ogni frase in cui compare) e in cui nessuna fonte trascritta
# a mano puo' fare da controllo: quindi lo si chiede prima. Il gruppo si
# calcola a ogni generazione della pagina e si svuota da solo: una conferma o
# una correzione promossa toglie la parola.
GRUPPI_FREQUENTI = ("parole", "parole700")
SOGLIA_DUBBIA = 0.6
CHIAVE_DUBBIE = "dubbie"


def lettura_dubbia(motore, italiano: str):
    """La voce OCR dubbia che risponde per `italiano` da sola, o None."""
    import difflib
    from . import glossario as G
    from .motore import IT_FE
    risposta = motore.traduci(italiano, IT_FE)
    if len(risposta.per_corrispondenza) != 1:
        return None
    _, tradotto, origine, _, dettaglio = risposta.per_corrispondenza[0]
    if origine != "glossario":
        return None
    voce = motore.glossario.per_id(dettaglio.split()[0])
    if voce is None or not G.letta_con_ocr(voce) or voce.conferme:
        return None
    somiglianza = difflib.SequenceMatcher(
        None, G.forma_confrontabile(tradotto),
        G.forma_confrontabile(italiano)).ratio()
    return voce if somiglianza < SOGLIA_DUBBIA else None


def gruppo_dubbie(motore, domande: dict) -> dict:
    """Le domande dei gruppi di parole frequenti che poggiano su una lettura
    dubbia, nell'ordine di frequenza. Gli id sono quelli delle domande: una
    risposta data qui vale anche nel gruppo da cui la domanda viene."""
    scelte = []
    for gruppo in domande.get("gruppi", []):
        if gruppo.get("chiave") not in GRUPPI_FREQUENTI:
            continue
        for d in gruppo.get("domande", []):
            voce = lettura_dubbia(motore, d["it"])
            if voce is not None:
                scelte.append(dict(d, tema="letto con l'OCR: %s, %s"
                                   % (voce.id, (voce.fonte or "")[:60])))
    return {"chiave": CHIAVE_DUBBIE, "titolo": "Le letture piu' dubbie",
            "spiegazione": ("Parole frequenti per cui il traduttore ha solo "
                            "una lettura automatica (OCR) di un vocabolario "
                            "antico, che nessuna altra fonte conferma e che "
                            "somiglia poco all'italiano. Alcune sono giuste, "
                            "altre sono righe del libro lette male: un «si'» "
                            "o una correzione qui valgono piu' che altrove."),
            "domande": scelte}


def per_la_pagina(motore, domande: dict = None) -> dict:
    """I gruppi con la proposta del motore accanto a ogni domanda."""
    domande = domande if domande is not None else leggi()
    gruppi = []
    sorgenti = list(domande.get("gruppi", []))
    dubbie = gruppo_dubbie(motore, domande)
    if dubbie["domande"]:
        sorgenti.insert(1, dubbie)
    for gruppo in sorgenti:
        righe = []
        for d in gruppo.get("domande", []):
            p = proposta(motore, d["it"])
            riga = {"id": d["id"], "it": d["it"], "p": p["proposta"]}
            if d.get("tema"):
                riga["t"] = d["tema"]
            if p["buchi"]:
                riga["b"] = p["buchi"]
            righe.append(riga)
        gruppi.append({"chiave": gruppo["chiave"], "titolo": gruppo["titolo"],
                       "spiegazione": gruppo.get("spiegazione", ""),
                       "domande": righe})
    return {"gruppi": gruppi}
