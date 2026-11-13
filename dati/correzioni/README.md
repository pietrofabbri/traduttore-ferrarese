# `dati/correzioni/` — le correzioni, l'archivio e il margine

Questa cartella risponde a tre domande:

1. **Il traduttore ha sbagliato: come si dice?** Lo dice chi parla ferrarese, dalla
   pagina, con un pulsante.
2. **Quando la correzione fa parte del traduttore?** Non subito: quando i suoi pezzi
   hanno un **margine**, cioè abbastanza correzioni concordi e nessuna contraria, o
   quando qualcuno la conferma.
3. **Dove altro sbaglia allo stesso modo?** Lo cerca il programma, e le sue risposte
   (le inferenze) dicono dove guardare.

## Il flusso

Le correzioni arrivano da due pagine: il traduttore (una frase, «Correggila») e la
**revisione** (`web/revisione.html`, molte risposte insieme, una riga per risposta:
vedi `dati/revisione/README.md`). La forma della riga e il percorso sono gli stessi.

```
pagina «Invia» ──► segnalazione GitHub ──► workflow «Correzioni»
                     (etichetta correzione)     │
                                                ├─ importa: correzioni.jsonl, da_verificare
                                                ├─ promuove quello che ha il suo margine
                                                ├─ rigenera inferenze, regole, pagine
                                                └─ commit su main, chiude la segnalazione,
                                                   ripubblica il sito se il traduttore è cambiato
```

1. **Inviare.** Nella pagina del traduttore, sotto la traduzione: «La traduzione è
   sbagliata? Correggila». Si scrive la frase giusta, se si vuole la pronuncia IPA
   **fra parentesi quadre** (`[al ˈkan]`, un ascolto e non una lettura della grafia)
   e una nota, e si preme **Invia**. Nome, varietà, paese e token si impostano una
   volta sola in «Impostazioni di invio» e restano nel browser; senza nome la
   correzione è firmata «titolare del sito», senza varietà è `cittadino`.

   L'invio usa un **token GitHub**, che dipende da chi lo crea:

   - il **proprietario** del repository (`pietrofabbri`) crea un token
     *fine-grained* (Settings → Developer settings → Personal access tokens →
     Fine-grained tokens), con *Repository access* limitato a questo repository e
     il solo permesso **Issues: read and write**. E' la strada piu' stretta;
   - un **collaboratore** crea un token *classic* (stessa pagina, Tokens
     (classic)) con il solo permesso `public_repo`: GitHub non da' i token
     fine-grained per i repository di un altro account personale. Il token puo'
     scrivere su tutti i repository pubblici del collaboratore: va dato con una
     scadenza e revocato se si perde il computer.

   Il workflow accetta le segnalazioni del proprietario e dei collaboratori; la
   correzione e' firmata con il nome scritto nelle impostazioni. Senza token la pagina non chiama
   nessuno: «Copia» e «Scarica» danno la riga, che si importa a mano.
2. **Archiviare.** Il workflow `.github/workflows/correzioni.yml` importa la riga in
   `correzioni.jsonl` con `stato: "da_verificare"` e `da_verificare: true`, scrive da
   quale segnalazione viene (`origine`) e chiude la segnalazione con l'esito. Accetta
   solo segnalazioni di chi ha accesso al repository. **Una correzione archiviata
   non fa ancora parte del traduttore.**
3. **Promuovere.** Una correzione si scompone in **elementi**, e ognuno entra nel
   traduttore per conto suo quando ha il suo margine (soglie in `soglie.json`):

   | Elemento | Esempio | Soglia predefinita | Che cosa diventa |
   |---|---|---|---|
   | `parola` | «casa» → `ca` | 2 correzioni concordi, 0 contrarie | una voce `D` del glossario che **corregge** la voce sbagliata (che resta, e viene dopo) |
   | `funzionale` | «il» davanti a consonante → `al` | 2 e 0 | una **regola di frase** in `dati/regole_frase.json`: il motore la applica guardando la prima lettera della parola **ferrarese** che segue (vocale, consonante, fine), nel secondo passaggio (0.41) |
   | `grafia` | «`ŋ` → `n` dopo `a`, prima di `d`» | 3 e 0 | una voce `I` e `da_verificare` per ogni voce candidata della stessa fonte: è la regola applicata, non un ascolto |

   Una correzione è **contraria** a un elemento se per la stessa parola (e lo stesso
   contesto) scrive un'altra forma, o la lascia com'era. Quando **tutti** gli elementi
   di una correzione sono nel traduttore, entra anche lei per intero: la frase come
   coppia `D` (la prossima volta il traduttore la trova identica) e la pronuncia come
   trascrizione `D`. La correzione passa a `stato: "applicata"` e dice che cosa ha
   creato (`crea`).
4. **Confermare a mano.** Quando chi tiene il repository è sicuro di una correzione:
   `correzioni conferma X0001` la segna come confermata e i suoi elementi passano
   senza soglia alla prossima promozione; `correzioni applica X0001` conferma e
   promuove subito. Una correzione sbagliata si chiude con
   `correzioni respingi X0001 --motivo "..."`.

## I comandi

```bash
export PYTHONPATH=sorgenti
python3 -m traduttore.cli correzioni                         # che cosa aspetta
python3 -m traduttore.cli correzioni importa FILE --origine "..."
python3 -m traduttore.cli correzioni allinea X0001           # parola per parola
python3 -m traduttore.cli correzioni promuovi                # entra quello che ha il margine
python3 -m traduttore.cli correzioni conferma X0001          # confermata a mano
python3 -m traduttore.cli correzioni applica X0001           # confermata e promossa subito
python3 -m traduttore.cli correzioni respingi X0001 --motivo "..."
python3 -m traduttore.cli correzioni inferisci               # rigenera inferenze.jsonl
python3 -m traduttore.cli correzioni conferma-inferenza I0001 --voci V1,V2=forma \
    --chi "..." --varieta cittadino --dove "..."
```

`promuovi` stampa anche gli elementi **in attesa**, con chi li sostiene e chi li
smentisce: è la lista di che cosa manca per farli entrare.

## I file

| File | Che cosa contiene | Chi lo scrive |
|---|---|---|
| `correzioni.jsonl` | una riga per correzione: chi, varietà, l'italiano, la proposta del traduttore, la frase giusta, la pronuncia; lo stato e da dove viene | `correzioni importa`, `promuovi`, `conferma`, mai a mano |
| `soglie.json` | il margine di ogni tipo di elemento | a mano: cambiarlo cambia quando le correzioni entrano |
| `inferenze.jsonl` | le regole di grafia ricavate dalle correzioni, con chi le sostiene, chi le smentisce e le voci candidate | `correzioni inferisci`: è **generato** |
| `../regole_frase.json` | le regole di frase promosse | `correzioni promuovi`, mai a mano |

## Le inferenze, e che cosa ci fa Claude

Un'inferenza confronta una forma sbagliata con quella giusta e ne ricava la
sostituzione con una lettera di contesto per parte; poi la cerca fra le voci **della
stessa fonte** (la stessa grafia). Usa anche i giudizi della verifica a campione con
`come_si_dice`. Sotto la soglia `grafia` non cambia niente; sopra, applica la regola
alle candidate come voci `I` e `da_verificare`, mai `D`.

Quando gli si chiede di lavorare sulle correzioni, Claude legge `correzioni` e le
inferenze e fa il lavoro che il programma non sa fare:

- due inferenze con lo **stesso cambiamento** in contesti diversi sono probabilmente
  una regola più larga: Claude lo dice e propone le correzioni che servirebbero a
  confermarla;
- un elemento **smentito** riguarda probabilmente una parola, non la grafia;
- un elemento in attesa con **una sola** correzione si conferma meglio con una frase
  nuova che lo contenga: Claude suggerisce quali frasi tradurre e correggere;
- una regola che **contraddice una fonte** (`dati/regole_grammaticali.json`,
  `dati/conversione_bigoni.json`) si segnala.

## I controlli

| Codice | Che cosa guarda |
|---|---|
| X1 | id mancante o duplicato |
| X2 | correzione senza `chi` |
| X3 | varietà fuori dalle cinque |
| X5 | senza l'italiano o senza il ferrarese |
| X6 | pronuncia fuori dalle quadre, o con simboli che non sono IPA |
| X7 | stato fuori da `da_verificare`, `applicata`, `respinta` |
| X8 | correzione applicata che non dice che cosa ha creato, o rimanda a righe che non ci sono |
| X9 | data non nella forma AAAA-MM-GG |
| X10 | correzione respinta senza motivo |
| Z1 | inferenza con `fonte` o `attendibilita D`: un'inferenza non è un dato |
| Z2 | inferenza che non dice da quali correzioni viene |
| Z3 | inferenza su una voce che non c'è |
| Z4 | regola di frase con un contesto che non è vocale, consonante o fine |
| Z5 | regola di frase senza le correzioni da cui viene, o con correzioni che non ci sono |

(X4, il consenso, c'era nella 0.39 e non c'è più: dalla 0.40 il sito lo usa chi lo
tiene.)
