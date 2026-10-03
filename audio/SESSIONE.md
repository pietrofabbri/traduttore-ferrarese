# La sessione di registrazione

Una pagina di istruzioni per una cosa che si fa in una stanza, davanti a una
persona, con il telefono sul tavolo. È scritta per chi non l'ha mai fatto e per
chi l'ha già fatto male.

La stima di quanto tempo serve sta in `STIMA-AUDIO.md`; qui c'è il come.

## Prima: il consenso, sempre

**Il consenso si chiede e si firma prima di premere il pulsante.** Non dopo,
non «tanto poi vediamo». Un registratore acceso prima del consenso è una cosa
che non si rimedia, e non è una cosa che si scarica dalla memoria del telefono.

Il testo da leggere ad alta voce è `modello-consenso.txt`. Si legge, si
spiega, si firma, e la copia firmata si tiene **fuori dal repository**: nel
repository ci finisce solo la riga del manifesto con `consenso: "scritto"`, e
quella riga è la prova che il consenso c'era. Il modulo firmato è un
documento personale di chi ha parlato.

Per i minori di età il consenso è di chi esercita la responsabilità. E vale per
tutti la regola che vale per il gioco: **i dati degli studenti non entrano nel
repository**, quindi la voce di un compagno di classe si registra in locale e
nel repository finisce solo il testo.

## La stanza e l'attrezzatura

- una stanza tranquilla: non in soggiorno con la televisione accesa, non
  vicino a un finestrone;
- il telefono o il registratore a **mezzo metro dalla bocca**, mai sul tavolo
  lontano: la distanza si sente e non si corregge dopo;
- il telefono in **modalità aereo**: nessuna notifica entra in un file audio,
  e nessuna richiesta di rete passa mentre si registra una persona;
- tre minuti di registrazione di prova, riascoltati **subito**: se si sente il
  ronzio o la televisione, si cambia stanza. Una registrazione sporca non si
  sistema con un filtro.

## I venti minuti, nell'ordine

L'ordine è importante, e non è estetico: le cose che costano fatica stanno
prima, quando la persona è fresca.

| Minuti | Che cosa | Perché lì |
|---|---|---|
| 0–2 | il consenso, e poi si registra il *nome* della persona come lo vuole essere citata | senza il nome il brano non si pubblica |
| 2–5 | **parlato libero**: «mi parli di un piatto che le piaceva, di un posto, di quando tornava a casa la domenica» | è l'unica cosa che non si sa produrre, quindi è l'unica che vale |
| 5–15 | **le frasi**, non le parole isolate | una parola isolata non si traduce in nessuna lingua |
| 15–18 | **lista di venti parole**, a circa dieci secondi l'una | è la lista che allinea l'audio al glossario |
| 18–20 | **le domande sulla varietà**: «questa parola la dicevano anche a Bondeno?», «da lei la dicevano differently?», «c'era qualcuno che la diceva in un altro modo?» | è l'unico modo onesto per sapere che una parola è di un posto solo |

Le domande finali sono quelle che riempiono il campo `varieta`. Se la persona
non lo sa, si scrive `I` e si lascia la domanda aperta: **meglio una varietà
incerta che una inventata**.

## Cosa non si chiede

- **non si chiede di leggere un testo scritto** se non è un testo autentico: la
  lettura a voce alta è un'altra lingua, e il gioco ha bisogno di parlato;
- **non si chiede di tradurre** in italiano: quello non è un dato di questa
  lingua, e metterlo accanto alla voce confonde chi ascolta;
- **non si corregge** durante il racconto. La correzione è un altro passaggio,
  e va fatta dopo, da un secondo ascoltatore.

## Dopo: cosa succede al file

1. il grezzo si tiene **fuori dal repository** (i `.m4a` sono in `.gitignore`);
2. si pulisce con l'unico comando dichiarato:

   ```bash
   ffmpeg -i grezzo.m4a -ac 1 -ar 22050 -b:a 48k -af "highpass=f=80, loudnorm" A0001.mp3
   ```

3. si scrive la riga in `dati/audio.jsonl`, con `riferimento` alla voce o alla
   coppia che il brano contiene, `varieta`, `lettubilita` **CEFR vero** e
   `durata` misurata;
4. si verifica con `python3 -m traduttore.cli audio` che la riga non abbia
   scambiato i tre permessi (consenso, licenza, `pubblicabile`);
5. solo adesso la parola, e la sua trascrizione IPA, possono passare da `I` a
   `D`.

## Il costo vero di una sessione

Non è mezz'ora: è mezz'ora **più** la trascrizione. Un'ora di audio pulito
sono circa quattro ore di trascrizione (`STIMA-AUDIO.md`, H6), perché la
punteggiatura del parlato va decisa parola per parola e le forme dialettali
vanno capite prima di essere scritte.

E la parte che nessuna stima quantifica bene: **trovare la persona**. Il
ferrarese si parla in famiglia, e chiedere a qualcuno di registrare una
sorella o un vicino è più difficile di quanto sembri. Per questo la stima
conta le sessioni e non le persone: ogni sessione ha probabilmente bisogno di
due contatti.

## Lo stato adesso

`python3 -m traduttore.cli audio` dice: zero brani. La prima sessione non è
avvenuta, e questa pagina è il modo perché accada. Quando avviene, la stima
va ricalcolata con i dati veri e questa pagina va corretta dove sbagliava.