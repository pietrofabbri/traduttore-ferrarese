"""Il significato moderno delle parole, preso da una fonte e non dalla testa.

Una parte del glossario porta nel campo `italiano` parole che un italiano di
oggi non scrive piu': vengono dal Ferri 1889, e il libro glossa con l'italiano
di quell'anno. Chi legge una voce come «ardiglione» o «tortiglione» ha bisogno
di capire di che cosa si parla, e non lo può intuire.

Qui il significato moderno **non viene scritto di testa**. Viene chiesto a una
fonte che lo dichiara, e ogni valore messo nel glossario porta con se' l'indirizzo
dell'articolo da cui e' stato preso. Una riga senza fonte non entra: e' il
controllo che c'e' in `verifica_dati`, e senza di esso questa colonna sarebbe
l'unica del progetto che puo' inventare.

**La fonte.** Wiktionary in italiano, che dichiara la licenza CC BY-SA 4.0 e la
pubblica in modomachine-readable: `w/api.php?action=query&meta=siteinfo&
siprop=rightsinfo`. Non e' il dizionario che uno studente ha sulla scrivania, e
per questo ogni riga dice **da quale fonte** e non parla di authority. E'
comunque una fonte che si può citare, e le sue definizioni sono brevi: il
formato del progetto ne-soffrirebbe di meno.

**Il problema che questo modulo dichiara di non risolvere.** Wiktionary non
marchia le parole obsolete: non esiste un template che dica «questa parola non
si usa piu'». Quindi **non si puo' chiedere alla fonte quale parola e' antica**,
e questo modulo non prova a indovinarlo con la grafia: nessun segno ortografico
distingue «ardiglione», che e' arcaico, da «cane», che non lo e'.

Quindi il modulo fa una cosa piu' modesta e piu' utile: chiede alla fonte il
significato di **tutte** le voci con una sola parola italiana, e tiene la risposta
solo dove dice qualcosa. Il filtro non e' mio, e' della fonte. Il numero di
risposte e' il risultato; il resto resta un buco dichiarato.

**Cosa non viene scritto.** Non viene trovato un sostituto, non viene data una
definizione «di senso comune», e non viene scritta la definizione di una parola
vicina: quello che non c'e' si dichiara, e ogni motivo di vuoto si conta
separato dagli altri.

**Attenzione a `{{Nodef}}`, che vuol dire una cosa sola.** Il template non
significa «questa pagina non ha definizioni»: significa «non le ha **per quel
senso**». In «fungo» c'e' `{{Nodef}}` accanto a «botanica» e le definizioni di
medicina ci sono lo stesso. Quindi il template viene tolto dalla riga e si legge
il resto; se non resta niente, allora e' un vuoto vero e viene detto. La prima
stesura di questo modulo scartava l'articolo intero appena trovava un `{{Nodef}}`
e perdeva parole come «fungo», «arcangelo», «sorriso» e «falda» — cioe' quasi
tutto il glossario, per un motivo che non aveva niente a che fare con quello che
la fonte scriveva. Era una frase nel docstring che descriveva un difetto, non
una regola: il docstring e' stato corretto insieme al codice.

**Cosa viene tagliato, e dichiarato.** In colonna si vedono tre definizioni e
tre sinonimi; nel file ci sono tutti. Il taglio si dichiara perche' una colonna
che mostra tre pezzi senza dire che sono tre sembra mostrarne tre di dieci che
ci sono.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
# Le risposte gia' prese. Non e' un file che entra nel repository: sta in
# `raccolta/lavorato/`, che e' il mezzo e non il risultato. Senza questo, ogni
# prova ripeteva tremila richieste alla fonte, e ogni prova ci metteva venti
# minuti: e il giorno in cui la rete e' assente si finisce con un glossario in
# cui la metta' delle parole ha «la fonte non ha risposto» scritto dentro,
# cioe' un vuoto che mente sul perche' e' vuoto.
CACHE = os.path.join(RADICE, "raccolta", "lavorato", "moderni_risposte.json")

API = "https://it.wiktionary.org/w/api.php"
# Quanti titoli per richiesta. Il massimo dell'API e' 50: andare oltre viene
# rifiutato, e chiedere tutto e' pretendere piu' di quanto la fonte dà.
LOTTO = 50
# Una pausa fra i lotti. Non per cortesia: per non essere l'ennesimo script che
# martella un sito pubblico, e per poter continuare a usarli domani.
PAUSA = 3.0
# La prima stesura chiedeva 40 parole ogni 1,2 secondi e si e' fatta
# bloccare: 95 risposte su 8536 sono arrivate come errore. Se non lo
# avessi detto, sarebbero finite nel glossario come se la fonte non
# avesse l'articolo, e un vuoto perche' hai chiesto troppo spesso e' un
# vuoto falso, che e' peggio di un vuoto vero.
RITENTI = 4

# Che versione del parser ha prodotto la cache. Il numero cambia quando
# cambia il modo in cui il testo della fonte viene letto, e quando cambia
# la cache **non** viene riutilizzata.
#
# Il motivo e' successo: la prima raccolta aveva salvato 8536 risposte lette da
# un parser che scartava l'articolo intero appena trovava un `{{Nodef}}`, e che
# scriveva solo la prima definizione. Il giorno in cui quei due difetti sono
# stati corretti, la cache diceva gia' «risposta» per 8536 parole e la
# correzione non si vedeva. Una cache che non sa con quale regola e' stata
# fatta non e' una cache: e' un posto dove si perdono i dati.
#
# Percio' la versione ci sta, e quando non corrisponde la cache si butta e si
# richiede. Costa venti minuti; il costo opposto e' una colonna sbagliata in
# silenzio, e quella costa di piu'.
VERSIONE_PARSER = 3

# Una parola sola, di lettere e apostrofi. I residui dell'OCR del Ferri non
# entrano: `O- rigliare vn, usolwe` non e' una parola, e chiedere alla fonte
# che cosa significa vuol dire accettare che la fonte indovini.
PAROLA = re.compile(r"^[a-zà-öø-ÿA-ZÀ-ÖØ-Ý][a-zà-öø-ÿA-ZÀ-ÖØ-Ý']{2,}$")


def _api(parametri: dict) -> dict:
    """Una chiamata all'API. Se la fonte non risponde, si dice: non si finge."""
    url = API + "?" + urllib.parse.urlencode(parametri, encoding="utf-8")
    richiesta = urllib.request.Request(
        url, headers={"User-Agent": "traduttore-ferrarese/0.14 (progetto didattico)"})
    with urllib.request.urlopen(richiesta, timeout=45) as risposta:
        return json.loads(risposta.read().decode("utf-8"))


def _sezione_italiana(testo: str) -> str:
    """Solo la sezione `{{-it-}}` dell'articolo.

    Wiktionary mette nella stessa pagina la parola in piu' lingue. Prendere tutto
    il testo prenderebbe anche il francese o l'inglese, che non c'entrano e che
    nessuno ha chiesto.
    """
    inizio = testo.find("{{-it-}}")
    if inizio < 0:
        return ""
    # Il template `{{-it-}}` e' chiuso: finisce dove finisce lui. La prima
    # stesura cercava `|}}`, che appartiene a `{{-sost-|it}}` e ad altri, e
    # tagliava il testo nel posto sbagliato: funzionava per caso, e per caso
    # non va bene in un modulo che scrive dentro i dati.
    resto = testo[inizio + len("{{-it-}}"):]
    # La sezione finisce alla prossima intestazione, **di qualsiasi livello**.
    # La prima stesura cercava `\n==` seguito da un carattere che non fosse
    # `=`, cioe' un'intestazione di secondo livello: su una pagina che annida
    # (`== {{-it-}} ==` con dentro `=== {{-en-}} ===`) l'inglese entrava nella
    # sezione italiana e compariva in colonna accanto all'italiano, senza che
    # nessuno potesse accorgersene guardando la riga. Il difetto e' comparso
    # davvero, in «pizzicato», che mostrava una definizione in inglese.
    prossima = re.search(r"\n=+[^=]", resto)
    return resto[:prossima.start()] if prossima else resto


def _pulito(riga: str) -> str:
    """Una riga di definizione ripulita dei modelli di formattazione.

    Qui si toglie solo la **forma**, non il contenuto: si tolgono i collegamenti
    `[[fibbia]]` diventando `fibbia`, i template che non aggiungono parole, e la
    formattazione. Quello che il dizionario scrive resta scritto.
    """
    testo = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", riga)
    testo = re.sub(r"\[\[([^\]]+)\]\]", r"\1", testo)
    # I template che portano solo qualita' o nota non sono il significato:
    # `{{Term|biologia|it}}` dice il campo, non che cosa vuol dire la parola.
    for prova in (r"\{\{Term\|[^|}]+\|it\}\}", r"\{\{Fonte\|it\}\}",
                  r"\{\{Pn\}\}", r"\{\{Linkp\|[^}]*\}\}", r"\{\{Tabs\|[^}]*\}\}"):
        testo = re.sub(prova, "", testo)
    testo = re.sub(r"\{\{[^}]*\}\}", "", testo)
    testo = re.sub(r"'{2,}", "", testo)
    testo = re.sub(r"\[\d+\]", "", testo)
    testo = testo.replace("&nbsp;", " ").strip()
    return testo.strip(" ,;:")


def _riga_definizione(riga: str) -> str:
    """Il testo di una riga di definizione, o la stringa vuota.

    Nelle pagine di Wiktionary la definizione si riconosce dal `#` iniziale,
    ma **non sempre seguito da uno spazio**: `#{{Nodef|it}}`,
    `#provocare deliberatamente la propria morte` sono forme che la fonte
    scrive davvero. La prima stesura accettava solo `# ` e perdeva quindi
    un pezzo delle definizioni; e accettava anche `#*`, che pero' non e' una
    definizione ma un esempio d'uso.

    La stella viene esclusa perche' un esempio non e' una definizione:
    mostrarla in colonna significa attribuire al dizionario una frase che il
    dizionario ha scritto solo per far capire la parola.
    """
    if not riga.startswith("#") or riga.startswith("#*"):
        return ""
    return _pulito(riga[1:])


# Le righe che la fonte scrive per dire **come si declina** la parola e non
# che cosa significa. Non sono definizioni, e in colonna sono un danno: fanno
# credere che «calunniare» voglia dire «seconda persona singolare
# dell'imperativo di calunniare».
#
# **Perche' si filtra la riga e non la sezione.** Una versione di questo modulo
# tagliava la sezione al primo `{{-...-}}` per escludere le tabelle di
# coniugazione, ed era una correzione che sembrava giusta e non lo era: le
# sotto-sezioni di Wiktionary sono anche **sezioni di significato** —
# `{{-bot-}}`, `{{-med-}}`, `{{-cul-}}` — e in «fungo» le definizioni di
# botanica stanno *dopo* quella intestazione. Tagliando li si perdevano
# proprio le parole che si volevano spiegare, e per far notare che il numero
# era sceso bastava un test su «fungo». Quindi si scarta la **riga** che
# descrive una forma del verbo, e si tiene quella che dice che cosa significa
# la parola, ovunque si trovi nella sezione.
MORFOLOGICI = re.compile(
    r"^(participio|aggettivo|avverbio|sostantivo|verbo|preposizione|"
    r"congiunzione|pronome|interiezione|articolo|locuzione|prefisso|suffisso)\b",
    re.IGNORECASE)

FORME_FLESSIVE = re.compile(
    r"^(prima|seconda|terza|quarta|quinta)\s+persona\b"
    r"|\bpersona (singolare|plurale)\b"
    r"|\b(indicativo|congiuntivo|condizionale|imperativo|participio|"
    r"gerundio|infinito)\b", re.IGNORECASE)


# Le righe che dicono solo **come si scrive e si pronuncia**, non che cosa
# significa. Il pericolo di una regola con `startswith("pronuncia")` e' che
# scarta anche «pronunciare le parole in modo confuso», che invece e' una
# definizione vera: qui si richiede che dopo «pronuncia» ci sia la sigla
# dell'alfabeto fonetico, e basta.
PRONUNCIA = re.compile(r"^pronuncia\s*\(?\s*(afi|ipa)\b|^sillabazione\b",
                       re.IGNORECASE)


def _riga_utilizzabile(pulita: str, parola: str) -> bool:
    """Una riga di definizione che si puo' mostrare, o no.

    Tre scarti, e tutti e tre sono casi che la fonte scrive davvero:
    la riga che ripete la parola («pizzicato» come definizione di
    «pizzicato» non spiega niente), le formule di flessione, e la riga che
    dice soltanto come si pronuncia.
    """
    if not pulita:
        return False
    if pulita.lower().strip(" .;:,") == parola.lower():
        return False
    if MORFOLOGICI.match(pulita):
        return False
    if FORME_FLESSIVE.search(pulita):
        return False
    if PRONUNCIA.match(pulita):
        return False
    return True


# Quante definizioni si mettono in colonna. La fonte ne scrive anche dodici e
# oltre, e con tutte quindici la colonna diventa un muro: il lettore smette di
# leggere al primo periodo. Tre e' il numero oltre il quale la spiegazione non
# guadagna piu' niente, e il taglio si dichiara: il **numero** di definizioni
# che la fonte scrive e' un dato, e se non lo si dichiara una riga con tre
# definizioni sembra una riga con tutte.
DEFINIZIONI_IN_COLONNA = 3


def _significato(testo: str, parola: str = "") -> tuple:
    """La definizione e i sinonimi, come li scrive la fonte.

    Ritorna `(significato, sinonimi, motivo_del_vuoto)`. Quando la fonte
    dichiara che non ha la definizione, il motivo lo dice e il significato resta
    vuoto: e' un'informazione, non un errore.
    """
    sezione = _sezione_italiana(testo)
    if not sezione:
        return ("", [], "l'articolo non ha una sezione italiana")
    # `{{Nodef|it}}` **non** vuol dire che la fonte non ha la definizione: vuol
    # dire che non l'ha per **quel senso**. In «fungo» c'e' `{{Nodef}}` accanto
    # a «medicina» e le definizioni di biologia, gastronomia e meccanica ci
    # sono lo stesso. La prima stesura scartava l'articolo intero appena
    # trovava un `{{Nodef}}` e cosi' perdeva parole come «fungo», «arcangelo»,
    # «sorriso» e «falda»: quasi tutte le parole del glossario, per un motivo
    # che non aveva niente a che fare con quello che la fonte scrive.
    #
    # Quindi `{{Nodef}}` si toglie dalla riga, e se non resta niente la riga
    # non era una definizione. Il vuoto che resta, se resta, e' un vuoto vero:
    # la fonte non ha niente da dire su quel termine.
    definizioni = []
    for riga in sezione.split("\n"):
        pulita = _riga_definizione(riga)
        if _riga_utilizzabile(pulita, parola) and pulita not in definizioni:
            definizioni.append(pulita)
    # **Tutte** le definizioni, non solo la prima, e per un motivo che va
    # detto. Il Wiktionary in italiano non divide gli articoli per parte del
    # discorso: in «mangiare» non c'e' `{{-verb-}}`, e la prima definizione
    # che si trova e' quella del **sostantivo** — «consumazione di cibi a
    # mezzogiorno o a sera» — mentre la voce del glossario e' un verbo. La
    # prima stesura scriveva quella, e nella colonna del significato moderno
    # un verbo ferrarese risultava spiegato come un pranzo.
    #
    # Scegliere il senso giusto richiederebbe di sapere quale parte del
    # discorso sia la parola, e questo progetto non lo sa per tutte le voci:
    # indovinarlo significa mettere in colonna una definizione inventata da
    # me. Quindi si scrive quello che la fonte scrive — tagliato a
    # `DEFINIZIONI_IN_COLONNA`, con il taglio dichiarato — e il lettore vede
    # gli altri sensi, sono la fonte, non una mia scelta.
    #
    # Sul perche' il massimo: la stesura precedente scriveva tutte le
    # definizioni e il risultato era una colonna con significati fino a 1970
    # caratteri, che nessuno legge e che al confronto fanno sembrare vuota
    # la colonna delle altre. Un dato che non si puo' mostrare si puo' solo
    # dichiarare, e la dichiarazione e' il numero.
    if len(definizioni) > DEFINIZIONI_IN_COLONNA:
        definizioni = definizioni[:DEFINIZIONI_IN_COLONNA]
    if not definizioni:
        if re.search(r"\{\{Nodef", sezione):
            return ("", [], "la fonte dichiara di non avere la definizione")
        # Qui la sezione **ha** delle righe di definizione, ma sono tutte forme
        # verbali: in «abbicato» l'unica cosa che la fonte scrive e' «participio
        # passato di abbicare». Dire «la sezione non ha definizioni» sarebbe
        # falso: ne ha, solo che non sono definizioni. Il vuoto e' vero, ma il
        # motivo deve essere quello vero, perche' i due buchi si chiudono in
        # modi opposti — questo chiudendo la pagina della fonte, l'altro solo
        # correggendo la fonte stessa.
        righe = [_riga_definizione(r) for r in sezione.split("\n")]
        righe = [r for r in righe if r]
        if righe:
            return ("", [], "la fonte scrive solo come si declina la parola")
        return ("", [], "la sezione italiana non ha definizioni")

    sinonimi = []
    inizio = sezione.find("{{-sin-}}")
    if inizio >= 0:
        resto = sezione[inizio + len("{{-sin-}}"):]
        # Il blocco finisce alla sezione successiva. Le sezioni sono
        # `{{-sin-}}`, `{{-var-}}` e cosi' via: cercare `{{-` basta, e non si
        # rischia di fermarsi su una parentesi di un altro template.
        fine = resto.find("{{-")
        blocco = resto[:fine] if fine > 0 else resto
        for riga in blocco.split("\n"):
            testo = riga.strip()
            # Le voci sono righe con `*` o `#`. Una riga che non ce l'ha non e'
            # un sinonimo: e' un titolo, un commento o il rumore di un
            # template, e mescolarli ai sinonimi significa mostrare in pagina
            # cose che non sono sinonimi.
            if not testo or testo[0] not in "*#":
                continue
            # `{{Nodef}}` dentro l'elenco dei sinonimi vale come nella
            # definizione: dice che su quel termine la fonte non scrive, e non
            # che il sinonimo sia la parola «Nodef».
            if "Nodef" in testo:
                continue
            pulito = _pulito(testo.lstrip("*#:").strip())
            # La fonte scrive i sinonimi separati da virgola: `[[casalinga]],
            # [[domestica]], donna di casa` sono **tre**, non uno. Leggerli
            # come uno solo faceva comparire in colonna una riga sola con tre
            # parole dentro, che non e' quello che uno studente cerca.
            for pezzo in re.split(r"[,;]", pulito):
                pezzo = pezzo.strip().strip("'\"")
                # Una parentesi aperta o chiusa senza l'altra significa che la
                # fonte scriveva una glossa — «(negli scacchi», «dama) prendere»
                # — e la divisione sulla virgola l'ha spezzata a meta'. Un
                # sinonimo non e' «(negli scacchi»: e' rumore di markup, e
                # metterlo in colonna fa sembrare che il dizionario abbia
                # scritto cosi'.
                if not pezzo or "(" in pezzo or ")" in pezzo:
                    continue
                if any(c in pezzo for c in "{}|="):
                    continue
                # Una frase lunga non e' un sinonimo, e' un esempio: fuori. Il
                # taglio e' sui 60 caratteri perche' il sinonimo piu' lungo che
                # ha senso e' «donna di casa», e il piu' corto che resta fuori e'
                # un esempio d'uso. Sopra questo numero non si sa piu' se
                # quello che la fonte scrive e' un sinonimo o una frase: e
                # quello che non si sa non si mette in colonna.
                if len(pezzo) > 60 or len(pezzo.split()) > 4:
                    continue
                if pezzo not in sinonimi:
                    sinonimi.append(pezzo)
    # Le definizioni si mettono tutte, separate da «; ». Il separatore e' il
    # punto e virgola perche' e' quello che il glossario usa gia' per i resi
    # multipli, e perche' la virgola dentro una definizione e' normale
    # («donna che sbriga faccende domestiche»).
    return ("; ".join(definizioni), sinonimi, "")


def _resi(voce: dict) -> list:
    """I pezzi del campo italiano, come li spezza il glossario."""
    testo = (voce.get("italiano") or "").strip()
    return [p.strip() for p in re.split(r"[,;]", testo) if p.strip()]


def _principale(voce: dict) -> str:
    """La forma da cercare: quella dichiarata, o la prima."""
    principale = (voce.get("principale_italiano") or "").strip()
    resi = _resi(voce)
    if principale:
        return principale
    return resi[0] if resi else ""


def raccogli(glossario: list) -> list:
    """Le voci da chiedere, con la parola da chiedere.

    Si chiede **una** parola per voce: quella dichiarata come principale, o la
    prima. Chiedere tutte le voci sarebbe chiedere due volte la stessa parola,
    e il glossario ha parole che compaiono in molte voci: la fonte risponderebbe
    la stessa cosa cinque volte, e la tabella mostrerebbe cinque volte la stessa
    definizione, che non e' quello che si voleva vedere.
    """
    da_chiedere = []
    viste = set()
    non_parole = 0
    for voce in glossario:
        parola = _principale(voce)
        if not parola:
            continue
        if not PAROLA.match(parola):
            non_parole += 1
            continue
        chiave = parola.lower()
        if chiave in viste:
            continue
        viste.add(chiave)
        # Si chiede la parola **in minuscolo**. Il Ferri scrive «Giustizia»,
        # «Combattere», «Piatto» con l'iniziale maiuscola, e il Wiktionary in
        # italiano scrive invece «giustizia», «combattere», «piatto»: non e' una
        # convenzione, e' il fatto che in italiano le voci sono minuscole. La
        # prima stesura mandava la parola come stava nel glossario e la fonte
        # rispondeva, correttamente, che l'articolo non esisteva: 8795 vuoti su
        # 8536 parole, cioe' una fonte che sembrava non sapere niente quando
        # sapeva tutto. Il maiuscolo iniziale viene rimesso al suo posto solo
        # quando si scrive l'indirizzo dell'articolo.
        da_chiedere.append(parola.lower())
    return da_chiedere, non_parole


def _cache() -> dict:
    try:
        with open(CACHE, encoding="utf-8") as f:
            letta = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(letta, dict):
        return {}
    if letta.get("versione") != VERSIONE_PARSER:
        # Il file c'e' ma e' stato scritto da un'altra versione del parser:
        # non si puo' sapere che cosa contiene, quindi non si usa.
        return {}
    return letta.get("risposte") or {}


def _salva_cache(risposte: dict) -> None:
    """Scrive la cache senza lasciare mezzo file.

    Il file si scrive in un altro nome e poi si rinomina: la rinomina e' una
    operazione che o c'e' o non c'e'. Scrivere diretto invece lascia, se il
    processo muore mentre scrive, un file troncato — e un file troncato si
    legge come «la fonte non ha nessuna risposta», cioe' come se le 8500
    parole non fossero mai state chieste. Perdere la cache costa venti minuti;
    perderla in silenzio costa una colonna vuota che nessuno spiega.

    Inoltre le risposte nuove si sommano a quelle gia' sul file, e non lo
    sostituiscono: cosi' due raccolte in contemporanea non si cancellano a
    vicenda.
    """
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tutto = _cache()
    tutto.update(risposte)
    provvisorio = CACHE + ".provvisorio"
    with open(provvisorio, "w", encoding="utf-8") as f:
        json.dump({"versione": VERSIONE_PARSER, "risposte": tutto}, f,
                  ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(provvisorio, CACHE)


def chiedi(parole: list) -> dict:
    """Le risposte della fonte, in lotti.

    Ritorna un dizionario `parola -> (significato, sinonimi, motivo)`, gia'
    letto dal wikitext. Una parola che la fonte non conosce ha motivo «la
    fonte non ha l'articolo», che e' una risposta, non un errore: vuol dire che
    quel vuoto e' della fonte.
    """
    risposte = _cache()
    # Solo le risposte riuscite si mettono in cache. Un errore di rete non e'
    # una risposta della fonte e non deve diventare un vuoto permanente: la
    # prossima esecuzione lo riprova, e questa volta se la rete c'e' lo trova.
    da_chiedere = [p for p in parole if p.lower() not in risposte]
    print("gia' in cache: %d, da chiedere: %d" % (len(parole) - len(da_chiedere),
                                                  len(da_chiedere)))
    parole = da_chiedere
    if not parole:
        # Niente da chiedere: si rilegge quello che c'e' e si esce. Il percorso
        # del ritorno e' lo stesso di quando la rete ha risposto, altrimenti
        # «rileggi la cache» e «rileggi la cache dopo aver scritto» darebbero
        # due risultati diversi per gli stessi dati.
        return _letto(risposte)
    nuove = {}
    lotti = (len(parole) + LOTTO - 1) // LOTTO
    for numero, inizio in enumerate(range(0, len(parole), LOTTO), 1):
        lotto = parole[inizio:inizio + LOTTO]
        dati = None
        ultimo = ""
        for tentativo in range(RITENTI + 1):
            try:
                dati = _api({
                    "action": "query",
                    "prop": "revisions",
                    "rvslots": "main",
                    "rvprop": "content",
                    "titles": "|".join(lotto),
                    "redirects": "1",
                    "format": "json",
                    "formatversion": "2",
                })
                break
            except Exception as errore:  # rete assente, fonte stanca
                ultimo = str(errore)
                if "429" in ultimo or "Too Many" in ultimo:
                    # La fonte ha detto «piano»: si aspetta e si riprova.
                    time.sleep(PAUSA * (2 ** tentativo))
                    continue
                break
        if dati is None:
            # Il lotto **non** va in cache. Un errore di rete non e' una
            # risposta della fonte: se finisse in cache diventerebbe, per
            # sempre, un vuoto con la scritta «la fonte non ha l'articolo»,
            # che e' falso. Torna al primo giro e lo riprova.
            print("  lotto %d/%d: la fonte non ha risposto (%s)" % (
                numero, lotti, ultimo[:80]), flush=True)
            continue
        pagine = (dati.get("query") or {}).get("pages") or []
        per_titolo = {}
        for pagina in pagine:
            titolo = pagina.get("title", "")
            if "missing" in pagina:
                per_titolo[str(titolo).lower()] = (
                    "", "la fonte non ha l'articolo")
                continue
            revisioni = pagina.get("revisions") or []
            testo = ""
            if revisioni:
                testo = revisioni[0].get("slots", {}).get("main", {}).get("content", "")
            # In cache finisce il **wikitext grezzo**, non il risultato della
            # lettura. La ragione e' che il parser e' stato sbagliato tre volte
            # e ogni volta la correzione costava un'ora di rete: con il testo
            # in cache, la correzione costa un secondo. Il file e' grande
            # (qualche decina di megabyte) e sta in `raccolta/lavorato/`, che
            # non entra nel repository: e' il mezzo, non il risultato.
            per_titolo[str(titolo).lower()] = (testo or "", "")
        for parola in lotto:
            trovato = per_titolo.get(
                parola.lower(),
                ("", "la fonte ha risposto ma non c'era il titolo"))
            # In cache finisce **tutto** quello che la fonte ha risposto,
            # compresa la risposta «non ho l'articolo». Un articolo che non
            # esiste e' una risposta della fonte, non un errore: domandarlo
            # domani darebbe la stessa risposta, e senza questa distinzione
            # ogni esecuzione ripeteva tutte le parole assenti e la raccolta
            # non finiva mai. Quello che va escluso e' il solo errore di rete,
            # e quello non arriva qui: il lotto intero viene saltato prima.
            risposte[parola.lower()] = trovato
            nuove[parola.lower()] = trovato
        _salva_cache(nuove)
        print("  lotto %d/%d, %d in cache" % (numero, lotti, len(risposte)),
              flush=True)
        if inizio + LOTTO < len(parole):
            time.sleep(PAUSA)
    return _letto(risposte)


def _letto(grezzo: dict) -> dict:
    """Il wikitext diventa significato, qui e non in `chiedi`.

    La separazione serve a una cosa sola: poter correggere il parser senza
    chiedere niente alla fonte. Il file di cache tiene il testo; questa
    funzione lo rilegge; se le due cose fossero la stessa, ogni correzione
    richiederebbe di buttar via la cache e di rifare un'ora di richieste.
    """
    risposte = {}
    for parola, grezzo_riga in grezzo.items():
        if isinstance(grezzo_riga, (list, tuple)) and len(grezzo_riga) == 2 \
                and isinstance(grezzo_riga[0], str):
            testo, motivo = grezzo_riga
            risposte[parola] = _significato(testo, parola) if testo \
                else ("", [], motivo)
        else:
            # Una riga scritta da una versione diversa del modulo non e' un
            # formato che questo sa leggere, e indovinare quale fosse e' peggio
            # che dichiararlo.
            raise ValueError("formato di cache non riconosciuto per %r" % parola)
    return risposte


def _indice_url(parola: str) -> str:
    """L'indirizzo dell'articolo: la fonte della voce, non la fonte della pagina."""
    return ("https://it.wiktionary.org/wiki/"
            + urllib.parse.quote(parola.replace(" ", "_")))


def applica(risposte: dict, scrivi: bool) -> dict:
    """Mette le risposte nel glossario, e conta tutto quello che resta fuori.

    Il file e' stato scritto in due modi diversi, in due momenti diversi della
    sua storia: 10363 righe con i separatori di default di `json.dumps` (con lo
    spazio dopo i due punti) e 24 righe compatte. La prima stesura di questo
    modulo le ha normalizzate **tutte** alle compatte, e il diff ha mostrato
    10379 righe modificate invece delle 4063 che avevano un campo nuovo: un
    diff cosi' non dice niente, perche' obbliga a controllare a mano ogni riga
    per capire se e' cambiato qualcosa o solo come e' scritta.

    Quindi ogni riga viene riscritta **come era**: se aveva lo spazio, torna
    con lo spazio. Il diff mostra allora solo le righe in cui il contenuto
    e' cambiato, che e' l'unica cosa che un diff deve mostrare.
    """
    voci = []
    spazi = []
    with open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.rstrip("\n")
            if riga.strip() and not riga.lstrip().startswith("//"):
                voci.append(json.loads(riga))
                spazi.append('": ' in riga)
            else:
                voci.append(riga)
                spazi.append(False)

    conto = {"riempite": 0, "con_sinonimi": 0, "vuote": 0, "parole": 0}
    motivi = {}
    nuove = []
    for voce in voci:
        if isinstance(voce, str):
            nuove.append(voce)
            continue
        parola = _principale(voce)
        if not parola or parola.lower() not in risposte:
            nuove.append(voce)
            continue
        conto["parole"] += 1
        significato, sinonimi, motivo = risposte[parola.lower()]
        if significato:
            conto["riempite"] += 1
            if sinonimi:
                conto["con_sinonimi"] += 1
            voce["moderno"] = significato
            voce["fonte_moderno"] = _indice_url(parola.lower())
            if sinonimi:
                voce["sinonimi"] = sinonimi
        else:
            conto["vuote"] += 1
            motivi[motivo] = motivi.get(motivo, 0) + 1
        nuove.append(voce)

    if scrivi:
        with open(GLOSSARIO, "w", encoding="utf-8") as f:
            for voce, con_spazi in zip(nuove, spazi):
                # `None` come separatore riproduce i separatori di default,
                # che sono quelli delle 10363 righe; la tupla compatta serve
                # alle 24 righe che erano state scritte cosi'. Vedi la nota
                # sopra: la scelta non e' un gusto, e' la differenza fra un
                # diff che si legge e un diff da 10000 righe.
                separatori = None if con_spazi else (",", ":")
                f.write((voce if isinstance(voce, str)
                         else json.dumps(voce, ensure_ascii=False,
                                          separators=separatori)) + "\n")
    conto["motivi"] = motivi
    return conto


def _leggi_righe() -> list:
    righe = []
    with open(GLOSSARIO, encoding="utf-8") as f:
        for riga in f:
            riga = riga.rstrip("\n")
            righe.append(json.loads(riga) if (riga.strip()
                                              and not riga.lstrip().startswith("//"))
                         else riga)
    return righe


LOG = os.path.join(RADICE, "raccolta", "lavorato", "moderni_log.txt")


def _sgancia() -> None:
    """Fa continuare la raccolta anche se questa shell muore.

    La raccolta dura piu' di un'ora e la shell che la lancia no. Il processo
    viene staccato dal gruppo della shell con un doppio fork e `setsid`, e da
    quel momento non e' piu' figliuolo di niente: chi chiude il terminale non
    lo tocca. Non e' una scorciatoia per evitare di aspettare, e' l'unico modo
    per eseguire un lavoro lungo da uno strumento che ha un tempo massimo.

    Il primo fork e il secondo servono perche' `setsid` fallisce se il
    processo e' gia' un capogruppo: il primo fork crea un figlio che non lo e',
    il secondo crea un nipote che puo' diventare capogruppo della sessione
    nuova. Le due uscite `os._exit` servono a non far girare il resto del
    programma nei figli che stanno per uscire.
    """
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    # Dopo i due fork non c'e' piu' nessun terminale: senza questo redirect
    # ogni scrittura su stdout fallisce con `OSError` e uccide la raccolta.
    log = open(LOG, "a", encoding="utf-8")
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    os.chdir(RADICE)
    log.write("--- raccolta sganciata %s ---\n" % time.strftime("%H:%M:%S"))
    log.flush()
    # Il processo sganciato ha perduto l'opzione `-u` della riga di comando.
    # Senza questo, il log resta vuoto per un'ora e sembra che la raccolta sia
    # ferma quando sta solo aspettando che il buffer si riempia.
    sys.stdout.reconfigure(line_buffering=True)


def main() -> int:
    scrivi = "--scrivi" in sys.argv
    if "--daemon" in sys.argv:
        _sgancia()
    righe = _leggi_righe()
    voci = [r for r in righe if not isinstance(r, str)]
    da_chiedere, non_parole = raccogli(voci)
    print("voci nel glossario            %d" % len(voci))
    print("parole distinte da chiedere   %d" % len(da_chiedere))
    print("voci scartate perche' la forma non e' una parola: %d" % non_parole)
    print()
    print("chiedo alla fonte, in lotti da %d, con una pausa di %.1fs"
          % (LOTTO, PAUSA))
    print("(serve la rete: e' l'unico punto di questo progetto che la usa, e la")
    print(" usa per chiedere, non per scaricare un vocabolario di nascosto)")
    print()
    risposte = chiedi(da_chiedere)
    conto = applica(risposte, scrivi)
    print("risposte con significato       %d" % conto["riempite"])
    print("  di cui con sinonimi         %d" % conto["con_sinonimi"])
    print("risposte vuote                 %d" % conto["vuote"])
    print()
    if conto["motivi"]:
        print("perche' sono vuote:")
        for motivo, quante in sorted(conto["motivi"].items(),
                                     key=lambda p: -p[1]):
            print("  %5d  %s" % (quante, motivo))
    print()
    print("scritto sul glossario: %s" % ("si" if scrivi else "no (prova)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())