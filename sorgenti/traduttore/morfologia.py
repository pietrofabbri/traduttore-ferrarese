"""Le regole morfologiche, imparate dal corpus e non scritte a mano.

Il ferrarese ha l'infinito in `-ar` dove l'italiano ha `-are`, scrive la `z`
aspra come `s`, e in alcuni casi serba le desinenze italiane (`dottór`,
`rasón`). Sono tre fatti diversi, e il primo non si impara cercando un
suffisso **identico**: `cantare` e `cantar` non hanno Suffissi uguali, hanno
lo stesso **prefisso** e due desinenze diverse.

Per questo qui si impara una cosa sola, che e' anche l'unica che non si puo'
inventare: **una parola e' un prefisso piu' una desinenza**. E la regola che
si impara e' «prefisso questo, desinenza questa, desinenza quella». Il resto
e' conteggio.

Le regole hanno due forme, e si distinguono per il prefisso:

- **con prefisso** (`cant` + `are` > `cant` + `ar`): il prefisso deve essere
  esattamente quello, parola per parola. E' la forma piu' forte e serve per
  gli infiniti, dove la radice non si sposta;
- **senza prefisso**: valgono ovunque la parola finisca con quella
  desinenza. Serve per i suffissi che si attaccano, come `-ione` > `-ion`.

Una regola vale solo se ha **almeno due coppie diverse** e un accordo del
**settanta per cento o piu'**. L'accordo si misura sui dati, non sulla
promessa della regola.

La regola che tiene insieme tutto il modulo: **una regola non sovrascrive mai
il glossario.** Il livello 3 del motore si reached solo quando i primi due
livelli hanno detto che non sanno, quindi per costruzione non puo'
contraddire il glossario. E il glossario vince sempre, perche' e' l'unica
fonte che dichiara da dove viene.

Non si scrivono regole a mano in questo file. Chi vuole aggiungere una regola
mette la coppia nel corpus e rilancia `impara`: una regola senza esempi non ha
accordo, e senza accordo non viene salvata. Questo e' scomodo e e' il punto.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import italiano as analisi_italiana
from . import normalizza

# Soglia di accordo minima per usare una regola.
SOGLIA_ACCORDO = 0.70
# Numero minimo di coppie diverse per considerare una regola.
MINIMO_ESEMPI = 2
# Minimo di radici diverse per **generalizzare** una regola, cioe' per
# scriverla senza prefisso. Una radice sola non basta a dire che la
# trasformazione e' generale: basta a dire che quella parola si comporta cosi'.
RADICI_MINIME = 2
# Prefisso minimo della forma «prefisso + desinenza»: sotto le tre lettere
# non distingue una radice da una coincidenza.
PREFFISSO_MINIMO = 3
# Desinenza minima, in lettere. Sotto le due, la regola vale per quasi tutte le
# parole e non distingue niente.
DESINENZA_MINIMA = 2


@dataclass
class Regola:
    """Una corrispondenza fra due modi di spezzare una parola.

    La parola da tradurre si spezza in `prefisso` + `suffisso_italiano` e
    quella ferrarese in `prefisso` + `suffisso_ferrarese`. Il prefisso e'
    lo stesso da una parte e dall'altra: e' la radice, ed e' quello che la
    regola non tocca.
    """

    prefisso: str = ""
    suffisso_italiano: str = ""
    suffisso_ferrarese: str = ""
    esempi: list = field(default_factory=list)
    # La classe grammaticale per cui la regola e' stata imparata.
    # Vuota significa **non classificata**, e in quel caso la regola
    # non passa dal cancello: non si sa di che cosa sia, e il progetto
    # non finge di saperlo.
    classe: str = ""

    @property
    def accordo(self) -> float:
        """Accordo empirico: quante volte la regola, applicata alla parola
        italiana del suo stesso esempio, restituisce la parola ferrarese
        osservata.

        Non e' una misura di quanto la regola e' bella, e' una misura di quanto
        la regola **sopravvive alla propria generalizzazione**. Una regola
        imparata da `cantare` > `cantar` e da `camminare` > `caminar`, e poi
        resa generale perche' due radici diverse mostrano la stessa desinenza,
        sbaglia su `camminare`: produce `camminar` dove il testo dice
        `caminar`. Quella e' una riga con `attestato` falso, e l'accordo
        scende sotto la soglia, e la regola viene buttata. E' esattamente il
        comportamento voluto: meglio nessuna regola che una regola che sbaglia
        una volta su tre e non lo dichiara.
        """
        righe = [r for r in self.esempi if r.get("prodotto")]
        if not righe:
            return 0.0
        giuste = sum(1 for r in righe if r.get("attestato"))
        return giuste / len(righe)

    @property
    def supporto(self) -> int:
        return len(self.esempi)

    def etichetta(self) -> str:
        if self.prefisso:
            return "%s+%s > %s+%s" % (
                self.prefisso, self.suffisso_italiano,
                self.prefisso, self.suffisso_ferrarese)
        return "%s > %s" % (self.suffisso_italiano or "·", self.suffisso_ferrarese or "·")

    def come_dict(self) -> dict:
        return {
            "classe": self.classe,
            "prefisso": self.prefisso,
            "suffisso_italiano": self.suffisso_italiano,
            "suffisso_ferrarese": self.suffisso_ferrarese,
            "accordo": round(self.accordo, 3),
            "supporto": self.supporto,
            "esempi": self.esempi[:6],
        }


def allinea(coppia_italiano: list, coppia_ferrarese: list) -> list:
    """Allinea due frasi per posizione, restituendo le coppie di parole.

    Solo quando le frasi hanno lo stesso numero di parole, e perche' la ragione
    e' dichiarata in `impara`: l'allineamento per posizione e' l'unico che non
    abbia bisogno di sapere cosa significano le parole, ed e' quindi immune
    all'errore che si propaga piu' in fretta in un corpus parallelo.
    """
    if len(coppia_italiano) != len(coppia_ferrarese):
        return []
    return list(zip(coppia_italiano, coppia_ferrarese))


def _prefisso_comune(a: str, b: str, minimo: int = PREFFISSO_MINIMO):
    """Il prefisso comune piu' lungo fra due chiavi, se arriva a `minimo`.

    Il prefisso non puo' mangiare tutto: su `cantare` e `cantar` il prefisso
    comune piu' lungo e' `cantar`, che e' l'intera parola ferrarese e non
    lascia nessuna desinenza da confrontare. Per questo la ricerca si ferma a
    `minimo(lunghezze) - DESINENZA_MINIMA`, e la regola richiede che dalle
    due parti resti almeno una desinenza.
    """
    n = min(len(a), len(b)) - DESINENZA_MINIMA
    for lunghezza in range(n, minimo - 1, -1):
        if a[:lunghezza] == b[:lunghezza]:
            return a[:lunghezza]
    return ""


def _suffisso_comune(a: str, b: str, minimo: int = DESINENZA_MINIMA):
    """Il suffisso comune piu' lungo fra due chiavi, se arriva a `minimo`."""
    n = min(len(a), len(b))
    for lunghezza in range(n, minimo - 1, -1):
        if a[-lunghezza:] == b[-lunghezza:]:
            return a[-lunghezza:]
    return ""


def _pezzi(italiano: str, ferrarese: str):
    """Spezza due parole allineate in (prefisso, desinenza_it, desinenza_fe).

    Si prova prima la forma con prefisso, che e' quella degli infiniti, e solo
    se fallisce la forma senza prefisso, che e' quella dei suffissi agglutinati.
    Il motivo di questo ordine e' che la forma con prefisso e' piu' forte: se
    due parole hanno la stessa radice e due desinenze diverse, il rapporto fra
    quelle due desinenze e' un fatto della lingua; se non hanno niente in
    comune e l'ultima lettera coincide, e' una coincidenza.
    """
    prefisso = _prefisso_comune(italiano, ferrarese)
    if prefisso:
        resto_it = italiano[len(prefisso):]
        resto_fe = ferrarese[len(prefisso):]
        if (len(resto_it) >= DESINENZA_MINIMA and len(resto_fe) >= DESINENZA_MINIMA
                and resto_it != resto_fe):
            return prefisso, resto_it, resto_fe
    suffisso = _suffisso_comune(italiano, ferrarese, DESINENZA_MINIMA + 1)
    if suffisso and suffisso != italiano and suffisso != ferrarese:
        return "", suffisso, suffisso
    return "", "", ""


def impara(corpo, glossario=None, italiano=None) -> list:
    """Impariamo le regole da un corpus di coppie valide.

    `glossario` serve a una cosa sola: a capire quali coppie sono gia' nel
    glossario, e quindi non insegnano niente sulle regole. Una coppia in cui
    entrambe le parole sono gia' note e' un duplicato del glossario, non una
    regola nuova, e usarla per imparare significa far imparare il glossario a
    se stesso.
    """
    conosciute = set()
    if glossario is not None:
        for voce in glossario.voci:
            conosciute.add(normalizza.chiave(voce.ferrarese))
            conosciute.add(normalizza.chiave(voce.italiano))

    # Qui si raccoglie **senza** filtrare. Il filtro del numero minimo di
    # coppie viene dopo, e non per radice: se lo si mettesse qui, una regola
    # che nasce da una coppia sola per radice verrebbe buttata prima di poter
    # essere generalizzata, ed e' proprio la generalizzazione a darle il
    # supporto che le manca. E' un difetto che si vede solo su un caso vero.
    raccolte = {}
    for coppia in corpo.coppie_valide():
        it = normalizza.tokenizza_chiave(coppia.italiano)
        fe = normalizza.tokenizza_chiave(coppia.ferrarese)
        for parola_it, parola_fe in allinea(it, fe):
            if not parola_it or not parola_fe or parola_it == parola_fe:
                continue
            if parola_it in conosciute and parola_fe in conosciute:
                # Entrambe le parole sono gia' nel glossario: la coppia non
                # insegna niente sulle regole, la insegna sul glossario.
                continue
            prefisso, resto_it, resto_fe = _pezzi(parola_it, parola_fe)
            if not prefisso and not resto_it:
                continue
            chiave = (prefisso, resto_it, resto_fe)
            raccolte.setdefault(chiave, []).append({
                "coppia": coppia.id,
                "italiano": parola_it,
                "ferrarese": parola_fe,
            })

    # Da qui in poi si decide **quanto sia generale** una regola, e la
    # decisione si prende sui dati e non sull'intenzione.
    #
    # Il problema e' reale e si vede su un caso vero: `cantare` e `camar`
    # danno la coppia `cant`+`are` > `cant`+`ar`. Se da li' si ricava una regola
    # con il prefisso `cant`, quella regola vale solo per `cantare`, e il gioco
    # non la usa mai. Se invece `camminare` > `caminar` dà la stessa coppia di
    # desinenze `are` > `ar` con un prefisso **diverso**, allora i dati stanno
    # dicendo che la trasformazione non dipende dalla radice, e la regola
    # generale si puo' scrivere.
    #
    # Il criterio e' quindi: se la stessa coppia di desinenze compare con
    # almeno due radici diverse, la regola e' generale e il prefisso si
    # accantona. Se compare con una radice sola, la regola resta specifica e
    # vale solo per quella radice, e vale solo se piu' coppie la sostengono.
    # Non si generalizza per analogia: si generalizza quando due radici
    # diverse mostrano lo stesso comportamento.
    per_desidenza = {}
    for (prefisso, resto_it, resto_fe), esempi in raccolte.items():
        per_desidenza.setdefault((resto_it, resto_fe), []).append((prefisso, esempi))

    regole = []
    for (resto_it, resto_fe), gruppo in per_desidenza.items():
        radici = {p for p, _ in gruppo}
        esempi = [e for _, esempi in gruppo for e in esempi]
        distinti = {e["coppia"] for e in esempi}
        if len(distinti) < MINIMO_ESEMPI:
            # Una sola coppia in tutto, per qualunque radice: non e' una
            # regola, e' un caso. Il gioco didattico non ci mette dentro niente
            # che sia stato visto una volta sola.
            continue
        if len(radici) >= RADICI_MINIME:
            regola = Regola("", resto_it, resto_fe, esempi)
        else:
            # Una sola radice: la regola vale solo per quella, e solo se la
            # sostiene piu' di una coppia.
            prefisso, esempi = gruppo[0]
            regola = Regola(prefisso, resto_it, resto_fe, esempi)
        _verifica_accordo(regola)
        if regola.accordo < SOGLIA_ACCORDO:
            continue
        regola.classe = _classe_di(esempi, italiano)
        regole.append(regola)
    # Dall'indicazione piu' specifica alla piu' generica: una regola con
    # prefisso e desinenza lunga batte una regola che aggancia solo l'ultima
    # lettera. E' lo stesso ordine con cui si applicano.
    regole.sort(key=lambda r: (-len(r.suffisso_italiano), -len(r.prefisso), -r.accordo))
    return regole


def _classe_di(esempi: list, italiano) -> str:
    """La classe grammaticale che gli esempi italiani dichiarano, insieme.

    Si prende la classe piu' frequente fra gli esempi della regola, e solo se e'
    una sola: se due esempi hanno due classi diverse la regola non e' di una
    classe, e non la si dichiara di una classe a caso — resta non classificata
    e il chiamante deve sapere che il progetto non lo sa.

    Senza analizzatore la classe resta vuota e la regola non viene filtrata:
    e' il comportamento di prima, dichiarato come scelta e non come silenzio.
    """
    if italiano is None:
        return ""
    conteggio = {}
    for esempio in esempi:
        risposta = italiano.analizza(esempio["italiano"])
        if risposta.nota:
            conteggio[risposta.classe] = conteggio.get(risposta.classe, 0) + 1
    if not conteggio:
        return ""
    ordinate = sorted(conteggio.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(ordinate) > 1 and ordinate[0][1] == ordinate[1][1]:
        return ""
    return ordinate[0][0]


def _verifica_accordo(regola: Regola) -> None:
    """Riapplica la regola ai suoi stessi esempi e annota il risultato.

    E' il momento in cui una regola viene messa alla prova, e va fatto **dopo**
    la generalizzazione, non prima: generalizzare e poi misurare e' l'unico
    ordine in cui la misura vale qualcosa.
    """
    for riga in regola.esempi:
        prodotto = applica(riga["italiano"], [regola], "it-fe")
        riga["prodotto"] = prodotto
        riga["attestato"] = prodotto == riga["ferrarese"]


def applica(parola: str, regole: list, direzione: str = "it-fe",
            italiano=None) -> str:
    """Applica la prima regola che produce una parola.

    Se nessuna regola produce niente si restituisce la parola di partenza, e
    il chiamante deve saperlo: e' il caso in cui il motore **non sa**.

    `italiano` e' l'analizzatore grammaticale. Quando c'e', una regola
    classificata vale solo per le parole della sua classe, e una parola di
    classe ignota non viene riscritta da nessuna regola: il progetto non
    indovina che cosa sia una parola per poterle toccare le desinenze. Passando
    `None` si ottiene esattamente il comportamento di prima.
    """
    k = normalizza.chiave(parola)
    if not k:
        return parola
    classe = ""
    if italiano is not None:
        classe = italiano.analizza(parola).classe
    if direzione == "it-fe":
        for regola in regole:
            if classe and regola.classe and not \
                    analisi_italiana.compatibile(classe, regola.classe):
                continue
            if not regola.suffisso_italiano or not k.endswith(regola.suffisso_italiano):
                continue
            if regola.prefisso and not k.startswith(regola.prefisso):
                continue
            nucleo = k[: len(k) - len(regola.suffisso_italiano)]
            if regola.prefisso and nucleo != regola.prefisso:
                continue
            prodotto = nucleo + regola.suffisso_ferrarese
            if prodotto != k and len(prodotto) >= DESINENZA_MINIMA + 1:
                return prodotto
        return parola
    for regola in regole:
        if classe and regola.classe and not \
                analisi_italiana.compatibile(classe, regola.classe):
            continue
        if not regola.suffisso_ferrarese or not k.endswith(regola.suffisso_ferrarese):
            continue
        if regola.prefisso and not k.startswith(regola.prefisso):
            continue
        nucleo = k[: len(k) - len(regola.suffisso_ferrarese)]
        if regola.prefisso and nucleo != regola.prefisso:
            continue
        prodotto = nucleo + regola.suffisso_italiano
        if prodotto != k and len(prodotto) >= DESINENZA_MINIMA + 1:
            return prodotto
    return parola


def spiega(parola: str, regole: list, direzione: str = "it-fe",
           italiano=None):
    """Dice quale regola ha prodotto la parola, o `(None, None)` se nessuna."""
    for regola in regole:
        if direzione == "it-fe" and not regola.suffisso_italiano:
            continue
        if direzione != "it-fe" and not regola.suffisso_ferrarese:
            continue
        if italiano is not None and regola.classe:
            risposta = italiano.analizza(parola)
            if not analisi_italiana.compatibile(risposta.classe,
                                                regola.classe):
                continue
        prodotto = applica(parola, [regola], direzione, italiano)
        if prodotto != parola:
            return regola, prodotto
    return None, None