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


def per_la_pagina(motore, domande: dict = None) -> dict:
    """I gruppi con la proposta del motore accanto a ogni domanda."""
    domande = domande if domande is not None else leggi()
    gruppi = []
    for gruppo in domande.get("gruppi", []):
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
