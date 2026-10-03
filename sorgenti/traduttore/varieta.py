"""Le varieta' del ferrarese: cinque, non una.

Il ferrarese non e' una lingua sola. Dentro la provincia di Ferrara, e
oltre, la parlata cambia di paese in paese in modo che uno che parla il
dialetto cittadino e uno di Bondeno si capiscono senza fatica e non si
confondono: sono varieta' della stessa lingua, e sono due lingue diverse per
chi le insegna.

Ignorarlo e' il modo piu' economico di sbagliare tutto. Una voce senza
varieta' non e' una voce sbagliata: e' una voce che non dice a chi la sta
ascoltando se la puo' usare. Per questo `varieta` e' un campo **obbligatorio**
del glossario, non un commento, e la sua assenza e' un errore (controllo G8).

Le cinque varieta' e i loro territori vengono da una fonte dichiarata
(`dati/fonti.json`, S002, Wikipedia «Dialetto ferrarese», CC BY-SA 4.0). Il
file `dati/varieta.json` e' la copia di lavoro di quella fonte con le note di
lettura, e questo modulo lo carica senza diventare l'autorita': l'autorita'
resta il file dei dati, perche' se la fonte cambia il file cambia e non il
codice.

Sul territorio che si sovrappone: Fiscaglia, Ostellato, Occhiobello e Goro
compaiono in piu' di un gruppo nella fonte, e il modulo non finge di
risolvere il conflitto. Lo dichiara e basta, perche' un territorio che il
gruppo non sa dividere e' un fatto che va dichiarato, non corretto.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

# I cinque codici. Sono cinque e non si aggiungono altri: un elenco aperto
# diventa un elenco in cui «varieta' del ferrarese» finisce per voler dire
# qualunque cosa.
VARIETA = ("cittadino", "centrale", "occidentale", "orientale", "transpadano")

# Come si chiamano in italiano. Il codice resta breve e va bene nei dati e
# nelle etichette corte; il nome completo va nelle intestazioni.
NOMI = {
    "cittadino": "cittadino",
    "centrale": "centrale, detto anche arioso",
    "occidentale": "occidentale",
    "orientale": "orientale",
    "transpadano": "transpadano, ibrido col polesano",
}

# Gli stati che una varieta' puo' avere nel progetto. `vuota` non e' un
# difetto da nascondere: e' il buco dichiarato di cui il progetto vive.
STATO_BASE = "base"
STATO_VUOTA = "vuota"


@dataclass
class Varieta:
    """Le varieta' caricate da `dati/varieta.json`."""

    voci: list = field(default_factory=list)

    # --- costruzione -----------------------------------------------------

    @classmethod
    def da_file(cls, percorso: str) -> "Varieta":
        voci = []
        if percorso and os.path.exists(percorso):
            with open(percorso, "r", encoding="utf-8") as f:
                grezzo = json.load(f)
            voci = grezzo.get("varieta", [])
        return cls(voci)

    # --- interrogazioni --------------------------------------------------

    def __len__(self) -> int:
        return len(self.voci)

    def per_codice(self, codice: str):
        for v in self.voci:
            if v.get("codice") == codice:
                return v
        return None

    def nomi(self) -> dict:
        """Codice -> nome leggibile, con i codici mancanti dichiarati.

        Se il file dei dati non conosce un codice che il codice conosce, il
        nome resta quello del modulo e nessuno se ne accorge. Per questo qui
        si unisce il file al modulo, e non si usa solo il file.
        """
        nomi = dict(NOMI)
        for v in self.voci:
            if v.get("codice") in nomi and v.get("nome"):
                nomi[v["codice"]] = v["nome"]
        return nomi

    def territori(self, codice: str) -> list:
        v = self.per_codice(codice)
        return list(v.get("territori", [])) if v else []

    def fonte(self, codice: str) -> str:
        v = self.per_codice(codice)
        return (v or {}).get("fonte", "")

    def conteggi(self, glossario=None, coppie=None, audio=None) -> dict:
        """Quante voci ha ogni varieta'.

        Il risultato serve al pannello della pagina e al comando `varieta`,
        e serve a una cosa sola: far vedere che quattro varieta' su cinque
        sono ancora vuote. Un pannello che dice solo «tutte le voci» mente per
        omissione, perche' lascia credere che il glossario copra la varieta'
        del ragazzo che sta dall'altra parte della provincia.
        """
        conto = {c: {"glossario": 0, "coppie": 0, "audio": 0} for c in VARIETA}
        if glossario is not None:
            for voce in glossario.voci:
                if voce.varieta in conto:
                    conto[voce.varieta]["glossario"] += 1
        if coppie is not None:
            for coppia in coppie:
                if coppia.varieta in conto:
                    conto[coppia.varieta]["coppie"] += 1
        if audio is not None:
            for brano in audio:
                if brano.varieta in conto:
                    conto[brano.varieta]["audio"] += 1
        for codice, numeri in conto.items():
            numeri["totale"] = sum(numeri.values())
            numeri["stato"] = (STATO_VUOTA if numeri["totale"] == 0
                               else STATO_BASE)
        return conto

    def vuote(self, conteggi: dict = None, glossario=None, coppie=None,
              audio=None) -> list:
        """Le varieta' senza niente dentro, nell'ordine dei cinque codici.

        Restituiscono i codici, non i nomi: il nome e' per l'inchiostro, il
        codice e' per il codice. I dati si possono passare qui o dentro
        `conteggi`, ma **non si possono omettere**: chiamata senza dati, questa
        funzione direbbe che tutte e cinque le varieta' sono vuote, che e'
        la risposta piu' falsa che un pannello possa dare.
        """
        conteggi = (conteggi if conteggi is not None
                    else self.conteggi(glossario=glossario, coppie=coppie, audio=audio))
        return [c for c in VARIETA if conteggi.get(c, {}).get("totale", 0) == 0]

    def come_dict(self) -> dict:
        """La forma che va nella pagina web, senza perdere le note."""
        nomi = self.nomi()
        return {
            "codici": list(VARIETA),
            "nomi": nomi,
            "voci": [
                {
                    "codice": v.get("codice", ""),
                    "nome": nomi.get(v.get("codice", ""), v.get("codice", "")),
                    "territori": v.get("territori", []),
                    "descrizione": v.get("descrizione", ""),
                    "confine": v.get("confine", ""),
                    "fonte": v.get("fonte", ""),
                    "attendibilita": v.get("attendibilita", ""),
                    "nota": v.get("nota", ""),
                }
                for v in self.voci
            ],
        }


def codice_valido(codice: str) -> bool:
    return (codice or "") in VARIETA


def _nome_valido(nome: str) -> bool:
    """Il nome e' il codice con qualche parola in piu': non si inventa niente.

    La differenza e' che il codice e' un dato che si puo' controllare e il
    nome no: un nome nuovo si puo' aggiungere per quello che dice a chi
    legge la pagina, mentre un codice nuovo cambierebbe il significato di
    tutte le voci gia' scritte. Per questo il codice no e il nome si'.
    """
    testo = (nome or "").strip().lower()
    parole = [p.strip(",") for p in testo.replace("-", " ").split() if p.strip(",")]
    if not parole:
        return False
    # Il nome puo' portare il gentilizio davanti («ferrarese transpadano»),
    # un nome popolare accanto («centrale, detto anche arioso») o un vicino
    # geografico («orientale, che si fonde col comacchiese»).
    parole = [p for p in parole if p not in ("detto", "anche", "e", "che", "si",
                                              "ferrarese", "col", "con", "il")]
    if not parole:
        return False
    # La parola che decide e' la prima che conosciamo: e' quella che nomina la
    # varieta', il resto e' spiegazione.
    return parole[0] in NOMI