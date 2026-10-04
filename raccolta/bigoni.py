"""Raccoglie il vocabolario di R. Bigoni e lo mette in file grezzi.

Il sito non pubblica il vocabolario in una pagina: `VocFeIt.html` contiene
solo la descrizione dell'ortografia, e l'elenco delle parole arriva da uno
script a parte che risponde a una POST. La nota di S006 nel registro
diceva che per questo non si poteva costruire un vocabolario dalla fonte, e
la ragione addotta era che «il sito non lo mette in una pagina». Il dato
c'e' ed e' stato raccolto: 7307 coppie numerate da 1 a 7307.

Questo script **non scrive il glossario**. Raccoglie e basta: quello che
diventa voce e' una decisione che passa dai controlli, e i controlli devono
poter dire no.

Idempotente come `sintetizza.py`: due giri producono file identici byte per
byte.

Uso:
    python3 raccolta/bigoni.py
"""
import argparse
import io
import json
import os
import re
import sys
import unicodedata
import urllib.request

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREZZI = os.path.join(RADICE, "raccolta", "grezzi")

URL_ELENCO = ("https://www.robertobigoni.it/Servizi/Ferrarese/"
              "elencoParoleFerraresiPerLettera.php")
USER_AGENT = "traduttore-ferrarese/0.17 (raccolta; Pietro Fabbri)"

# Il sito distingue le parole omonime con un suffisso numerato:
# l'italiano e' `ancora-1` e `ancora-2` per due significati diversi della
# stessa parola. Il suffisso e' del sito, non dell'italiano: entra
# nell'estrazione ma non nella parola.
#
# Due cose che il primo tentativo aveva sbagliate, e che sono la ragione per
# cui questa espressione non e' quella che sembrava:
#
# - il suffisso sta **nel bottone**, non nella cella dei significati. Il
#   codice lo cercava nella cella, dove non compare mai: su 7307 righe il
#   numero degli omonimi trovati era **zero**, e nessun controllo lo diceva,
#   perche' zero e' un numero che sembra giusto. Il conto vero e' **186
#   righe** (170 col trattino e 16 senza);
# - il sito scrive anche senza trattino (`acciarino1`, `brocca1`,
#   `pidocchioso1`), quindi `-(\d+)$` da solo manca 16 righe su 186.
#
# La forma e' una alternativa, non due ricerche: `-(\d+)$` per il trattino e
# `(\d+)$` per il numero attaccato. Il risultato e' il numero, e il
# chiamante non deve sapere quale delle due forme aveva trovato.
SUFFISSO_OMONIMO = re.compile(r"(?:-|)(\d+)$")

RIGA = re.compile(r"<tr>(.*?)</tr>", re.S)
CELLA = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
BOTTONE = re.compile(r"<button[^>]*?mostraEtimo\w*\(\s*\"([^\"]*)\"\s*,"
                     r"\s*\"([^\"]*)\"\s*,\s*\"(.*?)\"\s*\)", re.S)
BOTTONE_INTERO = re.compile(r"<button\b.*?</button>", re.S | re.I)


def scarica(url):
    richiesta = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(richiesta, timeout=60) as risposta:
        return risposta.read().decode("utf-8", "replace")


def _pulisci(testo):
    testo = re.sub(r"<[^>]+>", "", testo)
    for prima, dopo in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                        ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"),
                        ("&agrave;", "à"), ("&eacute;", "é"),
                        ("&egrave;", "è"), ("&igrave;", "ì"),
                        ("&ograve;", "ò"), ("&ugrave;", "ù")):
        testo = testo.replace(prima, dopo)
    return " ".join(testo.split())


def compatta(testo):
    """Chiave che distingue due voci davvero diverse.

    Toglie lo spirito e l'apostrofo — `skara'na` e `skarana` sono la stessa
    parola — ma **tutti gli accenti restano**. Difetto vero, di questo
    script: la prima versione toglieva anche `à`, `é`, `ò`, e allora
    `àɣar` diventava `gar` e `alòž` diventava `al`: duecento voci diverse si
    trovavano con la stessa chiave, e un glossario che unisce `acre` con
    `agro` non e' piu' un glossario. Nell'ortografia di Bigoni l'accento
    segna l'accento tonico: `aràdàr` e `aràdar` non sono la stessa parola.
    """
    t = unicodedata.normalize("NFC", testo).lower()
    t = t.replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9àâäèéêëìíîïòóôöùúûüñŋɣʎ]", "", t)


def lassa(testo):
    """Chiave permissiva, **solo per segnalare**.

    Toglie anche gli accenti e scioglie `j`, `ɣ`, `ŋ`. Serve a dire «questa
    voce potrebbe essere quella di là», e non a decidere che sono la stessa:
    una chiave che unisce voci diverse e' peggio di nessuna chiave, perche'
    fa sparire una voce senza che nessuno se ne accorga.
    """
    t = compatta(testo)
    t = (t.replace("j", "i").replace("ɣ", "g").replace("ʎ", "l")
          .replace("ŋ", "n"))
    for accento in "àâäèéêëìíîïòóôöùúûü":
        t = t.replace(accento, "")
    return t


def voci_da_html(html):
    """Legge le coppie dalla tabella e verifica la direzione.

    Ogni riga viene letta due volte: dalle celle che si vedono e dagli
    argomenti del bottone. Le due letture devono dire la stessa cosa.

    Difetti veri, incontrati su questi dati, perche' restano scritti:

    - la parola ferrarese delle due letture coincide **sempre**, e il suo
      confronto e' rigido: e' la cosa che dice da che parte stiamo leggendo;
    - l'italiano **non** coincide: la cella elenca tutti i significati
      («adacquare, innaffiare») mentre il bottone ne prende uno solo
      («adacquare»), perche' serve alla ricerca dell'etimologia. Confrontare
      i due per uguaglianza scartava 510 righe su 7307 e avrebbe detto che
      la fonte non tornava, mentre la fonte era a posto e il confronto
      era sbagliato.

    Restituisce le voci e quante righe non hanno tenuto il confronto.
    """
    voci = []
    incoerenti = 0
    for corpo in RIGA.findall(html):
        celle = CELLA.findall(corpo)
        bottone = BOTTONE.search(corpo)
        if len(celle) != 3 or bottone is None:
            continue
        numero = _pulisci(celle[0])
        if not numero.isdigit():
            continue
        parola = _pulisci(BOTTONE_INTERO.sub("", celle[1]))
        significati = _pulisci(celle[2])
        arg_italiano, arg_ferrarese, etimo = (_pulisci(x)
                                              for x in bottone.groups())

        # Il confronto e' **solo** sulla parola ferrarese, e serve a una
        # cosa sola: accorgersi che le colonne sono lette nel verso
        # sbagliato. Sulla parola ferrarese le due letture coincidono in
        # tutte e 7307 le righe della fonte, ed e' il confronto che tiene.
        #
        # L'italiano viene dalla cella, non dagli argomenti del bottone:
        # in 156 righe il bottone non porta la traduzione ma la parola da
        # cui deriva la ricerca dell'etimologia — per `bak` porta `bac`, che
        # e' il latino, mentre la cella dice «bastone, mazza». Prendendo
        # l'italiano dal bottone, 156 voci avrebbero portato dentro il
        # glossario una parola che non e' la loro traduzione, senza che
        # nulla lo segnalasse.
        if parola != arg_ferrarese:
            incoerenti += 1
            continue

        primo_significato = significati.split(",")[0].strip()
        # Il suffisso si cerca e si toglie **dove sta**: nel primo argomento
        # del bottone, non nella cella. La cella dice «ancora» in entrambe le
        # righe e non distingue niente; il bottone dice `ancora-1` e
        # `ancora-2`, ed e' l'unico posto in cui il sito distingue i due
        # significati della stessa parola ferrarese.
        #
        # Prima il codice guardava la cella e trovava zero omonimi su 7307
        # righe: nessun errore, nessun avviso, e 186 righe in cui due voci
        # diverse sembravano una sola voce con due numeri senza significato.
        # Un numero che arriva a zero quando nessuno lo controlla e' il
        # modo piu' economico di perdere un intero campo.
        trovato = SUFFISSO_OMONIMO.search(arg_italiano)
        omonimo = int(trovato.group(1)) if trovato else None

        voci.append({
            "numero": int(numero),
            "ferrarese": arg_ferrarese,
            "italiano": primo_significato,
            "significati": significati,
            "omonimo": omonimo,
            "etimologia": etimo,
            "chiave": compatta(arg_ferrarese),
            "chiave_lassa": lassa(arg_ferrarese),
        })
    return voci, incoerenti


def controlla(voci, incoerenti):
    """Se quello che e' arrivato ha senso, prima di scriverlo."""
    problemi = []
    if not voci:
        return ["nessuna voce letta: scarico fallito o formato cambiato"]
    if incoerenti:
        problemi.append("%d righe con le colonne nel verso sbagliato"
                        % incoerenti)
    numeri = [v["numero"] for v in voci]
    if len(set(numeri)) != len(numeri):
        ripetuti = sorted({n for n in numeri if numeri.count(n) > 1})
        problemi.append("%d numeri ripetuti (per esempio %s)"
                        % (len(ripetuti), ripetuti[:5]))
    if numeri != sorted(numeri):
        problemi.append("i numeri non sono in ordine")
    # I numeri della fonte sono consecutivi da 1. Se arrivassero 6797
    # numeri da 1 a 7307 il conto delle righe non se ne accorgerebbe:
    # mancherebbero 510 voci e nessuno lo saprebbe. Il numero massimo
    # e' l'unico che se ne accorge, quindi viene confrontato con il numero
    # delle righe.
    if numeri != list(range(1, len(numeri) + 1)):
        problemi.append("i numeri non sono consecutivi da 1 (primo %s, "
                        "ultimo %s, righe %d): mancano voci"
                        % (numeri[0], numeri[-1], len(numeri)))
    chiavi = [v["chiave"] for v in voci]
    se_n = len(set(chiavi)) - len(set(chiavi))
    if se_n:
        problemi.append("%d chiavi compatte uguali: due voci diverse avrebbero"
                        " la stessa identita'" % se_n)
    for voce in voci:
        if len(voce["ferrarese"]) < 2 or len(voce["italiano"]) < 2:
            problemi.append("voce troppo corta: %r" % voce)
            break
    return problemi


def relazione(voci):
    """Quante voci somigliano a un'altra senza essere la stessa.

    Non e' un errore: e' un numero che dice quanto lavoro farebbe chi
    deduplica, e va detto perche' nessun numero di questo senza saperlo e'
    confrontabile.
    """
    gruppi = {}
    for voce in voci:
        gruppi.setdefault(voce["chiave_lassa"], []).append(voce)
    somiglianti = 0
    esempi = []
    for chiave, gruppo in gruppi.items():
        if len(gruppo) < 2:
            continue
        compatte = {v["chiave"] for v in gruppo}
        if len(compatte) > 1:
            somiglianti += len(gruppo) - 1
            if len(esempi) < 5:
                esempi.append([(v["ferrarese"], v["italiano"])
                               for v in gruppo])
    return somiglianti, esempi


def scrivi(voci, nome):
    percorso = os.path.join(GREZZI, nome)
    righe = [json.dumps(voce, ensure_ascii=False, sort_keys=True)
             for voce in sorted(voci, key=lambda v: v["numero"])]
    with io.open(percorso, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(righe) + "\n")
    return percorso, len(righe)


def raccogli(url, nome):
    sys.stdout.write("scarico ... ")
    sys.stdout.flush()
    try:
        html = scarica(url)
    except Exception as errore:                          # noqa: BLE001
        print("FALLITO (%s: %s)" % (type(errore).__name__, errore))
        return None, None, ["download fallito"]
    voci, incoerenti = voci_da_html(html)
    guai = controlla(voci, incoerenti)
    if guai:
        print("PROBLEMA")
        for guaio in guai:
            print("   " + guaio)
        return None, None, guai
    somiglianti, esempi = relazione(voci)
    percorso, righe = scrivi(voci, nome)
    print("%d voci -> %s" % (righe, os.path.relpath(percorso, RADICE)))
    print("   %d voci somigliano a un'altra senza essere la stessa "
          "(da decidere a mano)" % somiglianti)
    for gruppo in esempi:
        print("   esempi: %s" % gruppo)
    return righe, somiglianti, []


def main(argv=None):
    analizzatore = argparse.ArgumentParser(
        description="Raccoglie il vocabolario di R. Bigoni.")
    analizzatore.parse_args(argv)

    if not os.path.isdir(GREZZI):
        os.makedirs(GREZZI)

    righe, _somiglianti, problemi = raccogli(
        URL_ELENCO, "bigoni_ferrarese_italiano.jsonl")
    if problemi:
        print("\n%d problemi: il file non e' stato scritto" % len(problemi))
        return 1
    print("\n%d coppie raccolte" % righe)
    return 0


if __name__ == "__main__":
    sys.exit(main())