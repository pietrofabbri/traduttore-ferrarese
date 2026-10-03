"""Il traduttore italiano <-> ferrarese di «I cinque duchi».

Un pacchetto piccolo e con una regola sola: **nessuna risposta senza fonte**.
Ogni traduzione che esce da qui porta da dove viene e quanto e' sicura, e
quando non sa qualcosa lo dichiara invece di riempire.
"""

__version__ = "0.1.0"

from .glossario import Glossario, Voce, IT_FE, FE_IT
from .corpora import Corpus, Coppia, Proverbio
from .morfologia import impara, applica, Regola
from .motore import Motore, Risposta
from .modello import costruisci_modello

__all__ = [
    "Glossario", "Voce", "Corpus", "Coppia", "Proverbio",
    "Motore", "Risposta", "Regola", "impara", "applica",
    "costruisci_modello", "IT_FE", "FE_IT",
]