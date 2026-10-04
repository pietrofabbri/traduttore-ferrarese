#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fa ascoltare le voci disponibili, su parole dove le regole sono difficili.

Il problema che questo script non risolve, e che va detto prima di tutto:
**la voce non e' la pronuncia.** Una voce e' un timbro. Il ferrarese suona
sbagliato perche' i fonemi li produce `traduttore.voce` con le regole
dichiarate in `dati/fonetica.jsonl`, e quelle regole descrivono l'italiano
schiacciato in una grafia romagnola. Cambiare voce cambia il timbro e lascia
la pronuncia com'e'. Ecco perche' il primo tentativo di questa pagina e' una
pagina di confronto e non una scelta: se due voci suonano diverse e una
sembra meno falsa, quella e' la risposta alla domanda che e' stata posta
«quale suono meno male», che e' diversa da «parla ferrarese».

**Perche' queste parole e non altre.** Una pool di parole facili non distingue
le voci: tutte dicono «questa si sente male» e il confronto non serve a
niente. Qui le parole sono scelte perche' ognuna mette alla prova una regola
diversa, e la ragione e' scritta accanto a ciascuna. Se una voce e' buona su
`ghe` e cattiva su `majàl`, il difetto e' della voce; se e' cattiva su tutte, il
difetto e' delle regole. Sono due problemi diversi e si risolvono in due modi
diversi, quindi la pagina serve anche a distinguerli.

**Dove finiscono i file.** In `raccolta/lavorato/audizione/`, che e' gitignorato
come tutto il resto di `lavorato/`: e' il mezzo, non il risultato. Il risultato
e' una **decisione dichiarata** — quale voce ha scelto una persona e perche' —
che va scritta in `dati/` e nel registro. Qui non si scrive nessuna scelta, perche'
una scelta non la prende uno script: la prende chi ha ascoltato.

Uso:
    python3 raccolta/audizione.py                # la pagina e i suoni
    python3 raccolta/audizione.py --voce it+f4   # una voce sola
    python3 raccolta/audizione.py --apri         # dice dove si apre
"""
from __future__ import annotations

import argparse
import html
import io
import os
import subprocess
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

DESTINAZIONE = os.path.join(RADICE, "raccolta", "lavorato", "audizione")

# Le parole di prova, e **perche'** ognuna c'e'. Una riga senza motivo non
# entra: una pool non spiegata e' una lista di parole a caso, e una lista di
# parole a random non distingue niente.
#
# `attesa` e' quello che la regola dice che dovrebbe uscire. Non e' un giudizio:
# e' la trascrizione che il progetto ha dichiarato per quella grafia, e serve a
# sentire il disaccordo fra quello che e' scritto e quello che si sente.
POOL = [
    # La `gh` ferrarese e' /g/, non /g/ palatale. In italiano la stessa sequenza
    # e' diversa, quindi e' il primo caso dove la voce «inglese che parla
    # ferrarese» si sente di piu'.
    ("ghe", "/ɡe/", "la `gh` e' /g/: in italiano non lo sarebbe"),
    # La `z` aspra. Il libro del 1853 rende /s/ dove l'italiano ha /dz/, e
    # questa e' una delle quattro righe che il controllo F14 dichiara in
    # disaccordo con le regole in testa al file.
    ("sittadìn", "/sittaˈdin/", "`z` aspra resa /s/, non /dz/"),
    # `ci` davanti a `i` diventa /tʃ/ in ferrarese. E' la regola che non esiste
    # in italiano e che un orecchio italiano sente subito.
    ("principiar", "/prinˈtʃipjar/", "`ci` davanti a `i` diventa /tʃ/"),
    # `nc` diventa /nk/. Un fonema che in italiano non esiste.
    ("mancà", "/manˈka/", "`nc` reso /nk/"),
    # `gn` diventa /ɲ/ palatale, non nasale semplice.
    ("magnàr", "/maˈɲnar/", "`gn` reso /ɲ/ palatale"),
    # La `j` e' semivocale e non una consonante: la differenza si sente in
    # `majàl`, che si dice come «maial» ma non come una sequenza di due suoni.
    ("majàl", "/maˈjal/", "`j` semivocale, non consonante"),
    ("oj", "/oj/", "due suoni, il secondo e' la vocale finale"),
    # La `v` iniziale. In ferrarese e' bilabiale come la `b` italiana.
    ("ved", "/ved/", "`v` iniziale, bilabiale in ferrarese"),
    # L'accento cade sull'ultima sillaba anche nei casi in cui l'italiano lo
    # mette sulla penultima: e' cio' che rende una frase riconoscibile come
    # non italiana piu' di qualunque scelta di voce.
    ("dottór", "/dotˈtor/", "accento sulla finale, non sulla penultima"),
    ("padrón", "/paˈdron/", "accento sulla finale"),
    # Il punto debole dichiarato: la `z` intervocalica e' il suono su cui la
    # stessa fonte non e' d'accordo con se stessa.
    ("casa", "/kasa/", "**la `z` intervocalica e' il punto debole dichiarato**"),
    # L'apostrofo segna il contatto e non si legge: una voce che lo legge o che
    # lo inghiotte dice male questa parola.
    ("n'agh", "/naɡ/", "l'apostrofo segna il contatto, non si legge"),
    # Monosillaba senza accento nella fonte: quello che non si deve aggiungere.
    ("brisa", "/brisa/", "nessun accento nella fonte: non se ne deve mettere"),
]

# Le voci in prova. **Dichiarate, non scoperte**: se la lista cambiasse a ogni
# esecuzione il confronto non ripetibile, e un confronto che non si ripete non
# e' un confronto. Sono le varianti di espeak-ng applicate all'italiano, che e'
# l'unica lingua romanza che questa installazione offre — non c'e' l'emiliano
# romagnolo, che e' la famiglia giusta, quindi qui si puo' scegliere il timbro
# e non la lingua. Il nome di ogni variante porta con se' `+`, e con `-v` vuol
# dire «questa voce applicata a questa lingua».
# La lista **di riserva**, per quando `dati/fonetica.jsonl` non dichiara
# nessun voto. Quando il file li dichiara, sono quelli che si sentono: una
# griglia che confronta voci diverse da quelle che il progetto puo' usare
# e' una griglia che non serve a niente.
VOCI = ["it", "it+f2", "it+f3", "it+f4", "it+f5",
        "it+adam", "it+Antonio", "it+Belinda", "it+Denis", "it+croak"]


def voti_dichiarati() -> list:
    """I voti che il file delle regole dichiara, o la lista di riserva."""
    from traduttore import voce
    return voce.voci_dichiarate() or list(VOCI)

NOTA_VOCE = (
    "Nessuna di queste voci parla ferrarese: e' un italiano che pronuncia "
    "grafia ferrarese secondo le regole dichiarate dal progetto, che sono "
    "quelle dell'italiano. Il timbro si sceglie qui; la pronuncia si "
    "corregge nelle regole, e quello e' lavoro di una persona."
)


def _impronta(percorso: str) -> str:
    """L'impronta del file generato, o `''` se il file non c'e'.

    Serve a una cosa sola, e serve perche' e' gia' successo: una voce
    che il programma accetta puo' produrre **lo stesso file** di un'altra,
    e allora la colonna della griglia e' identica a tutte le altre e
    sembra una scelta che non c'e'. Il file e' la prova.
    """
    import hashlib
    if not (percorso and os.path.isfile(percorso)):
        return ""
    with open(percorso, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _genera(nome_voce: str, forma: str, percorso: str) -> str:
    """Il `wav` della parola, con la voce scelta. Torna la nota, non il file.

    La nota torna anche quando il file c'e': un programma che fallisce in
    silenzio e' un programma che sembra funzionare.

    Il parametro si chiama `nome_voce` e non `voce` perche' dentro questa
    funzione `voce` e' il modulo, e un parametro con lo stesso nome lo copre:
    la prima stesura finiva col modulo al posto della stringa e moriva su
    `expected str, not module`, che non diceva niente della causa.
    """
    from traduttore import voce  # noqa: E402
    programma = voce.percorso_espeak()
    if not programma:
        return "espeak-ng non e' installato"
    esito = voce.voce(forma)
    if esito.get("problema"):
        return esito["problema"]
    comando = [programma, "-v", nome_voce, "-s", str(voce.VELOCITA_DEFAULT),
               "-w", percorso, "[[%s]]" % esito["fonemi"]]
    fatto = subprocess.run(comando, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    if fatto.returncode != 0 or not os.path.isfile(percorso):
        return "espeak-ng ha fallito: %s" % fatto.stderr.decode("utf-8", "replace").strip()
    return ""


def _pagina(varianti, risultati, uguali, dichiarata) -> str:
    """La pagina dell'audizione: una tabella parole per voci.

    Ogni cella e' un file audio e nient'altro. Nessun punteggio e nessuna
    stellina: un numero qui sarebbe un giudizio che lo script non puo'
    formulare, e un giudizio travestito da numero e' la cosa che questo progetto
    non accetta. La colonna finale dice solo **quanti suoni la voce ha fatto**,
    che e' un fatto, non una qualita'.
    """
    sc = html.escape
    parti = ["<!doctype html>", "<html lang=it>", "<head>",
             "<meta charset=utf-8>",
             "<title>Audizione delle voci — ferrarese</title>",
             "<style>",
             "body{font-family:system-ui,sans-serif;margin:2rem;max-width:70rem}",
             "table{border-collapse:collapse;width:100%}",
             "th,td{border:1px solid #ccc;padding:.4rem;vertical-align:top}",
             "th{background:#f2f2f2;text-align:left}",
             "audio{width:9rem;height:2rem}",
             ".vuoto{color:#666;font-size:.85rem}",
             ".motivo{font-size:.8rem;color:#555}",
             ".uguale{font-size:.75rem;color:#a33}",
             "</style>", "</head>", "<body>",
             "<h1>Audizione delle voci</h1>",
             '<p class="vuoto">%s</p>' % sc(NOTA_VOCE),
             "<table>", "<tr><th>parola</th><th>attesa</th>",
             "<th>perche' e' nella pool</th>"]
    for v in varianti:
        parti.append("<th>%s</th>" % sc(v))
    parti.append("</tr>")
    for forma, attesa, motivo, suoni in risultati:
        parti.append("<tr><td><strong>%s</strong></td><td>%s</td>"
                     '<td class="motivo">%s</td>' % (sc(forma), sc(attesa), sc(motivo)))
        for v in varianti:
            file_ = suoni.get((forma, v))
            if file_:
                # `preload="metadata"` e non `"none"`: la pagina dei suoni
                # dichiara gia' che un lettore fermo a `0:00 / 0:00` sembra
                # rotto e che chi crede sia rotto non lo preme. Qui sono
                # centotrenta celle e il totale fa 6 megabyte, ma
                # `metadata` scarica solo le intestazioni: la durazione si vede
                # e l'audio no, che per una griglia da confrontare e' quello
                # che serve.
                suono = ('<audio controls preload="metadata" src="%s"></audio>'
                         % sc(file_))
                if file_ in uguali:
                    # La colonna che sembra una scelta e non lo e'. Meglio
                    # una riga in piccolo che una scelta che non c'e'.
                    suono += ('<br><span class="uguale">file identico a quello '
                              'di `%s`</span>' % sc(dichiarata))
                parti.append("<td>%s</td>" % suono)
            else:
                parti.append('<td class="vuoto">—</td>')
        parti.append("</tr>")
    parti.append("</table>")
    falliti = risultati and sum(1 for r in risultati for v in varianti
                                if not r[3].get((r[0], v)))
    parti.append('<p class="vuoto">%d suoni generati.</p>'
                 % (len(risultati) * len(varianti) - (falliti or 0)))
    parti.append("</body></html>")
    return "\n".join(parti)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--voce", action="append",
                    help="una voce sola; ripetibile. Se non si dice, quella "
                         "che dichiara dati/fonetica.jsonl")
    ap.add_argument("--apri", action="store_true",
                    help="stampa il percorso della pagina")
    args = ap.parse_args()

    varianti = args.voce or voti_dichiarati()

    from traduttore import voce as modulo_voce  # noqa: E402
    if not modulo_voce.percorso_espeak():
        print("espeak-ng non e' installato: senza un programma che suoni non "
              "si puo' fare una voce, e non si inventa un suono.")
        return 1

    if not os.path.isdir(DESTINAZIONE):
        os.makedirs(DESTINAZIONE)

    dichiarata = (varianti[0] if len(varianti) == 1
                  else (modulo_voce.voce_dichiarata()
                        if modulo_voce.voce_dichiarata() in varianti
                        else varianti[0]))

    def _nome(voce, forma):
        return "%s_%s.wav" % (voce.replace("+", "-"), _pulito(forma))

    risultati = []
    impronte = {}
    for forma, attesa, motivo in POOL:
        suoni = {}
        for v in varianti:
            percorso = os.path.join(DESTINAZIONE, _nome(v, forma))
            nota = _genera(v, forma, percorso)
            impronte[_nome(v, forma)] = _impronta(percorso)
            if not nota:
                # Il percorso nella pagina e' **relativo**, non `file://` con
                # l'indirizzo assoluto: cosi' la pagina si apre sia con un
                # doppio clic dal disco sia da un qualsiasi server, e non
                # funziona solo perche' la cartella sta nel posto in cui
                # l'ho generata.
                suoni[(forma, v)] = os.path.basename(percorso)
        risultati.append((forma, attesa, motivo, suoni))

    # Le colonne che suonano come la voce dichiarata: una colonna e' una
    # scelta solo se produce un suono che le altre non producono. Il
    # confronto e' fra file e non fra giudizi.
    prima = _nome(dichiarata, POOL[0][0])
    riferimento = impronte.get(prima)
    uguali = set()
    if riferimento:
        uguali = set(n for n, i in impronte.items()
                      if i and i == riferimento)
        uguali.discard(prima)
    per_voce = {}
    for v in varianti:
        mio = impronte.get(_nome(v, POOL[0][0]))
        per_voce[v] = sum(1 for n, i in impronte.items()
                          if mio and i == mio and n != _nome(v, POOL[0][0]))

    pagina = os.path.join(DESTINAZIONE, "index.html")
    with io.open(pagina, "w", encoding="utf-8", newline="\n") as f:
        f.write(_pagina(varianti, risultati, uguali, dichiarata))

    print("%d parole × %d voci -> %s"
          % (len(POOL), len(varianti), pagina))
    se_niente = [v for v, n in sorted(per_voce.items()) if n]
    if se_niente:
        print()
        print("Queste colonne hanno prodotto **lo stesso file** di `%s`:"
              % dichiarata)
        for v in se_niente:
            print("  %s" % v)
        print("Una colonna che suona come un'altra non e' una scelta: in "
              "griglia e' scritto sotto la cella, perche' una scelta che non "
              "cambia niente e' peggio di nessuna scelta.")
    for forma, attesa, motivo, suoni in risultati:
        mancanti = [v for v in varianti if (forma, v) not in suoni]
        if mancanti:
            print("  %s: nessun suono per %s" % (forma, ", ".join(mancanti)))
    print()
    print("Nessun punteggio: la scelta la fa chi ascolta. Il risultato della")
    print("scelta va scritto in `dati/` e dichiarato nel registro, non qui.")
    if args.apri:
        print("apri: file://%s" % pagina)
    return 0


def _pulito(s: str) -> str:
    import re
    return re.sub(r"[^0-9a-z]+", "-", s.lower()).strip("-")


if __name__ == "__main__":
    raise SystemExit(main())