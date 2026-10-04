"""Il suono delle parole che hanno una trascrizione dichiarata, e nient'altro.

Il gioco ha bisogno di far ascoltoare, e per far ascoltoare servono due cose
che il progetto non ha: un **parlante ferrarese**, che non c'è, e una voce
sintetica, che c'è ma non è la stessa cosa. `traduttore.voce` costruisce la
seconda e dichiara che non è la prima; questo script la rende pubblicabile,
**dichiarandolo ogni volta che la pagina la fa suonare**.

**Perché solo dodici parole, e non tutte.** Si potrebbe pensare di suonare
tutto il glossario: 10401 parole a circa 47 KB l'una sono **493 megabyte**, e
una pagina che ne scarica 493 non si apre da `file://` in una classe. Quindi il
suono esiste solo dove il progetto ha già scritto **come** la parola si
pronuncia, cioè le 28 righe di `dati/fonetica.jsonl`. E anche lì non tutte:
dodici su ventotto.

**Perché dodici e non ventotto.** `traduttore.voce` restituisce i **dubbi**
che `legge` trova, e un dubbio è il progetto che dice «qui non so». Suonare
una pronuncia che il progetto non sa dare è peggio che non suonare: lo
studente impara il suono sbagliato con la stessa efficacia con cui avrebbe
imparato quello giusto, e non ha modo di accorgersene. Quindi **una parola con
un dubbio non suona**, e il conteggio delle rifiutate viene stampato con il
motivo. I due esempi più dolorosi sono `magnàr` e `principiar`: la `gn` davanti
ad `à` e l'accento che la fonte non marca, e sono proprio le quattro righe su
cui il controllo **F14** non riesce a decidere.

**Dove finiscono i file, e perché lì.** In `web/sintesi/`, e **non** in
`web/audio/`. Quella cartella è quella dei brani di persone vere: i controlli
**A1**-**A10** e la verifica continua contano i file che ci trovano e pretendono
consenso, licenza e `pubblicabile`. Metterci dentro una voce di macchina
renderebbe quel conto falso, e un brano che una persona ha accettato di
pubblicare finirebbe in una cartella dove il conto non lo distingue. Sono due
cartelle diverse perché sono due cose diverse.

**Cosa non cambia.** I suoni sintetici non verificano niente. Le righe di
`dati/fonetica.jsonl` restano `attendibilita: "I"` e `da_verificare: true`, e il
`wav` che ne esce è dichiarato sintetico nella pagina, accanto al pulsante, non
in un documento che nessuno legge. Un parlante che dica la parola è ancora
l'unica cosa che chiuda la domanda.

Uso:
    python3 sintetizza.py             # scrive i wav e il manifesto
    python3 sintetizza.py --prova     # dice i numeri, non scrive
"""

from __future__ import annotations

import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from traduttore import voce  # noqa: E402
from traduttore.fonetica import Fonetica  # noqa: E402
from traduttore.varieta import codice_valido  # noqa: E402

TRASCRIZIONI = os.path.join(RADICE, "dati", "fonetica.jsonl")
MANIFESTO = os.path.join(RADICE, "dati", "sintesi.jsonl")
DESTINAZIONE = os.path.join(RADICE, "web", "sintesi")

# La dichiarazione che va accanto al pulsante. Una sola frase, e la stessa in
# pagina, nel manifesto e qui: se le tre divergono, vuol dire che una delle tre
# e' stata scritta quando si poteva ancora sperare che la cosa fosse diversa.
NOTA = ("voce sintetica generata in locale dalle regole dichiarate: non e' un "
        "parlante ferrarese e non verifica la trascrizione")

# Il periodo di questa frase, quando uno studente la legge. La dichiarazione
# tecnica sta nel manifesto; questa e' la frase che ferma il fraintendimento.
AVVERTIMENTO = ("Attenzione: questo suono lo ha fatto un programma, non una "
                "persona di Ferrara.")


def _riga(t: dict, esito: dict, nome_file: str) -> dict:
    """La riga del manifesto. Generata, non scritta a mano."""
    return {
        "id": "Y" + t.id.lstrip("T"),
        "riferimento": t.riferimento,
        "forma": t.forma,
        "ipa": esito["ipa"],
        "fonemi": esito["fonemi"],
        "file": nome_file,
        "varieta": t.varieta or "cittadino",
        "fonte": t.fonte,
        "attendibilita": "I",
        "da_verificare": True,
        "sintetica": True,
        # `scrivi_wav` ha gia' appeso la dichiarazione di sintesi, e vale la
        # pena lasciarla li' perche' sta dove la produce: se un giorno cambia
        # il modo in cui la voce viene generata, la frase da rileggere e' una
        # sola. Qui si aggiunge solo la parte per lo studente, che non serve a
        # chi verifica ma serve a chi ascolta.
        "nota": esito.get("nota") or NOTA,
        "avvertimento": AVVERTIMENTO,
    }


def main() -> int:
    solo_prova = "--prova" in sys.argv

    if not voce.percorso_espeak():
        print("espeak-ng non e' installato: senza un programma che suoni non "
              "si puo' fare una voce, e non si inventa un suono.")
        return 1

    fonetica = Fonetica.da_file(TRASCRIZIONI)
    righe, rifiutate = [], {}
    for t in fonetica.trascrizioni:
        esito = voce.voce(t.forma)
        if esito["problema"]:
            rifiutate["non suonabile"] = rifiutate.get("non suonabile", 0) + 1
            continue
        if esito["dubbi"]:
            # Il motivo conta: un dubbio sull'accento non e' la stessa cosa di
            # una `s` intervocalica, e chi legge il conto deve saperlo.
            rifiutate["con un dubbio dichiarato"] = \
                rifiutate.get("con un dubbio dichiarato", 0) + 1
            continue
        righe.append((t, esito))

    print("trascrizioni dichiarate   %4d" % len(fonetica.trascrizioni))
    print("suonate                  %4d   un file per parola, in web/sintesi/"
          % len(righe))
    print("non suonate              %4d   %s"
          % (sum(rifiutate.values()),
             ", ".join("%s %d" % kv for kv in sorted(rifiutate.items())) or "-"))
    print()
    print("Nessun suono e' un attestato: le righe restano `I` e "
          "`da_verificare`.")
    print("Un parlante ferrarese che dica la parola e' l'unica cosa che chiude")
    print("la domanda, e questa pagina non lo sostituisce.")
    print()
    if solo_prova:
        for t, esito in righe[:6]:
            print("  %-6s %-12s %-14s %s"
                  % (t.id, t.forma, esito["ipa"], "Y" + t.id.lstrip("T")))
        return 0

    if os.path.isdir(DESTINAZIONE):
        for nome in os.listdir(DESTINAZIONE):
            if nome.endswith(".wav"):
                os.remove(os.path.join(DESTINAZIONE, nome))
    os.makedirs(DESTINAZIONE, exist_ok=True)

    scritte = []
    for t, esito in righe:
        nome_file = "%s.wav" % t.id
        fatto = voce.scrivi_wav(t.forma, os.path.join(DESTINAZIONE, nome_file))
        if not fatto["wav"]:
            rifiutate["espeak-ng ha fallito"] = \
                rifiutate.get("espeak-ng ha fallito", 0) + 1
            continue
        scritte.append(_riga(t, fatto, nome_file))

    with open(MANIFESTO, "w", encoding="utf-8") as f:
        f.write("// I suoni sintetici che la pagina puo' far ascoltare.\n")
        f.write("//\n")
        f.write("// **Generato da `raccolta/sintetizza.py`, non si modifica a "
                "mano.**\n")
        f.write("// Un suono qui e' la lettura di una grafia, non una voce: e' "
                "generato in\n")
        f.write("// locale con `espeak-ng` dalle regole dichiarate in "
                "`dati/fonetica.jsonl`, e non\n")
        f.write("// verifica niente. Esistono solo per le parole che hanno una "
                "trascrizione\n")
        f.write("// dichiarata **senza dubbi**: dove la fonte non sa, questo "
                "file non c'e'.\n")
        f.write("//\n")
        f.write("// I file vanno in `web/sintesi/`, mai in `web/audio/`: "
                "quella cartella e' dei\n")
        f.write("// brani di persone vere e i controlli A1-A10 contano "
                "quello che c'e' dentro.\n")
        for riga in scritte:
            f.write(json.dumps(riga, ensure_ascii=False,
                              separators=(",", ":")) + "\n")

    print("scritti %d suoni in web/sintesi/ e %d righe in dati/sintesi.jsonl"
          % (len(scritte), len(scritte)))
    varieta_rotte = [r["id"] for r in scritte if not codice_valido(r["varieta"])]
    if varieta_rotte:
        print("AVVERTENZA: varieta' non valida in %s" % ", ".join(varieta_rotte))
    return 0


if __name__ == "__main__":
    sys.exit(main())
