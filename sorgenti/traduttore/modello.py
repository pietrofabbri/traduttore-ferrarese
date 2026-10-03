"""Il livello 4: un modello linguistico, se e solo se ce n'e' uno.

Il livello 4 e' quello per cui si paga una chiave, e per questa ragione e'
anche quello che va costruito con piu' cura. Tre regole, in quest'ordine:

1. **Il modello non e' una fonte.** Non entra mai nel glossario e non entra
   mai nel corpus. Quello che produce resta in `dati/proposte/`, dove puo'
   diventare una voce solo se una persona la guarda e la approva.
2. **Il modello non puo' rispondere da solo.** Riceve il contesto (le voci
   vicine, le coppie simili, le regole) e gli si chiede esplicitamente di
   dichiarare quando non sa. Una risposta senza `confidenza` non viene usata.
3. **Senza chiave non c'e' livello 4.** Il motore funziona lo stesso, e
   funziona peggio ma funziona: e' la condizione che rende il progetto
   utilizzabile in una classe senza rete e senza budget.

Il prompt segue la regola che vale in «I cinque duchi»: al modello si dice
che cosa non sa, non soltanto che cosa deve fare. Un modello a cui si
chiede solo di tradurre produce; a cui si dice «se non sei sicuro scrivi
`non_so`» produce molto meno, e molto meglio.
"""

from __future__ import annotations

import json
import os

# Il modello di default. Va cambiabile con la variabile d'ambiente
# TRADUTTORE_MODELO, perche' il default cambia nel tempo e un progetto che
# depende da un nome fisso si rompe quando quel nome muore.
MODELLO_PREDEFINITO = "claude-sonnet-5"

ISTRUZIONI = """Sei un traduttore dal ferrarese all'italiano e dall'italiano al ferrarese.

Il ferrarese e' una lingua parlata nella provincia di Ferrara, oggi in \
regressione forte. Non e' italiano con qualche parola cambiata: ha un lessico \
proprio, e la grammatica non coincide.

Ricevi quattro cose: la parola da tradurre, il contesto (frase in cui compare), \
alcune voci di glossario vicine, alcune frasi parallele vere. Sono le uniche cose \
che puoi usare come riferimento.

Regole, in ordine di importanza:

1. Se nel contesto c'e' una voce di glossario o una frase parallela che \
risponde, usa quella. Il glossario ha la precedenza su tutto.
2. Non inventare. Se la parola non e' nel contesto e non conosci una forma \
ferrarese attestata, rispondi con `non_so` e spiega perche' in una riga.
3. Una parola che conosci per ragioni tue ma che non e' attestata nel contesto \
va marcata con `?` davanti, e va detto che non e' attestata.
4. Non tradurre una parola funzionale con una parola funzionale diversa se \
cambia la frase. Il ferrarese ha parole funzionali che l'italiano non ha e \
viceversa: meglio lasciare la parola che sbagliare la funzione.
5. Restituisci solo JSON valido, senza testo attorno.

Schema della risposta:

{"traduzione": "..." oppure "non_so",
 "confidenza": numero fra 0 e 1,
 "dettaglio": "una riga: da dove viene la risposta, o perche' non sai",
 "sources": ["id delle voci o coppie usate, se usate"]}
"""


class ModelloAssente:
    """Il livello 4 quando non c'e'. Non solleva: semplicemente non esiste."""

    def disponibile(self) -> bool:
        return False

    def traduci(self, parola: str, direzione: str, contesto) -> dict:
        return {}


class ModelloAnthropic:
    """Il livello 4 vero, su API Anthropic.

    La chiave si legge da `ANTHROPIC_API_KEY`. Il client si importa pigrano,
    cosi' il progetto gira anche senza `anthropic` installato e senza chiave.
    """

    def __init__(self, chiave: str = None, modello: str = None):
        self.chiave = chiave or os.environ.get("ANTHROPIC_API_KEY", "")
        self.modello = modello or os.environ.get("TRADUTTORE_MODELO", MODELLO_PREDEFINITO)
        self._client = None

    def disponibile(self) -> bool:
        if not self.chiave:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def _ottieni_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.chiave)
        return self._client

    def traduci(self, parola: str, direzione: str, contesto) -> dict:
        if not self.disponibile():
            return {}
        richiesta = {
            "parola": parola,
            "direzione": direzione,
            "contesto": contesto,
        }
        messaggio = "\n\n".join([
            ISTRUZIONI,
            "Ora la richiesta, in JSON:\n" + json.dumps(richiesta, ensure_ascii=False),
        ])
        try:
            risposta = self._ottieni_client().messages.create(
                model=self.modello,
                max_tokens=512,
                system="Sei il traduttore ferrarese di «I cinque duchi». Rispondi solo in JSON.",
                messages=[{"role": "user", "content": messaggio}],
            )
        except Exception:  # noqa: BLE001
            # Un errore di rete o di quota non deve far cadere la traduzione:
            # si torna al livello 3, che e' quello verificato. Il guasto va
            # pero' dichiarato, non nascosto.
            return {"errore": "chiamata al modello fallita", "traduzione": "", "confidenza": 0}
        testo = "".join(
            blocco.text for blocco in risposta.content if getattr(blocco, "type", "") == "text"
        )
        return _leggi_json(testo)


def _leggi_json(testo: str) -> dict:
    """Legge il JSON che il modello ha risposto.

    Il modello mette volentieri il JSON dentro un blocco di codice o
    circondato da una riga di spiegazione. Si prova prima il testo intero,
    poi il contenuto fra i primi due graffe: e' tolleranza, non fiducia,
    perche' il JSON ottenuto cosi' passa comunque dai controlli dello schema.
    """
    testo = (testo or "").strip()
    for candidato in (testo, _fra_graffe(testo)):
        if not candidato:
            continue
        try:
            dato = json.loads(candidato)
        except ValueError:
            continue
        if isinstance(dato, dict) and ("traduzione" in dato or "non_so" in dato):
            return dato
    return {"errore": "risposta non e' JSON valido", "traduzione": "", "confidenza": 0}


def _fra_graffe(testo: str) -> str:
    inizio = testo.find("{")
    fine = testo.rfind("}")
    if inizio >= 0 and fine > inizio:
        return testo[inizio: fine + 1]
    return ""


def costruisci_modello(chiave: str = None, modello: str = None):
    """Restituisce il livello 4, o `ModelloAssente` se non e' possibile.

    Questa e' l'unico punto del progetto in cui si decide se esiste un
    livello IA. Tutto il resto lavora senza sapere se c'e'.
    """
    candidato = ModelloAnthropic(chiave, modello)
    return candidato if candidato.disponibile() else ModelloAssente()