# `dati/correzioni/` — le correzioni dei parlanti, e le inferenze

Questa cartella risponde a due domande:

1. **Il traduttore ha sbagliato: come si dice?** Lo dice un parlante, e la sua
   risposta diventa un dato con il suo nome.
2. **Dove altro sbaglia allo stesso modo?** Lo cerca il programma, confrontando la
   forma sbagliata con quella giusta. La sua risposta non è un dato: è un elenco di
   voci da far confermare.

La linea fra le due è la regola del progetto (`AGENTS.md` §1): **una correzione è
una fonte, un'inferenza no.**

## I due file

| File | Che cosa contiene | Chi lo scrive |
|---|---|---|
| `correzioni.jsonl` | una riga per correzione: chi, che varietà, consenso, l'italiano, che cosa proponeva il traduttore, come si dice, la pronuncia fra quadre; poi lo stato | `correzioni importa` e `correzioni conferma`, mai a mano |
| `inferenze.jsonl` | le regole di grafia ricavate dalle correzioni, con chi le sostiene, chi le smentisce e le voci della stessa fonte che cambierebbero | `correzioni inferisci`: è **generato**, e si rigenera |

Una correzione:

```json
{"id": "X0001", "stato": "da_applicare", "data": "2026-11-04",
 "chi": "Maria Rossi", "luogo": "Ferrara", "varieta": "cittadino", "consenso": true,
 "italiano": "andare", "proposta": "aŋdàr", "ferrarese": "andàr", "ipa": "[anˈdar]"}
```

Un'inferenza:

```json
{"id": "I0001", "descrizione": "«ŋ» → «n» dopo «a», prima di «d»", "famiglia": "S006",
 "da": ["X0001"], "supporto": 1, "contro": [], "candidate": 60,
 "esempi": [{"voce": "V10405", "ora": "abaŋdóŋ", "proposta": "abandóŋ", "italiano": "abbandono"}],
 "stato": "da rivedere", "giudizio": "una sola correzione: è un indizio, ..."}
```

## Da dove arrivano: la pagina

Nella pagina del traduttore, sotto ogni traduzione, c'è **«La traduzione è
sbagliata? Correggila»**. Chi parla ferrarese scrive la frase giusta, se vuole la
pronuncia in IPA **fra parentesi quadre** (`[al ˈkan]`: è un ascolto, non la lettura
della grafia che `dati/fonetica.jsonl` scrive fra barre), il proprio nome, la
varietà e il paese, e dà il consenso: ha almeno 18 anni e accetta che la correzione,
con il nome, stia nel repository pubblico. **I dati degli studenti non entrano**
(`AGENTS.md` §2): una correzione è di un adulto che si firma.

La pagina **non manda niente**. Prepara la riga, e la persona la consegna in uno
di tre modi: copiata in un messaggio, scaricata, o aprendo una **segnalazione su
GitHub** già compilata (modulo `.github/ISSUE_TEMPLATE/correzione.yml`, etichetta
`correzione`). I controlli della pagina sono gli stessi del repository: una riga
che il repository rifiuterebbe non si prepara.

## Il procedimento, per chi tiene il repository (persona o Claude)

```bash
export PYTHONPATH=sorgenti
python3 -m traduttore.cli correzioni importa FILE      # o - per lo standard input
python3 -m traduttore.cli correzioni                   # che cosa aspetta
python3 -m traduttore.cli correzioni allinea X0001     # parola per parola
python3 -m traduttore.cli correzioni applica X0001     # scrive i dati
python3 -m traduttore.cli correzioni inferisci         # rigenera le inferenze
python3 -m traduttore.cli impara && python3 -m traduttore.cli web
python3 -m traduttore.cli verifica                     # X1–X10, Z1–Z3
```

1. **Importare.** Le righe si incollano anche dentro un messaggio o dal testo di una
   segnalazione: tutto quello che non è una riga di correzione si salta. Una riga
   senza chi, senza varietà, senza consenso o con una pronuncia fuori dalle quadre
   viene **scartata e detta**.
2. **Guardare l'allineamento** prima di applicare. `allinea` ritraduce l'italiano e
   mette accanto, parola per parola, la proposta e la correzione, con un tipo:
   `confermata`, `forma` (la stessa parola scritta diversamente, anche solo
   nell'accento), `sostituzione` (un'altra parola), `buco` (il traduttore non la
   sapeva), `aggiunta`, `tolta`. Se l'allineamento è sbagliato — una frase
   riformulata, un ordine diverso — si applica lo stesso: la frase intera entra
   comunque, ed è quella che conta.
3. **Applicare.** `applica` scrive, con `attendibilita: "D"` e la fonte «correzione
   X0001: chi, luogo, varietà, data»:
   - la **frase intera** in `dati/coppie.jsonl`, se l'italiano ha più di una parola:
     la prossima volta il traduttore la trova come frase gemella;
   - una **voce del glossario** per ogni parola di tipo `forma` o `sostituzione`,
     con il campo `corregge` che punta alla voce sbagliata. **La voce sbagliata non
     si cancella**: è quello che la fonte scrive, ed è un fatto anche quando è
     sbagliato. La voce che corregge viene prima di lei in ogni ricerca, nel motore
     e nella pagina;
   - la **pronuncia** fra quadre in `dati/fonetica.jsonl`, riferita alla frase o
     alla voce nuova: è la prima trascrizione ascoltata del progetto, non una
     lettura.

   Le parole che il traduttore non sapeva (`buco`) restano nella frase e non
   diventano voci, a meno di `--anche-buchi`: sono quasi sempre parole funzionali
   («il» → `al`), su cui `AGENTS.md` §6 punto 8 lascia aperta la decisione, e una
   voce «il → al» da sola sbaglierebbe davanti a vocale.

   Una correzione che non si applica si **respinge** con il motivo:
   `correzioni respingi X0001 --motivo "..."`.
4. **Inferire.** `inferisci` confronta ogni forma sbagliata con quella giusta e ne
   ricava le sostituzioni con una lettera di contesto per parte («`ŋ` → `n` dopo
   `a`, prima di `d`»). Poi cerca le voci **della stessa fonte** (la stessa
   grafia: S006, il Ferri, Musacchi) dove la sostituzione si potrebbe fare. Conta
   anche le prove contrarie: le parole che un parlante ha confermato, in una
   correzione o nella verifica a campione, e a cui la regola si sarebbe applicata.
   Usa anche i giudizi della verifica a campione con `come_si_dice`, che sono
   correzioni di grafia.

   **Il glossario non cambia.** Il file dice dove guardare.
5. **Far confermare.** Le voci candidate si mostrano a un parlante — nella
   segnalazione su GitHub, in un messaggio, di persona — e quelle che conferma si
   registrano:

   ```bash
   python3 -m traduttore.cli correzioni conferma I0001 \
       --voci V10405,V10406=abandunàr --chi "Maria Rossi" --varieta cittadino \
       --dove "segnalazione #12"
   ```

   Ogni voce confermata diventa una correzione `da_applicare` **di quella voce**,
   con il nome di chi ha confermato; `V=forma` registra la forma che il parlante
   dice, se è diversa da quella proposta. Poi si applica come le altre.

## Che cosa fa Claude con le inferenze

Quando gli si chiede di lavorare sulle correzioni, Claude segue il procedimento
sopra e in più **legge le inferenze**, che è il lavoro che il programma non può
fare:

- un'inferenza con **una sola correzione** è un indizio: Claude sceglie poche
  voci candidate, diverse fra loro, e le propone a un parlante, invece di
  proporle tutte;
- un'inferenza **smentita** quanto è sostenuta riguarda probabilmente una parola,
  non la grafia: Claude lo scrive e non la propone;
- due inferenze con lo **stesso cambiamento** in contesti diversi («`ŋ` → `n`
  prima di `d`» e «prima di `t`») sono probabilmente la stessa regola più larga:
  Claude lo dice, ma la regola larga non la scrive, finché le correzioni non
  coprono quei contesti;
- una regola che **contraddice una fonte** (`dati/regole_grammaticali.json`,
  `dati/conversione_bigoni.json`) si segnala nella pull request.

Claude non applica mai un'inferenza senza una conferma: una voce cambiata perché
«la regola lo dice» è esattamente la parola inventata che `AGENTS.md` §1 vieta.

## I controlli

| Codice | Che cosa guarda |
|---|---|
| X1 | id mancante o duplicato |
| X2 | correzione senza `chi` |
| X3 | varietà fuori dalle cinque |
| X4 | senza consenso |
| X5 | senza l'italiano o senza il ferrarese |
| X6 | pronuncia fuori dalle quadre, o con simboli che non sono IPA |
| X7 | stato fuori da `da_applicare`, `applicata`, `respinta` |
| X8 | correzione applicata che non dice che cosa ha creato, o rimanda a righe che non ci sono |
| X9 | data non nella forma AAAA-MM-GG |
| X10 | correzione respinta senza motivo |
| Z1 | inferenza con `fonte` o `attendibilita D`: un'inferenza non è un dato |
| Z2 | inferenza che non dice da quali correzioni viene |
| Z3 | inferenza su una voce che non c'è |
