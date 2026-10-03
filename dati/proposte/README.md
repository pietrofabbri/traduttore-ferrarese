# `dati/proposte/` — la coda di revisione del livello IA

Il livello 4 produce risposte che **non sono fonti**. Non entrano nel
glossario, non entrano nel corpus, non entrano nella pagina e non vengono
pubblicate. Quello che ne resta viene scritto qui, in chiaro, in un file che
chiunque può aprire.

Questa cartella è la **coda di revisione**: il posto da cui una risposta del
modello diventa, eventualmente, una voce del glossario — e il posto in cui
finisce se nessuno la approva.

## Come si scrive

Da solo, con `--ia`:

```bash
export ANTHROPIC_API_KEY=...
python3 -m traduttore.cli traduci "parola nuova" --ia
```

Ogni risposta che il motore ha accettato viene aggiunta in fondo a
`proposte.jsonl`. Il file si **append-e**, non si riscrive: non si perde niente
e si vede anche quello che nessuno ha approvato, che è informazione.

Con `--no-proposte` la scrittura non avviene. Serve quando si fa una prova e
non si vuole sporcare la coda.

Le risposte `non_so` **non** si registrano: il motore le dichiara già come
buchi, e riempiere la coda di «non so» è l'opposto di tenerla utile.

## I campi

| Campo | Che cosa vuol dire |
|---|---|
| `data` | il giorno in cui la risposta è arrivata |
| `direzione` | `it-fe` o `fe-it` |
| `parola` | la parola da tradurre, come è stata scritta |
| `traduzione` | quello che il modello ha risposto |
| `confidenza` | da 0 a 1, la sua confidenza, non la nostra |
| `dettaglio` | la riga di spiegazione che il modello è obbligato a dare |
| `fonti_citate` | gli id di voci o coppie che il modello ha detto di usare |
| `stato` | `da rivedere`, `approvata` o `respinta` |
| `promossa_a` | l'id della voce nata da questa proposta |

`fonti_citate` **non sono fonti della proposta**: sono i punti di riferimento
che il modello ha citato. Il controllo **M3** verifica che quegli id esistano
davvero, perché un modello che cita una voce inesistente ha risposto
inventando, e va saputo.

## Cosa non si può fare qui

1. **non si scrive `fonte`** e **non si scrive `attendibilita: "D"`**. Il
   controllo **M2** fallisce. Il passaggio da «il modello ha detto così» a «la
   fonte dice così» è una decisione di una persona che ha aperto il libro, e
   una riga non può prenderla al posto suo.
2. **non si copia una proposta nel glossario senza verificarla.** La verifica
   è su una fonte stampata (`RACCOLTA.md` §1), non sul fatto che la parola
   suonì bene.
3. **non si riempie `stato` per liberarsene.** Una proposta respinta resta nel
   file con `stato: "respinta"`: il file racconta anche i tentativi falliti, e
   un file in cui sparisce tutto quello che è stato respinto mente.

## Chi approva

**La domanda che questo progetto non ha ancora risolto**, e che è dichiarata
come aperta in `AGENTS.md`: il criterio di revisione deve nominare chi
approva. Fino a quel momento, la regola è la più conservatrice possibile —
una proposta è `da rivedere` e nessuno la tocca.

La sequenza che rende una proposta una voce, nell'ordine:

1. la parola si cerca in un vocabolario stampato (Ferri 1885, Nannini), con la
   sua pagina;
2. se la fonte c'è, si scrive la voce **dal vocabolario**, non dalla
   proposta, e la proposta si marca `approvata` con `promossa_a`;
3. se la fonte non c'è, la proposta si marca `respinta` e la parola resta un
   buco dichiarato.

Il modello serve per arrivare prima alla domanda, non per rispondere al posto
del libro.

## Lo stato adesso

`python3 -m traduttore.cli proposte` stampa la situazione. Adesso dice: zero
proposte, zero approvate, zero respinte — perché senza chiave e senza una
risposta da rivedere non c'è niente da avere.