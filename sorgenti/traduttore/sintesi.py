"""I suoni sintetici: quello che la pagina puo' far ascoltare **non e'** una
voce, e il posto in cui sta e' la dichiarazione di questa frase.

**La distinzione che regge tutto il modulo.** Il progetto ha due cartelle di
suoni e non le confonde:

- `web/audio/` — i brani di **persone vere**. Entrano solo con consenso, licenza
  e una decisione esplicita di pubblicazione. Oggi non c'e' niente, e va
  bene cosi'.
- `web/sintesi/` — i suoni che ha fatto **un programma**, generati in locale con
  `espeak-ng` dalle regole dichiarate in `dati/fonetica.jsonl`.

Sono due fatti diversi e una confusione fra i due e' il modo tipico in cui un
progetto di lingue minori si racconta di avere una voce che non ha. Per questo i
due insiemi non si toccano mai e nessun controllo li lascia avvicinare: **Y3b**
segnala un suono generato comparso dentro `audio/`, che e' l'errore che rende
falso il conteggio dei brani di persone vere.

Il controllo guarda il **nome** del file e non il suo contenuto, perche' il
contenuto non dice nulla: un `wav` prodotto da `espeak-ng` e' un RIFF con
quattro campi e nient'altro, senza una parola che dica da dove viene. Un
controllo che promette di distinguere le due cose guardando dentro il file
sarebbe un controllo che passa senza mai aver guardato niente.

**Un suono qui non verifica niente.** `dati/sintesi.jsonl` esiste perche' una
trascrizione, da sola, non si puo' ascoltare: e' un insieme di simboli. Il suono
e' la lettura di quei simboli, non la prova che i simboli siano giusti. Per
questo ogni riga resta `attendibilita: "I"` e `da_verificare: true`, come la
trascrizione da cui viene, e ogni riga porta la dichiarazione di sintesi.

**Solo dove il progetto non ha dubbi.** Le 28 trascrizioni dichiarate non sono
tutte suonabili: 16 hanno un dubbio che `legge` segnala (la `gn` davanti ad
accento, l'accento non marcato nella fonte). Suonarle produrrebbe uno studente
che impara un suono sbagliato con la stessa efficacia di uno giusto, senza
potersene accorgere. Quindi **una parola con un dubbio non ha un file**, e
**Y4** verifica che nessun file senza dubbio dichiarato sia comparso: e' il
controllo che impedisce che la comodo' diventi un buco.

**Il peso.** Suonare tutte le 10401 parole del glossario costerebbe circa
**493 megabyte**, che non e' una pagina. Percio' il suono esiste solo dove il
progetto ha gia' scritto come si pronuncia: 12 parole, circa 556 KB.

**Quello che chiude la domanda resta un altro.** Una voce di macchina non
insegna la musicalita' dell'italiano ferrarese, che e' quasi tutto il modo in
cui le vocali finali si chiudono. Il percorso vero e' S007, il portale dei
dialetti della Regione, e chiede il permesso alle persone che hanno parlato.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .varieta import codice_valido

# La dichiarazione che sta in ogni riga del manifesto. Una sola frase e un solo
# posto in cui scriverla: se la pagina e il manifesto dicessero cose diverse,
# la pagina avrebbe vinto, perche' e' li' che lo studente la legge.
NOTA_SINTETICA = ("voce sintetica: non e' un parlante ferrarese e non "
                  "verifica la trascrizione")

# La cartella dei suoni generati. Il nome e' dichiarato qui e non dedotto: se
# domani la si chiama `audio` e il progetto perde la distinzione che e' il
# punto di questo modulo.
CARTELLA = "sintesi"

# La cartella dei brani di persone vere, che i suoni generati non possono
# raggiungere. Serve al controllo Y5.
CARTELLA_BRANI = "audio"

# Quanti byte puo' pesare un suono prima di essere un problema. Serve al
# controllo Y3: 556 KB per dodici parole sono ~46 KB l'una, e una parola che
# ne pesa mille non e' una parola.
PESO_MAX = 120 * 1024


@dataclass
class Suono:
    """Un suono generato, con tutto quello che va detto su di lui."""

    id: str
    riferimento: str
    forma: str
    ipa: str
    file: str
    varieta: str = ""
    fonte: str = ""
    fonemi: str = ""
    attendibilita: str = "I"
    da_verificare: bool = True
    sintetica: bool = True
    nota: str = ""
    avvertimento: str = ""

    def come_dict(self) -> dict:
        return {
            "id": self.id,
            "riferimento": self.riferimento,
            "forma": self.forma,
            "ipa": self.ipa,
            "file": self.file,
            "varieta": self.varieta,
            "fonte": self.fonte,
            "fonemi": self.fonemi,
            "attendibilita": self.attendibilita,
            "da_verificare": self.da_verificare,
            "sintetica": self.sintetica,
            "nota": self.nota,
            "avvertimento": self.avvertimento,
        }

    def esiste(self, radice: str) -> bool:
        return bool(self.file) and os.path.isfile(
            os.path.join(radice, CARTELLA, self.file))

    def peso(self, radice: str) -> int:
        percorso = os.path.join(radice, CARTELLA, self.file)
        try:
            return os.path.getsize(percorso)
        except OSError:
            return 0


@dataclass
class Sintesi:
    """Il manifesto dei suoni generati."""

    suoni: list = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.suoni)

    def __iter__(self):
        return iter(self.suoni)

    @classmethod
    def da_file(cls, percorso: str) -> "Sintesi":
        suoni = []
        if percorso and os.path.exists(percorso):
            with open(percorso, "r", encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if riga and not riga.startswith("//"):
                        suoni.append(_suono_da_dict(json.loads(riga)))
        return cls(suoni)

    def per_id(self, identificatore: str):
        for s in self.suoni:
            if s.id == identificatore:
                return s
        return None

    def per_riferimento(self, riferimento: str) -> list:
        return [s for s in self.suoni if s.riferimento == riferimento]

    def stato(self, radice: str) -> dict:
        """Che cosa c'e' davvero, in numeri, e che cosa manca.

        `presenti` conta i file che ci sono: un suono dichiarato senza file non
        e' un suono, e la pagina non puo'offerre un pulsante che non porta da
        nessuna parte.
        """
        return {
            "dichiarati": len(self.suoni),
            "presenti": sum(1 for s in self.suoni if s.esiste(radice)),
            "peso": sum(s.peso(radice) for s in self.suoni),
            "varieta": sorted({s.varieta for s in self.suoni if s.varieta}),
            "sintetiche": sum(1 for s in self.suoni if s.sintetica),
        }


def _suono_da_dict(grezzo: dict) -> Suono:
    da_verificare = grezzo.get("da_verificare", True)
    if isinstance(da_verificare, str):
        da_verificare = da_verificare.strip().lower() in ("1", "true", "si", "sì")
    sintetica = grezzo.get("sintetica", True)
    if isinstance(sintetica, str):
        sintetica = sintetica.strip().lower() in ("1", "true", "si", "sì")
    return Suono(
        id=str(grezzo.get("id", "")).strip(),
        riferimento=str(grezzo.get("riferimento", "") or "").strip(),
        forma=str(grezzo.get("forma", "") or "").strip(),
        ipa=str(grezzo.get("ipa", "") or "").strip(),
        file=str(grezzo.get("file", "") or "").strip(),
        varieta=str(grezzo.get("varieta", "") or "").strip(),
        fonte=str(grezzo.get("fonte", "") or "").strip(),
        fonemi=str(grezzo.get("fonemi", "") or "").strip(),
        attendibilita=str(grezzo.get("attendibilita", "I") or "I").strip(),
        da_verificare=bool(da_verificare),
        sintetica=bool(sintetica),
        nota=str(grezzo.get("nota", "") or "").strip(),
        avvertimento=str(grezzo.get("avvertimento", "") or "").strip(),
    )


def controlla_sintesi(sintesi: "Sintesi", radice_web: str = None,
                     id_ammessi: set = None,
                     forme_senza_dubbio: set = None,
                     nomi_generati: set = None) -> list:
    """I controlli sui suoni generati.

    Sono separati dai controlli A1-A10 di `audio` perche' le due cartelle
    hanno regole opposte: li' un suono senza consenso e' un errore gravissimo,
    qui un suono senza dubbio dichiarato e' un errore gravissimo, e non hanno
    niente da dirsi.

    `Y3` e `Y4` sono i due che contano. `Y3` chiude la porta di `audio/` da
    fuori: un file generato che finisca li' dentro renderebbe falso il conto dei
    brani di persone vere, che e' un conto che il progetto fa pubblicamente.
    `Y4` verifica che non sia comparso un suono per una parola che il progetto
    sa di non poter pronunciare con sicurezza: e' il buco che la comodo' aprirebbe.
    """
    from .verifica_dati import Problema

    nomi_generati = nomi_generati or {s.file for s in sintesi.suoni if s.file}
    problemi = []
    visti = set()
    for suono in sintesi.suoni:
        dove = suono.id or "(senza id)"
        if not suono.id:
            problemi.append(Problema("Y1", dove, "suono senza id"))
        elif suono.id in visti:
            problemi.append(Problema("Y2", dove, "id duplicato nel manifesto"))
        visti.add(suono.id)

        if not suono.file:
            problemi.append(Problema("Y1b", dove, "suono senza file"))
        elif os.path.basename(suono.file) != suono.file:
            # Un percorso che esce dalla cartella e' un modo per arrivare
            # anywhere. Su `file://` la pagina puo' aprire qualunque cosa sul
            # disco dello studente, quindi il nome del file non puo' contenere
            # percorsi.
            problemi.append(Problema(
                "Y2b", dove,
                "il file %r ha un percorso dentro il nome: deve stare solo in %s/"
                % (suono.file, CARTELLA)))
        if not suono.riferimento:
            problemi.append(Problema(
                "Y2c", dove,
                "suono senza riferimento: non dice di che parola e' la voce"))
        elif not suono.riferimento.startswith(("V", "F", "P")):
            problemi.append(Problema(
                "Y2d", dove,
                "riferimento %r che non sembra un id di voce, di coppia o di "
                " proverbio" % suono.riferimento))
        if not suono.forma:
            problemi.append(Problema(
                "Y2e", dove, "suono senza la forma scritta da pronunciare"))
        if not suono.ipa:
            problemi.append(Problema(
                "Y2f", dove,
                "suono senza IPA: un suono di cui non si sa la pronuncia "
                "scritta non e' verificabile da nessuno"))
        if suono.file and not codice_valido(suono.varieta):
            problemi.append(Problema(
                "Y1c", dove, "varieta' %r fuori dall'insieme delle cinque"
                % (suono.varieta or "")))
        if suono.file and not suono.nota:
            # Il campo che dichiara che non e' una persona. Se sparisce, il
            # pulsante suona senza dire niente, ed e' il modo in cui una voce
            # di macchina diventa «il ferrarese».
            problemi.append(Problema(
                "Y1d", dove,
                "suono senza la dichiarazione di sintesi: ogni suono generato "
                "deve dire che non e' un parlante ferrarese"))

        if radice_web and suono.file and not suono.esiste(radice_web):
            problemi.append(Problema(
                "Y2g", dove,
                "dichiarato in %s.jsonl ma il file non c'e' in %s/: %s"
                % (CARTELLA, CARTELLA, suono.file)))
            continue
        if radice_web and suono.file and suono.peso(radice_web) > PESO_MAX:
            problemi.append(Problema(
                "Y3", dove,
                "il file pesa %d byte, sopra il tetto di %d: una parola che "
                "costa piu' di %d KB non e' una parola"
                % (suono.peso(radice_web), PESO_MAX, PESO_MAX // 1024)))

        if (forme_senza_dubbio is not None and suono.forma
                and suono.forma not in forme_senza_dubbio):
            problemi.append(Problema(
                "Y4", dove,
                "suono generato per %r, che il progetto non sa pronunciare "
                "senza dubbi: il file non deve esserci finche' il dubbio non "
                "e' risolto" % suono.forma))

    # Y3b per la porta chiusa: nessun suono generato dentro la cartella dei
    # brani di persone vere.
    #
    # Qui c'era un controllo che leggeva i primi 2048 byte del file e cercava
    # la parola «espeak», perche' avevo scritto — e poi verificato — che
    # `espeak-ng` scrive il suo nome nel commento del formato RIFF. **Non e'
    # vero**: il file che produce e' un RIFF con quattro campi e nient'altro,
    # 45 KB di silenzio e campione, e la stringa non c'e' da nessuna parte.
    # Il controllo non poteva scattare mai, e sarebbe passato per sempre.
    #
    # La domanda giusta non e' «da quale programma viene questo file», che il
    # file non dice, ma «** questo nome l'aveva gia' dichiarato un manifesto
    # di suoni generati?». Se sì, e il file e' finito in `audio/`, e' un
    # suono di programma dentro la cartella delle persone vere, ed e'
    # esattamente il caso da prendere. Il resto — un file che nessun dei due
    # manifesti dichiara — l'ha sempre segnalato il passo della CI sui
    # brani, che e' il posto giusto per quella domanda.
    if radice_web and nomi_generati:
        cartella_brani = os.path.join(radice_web, CARTELLA_BRANI)
        if os.path.isdir(cartella_brani):
            per_audio = sorted(n for n in os.listdir(cartella_brani)
                               if n.endswith(".wav") and n in nomi_generati)
            for nome in per_audio:
                problemi.append(Problema(
                    "Y3b", os.path.join(CARTELLA_BRANI, nome),
                    "%s e' un suono generato dentro la cartella dei brani di "
                    "persone vere: %s/ contiene registrazioni, %s/ contiene "
                    "voci di programma, e i due conti non si sommano"
                    % (nome, CARTELLA_BRANI, CARTELLA)))
    return problemi
