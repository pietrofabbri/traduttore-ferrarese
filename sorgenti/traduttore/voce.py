"""Far suonare una parola ferrarese, e dire quanto il suono e' incerto.

Il gioco ha bisogno di far ascoltare, e per far ascoltare servono due cose
che il progetto non ha: un **parlante ferrarese**, che non c'e', e una voce
sintetica, che c'e' ma non e' la stessa cosa. Questo modulo costruisce la
seconda e **dice chiaramente che non e' la prima**.

La catena e' quattro passi, e ognuno puo' fallire in modo diverso:

1. la grafia ferrarese passa da `legge.leggi`, che applica le regole
   dichiarate in `dati/fonetica.jsonl` e dove non si sa **si ferma**;
2. la IPA ottenuta viene tradotta nell'alfabeto fonemico di `espeak-ng`,
   che e' diverso dall'IPA e non accetta gli stessi simboli;
3. `espeak-ng`, **in locale**, produce il `wav`;
4. ogni dubbio emerso al passo 1 resta scritto accanto al suono.

Il punto 2 merita una riga: `espeak-ng` non accetta `tʃ` ne' `ɲ`, accetta
`tS` e `N`. Scrivere `tʃ` non da errore e non dice niente: **taglia la parola
nel punto in cui l'ha incontrato**, e il risultante wav sembra parlato ma
sta zoppicando. Per questo la traduzione non prova e basta: ogni simbolo
che non sa tradurre **ferma la generazione** e lo dichiara.

Quello che questo modulo NON e', e che nessuna riga di codice puo' fare
diversamente:

- non e' un ferrarese che parla, e non va presentato come tale. Una voce
  sintetica che conosce le regole di *lettura* non conosce il parlato: non
  sa che la `s` intervocalica si dice come vuole, e non sa come si sente
  `scaranna` detta da chi e' nato a Ferrara;
- non sostituisce la conferma di un parlante. Le righe di
  `dati/fonetica.jsonl` restano `attendibilita: "I"` e `da_verificare: true`,
  e un wav generato da una riga non verificata resta non verificato: si
  propaga il dubbio, non si lava via.

Per questo i file generati **non entrano in `web/audio/`**. Copiare li'
significherebbe pubblicarli, e la regola del progetto e' che un brano si
pubblica solo con consenso, licenza e `pubblicabile`. Qui non c'e' nessuna
persona che abbia acconsentito a nulla, perche' nessuna persona ha parlato:
c'e' una macchina. Escono in `raccolta/lavorato/voci/`, che non e' tracciata,
e il comando `dati/audio.jsonl` resta quello che dice: vuoto, e vuoto e' il
numero giusto.

Nessuna rete: `espeak-ng` gira in locale. Senza di lui il comando **dice
che manca** e non indovina un suono.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from traduttore import legge

# L'alfabeto di `espeak-ng`, non l'IPA. Ogni chiave e' un simbolo IPA che il
# modulo `legge` puo' produrre; il valore e' come quell'unico programma lo
# scrive. I simboli sono messi per lunghezza decrescente quando si cerca un
# prefisso piu' lungo, altrimenti `tʃ` diventerebbe `t` + `ʃ`.
DA_IPA = {
    "tʃ": "tS",   # affricata dentale sorda
    "dʒ": "dZ",   # affricata alveolare sonora
    "ɲ": "N",     # nasale palatale
    "ʃ": "S",     # fricativa palato-alveolare sorda
    "ʒ": "Z",     # fricativa palato-alveolare sonora
    "ɛ": "E",     # vocale aperta
    "a": "a", "e": "e", "i": "i", "o": "o", "u": "u",
    "s": "s", "z": "z",
    "b": "b", "d": "d", "f": "f", "k": "k", "g": "g",
    "l": "l", "m": "m", "n": "n", "p": "p", "r": "r",
    "t": "t", "v": "v", "j": "j",
}

# Le vocali toniche si marcano con l'apostrofo, che e' come `espeak-ng` le
# marca. Le consonanti non si marcano: in italiano l'accento non puo' cadere
# su una, e segnarlo produrrebbe una sillaba che nella lingua non esiste.
VOCALI_ESPEAK = set("aeiouE")

# La velocita' di default. Piu' lenta della parla di tutti e di proposito:
# chi ascolta una voce che non conosce ha bisogno di tempo, e il gioco chiede
# di far **ripetere**, non di far capire al volo. Si puo' cambiare.
VELOCITA_DEFAULT = 130

# La voce di base. `it` e' italiano: non esiste un italiano ferrarese che possa
# fingere di essere ferrarese, e dirlo e' piu' onesto che sceglierne una.
VOCE_DEFAULT = "it"


def percorso_espeak() -> str:
    """Il percorso di `espeak-ng`, o una stringa vuota se non c'e'.

    Il progetto non ha dipendenze e non puo' averne: quindi si controlla e si
    dice, non si importa e si spera.
    """
    return shutil.which("espeak-ng") or ""


def percorso_ffmpeg() -> str:
    """Il percorso di `ffmpeg`, per il formato compresso. Vedi sopra."""
    return shutil.which("ffmpeg") or ""


def ipa_a_fonemi(ipa: str) -> tuple:
    """La IPA nell'alfabeto di `espeak-ng`.

    Ritorna `(fonemi, problema)`. Se `problema` non e' vuota i fonemi sono
    incompleti e **non vanno usati**: e' esattamente il caso in cui `espeak-ng`
    taglia la parola e produce un wav che sembra parlato.

    Il gesto di non procedere e' il punto. Un mapping che perde una lettera
    senza dirlo e' peggio di nessuna voce, perche' l'errore si sente solo da
    chi conosce la parola.

    Il segno di accento `ˈ` **non** e' un fonema: dice dove cade la sillaba
    tonica, e in questo alfabeto si marca con un apostrofo messo subito
    prima della vocale accentata. Percio' viene tolto dal flusso e
    reintrodotto al posto giusto, altrimenti finirebbe dentro i fonemi come
    una lettera che non esiste.
    """
    resto = []
    accento = False
    for simbolo in ipa.strip("/"):
        if simbolo == "ˈ":
            accento = True
        else:
            resto.append((simbolo, accento))
            accento = False
    

    # Dal piu' lungo al piu' breve, cosi' `tʃ` non viene letto come `t`.
    ordine = sorted(DA_IPA, key=len, reverse=True)

    # Il segno di accento marca una **sillaba**, non una lettera: in
    # `/maˈɲnar/` la vocale accentata arriva dopo la `ɲ`. Quindi il mark
    # resta in attesa e l'apostrofo va sulla prima vocale che segue, che e'
    # il vero nucleo della sillaba accentata.
    fonemi = []
    accento_in_attesa = False
    i = 0
    while i < len(resto):
        lettera, accentata = resto[i]
        if accentata:
            accento_in_attesa = True
        for simbolo in ordine:
            if "".join(s for s, _ in resto[i:]).startswith(simbolo):
                if simbolo in VOCALI_ESPEAK:
                    if accento_in_attesa:
                        fonemi.append("'")
                    accento_in_attesa = False
                fonemi.append(DA_IPA[simbolo])
                i += len(simbolo)
                break
        else:
            return (None,
                    "simbolo IPA %r: nessuna fonte e nessun programma dice "
                    "come suona, quindi la voce non la puo' dire" % lettera)
    return ("".join(fonemi), "")


def _ultimo(pezzi: list) -> str:
    """L'ultimo carattere di una stringa di fonemi, o `''` se e' vuota."""
    return pezzi[-1] if pezzi else ""


def voce(parola: str, velocita: int = VELOCITA_DEFAULT,
         lingua: str = VOCE_DEFAULT) -> dict:
    """La parola ferrarese, con la sua IPA e la voce che la direbbe.

    Ritorna sempre un dizionario, anche quando non e' andata: quando non e'
    andata, `wav` e' vuoto e `problema` spiega perche'. La funzione non
    solleva e non indovina.
    """
    esito = {
        "forma": parola or "",
        "ipa": "",
        "fonemi": "",
        "wav": "",
        "nota": "",
        "dubbi": [],
        "attendibilita": "I",
        "da_verificare": True,
        "problema": "",
    }
    if not (parola or "").strip():
        esito["problema"] = "parola vuota: non c'e' niente da dire"
        return esito

    # Passo 1: la grafia letta secondo le regole dichiarate.
    letta = legge.leggi(parola)
    esito["ipa"] = letta["ipa"]
    esito["dubbi"] = list(letta["dubbi"])

    # Passo 2: la IPA nell'alfabeto del programma che suona.
    fonemi, problema = ipa_a_fonemi(letta["ipa"])
    if problema:
        esito["problema"] = problema
        esito["dubbi"].append(problema)
        return esito
    esito["fonemi"] = fonemi

    # Il dubbio di `legge` resta: la voce suona, ma suona **una delle**
    # letture possibili, e questo resta scritto.
    if letta["nota"]:
        esito["nota"] = letta["nota"]
    if esito["dubbi"]:
        esito["nota"] = "; ".join(esito["dubbi"]) if not esito["nota"] \
            else esito["nota"]
    return esito


def scrivi_wav(parola: str, percorso: str, velocita: int = VELOCITA_DEFAULT,
               lingua: str = VOCE_DEFAULT) -> dict:
    """La parola suonata, con il `wav` scritto dove si e' chiesto.

    Il comando esterno e' dichiarato qui, non nascosto: se manca
    `espeak-ng` la funzione dice che manca, e non produce nessun file. Un
    file audio prodotto da un programma diverso non sarebbe piu' verificabile.
    """
    esito = voce(parola, velocita=velocita, lingua=lingua)
    if esito["problema"]:
        return esito

    programma = percorso_espeak()
    if not programma:
        esito["problema"] = ("espeak-ng non e' installato: senza un programma "
                            "che suoni non si puo' fare una voce, e non si "
                            "inventa un suono")
        return esito

    cartella = os.path.dirname(percorso)
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella)

    comando = [programma, "-v", lingua, "-s", str(velocita),
               "-w", percorso, "[[%s]]" % esito["fonemi"]]
    try:
        fatto = subprocess.run(comando, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    except OSError as errore:
        esito["problema"] = "espeak-ng non e' partito: %s" % errore
        return esito
    if fatto.returncode != 0:
        esito["problema"] = ("espeak-ng ha fallito: %s"
                             % fatto.stderr.decode("utf-8", "replace").strip())
        return esito
    if not os.path.isfile(percorso):
        esito["problema"] = ("espeak-ng ha detto di si' ma il file non c'e': "
                             "non si scrive un suono che non si e' sentito")
        return esito

    esito["wav"] = percorso
    # Il dubbio resta anche adesso che il suono c'e'. E' il punto del
    # modulo: un wav non verifica niente, e non e' un attestato.
    esito["nota"] = (esito["nota"] + "; " if esito["nota"] else "") + (
        "voce sintetica: non e' un parlante ferrarese e non verifica la "
        "trascrizione")
    return esito