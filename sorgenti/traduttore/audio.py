"""I brani audio: il manifesto, e la parte che non c'e'.

Il progetto ha un solo vincolo non negoziabile sull'audio, e non e' tecnico:
**nessun brano di una persona che non ha detto di si'**. Non «solo per
prova», non «solo nel repository privato». Una voce e' una persona, e il
consenso non e' una formalita' che si puo' dimenticare per una settimana.

Quindi `dati/audio.jsonl` non e' un elenco di file: e' un elenco di
**persone che hanno parlato e di che cosa hanno detto**. Un brano entra nel
manifesto quando la registrazione esiste, e entra nella pagina solo se ha il
consenso, la licenza e il consenso anche per la pubblicazione.

Le tre condizioni sono separate e servono tutte e tre:

- `consenso`: la persona ha detto di si'. Sta in `audio.jsonl`, non in un
  foglio sparso, perche' la domanda «questa voce si puo' pubblicare?» va
  poter rispondere senza dover cercare in giro.
- `licenza`: il file e' di chi puo' ridistribuirlo. Un brano registrato dalla
  scuola e' della scuola fino a prova contraria.
- `pubblicabile`: la decisione finale, che puo' essere `false` anche quando le
  altre due ci sono, e in quel caso resta `false` per sempre. Registrare
  qualcuno a casa sua non autorizza niente.

**Quello che c'e' adesso: niente.** Non un brano. Non un file in `audio/`.
Il riproduttore della pagina esiste, funziona, e dice che non ha niente da
far suonare. E' il modo piu' onesto di iniziare la parte audio, ed e'
l'opposto di quello che fanno i progetti che mettono una voce sintetica e
la chiamano «il ferrarese».

Il percorso che c'e', e che non e' breve:

1. il portale dei dialetti della Regione Emilia-Romagna (`dati/fonti.json`,
   S007) annuncia testi **e audio** di autori e autrici dei dialetti del
   territorio ferrarese, con Floriana Guidetti e «Storie dei nostri
   dialetti»: e' materiale di altre persone, e va chiesto il permesso con
   le sue modalita', non scaricato;
2. registrare qualche parlante, di ogni varieta' possibile, con il consenso
   per iscritto;
3. e solo allora i brani entrano nella pagina, con la varieta' dichiarata.

Il livello di lettibilita' (`lettibilita`) e' qui in latino perche' e' la sola
parola giusta: un brano con dentro `magnàr` due volte non e' un brano A1 solo
perche' e' breve.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .varieta import codice_valido

# I contesti dichiarati dal manifesto. Sono quattro e descrivono **che cosa
# stai ascoltando**, non la difficolta' della lingua: la difficolta' e' nel
# campo `lettibilita`, che e' il livello CEFR reale.
CONTESTI = ("racconto", "lettura", "dialogo", "lista di parole")

# I livelli CEFR ammessi. Qui la sigla e' quella ufficiale e non una
# metafora per «facile»: e' il motivo per cui il manifesto la scrive e non la
# deduce da una lunghezza.
LIVELLI = ("A1", "A2", "B1", "B2")

ESTENSIONI_ACCETTATE = (".mp3", ".ogg", ".m4a", ".oga", ".wav", ".webm")


@dataclass
class Brano:
    """Una registrazione, con la persona che ha parlato e il suo consenso."""

    id: str
    file: str = ""
    # `riferimento` collega il brano a una voce (V0001) o a una coppia
    # (F0001). Serve a una cosa sola: far suonare la parola giusta quando si
    # cerca una parola nel riproduttore. Un brano senza riferimento si
    # pubblica ma non si trova, e quindi non serve a nessuno.
    riferimento: str = ""
    testo: str = ""
    italiano: str = ""
    # `voce` e' come la persona si fa chiamare e come si vuole essere citata.
    # Non il nome del file, non l'etichetta del registratore.
    voce: str = ""
    luogo: str = ""
    varieta: str = ""
    contesto: str = ""
    licenza: str = ""
    consenso: str = ""
    pubblicabile: bool = False
    lettibilita: str = "A1"
    nota: str = ""
    # `durata` in secondi, se qualcuno lo ha misurato. Serve a non promettere
    # a uno studente un brano di quattro minuti che e' di quaranta secondi.
    durata: float = 0.0

    def publicabile(self) -> bool:
        """Le tre condizioni insieme. Il `pubblicabile` da solo non basta."""
        return bool(self.pubblicabile and self.consenso and self.licenza)

    def percorso(self, radice_audio: str) -> str:
        return os.path.join(radice_audio, self.file) if self.file else ""

    def esiste(self, radice_audio: str) -> bool:
        if not self.file:
            return False
        estensione = os.path.splitext(self.file)[1].lower()
        if estensione not in ESTENSIONI_ACCETTATE:
            return False
        return os.path.exists(self.percorso(radice_audio))

    def come_dict(self) -> dict:
        return {
            "id": self.id,
            "riferimento": self.riferimento,
            "file": self.file,
            "testo": self.testo,
            "italiano": self.italiano,
            "voce": self.voce,
            "luogo": self.luogo,
            "varieta": self.varieta,
            "contesto": self.contesto,
            "licenza": self.licenza,
            "consenso": self.consenso,
            "pubblicabile": self.publicabile(),
            "lettibilita": self.lettibilita,
            "nota": self.nota,
        }


@dataclass
class Archivio:
    """Il manifesto dei brani."""

    brani: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.brani)

    def __iter__(self):
        return iter(self.brani)

    @classmethod
    def da_file(cls, percorso: str) -> "Archivio":
        brani = []
        if percorso and os.path.exists(percorso):
            with open(percorso, "r", encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if riga and not riga.startswith("//"):
                        brani.append(_brano_da_dict(json.loads(riga)))
        return cls(brani)

    def pubblicabili(self) -> list:
        return [b for b in self.brani if b.publicabile()]

    def senza_consenso(self) -> list:
        """Brano presente ma non pubblicabile. Va saputo, non nascosto."""
        return [b for b in self.brani if not b.publicabile()]

    def per_id(self, identificatore: str):
        for b in self.brani:
            if b.id == identificatore:
                return b
        return None

    def stato(self, radice_audio: str) -> dict:
        """Che cosa c'e' davvero, in numeri, e che cosa manca.

        La differenza fra `brani` e `pronti` e' la parte importante: un
        brano registrato che non si puo' pubblicare e' un brano che il
        riproduttore non suona, e il riproduttore deve dirlo.
        """
        pronti = [b for b in self.brani
                  if b.publicabile() and b.esiste(radice_audio)]
        return {
            "brani": len(self.brani),
            "pubblicabili": len(self.pubblicabili()),
            "pronti": len(pronti),
            "da_verificare": len(self.senza_consenso()),
            "varieta": sorted({b.varieta for b in self.brani if b.varieta}),
        }


def _brano_da_dict(grezzo: dict) -> Brano:
    pubblicabile = grezzo.get("pubblicabile", False)
    if isinstance(pubblicabile, str):
        pubblicabile = pubblicabile.strip().lower() in ("1", "true", "si", "sì")
    durata = grezzo.get("durata", 0.0) or 0.0
    try:
        durata = float(durata)
    except (TypeError, ValueError):
        durata = 0.0
    return Brano(
        id=str(grezzo.get("id", "")).strip(),
        riferimento=str(grezzo.get("riferimento", "") or "").strip(),
        file=str(grezzo.get("file", "") or "").strip(),
        testo=str(grezzo.get("testo", "") or "").strip(),
        italiano=str(grezzo.get("italiano", "") or "").strip(),
        voce=str(grezzo.get("voce", "") or "").strip(),
        luogo=str(grezzo.get("luogo", "") or "").strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        contesto=str(grezzo.get("contesto", "") or "").strip(),
        licenza=str(grezzo.get("licenza", "") or "").strip(),
        consenso=str(grezzo.get("consenso", "") or "").strip(),
        pubblicabile=bool(pubblicabile),
        lettibilita=str(grezzo.get("lettibilita", "A1") or "A1").strip().upper(),
        nota=str(grezzo.get("nota", "") or "").strip(),
        durata=durata,
    )


def controlla_archivo(archivio: "Archivio", radice_audio: str = None) -> list:
    """I controlli sui brani audio.

    Sono gli stessi del glossario, e per la stessa ragione: un brano con un
    campo vuoto non e' un brano incompleto, e' un brano che puo' finire
    pubblicato senza che nessuno lo abbia deciso.

    Il controllo che pesa di piu' e' **A4**: `pubblicabile: true` senza
    consenso o senza licenza. E' il caso in cui il progetto pubblicherebbe una
    voce senza aver chiesto, e sbaglierebbe nel modo piu' grave che possa
    sbagliare.
    """
    from .verifica_dati import Problema

    problemi = []
    visti = set()
    for brano in archivio.brani:
        dove = brano.id or "(senza id)"
        if not brano.id:
            problemi.append(Problema("A1", dove, "brano senza id"))
        elif brano.id in visti:
            problemi.append(Problema("A2", dove, "id duplicato nel manifesto"))
        visti.add(brano.id)

        if not brano.file:
            problemi.append(Problema("A3", dove, "brano senza file"))
        if brano.riferimento:
            if not brano.riferimento.startswith(("V", "F")):
                problemi.append(Problema(
                    "A3b", dove,
                    "riferimento %r che non sembra un id di voce o di coppia"
                    % brano.riferimento))
        if brano.pubblicabile and not brano.consenso:
            problemi.append(Problema(
                "A4", dove,
                "dichiarato pubblicabile senza consenso: questo brano non entra "
                "nella pagina finche' non c'e' il consenso"))
        if brano.pubblicabile and not brano.licenza:
            problemi.append(Problema(
                "A5", dove,
                "dichiarato pubblicabile senza licenza: la registrazione e' di "
                "qualcuno e ridistribuirla e' una decisione, non un default"))
        if brano.file and not codice_valido(brano.varieta):
            problemi.append(Problema(
                "A6", dove, "varieta' %r fuori dall'insieme delle cinque"
                % (brano.varieta or "")))
        if brano.contesto and brano.contesto not in CONTESTI:
            problemi.append(Problema(
                "A7", dove, "contesto %r fuori dall'insieme %s"
                % (brano.contesto, ", ".join(CONTESTI))))
        if brano.lettibilita not in LIVELLI:
            problemi.append(Problema(
                "A8", dove, "lettibilita %r fuori dall'insieme %s"
                % (brano.lettibilita, ", ".join(LIVELLI))))
        if brano.consenso and not brano.voce:
            problemi.append(Problema(
                "A9", dove,
                "c'e' il consenso ma non c'e' detto chi ha parlato: un consenso "
                "senza nome non si puo' onorare"))
        if radice_audio and brano.publicabile() and not brano.esiste(radice_audio):
            problemi.append(Problema(
                "A10", dove,
                "dichiarato pubblicabile ma il file non c'e' in audio/: "
                "%s" % (brano.file or "(nessun file)")))
    return problemi