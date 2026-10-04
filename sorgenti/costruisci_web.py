"""Il sito statico: piu' pagine, nessuna richiesta di rete, nessun account.

Le stesse regole che valgono per il gioco valgono qui, perche' e' lo stesso
pubblico: la pagina si apre da un file sul disco o da GitHub Pages, funziona
senza connessione e non chiede nulla a nessuno.

**Perche' sei pagine e non una.** La pagina unica pesava **6,2 megabyte**, di
cui il 99,2% era il blocco dei dati e l'87,5% era il glossario. Il glossario
intero dentro ogni pagina significa che anche la pagina che serve solo a
leggere i numeri del progetto deve scaricare un vocabolario. E' il motivo per
cui il sito era scomodo da consultare: non perche' i dati fossero sbagliati,
ma perche' erano tutti nella stessa stanza.

La divisione segue quello che le pagine hanno davvero in comune:

| pagina | cosa c'e' | peso |
|---|---|---|
| `index.html` | i numeri, i buchi, la strada per le altre pagine | ~60 KB |
| `traduttore.html` | il traduttore, con il glossario ridotto ai campi che serve | ~1,5 MB |
| `glossario.html` | l'indice delle fette | ~30 KB |
| `glossario-NN.html` | una fetta di 500 voci, con ricerca dentro la fetta | ~140 KB |
| `frasi.html` | coppie parallele e proverbi | ~30 KB |
| `suoni.html` | le varieta' e il riproduttore | ~40 KB |

**Perche' il glossario e' a fette e non in una pagina sola.** Perche' 10387
voci in un'unica pagina resterebbero 5,6 megabyte: si puo' alleggerire il
glossario potando i campi, ma la misura dice che i dati sono distribuiti e
nessun campo lo salva da solo. L'unica cosa che funziona e' **spostare il
peso in piu' pagine**, ognuna con la sua. Ogni fetta ha la sua ricerca, il
suo link precedente e successivo e la sua lettera: si arriva alla parola
che si cerca aprendo la pagina giusta, non leggendo 10387 righe.

**L'ordine delle fette e' quello della ricerca.** Le voci sono ordinate con
`normalizza.chiave()`, la stessa funzione che il motore usa in Python e che
la pagina usa in JavaScript. Se l'ordine fosse un altro, la lettera nella
barra non porterebbe da nessuna parte.

**I dati viaggiano dentro la pagina, in un blocco `<script>`.** Non e' una
scelta elegante: e' la scelta che rende la pagina apribile da `file://` senza
server, che e' la condizione con cui la si distribuisce. Lo stesso vale per
la divisione in pagine: ogni pagina porta dentro i suoi dati, quindi passare
da una all'altra e' un collegamento e non una richiesta. L'audio non puo'
fare la stessa cosa, quindi viene copiato in `web/audio/` e li' resta, e il
permesso di copiarlo e' chiesto tre volte prima (vedi `audio/README.md`).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traduttore import morfologia  # noqa: E402
from traduttore.audio import Archivio  # noqa: E402
from traduttore.sintesi import Sintesi  # noqa: E402
from traduttore.corpora import Corpus  # noqa: E402
from traduttore.fonetica import Fonetica  # noqa: E402
from traduttore import verifica_dati  # noqa: E402
from traduttore.glossario import Glossario  # noqa: E402
from traduttore.motore import ORIGINE  # noqa: E402
from traduttore.normalizza import chiave  # noqa: E402
from traduttore.varieta import NOMI, Varieta  # noqa: E402


TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modello.html")

# Quante voci in una fetta. Il numero e' una scelta e va dichiarata perche'
# non e' neutrale: 300 vuol dire 35 pagine e 88 KB l'una, 800 vuol dire 13
# pagine e 205 KB l'una. Sotto i ~150 KB la pagina si sente subito veloce
# anche su una scuola con la connessione lenta, e il sito si apre da `file://`
# dove il costo e' proprio la lettura del file. 500 e' il compromesso, e se
# un giorno il glossario raddoppia il numero va riguardato perche' il peso
# di una pagina raddoppia con lui.
VOCI_PER_FETTA = 500

# La frase che dichiara che il suono non e' una persona. Vive qui e nella
# pagina la legge: due posti, uno solo da tenere d'accordo.
AVVERTIMENTO_SINTESI = (
    "Attenzione: questo suono lo ha fatto un programma, non una persona "
    "di Ferrara. Serve per sentire come suona la grafia, non per imparare "
    "come parlano i ferraresi.")

# Le voci del glossario in **array**, non in oggetti: i nomi dei campi si
# ripetono una volta per voce in un JSON di oggetti e sono qualche
# centinaio di kilobyte di sovrapprezzo.
# Dichiarandoli una volta sola si risparmia il 23%, che su 5,6 megabyte fa
# oltre un megabyte. Il prezzo e' che la pagina deve leggere per posizione,
# e quindi `intestazione` e `voci` non possono separarsi.
CAMPI_TABELLA = ("id", "fe", "it", "varianti", "campo", "varieta",
                 "attendibilita", "da_verificare", "fonte", "moderno",
                 "fonte_moderno", "sinonimi", "principale_it", "principale_fe")
# I campi che la pagina del traduttore riceve. Dieci, e non undici: `note`
# e' stato tolto, e la ragione sta nel peso.
#
# Le note del glossario sono 1,4 megabyte di testo, quasi il 47% di tutto
# quello che la pagina trasporta, e **nessun codice della pagina le legge**:
# il motore cerca per `id`, `fe`, `it`, `varianti`, `campo` e `principale_*`,
# e la tabella del glossario non usa i campi di questa lista. La nota era
# dentro per completezza dello schema, non perche' serviva.
#
# Senza di essa `traduttore.html` pesa 2,5 MB invece di 3,9. Il tetto di 3 MB
# nella CI e' dichiarato e non si alza: «sopra, la pagina non si apre subito
# e il progetto smette di essere consultabile», che era il motivo per cui il
# sito era stato diviso. Il glossario e' passato da 10387 a 16739 voci, quindi
# il peso e' cresciuto davvero, e la risposta non e' spostare la soglia ma
# togliere il campo che nessuno leggeva.
#
# Le note restano tutte in `dati/glossario.jsonl` e nelle pagine del
# glossario: questo e' solo il trasporto della pagina del traduttore.
CAMPI_MOTORE = ("id", "fe", "it", "varianti", "campo", "varieta",
                "attendibilita", "da_verificare", "principale_it",
                "principale_fe")

# Le pagine del sito. `sezioni` sono i marcatori di `modello.html` che la
# pagina tiene: tutto il resto viene rimosso. La lista e' qui e non nel
# generatore perche' una pagina che non e' dichiarata qui non esiste, e
# `prove/test_traduttore.py` verifica che la lista e le sezioni del modello
# tornino: una sezione senza pagina e' codice che nessuno vedra' mai.
PAGINE = (
    {"file": "index.html", "chiave": "index",
     "titolo": "Il progetto",
     "occhiello": "Che cosa sa il motore, che cosa non sa, e da dove si comincia.",
     "sezioni": ("fette", "index")},
    {"file": "traduttore.html", "chiave": "traduttore",
     "titolo": "Traduttore",
     "occhiello": "Traduce parola per parola e dice da dove viene ogni parola.",
     "sezioni": ("traduttore",)},
    {"file": "glossario.html", "chiave": "glossario",
     "titolo": "Il glossario",
     "occhiello": "Le voci sono a fette: si apre la lettera e si cerca dentro.",
     "sezioni": ("fette",)},
    {"file": "frasi.html", "chiave": "frasi",
     "titolo": "Coppie e proverbi",
     "occhiello": "Le frasi che il glossario non puo' contenere.",
     "sezioni": ("frasi",)},
    {"file": "suoni.html", "chiave": "suoni",
     "titolo": "Varieta' e suoni",
     "occhiello": "Le cinque varieta' e le poche parole che si possono ascoltare.",
     "sezioni": ("suoni",)},
    {"file": "regole.html", "chiave": "regole",
     "titolo": "Le regole",
     "occhiello": "Che cosa succede a una parola quando la si pluralizza o la si coniuga.",
     "sezioni": ("regole",)},
)

# La barra di navigazione: l'ordine in cui le pagine si presentano, e la
# voce «verso» per il glossario, che non e' una pagina sola ma un indice.
NAVIGAZIONE = (
    ("index.html", "Il progetto"),
    ("traduttore.html", "Traduttore"),
    ("glossario.html", "Glossario"),
    ("frasi.html", "Coppie e proverbi"),
    ("suoni.html", "Varieta' e suoni"),
    ("regole.html", "Le regole"),
)


# I nomi che la pagina usa e i nomi che la classe `Voce` ha. Sono diversi per
# quattro campi, e la differenza e' gia' costata una generazione intera di
# pagine con `fe: null` e `it: null`: `getattr(v, "fe", None)` su un attributo
# che si chiama `ferrarese` **non fallisce**, restituisce `None`, e una pagina
# con tutte le forme a vuoto sembra un glossario vuoto invece di un refuso.
#
# Per questo il nome della pagina non viene mai usato come nome dell'attributo:
# la mappa e' dichiarata qui, e se un campo non c'e' la generazione fallisce
# invece di produrre una pagina mezza vuota.
CAMPI_VOCE = {
    "id": "id",
    "fe": "ferrarese",
    "it": "italiano",
    "varianti": "varianti",
    "campo": "campo",
    "varieta": "varieta",
    "attendibilita": "attendibilita",
    "da_verificare": "da_verificare",
    "fonte": "fonte",
    "note": "note",
    "registro": "registro",
    "moderno": "moderno",
    "fonte_moderno": "fonte_moderno",
    "sinonimi": "sinonimi",
    "principale_it": "principale_italiano",
    "principale_fe": "principale_ferrarese",
}


def _voce(v, campi: tuple) -> list:
    """Una voce come lista di valori, nell'ordine dichiarato in `campi`.

    Un campo che non esiste in `CAMPI_VOCE` e' un errore, non un `None`: e' la
    differenza fra «questa voce non ha una nota» e «qui il nome del campo e'
    sbagliato», che si vedono uguali e non lo sono.
    """
    fuori = [c for c in campi if c not in CAMPI_VOCE]
    if fuori:
        raise KeyError("campo della pagina senza nome in `Voce`: %s"
                       % ", ".join(fuori))
    return [getattr(v, CAMPI_VOCE[c]) for c in campi]


def _coppie(corpus) -> list:
    """Le coppie parallele come la pagina le legge.

    `Coppia` e `Proverbio` non hanno `come_dict`, quindi il dizionario si
    scrive qui. I nomi dei campi non sono un dettaglio: sono i nomi che il
    codice della pagina usa, e cambiarli qui rompe la tabella senza che
    nessuno se ne accorga.
    """
    return [{"id": c.id, "it": c.italiano, "fe": c.ferrarese, "tipo": c.tipo,
             "varieta": c.varieta, "fonte": c.fonte, "nota": c.nota}
            for c in corpus.coppie]


def _proverbi(corpus) -> list:
    return [{"id": p.id, "it": p.italiano, "fe": p.ferrarese,
             "letterario": p.letterario, "popolare": p.popolare,
             "fonte": p.fonte, "significato": p.significato}
            for p in corpus.proverbi]


def _regole(regole) -> list:
    return [{"etichetta": r.etichetta(), "accordo": round(r.accordo, 3),
             "supporto": r.supporto, "prefisso": r.prefisso,
             "suffisso_italiano": r.suffisso_italiano,
             "suffisso_ferrarese": r.suffisso_ferrarese}
            for r in regole]


def _serie(voci, campi: tuple) -> dict:
    """Le voci in forma compatta: nomi dei campi una volta, valori in fila."""
    return {"intestazione": list(campi), "voci": [_voce(v, campi) for v in voci]}


def fette_del_glossario(glossario: Glossario) -> list:
    """Le voci in fette, ordinate come le cerca il motore.

    L'ordine e' quello di `normalizza.chiave()` perche' e' lo stesso che usa
    la ricerca: una fetta che comincia con la `c` deve contenere le `c`,
    altrimenti la lettera nella barra sarebbe una promessa che il sito non
    mantiene. Il `locale` non c'entra e non viene usato: `chiave()` toglie
    accenti e punteggiatura e restituisce solo lettere, quindi l'ordinamento e
    quello dei nomi di `Voce`, non quello italiano di questa macchina.
    """
    voci = sorted(glossario.voci,
                  key=lambda v: (chiave(v.principale_ferrarese or v.ferrarese or ""),
                                 chiave(v.ferrarese or "")))
    fette = []
    for i in range(0, len(voci), VOCI_PER_FETTA):
        numero = len(fette) + 1
        fette.append({
            "numero": numero,
            "file": "glossario-%02d.html" % numero,
            "lettera": _etichetta(numero, voci[i],
                                 voci[min(i + VOCI_PER_FETTA, len(voci)) - 1]),
            "voci": voci[i:i + VOCI_PER_FETTA],
        })
    return fette


def _iniziale(voce) -> str:
    """La lettera da cui comincia la voce, o `#` se non comincia con una.

    Il `#` serve per le forme che cominciano con un apostrofo o un numero:
    senza, la barra avrebbe una voce senza nome e il lettore non saprebbe
    che cos'e'. Resta dichiarato perche' un carattere fuori dall'alfabeto in
    una barra di navigazione sembra un errore di battitura, e invece e' una
    voce che il progetto ha e non sa da che lettera cominciare.
    """
    k = chiave(voce.principale_ferrarese or voce.ferrarese or "")
    if not k or not k[0].isalpha():
        return "#"
    return k[0].upper()


def _etichetta(numero, prima, ultima) -> str:
    """L'etichetta della fetta: il numero e l'intervallo di lettere.

    Sono state provate due etichette e nessuna delle due reggeva da sola.

    La prima era la lettera iniziale, e la barra risultava `A A B C C D D`.
    La seconda era l'intervallo, `A`, `A–B`, `C–D`, e andava meglio — ma non
    abbastanza: una fetta che comincia e finisce dentro la stessa lettera
    riceve `C`, e se ce n'e' un'altra comincia e finisce dentro `C` riceve
    `C` lo stesso. Sarebbero due voci diverse che portano da due parti
    diverse, e chi sceglie «C» non saprebbe quale sta aprendo.

    Quindi il numero c'e' sempre, ed e' l'unica parte dell'etichetta che non
    puo' ripetersi: due voci uguali nella barra significano la stessa cosa.
    Il numero e' anche quello che la pagina dichiara in titolo («fetta 4 di
    21»), quindi non e' un numero nuovo da imparare.
    """
    a = _iniziale(prima)
    b = _iniziale(ultima)
    intervallo = a if a == b else "%s\u2013%s" % (a, b)
    return "%d. %s" % (numero, intervallo)


def _dati_comuni(glossario, corpus, varieta, fonetica, archivio, sintesi,
                 web_dir, audio_disponibili, radice) -> dict:
    """I dati che non dipendono dalla pagina: le fonti, i numeri, i buchi."""
    return {
        "origine": ORIGINE,
        "nomi_varieta": NOMI,
        "varieta": dict(varieta.come_dict(),
                        conteggi=varieta.conteggi(glossario=glossario,
                                                 coppie=corpus.coppie,
                                                 audio=list(archivio))),
        "sintesi_avviso": AVVERTIMENTO_SINTESI,
        # I numeri della home, calcolati qui e non in JavaScript: se la pagina
        # li contasse da sola, un giorno la pagina e il terminale direbbero
        # cose diverse e nessuno saprebbe quale delle due quella giusta.
        "conteggi": {
            "voci": len(glossario.voci),
            "con_fonte": sum(1 for v in glossario.voci if v.fonte),
            "da_verificare": sum(1 for v in glossario.voci if v.da_verificare),
            "coppie": len(corpus.coppie),
            "proverbi": len(corpus.proverbi),
            "regole": 0,
        },
        "buchi": verifica_dati.buchi_dichiarati(glossario, corpus, fonetica),
        "verbi": _verbi(),
        "moderno_buchi": sum(1 for v in glossario.voci if not v.moderno),
        "moderno_con_sinonimi": sum(1 for v in glossario.voci if v.sinonimi),
        "audio": [dict(b.come_dict(),
                       file_playable="audio/" + b.file
                       if b.id in audio_disponibili else "")
                  for b in archivio.brani],
        "sintesi": [dict(s.come_dict(),
                         file_playable=("sintesi/" + s.file)
                         if s.esiste(web_dir) else "")
                    for s in sintesi.suoni],
    }


def _verbi() -> dict:
    """Le forme verbali attestate, per la pagina.

    La chiave che arriva e' la parola **italiana come sta scritta**, non la sua
    chiave normalizzata: la pagina costruisce l'indice con la sua `chiave()`,
    che e' una copia di quella di Python, e se qui si mandasse gia' la chiave
    le due copie potrebbero normalizzare in modo diverso e la ricerca
    fallirebbe in silenzio. Il glossario funziona cosi' e quindi funziona
    anche questo.
    """
    from traduttore import verbi as verbi_modulo
    sa = verbi_modulo.cosa_sa()
    per_italiano = {}
    for riga in verbi_modulo.carica()["righe"]:
        if not (riga.get("italiano") or "").strip():
            continue
        per_italiano.setdefault(riga["italiano"], []).append({
            "forma": riga["forma"],
            "persona": riga.get("persona", ""),
            "tempo": riga["tempo"],
            "fonte": riga["fonte"],
            "dove": riga["dove"],
            "nota": riga.get("nota", ""),
        })
    return {"per_italiano": per_italiano, "forme": sa["forme"],
            "verbi": sa["verbi"],
            "vuoto": [list(v) for v in sa["vuoto"]]}


def _sezioni(modello: str, tenute: tuple) -> str:
    """Il modello con dentro solo le sezioni che questa pagina deve avere.

    Una sezione tolta sparisce dal codice e dal testo insieme: non resta una
    `#tabellaGlossario` vuota, e non resta un `addEventListener` che aggancia
    un elemento che non c'e'. E' il motivo per cui le sezioni sono marcate nel
    modello e non riconosciute dal generatore: il posto in cui si decide cosa
    mettere in una pagina deve essere leggibile da chi apre il modello.
    """
    def via(m: re.Match) -> str:
        return "" if m.group(1) not in tenute else m.group(0)
    # I blocchi sono `<!-- pagina:NOME -->` ... `<!-- /pagina:NOME -->` e
    # possono stare su piu' righe: il confronto e' fra i due, non per riga.
    return re.sub(r"  <!-- pagina:([a-z]+) -->.*?  <!-- /pagina:\1 -->",
                  via, modello, flags=re.S)


def _navigazione(pagina: str) -> str:
    parti = ['<span class="titolo-nav">Pagine</span>']
    for file, testo in NAVIGAZIONE:
        qui = ' class="qui"' if file == pagina else ""
        parti.append('<a href="%s"%s>%s</a>' % (file, qui, testo))
    return "\n    ".join(parti)


REGOLE_ORDINE = ("ortografia", "articoli", "nomi", "verbi", "pronomi",
                 "lessico")

REGOLE_TITOLI = {
    "ortografia": "Come si scrive",
    "articoli": "Gli articoli",
    "nomi": "I nomi e i loro plurali",
    "verbi": "I verbi",
    "pronomi": "Pronomi e aggettivi",
    "lessico": "Le parole",
}


def _fuga(testo: str) -> str:
    """Il testo va nella pagina: `&`, `<` e `>` vanno scappati."""
    return (testo.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def carica_regole_grammaticali(radice: str) -> dict:
    """Le regole della pagina, dal file in `dati/`.

    Se il file manca la pagina esce lo stesso, con un avviso: una pagina
    vuota che spiega perche' e' vuota e' meglio di una pagina che non si
    apre.
    """
    percorso = os.path.join(radice, "dati", "regole_grammaticali.json")
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            return json.load(f)
    except (IOError, ValueError) as errore:
        return {"regole": [], "alfabeto": {}, "errore": str(errore)}


def _pagina_regole(dati: dict) -> str:
    """Le regole diventano html, raggruppate per categoria."""
    if dati.get("errore"):
        return ('<p class="vuoto">Le regole non si sono potute leggere '
                '(%s). Il resto della pagina funziona.</p>'
                % _fuga(dati["errore"]))
    parti = []
    for categoria in REGOLE_ORDINE:
        gruppo = [r for r in dati.get("regole", [])
                  if r.get("categoria") == categoria]
        if not gruppo:
            continue
        parti.append("<h3>%s</h3>" % _fuga(REGOLE_TITOLI[categoria]))
        parti.append('<div class="regole">')
        for regola in gruppo:
            righe = []
            for esempio in regola.get("esempi", []):
                righe.append(
                    '<tr><td class="fe">%s</td><td class="it">%s</td></tr>'
                    % (_fuga(esempio.get("fe", "")),
                       _fuga(esempio.get("it", ""))))
            esempi = ""
            if righe:
                esempi = ('<table class="esempi"><thead><tr>'
                         '<th>ferrarese</th><th>italiano</th></tr></thead>'
                         '<tbody>%s</tbody></table>' % "".join(righe))
            # La fonte si scrive per chi legge, non per il codice: «S015» e'
            # l'identificatore che il registro usa, e a chi sta imparando la
            # lingua non dice niente. L'identificatore resta, nel titolo,
            # per chi deve tornare al registro e capire da dove viene.
            opera = dati.get("opera") or regola.get("fonte", "")
            parti.append(
                '<div class="scheda regola" id="%s">'
                '<h4>%s</h4><p>%s</p>%s'
                '<p class="fonte" title="voce %s del registro delle fonti">'
                '%s, sezione %s</p></div>'
                % (_fuga(regola.get("id", "")),
                   _fuga(regola.get("titolo", "")),
                   _fuga(regola.get("regola", "")), esempi,
                   _fuga(regola.get("fonte", "")), _fuga(opera),
                   _fuga(str(regola.get("sezione", "")))))
        parti.append("</div>")

    alfabeto = dati.get("alfabeto") or {}
    consonanti = alfabeto.get("consonanti") or []
    vocali = alfabeto.get("vocali") or []
    if consonanti or vocali:
        parti.append("<h3>L'alfabeto per capire la pronuncia</h3>")
        parti.append(
            '<p class="occhiello">Non serve per scrivere: serve per capire '
            'che suono ha una parola. A ogni suono corrisponde un solo '
            'carattere, e cos&iacute; non ci sono i digrammi.</p>')
        for titolo, elenco in (("Consonanti", consonanti),
                               ("Vocali", vocali)):
            if not elenco:
                continue
            righe = "".join(
                '<tr><td class="carattere">%s</td><td>%s</td></tr>'
                % (_fuga(v["carattere"]), _fuga(v["suono"])) for v in elenco)
            parti.append('<h4>%s</h4><table class="alfabeto">%s</table>'
                         % (titolo, righe))
    return "\n".join(parti)


def _pagina(modello: str, sezioni: tuple, dati: dict, titolo: str,
            occhiello: str, chiave_pagina: str, file_pagina: str,
            marcatori: dict = None) -> str:
    """Una pagina intera: guscio, sezioni della pagina, navigazione, dati.

    `marcatori` sostituisce nel corpo pezzi di html che il modello non puo'
    scrivere da solo, perche' dipendono dai dati: e' il modo in cui la
    navigazione finisce in tutte le pagine, e il modo in cui questa pagina
    riceve le regole. Un marcatore che nessuno sostituisce resta nel testo
    finale, e per questo il test ne cerca uno.
    """
    testo = _sezioni(modello, sezioni)
    for marcatore, valore in (marcatori or {}).items():
        testo = testo.replace(marcatore, valore)
    testo = testo.replace("<!--NAVIGAZIONE-->", _navigazione(file_pagina))
    # Il titolo e l'occhiello stanno nel corpo e cambiano da pagina a pagina:
    # una pagina che si chiama «Traduttore» e si presenta come «Il progetto»
    # costringe chi ci arriva a indovinare dov'e'.
    testo = re.sub(r"<h1>.*?</h1>",
                   "<h1>%s</h1>" % titolo, testo, count=1, flags=re.S)
    testo = re.sub(r'<p class="occhiello">.*?</p>',
                   '<p class="occhiello">%s</p>' % occhiello, testo,
                   count=1, flags=re.S)
    grezzo = json.dumps(dati, ensure_ascii=False, indent=1)
    # Il JSON va in un elemento di tipo non eseguibile, perche' una voce con
    # la sequenza `</script>` dentro romperebbe la pagina. Il carattere di
    # escape e' la barra rovesciata, che JSON accetta e il browser no dentro
    # un elemento script: e' il modo piu' semplice per non doverlo sostituire.
    grezzo = grezzo.replace("</", "<\\/")
    pagina = testo.replace("/*DATI*/null", grezzo)
    return pagina.replace("<title>Traduttore italiano",
                          "<title>%s &ndash; Traduttore italiano" % titolo) \
        if "<title>Traduttore italiano" in pagina else pagina


def costruisci(radice: str = None, web_dir: str = None) -> list:
    """Genera tutte le pagine e restituisce l'elenco dei file scritti.

    Il valore di ritorno era una stringa (il percorso di `index.html`) e
    adesso e' un elenco: la pagina non e' piu' una, e un sito ramificato che
    si dichiara una pagina sola e' un sito che mente sul proprio contenuto.
    """
    radice = radice or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = web_dir or os.path.join(radice, "web")
    (glossario, corpus, regole, varieta, fonetica, archivio,
     sintesi) = carica_tutto(radice)
    copiati = copia_audio(archivio, os.path.join(radice, "audio"), web_dir)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        modello = f.read()

    regole_grammaticali = carica_regole_grammaticali(radice)
    comuni = _dati_comuni(glossario, corpus, varieta, fonetica, archivio,
                          sintesi, web_dir, copiati, radice)
    comuni["conteggi"]["regole"] = len(regole)

    fette = fette_del_glossario(glossario)
    indice_fette = [{"numero": f["numero"], "file": f["file"],
                     "lettera": f["lettera"]} for f in fette]

    scritte = []

    def scrivi(nome, sezioni, dati, titolo, occhiello, marcatori=None):
        pagina = _pagina(modello, sezioni, dati, titolo, occhiello, nome, nome,
                         marcatori)
        percorso = os.path.join(web_dir, nome)
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(pagina)
        scritte.append((nome, os.path.getsize(percorso)))

    for pagina in PAGINE:
        chiave_p = pagina["chiave"]
        dati = dict(comuni)
        dati["fette"] = indice_fette
        dati["pagina"] = chiave_p
        if chiave_p == "traduttore":
            # Il motore ha bisogno di tutte le parole e di tutti i campi che
            # usa per rispondere. Non ha bisogno del significato moderno ne'
            # della fonte: sono cose che si leggono, e si leggono sulla pagina
            # del glossario. Potarle qui fa risparmiare il 57%.
            dati["glossario"] = _serie(glossario.voci, CAMPI_MOTORE)
            dati["coppie"] = _coppie(corpus)
            dati["proverbi"] = _proverbi(corpus)
            dati["regole"] = _regole(regole)
            # Le trascrizioni IPA sono 11 KB e servono anche qui: senza, la
            # risposta dice «come suona: nessuna parola di questa frase ha
            # ancora una trascrizione» anche quando la frase contiene
            # `portàr`, che ce l'ha. Undici kilobyte per non dire una frase
            # falsa.
            dati["fonetica"] = [t.come_dict() for t in fonetica.trascrizioni]
        elif chiave_p == "frasi":
            dati["coppie"] = _coppie(corpus)
            dati["proverbi"] = _proverbi(corpus)
        elif chiave_p == "regole":
            # La pagina delle regole non ha bisogno di dati nel motore: li
            # scrive sul corpo del documento. Nessun json, nessun motore,
            # nessuna pagina che sparisce se lo scripting e' spento.
            pass
        elif chiave_p == "suoni":
            dati["scontoSuoni"] = {
                "con_suono": sum(1 for s in sintesi.suoni if s.esiste(web_dir)),
                "dichiarate": len(fonetica.trascrizioni),
            }
            # Solo le parole che il progetto sa pronunciare. Le altre 10359
            # non hanno una trascrizione e quindi non hanno niente da
            # ascoltare: mostrarle qui sarebbe una pagina di 10387 «trascrizione
            # assente», cioe' una pagina che dice una cosa sola 10387 volte.
            con_trascrizione = _serie(
                [v for v in glossario.voci if _ha_trascrizione(v, fonetica)],
                CAMPI_TABELLA)
            dati["glossario"] = con_trascrizione
            dati["fonetica"] = [t.come_dict() for t in fonetica.trascrizioni]
            dati["conteggi"]["voci"] = len(con_trascrizione["voci"])
        elif chiave_p == "index":
            dati["fonetica"] = [t.come_dict() for t in fonetica.trascrizioni]
        marcatori = None
        if chiave_p == "regole":
            marcatori = {"<!--REGOLE-->": _pagina_regole(regole_grammaticali)}
        scrivi(pagina["file"], pagina["sezioni"], dati,
               pagina["titolo"], pagina["occhiello"], marcatori)

    for f in fette:
        dati = dict(comuni)
        dati["glossario"] = _serie(f["voci"], CAMPI_TABELLA)
        dati["fette"] = indice_fette
        dati["fetta"] = f["numero"]
        dati["pagina"] = "glossario"
        # I numeri del «significato moderno» qui sono di questa fetta e non
        # del glossario intero. Dire 6324 sotto una tabella di 500 voci
        # sarebbe un numero che non descrive quello che si vede.
        dati["moderno_buchi"] = sum(1 for v in f["voci"] if not v.moderno)
        dati["moderno_con_sinonimi"] = sum(1 for v in f["voci"] if v.sinonimi)
        scrivi(f["file"], ("fette", "glossario"), dati,
               "Glossario &ndash; %s" % f["lettera"].split(". ", 1)[1],
               "Fetta %d di %d: %d voci da %s a %s."
               % (f["numero"], len(fette), len(f["voci"]),
                  scappa_maiuscolo(f["voci"][0]),
                  scappa_maiuscolo(f["voci"][-1])))

    # Le pagine che non esistono piu' non devono restare: una `glossario-99`
    # rimasta dal glossario di ieri fa pensare che ci sia ancora.
    for nome in os.listdir(web_dir):
        if nome.startswith("glossario-") and nome.endswith(".html") \
                and nome not in [f["file"] for f in fette]:
            os.remove(os.path.join(web_dir, nome))
            print("rimossa la pagina che non esiste piu': %s" % nome)

    return scritte


def scappa_maiuscolo(voce) -> str:
    """La prima parola della voce, per il titolo della fetta."""
    testo = voce.principale_ferrarese or voce.ferrarese or voce.italiano or ""
    parola = testo.split(" ")[0] if testo else ""
    return parola or "(senza nome)"


def _ha_trascrizione(voce, fonetica: Fonetica) -> bool:
    """La voce ha una trascrizione dichiarata, per id o per forma.

    Il nome dei due metodi e' quello del modulo `fonetica`: `per_riferimento`
    e `cerca_forma`. Ho scritto prima due nomi che non esistono, e un metodo
    inesistente non falla subito: fallisce quando la riga viene eseguita,
    cioe' solo sulla pagina dei suoni, e solo se qualcuno la apre.
    """
    if fonetica.per_riferimento(voce.id):
        return True
    return bool(fonetica.cerca_forma(voce.ferrarese))


def carica_tutto(radice: str):
    dati = os.path.join(radice, "dati")
    glossario = Glossario.da_file(os.path.join(dati, "glossario.jsonl"))
    corpus = Corpus.da_file(os.path.join(dati, "coppie.jsonl"), os.path.join(dati, "proverbi.jsonl"))
    varieta = Varieta.da_file(os.path.join(dati, "varieta.json"))
    fonetica = Fonetica.da_file(os.path.join(dati, "fonetica.jsonl"))
    archivio = Archivio.da_file(os.path.join(dati, "audio.jsonl"))
    sintesi = Sintesi.da_file(os.path.join(dati, "sintesi.jsonl"))
    percorso_regole = os.path.join(dati, "regole.json")
    regole = []
    if os.path.exists(percorso_regole):
        with open(percorso_regole, "r", encoding="utf-8") as f:
            regole = [morfologia.Regola(**r) for r in json.load(f).get("regole", [])]
    return glossario, corpus, regole, varieta, fonetica, archivio, sintesi


def copia_audio(archivio: Archivio, radice_audio: str, web_dir: str) -> list:
    """Copia in `web/audio/` solo i brani che si possono davvero pubblicare.

    Copiare un brano e' pubblicarlo: e' il punto in cui una registrazione
    fatta in una cucina finisce su un sito pubblico. Per questo la copia non
    guarda il flag `pubblicabile` da solo, e pretende anche il consenso, la
    licenza e il file sul disco. Un brano che non passa non viene copiato e
    la pagina non lo annuncia: non si promette un suono che non c'e'.
    """
    destinazione = os.path.join(web_dir, "audio")
    copiati = []
    for brano in archivio.brani:
        if not brano.publicabile():
            continue
        if not brano.esiste(radice_audio):
            continue
        os.makedirs(destinazione, exist_ok=True)
        shutil.copyfile(brano.percorso(radice_audio),
                        os.path.join(destinazione, os.path.basename(brano.file)))
        copiati.append(brano.id)
    return copiati


if __name__ == "__main__":
    for nome, peso in costruisci():
        print("%-22s %8d byte" % (nome, peso))
