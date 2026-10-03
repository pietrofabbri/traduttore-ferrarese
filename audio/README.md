# `audio/` — i brani registrati

Questa cartella è **vuota**, e lo è per una ragione precisa: nessuna
registrazione di nessuna persona è ancora stata autorizzata per entrare nel
progetto. Non è un posto dove mettere i file per poi dichiararli: è il posto
dove finiscono i brani che hanno già superato i tre controlli.

## I tre controlli, e perché sono tre

Un brano entra in `audio/` e nella pagina solo se ha tutte e tre le cose:

| # | Condizione | Campo | Chi decide |
|---|---|---|---|
| 1 | la persona ha detto di sì | `consenso` | la persona, per iscritto o a verbale |
| 2 | il file è di chi può ridistribuirlo | `licenza` | chi ha registrato e con quale accordo |
| 3 | si decide di pubblicarlo | `pubblicabile` | chi cura il progetto, per sempre |

Il terzo non è una formalità: **un brano registrato a casa di qualcuno resta
`false` per sempre**, anche se la persona ha detto sì a registrarla. La
registrazione è di chi parla; la pubblicazione è una decisione di progetto,
e non è automatica.

Per i minori, il consenso è di chi esercita la responsabilità, e va messo per
iscritto. **I dati degli studenti non entrano nel repository**: questo vale
anche, e soprattutto, per le voci dei compagni di classe, che sono la cosa che
questo progetto vorrebbe più di tutte e che non ci devono stare.

## Come si registra, e con quali formati

La pagina funziona da un file, senza connessione: quindi i file devono essere
piccoli e devono essere mp3. Non c'è motivo di tenere un wav da 40 MB quando
la stessa frase in mp3 a 22 kHz mono sta in 30 KB.

Una registrazione breve e pulita si prepara così (ffmpeg, in locale, senza
rete):

```bash
ffmpeg -i grezzo.m4a -ac 1 -ar 22050 -b:a 48k -af "highpass=f=80, loudnorm" A0001.mp3
```

Tre scelte, e ognuna ha un motivo:

- **mono**: la voce è una, e stereo qui è solo peso;
- **22050 Hz**: è la frequenza oltre la quale l'orecchio di uno studente non
  sente la differenza in una voce parlata;
- **`highpass`**: toglie il ronzio, che si sente sempre e non si sente mai
  finché non lo togli.

E si registra **in silenzio**. Non in una stanza con la televisione accesa,
non vicino a un finestrone. Una registrazione sporca non si corregge, e
un minuto di silenzio fa più per la qualità di qualsiasi filtro.

## Come si scrive una riga del manifesto

Una riga per brano in `dati/audio.jsonl`, e la riga è la prova, non
l'indice:

```json
{"id":"A0001","riferimento":"F0002","file":"A0001.mp3","testo":"a n'agh ved brisa","italiano":"non ci vedo niente","voce":"come la persona si fa chiamare","luogo":"Bondeno, 2026","varieta":"occidentale","contesto":"racconto","licenza":"CC BY 4.0","consenso":"scritto","pubblicabile":true,"lettibilita":"A1","durata":7,"nota":"registrato al tavolo di cucina, senza rumori"}
```

I campi che non si possono saltare:

- **`voce`**: come la persona si fa chiamare e come vuole essere citata. Non
  il nome del file, non l'etichetta del registratore. Il controllo **A9**
  fallisce se c'è il consenso ma non c'è questa riga, perché un consenso
  senza nome non si può onorare.
- **`varieta`**: una delle cinque. È il campo che distingue una voce di
  Bondeno da una voce di città, ed è quello che il gioco mostra.
- **`lettibilita`**: A1, A2, B1, B2 — **CEFR vero**, non metafora. Un brano
  con dentro `magnàr` due volte non è un brano A1 solo perché è breve.
- **`durata`**: in secondi, se qualcuno l'ha misurata. Serve a non promettere
  a uno studente un brano di quattro minuti che è di quaranta secondi.
- **`riferimento`**: l'id della voce o della coppia che il brano contiene. Se
  manca, il brano si sente ma non si trova: il riproduttore non ha modo di
  accostarlo alla parola che lo studente sta cercando.

## Da dove cominciare

1. **Il portale dei dialetti della Regione Emilia-Romagna**
   (`dati/fonti.json`, S007) annuncia testi e audio di autori e autrici dei
   dialetti del territorio ferrarese, con Floriana Guidetti e «Storie dei
   nostri dialetti». Sono registrazioni di altre persone: si chiede il
   permesso alle loro condizioni, non si scarica.
2. **Qualcuno che si sa`** della zona, e che vuole parlare. Le prime quattro
   varietà hanno tutte e quattro i loro vuoti, e si comincia dall'occidentale
   perché è quella dove la differenza dal cittadino si sente di più.
3. **Il consenso prima**, il file dopo, la riga del manifesto per ultima. In
   quest'ordine, sempre: è l'ordine che non lascia spazio a un file di troppo.

## Lo stato adesso

`python3 -m traduttore.cli audio` stampa la situazione. Adesso dice: zero
brani, zero pubblicabili, zero pronti. È il numero giusto: non è un posto
vuoto da riempire, è un numero che non si può gonfiare.