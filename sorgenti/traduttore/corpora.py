"""Le coppie parallele e i proverbi: le frasi, non le parole.

Una parola isolata non si traduce bene in nessuna lingua. «Il gatto dorme
sotto il tavolo» e «dormir» sono due problemi diversi, e il secondo si
risolve con il glossario mentre il primo no.

Il corpus parallelo serve a tre cose, in ordine di importanza:

1. dare al traduttore un contesto reale da cui copiare la struttura;
2. misurare quanto il motore sbaglia (corpus di valutazione);
3. estrarre le regole morfologiche, perche' una regola imparata da
   venti esempi verificati e' un fatto, mentre una regola scritta a mano e'
   un'opinione.

**Ogni coppia porta la sua provenienza.** Una coppia senza fonte non entra
nel motore: entra nella cartella `da_verificare/`, dove non puo' fare
danno. Questa e' la differenza fra un motore che impara e uno che indovina.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from . import normalizza
from .glossario import IT_FE
from .varieta import codice_valido

# I tipi di coppia, in ordine di utilita' per il motore.
# `conversazione`  frasi parlate, le piu' vicine all'uso del gioco
# `narrativa`      racconti, proverbi sciolti
# `poesia`         rime metriche, utili per il ritmo ma con parole alte
# `attestato`      voce di dizionario con frase d'esempio
# `gioco`          frasi scritte per «I cinque duchi», dichiarate tali
TIPI = ("conversazione", "narrativa", "poesia", "attestato", "gioco")


@dataclass
class Coppia:
    """Una frase nelle due lingue, con la sua provenienza."""

    id: str
    italiano: str
    ferrarese: str
    tipo: str = "conversazione"
    # `varieta` come nel glossario, e con la stessa regola: una frase
    # raccolta a Bondeno non e' una frase di Ferrara citta'. Il controllo C7
    # lo chiede anche per le coppie, perche' una frase senza varieta' si
    # propaga nel gioco insieme al suo contesto.
    varieta: str = ""
    fonte: str = ""
    # `nota` dice perche' la coppia c'e'. Alcune frasi si mettono in corpora
    # perche' esercitano una costruzione, non perche' sono tipiche.
    nota: str = ""
    # `attendibilita` come nel glossario.
    attendibilita: str = "M"
    # `ricorrenze`: quante volte la frase appare in testi raccolti. Serve a
    # pesare una coppia: una frase che si trova una volta sola non e' una
    # regola, e' unhappened.
    ricorrenze: int = 1

    def varieta_valida(self) -> bool:
        return codice_valido(self.varieta)

    def valida(self) -> bool:
        """Una coppia entra nel motore solo se ha due lati e una fonte."""
        return bool(self.ferrarese.strip() and self.italiano.strip() and self.fonte.strip())

    def chiave_ferrarese(self) -> str:
        return normalizza.chiave(self.ferrarese)

    def chiave_italiano(self) -> str:
        return normalizza.chiave(self.italiano)


@dataclass
class Proverbio:
    """Un proverbio: due forme, due registri, due parti.

    Il proverbio e' la voce piu' interessante e la piu' insidiosa: e'
    pronunziabile, e'-bel bisso, e la forma letteraria non coincide quasi
    mai con quella parlata. Per questo ha due campi e non uno.
    """

    id: str
    italiano: str
    ferrarese: str
    # `letterario` e' la forma dei libri, `popolare` quella che si dice.
    letterario: str = ""
    popolare: str = ""
    fonte: str = ""
    # `significato` quando i due lati non coincidono letteralmente. E' il
    # caso normale, non l'eccezione.
    significato: str = ""
    attendibilita: str = "M"


class Corpus:
    """Coppie e proverbi indicizzati."""

    def __init__(self, coppie=None, proverbi=None):
        self.coppie = list(coppie or [])
        self.proverbi = list(proverbi or [])
        self._per_ferrarese = {}
        self._per_italiano = {}
        self.indizza()

    @classmethod
    def da_file(cls, coppie_path: str = None, proverbi_path: str = None) -> "Corpus":
        coppie = []
        proverbi = []
        if coppie_path and os.path.exists(coppie_path):
            coppie = _leggi_jsonl(coppie_path, _coppia_da_dict)
        if proverbi_path and os.path.exists(proverbi_path):
            proverbi = _leggi_jsonl(proverbi_path, _proverbio_da_dict)
        return cls(coppie, proverbi)

    def indizza(self) -> None:
        self._per_ferrarese = {}
        self._per_italiano = {}
        for coppia in self.coppie:
            for lato, indice in (
                (coppia.chiave_ferrarese(), self._per_ferrarese),
                (coppia.chiave_italiano(), self._per_italiano),
            ):
                if lato:
                    indice.setdefault(lato, []).append(coppia)

    def __len__(self) -> int:
        return len(self.coppie)

    def coppie_valide(self) -> list:
        return [c for c in self.coppie if c.valida()]

    def cerca(self, frase: str, direzione: str = IT_FE, soglia: float = 0.80,
              limite: int = 5) -> list:
        """Coppie che somigliano a questa frase.

        Il ritorno e' una lista di coppie con `somiglianza`, dalla piu'
        somigliante alla meno. Una frase che non ha riscontro arriva come
        lista vuota: il motore allora non usa il corpus, e lo dice.
        """
        indice = self._per_italiano if direzione == IT_FE else self._per_ferrarese
        k = normalizza.chiave(frase)
        risultati = []
        if not k:
            return risultati
        for k_coppia, coppie in indice.items():
            if k_coppia == k:
                punteggio = 1.0
            else:
                punteggio = normalizza.somiglianza(k, k_coppia)
            if punteggio >= soglia:
                for coppia in coppie:
                    risultati.append((punteggio, coppia))
        risultati.sort(key=lambda p: (-p[0], -p[1].ricorrenze, p[1].id))
        return risultati[:limite]

    def corrispondenze(self, frase: str, direzione: str = IT_FE, soglia: float = 0.55,
                       limite: int = 12) -> list:
        """Coppie in cui almeno un lato assomiglia alla frase data.

        Serve a trovare il «come si dice *questa* parola in ferrarese»
        dentro un testo, non una frase intera. La soglia e' piu' bassa perche'
        il confronto e' su un pezzo, e ogni coppia porta il pezzo che ha
        combaciato, perche' il motore ha bisogno di vedere il contesto.
        """
        k = normalizza.chiave(frase)
        risultati = []
        if not k:
            return risultati
        for coppia in self.coppie:
            if not coppia.valida():
                continue
            lato = coppia.italiano if direzione == IT_FE else coppia.ferrarese
            punteggio = max(
                normalizza.somiglianza(k, t) for t in normalizza.tokenizza_chiave(lato)
            ) if normalizza.tokenizza_chiave(lato) else 0.0
            if punteggio >= soglia:
                risultati.append((punteggio, coppia))
        risultati.sort(key=lambda p: (-p[0], p[1].id))
        return risultati[:limite]

    def per_id(self, identificatore: str):
        for coppia in self.coppie:
            if coppia.id == identificatore:
                return coppia
        return None

    def cerca_proverbio(self, frase: str, direzione: str = IT_FE,
                        soglia: float = 0.62) -> list:
        """Proverbi in cui un pezzo di un lato somiglia alla frase data.

        Dal lato italiano si cerca solo nel glossato italiano. Dal lato
        ferrarese si cercano tutte e tre le forme, perche' tutte e tre sono
        ferraresi: `ferrarese` e' la forma unica quando c'e' una sola,
        `letterario` e' quella dei libri, `popolare` quella che si dice — e le
        due ultime non coincidono quasi mai. Mettere `letterario` dalla parte
        italiana faceva trovare «magnàr» nel proverbio *lupo non mangia di
        lupo*, perche' l'unico pezzo che combaciava era «magna» della forma
        ferrarese.

        Il confronto e' a **finestre**, non sul testo intero: nessuno cerca
        «non tutte le ciambelle» e si aspetta di ricevere la traduzione
        ferrarese di un proverbio italiano di quindici parole. Si prende la
        finestra di parole che meglio combacia con quello che e' stato
        scritto, che e' anche quello che fa una persona che sfoglia
        l'elenco. Il ritorno e' (punteggio, proverbio, pezzo), dalla piu'
        somigliante alla meno.
        """
        k = normalizza.chiave(frase)
        risultati = []
        if not k:
            return risultati
        for proverbio in self.proverbi:
            if direzione == IT_FE:
                lati = [proverbio.italiano]
            else:
                lati = [proverbio.ferrarese, proverbio.letterario,
                        proverbio.popolare]
            punteggio, pezzo = 0.0, ""
            for lato in lati:
                if not lato:
                    continue
                p, t = _migliora_finestra(k, lato)
                if p > punteggio:
                    punteggio, pezzo = p, t
            if punteggio >= soglia:
                risultati.append((punteggio, proverbio, pezzo))
        risultati.sort(key=lambda p: (-p[0], p[1].id))
        return risultati

    def frase_gemella(self, frase: str, direzione: str = IT_FE):
        """La coppia che contiene la frase data, per esteso.

        E' il caso piu' forte del livello 2: quando la frase c'e' tutta, si
        restituisce tutta. Non richiede nessuna soglia perche' il confronto e'
        un'identita'.
        """
        k = normalizza.chiave(frase)
        if not k:
            return None
        indice = self._per_italiano if direzione == IT_FE else self._per_ferrarese
        coppie = indice.get(k, [])
        return coppie[0] if coppie else None

    def frammento(self, coppia: Coppia, parola: str, direzione: str = IT_FE,
                  soglia: float = 0.75):
        """Il pezzo della coppia che corrisponde a `parola`.

        E' la parte difficile del livello 2, e la parte in cui un traduttore
        sbaglia piu' spesso: data la coppia «non c'e' pane» / «an ghe brisa
        pan», la parola «non» **non** ha un corrispondente in quella frase. In
        ferrarese la negazione e' dentro `an` e dentro `brisa`, e nessuna delle
        due e' `non`. Un motore che risponde «an ghe brisa pan» a «non» ha
        tradotto la frase, non la parola, e l'ha tradotta per intero tre volte
        quando capitava in una frase lunga.

        Per questo il ritorno e' il **singolo frammento** che combacia, e
        quando nessun frammento arriva alla soglia il metodo restituisce
        `None`: la coppia resta disponibile come esempio, ma non come
        traduzione. La soglia e' piu' alta di quella di `corrispondenze` perche'
        qui non si confronta una frase con una frase, ma una parola con una
        parola, e il contesto che di solito aiuta qui manca del tutto.
        """
        k = normalizza.chiave(parola)
        if not k:
            return None
        lato = coppia.ferrarese if direzione == IT_FE else coppia.italiano
        migliore = (0.0, None)
        for token in normalizza.tokenizza(lato):
            punteggio = normalizza.somiglianza(k, token)
            if punteggio > migliore[0]:
                migliore = (punteggio, token)
        if migliore[1] is None or migliore[0] < soglia:
            return None
        return migliore[1], migliore[0]


def _migliora_finestra(k: str, testo: str, parole_max: int = 12):
    """La sequenza di parole di `testo` che meglio combacia con `k`.

    Torna `(punteggio, pezzo)`. Il confronto parte dalla finestra piu' lunga
    e scende: una finestra lunga che combacia dice «e' questo proverbio», una
    finestra corta che combacia dice solo «c'e' una parola in comune», e il
    progetto non confonde le due cose.
    """
    token = normalizza.tokenizza(testo)
    migliore = (0.0, "")
    for quante in range(min(parole_max, len(token)), 0, -1):
        for inizio in range(0, len(token) - quante + 1):
            pezzo = " ".join(token[inizio:inizio + quante])
            punteggio = normalizza.somiglianza(k, normalizza.chiave(pezzo))
            if punteggio > migliore[0]:
                migliore = (punteggio, pezzo)
        if migliore[0] >= 1.0:
            break
    return migliore


def _leggi_jsonl(percorso: str, costruttore):
    elementi = []
    with open(percorso, "r", encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.startswith("//"):
                elementi.append(costruttore(json.loads(riga)))
    return elementi


def _coppia_da_dict(grezzo: dict) -> Coppia:
    return Coppia(
        id=str(grezzo.get("id", "")).strip(),
        italiano=str(grezzo.get("italiano", "")).strip(),
        ferrarese=str(grezzo.get("ferrarese", "")).strip(),
        tipo=str(grezzo.get("tipo", "conversazione") or "conversazione").strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        fonte=str(grezzo.get("fonte", "") or "").strip(),
        nota=str(grezzo.get("nota", "") or "").strip(),
        attendibilita=str(grezzo.get("attendibilita", "M") or "M").strip().upper()[:1],
        ricorrenze=int(grezzo.get("ricorrenze", 1) or 1),
    )


def _proverbio_da_dict(grezzo: dict) -> Proverbio:
    return Proverbio(
        id=str(grezzo.get("id", "")).strip(),
        italiano=str(grezzo.get("italiano", "")).strip(),
        ferrarese=str(grezzo.get("ferrarese", "") or "").strip(),
        letterario=str(grezzo.get("letterario", "") or "").strip(),
        popolare=str(grezzo.get("popolare", "") or "").strip(),
        fonte=str(grezzo.get("fonte", "") or "").strip(),
        significato=str(grezzo.get("significato", "") or "").strip(),
        attendibilita=str(grezzo.get("attendibilita", "M") or "M").strip().upper()[:1],
    )