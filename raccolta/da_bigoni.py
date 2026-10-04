#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porta il vocabolario di Bigoni dentro `dati/glossario.jsonl`.

`bigoni.py` raccoglie e basta: mette 7307 coppie in un file grezzo e non
toca il glossario, perche' una voce non si diventa voce perche' e' stata
raccolta. Questo script e' il passo dopo, e fa tre cose e non una quarta:

1. **non duplica**: confronta ogni coppia con il glossario attivo e lascia
   fuori quello che c'e' gia';
2. **dichiara**: ogni voce che scrive porta la fonte, la `varieta` e il
   numero della riga da cui viene, e porta `da_verificare: true`, perche'
   nessuno di queste righe e' stata confrontata con un libro;
3. **segnala e non decide**: quello che non sa risolvere — le voci che
   somigliano a un'altra senza essere la stessa, i disaccordi fra S006 e il
   Ferri — lo stampa e lo lascia a chi guarda.

Il quarto passo che questo script **non** fa e' scegliere quale delle due
fonti abbia ragione quando dicono cose diverse. Il controllo segnala; la
correzione la fa una persona.

Uso:
    python3 raccolta/da_bigoni.py --prova     # dice cosa farebbe, non scrive
    python3 raccolta/da_bigoni.py             # scrive

Idempotente: due giri producono lo stesso file, e il secondo giro scrive
zero righe perche' trova tutto gia' dentro. E' la stessa proprieta' che
`bigoni.py` ha e che `sintetizza.py` ha, e serve a una cosa sola: un file
generato che cambia a ogni giro e' un file di cui non ci si fida.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore.normalizza import chiave  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copertura import FUNZIONALI  # noqa: E402

GREZZO = os.path.join(RADICE, "raccolta", "grezzi",
                      "bigoni_ferrarese_italiano.jsonl")
GLOSSARIO = os.path.join(RADICE, "dati", "glossario.jsonl")
VARIETA = os.path.join(RADICE, "dati", "varieta.json")

# La fonte, per voce. `S006` e' l'id del registro: chi legge la voce trova
# il nome, l'indirizzo e la licenza andando avanti di una riga, e non deve
# fidarsi di una stringa scritta qui.
ID_FONTE = "S006"
AUTORE = "Roberto Bigoni"
SITO = "https://www.robertobigoni.it/Servizi/Ferrarese/"
SCRIPT = "elencoParoleFerraresiPerLettera.php"

# La varieta' non e' scritta qui. `dati/varieta.json` la dichiara per fonte,
# con il motivo per cui e' stata scelta e con quanto e' documentata: se la
# fonte non distingue le cinque varieta' la scelta resta **nostra** e viene
# dichiarata come memoria (`M`), non come fatto documentato (`D`).
# Scrivere `cittadino` in questo file sarebbe una parola in piu' da
# mantenere e un posto in piu' in cui la dichiarazione puo' divergere da
# quella vera.
CODICE_VARIETA_ATTESA = "cittadino"

# L'attendibilita' delle voci che arrivano da qui e' `I`, **non** `D`, e la
# ragione sta nel project's stessi termini: `D` vuol dire «cito una fonte che
# si puo' aprire e controllare», e qui la fonte si puo' aprire ma nessuno ha
# controllato che la riga letta corrisponda a quello che c'e' scritto. Lo
# dichiarare `D` sarebbe dichiarare una verifica che non e' avvenuta, e il
# controllo **G7** lo segnalerebbe — 6426 volte, cio' un avviso per voce e
# un controllo che smette di dire niente.
#
# Le 209 voci del Ferri che sono `D` lo sono perche' qualcuno le ha aperte
# sul libro alla pagina indicata; le altre 10156 dello stesso Ferri, che
# vengono dall'OCR e nessuno ha riletto, sono `I`. Queste 6426 sono dalla
# seconda specie: raccolte dalla pagina, non confrontate con niente.
#
# Il `fonte` c'e' lo stesso, quindi la voce rimane verificabile da chi
# vuole: la fonte e' dichiarata per voce con il numero della riga, e aprirla
# basta. `I` non vuol dire «non so dove viene», vuol dire «so dove viene e
# non l'ho ancora controllata».
ATTENDIBILITA = "I"


def varieta_dichiarata(percorso: str, id_fonte: str) -> dict:
    """La riga di `dati/varieta.json` che riguarda questa fonte.

    Se non c'e', il problema non e' un avviso: e' una voce che entra nel
    glossario senza che nessuno abbia detto in quale dei cinque territori
    vale, e il controllo G8 la rifiuterebbe subito dopo. Meglio fermarsi
    qui, dove si puo' spiegare, che produrre 6383 righe da scartare.
    """
    if not os.path.exists(percorso):
        raise SystemExit("manca dati/varieta.json: la varieta' non si indovina")
    with io.open(percorso, encoding="utf-8") as f:
        grezzo = json.load(f)
    for assegnazione in grezzo.get("assegnazioni", []):
        if assegnazione.get("fonte") == id_fonte:
            return assegnazione
    raise SystemExit(
        "dati/varieta.json non dichiara la varieta' per %s: senza quella riga "
        "le voci non sanno a chi servire, e il progetto non indovina"
        % id_fonte)


def carica_grezzo(percorso: str) -> list:
    """Le coppie raccolte, in numero di fonte.

    Il numero e' la posizione nella fonte e serve a due cose: tiene
    l'ordine stabile fra due giri, e permette a chi legge una voce di
    sapere dove cercarla sul sito senza dover cercare la parola fra 7307.
    """
    if not os.path.exists(percorso):
        raise SystemExit(
            "manca %s: prima si raccoglie, con `python3 raccolta/bigoni.py`.\n"
            "Il grezzo non e' nel repository per scelta (sono 1,3 MB che si "
            "ricreano con una riga), quindi questo script non puo' andare "
            "avanti da solo." % os.path.relpath(percorso, RADICE))
    voci = []
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip():
                continue
            voce = json.loads(riga)
            if "numero" not in voce or "ferrarese" not in voce:
                raise SystemExit("riga del grezzo senza numero o parola: %r"
                                 % voce)
            voci.append(voce)
    voci.sort(key=lambda v: v["numero"])
    return voci


def voci_attive(percorso: str) -> list:
    if not os.path.exists(percorso):
        raise SystemExit("manca dati/glossario.jsonl")
    voci = []
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.lstrip().startswith("//"):
                continue
            voci.append(json.loads(riga))
    return voci


def prossimo_id(voci: list, prefisso: str = "V") -> int:
    """Il primo id libero.

    Si guarda **tutto** il glossario, non solo le ultime righe: gli id non
    sono in ordine e una riga aggiunta a mano in mezzo puo' avere un numero
    piu' alto di tutte quelle scritte in seguito. Partire dal massimo
    dell'ultima riga sbaglierebbe di niente e romperebbe la G2.
    """
    maggiore = 0
    for voce in voci:
        identificatore = voce.get("id", "")
        if identificatore.startswith(prefisso) and identificatore[1:].isdigit():
            maggiore = max(maggiore, int(identificatore[1:]))
    return maggiore + 1


def id_in_attesa() -> int:
    """Il massimo degli id che vivono nella fila d'attesa.

    Difetto vero, di questa sessione, e uno di quelli che il progetto chiama
    per nome: `prossimo_id()` guardava **solo** il glossario attivo, e la
    fila d'attesa di `dati/da_verificare/glossario.jsonl` contiene cinque id
    (`V10400`-`V10404`) piu' alti di tutti quelli attivi. Il generatore ha
    quindi cominciato a scrivere da `V10390` e ha **ridescritto quei cinque
    id**: non le voci in attesa, che non si toccano, ma i numeri.

    L'errore e' arrivato solo dopo, dal controllo **D1**, che fa esattamente
    il suo lavoro: «id in attesa di verifica e anche nei dati attivi». Il
    guaio e' che il generatore aveva prodotto 6426 righe prima che qualcuno
    guardasse, e D1 le ha respinte tutte insieme: una collisione di cinque
    numeri blocca il lavoro di settimila voci.

    Un id non e' un contatore: e' un'identita' che due file diversi si
    contendono. Per questo il prossimo id si calcola sui due file insieme, e
    non su quello che si sta scrivendo.
    """
    maggiore = 0
    percorso = os.path.join(RADICE, "dati", "da_verificare", "glossario.jsonl")
    if not os.path.exists(percorso):
        return maggiore
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            if not riga.strip() or riga.lstrip().startswith("//"):
                continue
            identificatore = json.loads(riga).get("id", "")
            if identificatore.startswith("V") and identificatore[1:].isdigit():
                maggiore = max(maggiore, int(identificatore[1:]))
    return maggiore


def fonte_voce(numero: int) -> str:
    """La fonte di una voce, con il numero della riga da cui viene.

    Il numero non e' un vezzo: senza di lui la voce dice «viene da Bigoni»
    come 7306 altre, e chi trova un errore non sa dove guardare. Con il
    numero, il rimando porta alla riga esatta.
    """
    return ("%s, vocabolario ferrarese-italiano (%s), voce n. %d "
            "(%s%s)" % (AUTORE, ID_FONTE, numero, SITO, SCRIPT))


def nota_voce(voce: dict, gemelli: int) -> str:
    """La nota: quello che la fonte dice e che nessun altro campo porta.

    - l'**etimologia** e' dichiarata dalla fonte, non verificata: e' la
      ricostruzione di Bigoni, e il progetto non la dà per documentata;
    - il **numero di gemelli** dice se la stessa parola ferrarese compare
      piu' di una volta nella fonte con altri significati. E' un fatto
      dichiarato, non un errore: sono omonimi, e il sito li distingue con un
      suffisso numerato che non entra nella parola.
    """
    parti = []
    etimologia = (voce.get("etimologia") or "").strip()
    if etimologia:
        parti.append("Etimologia dichiarata dalla fonte: %s. Non verificata: "
                     "e' la ricostruzione dell'autore, non un fatto accertato."
                     % etimologia)
    if voce.get("omonimo") is not None:
        parti.append("Il sito distingue questa voce da un'altra con lo stesso "
                     "significato con il suffisso %d: sono due omonimi."
                     % voce["omonimo"])
    if gemelli > 1:
        parti.append("La stessa parola ferrarese compare %d volte nella "
                     "fonte con significati diversi." % gemelli)
    if not parti:
        parti.append("Raccolta meccanica dalla pagina della fonte, non "
                     "confrontata con un libro: resta da verificare.")
    return " ".join(parti)


# Le chiavi delle parole funzionali, calcolate una volta sola: `chiave()`
# rifarebbe lo stesso lavoro 7307 volte e la lista ha oltre duecento voci.
_CHIAVI_FUNZIONALI = frozenset(chiave(f) for f in FUNZIONALI)


def funzionale(voce: dict) -> bool:
    """Se questa riga non deve diventare voce, e perche'.

    Il caso e' semplice e la regola no, quindi vanno detti entrambi.

    **La regola**: gli articoli e le preposizioni non sono voci. Il progetto
    lo dichiara da sempre e lo dichiara in tre posti (`copertura.py`,
    `costruisci_meccanico.py` e il test `TestCopertura`), e i test lo
    fanno fallire se una di loro finisce nel glossario.

    **Il caso**: Bigoni porta due righe che la toccano, ed hanno lati
    opposti.

    - `al` = «il»: e' una funzionale **da entrambe le parti**. La parola
      ferrarese `al` non e' un articolo, e la sua traduzione non porta
      niente: e' rumore.

    - `kóŋ` = «con»: la parola ferrarese e' una voce **vera** e utile:
      traduce `kóŋ` in italiano e viceversa — ma la sua traduzione e' una
      funzionale. Il glossario la indicizzerebbe dal lato italiano, e da li'
      il motore troverebbe «con» e la tradurrebbe in `kóŋ` dentro una frase
      dove l'inglese del motore ha gia' deciso che «con» e' un casoso
      terminale. Il test `TestCopertura` lo dice esplicitamente: `con` non
      deve trovarsi fra le traduzioni, «aggiorna la dichiarazione sulle
      funzionali».

    Quindi il filtro guarda **la traduzione**, non la parola ferrarese: e' il
    lato che il glossario indicizza e che il motore usa per costruire la
    frase. Una voce ferrarese di una funzionale non si perde: la parola
    ferrarese resta nel vocabolario di S006, che e' la fonte, e il glossario
    non e' il posto dove si tengono le parole che il motore non deve usare.

    Un filtro che guardasse la parola ferrarese avrebbe scartato anche
    `kóŋ`, che e' esattamente la voce che si voleva. Sarebbe passato lo
    stesso test e avrebbe perso la parola: un filtro che fa passare il
    controllo senza fare il suo lavoro e' peggio di nessun filtro.
    """
    significati = (voce.get("significati") or "").strip()
    if not significati:
        return True
    # Tutti i significati, non solo il primo: `n.2159` porta «fico (albero)»
    # e nessuna delle due meta' e' una funzionale, mentre una riga con
    # «in, dentro» va scartata perche' uno dei due lo e'.
    return any(chiave(parte) in _CHIAVI_FUNZIONALI
               for parte in significati.split(",") if parte.strip())


def confronta(voci_raccolte: list, attive: list) -> dict:
    """Cosa succede a ogni coppia, e in cinque esiti.

    I cinque esiti sono distinti perche' richiedono azioni diverse, e
    confonderli e' il modo di perdere informazione senza accorgersene:

    - `nuove`: la parola non c'e' nel glossario. Va aggiunta;
    - `gia_presenti`: la parola c'e' gia' **con lo stesso significato**.
      Due righe che dicono la stessa cosa non sono due voci: aggiungerle
      farebbe doppioni e gonfierebbe il conto di 591 righe senza portare
      niente;
    - `disaccordi`: la parola c'e' gia' ma **con un significato diverso**.
      Qui nessuno sceglie: il disaccordo fra due fonti si stampa e resta,
      perche' decidere quale abbia ragione e' lavoro di una persona (V0520
      «Anel»: il Ferri dice anello e Bigoni agnello, e nessuno dei due
      numeri dice quale dei due sia il ferrarese);
    - `doppie`: due righe della stessa fonte con la stessa parola e lo
      stesso significato, cioe' la stessa voce scritta due volte. Se ne
      tiene una e si dice quante erano;
    - `funzionali`: la parola e' un articolo o una preposizione. Non entra
      e non e' un errore: sono gia' in `morfologia.py`, e vederle nel
      glossario e' il modo di toglierle al motore.
    """
    per_chiave = {}
    for voce in attive:
        per_chiave.setdefault(chiave(voce.get("ferrarese", "")), []).append(voce)

    esiti = {"nuove": [], "gia_presenti": [], "disaccordi": [], "doppie": [],
             "funzionali": []}
    visti = {}
    for voce in voci_raccolte:
        k = chiave(voce["ferrarese"])
        if funzionale(voce):
            esiti["funzionali"].append(voce)
            continue
        # L'ordine dei due confronti e' **il punto**, ed e' stato invertito
        # due volte in questa sessione.
        #
        # Prima si guardava `visti` (la fonte) e solo dopo l'attivo. Al
        # secondo giro una riga che era stata scartata come seconda di un
        # gruppo (un omonimo, o una doppia) non veniva piu' cercata
        #nell'attivo, e il generatore la riscriveva: **194 righe duplicate**
        #di parole che aveva scritto lui stesso un giro prima.
        #
        # Adesso si guarda **prima** l'attivo, che e' la verita' — e se la
        # voce c'e' gia' li', non si riscrive, qualunque cosa abbia fatto la
        # fonte con quella parola. Solo se non c'e' si chiede se la fonte la
        # sta ripetendo. E' l'unico ordine che rende il secondo giro zero.
        gia = per_chiave.get(k)
        if gia:
            coincidenti = [v for v in gia
                           if chiave(v.get("italiano", "")) == chiave(
                               voce.get("significati") or "")]
            if coincidenti:
                esiti["gia_presenti"].append((coincidenti[0], voce))
                continue
            if len(gia) > 1 or any(
                    chiave(v.get("italiano", "")) != chiave(
                        voce.get("significati") or "") for v in gia):
                esiti["disaccordi"].append((voce, gia))
                continue
        if k in visti:
            prima = visti[k]
            if (prima.get("significati") or "") == (voce.get("significati") or ""):
                esiti["doppie"].append((prima, voce))
                continue
            # Stessa parola, significati diversi: due omonimi della fonte.
            # Entrano come due voci, ognuna con la sua: e' quello che la
            # fonte scrive, e unire i due significati sarebbe una scelta.
            esiti["nuove"].append(voce)
            continue
        visti[k] = voce
        if not gia:
            esiti["nuove"].append(voce)
            continue
        # Piu' voci attive con la stessa chiave: e' il caso normale, non
        # l'eccezione. Ferri porta le parole in due righe (`Aldam` = letame e
        # `Aldamar` = letamaio sono parole diverse, ma `Alvar` = levare e
        # `Alvar` = sollevare sono la stessa parola con due sensi), e Bigoni
        # fa lo stesso. Quindi la domanda non e' «c'e' piu' di una?» ma
        # «c'e' piu' di una che dica **questa**?».
        #
        # Difetto vero, di questa sessione: la versione precedente trattava
        # `len(gia) > 1` come un caso da segnalare, e al secondo giro il
        # generatore scriveva **194 righe duplicate** di parole che aveva
        # scritto lui stesso un minuto prima. Il sintomo non era nel
        # glossario — le righe erano ben formate — ma nel fatto che uno
        # script che riscrive quello che ha gia' scritto non e' uno script
        # su cui si puo' contare: il secondo giro doveva essere zero.
        #
        # Il confronto si fa quindi voce per voce, e una voce che coincide
        # esattamente chiude la fila. Se nessuna coincide, e' un disaccordo
        # e non si sceglie: `V0520` dice «anello» e Bigoni dice «agnello» per
        # la stessa `anèl`, e quale delle due sia giusta lo decide una
        # persona guardando le due fonti.
        coincidenti = [v for v in gia
                       if chiave(v.get("italiano", "")) == chiave(
                           voce.get("significati") or "")]
        if coincidenti:
            esiti["gia_presenti"].append((coincidenti[0], voce))
            continue
        if len(gia) > 1:
            esiti["disaccordi"].append((voce, gia))
            continue
        esistente = gia[0]
        if chiave(esistente.get("italiano", "")) == chiave(
                voce.get("significati") or ""):
            esiti["gia_presenti"].append((esistente, voce))
        else:
            esiti["disaccordi"].append((voce, gia))
    return esiti


def gemelli_per_chiave(voci_raccolte: list) -> dict:
    """Quante volte la stessa parola ferrarese compare nella fonte."""
    conto = {}
    for voce in voci_raccolte:
        k = chiave(voce["ferrarese"])
        conto.setdefault(k, []).append(voce)
    return {k: len(v) for k, v in conto.items()}


def costruisci(nuove: list, prossimo: int, gemelli: dict) -> list:
    righe = []
    for voce in nuove:
        # `italiano` porta **tutti** i significati che la fonte elenca, non
        # solo il primo, e `principale_italiano` porta il primo di essi.
        #
        # Difetto vero, di questa sessione: si scriveva il primo significato
        # in `italiano` e si buttava via il resto. Il glossario non se n'e'
        # accorto e i controlli non hanno detto niente, perche' una voce con
        # un solo significato e' ben formata. Il guasto e' arrivato al giro
        # dopo: confrontando la cella della fonte con il campo `italiano`,
        # «adacquare, innaffiare» non era piu' coperto da «adacquare», e il
        # generatore scriveva **194 voci duplicate** alla seconda esecuzione.
        # Uno script che non e' idempotente e' uno script che non si puo'
        # rilanciare senza sapere cosa sta facendo.
        #
        # La convenzione e' gia' quella del glossario: V0287 scrive
        # `italiano: "Adacquare, inaffiare"` con `principale_italiano:
        # "Adacquare"`, e `glossario.py` (_chiavi_resi) divide sui due campi
        # perche' ogni reso sia cercabile. Si segue quella, e la fonte resta
        # leggibile per intero.
        significati = (voce.get("significati") or "").strip()
        principale = significati.split(",")[0].strip() if significati else ""
        riga = {
            "id": "V%04d" % prossimo,
            "varieta": CODICE_VARIETA_ATTESA,
            "ferrarese": voce["ferrarese"],
            "italiano": significati,
            "principale_italiano": principale,
            "varianti": [],
            "campo": "",
            "note": nota_voce(voce, gemelli.get(chiave(voce["ferrarese"]), 1)),
            "fonte": fonte_voce(voce["numero"]),
            "attendibilita": ATTENDIBILITA,
            "da_verificare": True,
        }
        prossimo += 1
        righe.append(riga)
    return righe


def relazione(esiti: dict) -> None:
    """I numeri che il lavoro lascia da fare, stampati.

    Stamparli non e' decorazione: sono il lavoro di chi guarda dopo. Un
    numero che si vede solo quando qualcuno chiede di vederlo e' un numero
    su cui nessuno lavora.
    """
    print("gia' nel glossario, stesso significato: %4d (non si aggiungono)"
          % len(esiti["gia_presenti"]))
    print("disaccordi con una voce esistente:        %4d (nessuno sceglie)"
          % len(esiti["disaccordi"]))
    print("doppie nella stessa fonte:               %4d (se ne tiene una)"
          % len(esiti["doppie"]))
    print("parole funzionali:                       %4d (non sono voci)"
          % len(esiti["funzionali"]))
    for voce, esistenti in esiti["disaccordi"][:10]:
        numeri = ", ".join(sorted(v.get("id", "?") for v in esistenti))
        if isinstance(esistenti, dict):
            numeri = esistenti.get("id", "?")
            esistenti = [esistenti]
        primo = esistenti[0]
        print("   n.%-5d %-12s %-26s vs %s: %s"
              % (voce["numero"], voce["ferrarese"],
                 (voce.get("significati") or "")[:26], numeri,
                 (primo.get("italiano") or "")[:26]))
    if len(esiti["disaccordi"]) > 10:
        print("   ... e altri %d" % (len(esiti["disaccordi"]) - 10))


def main(argv=None) -> int:
    analizzatore = argparse.ArgumentParser(
        description="Porta il vocabolario di Bigoni nel glossario attivo.")
    analizzatore.add_argument("--prova", action="store_true",
                              help="dice cosa farebbe e non scrive")
    argomenti = analizzatore.parse_args(argv)

    dichiarazione = varieta_dichiarata(VARIETA, ID_FONTE)
    if dichiarazione.get("varieta") != CODICE_VARIETA_ATTESA:
        raise SystemExit(
            "dati/varieta.json dichiara %r per %s e questo script scrive %r.\n"
            "Le due cose non possono essere diverse: o si cambia il codice "
            "qui, o si cambia la dichiarazione nei dati, e la seconda e' "
            "quella giusta perche' i dati sono la fonte e il codice no."
            % (dichiarazione.get("varieta"), ID_FONTE, CODICE_VARIETA_ATTESA))

    voci_raccolte = carica_grezzo(GREZZO)
    attive = voci_attive(GLOSSARIO)
    esiti = confronta(voci_raccolte, attive)
    gemelli = gemelli_per_chiave(voci_raccolte)
    # I due massimi si sommano: i dati attivi danno V10389 e la
    # fila d'attesa V10404, quindi il primo id libero e' V10405.
    prossimo = max(prossimo_id(attive), id_in_attesa() + 1)
    righe = costruisci(esiti["nuove"], prossimo, gemelli)

    print("raccolte %d coppie, glossario attivo %d voci"
          % (len(voci_raccolte), len(attive)))
    relazione(esiti)
    print("nuove voci: %d (da V%04d a V%04d)"
          % (len(righe), prossimo, prossimo + len(righe) - 1))
    print("attendibilita' %s dichiarata come %s in dati/varieta.json"
          % (righe[0]["attendibilita"] if righe else "-",
             dichiarazione.get("attendibilita", "?")))

    if argomenti.prova:
        for riga in righe[:5]:
            print(json.dumps(riga, ensure_ascii=False))
        print("\n--prova: non e' stato scritto niente")
        return 0

    with io.open(GLOSSARIO, "a", encoding="utf-8", newline="\n") as f:
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print("scritte %d voci in dati/glossario.jsonl" % len(righe))
    return 0


if __name__ == "__main__":
    sys.exit(main())