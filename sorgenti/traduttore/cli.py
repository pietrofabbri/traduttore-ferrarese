"""La riga di comando.

Cinque comandi, e sono tutti sottocomandi di una sola cosa: guardare e
costruire. Non c'e' un comando che «migliora» i dati da solo, perche' un
programma che sistema un glossario senza chiedere lo rovina.

    traduci       traduce una frase e dice da dove viene ogni parola
    cerca         cerca una voce o una coppia
    impara        impara le regole morfologiche dal corpus e le scrive
    verifica      i controlli sui dati
    stato         che cosa sa il motore, in numeri
    varieta       le cinque varieta' del ferrarese, e quante voci ha ciascuna
    pronuncia     la trascrizione IPA di una parola, e quanto e' sicura
    audio         che brani audio ci sono, e quali si possono pubblicare
    proposte      la coda di revisione delle risposte del modello
    web           genera il sito statico

Il comando `traduci` e' l'unico che esce dal terminale e va progettato per
essere usato da chi non e' un programmatore: il risultato si legge, e in
fondo dice sempre una delle tre frasi che contano, che sono «pubblicabile»,
«da rivedere» e «non lo so».
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import morfologia, verifica_dati
from .audio import Archivio, controlla_archivo
from .corpora import Corpus
from .fonetica import Fonetica
from .glossario import FE_IT, IT_FE, Glossario
from .modello import costruisci_modello
from .motore import Motore
from .proposte import controlla_proposte, conta_stati, da_risposta, leggi, salva
from .varieta import NOMI, VARIETA, Varieta

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATI = os.path.join(RADICE, "dati")
AUDIO = os.path.join(RADICE, "audio")

PERCORSI = {
    "glossario": os.path.join(DATI, "glossario.jsonl"),
    "coppie": os.path.join(DATI, "coppie.jsonl"),
    "proverbi": os.path.join(DATI, "proverbi.jsonl"),
    "regole": os.path.join(DATI, "regole.json"),
    "varieta": os.path.join(DATI, "varieta.json"),
    "fonetica": os.path.join(DATI, "fonetica.jsonl"),
    "audio": os.path.join(DATI, "audio.jsonl"),
}

# La fila d'attesa: materiale raccolto ma non ancora pubblicabile. Non entra
# nel motore e non entra nella pagina, e il controllo D1 verifica che non ci
# finisca per sbaglio.
IN_ATTESA = {
    "glossario": os.path.join(DATI, "da_verificare", "glossario.jsonl"),
    "coppie": os.path.join(DATI, "da_verificare", "coppie.jsonl"),
    "fonetica": os.path.join(DATI, "da_verificare", "fonetica.jsonl"),
}

# La coda di revisione del livello IA. Non e' un glossario e non e' un corpus:
# e' il posto dove le risposte del modello aspettano che qualcuno le guardi.
PERCORSO_PROPOSTE = os.path.join(DATI, "proposte", "proposte.jsonl")


def carica(modello_attivo: bool = False):
    """Carica il motore. Un posto solo in cui si fanno queste cose."""
    glossario = Glossario.da_file(PERCORSI["glossario"])
    corpus = Corpus.da_file(PERCORSI["coppie"], PERCORSI["proverbi"])
    regole = _carica_regole()
    modello = costruisci_modello() if modello_attivo else None
    return Motore(glossario, corpus, regole, modello)


def _carica_regole() -> list:
    percorso = PERCORSI["regole"]
    if not os.path.exists(percorso):
        return []
    with open(percorso, "r", encoding="utf-8") as f:
        grezzo = json.load(f)
    return [morfologia.Regola(**r) for r in grezzo.get("regole", [])]


def _salva_regole(regole: list, percorso: str = None) -> None:
    percorso = percorso or PERCORSI["regole"]
    grezzo = {
        "_nota": "File generato da `python3 -m traduttore.cli impara`. "
                 "Non si modifica a mano: si rigenera e si legge.",
        "regole": [r.come_dict() for r in regole],
    }
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(grezzo, f, ensure_ascii=False, indent=2)
        f.write("\n")


# --- i comandi -----------------------------------------------------------

def comando_traduci(args) -> int:
    motore = carica(modello_attivo=args.ia)
    direzione = FE_IT if args.direzione == "fe-it" else IT_FE
    risposta = motore.traduci(" ".join(args.testo), direzione)
    salvate = _salva_proposte(risposta, direzione, args)
    if args.json:
        print(json.dumps(risposta.come_json(), ensure_ascii=False, indent=2))
        return 0 if risposta.da_pubblicare else 1
    etichetta = "ferrarese" if direzione == IT_FE else "italiano"
    print(risposta.spiega())
    print()
    print("%-10s %s" % (etichetta + ":", risposta.testo))
    for riga in salvate:
        print("           proposta salvata in dati/proposte/: %s -> %s "
              "(%0.2f), da rivedere" % (riga["parola"], riga["traduzione"],
                                        riga["confidenza"]))
    return 0 if risposta.da_pubblicare else 1


def _salva_proposte(risposta, direzione: str, args) -> list:
    """Mette in coda di revisione quello che ha risposto il modello.

    Solo quando il livello 4 e' attivo (`--ia`) e solo per le risposte che il
    motore ha **accettato**: i buchi non si salvano, perche' il buco e' gia'
    dichiarato a schermo e nella coda non aggiunge niente.

    La scrittura c'è anche con `--no-proposte` disattivato, e cioè si puo'
    spegnerla: la coda di revisione e' un file del repository e scriverci
    mentre si fa una prova e' rumore. Il default e' perche' la promessa scritta
    nel README e nel modulo `modello.py` e' che le risposte del modello non
    vengono perse.
    """
    if not args.ia or getattr(args, "no_proposte", False):
        return []
    salvate = []
    for originale, tradotto, origine, confidenza, dettaglio in risposta.per_corrispondenza:
        if origine != "modello":
            continue
        proposta = da_risposta(originale, direzione, {
            "traduzione": tradotto,
            "confidenza": confidenza,
            "dettaglio": dettaglio,
        })
        salva(proposta, PERCORSO_PROPOSTE)
        salvate.append(proposta.come_dict())
    return salvate


def comando_proposte(args) -> int:
    """La coda di revisione, e i numeri che dicono se sta servendo a qualcosa.

    Il comando esiste perche' una coda di revisione che nessuno guarda e' un
    posto dove le risposte del modello marcano `da rivedere` per sempre. Il
    numero che conta e' `approvate`: se resta a zero per mesi, o non c'e' niente
    da approvare, o nessuno approva, e le due cose si confondono.
    """
    proposte = leggi(PERCORSO_PROPOSTE)
    if args.json:
        print(json.dumps({"proposte": proposte and [p.come_dict() for p in proposte],
                          "stati": conta_stati(proposte)},
                         ensure_ascii=False, indent=2))
        return 0
    for stato, numero in conta_stati(proposte).items():
        print("%-12s %d" % (stato, numero))
    print()
    if not proposte:
        print("la coda e' vuota.")
        print("non e' un difetto: senza chiave il livello 4 non esiste, e con "
              "la chiave la coda si riempie da sola quando si usa `--ia`.")
        print("Il protocollo, i campi e chi approva sono in "
              "dati/proposte/README.md.")
        return 0
    for p in proposte[-20:]:
        print("%-10s %-16s %-22s %0.2f  %s"
              % (p.data, p.parola, (p.traduzione or "")[:22], p.confidenza,
                 p.stato + (" -> " + p.promossa_a if p.promossa_a else "")))
    if len(proposte) > 20:
        print("... prime %d di %d" % (len(proposte) - 20, len(proposte)))
    return 0


def comando_cerca(args) -> int:
    glossario = Glossario.da_file(PERCORSI["glossario"])
    direzione = FE_IT if args.direzione == "fe-it" else IT_FE
    voci = glossario.cerca(args.forma, direzione)
    if not voci:
        print("nessuna voce per %r" % args.forma)
        vicine = glossario.vicine(args.forma, direzione, soglia=0.6)
        if vicine:
            print("vicine (non sono risposte):")
            for punteggio, voce in vicine:
                print("  %0.2f  %s = %s  (%s)"
                      % (punteggio, voce.ferrarese, voce.italiano, voce.fonte or "senza fonte"))
        return 1
    for voce in voci:
        print("%-8s %s = %s" % (voce.id, voce.ferrarese, voce.italiano))
        if voce.varianti:
            print("         varianti: " + ", ".join(voce.varianti))
        print("         campo: %s | attendibilita: %s%s"
              % (voce.campo or "-", voce.attendibilita,
                 " | DA VERIFICARE" if voce.da_verificare else ""))
        print("         varieta': %s" % (voce.varieta or "NON DICHIARATA"))
        fonetica = Fonetica.da_file(PERCORSI["fonetica"])
        for t in fonetica.per_riferimento(voce.id):
            print("         suona:   %-10s %s  (%s%s)"
                  % (t.forma, t.ipa, t.attendibilita,
                     ", da verificare" if t.da_verificare else ""))
        print("         fonte: %s" % (voce.fonte or "SENZA FONTE"))
        if voce.note:
            print("         nota: %s" % voce.note)
    return 0


def comando_impara(args) -> int:
    glossario = Glossario.da_file(PERCORSI["glossario"])
    corpus = Corpus.da_file(PERCORSI["coppie"], PERCORSI["proverbi"])
    regole = morfologia.impara(corpus, glossario)
    if args.vedi:
        for regola in regole:
            print("%-40s accordo %0.2f  %d esempi"
                  % (regola.etichetta(), regola.accordo, regola.supporto))
        print()
        print("%d regole" % len(regole))
    if not args.solo_vedi:
        _salva_regole(regole)
        print("scritte %d regole in %s" % (len(regole), PERCORSI["regole"]))
    return 0


def comando_verifica(args) -> int:
    glossario = Glossario.da_file(PERCORSI["glossario"])
    corpus = Corpus.da_file(PERCORSI["coppie"], PERCORSI["proverbi"])
    regole = _carica_regole()
    varieta = Varieta.da_file(PERCORSI["varieta"])
    fonetica = Fonetica.da_file(PERCORSI["fonetica"])
    archivio = Archivio.da_file(PERCORSI["audio"])
    in_attesa_glossario = Glossario.da_file(IN_ATTESA["glossario"])
    in_attesa_corpus = Corpus.da_file(IN_ATTESA["coppie"])
    problemi = (verifica_dati.controlla_varieta(varieta)
                + verifica_dati.controlla_glossario(glossario)
                + verifica_dati.controlla_corpora(corpus)
                + verifica_dati.controlla_fonetica(fonetica, glossario, corpus, varieta)
                + controlla_archivo(archivio, AUDIO)
                + verifica_dati.controlla_tenuta(glossario, corpus,
                                                in_attesa_glossario, in_attesa_corpus)
                + controlla_proposte(
                    leggi(PERCORSO_PROPOSTE),
                    {v.id for v in glossario.voci} | {c.id for c in corpus.coppie})
                + verifica_dati.controlla_regole(regole))
    if args.json:
        print(json.dumps({
            "problemi": [p.__dict__ for p in problemi],
            **verifica_dati.riepilogo(problemi),
        }, ensure_ascii=False, indent=2))
    else:
        for problema in problemi:
            print(problema.riga())
        r = verifica_dati.riepilogo(problemi)
        print()
        print("%d errori, %d avvisi" % (r["errori"], r["avvisi"]))
    return 0 if verifica_dati.riepilogo(problemi)["ok"] else 1


def comando_varieta(args) -> int:
    """Le cinque varieta', e che cosa c'e' dentro ciascuna.

    Il comando esiste perche' la domanda «il glossario copre il ferrarese?»
    ha due risposte diverse a seconda di chi la fa, e solo una e' vera: un
    glossario interamente cittadino non copre il ferrarese. Qui la risposta
    si vede in cinque righe.
    """
    glossario = Glossario.da_file(PERCORSI["glossario"])
    corpus = Corpus.da_file(PERCORSI["coppie"], PERCORSI["proverbi"])
    archivio = Archivio.da_file(PERCORSI["audio"])
    varieta = Varieta.da_file(PERCORSI["varieta"])
    conteggi = varieta.conteggi(glossario=glossario, coppie=corpus.coppie,
                                audio=list(archivio))
    righe = []
    for codice in VARIETA:
        numeri = conteggi[codice]
        righe.append({
            "codice": codice,
            "nome": NOMI.get(codice, codice),
            "territori": varieta.territori(codice),
            "glossario": numeri["glossario"],
            "coppie": numeri["coppie"],
            "audio": numeri["audio"],
            "stato": numeri["stato"],
        })
    if args.json:
        print(json.dumps(righe, ensure_ascii=False, indent=2))
        return 0
    for riga in righe:
        stato = "VUOTA" if riga["stato"] == "vuota" else "%d voci" % riga["glossario"]
        print("%-12s %-42s %-9s %d coppie, %d brani"
              % (riga["codice"], riga["nome"][:42], stato,
                 riga["coppie"], riga["audio"]))
        if riga["territori"]:
            print("             territorio: " + ", ".join(riga["territori"][:6])
                  + (" ..." if len(riga["territori"]) > 6 else ""))
    vuote = varieta.vuote(conteggi)
    print()
    if vuote:
        print("varieta' ancora vuote: " + ", ".join(vuote))
        print("una varieta' vuota e' un buco dichiarato: il glossario copre solo "
              "quello che ha dentro, e quello che ha dentro e' tutto cittadino.")
    else:
        print("nessuna varieta' vuota")
    print()
    _stampa_attesa()
    return 0


def comando_pronuncia(args) -> int:
    """Come suona una parola, e quanto quella risposta e' sicura.

    Il comando stampa sempre due righe che vengono dal file e non da una
    deduzione: la trascrizione e il suo stato. Una IPA senza stato accanto e'
    un'affermazione, e questo progetto non le fa.
    """
    fonetica = Fonetica.da_file(PERCORSI["fonetica"])
    glossario = Glossario.da_file(PERCORSI["glossario"])
    if args.tutte:
        for t in fonetica.trascrizioni:
            print("%-7s %-11s %-10s %-10s %s%s"
                  % (t.id, t.riferimento, t.forma, t.ipa, t.varieta,
                     "  (da verificare)" if t.da_verificare else ""))
        print()
        print("%d trascrizioni, %d verificate da un parlante"
              % (len(fonetica), fonetica.quante_verificate()))
        return 0

    voci = glossario.cerca(args.forma, FE_IT) or glossario.cerca(args.forma, IT_FE)
    forma = args.forma
    for voce in voci:
        forma = voce.ferrarese
    trovate = fonetica.cerca_forma(forma) or fonetica.cerca_forma(args.forma)
    if not trovate:
        print("nessuna trascrizione per %r" % args.forma)
        print("non e' un errore: e' un buco. Le trascrizioni stanno in "
              "dati/fonetica.jsonl e si scrivono a mano, con la fonte della "
              "grafia e la nota sul dubbio.")
        return 1
    for t in trovate:
        print("%-10s %s" % (t.forma, t.ipa))
        print("           voce %s | varieta' %s | attendibilita %s%s"
              % (t.riferimento, t.varieta or "-", t.attendibilita,
                 " | DA VERIFICARE" if t.da_verificare else ""))
        print("           scrittura da: %s" % (t.fonte or "senza fonte"))
        if t.nota:
            print("           nota: %s" % t.nota)
    return 0


def _stampa_attesa() -> None:
    """La fila d'attesa, dichiarata anche lei.

    Un dato che aspetta la verifica della licenza e' un dato che il progetto
    possiede e non usa. Se non lo si stampa da nessuna parte, fra sei mesi
    sembra materiale dimenticato, e un materiale dimenticato non torna piu'.
    """
    in_attesa = Glossario.da_file(IN_ATTESA["glossario"])
    coppie_attesa = Corpus.da_file(IN_ATTESA["coppie"])
    if not in_attesa.voci and not coppie_attesa.coppie:
        return
    print("in attesa di licenza verificata (dati/da_verificare/):")
    for voce in in_attesa.voci:
        print("  %-7s %-22s %s" % (voce.id, voce.ferrarese,
                                    voce.fonte or "senza fonte"))
    for coppia in coppie_attesa.coppie:
        print("  %-7s %-22s %s" % (coppia.id, (coppia.ferrarese or "")[:22],
                                   coppia.fonte or "senza fonte"))
    print("  non le usa nessuno, e tornano nel glossario quando la fonte "
          "sar' verificata.")


def comando_audio(args) -> int:
    """Che cosa si puo' ascoltare, e che cosa non si puo'.

    Il comando esiste perche' la domanda «posso mettere la voce di mia nonna
    nel gioco?» ha una risposta che dipende da tre campi, e la risposta
    giusta e' quasi sempre «no, non ancora».
    """
    archivio = Archivio.da_file(PERCORSI["audio"])
    stato = archivio.stato(AUDIO)
    if args.json:
        print(json.dumps({"stato": stato,
                          "brani": [b.come_dict() for b in archivio.brani]},
                         ensure_ascii=False, indent=2))
        return 0
    for chiave, valore in stato.items():
        print("%-16s %s" % (chiave, valore))
    print()
    _stampa_attesa()
    if not archivio.brani:
        print("non c'e' nessun brano registrato.")
        print("non e' un difetto del progetto: e' il punto in cui siamo. Il "
              "protocollo e' in audio/README.md e in RACCOLTA.md.")
        print("Quello che c'e' gia': la traccia IPA in dati/fonetica.jsonl, che "
              "serve a far ripetere e ad ascoltare quando i brani arriveranno.")
        return 0
    for brano in archivio.brani:
        stato_brano = "pubblicabile" if brano.publicabile() else "NON pubblicabile"
        print("%-8s %-10s %-28s %s | consenso: %s | %s"
              % (brano.id, brano.file or "(senza file)",
                 brano.voce or "(chi ha parlato non e' dichiarato)",
                 stato_brano, brano.consenso or "NESSUNO", brano.nota or ""))
    return 0


def comando_stato(args) -> int:
    motore = carica(modello_attivo=False)
    cosa = motore.cosa_sa()
    if args.json:
        print(json.dumps(cosa, ensure_ascii=False, indent=2))
        return 0
    for chiave, valore in cosa.items():
        print("%-24s %s" % (chiave.replace("_", " "), valore))
    print()
    print("il livello 4 (modello) e' %s" % ("presente" if cosa["con_modello"] else "assente"))
    if not cosa["con_modello"]:
        print("  per attivarlo: pip install anthropic, poi esporta ANTHROPIC_API_KEY")
    return 0


def comando_web(args) -> int:
    from costruisci_web import costruisci
    percorso = costruisci(RADICE)
    print("scritto %s" % percorso)
    return 0


# --- l'avvio -------------------------------------------------------------

def costruisci_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="traduttore",
        description="Traduttore italiano <-> ferrarese. "
                    "Ogni risposta dice da dove viene e quando non sa.",
    )
    parser.add_argument("--version", action="store_true", help="stampa la versione e esce")
    sotto = parser.add_subparsers(dest="comando")

    p = sotto.add_parser("traduci", help="traduce una frase")
    p.add_argument("testo", nargs="+", help="la frase da tradurre")
    p.add_argument("--direzione", choices=["it-fe", "fe-it"], default="it-fe")
    p.add_argument("--ia", action="store_true",
                   help="attiva il livello 4 se c'e' la chiave")
    p.add_argument("--no-proposte", action="store_true",
                   help="non scrivere le risposte del modello in "
                        "dati/proposte/ (la coda di revisione)")
    p.add_argument("--json", action="store_true", help="esce in JSON")
    p.set_defaults(func=comando_traduci)

    p = sotto.add_parser("cerca", help="cerca una voce")
    p.add_argument("forma")
    p.add_argument("--direzione", choices=["it-fe", "fe-it"], default="it-fe")
    p.set_defaults(func=comando_cerca)

    p = sotto.add_parser("impara", help="impara le regole dal corpus")
    p.add_argument("--vedi", action="store_true", help="mostra le regole e basta")
    p.add_argument("--solo-vedi", action="store_true", help="non scrive il file")
    p.set_defaults(func=comando_impara)

    p = sotto.add_parser("verifica", help="i controlli sui dati")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=comando_verifica)

    p = sotto.add_parser("stato", help="che cosa sa il motore")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=comando_stato)

    p = sotto.add_parser("varieta", help="le cinque varieta' e quello che c'e' dentro")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=comando_varieta)

    p = sotto.add_parser("pronuncia", help="la trascrizione IPA di una parola")
    p.add_argument("forma", nargs="?", default="",
                   help="la parola, in italiano o in ferrarese")
    p.add_argument("--tutte", action="store_true", help="elenca tutte le trascrizioni")
    p.set_defaults(func=comando_pronuncia)

    p = sotto.add_parser("audio", help="che brani audio ci sono e quali si pubblicano")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=comando_audio)

    p = sotto.add_parser("proposte", help="la coda di revisione del livello IA")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=comando_proposte)

    p = sotto.add_parser("web", help="genera il sito statico")
    p.set_defaults(func=comando_web)

    return parser


def main(argv=None) -> int:
    parser = costruisci_parser()
    args = parser.parse_args(argv)
    if args.version:
        from . import __version__
        print(__version__)
        return 0
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    # `pronuncia` senza argomenti e senza `--tutte` non ha niente da dire e
    # resterebbe in silenzio: e' l'unico modo in cui un utente pensa che il
    # programma sia rotto.
    if args.comando == "pronuncia" and not args.forma and not getattr(args, "tutte", False):
        parser.parse_args(["pronuncia", "--help"])
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())