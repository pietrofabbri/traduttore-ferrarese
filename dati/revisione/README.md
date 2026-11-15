# `dati/revisione/` — le domande della pagina «Revisione»

`domande.json` contiene le domande della pagina `web/revisione.html`, e **solo
l'italiano**: 79 frasi che insegnano le regole, 115 frasi di ogni giorno in otto
situazioni, le 300 parole più usate e altre 700 (dalla 301esima, solo quelle che il
glossario conosce in italiano), 80 singolari e
plurali, 30 preposizioni, 30 pronomi e particelle, 640 forme di 20 verbi (presente,
imperfetto, futuro, condizionale, passato prossimo, participio). Sono le stesse del
foglio di revisione.

**La traduzione proposta non è qui.** La calcola il motore quando si genera la
pagina (`sorgenti/traduttore/revisione.py`, `per_la_pagina`), quindi la pagina
mostra sempre quello che il traduttore risponde oggi; le parole che il motore non sa
sono segnate (campo `b`) e per quelle la pagina non offre «sì».

## Dalle risposte ai dati

La pagina non scrive niente qui. Chi risponde dice prima chi è (nome, paese,
varietà, consenso a pubblicarli; 18 anni). Le risposte partono, premendo **Manda le
risposte**, come **correzioni** (`dati/correzioni/`), una riga per risposta, firmata
con quel nome:

- **con un token** (chi cura il progetto, i collaboratori): direttamente, come
  segnalazione su GitHub;
- **senza** (chiunque altro): con il menu del telefono (WhatsApp, posta) o «Copia il
  messaggio», a chi cura il progetto, che incolla il messaggio nella pagina («Per chi
  cura il progetto» → «Risposte ricevute») e lo invia con il suo token. Le righe
  restano firmate da chi ha risposto; chi le incolla fa da garante.

Nel modo **Controlla la traduzione**:

| risposta | riga di correzione |
|---|---|
| sì | `ferrarese` uguale alla `proposta`: una conferma |
| no | `ferrarese` con la forma scritta da chi risponde |
| non so | nessuna riga |

Nel modo **Traduci tu** la persona vede solo l'italiano e scrive la sua forma:
la riga ha la forma scritta in `ferrarese` e la proposta del motore in `proposta`
(se sono uguali è una conferma). La nota comincia con `traduci <id>` invece di
`revisione <id>`.

Gli altri modi di dirlo e la nota vanno in `nota`, insieme all'id della domanda
(`revisione F012; altre forme in cittadino: ...`). Da lì il percorso è quello di ogni
correzione: archiviata **da verificare**, poi promossa a pezzi quando ha il suo
margine (`dati/correzioni/README.md`). Le risposte di una persona nella pagina
restano nel suo browser finché non le invia, e una segnalazione porta al più 80
risposte.

## Le fonti delle domande

Le 1000 parole vengono da *FrequencyWords* di Hermit Dave (lista `it_50k`, dai
sottotitoli di OpenSubtitles), licenza CC-BY-SA 4.0:
<https://github.com/hermitdave/FrequencyWords>. Le altre domande sono scritte per
il progetto: sono domande, non dati sul ferrarese, e non hanno bisogno di una fonte.
Una domanda nuova si aggiunge a mano in `domande.json` con un `id` nuovo; gli `id`
non si riusano, perché le risposte già inviate li citano.
