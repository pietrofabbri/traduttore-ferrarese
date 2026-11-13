# `dati/revisione/` — le domande della pagina «Revisione»

`domande.json` contiene le domande della pagina `web/revisione.html`, e **solo
l'italiano**: 79 frasi di tutti i giorni, le 300 parole più usate, 80 singolari e
plurali, 30 preposizioni, 30 pronomi e particelle, 640 forme di 20 verbi (presente,
imperfetto, futuro, condizionale, passato prossimo, participio). Sono le stesse del
foglio di revisione.

**La traduzione proposta non è qui.** La calcola il motore quando si genera la
pagina (`sorgenti/traduttore/revisione.py`, `per_la_pagina`), quindi la pagina
mostra sempre quello che il traduttore risponde oggi; le parole che il motore non sa
sono segnate (campo `b`) e per quelle la pagina non offre «sì».

## Dalle risposte ai dati

La pagina non scrive niente qui. Le risposte partono, premendo **Invia**, come
**correzioni** (`dati/correzioni/`), una riga per risposta, firmata con il nome e la
varietà scritti nelle impostazioni:

| risposta | riga di correzione |
|---|---|
| sì | `ferrarese` uguale alla `proposta`: una conferma |
| no | `ferrarese` con la forma scritta da chi risponde |
| non so | nessuna riga |

Gli altri modi di dirlo e la nota vanno in `nota`, insieme all'id della domanda
(`revisione F012; altre forme in cittadino: ...`). Da lì il percorso è quello di ogni
correzione: archiviata **da verificare**, poi promossa a pezzi quando ha il suo
margine (`dati/correzioni/README.md`). Le risposte di una persona nella pagina
restano nel suo browser finché non le invia, e una segnalazione porta al più 80
risposte.

## Le fonti delle domande

Le 300 parole vengono da *FrequencyWords* di Hermit Dave (lista `it_50k`, dai
sottotitoli di OpenSubtitles), licenza CC-BY-SA 4.0:
<https://github.com/hermitdave/FrequencyWords>. Le altre domande sono scritte per
il progetto: sono domande, non dati sul ferrarese, e non hanno bisogno di una fonte.
Una domanda nuova si aggiunge a mano in `domande.json` con un `id` nuovo; gli `id`
non si riusano, perché le risposte già inviate li citano.
