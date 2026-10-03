"""Le proposte del livello IA: la coda di revisione, e nient'altro.

Il livello 4 produce risposte che **non sono fonti**. Non entrano nel
glossario, non entrano nel corpus, non entrano nella pagina e non vengono
pubblicate. Quello che ne resta va in `dati/proposte/proposte.jsonl`: una riga
per risposta, in chiaro, in un file che chiunque puo' aprire e da cui
partono i due esiti possibili — una persona la verifica e ne fa una voce con
la fonte dichiarata, oppure la respinge.

Tre cose che questo modulo rende difficili per sbaglio:

1. **Una proposta non si dichiara documentata.** Non ha un campo `fonte` e non
   ha un campo `attendibilita`, e i controlli **M1** e **M2** falliscono se
   qualcuno glieli aggiunge. Il motivo e' che il passaggio da «il modello ha
   detto cosi'» a «la fonte dice cosi'» e' una decisione di una persona che ha
   aperto il libro, e se la riga lo dichiara da sola la decisione e' gia' stata
   presa senza guardare.
2. **Il file si appende, non si riscrive.** Quindi non si perde niente per
   errore e il file racconta la storia: si vede anche quello che il modello ha
   detto e che nessuno ha approvato, il che e' informazione.
3. **Le risposte `non_so` non si registrano.** Il motore le dichiara gia' come
   buchi, e registrarle riempirebbe la coda di noninformazione.

Il modulo non decide niente e non approva niente. Scrive, legge e controlla.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

# I tre esiti possibili di una proposta. Sono tre e non si aggiungono altri:
# una proposta o aspetta, o e' stata approvata, o e' stata respinta.
STATI = ("da rivedere", "approvata", "respinta")

# La riga che promuove una proposta: il glossario la porta nel campo `fonte`,
# e cosi' si sa da quale risposta del modello la voce e' venuta.
CAMPO_PROMOZIONE = "promossa_a"


@dataclass
class Proposta:
    """Una risposta del modello, in attesa di una persona."""

    parola: str
    traduzione: str
    direzione: str
    confidenza: float = 0.0
    data: str = ""
    dettaglio: str = ""
    # `fonti_citate` sono gli id che il modello ha detto di aver usato. Non sono
    # fonti della proposta: sono i punti di riferimento che lui ha citato, e
    # servono a capire se ha risposto davvero o se ha tirato a indovinare.
    fonti_citate: list = field(default_factory=list)
    stato: str = "da rivedere"
    promossa_a: str = ""
    # `grezzo` e' il dizionario originale. Serve ai controlli, che devono poter
    # vedere i campi che qualcuno ha aggiunto a mano: una riga con un campo
    # `fonte` non si vede guardando i campi noti.
    grezzo: dict = field(default_factory=dict)

    def come_dict(self) -> dict:
        return {
            "data": self.data,
            "direzione": self.direzione,
            "parola": self.parola,
            "traduzione": self.traduzione,
            "confidenza": round(self.confidenza, 3),
            "dettaglio": self.dettaglio,
            "fonti_citate": self.fonti_citate,
            "stato": self.stato,
            CAMPO_PROMOZIONE: self.promossa_a,
        }


def da_risposta(parola: str, direzione: str, risposta: dict,
                quando: str = "") -> Proposta:
    """Costruisce una proposta dalla risposta cruda del modello.

    Il nome del parametro e' `risposta` e non `modello`, perche' qui dentro non
    si sa cosa sia: arriva un dizionario, e il modulo non fa domande. Questo e'
    deliberato: se il giorno dopo il livello 4 smette di essere Anthropic e
    diventa qualcos'altro, questo file non si tocca.
    """
    return Proposta(
        parola=parola,
        traduzione=str(risposta.get("traduzione", "") or ""),
        direzione=direzione,
        confidenza=float(risposta.get("confidenza", 0.0) or 0.0),
        data=quando or _oggi(),
        dettaglio=str(risposta.get("dettaglio", "") or ""),
        fonti_citate=[str(s) for s in (risposta.get("sources") or [])],
        grezzo=dict(risposta),
    )


def salva(proposta: Proposta, percorso: str) -> None:
    """Aggiunge in fondo al file. Crea la cartella se non c'e'.

    Il parametro e' `percorso` e non `cartella`, perche' quello che si sa e' il
    file: il nome del file e' una convenzione del progetto e non va cambiato da
    un modulo.
    """
    cartella = os.path.dirname(percorso)
    if cartella:
        os.makedirs(cartella, exist_ok=True)
    with open(percorso, "a", encoding="utf-8") as f:
        f.write(json.dumps(proposta.come_dict(), ensure_ascii=False) + "\n")


def leggi(percorso: str) -> list:
    """Le proposte del file, nell'ordine in cui sono arrivate."""
    proposte = []
    if not percorso or not os.path.exists(percorso):
        return proposte
    with open(percorso, "r", encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("//"):
                continue
            grezzo = json.loads(riga)
            proposte.append(Proposta(
                parola=str(grezzo.get("parola", "")),
                traduzione=str(grezzo.get("traduzione", "")),
                direzione=str(grezzo.get("direzione", "")),
                confidenza=float(grezzo.get("confidenza", 0.0) or 0.0),
                data=str(grezzo.get("data", "")),
                dettaglio=str(grezzo.get("dettaglio", "")),
                fonti_citate=list(grezzo.get("fonti_citate", []) or []),
                stato=str(grezzo.get("stato", "") or ""),
                promossa_a=str(grezzo.get(CAMPO_PROMOZIONE, "") or ""),
                grezzo=grezzo,
            ))
    return proposte


def conta_stati(proposte: list) -> dict:
    """Quante proposte per stato. Il numero che si guarda in una revisione."""
    conto = {s: 0 for s in STATI}
    for p in proposte:
        conto[p.stato if p.stato in conto else "da rivedere"] += 1
    return conto


def _oggi() -> str:
    import datetime
    return datetime.date.today().isoformat()


def controlla_proposte(proposte: list, conosciute=None) -> list:
    """I controlli sulla coda di revisione.

    Sono quattro e sono tutti sui **metadati**, non sulla traduzione proposta:
    a questo progetto non interessa se la traduzione del modello e' bella,
    interessa che nessuno la faccia passare per una fonte.

    - **M1** la proposta ha uno stato fra i tre dichiarati;
    - **M2** la proposta **non ha un campo `fonte`** e **non si dichiara
      `D`**: e' il controllo che impedisce al livello 4 di diventare una fonte
      senza che nessuno lo decida;
    - **M3** gli id che il modello ha citato esistono davvero (avviso: il
      modello puo' citare una voce che non c'e', e allora vuol dire che ha
      risposto inventando);
    - **M4** una proposta dichiarata promossa punta a una voce che esiste
      (avviso: la promozione non e' ancora automatizzata, e se l'id non
      c'e' la voce non e' stata creata).
    """
    from .verifica_dati import Problema

    problemi = []
    for p in proposte:
        dove = "%s %s" % (p.data or "(senza data)", p.parola or "(senza parola)")
        if p.stato not in STATI:
            problemi.append(Problema(
                "M1", dove, "stato %r fuori dall'insieme %s"
                % (p.stato, ", ".join(STATI))))
        if p.grezzo.get("fonte"):
            problemi.append(Problema(
                "M2", dove,
                "la proposta ha un campo `fonte`: una risposta del modello non "
                "e' una fonte, e la fonte la dichiara una persona che ha aperto "
                "il libro"))
        if p.grezzo.get("attendibilita") == "D":
            problemi.append(Problema(
                "M2", dove,
                "la proposta si dichiara documentata: il livello 4 non puo' "
                "promuovere se stesso"))
        if not p.parola or not p.traduzione:
            problemi.append(Problema(
                "M1", dove, "proposta senza parola o senza traduzione"))
        if conosciute is not None:
            for citato in p.fonti_citate:
                if citato not in conosciute:
                    problemi.append(Problema(
                        "M3", dove,
                        "il modello ha citato %r, che non e' nel glossario ne' "
                        "nel corpus: vuol dire che ha risposto inventando"
                        % citato, gravita="avviso"))
        if p.promossa_a and conosciute is not None and p.promossa_a not in conosciute:
            problemi.append(Problema(
                "M4", dove,
                "dichiara di essere diventata %r, che non esiste nel glossario: "
                "la promozione non e' stata fatta" % p.promossa_a,
                gravita="avviso"))
    return problemi