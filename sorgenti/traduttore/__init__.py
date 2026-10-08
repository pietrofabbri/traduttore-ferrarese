"""Il traduttore italiano <-> ferrarese di «I cinque duchi».

Un pacchetto piccolo e con una regola sola: **nessuna risposta senza fonte**.
Ogni traduzione che esce da qui porta da dove viene e quanto e' sicura, e
quando non sa qualcosa lo dichiara invece di riempire.
"""

__version__ = "0.34.0"

from .glossario import Glossario, Voce, IT_FE, FE_IT
from .corpora import Corpus, Coppia, Proverbio
from .varieta import Varieta, VARIETA
from .fonetica import Fonetica, Trascrizione
from .audio import Archivio, Brano
# I suoni generati stanno in un pacchetto a parte perche' hanno regole
# opposte a quelle dei brani: li' una riga senza consenso e' un errore
# gravissimo, qui una riga senza dubbio dichiarato lo e' ugualmente.
from .sintesi import Sintesi, Suono
from .morfologia import impara, applica, Regola
from .motore import Motore, Risposta
from .modello import costruisci_modello
from . import proposte

__all__ = [
    "Glossario", "Voce", "Corpus", "Coppia", "Proverbio",
    "Motore", "Risposta", "Regola", "impara", "applica",
    "costruisci_modello", "IT_FE", "FE_IT",
    # La varieta' non e' un dettaglio del glossario: e' parte della risposta, e
    # quindi parte di quello che questo pacchetto espone.
    "Varieta", "VARIETA", "Fonetica", "Trascrizione",
    "Archivio", "Brano",
    # I suoni generati sono esposti come quelli audio, perche' chi legge
    # il pacchetto li cerca con lo stesso nome. Sono la stessa cosa in
    # forma e non in significato, ed e' la distinzione che li tiene separati.
    "Sintesi", "Suono", "proposte",
]