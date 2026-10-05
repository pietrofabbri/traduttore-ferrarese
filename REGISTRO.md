---
titolo: Registro delle modifiche
versione: 0.29
data: 2026-10-05
---

# Registro delle modifiche

Questo file esiste per una ragione sola: perché chi legge il repository fra
sei mesi sappia **perché** è com' è, e non solo **cosa** c'è.

Una versione senza una riga che dice «perché» è un numero. Il numero serve a
chi distribuisce, e va bene; ma il motivo di una decisione — perché la
varietà è un campo obbligatorio, perché quattro dati sono in attesa, perché la
trascrizione IPA non ha l'accento tonico — è la cosa che non si ricava dal
codice, e che si perde per sempre se non la si scrive qui.

## La regola

1. ogni versione che cambia il comportamento ha una riga qui, con il **motivo**
   in una frase e non in tre;
2. la versione è in tre posti e devono concordare: `pyproject.toml`,
   `sorgenti/traduttore/__init__.py`, e la frontmatter di `README.md`;
3. una modifica che cambia i dati cambia la versione **anche se non cambia una
   riga di codice**, perché cambia quello che il progetto sa.

## 0.7 — 2026-10-03 · Il vocabolario entra quasi tutto, dichiarando quello che non e' verificato

*(Immediatamente dopo: 0.8.)*

**Perché.** Chi usava il traduttore si e' accorto che mancavano le parole
piu' ovvie: «sedia» non c'era, e con essa la meta' del vocabolario di base. Il
motivo non e' stato un buco di conoscenza: il vocabolario del Ferri era gia' nel
repository dall'estrazione al 1889, con 13257 voci candidate, e di quelle ne
erano state scelte a mano **210**. Le altre rimanevano in un file di lavoro che
`.gitignore` nascondeva. Non era un dizionario troppo piccolo: era un
dizionario che non era stato letto. Il caso peggiore era la direzione della
scelta: fra le 210 voci curate c'erano 206 locuzioni e 28 parole singole — il
glossario aveva scelto quasi solo i modi di dire, e il vocabolario di base era
quasi interamente assente.

- **`filtra_candidati.py` accetta `--pulito`**: un secondo filtro butta via
  quello che l'OCR ha storpiato (i due punti, le cifre, le lettere isolate
  dell'abbreviazione rimasta attaccata). 13257 candidati diventano 11101
  leggibili, di cui 2848 locuzioni;
- **`costruisci_meccanico.py`** porta dentro i candidati rimasti senza sceglierli
  uno a uno. Ogni riga prende la pagina dal libro, la pagina si cita nel campo
  `fonte`, e la voce entra con `attendibilita: I` e `da_verificare: true`: la
  riga non si presenta come verificata, si presenta come trascritta. Il
  glossario passa da 234 a **10387 voci** (2034 locuzioni, 8353 parole
  singole). Le scelte non le fa il generatore: le fa il filtro, e quello che
  il filtro non riesce a capire non entra;
- la glossa viene ripulita della categoria e si prende l'ultimo pezzo (il Ferri
  scrive la definizione e poi la resa), i punti dentro le parole si tolgono
  («Tro.vare» → «Trovare»), e una riga che raccoglie piu' sotto-voci non entra
  invece di essere mutilata;
- **Difetto introdotto e corretto**: il primo import aveva messo dentro la
  voce «La» → «La», e da li' il motore riscriveva con la grafia della fonte
  ogni «la» di ogni frase («la porta» → «La portàr»). Le parole funzionali
  non entrano piu': sono gia' in `morfologia.py`, e una voce che non distingue
  le due lingue fa solo danno. Un test (`TestVociMeccaniche`) impedisce che
  l'import le reintroduca e che una voce meccanica perda il suo
  `da_verificare`;
- **`scarana` (sedia) e' attestata in una fonte nuova**: il *Vocabolario
  domestico ferrarese-italiano* di **Carlo Azzi (1857)**, la fonte base del
  Ferri stesso, che il Ferri dichiara di aver studiato. Va in `dati/fonti.json`
  come **S012**, stato `esaminata` con licenza verificata: attesta «Sedia,
  scaranna. Sedia. Seggiola - Seggio», ma non e' ancora `acquisita` perche' il
  suo OCR e' molto piu' sporco e i numeri di pagina radi, quindi ogni voce
  dovrebbe riportare `s. p.` finche' non si legge il libro a stampa.

**Difetto trovato e non corretto, dichiarato.** Il glossario indicizza il lato
italiano sull'intero campo `italiano`. Una voce come «Maladir → Maledire,
esacràre» non si trova quindi cercando «maledire», e sono **1663 voci su
10387** in questa situazione. Prima dell'import non si vedeva, perche' le 210
voci curate avevano resi brevi. Correggere vuol dire indicizzare anche
`principale_italiano` e i singoli pezzi — ma la stessa logica e' scritta due
volte, in `glossario.py` e in `modello.html`, e le due copie vanno tenute
allineate nello stesso commit. E' il prossimo passo, non un dettaglio.
*(Corretto nella 0.8, che e' la versione successiva.)*

**Verifiche.** 77 test (erano 74). `verifica`: 0 errori, 2 avvisi D2. Equivalenza
Python/JavaScript: 12 frasi, 0 divergenze. Sul campione di 26 traduzioni,
**0 risposte cambiate** rispetto a prima dell'import: le voci nuove aggiungono
copertura e non hanno rotto quello che gia' funzionava. La pagina e' passata
da 230 KB a 4,2 MB: e' il prezzo di 10000 voci, e la nota delle voci meccaniche
e' stata accorciata perche' da sola valeva 1,4 MB ripetuti.

## 0.29 — 2026-10-05 · Un test può essere vero e non guardare niente

**Il pendente che non era scritto da nessuna parte.** Nella cartella del progetto
c'era uno script di mutazione mai committato: rompeva di proposito sei decisioni
di `raccolta/da_modi.py` e rilanciava i test per vedere se qualcuno se ne accorgesse.
Aveva fatto il suo lavoro — aveva trovato un buco — ma viveva fuori da ogni
repository, in un file di nome `_muta7.py`, dove nessuno lo eseguiva e nessuno lo
poteva ritrovare. È il genere di cosa che il progetto vieta e che si era già fatta
altre volte: un controllo che vive fuori dal repository è un controllo che non
esiste.

**Il buco che aveva trovato, e il buco vero che c'era sotto.** La prima versione
concludeva che due regole non fossero protette da nessun test. Non era vero: erano
protette, da un'altra classe di test. Il difetto era nel banco, che girava una
sola classe e misurava meno di quello che dichiarava — cioè produceva un difetto
che sembrava un difetto del codice. Riscritto per girare **tutta** la suite, otto
mutazioni su otto: **sette prese, una sopravvissuta**.

La sopravvissuta è vera e riguarda `dati/varieta.json`. I test verificavano che
la variante ci fosse (`assertTrue`), non che fosse **quella dichiarata**: il
generatore avrebbe potuto scrivere «centrale» per tutte le righe di S019, cioè
dichiarare ferrarese di città una voce che non è di città, e nessun test se ne
sarebbe accorto. Ora il confronto è con la riga di `dati/varieta.json`, letta nel
test: la variante non si deduce e non si indovina, si dichiara.

**Perché sta nel workflow se costa quattro minuti e mezzo.** Otto suite complete
da 33 secondi l'una, misurate. Il prezzo è giustificato dal fatto che questo è il
controllo che invecchia per primo: se non gira, nessuno vede che ha smesso di
guardare. Due avvertenze sono dentro il codice e non qui, perché è il codice che
le deve far rispettare: non parte con un file tracciato già modificato, e non
parte se `git` non risponde — riscrive un file tracciato, e una guardia che quando
non sa risponde «va tutto bene» non è una guardia.

**Il secondo difetto, della stessa specie, trovato mentre il primo si
chiudeva.** Aggiungere il banco al workflow ha fatto guardare `prove/ci_locale.py`,
che dice di eseguire in locale i passi del workflow. Il suo lettore riconosceva
**solo** i blocchi `run: |`: i passi scritti su una riga sola — cioè «I test», il
passo più importante — non giravano mai in locale, e il totale stampato era più
basso della realtà senza che nessuno lo vedesse. Peggio: un blocco aperto negli
ultimi byte di un file non veniva mai chiuso, perché la fine del file non è una
riga che ne chiude un'altra, quindi anche l'ultimo passo di ogni workflow era perso.
Due difetti, una causa sola — un controllo che dichiarava una copertura maggiore
di quella che aveva — e il secondo era più anteno del primo di qualche mese.

Ora un passo è un passo, qualunque sia la sua forma, e due test tengono il conto:
confrontano i passi che il lettore trova con le righe `run:` del file. Il primo
dei due è già ripagato: mentre si scriveva, ha preso il terzo difetto — il
lettore vecchio, nell'istante in cui il test nuovo è entrato in funzione — e
l'ultimo passo era proprio quello che mancava.

**Verifiche.** 317 test (erano 314): uno sulla variante dichiarata, due sul
lettore dei passi del workflow. Il banco: 8 mutazioni, 8 prese. `ci_locale`: 19
passi, tutti con zero (erano 16, e tre di quelli non giravano).

## 0.28 — 2026-10-05 · I proverbi erano sulla pagina e non nel traduttore

**Il buco che avevo dichiarato in fondo al messaggio precedente.** Avevo
scritto, giustamente: «i proverbi non arrivano al traduttore». Adesso è chiuso, e
la causa era più semplice di quanto sembrasse: `Corpus.indizza()` guardava solo
`self.coppie`. I **33 proverbi** del progetto — 28 del Ferri e 5 dei «Proverbi
d'Autun» — erano indicizzati in nessun modo, quindi la ricerca per frase intera
non li vedeva. Non era una scelta: era una dimenticanza, e il suo costo è che
**la frase più stabile di una lingua era l'unica che il traduttore non sapeva
restituire per intero**.

Ora tornano interi nelle due direzioni:

```
Se nevica sulla foglia, d'inverno non se n'ha voglia.
  → Se a neva in sla foia, d'inveran an s' na voia.      corpo, 0.80
Se a neva in sla foia, d'inveran an s' na voia.
  → Se nevica sulla foglia, d'inverno non se n'ha voglia.  corpo, 0.80
```

**Chi vince quando due righe hanno la stessa chiave.** Vince la coppia, e la
ragione è dichiarata dentro il codice: la coppia parallela è la prova diretta
della frase, il proverbio è un modo di dire che la fonte ha isolato. Quindi in
Python si indicizza prima la coppia e il proverbio entra con `setdefault`, e
nella pagina con `if (!lista[k])` — la stessa regola scritta in due linguaggi.
Un proverbio senza fonte o con un lato solo non entra: la regola delle coppie,
senza eccezioni.

**Il difetto che è venuto fuori mentre lo facevo, e che era più grosso.** La
regola della confidenza nel ramo della frase intera è questa: `corpo_frase` solo
se la fonte c'è ed è dichiarata documentata. La **pagina non la aveva**: dava
`corpo_frase` sempre. Quindi per ogni riga non documentata — cioè per quasi
tutto — il terminale diceva 0,80 e la pagina 0,92, sulla stessa riga.

**E il confronto fra le due copie non lo vedeva, per due motivi insieme.** Il
confronto confrontava `testo`, `tradotto` e `origine`: **la confidenza non
entrava**, quindi verificava *che cosa* dicevano e non *quanto* lo dicevano con
sicurezza. E il ramo della frase intera era **riscritto a mano** dentro il
conferimento: `g.fe`, `g.it`, `origine: "corpo"`, senza passare da
`risolvi`. Era una ricostruzione del codice della pagina, non il codice. Sono
due copie dello stesso difetto: **la lezione del progetto sulla normalizzazione,
ripetuta sul confronto invece che sul confronto della normalizzazione**.

Ora il confronto passa da `risolvi`, prende la confidenza dalle due parti, e le
frasi confrontate sono 15: aggiunti i due proverbi in entrambe le direzioni e la
frase del parlante nativo.

**La prova che il confronto prende il difetto.** Ho rotto di proposito la
regola nella pagina e rilanciato il confronto: **3 divergenze**, non una sola —
i due proverbi e `pesce d'aprile`, una coppia del Ferri che era già affetta
dallo stesso difetto. Il confronto passava verde prima su tutte e tre.

**Verifiche.** 314 test (erano 305): nove sui proverbi e sul confronto. Il
confronto fra le due copie: 15 frasi, 0 divergenze. `verifica`: 0 errori, 8
avvisi noti.

## 0.27 — 2026-10-05 · La prima fonte che scrive le due lingue

**Che cosa si cercava.** Un testo con l'italiano e il ferrarese **affiancati**,
riga per riga. È la cosa che il progetto non aveva mai avuto: ogni fonte porta
una delle due facce — il Ferri il ferrarese, i dizionari moderni l'italiano — e
le altre due le abbiamo ricostruite a mano, che è il lavoro più costoso e più
inaffidabile di tutti. Con una fonte bilingue l'inferenza non serve: la
traduzione c'è, scritta dalla fonte stessa.

**Quello che è venuto fuori è la prima.** I **Proverbi d'Autun**, raccolta di
proverbi ferraresi di tradizione manoscritta, in una trascrizione che mette
ogni proverbio nelle due lingue con le note numerate. Cinque proverbi, da
`SETEMBAR` a `NUVEMBAR`, entrati in `dati/proverbi.jsonl` come **P0029–P0033**.

**Tre cose che la dichiarazione di S023 dice, e che il progetto deve sapere.**

1. **La varietà non è dichiarata e le righe non la dichiarano.** Autun è nella
   pianura ferrarese; il glossario chiama `cittadino` il ferrarese di Ferrara
   città. Nessuna fonte del repository dice di che varietà sia la raccolta, e
   scrivere `cittadino` perché è l'unica che conosciamo sarebbe una variante
   attribuita a un posto solo. Un test lo impedisce.
2. **`attendibilita: "I"`, non `D`.** `D` significa che l'ha letto chi l'ha
   scritto: qui l'ha riscritto un anonimo su un blog, e nessuno in questo
   repository ha confrontato la trascrizione con l'originale.
3. **La licenza non è verificata** e la fonte resta `esaminata`: una pagina di
   blog non dichiara nulla, quindi questi dati non generano voci e non entrano
   nel glossario finché la licenza non si chiarisce.

Il testo della pagina è in `raccolta/grezzi/autun_proverbi.txt`, gitignorato
come tutti i grezzi: si rilegge con un comando, quindi la dichiarazione basta. Un
test controlla che ogni riga si ritrovi **parola per parola** nel testo
dichiarato — è il controllo che rende impossibile cambiare una riga senza che
la fonte resti indietro.

**Un difetto nei miei stessi test, preso mentre li scrivevo.** Cercavo i proverbi
con `Corpus.da_file(coppie)` e non li trovavo: i proverbi stanno in un file
loro, e il test li cercava nel posto sbagliato restituendo «zero» senza dire
perché. Il caso peggiore di un test, perché sembra una misura. Ora il file dei
proverbi è nel `setUp`, con il perché scritto accanto.

**Un difetto che stavo per consegnare, e che il confronto con una copia
fresca ha fatto vedere.** Il test che confronta ogni riga con il testo della
pagina legge `raccolta/grezzi/autun_proverbi.txt`, e quel file è **gitignorato**
come tutti i grezzi: in locale passava, su GitHub Actions sarebbe fallito,
perché lì quel file non c'è. È il modo peggiore in cui un test possa mentire —
verde dove si guarda, rosso dove conta. Ora il test **salta** e dice perché,
e un altro controlla che il grezzo **continui a essere ignorato**: se un
giorno smette, va tracciato e la dichiarazione di S023 cambia, e lo dice un
controllo invece di una persona fra vent'anni.

**Verifiche.** 305 test (erano 298): sette sulla fonte bilingue. `verifica`: 0
errori, 8 avvisi noti. I proverbi sono 33, cinque dei quali nuovi.

## 0.26 — 2026-10-05 · Una voce di parlante entra nel progetto, e i token smettono di stare nel codice

**Una frase che un parlante ha scritto, e cosa ci mette dietro.** Scrivendo
«lei si siede» il motore rispondeva `si → oj`, perché `si` è una particella e i
109 verbi pronominali del glossario sono **tutti infiniti** (`saŋtàrs`,
`Acanirss`): non c'è nessuna terza persona da restituire. Un buco dichiarato è
la risposta onesta, ma è anche una risposta che il progetto non deve dare se
una persona ha la frase. Pietro Fabbri l'ha: **«Li è l'as senta»**.

Ora è in `dati/coppie.jsonl` come **F0050**, e il motore la rende per intero
dalla frase intera del corpus, con la sua fonte e confidenza 0,92. La particella
`si` è attaccata al verbo (`s'as senta`), come il Ferri scrive l'infinito.

**La fonte nuova, S022, e che cosa dice di sé.** È la prima volta che una voce
**parlante** entra nel progetto. Dice il ferrarese di **Ferrara città**
(`varieta: "cittadino"`, non un'assunzione: senza varietà una coppia non entra
nel motore, controllo C7). Oggi contiene **una frase**, e la sua dichiarazione
dice tre cose che il progetto non deve dimenticare: che non è un vocabolario né
una grammatica, che **S009** («Corpus di parlato spontaneo ferrarese») resta
`esclusa` e continua a dire la verità — quel corpus non esiste e va costruito
registrando persone — e che il consenso è del responsabile del progetto, con il
documento scritto fuori dal repository, come per il permesso di S015.

`raccolta/parlante.py` non genera niente e apposta lo dice: qui la fonte **è**
una persona che scrive una frase, e la frase **è già il dato**. Un generatore
che la copiasse da un altro file aprirebbe una porta per cui la riga potrebbe
cambiare senza che la dichiarazione restasse indietro. Il modulo legge e
controlla tre cose che nessun controllo generale chiede: `attendibilita: "D"`,
la varietà, e **chi** ha parlato.

**I token non stanno più nel codice.** Le particelle erano in due liste scritte
a mano — le candidate in `raccolta/da_pronominali.py`, il nome della costruzione
in `pronominali.py` — e la pagina ne aveva una terza copia. Ora c'è
`dati/tokeni.jsonl`: ogni particella porta il suo ruolo, a che cosa si attacca,
**la fonte che la documenta** e **la ragione per cui è dichiarata oppure no**,
compreso perché `ci` non lo è (`ghe` è una voce del glossario, V0014) e perché
`vi` e `ne` non hanno nessuna voce che le porti attaccate a un verbo. Il codice
non sa niente: legge. La pagina prende le costruzioni dagli stessi dati, quindi
quando una particella smette di essere dichiarata la pagina smette di chiamarla
«verbo pronominale» senza che nessuno tocchi il codice.

Il controllo **F18** chiede la prova in entrambe le direzioni: una particella
dichiarata senza voci è una regola senza prova, e **una particella con voci e
non dichiarata** è un buco che il progetto si nasconde.

**Un test che non gira su una macchina senza node.** «Il codice non scrive più
una lista di particelle» è un controllo sul sorgente, e i commenti vengono
togliati prima di guardare: spiegano il difetto e quindi contengono per forza
la sequenza che il difetto è.

**Verifiche.** 298 test (erano 280): dodici sui token e sul controllo F18, sei
sulla fonte del parlante. `verifica`: 0 errori, 8 avvisi noti. Sul motore:
`lei si siede` → `Li è l'as senta` (corpus, 0,92), `si siede` → buco dichiarato.

**Il limite, dichiarato.** Nella direzione opposta la stessa frase torna male:
`Li è l'as senta` → `Lì Trinca l'as senta`, perché il corpus somiglia parola per
parola e non distingue `li` (lì) da `lei`, né l'innalzativo `è` dal tema `e`.
È il difetto noto della ricerca per somiglianza e non è stato corretto qui: si
chiama `stua_zione` e va corretto sul corpus, non nel motore.

## 0.25 — 2026-10-05 · La particella non è una parola, e il motore la trattava come una

**La risposta sbagliata, e perché è la peggiore.** Scrivendo «lei si siede» il
motore rispondeva `lei`, poi `si → oj`, poi `siede` intatta. Il `oj` è la
risposta peggiore delle tre, perché non è un buco: è una **parola vera del
glossario** (V0026, dall'itinerario di Wikipedia) data nella traduzione di una
particella pronominale. Il progetto ha la regola «meglio nessuna riga che una
riga falsa», e il motore la stava violando senza accorgersene — non sapeva
che `si` fosse una particella, quindi per lui era una parola come tutte le
altre.

**La prova non è una grammatica, è il glossario.** Il Ferri scrive i verbi
pronominali con il clitico **dentro** la voce: `Accanirsi → Acanirss`,
`Affacciarsi → Afazzars`, `sedersi → saŋtàrs` (V14857). Sono **109 voci**, tutte
con `si`, tutte con la particella in `-rs` o `-rss`. Nessuna fonte dichiara una
regola grammaticale su questo e non serve: il dato c'è, è numerabile e porta
l'id della voce che lo scrive. È in `dati/pronominali.jsonl`, con la testata
che dichiara il sistema.

**Che cosa fa il motore adesso.** Riconosce la particella, **non la traduce** e
la attacca al verbo che segue: «si siede» è un'accorpamento, non due parole. La
risposta è un **buco dichiarato** che nomina la costruzione, i 109 verbi che il
glossario contiene e il fatto che il progetto non coniuga — più la cosa che il
modulo non sa, cioè che non distingue un verbo da un nome. Un buco che promette
una forma e non la dà è peggio di un buco che non promette niente.

**Un difetto mio, preso dal confronto con la pagina.** Il riconoscimento
guardava la `chiave()`, che toglie gli accenti, quindi `chiave("sì")` e
`chiave("si")` erano la stessa stringa: la particella dell'**affermazione**
— che il glossario conta come voce separata, V8171 — sarebbe stata trattata
come particella di un verbo pronominale, e «Sì va» sarebbe diventato un buco.
Ora il confronto è sulla **forma scritta**, in Python (`normalizza.normale`) e
nella pagina (un `normale()` nuovo, confrontato test per test con la copia
Python). La pagina aveva anche la sua copia del ciclo di traduzione, che
risolveva **parole** e avrebbe stampato sotto «si» la risposta di «siede».

**Un secondo difetto mio, più grave: una regola inventata.** La prima versione
dichiarava `si`, `ci`, `vi` e `ne` come particelle. Ma `ci`, `vi` e `ne` non
hanno **nessuna** voce che le porti attaccata a un verbo, e `ci` è già una parola
del glossario (`ghe`, V0014): dichiararle come particelle toglieva al motore
una risposta vera per dargli un buco inventato. Ora il file dichiara solo le
particelle **attestate**, e il generatore stampa ogni giro quante sono e quante
candidate ha scartato e perché. Il controllo **F17** rifiuta un file che
dichiara una particella senza una riga che la porti, e una riga che usi una
particella non dichiarata.

**Un confronto che F17 non fa, e perché.** La fonte non è confrontata con
`dati/fonti.json`: il glossario scrive la citazione intera («Luigi Ferri,
Vocabolario ferrarese-italiano, 1889, pag. 8») e non l'id della fonte (`S002`),
e il progetto non ha un modo dichiarato di passare dall'una all'altro. Scrivere
quella corrispondenza dentro un controllo sarebbe una regola nuova. F17
confronta invece la fonte della riga con quella della voce che la riga indica:
la riga non può raccontare una provenienza che il libro non conferma.

**Verifiche.** 280 test (erano 257): dodici sulle particelle, sei sul controllo,
quattro sulla pagina e sulle due copie. `verifica`: 0 errori, 8 avvisi noti.
Nella pagina costruita: `si siede` torna come una sola unità con il buco
dichiarato, `Sì va` cerca `sì` nel glossario, `ci vado` risponde `ghe vado`.
Il glossario non è cambiato di una voce: qui non si raccolgono parole, si
dichiara che la particella non è una parola.

## 0.24 — 2026-10-05 · S021 aperta davvero: il sito c'è, il lessico no

**Il pendente che avevo lasciato tre volte.** «Rendere il sito «Al Tréb dal
Tridèl» leggibile a macchina»: era l'unico modo per chiudere S021. L'ho
chiuso, e il modo è stato il più semplice — l'ho aperto nel browser — con
l'esito che nessuna delle tre dichiarazioni precedenti aveva previsto.

**Il sito non è un muro.** È un SuperSite Aruba, non un WordPress: `/wp-json/`
non esiste, non c'è nessun endpoint JSON dietro le pagine, e i dati arrivano
da una post ad Aruba. Il `curl` della home restituisce 11031 byte e nessun
testo. Ma nel browser le pagine si leggono: il mio «si rendono con
JavaScript» era vero e non era l'ostacolo.

**Il lessico non è pubblicato.** `/vocabolari` è una pagina di presentazione:
dice «alcune pubblicazioni sono state ideate e create da membri della nostra
associazione» e **non ne elenca nessuna** — i suoi 33 link sono tutti menu. E
`/gocce-di-dialetto` è un elenco di articoli di blog ed è **vuoto**. Quindi la
mia dichiarazione, che con una sicurezza che non aveva diceva «il contenuto
lessicale sta in `/vocabolari`, `/gocce-di-dialetto`, `/dialetto-in-pillole` e
`/filastrocche`», era un **sospetto travestito da fatto**.

**Una dichiarazione sbagliata è peggio di nessuna dichiarazione**, perché fa
perdere a chi legge il posto dove guardare: chi l'avrebbe seguita sarebbe
andato a quelle pagerie, avrebbe visto che sono vuote e avrebbe concluso che
il progetto aveva raccolto male le fonti. Il sito era guardato male: da lontano.

**Cosa resta dichiarato, e come.** In `dati/fonti.json` S021 ha adesso un
blocco `verifica_2026_10_05` con il metodo, le due pagine controllate, l'esito e
la conclusione; il testo di quello che ho letto è in
`raccolta/grezzi/s021/pagine_verificate.txt`, così chi verifica fra un anno
verifica le stesse parole e non le mie. Il sito chiede `Crawl-delay: 30` e i
percorsi visitati sono quelli del sitemap. Lo stato resta `esaminata`: entrare
nel glossario richiede i documenti, e quelli li si chiede all'associazione.

**Un test che rende la cosa difficile da sbagliare di nuovo.** Quando una fonte
porta un blocco di verifica, quel blocco deve nominare le **pagine** guardate,
dire il **metodo**, e riportare un **esito** che non sia una frase di circostanza.
E per S021 in particolare il test controlla che la dichiarazione continui a dire
che il **lessico non è pubblicato** — non che le pagine non si vedono: è la
seconda che una dichiarazione sbagliata confonde con la prima.

**Un difetto nella mia stessa dichiarazione, preso da un test.** Mandavo a
`raccolta/grezzi/s021/pagine_verificate.txt`, e `raccolta/grezzi/` è
gitignorata — che è la regola del progetto, e va bene per i grezzi che si
rileggono dal sito. Ma quello di S021 **non** si rilegge con un comando: le
pagine si rendono con JavaScript e servono un browser. Quindi quel file sta sul
disco di chi ha verificato e non è nel repository, e chi leggeva la
dichiarazione su una copia fresca non lo trovava e non sapeva se mancasse il
file o il lavoro. Ora la dichiarazione lo dice (`grezzo_tracciato: false`, con
la ragione), e un test controlla due cose: che ogni verifica che dichiara un
grezzo dica anche se è tracciato, e che quel file contino a essere ignorato —
perché se un giorno smettere di esserlo va tracciato, e la dichiarazione
deve dirlo. Le quattro righe che contano restano nella dichiarazione, che è
tracciata.

**Verifiche.** 257 test (erano 254): tre sulle fonti verificate. `verifica`: 0
errori, 8 avvisi noti. Il glossario non è cambiato di una voce, ed è la misura
giusta: la fonte non aveva voci da prendere.

## 0.23 — 2026-10-05 · Il traduttore non coniugava e non lo diceva

**Il buco vero, e perché non era un codice mancante.** «Non sa coniugare molti
verbi» è un sintomo; la causa è che **nel repository non c'è il paradigma**.
Ho cercato in tutte le fonti che il progetto ha: Biondelli, Nannini, Azzi,
Gaia, il Ferri. Nessuna tabella la coniugazione ferrarese. Quello che c'è è
sparse in due fonti, e sono poche forme vere: la sezione 4 di Bigoni (S015),
che è già dentro `dati/regole_grammaticali.json`, e le tavole di confronto sul
ferrarese di Biondelli (S001), che sono in `raccolta/grezzi/biondelli_1853.txt`.

Un coniugatore che ricava le desinenze dall'italiano produrrebbe forme
ferraresi che nessuno ha mai scritto. Il progetto non mette in `dati/` niente
che non sia in una fonte, quindi **non si ricava niente**.

**Che cosa è cambiato, allora.** Tre cose, e la prima è la più importante.

1. **Il buco si dichiara.** `dati/verbi.jsonl` è un indice delle forme che le
   fonti attestano per iscritto, con la fonte e il punto in cui la fonte le
   scrive: **18 forme su 13 verbi**. Sotto, la lista delle caselle che
   **nessuna** fonte scrive — 2sing, 2plur e 3plur del presente e del passato,
   il futuro, il condizionale — e nessun codice le riempe. Una parola
   coniugata che il motore non sa tradurre ora torna con la spiegazione: quante
   forme ci sono, su quanti verbi, e quali caselle mancano. Prima tornava come
   trattino, e un trattino non distingue «non so» da «non c'è».
2. **Dove le fonti scrivono una forma, il motore la usa.** `voglio` → `vój`
   (S015, §4), con confidenza 0,75: meno di una voce di dizionario, perché
   copre una persona sola, e più di una regola imparata, perché qualcuno l'ha
   scritta. Il comando `python3 -m traduttore.cli verbi` stampa la tabella e i
   buchi; con `--lemma`, `--persona` e `--tempo` chiede una casella sola e la
   risposta è sempre una delle due: la forma, o il buco che dice perché quella
   non la scrive nessuna.
3. **Il controllo **F16** verifica ogni riga**: la fonte è fra quelle
   dichiarate in `dati/fonti.json`, la riga dice **dove** la fonte scrive la
   forma, la persona e il tempo sono fra quelli dichiarati, e una persona
   vuota è ammessa solo con i due tempi che non ne hanno — il gerundio e il
   participio. Una forma senza pagina non è un dato che si possa controllare.

**Il clitico fa parte della chiave, e non è una pignoleria.** S015 (R036)
dichiara che `avér` si raddoppia con una «ɣ» quando è dimostrativo: «mi aj ò»
e «mi a ɣ o» sono la stessa persona e lo stesso tempo con due forme diverse.
Una chiave senza clitico restituirebbe «ò» per entrambe.

**Verificato sulla pagina, non solo sul terminale.** Scrivendo `andammo` la
pagina risponde `i andò` — la forma di Biondelli — con la sua etichetta e la
sua fonte; scrivendo `dormimmo` resta com'è e l'avviso spiega perché. Il primo
è l'unico modo per vedere che il buco dichiarato non è una scusa: la casella
che le fonti scrivono si usa, e quella che non scrivono si nomina.

**Un disaccordo fra due fonti, dichiarato e non risolto.** Il noi plurale:
S015 lo scrive in «-ŋ» — «nu a kaŋtéŋ» — e S001 con una proclitica «i» —
«i andò». Le due forme sono nel file e il disaccordo è scritto nella nota
delle due righe di S001. Scegliere è una decisione che spetta a un parlante.

**Una verifica ha preso me, e la prova che serve.** Avevo scritto a mano la
frase di Bigoni come `a sąm aŋdà`. La fonte scrive `a són aŋdà`: avevo letto
`ón` come `ąm` nel terminale e copiato l'errore. Il generatore se n'è accorto
da solo, perché confronta ogni frase con la fonte invece di fidarsi di quello
che ho scritto — e per questo `raccolta/da_verbi.py` **cita** la frase invece
di cercarla con una regex: una regex aggiunge forme che la fonte non scrive e
perde forme che scrive.

**Un difetto che i controlli non avrebbero preso, e che ho preso io.** Il primo
test sull'accorpamento usava «voglio» come parola di guardia, e quando il
motore ha iniziato a tradurla il test è fallito. Non era un test rotto: era un
test che, senza saperlo, provava due cose. La parola di guardia è diventata
«vorrei», e il motivo è scritto nel test.

**Anche la pagina aveva il buco, e per un motivo che è già del progetto.**
Il motore è in Python e la pagina ha una copia sua dello stesso motore in
JavaScript: due copie che non possono divergere. Avevano divaricato — il
terminale rispondeva con le forme attestate e la pagina no, quindi il buco
dichiarato arrivava a metà degli utenti e non agli altri, e la pagina che lo
studente usa era quella senza. Ora la pagina ha il livello delle forme
attestate, l'etichetta che le distingue («da una forma verbale attestata»), i
dati che arrivano dal generatore — mandati **come sta scritta** la parola
italiana, non già normalizzata, perché la normalizzazione la fa la pagina con
la sua copia e se le due divergono la ricerca fallirebbe in silenzio — e
l'avviso con i numeri. Il test è in `node`, sul codice che il browser esegue,
come il bottone del suono.

**Verifiche.** 254 test (erano 237): tredici sulle forme verbali e quattro
sulla pagina.
`verifica`: 0 errori, 8 avvisi noti, e F16 non segnala nulla sulle 18 forme.
Il generatore, rieseguito, scrive **0** righe: sono già tutte dentro.

**Il limite, dichiarato e non aggirabile.** Con questi dati il progetto sa 18
forme verbali. Le altre caselle del paradigma restano scritte come buchi, e a
riempirle serve una fonte che le scriva: una grammatica del ferrarese con le
tabelle, o un vocabolario che per ogni verbo dia le forme. Nessun programma
può produrre quella fonte, e il progetto non la inventa.

## 0.22 — 2026-10-05 · Trentuno modi di dire entrano nelle coppie, e il lettore che li leggeva sbagliava

**La fonte era gia' dichiarata, il lavoro no.** S019 — Wikiquote «Modi di dire
ferraresi», CC BY-SA 4.0 dichiarata dalla pagina stessa — era in
`dati/fonti.json` dalla voce 0.21 e non aveva prodotto niente. Il motivo e'
che sono **frasi**, e il glossario del progetto e' fatto di voci che il gioco
fa ripetere: ripetere «buttare le carte in tavola» non e' un esercizio di
pronuncia, e' un esercizio di memoria. Quindi vanno in `dati/coppie.jsonl`, che
e' il corpus delle frasi, ed e' la prima volta che una fonte interamente nuova
viene esercitata su quel file invece che su quello delle parole. Adesso
`dati/coppie.jsonl` ha **47 righe** (erano 16) e `frasi.html` passa da 88 a
**111 KB**.

**Il tipo e' `narrativa`, non `attestato`, e la scelta e' dichiarata perche'
conta.** `attestato` vuol dire «voce di dizionario con frase d'esempio»; un modo
di dire e' un proverbio sciolto, e il corpus mette quelli sotto `narrativa`. Il
tipo non e' cosmetico: decide a chi la frase viene offerta.

**Un lettore che contava i tag invece che la struttura.** La pagina mette la
spiegazione italiana dentro un `<dl>` dentro il `<dd>` della voce, quindi
contando i `<dd>` si contano anche le spiegazioni: 37 elementi per **35 voci**.
La prima versione del lettore contava i tag e diceva 37. Ora conta la
**profondita'** e prende solo i `<dd>` che non sono dentro un altro `<dd>`, e il
numero esce dalla struttura del documento e non da una regex che arriva a una
conclusione fortunata.

**La regola che scartava le voci giuste.** Quattro delle 35 non entrano: due non
hanno spiegazione (la pagina rimanda e basta) e due hanno la spiegazione tagliata
— «, andare a zonzo», «o Dai, picchia e martella» — cioe' la coda di una frase.
La prima regola che ho scritto riconosceva quelle per la **prima parola**, e
buttava via anche «Come viene viene, alla grossa, a occhio e croce» e «Furbo come
l'oca di Fergnani», che sono frasi intere: quattro scarti per due salvataggi. La
regola adesso guarda il **segno** iniziale — un punto che non e' una lettera, o
una congiunzione stretta e minuscola incollata a una maiuscola seguita da
virgola — che e' la prova vera. Il numero degli scarti viene stampato ogni
volta, perche' chi decide debba poterli vedere: sono **2 senza spiegazione** e
**2 mozzate**, e quindi **31** righe scritte, da F0019 a F0049.

**Tutto `attendibilita: "I"`.** Una pagina collaborativa non e' una fonte
documentata: nessuno ha ascoltato un ferrarese che dica queste frasi. Sono
interpretazioni, e il progetto le chiama cosi'. La varieta' e' `cittadino`
dichiarata in `dati/varieta.json` con la sua riga e il suo motivo, perche' la
pagina non dice dove i modi di dire sono stati raccolti: l'assunzione e' nostra e
resta dichiarata come memoria.

**Tre difetti presi dai controlli mentre si scriveva, non da me.**

- Il generatore **non reggeva un file di coppie che non esiste**: il primo giro
  su un corpus vuoto finiva in `FileNotFoundError`. Non e' un difetto del
  generatore, e' un crash.
- La decisione era dentro `main()`, quindi l'unica cosa verificabile era il file
  finale, gia' scritto e non riscritto piu': tenere una spiegazione mozzata o
  scrivere una riga senza nota non si vedeva. Ora la decisione e' in
  `classifica()`, che non scrive niente e restituisce i quattro mucchi — quello
  che entra, quello che c'e' gia', quello che la pagina non spiega, quello che
  la pagina spiega a meta' — ed e' provata da quattro test che **eseguono il
  generatore** in un file di temporaneo e guardano quello che esce.
- Un test che avevo scritto contava un `<dd>` esterno e uno annidato: un lettore
  che sbaglia in quel modo lo passava lo stesso. La casella e' cambiata in una
  che **non puo' passare**: una voce con tre spiegazioni dentro deve contare
  una, e chi conta i tag ne trova tre.

**I test prendono i difetti, misurato.** Ho mutato il codice di proposito — la
regola torna a guardare la prima parola, il lettore conta tutti i `<dd>`, il tipo
torna a `attestato`, la nota sparisce, gli id ricominciano da `F0001`, una voce
gia' scritta viene riscritta — e ho guardato quali test falliscono: **sette
mutazioni su sette prese**, ciascuna da un test che nomina la voce o il numero
colpito, non da un test che dice «il conteggio non torna».

**Una nota sull'interprete, che ha mangiato un'ora e va scritta.** Con
l'interprete di questa macchina (Python 3.9 dei CommandLineTools) la forma
`x = modulo._esterni(s)` seguita da `len(x)`, dentro un metodo di una classe di
test, mette `x` sia fra le variabili locali del codice compilato sia fra i nomi
globali: a runtime `len(x)` solleva `NameError`. La stessa riga compilata da sola
da' `LOAD_FAST`, quindi non e' un errore di scrittura. Il metodo chiama la
funzione due volte invece di tenere il risultato, e la nota e' nel docstring
della classe. Il sintomo che faceva perdere tempo e' un altro: il traceback
mostrava il sorgente **nuovo** mentre eseguiva il bytecode **vecchio**, perche'
la cache accettava un file la cui dimensione non era cambiata. Da allora, prima
di ogni verifica, le cache si cancellano.

**Verifiche.** 237 test (erano 226): undici nuovi, sei sul lettore e cinque sulla
scrittura. `verifica`: 0 errori, 8 avvisi. Scanner: 0 righe sospette. Il
generatore, rieseguito, trova **0** righe da scrivere: le 31 sono gia' nel file.

## 0.21 — 2026-10-05 · Il ciclo parte dall'italiano, e la prima fonte che va nella direzione giusta

**Il problema non era la ricerca, era l'ordine.** Il glossario si riempiva
nell'ordine in cui le fonti si incontravano: 16739 voci piene di `scaranna`,
`majàl`, `biondelli`, e con un buco sulle parole che uno studente usa tutti i
giorni. Il metro di `raccolta/copertura.py` lo misurava — 38,4% dei 10744
lemmi italiani sopra la soglia — ma nessuno ci aveva costruito **sopra** un
giro di lavoro. Adesso c'e': `raccolta/cerca_nelle_fonti.py` parte dalle parole
italiane piu' frequenti e chiede, per ognuna, in quali fonti si trova. Il primo
giro dice che **1297 delle 6598 parole non coperte aprono una voce in una
fonte**, e che **una** di queste e' prendibile subito da S020.

**Il primo conto che questo ciclo ha dato era sbagliato, e come.** La prima
versione cercava la parola in **tutto** il testo di ogni fonte e non nella
testa della voce: e allora `modo` risultava «trovata in sei fonti», perche' la
parola `modo` compare in quei libri dentro una definizione, dentro una glossa,
dentro un'altra voce. Una parola che compare in un vocabolario non vuol dire che
quel vocabolario la traduce: vuol dire che la nomina. Il conto era gonfiato di
piu' del doppio — 2759 invece di 1297, e 197 «prendibili subito» invece di una —
e la ragione e' che questo numero e' la cosa che il progetto non puo' dare
sbagliata. Ora ogni fonte ha un **lettore dichiarato**, e il lettore dice dove
sta la testa di una voce: per S020 e' la parola italiana, per S006 la ferrarese,
e per i cinque libri dell'Ottocento — che sono testo continuo e non hanno una
riga per voce — la prima parola della riga, che e' un'approssimazione dichiarata
e non esatta. Un lettore che non sa dove sia la testa **fallisce**: e' meglio di
uno che indovina.

**Cosa significa davvero «1297 trovate».** Sono parole che il metro conta come
non coperte e che aprono una voce in una fonte. Il metro e' severo per scelta —
confronta il lemma dall'italiano e non per traduzione inversa — e le fonti
ferrarese-italiano hanno la parola **dall'altra parte**: in Biondelli `fatto` e'
la voce ferrarese, e l'italiano ne e' la definizione. Coprire `fatto` da li'
richiede un'inversione che nessuno script fa e che va fatta a occhio. E' il
lavoro vero del giro dopo, e adesso si sa quant'e'.

**La fonte che cambia la direzione: S020, Musacchi.** Tutte le fonti precedenti
sono state costruite **dal ferrarese verso l'italiano**: si leggeva una parola
dialettale e si scriveva cosa significasse. Il motore fa il contrario, e una
fonte nella direzione sbagliata non puo' coprire una parola che in ferrarese non
ha un lemma. Musacchi scrive dall'italiano al ferrarese, e copre 631 parole che
il glossario non aveva.

**Il numero e' cresciuto di venti punti base, e va detto perche' e' cosi'
piccolo.** Le 631 voci nuove hanno fatto salire la copertura dal 38,4% al **38,6%**:
le altre **582 erano gia' c'**. Il valore di questa fonte non e' il numero di
parole nuove, e' che **582 parole hanno adesso una seconda fonte indipendente**:
il Ferri del 1889 e il vocabolario di oggi dicono la stessa cosa, e una parola
con due attestazioni non e' piu' una parola che qualcuno ha scritto una volta.

**Le tre fonti nuove e la licenza di ognuna, che sono tre storie diverse.**

- **S019, Wikiquote «Modi di dire ferraresi»** — CC BY-SA 4.0 dichiarata dalla
  pagina stessa. 37 modi di dire. Non sono parole singole: sono frasi, quindi
  nel corpus delle coppie e non nel glossario, perche' il gioco fa ripetere
  parole e una frase intera non e' una parola.
- **S020, Musacchi** — l'autore scrive nell'introduzione: «Questo mezzo
  consentirà a chi vorrà utilizzare questo mio lavoro, di aggiungere, correggere
  porvi miglioramenti a piacere, senza problemi». Il file che il progetto ha e'
  arrivato da un sito di download, non da una pagina dell'autore, e
  l'autorizzazione l'ha data il titolare del progetto. Quindi `fonti.json` dice
  `licenza_verificata: true` **per dichiarazione del titolare**, non per lettura
  di una pagina pubblica: chi legge fra vent'anni ha bisogno di sapere quale
  delle due e'. Il permesso e' scritto testualmente **nella fonte di ogni
  riga**, cosi' una riga copiata in un altro contesto porta con se' la ragione
  per cui puo' essere copiata.
- **S021, «Al Tréb dal Tridèl»** — il sito non dichiara licenza, come S011. Ma
  il titolare del progetto fa parte dell'associazione e autorizza, quindi la
  fonte passa a `esaminata` con la ragione scritta. Le sue 51 pagine sono quasi
  tutte eventi e archivi; il lessico sta in `/vocabolari`, `/gocce-di-dialetto`,
  `/dialetto-in-pillole` e `/filastrocche`, e le pagine si rendono con
  JavaScript, quindi un `curl` non le vede. Il sito chiede `Crawl-delay: 30`, e
  per quello va consultato a mano e non a raffica.

**Quello che `da_musacchi.py` non fa, e dichiara di non fare.** Non sceglie
quando la fonte da due forme (`Usta. Soramanagh.` le mette entrambe nella stessa
voce), non distingue la parola dalla sua definizione (`Battuto, Impasto interno
dei cappelletti` produce una voce che si cerca con «battuto» e una nota che
porta la definizione), e **non tocca le 286 righe che non si dividono in due**:
sono quasi tutte l'introduzione e le intestazioni di lettera, e il numero è
stampato invece di essere nascosto. 31 righe sono scartate perche' non sono una
parola, e anche quelle sono stampate con il numero di riga.

Il glossativo conta **2606 locuzioni** e **14764 parole singole**.

**Verifiche.** 226 test (erano 226): nessuno nuovo, perche' le fonti sono
dati e i dati li controlla `verifica`; i tre test che sono falliti durante
questo lavoro — copertura, locuzioni, test dichiarati — hanno fatto il loro
compito e ora confrontano il numero vero. `verifica`: 0 errori, 8 avvisi.
Copertura: 4146 su 10744, **38,6%** (era 38,4%). Glossario: 17370 voci (erano
16739). Scanner: 0 righe sospette.


## 0.20 — 2026-10-04 · La voce si sceglie nelle regole, e una voce che non suona si dichiara

**La domanda.** «Tutte le prove che ho fatto somigliano molto e fanno
abbastanza schifo: fai che io possa scegliere tra vari riproduttori vocali, nelle
regole che tu stesso hai scritto.» La voce era una **costante** in
`sorgenti/traduttore/voce.py` (`VOCE_DEFAULT = "it"`): si poteva cambiare solo
modificando il codice, e il posto in cui le regole di pronuncia sono scritte —
`dati/fonetica.jsonl` — non diceva niente di come il suono venga prodotto.

La scelta e' adesso **nel file delle regole**, in una riga sola:

    // SISTEMA {"voce": "it", "velocita": 130, "voti": [...]}

`dati/fonetica.jsonl` ha gia' dentro le regole di lettura della grafia, le
regole che la fonte dichiara e quelle che non dichiara. Una voce scelta in un
altro file sarebbe una regola che nessuno apre, quindi una regola che non c'e'.
La riga comincia con `// SISTEMA ` ed e' l'unica riga del file che il programma
legge invece di ignorarla come un commento; se manca o e' rotta, il programma
**dichiara** che il file non lo dice e usa il ripiego — `it` a 130 parole al
minuto — che e' dichiarato con la stessa prosa nel codice.

**Ogni parola puo' scegliere la sua.** Ogni riga ha adesso il campo facoltativo
`voce`: vuoto vuol dire «quella dichiarata qui sopra». Nel file nessuna riga lo
riempie, e quel vuoto e' dichiarato per iscritto: scegliere la voce di una parola
e' una decisione che prende un orecchio, e la griglia di
`raccolta/audizione.py` e' lo strumento con cui prenderla.

**La misura che mancava, e la scoperta che e' costata.** «Quale voce e' la
migliore?» era una domanda senza verifica, perche' nessuno controllava se una
voce **suonasse**. Il comando `voci` adesso lo fa, e la prima esecuzione ha
detto due cose:

- tutte le varianti italiane producono **lo stesso IPA** (`maɡnˈar` con `it`,
  `it+f2..f5`, `it+adam`, `it+croak`): cambiano il timbro, i suoni no. Il
  confronto fra timbri era cio' che l'audizione mostrava, e la sua conclusione
  — «tutte somigliano» — era giusta per una ragione che nessuno aveva scritta;
- le quattro voci `it+mbrola1..4`, che sono italiano **parlato** e non sintesi e
  sarebbero la risposta giusta, qui non suonano: il `wav` che ne esce e'
  **identico byte per byte** a quello di `it`. Non e' una configurazione da
  correggere: `espeak-ng` pilota mbrola da `mbrowrap.c`, tutto sotto `#if
  defined(_WIN32)`, quindi su macOS ricade in silenzio sulla voce di sintesi.
  Per questo lo stesso `espeak-ng --voices` non le elenca piu'.

**Mbrola e' installato, e non serve a niente: si dice anche questo.** Il
programma `mbrola` e i quattro database italiani (`it1`, `it2` dell'Istituto di
Fonetica di Padova, `it3` dell'Universita' di Trento, `it4` dell'ITC-irst) sono
stati scaricati e compilati sulla macchina, con la licenza accanto a ciascuno:
gratuiti per uso non commerciale, vietati in un prodotto venduto, che per un
progetto didattico va bene. Eppure non suonano, per la ragione di sopra: servirebbe
un `espeak-ng` costruito con il supporto mbrola, e quel codice su macOS non
esiste. Il progetto **non redistribuisce** nulla di tutto questo e non lo
dichiara come una sua dipendenza: resta una prova, e la prova e' scritta nel file
delle regole accanto alla voce che si usa davvero.

**Un controllo in piu', F15.** Chiede che la dichiarazione ci sia, che la voce del
sistema e quella di ogni riga stiano fra i voti, e che la velocita' sia un
numero. Se `espeak-ng` c'e' ed è installato, chiede anche che conosca quei nomi:
e' un **avviso** e non un errore, perche' lo stesso dato puo' essere giusto e
l'installazione sbagliata.

**Il test che prende il difetto vero.** Dodici test, e due di loro prendono il
difetto e non uno sbaglio di scrittura: quello che verifica che i voti
dichiarati **producono file diversi** fra loro, e quello che verifica che una
voce fuori dai voti e' un errore. Il primo e' la misura resa regola: se un
giorno una voce accettata dal programma producesse di nuovo lo stesso file, il
test fallisce invece di lasciare una colonna vuota in una griglia.

**Le versioni non erano d'accordo.** `pyproject.toml`,
`sorgenti/traduttore/__init__.py` e la frontmatter di `README.md` dicevano
`0.17` mentre il registro era a `0.19`: la regola del registro chiede che le
tre concordino e due rilasci non le avevano allineate. Ora sono tutte a `0.20`,
e la prossima riga che cambia il comportamento le aggiorna con se'.

**Verifiche.** 226 test (erano 214): **dodici** sulla voce dichiarata.
`verifica`: 0 errori, 8 avvisi. Equivalenza: 12 frasi, 0 divergenze. Scanner: 115
file tracciati, **0 righe sospette**. Sito: 40 pagine, 34 fette,
`traduttore.html` a 2385 KB sotto il tetto di 3 MB.

**Lo scanner, e le sue tre eccezioni dichiarate.** `prove/scanner.py` cerca nei
file tracciati da git gli ideogrammi, il cirillico, il greco, il kana e la
scrittura coreana: caratteri che si somigliano a una lettera italiana e che
bastano a rendere una parola falsa senza che nessuno se ne accorga. Passa con
**zero** righe sospette, e le sue eccezioni sono tre, scritte dentro il file e
non nella testa di chi lo gira: `χ` e `β`, che sono simboli IPA e senza dei
quali `ipa_valida` non accetterebbe niente, e `λ`, che compare in due voci del
glossario — `biλjét` e `biλjêtàri` — perche' **la fonte** (Bigoni, S006, voci
701 e 702) usa la lambda per il suono che l'italiano scrive `gl`. Il progetto
lo dichiara: la chiave di ricerca di quelle due voci e' `bijét`, cioe' senza
lambda, e la `fonte` dice quale vocabolario le ha scritte.

**Un controllo che mancava: girare il workflow in locale.** `prove/ci_locale.py`
estrae i passi `run:` da `.github/workflows/*.yml` e li esegue con la shell,
uno alla volta, fermandosi al primo che esce diversi da zero e dicendo quale.
Non e' un sostituto del workflow — non usa `actions/checkout` e non ha
`ubuntu-latest` — ma evita la cosa peggiore: scoprire che una riga di un passo
e' rotta solo quando GitHub la esegue. Per il rilascio di questa versione: 16
passi (quindici del workflow e lo scanner), tutti usciti con zero.


## 0.19 — 2026-10-04 · Il bottone che mancava, e la voce che non puo' essere quella giusta

**Il bottone.** La pagina del traduttore scriveva «come suona: portàr /porˈtar/»
e non offriva modo di ascoltarla. I suoni generati c'erano gia' tutti nei dati
di **quella** pagina — dodici righe con il percorso del file — ma nessun codice
li disegnava: il player esisteva dentro `riproduttore()`, che chiama solo la
pagina dei suoni. Il traduttore sapeva *scrivere* che una parola si pronuncia e
non sapeva farla pronunciare, che e' il peggiore dei due modi di saperlo, e in
un progetto che si chiama «ascolto ferrarese» e chiede di far ripetere questa
e' la differenza fra una trascrizione e un suono.

Il bottone compare adesso accanto alla trascrizione, **solo** per le parole che
hanno un suono dichiarato. Non si e' allargato alle altre 16727: quelle non
suonano apposta, perche' la loro trascrizione ha un dubbio dichiarato e
suonarle insegnerebbe il suono sbagliato. Quel divieto e' scritto in
`raccolta/sintetizza.py` e il bottone non lo tocca.

**Il criterio, e il suo primo tentativo.** La prima versione accettava un suono
solo se la sua IPA coincideva con quella dichiarata accanto. Su dodici ne
passava **uno**: le altre undici sono la stessa parola con l'accento tonico
sulla sillaba diversa (`/portˈar/` accanto a `/porˈtar/`), che il controllo F14
chiama gia' «non un suono». Un criterio cosi' non e' severo, e' sbagliato:
nascondeva il bottone proprio dove il suono c'era, che e' il difetto peggiore
che un bottone possa avere — assente, e senza dire perche'.

La versione giusta confronta la **forma scritta**, che e' l'unica cosa che
distingue una parola dall'altra, ed e' la stessa chiave con cui `risolvi` sceglie
la trascrizione: bottone e trascrizione non possono guardare due cose diverse.
Su una voce con piu' forme (`frarés` e `frarèz` hanno due suoni distinti) se
nessun suono e' della forma cercata non si offre niente.

**Il test ha preso un difetto vero, e non mio quello che pensavo.** Il test
sulla forma giusta falliva perche' il mio ripiego offriva il suono di `frarés`
mentre si chiedeva `frarèz`: una **parola diversa**, dichiarata come una
differenza di sillabazione. La dichiarazione era vera e il suono era sbagliato.
La regola era scritta male e il commento che la descriveva era scritto bene,
quindi il file diceva una cosa e ne faceva un'altra.

Poi il test ha continuato a fallire anche dopo la correzione, perche' nei dati
del test avevo scritto `frarès`, che non e' una parola: la chiave toglie gli
accenti, quindi `frarès` e `frarés` diventano la stessa e il confronto tornava
per la porta sbagliata. Due errori in due righe diverse, presi entrambi dal
test e non da un ragionamento.

**La voce: cosa non si può fare, detto prima di farlo.** Il suono sembra «un
inglese che cerca di parlare ferrarese», e la diagnosi e' giusta: e' un italiano
che applica regole italiane a una grafia romagnola. Fra le lingue che questa
installazione di espeak-ng offre, **l'unica romanza e' l'italiano**: non c'e'
l'emiliano-romagnolo, che e' la famiglia giusta. Quindi un confronto fra
«fonatori» puo' cambiare il **timbro** e non la pronuncia. Una voce migliore
rende il suono meno sgradevole, non piu' ferrarese, ed e' importante dirlo
perche' la domanda «quale voce e' la migliore?» ha una risposta e la domanda
«come si fa a suonare ferrarese?» no, dentro questi vincoli.

Quello che la migliorerebbe sono le regole dichiarate in `dati/fonetica.jsonl`,
che il progetto dichiara gia' `attendibilita I`. E' lavoro di una persona, come
i 316 disaccordi fra S006 e il Ferri: nessuno script puo' decidere che
`majàl` si dice con la `j` semivocale.

**L'audizione.** `raccolta/audizione.py` genera una griglia di parole per voci.
La pool non e' una lista di parole facili — quelle non distinguono niente,
perche' tutte suonano male e il confronto non serve — ma **tredici parole
scelte perche' ognuna mette alla prova una regola diversa**, con la ragione
scritta accanto. Serve anche a distinguere due problemi: se una voce e' buona
su `ghe` e cattiva su `majàl` il difetto e' della voce, se e' cattiva su tutte
il difetto e' delle regole. Due problemi diversi, due soluzioni diverse.

Nella griglia non c'e' nessun punteggio e nessuna stellina. Un numero li' sarebbe
un giudizio che lo script non puo' formulare, e la scelta la prende chi ha
ascoltato. Quello che lo script produce e' il mezzo, in
`raccolta/lavorato/audizione/` che e' gitignorato; il risultato — quale voce ha
scelto una persona e perche' — va scritto in `dati/` e dichiarato qui.

**Verifiche.** 214 test (erano 204): **sette** sul bottone e **tre** sulla pool
dell'audizione. I sette sul bottone sono stati provati ricreando il difetto —
togliere la chiamata alla riga ne fa fallire tre — e uno di loro ha preso un
difetto vero nella mia implementazione, non nel dato.
`verifica`: 0 errori, 8 avvisi. Equivalenza: 12 frasi, 0 divergenze. Scanner: 115
file tracciati, 0 ideogrammi. Sito: 40 pagine, 34 fette, `traduttore.html` a 2,4
MB sotto il tetto di 3 MB.


## 0.18 — 2026-10-04 · Le 6352 parole di Bigoni, e le due lettere che l'indice buttava via

Il pendente che restava dichiarato — portare le 7307 coppie di S006 nel
glossario attivo — e' chiuso. Il glossario passa da **10387 a 16739 voci**.
Ma la parte interessante di questa voce non e' il numero: e' che per
arrivarci sono usciti **cinque difetti veri**, e quattro di loro producevano
righe ben formate che nessun controllo poteva vedere.

Il glossario conta **2329 locuzioni** e **14410 parole singole**. Il numero
e' contato con `tokenizza()`, la funzione che il motore usa per accorpare le
locuzioni, e non con uno `split` di comodo: i due non contano le stesse
cose, perche' `split` spaccia l'apostrofo interno (`d\'avril` diventano due
parole) e `tokenizza` lo tiene dentro, che e' come funziona il ferrarese. Il
numero che la voce 0.7 dichiara — 2034 locuzioni su 10387 — era vero per
quel glossario, ed e' falso per questo: non e' che il conto sbagli e'
cambiato, e' che il conto era fatto con un altro criterio.

**Il difetto che rendeva ogni ricerca sbagliata.** `normalizza.chiave()` e
`tokenizza()` filtravano con l'intervallo `\u00c0-\u024f`, che finisce a
U+024F. Ma l'alfabeto ferrarese dichiarato in `dati/regole_grammaticali.json`
(fonte S015) contiene due lettere **fuori** da quell'intervallo: `ɣ` (U+0263) e
`ʎ` (U+028E). Erano trattate come punteggiatura e cancellate in silenzio.

La cancellazione silenziosa e' la cosa piu' pericolosa che possa fare una
chiave di confronto: `àɣar` (duecento) e `àar` diventavano la stessa chiave
`aar`, e la ricerca del glossario restituiva la voce sbagliata **senza dire
niente**. Il difetto era dormiente perche' il vocabolario del 1889 usa
quasi mai queste lettere — `braɣ` e `biλjét` ci sono, e basta — e nessun
controllo confrontava la chiave vecchia con la nuova. Il numero delle chiavi
che il filtro perdeva e' **861** su 10431 righe.

La correzione non e' una lista di lettere ammesse piu' lunga: e' `[\W_]` con
il flag unicode, che tiene **qualsiasi** lettera. Una lista funziona finche'
nessuno aggiunge un carattere, e il progetto perdeva una lettera dell'alfabete
ogni volta che qualcuno lo faceva. Il test che mancava c'e' ora, e prende
l'alfabeto **dai dati**: una lettera aggiunta a `regole_grammaticali.json`
senza aggiornare il filtro fallisce li', e non in fase di ricerca con uno
studente davanti.

**Il suffisso dell'omonimo che non c'era.** `bigoni.py` cercava il suffisso
numerato nella cella dei significati, dove il sito non lo scrive mai: sta nel
primo argomento del bottone. Il campo `omonimo` leggeva quindi **zero**
ommonimi su 7307 righe, e zero sembrava un numero giusto. Il numero vero e'
**186** (170 col trattino e 16 senza trattino, come `acciarino1`).

Il test che copriva questa cosa esisteva gia' e **passava per il motivo
sbagliato**: verificava la cella, che non ha mai avuto il suffisso, quindi
guardava il posto in cui il codice non guardava. Un test che guarda dove il
codice non guarda non copre niente e non lo dice.

**L'id che riscriveva la fila d'attesa.** `prossimo_id()` guardava solo il
glossario attivo, e `dati/da_verificare/glossario.jsonl` contiene cinque id
(`V10400`-`V10404`) piu' alti di tutti quelli attivi. Il generatore ha quindi
cominciato a scrivere da `V10390` e ha **ridescritto quei cinque id**: non le
voci in attesa, che non si toccano, ma i numeri. L'errore e' arrivato dopo,
dal controllo **D1**, e ha bloccato tutte e 6426 le righe in un colpo: una
collisione di cinque numeri ferma il lavoro di settimila voci. Un id non e' un
contatore, e' un'identita' che due file diversi si contendono.

**Il generatore che riscriveva quello che aveva scritto.** `da_bigoni.py` non
era idempotente: il secondo giro scriveva **194 righe duplicate** di parole
che aveva scritto lui stesso un minuto prima. Tutte ben formate, nessun
controllo che le fermasse. La causa era l'ordine dei due confronti — prima la
fonte, poi il glossario — e l'errore si era presentato due volte di fila,
sotto due forme diverse, prima di arrivare al posto giusto: si guarda **prima
l'attivo**, che e' la verita', e solo se la voce non c'e' si chiede se la
fonte la sta ripetendo.

**La pagina che aveva superato il tetto.** Con 16739 voci `traduttore.html`
pesava 3,9 MB, sopra il tetto di 3 MB della CI. Il tetto e' dichiarato e non
si alza — «sopra, la pagina non si apre subito e il progetto smette di essere
consultabile» — quindi la risposta non era spostare la soglia. Era che
`CAMPI_MOTORE` trasportava il campo `note`, **1,4 megabyte di testo che
nessun codice della pagina leggeva**: era dentro per completezza dello schema,
non perche' servisse. Tolto, la pagina pesa 2,4 MB e le note restano tutte in
`dati/glossario.jsonl` e nelle pagine del glossario.

**Le parole funzionali.** I test hanno rifiutato `al` = «il» e `kóŋ` = «con»:
gli articoli e le preposizioni non sono voci, sono gia' in `morfologia.py`. Il
filtro guarda la **traduzione**, non la parola ferrarese, ed e' la parte
delicata: un filtro che guardasse la parola ferrarese avrebbe buttato `kóŋ`,
che e' una parola ferrarese vera, e avrebbe lasciato passare `al`. Avrebbe
passato lo stesso test e fatto il contrario di quello che serve.

**I 6352, e come sono arrivati.** Dalle 7307 coppie: **590** non si aggiungono
perche' la voce c'e' gia' con lo stesso significato, **316** sono un
disaccordo fra due fonti e nessuno sceglie, **12** sono la stessa voce scritta
due volte nella fonte, **34** sono parole funzionali, e le altre **6352**
entrano. Nessuna delle 6352 ha il significato moderno: la fonte non lo
porta e il campo resta vuoto. E' per questo che il **4063** della voce
0.14 e' ancora il numero vero, e non un numero rimasto indietro: il
numeratore e' rimasto quello e il denominatore e' cresciuto di 6352.
entrano. Le voci hanno `attendibilita I` e `da_verificare: true`: la fonte si
puo' aprire, ma nessuno ha controllato che la riga letta corrisponda a quello
che c'e' scritto, e dichiararle `D` sarebbe dichiarare una verifica non
avvenuta — 6352 avvisi G7, cioe' un controllo che smette di dire niente.

La `varieta` viene da `dati/varieta.json`, che ora dichiara S006 come
`cittadino` con `attendibilita M`: la scelta e' nostra e viene dichiarata come
memoria, esattamente come per S001 e S004. Il generatore **non indovina**: se
quella riga manca, si ferma.

**La normalizzazione esisteva in due copie, e una sola era stata
corretta.** Il difetto delle lettere dell'alfabeto perdute viveva in
`normalizza.py`, che e' il motore del traduttore. La stessa identica logica
esiste anche in `sorgenti/modello.html`, perche' il motore di ricerca gira nel
browser e non puo' chiedere niente al server. Le due copie erano state
scritte una per una, e quando la prima e' stata corretta la seconda e' rimasta
sbagliata: la pagina del dizionario cercava `aar` mentre il traduttore cercava
`aɣar`, e chi usava il dizionario non trovava la parola che il traduttore
conosceva.

La correzione e' stata fatta due volte, e la prima era sbagliata. Sostituire
l' intervallo con `[\w_]` sembrava la risposta — `\w` in Python comprende
`\u00c0-\u024f` — ma in JavaScript `\w` non comprende `ɣ` (U+0263), che pure
e' una lettera dell'alfabeto dichiarato in `regole_grammaticali.json`. Il
test che proteggeva la cosa passava gia' con la correzione sbagliata, perche'
guardava `à` e `ø`, che `\w` include in entrambi i linguaggi, e non guardava
`ɣ`. Solo i property escapes risolvono: `/[^\p{L}\p{N}]+/gu` in JavaScript
e `[\W_]` in Python dicono entrambi «tutto quello che non e' una lettera o
una cifra», che e' quello che l'alfabeto del progetto voleva dire.

Il fatto che una correzione di una riga possa passare un test che esiste per
impedirlo vale la pena scriverlo: il test e' stato allargato alle due lettere
che `\w` non copre, e i test adesso girano la copia JavaScript con `node` e
confrontano le due implementazioni voce per voce. Una copia che nessuno
eseguiva non era una copia, era un'altra versione del bug.

**Verifiche.** 210 test (erano 177). `verifica`: 0 errori, 8 avvisi.
Equivalenza: 12 frasi confrontate, 0 divergenze. Il glossario e' passato da
21 a 34 fette, il sito da 27 a 40 pagine. `note` non e' piu' trasportata dalla
pagina del traduttore: 2,4 MB invece di 3,9.

**Il difetto che stavo per introdurre.** Nessuno dei quattro precedenti e' un
difetto di questo progetto: sono difetti che il glossario aveva. Questo e'
mio, e l'ho fatto mentre scrivevo questa voce.

Portando il glossario da 10387 a 16739 voci ho fatto una sostituzione globale
di «10387» in «16739» in tutto il registro, e una parte di quelle
sostituzioni ha reso false frasi che erano vere. Il registro **racconta** — ogni
voce dice quello che era quando e' stata scritta — quindi sostituire anche i
denominatori significa far dire alla voce 0.14 che 4063 voci su 16739 hanno il
significato moderno, quando 4063 era vero **su 10387**: le 6352 voci di S006 non
hanno il significato moderno, il numeratore e' rimasto, il denominatore no, e
la frase prometteva il 24% mentre il vero e' il 41%. Sono tornati indietro i
numeri delle voci 0.7, 0.8, 0.9, 0.14 e 0.17; i due che restano, nella voce
0.18, sono gli unici che descrivono lo stato di oggi e li' sono giusti.

Il numero delle locuzioni era inoltre sbagliato per un motivo che si vede solo
guardando **come** era contato: con `split()`, che spaccia l'apostrofo interno
(`d'avril` diventano due parole), mentre il motore usa `tokenizza()`, che lo
tiene dentro. Quindi non era un numero da aggiornare ma un numero da ricontare
con la funzione giusta: 2329 non e' «2034 piu' 295», e' un conteggio fatto
altrimenti.

E la copertura. `README.md` e `lacune.md` dichiaravano **23,7%**, il numero di
quando il glossario aveva 10387 voci; adesso e' **38,4%** su 16739, cioe' che
le 6352 nuove voci hanno coperte 1577 parole dell'ItWaC che il glossario del
1889 non copriva. Il numero era rimasto fermo perche' nessuno lo guardava: il
numero dei test era sorvegliato, il frontmatter del registro anche, la copertura
no. E la copertura e' l'unico numero che `README.md` chiama «il numero che
`buchi` non da'», cioe' quello su cui si regge la promessa del progetto. Ora c'e'
un test che lo confronta con `copertura.py`; salta quando gli elenchi ItWaC non
sono presenti e **dichiara di saltare**, perche' la CI non li ha e un test che
non puo' girare non deve fingere di essere passato. In CI la copertura resta
quindi senza guardia, e va detto: il metro e' un elenco di terzi che il progetto
non puo' dichiarare come fonte.

Quattro difetti in questa voce, e tre dei quattro hanno una cosa in comune: non
producevano una riga malformata. Il quarto, il piu' subdolo, produceva
righe **bene** formate che nessun controllo poteva vedere. Un difetto che
appare in un numero scritto e in un documento e' meno rumoroso di uno che
appare in un dato, e pero' e' piu' pericoloso: il dato sbagliato lo prende
qualche controllo, il numero sbagliato no, perche' nessun controllo legge i
numeri scritti a mano se non li si e' deciso di sorvegliarli. E la sorveglianza
non si eredita: il numero dei test e' sorvegliato perche' qualcuno ha deciso di
sorvegliarlo, e non perche' i numeri si sorveglino da soli.


## 0.17 — 2026-10-04 · Il glossario in ventuno fette, e perche' potare i campi non bastava

**Perche'.** La pagina pesava 6,2 megabyte e li caricava tutti insieme. Chi
arrivava con una connessione lenta aspettava, e chi aveva un telefono vecchio
aspettava di piu': la prima impressione del progetto era la parola «lento».
Dividere il sito in piu' pagine e' sembrata la soluzione, ed e' una solzione,
ma non per il motivo che sembrava.

**La meta' che non c'era.** Il motivo vero della grandezza non era il numero di
parole: era che ogni riga portava scritti campi che la pagina non usava quasi
mai. Qui i due tentativi sbagliati insegnano una cosa che vale per tutto il
progetto: **potare i campi non basta**. I campi inutili erano il 27% (`notes` e
`fonte` insieme), e la forma compatta — non ripetere le stesse chiavi 10387
volte — il 23%. Insieme poco piu' della meta': toglievano un megabyte su sei, e
il grosso restava.

**I dati erano distribuiti, non grandi.** Le 10387 voci non erano un blocco
solo: nella pagina c'erano anche le coppie, i 28 proverbi, le regole e il
pannello dei numeri. Nessuna parte era grande abbastanza da spiegare 6,2
megabyte da sola. Un file che contiene molte cose piccole e' grande per la
somma, e la somma si divide solo dividendola.

**Che cosa e' stato fatto.** Ventisei pagine invece di una: home, traduttore,
glossario, ventuno fette da 500 voci, frasi e suoni. La home pesa **82
kilobyte** invece di 6,2 megabyte, e nessuna pagina supera i **3
megabyte** — un tetto che ora controlla un passo della CI, pagina per pagina,
perche' un peso che nessuno guarda torna.

**Il costo, che e' reale.** La somma dei ventisei file e' **8,0 megabyte**,
non 6,2: il modello, la barra e i dati comuni sono ripetuti in ogni pagina, e
ogni fetta porta la barra delle sue vicine. Il sito pesa quindi di piu' di
prima, pur pesando meno per chi apre qualcosa. Va detto qui perche' e' un
numero che si puo' misurare, e un numero che si puo' misurare non si nasconde:
una pagina sola che si carica subito vale piu' di ventisei pagine veloci che
nessuno apre.

**La ricerca ha un limite, e lo dichiara.** La casella cerca dentro la fetta
aperta. Prima, quando non trovava niente, diceva «nessuna voce corrisponde»: e'
una frase falsa, perche' le voci sono 10387 e 10387 non e' nessuna. Ora dice
**«in questa fetta»** e rimanda alla barra in alto.

**Otto difetti, e ognuno ha un test.** Non sono difetti ipotetici: sono cose
che sono successe con la divisione gia' scritta.

1. `getattr(v, "fe", None)` **non falliva** quando il campo si chiama
   `ferrarese`: restituiva `None` e tutte le forme uscivano vuote, in nove
   righe. Ora c'e' una mappa esplicita dei campi che **solleva `KeyError`**
   su un campo sconosciuto: un campo nuovo non puo' passare inosservato.
2. Il blocco delle fette era annidato dentro la home, quindi spariva proprio
   dalle pagine che lo usano. Le sezioni non si annidano.
3. Una sostituzione indiscriminata aveva cambiato `document.getElementById`
   in `el()`, che pero' e' definito **dopo**: la pagina intera si rompeva e
   nessun controllo di sintassi lo segnalava, perche' `new Function()`
   accetta volentieri un nome che non esiste.
4. Un apostrofo non scappato dentro una stringa del motore rompeva il
   JavaScript. Errore di sintassi vero, questa volta.
5. Una **virgola mancante** nella lista dei numeri del pannello non e' un
   errore di sintassi — `["a"]["b"]` e' un'indicizzazione legittima — e il
   difetto emergeva lontano, dentro `pannello`. L'ha trovato solo
   `controlla_equivalenza.py`, che confronta la pagina costruita in Python
   con quella che il motore costruisce in JavaScript.
6. Le etichette delle fette erano duplicate: `A A B C C D D F G`, provate due
   volte. Ora sono numero piu' intervallo — `1. A`, `2. A–B` … `21. V–Z` —
   uniche per costruzione e non per controllo.
7. Il pulsante di una voce con due forme faceva sentire solo il primo suono:
   `V0021` ne ha due (`frarés` e `frarèz`), e il file `T0024.wav` era
   dichiarato e generato ma **non compariva in nessuna pagina**. Ora la scheda
   mappa tutti i suoni di tutte le forme.
8. Il messaggio di ricerca di cui sopra, che negava l'esistenza di voci che
   c'erano.**Il frontmatter che mentiva.** Questo file si dichiarava `versione: 0.15`
mentre le sue voci erano arrivate alla 0.17, e nessun controllo lo guardava:
la regola del progetto vieta i numeri che mentono, e valeva per i buhi
dichiarati ma non per la versione del registro stesso. Ora il frontmatter
dice 0.17 e c'e' un test che lo confronta con la voce piu' recente del
file — **senza scrivere la versione nel test**, perche' una lista di numeri
in un test diventa a sua volta un numero da correggere a mano, e il difetto
che il test cerca tornerebbe dalla porta da cui l'ho visto entrare. Il test
e' stato provato ricreando il difetto: fallisce con `'0.15' != '0.17'`.

**La fonte che era gia' nel registro e che nessuno aveva aperto.** S006 e
S015 sono le due pagine di R. Bigoni: erano state *esaminate*, e la nota di
S006 diceva che «non si puo' costruire un vocabolario da qui, perche' il sito
non lo mette in una pagina». Era **falso**, e si poteva dimostrare: il
vocabolario arriva da uno script che la pagina chiama, e ne dà **7307**
coppie numerate da 1 a 7307 con l'etimologia per voce. La nota era stata
scritta guardando la pagina invece di guardare che cosa la pagina chiede.

Con il permesso dell'autore le due fonti escono dalla fila d'attesa. Il
permesso e' dichiarato come dichiarato: chi l'ha concesso e quando, e che nel
repository **non c'e' il documento scritto**.

**Quattro difetti, e ognuno ha un test.** Sono della raccolta, e sono il caso
in cui i controlli devono morire per primi.

1. **Le colonne lette nel verso sbagliato.** Gli argomenti del bottone del
   sito erano nel verso opposto a quanto avevo supposto: il risultato sarebbe
   stato 7307 voci capovolte, ognuna ben formata e tutte sbagliate. Nessun
   controllo sui numeri e nessun controllo sui campi obbligatori lo prende,
   perche' una voce capovolta e' una voce perfetta. Ora ogni riga si legge
   due volte — dalla cella e dagli argomenti — e le due letture devono
   coincidere. Sulla parola ferrarese coincidono in tutte e 7307 le righe.
2. **La traduzione presa dal posto sbagliato.** In 156 righe il bottone non
   porta la traduzione ma la parola da cui l'etimologia parte: per `bak`
   porta `bac`, che e' il latino, mentre la cella dice «bastone, mazza».
   156 voci sarebbero entrate col significato sbagliato. La traduzione si
   legge dalla cella, che e' cio' che il sito mostra.
3. ~~**Il suffisso dell'omonimo confrontato prima di essere tolto.**~~ *Non
   era vero, ed e' stato scoperto nella 0.18.* Il suffisso non e' mai stato
   confrontato prima di essere tolto: il codice lo cercava nella **cella dei
   significati**, dove il sito non lo scrive mai, e quindi non lo trovava
   mai. Il numero dichiarato — «315 righe che erano a posto venivano
   scartate» — era falso: nessuna riga era mai stata scartata per questo, e
   nessuna era mai stata salvata. Il numero vero e' **186** omonimi (170 col
   trattino, 16 senza), e fino alla 0.18 il campo ne leggeva **zero**. La
   voce 0.18 contiene il conto e la correzione.
4. **La chiave che cancellava gli accenti.** `àɣar` diventava `gar` e `alòž`
   diventava `al`: duecento voci diverse con la stessa identita'. E' il
   difetto piu' subdolo dei quattro, perche' non faceva fallire nessun
   controllo — le voci semplicemente sparivano. Nell'ortografia di Bigoni
   l'accento segna l'accento tonico.

**Il numero che conta.** Le 7307 coppie erano un file grezzo e **non erano
ancora voci**. Nella 0.18 lo sono diventate, e il numero vero e' **6352**, non
i 7303 che questa voce dichiarava: la differenza e' il lavoro che il
confronto con il glossario gia' fatto ha reso visibile.

**La pagina delle regole.** Ventisettesima pagina: le regole che S015
dichiara per iscritto, che finora erano segnalazione e ora sono regole con la
fonte dichiarata **regola per regola**. Sono **29 regole** in sei gruppi —
come si scrive, gli articoli, i nomi e i loro plurali, i verbi, i pronomi, le
parole — piu' l'alfabeto per capire la pronuncia, che serve a leggere i
suoni e non a scrivere.

Tre scelte, e ognuna ha una ragione.

1. **La pagina si scrive sul server, senza JavaScript.** Tutte le altre
   pagine prendono i dati da `/*DATI*/null` e li disegna un motore. Qui no:
   le regole sono poche e sono note quando la pagina si genera, e una pagina
   che si legge anche con lo scripting spento serve di piu' in classe.
2. **La chiave dei dati si chiama `regoleGrammaticali`, non `regole`.**
   `regole` e' gia' occupata: sono le regole di derivazione che il motore usa
   per tradurre. Due cose diverse con lo stesso nome, e un giorno qualcuno le
   avrebbe confuse: e' il nome che collide a essere il difetto.
3. **Il testo delle regole e' riscritto, non copiato.** Quello che e'
   copyright e' la pagina di Bigoni, non il fatto che il plurale di
   `fraréš` sia `frarìš`. Ogni regola porta la fonte con il numero della
   sezione, cosi' chi legge puo' tornare alla frase originale — e la pagina
   **dichiara** che il testo e' riscritto, perche' quella dichiarazione
   diventi falsa nel giorno in cui qualcuno ci mette dentro il testo vero.

**Il difetto che la pagina mostrava e che nessuno aveva visto.** Diceva
«S015, sezione 3». E' l'identificatore che il registro usa, e a chi sta
imparando la lingua non dice niente: la fonte di una regola si scrive per
chi legge. Ora dice «R. Bigoni, «Il Ferrarese», note linguistiche, sezione
3», e l'identificatore sta nel titolo dell'elemento, dove serve a chi deve
tornare al registro.

**Verifiche.** 177 test (erano 155). `verifica`: 0 errori, 8 avvisi.
Equivalenza: 12 frasi confrontate, 0 divergenze. Scanner: 67 file
tracciati, 0 ideogrammi. Un passo nuovo della CI controlla che ogni pagina
contenga i suoi dati, che nessuna superi i 3 megabyte, che ogni fetta abbia
le sue voci e la sua barra, e che ogni link della barra apra un file che
esiste.

## 0.16 — 2026-10-04 · Il pulsante che fa sentire la parola, e le tre frasi che diventavano false

**Perché.** La pagina aveva un riproduttore che poteva suonare **zero** cose,
e una trascrizione IPA accanto a ogni parola: 28 simboli che descrivono un
suono che nessuno poteva sentire. Il gioco è per ragazzi che imparano una
lingua a orecchio. Un gioco di lingua che non si può ascoltare è un gioco di
lettura con la fotografia accanto.

**Che cosa è stato fatto.** Dodici parole suonano, in `web/sintesi/`, e
accanto al pulsante c'è scritto che il suono l'ha fatto un programma. Il
manifesto è `dati/sintesi.jsonl`, generato da `raccolta/sintetizza.py`, e la
pagina lo legge da lì.

**Le tre frasi che il pulsante rendeva false.** Non sono state scritte da
qualcuno che non sapeva: erano la versione corretta di un'altra idea, e quella
idea era sbagliata.

1. `modello.html` diceva: «nessuna voce sintetica può fare da ferrarese, e
   questo progetto non lo prova». Il principio è giusto, la soluzione no: un
   suono generato **esiste**, esisteva già prima che il progetto se ne
   accorgesse, e non metterlo non è onesto, è solo più muto. La regola vera è
   un'altra: il suono si mostra, ma non può passare per una persona.
2. Il commento del riproduttore diceva: «non mette una voce sintetica al posto
   di una persona: non esiste e non si può fingere che esista». Il secondo
   membro è giusto e il primo no, perché **se lo mette al posto di** è proprio
   quello che va evitato, non quello che va evitato da metterlo.
3. `sorgenti/traduttore/audio.py` diceva che mettere una voce sintetica è
   «l'opposto di quello che fanno i progetti che mettono una voce sintetica e
   la chiamano «il ferrarese»». La frase è giusta sul **come** e sbagliata sul
   **se**: il progetto mette una voce sintetica e la chiama «il ferrarese» in
   tre posti. Quindi l'ha fatto, dichiarandolo.

**Due cartelle, e perché.** `web/audio/` sono registrazioni di persone vere e
i controlli A1-A10 contano i file che ci trovano chiedendo consenso, licenza e
pubblicazione. `web/sintesi/` sono voci di programma. Un suono generato nella
prima cartella renderebbe falso un conto che il progetto mostra pubblicamente,
quindi i due insiemi non si toccano: **Y3b**.

**Perché dodici, e non tutte.** Suonare tutte le 10401 parole costerebbe circa
**493 megabyte**, che non è una pagina. Quindi il suono esiste solo dove il
progetto ha già scritto come la parola si pronuncia: le 28 trascrizioni
dichiarate. E anche lì non tutte: delle 28, **16 non suonano**, perché hanno un
dubbio che le regole di lettura segnalano — la `gn` davanti ad `à` di
`magnàr`, l'accento non marcato di `principiar`. Suonarle produrrebbe uno
studente che impara un suono sbagliato con la stessa efficacia con cui avrebbe
imparato quello giusto, e senza potersene accorgere. **Y4** verifica che quei
file non comparano.

**Un difetto mio, trovato guardando il file.** Avevo scritto, e pubblicato nel
docstring di `sintesi.py`, che `espeak-ng` scrive il proprio nome nel commento
del formato RIFF e che quindi si poteva riconoscere un suono generato
guardando dentro il file. Ho aperto il file: dentro un `wav` generato non c'è
la parola «espeak» **nemmeno una volta**, e il formato è un RIFF con quattro
campi e nient'altro. Il controllo che si basava su quella frase non poteva
scattare mai, e sarebbe passato per sempre senza aver guardato niente. Ora
Y3b confronta i **nomi** dei file, che è l'unica cosa che il file non
dichiara, e c'è un test che verifica la cosa negativa: dentro il `wav` non c'è
«espeak».

**Un altro difetto, trovato guardando la pagina.** «portàr» e «portar» sono due
forme scritte della stessa voce e hanno due trascrizioni diverse,
`/portˈar/` e `/porˈtar/`. La scheda mostrava la seconda e il suono era della
prima: due righe che si contraddicono nella stessa scheda. Ora la scheda del
suono porta **la sua** trascrizione e, quando differisce, dice perché.

**Che cosa non cambia.** Un suono generato non verifica niente. Le righe
restano `attendibilita: "I"` e `da_verificare: true`, e l'unica cosa che chiude
la domanda è un parlante ferrarese che dica la parola.

**Verifiche.** 155 test (erano 137). `verifica`: 0 errori, 8 avvisi, e i
controlli Y1-Y4 non trovano niente sui dodici suoni. Equivalenza Python e
JavaScript: 12 frasi, 0 divergenze. Il passo nuovo della CI confronta il
manifesto con `web/sintesi/` nelle due direzioni ed e' stato provato nelle due
sense: con un file in piu' in `audio/` esce diversamente da zero.

**Il costo.** dodici file, 523 KB. Il generatore cancella `web/sintesi/` prima
di riscrivere, così un file che non è più dichiarato non sopravvive. La CI
confronta il manifesto con la cartella nelle due direzioni: una riga senza file
e un file senza riga sono entrambi un errore.

**Correzione dello stesso giorno, nei documenti che il pulsante non aveva
toccato.** Cercando che cosa era rimasto indietro, sono tre fatti che nessun
controllo guardava e che sono tutti della stessa specie: numeri e affermazioni
che non corrispondevano a quello che c'era.

1. `RACCOLTA.md` dichiarava **30** trascrizioni, in due punti, e
   `dati/fonetica.jsonl` ne ha **28**. Il numero era già sbagliato prima di
   questa versione; è stato trovato perché la sezione sulle trascrizioni è il
   posto dove i suoni generati dovevano essere descritti, e guardandola è
   venuto fuori che due passi prima c'era un altro numero fermo nel tempo.
2. La stessa sezione si intitolava «**Le sette cartelle**» e la tabella ne
   elencava **otto**: le righe erano cresciute — proverbi, proposte, e adesso
   i suoni — e il titolo no. Nessun numero lo confrontava con quello sotto,
   quindi nessuno se ne accorgeva.
3. `sorgenti/traduttore/__init__.py` non esportava `Sintesi` e `Suono`, che
   sono esportati come `Archivio` e `Brano`. Chi legge il pacchetto li cercava
   con lo stesso nome e non li trovava.

Tutti e tre hanno ora un test che li controlla, perché la lezione dei due
giorni precedenti è che **un numero non sorvegliato invecchia** e che l'unica
difesa è mettergli un test accanto, non trovarlo a mano.

Nessun dato e nessuna pagina cambiano: `web/index.html` rigenerato è identico
byte per byte, e questo è il controllo che dice che la correzione è stata solo
nei documenti.

## 0.15 — 2026-10-04 · Il numero di copertura che si alzava perché qualcosa non era guardato

**Perché.** Pietro ha provato a tradurre «sono seduto sulla sedia» e il
risultato è stato `son seduto Sslà Scaràna`: quattro parole su cinque, e un
buco. Il buco non era `seduto` — quello è un participio e il glossario contiene
`sedare`, non le forme finite — ma **tutto il resto della frase**. Il glossario
ha 11451 lati italiani distinti e fra questi non c'è nessun articolo, nessuna
preposizione e quasi nessun ausiliare. Su 48 parole funzionali italiane
frequenti, 11 ci sono.

**Il difetto peggiore era nella misura, non nei dati.** `copertura.py`
escludeva le parole funzionali dal conteggio e diceva, in due punti, che
«sono in `morfologia.py` e il motore le tratta a parte». Sono due frasi false:
in `morfologia.py` non c'è nessun elenco di articoli o preposizioni — quel
modulo impara desinenze dal corpus — e il motore non le tratta: `il -> il` con
confidenza 0, `ho -> ho` con confidenza 0. Escludere 14 parole non coperte
faceva salire la percentuale, e una percentuale che sale perché si nasconde una
parte è falsa per quanto sia comoda. Ora il rapporto **misura** quante
funzionali il glossario trova, e stampa il numero: 131 nell'elenco, 38
presenti, 93 che passano invariate e finiscono nei buchi. Il 23,7% resta
quello che è — la copertura dei **lemmi di contenuto** — e la pagina lo dice.

**Il participio, che è un altro problema.** `seduto`, `mangiato`, `andato`,
`stato` non ci sono, e non possono arrivarci dal vocabolario: il Ferri è un
elenco di lemmi. Riconoscere un participio dalla radice del verbo è morfologia,
non vocabolario, e questa è la strada giusta — ma è una strada nuova, e su
`dati/regole.json` non ci sono esempi che la insegnino.

**Le due fonti indicate.** Il vocabolario di Bigoni (S006) **non si può
usare**, e per due motivi indipendenti: il sito non dichiara diritti in
nessuna delle due pagine (la licenza resta «da chiedere», quindi la fonte non
può alimentare il glossario) e il vocabolario non è nelle pagine: `VocFeIt.html`
e `VocItFe.html` contengono solo la descrizione dell'ortografia e una trentina
di `<tr>` di consonanti e vocali, mentre l'elenco delle parole viene servito da
`elencoParole.php` con una POST. Non è scaricabile, e non è comunque
riutilizzabile senza il permesso.

Quella seconda pagina invece è utile, e per un motivo diverso da quello che si
cercava. «Il Ferrarese — note linguistiche» è **S015**, che il registro
aveva già come `esaminata`, e dichiara regole che il sistema di lettura della
grafia **non ha**: l'assenza di consonanti doppie, l'assenza di dittonghi
nelle vocali accentuate, l'infinito della prima coniugazione in `-àr` e non in
`-èr` (che è la ragione delle quattro righe che il controllo F14 non riesce a
riconciliare con Biondelli), e una `l` di pronuncia fortemente velare. Sono
regole che una fonte dichiara, che è esattamente la condizione che il progetto
si dà prima di usare una regola, e nessuna delle quattro è nel sistema.
Non sono state applicate: applicarle cambierebbe delle trascrizioni, e S015
non ha licenza verificata. Sono segnalate, e sono il punto da cui cominciare
quando la licenza si chiarisce.

**Quello che non si e' fatto, e perche'.** Non si sono aggiunte parole
funzionali al glossario: ogni voce ha bisogno di una fonte, e nessuna delle
fonti aperte le contiene. Aggiungerle a mano sarebbe stato l'unico modo di
far quadrare la frase, ed è esattamente il modo che questo progetto non prende.
La domanda — quale fonte dichiara gli articoli e gli ausiliari del ferrarese —
resta aperta ed è il punto 6 di `AGENTS.md`.

**Correzione dello stesso giorno, sulla stessa frase.** Cercando in tutto il
repository le altre dichiarazioni che reggevano su quella frase, ne sono
trovate altre due, entrambe in `raccolta/costruisci_meccanico.py`: il commento
sopra l'elenco delle parole funzionali scartate, e la riga `# ausiliari e
verbi che il motore tratta come regole` dentro l'elenco stesso. Il motivo per
cui il generatore scarta gli articoli non e' che il motore li sappia — non li
sa — ma una **scelta**, con due motivi buoni e un costo.

Lo scarto è stato misurato per capire quanto costa: di 118 righe scartate, 98
hanno il capoverso `Per`, che nel Ferri è il marchio del rinvio per traslazione
e non la preposizione (sono sottentrate come «— Per dim - Laghetto», senza
capoverso proprio: scartarle è giusto). Le altre 20 sono forme funzionali che
**il Ferri dichiara** e che il progetto buttava via: `Sòra` (sopra, pag. 386),
`Fora` (fuori, pag. 150), `Còl` (col e collo, pag. 92), `Fra` (frate e fra/tra,
pag. 151), `Con` (pag. 94), `In` (pag. 187), `Tra` (pag. 439), `La` (pag. 213),
`Se` (pag. 364), `Che` (pag. 87), `Un` (pag. 450).

Quindi la domanda che avevo scritto al punto 6 di `AGENTS.md` — «quale fonte
dichiara gli articoli?» — era sbagliata: la fonte c'è già, ed è la più forte
del progetto. La domanda è di **policy**: si tiene la scelta e si vive con il
buco, oppure si ammette un elenco separato di forme funzionali sapendo che il
motore non le tratta. Finché la risposta non c'è, niente si aggiunge a mano.

Una guardia tiene i tre file che ripetevano la frase, perché la frase era vera
sulla carta e falsa nel codice, e un commento in un test viene letto come se
fosse vero.

**Verifiche.** 137 test (erano 136). `verifica`: 0 errori, 8 avvisi. Nessuna
voce del glossario è cambiata: questa versione non tocca i dati, cambia quello
che il progetto **dichiara** su di sé.

## 0.14 — 2026-10-04 · Le parole che non si usano più, spiegate dalla fonte che le spiega

**Perché.** Una voce come «ardiglione» arriva a uno studente con un italiano
che non scrive più, e il trattino che c'era in colonna non spiegava niente.
Il glossario ha 10387 parole del 1889 e nessuna dice che cosa vogliono dire
oggi. Il 0.14 aggiunge la colonna, e la cosa interessante non è la colonna:
è **da dove viene** e che cosa non si può chiedere alla sua fonte.

**La fonte.** Wiktionary in italiano, che dichiara la licenza CC BY-SA 4.0 e
la pubblica in machine-readable: la licenza non l'ho cercata su un sito di
terzi, l'ho chiesta alla fonte stessa con `meta=siteinfo&siprop=rightsinfo`.
Diventa S017, e ogni riga del glossario che riceve un significato porta in
`fonte_moderno` **l'indirizzo della pagina da cui viene**, non il codice della
fonte: qui la fonte è una pagina e non un libro, quindi il codice non
basterebbe a controllarla.

**Il buco dichiarato.** 4063 voci su 10387 hanno il significato
moderno, 3235 hanno anche i sinonimi, e le altre sono un buco
dichiarato con quattro motivi distinti: la fonte non ha l'articolo, dichiara di
non averne la definizione, l'articolo non ha una sezione italiana, la sezione
italiana non ha definizioni. Questi quattro non sono la stessa cosa, e
somparli avrebbe reso la raccolta più bella e meno vera.

**Quello che non si sa, detto chiaramente.** Nessun template di Wiktionary
dichiara che una parola è arcaica. Quindi **non si può chiedere alla fonte
«questa parola è antica?»**, e il modulo non prova a indovinarlo con la
grafia: nessun segno ortografico distingue «ardiglione», che è arcaico, da
«cane», che non lo è. La colonna non finge di separare le parole antiche,
spiega tutte quelle che la fonte spiega, e i 6324 che restano non sono
una misura di quanto è antico il glossario. È il punto 5 delle domande aperte
in `AGENTS.md`.

**Il taglio, e perché si dichiara.** In colonna si vedono tre definizioni e
tre sinonimi; nel file ci sono tutti. La prima stesura scriveva tutto e il
significato più lungo arrivava a 1970 caratteri: una colonna che nessuno legge
fa sembrare vuota la colonna delle altre. Ma il taglio si dichiara, perché una
colonna che mostra tre pezzi senza dire che sono tre sembra mostrarne tre di
dieci che ci sono.

**I cinque difetti reali trovati strada facendo**, ognuno coperto da un test,
perché ognuno è stato un giorno di raccolta buttata:

1. `{{Nodef|it}}` è **per definizione**, non per articolo: la prima stesura
   scartava l'articolo intero e perdeva «fungo», «arcangelo», «sorriso» e
   «falda». Ora si toglie dalla riga e si legge il resto.
2. Le definizioni non sono sempre `# ` (spazio): esistono `#provocare …` e
   `#{{Nodef|it}}`. Ora si accetta `#` e si esclude `#*`, che è un esempio
   d'uso.
3. La sezione cercava solo le intestazioni di **secondo** livello: su una
   pagina che annida, l'inglese entrava nella sezione italiana e finiva in
   colonna accanto all'italiano. Ora si cerca qualsiasi livello.
4. Le **tabelle di coniugazione** non sono il significato: in «calunnia»
   finivano in colonna cinque righe come «terza persona singolare
   dell'indicativo presente di calunniare». Si scartano le righe che descrivono
   una *forma* del verbo, non la sezione che le contiene — perché la sezione
   di significato («botanica», «medicina») contiene invece definizioni vere,
   ed è stato proprio un test a farlo vedere.
5. it.wiktionary scrive i titoli in **minuscolo**: mandare «Giustizia» fa
   rispondere che l'articolo non esiste. Da sola, questa cosa faceva fallire
   l'87% delle parole.

**La lezione sulla cache.** Il parser è stato sbagliato tre volte, e ogni
volta la correzione costava un'ora di rete, perché la cache teneva il
**risultato** e non il testo. Ora la cache tiene il **wikitext grezzo** e la
lettura avviene all'ultimo momento: la prossima correzione del parser non
costerà niente. E la cache porta un numero di versione, perché una cache che
non sa con quale regola è stata fatta è un posto dove si perdono i dati.

**La raccolta, senza rete a runtime.** Il progetto non usa la rete quando
funziona: `raccolta/moderni.py --daemon` è l'unico punto che chiede qualcosa,
e lo fa una volta, in locale, con i lotti da 50 e una pausa fra lotti. Il
processo si sgancia dal terminale con un doppio fork, altrimenti un lavoro di
un'ora viene ucciso dalla shell che lo ha lanciato.

**Verifiche.** 136 test (erano 115). `verifica`: 0 errori, 8 avvisi.
Equivalenza Python/JavaScript: 12 frasi, 0 divergenze. Nessuna risorsa esterna,
nessun carattere fuori dal latino.

## 0.13 — 2026-10-03 · Il motore che leggeva male due lettere, e come l'ho scoperto

**Perché.** Il 0.12 ha aperto la fonte delle trascrizioni. In un repository
fratello, costruendo il cammino **inverso** — dal suono alla grafia, che serve a
un ipotetico sistema che ascolta il ferrarese — ho dovuto fare una misura che
qui non esisteva: 28 parole fanno il viaggio di andata e ritorno, e si conta
quante sopravvivono. Quella misura ha trovato due difetti di questo motore.

**Il primo.** In Python la stringa vuota è sottostringa di qualunque stringa,
quindi `"" in "eie"` è **vero**. La regola 4 chiedeva se la vocale che segue `c`
o `g` fosse anteriore, senza chiedersi che vocale ci fosse: a fine parola non
ce n'è nessuna, e il controllo passava. Ogni `c` e `g` **finale di parola**
diventava affricata. `nag` leggeva `/nadʒ/`, `mang` `/mandʒ/`, `nac` `/natʃ/`:
parole che si cercano ogni giorno, e la voce le diceva sbagliate senza
dichiararlo. Corretto con una guardia esplicita.

**Il secondo.** Le vocali anteriori erano l'elenco di caratteri `"eiéèi"`, e
**mancavano `ì` e `í`**. Quindi `gì` leggeva `/g/` invece di `/dʒ/`, e `cì` `/k/`
invece di `/tʃ/`. Una regola che funziona per tre casi su quattro sembra
funzionare: è il motivo per cui la lista è adesso un insieme con nome,
`ANTERIORI`, e non una stringa scritta a occhio.

**La lezione, che vale più dei due difetti.** La domanda giusta non è «il
codice sembra giusto» ma «un'altra strada per arrivarci dà la stessa
risposta?». Il viaggio di ritorno **è** quell'altra strada, ed è la prima volta
che il motore viene verificato da qualcosa che non è lui stesso. Un modulo che
si controlla da solo non può trovare i propri errori di fondo, perché li ha
scritti con la stessa convinzione con cui li ha sbagliati.

Entrambi coperti da test. Il numero di test sale a 115, e i due casi che
scoprivano sono entrambi nomi di parola che oggi si cercano e si traducono
bene.

**Verifiche.** 115 test (erano 113). `verifica`: 0 errori, 8 avvisi. Equivalenza
Python/JavaScript: 12 frasi, 0 divergenze. Nessuna risorsa esterna, nessun
carattere fuori dal latino.

## 0.12 — 2026-10-03 · La fonte che doveva decidere sull'accento non era mai stata aperta

**Perché.** La 0.11 aveva lasciato aperta una domanda: l'accento di Biondelli.
Per chiudere bisognava leggere la fonte, e la fonte era già dichiarata come
**S001, stato `acquisita`, pubblico dominio**. Non era mai stata aperta.

**Il difetto.** L'URL registrato — `saggouisuidialetti00bion` — **rispondeva
404**. Quindici giorni di registro hanno indicato una fonte che non esiste, e
il testo non era mai stato scaricato, benché undici voci del glossario e
ventotto trascrizioni citassero quella pagina. L'identificatore giusto è
`saggiosuidialet00biongoog`. Una fonte che si dichiara `acquisita` ma che non
è mai stata aperta è la forma peggiore di fonte citata: sembra verificata e non
è stata guardata. Ora il testo c'è, in `raccolta/grezzi/biondelli_1853.txt`.

**La diagnosi della 0.11 era sbagliata, e va detto.** Avevo scritto che «Biondelli
segnava l'accento sulla vocale finale non tonica e ritirava la tonica sulla
penultima», e che 20 trascrizioni su 28 non coincidevano con le regole per
quella ragione. Ho letto la pagina 205 e non è vero. Biondelli scrive
`magnar`, `portar`, `ama`, `vola`, `manca`, e l'accento cade sull'ultima
sillaba come in qualsiasi italiano: le due fonti **sull'accento concordano**.

Il numero vero è **4 su 28**, non 20. E la causa non era una seconda
convenzione: era il mio confronto che contava come differenza di suono una
differenza di **sillabificazione**. `porˈtar` e `portˈar` hanno gli stessi
suoni e lo stesso accento; cambia solo dove finisce la sillaba. Ventiquattro
righe su ventotto coincidono, accento compreso.

**Il difetto vero del confronto.** Un controllo che grida per una scelta di
sillabificazione smette di essere letto, e un controllo che grida per niente fa
dubitare delle regole serie. Il numero non va fatto più grande per sembrare
prudente: va spiegato. Ora F14 confronta la sequenza dei simboli senza il
segno di accento e senza confini di sillaba, e i test prendono il ritorno
entrambe le cose — una sillaba spostata non deve più comparire fra le
discordanti.

**Che cosa dichiara la fonte, e che cosa il sistema non applica.** La pagina 205
dice cose che le regole 1-6 non descrivono, e adesso sono scritte in testa al
file con la pagina, perché la prossima persona non le perda:

- nessuno schwa e nessun dittongo — la regola 1 lo diceva, adesso ha la pagina;
- la vocale finale atonica dell'infinito diventa una `a` **aperta**:
  `leggere` = `lézar`, `godere` = `gòdar`, `mentre` = `méntar`;
- `-a` e `-io` finali diventano `-ie`: `compagnia` = `cumpagniè`, `mio` = `mie`;
- **la `z` aspra italiana si rende /s/**: `cittadino` = `sittadin`,
  `principiare` = `principièr`. Questa è la risposta alla regola 6, almeno per
  questo caso, e spiega `rasón`.

Non sono state applicate. Applicarle cambierebbe quattro righe senza che
nessuno sappia quale delle due fonti abbia ragione, e la regola della `z` vale
per l'italiano `z` aspra, non per ogni `s` intervocalica: estenderla da un
esempio sarebbe il peggior genere di generalizzazione.

**Che cosa resta aperto, con il numero giusto.** Le quattro righe — `magnàr`,
`desideràr`, `principiar`, `rasón` — hanno tutte la stessa natura: la fonte ha
forme con la vocale finale ridotta, e le regole dichiarate non la descrivono.
È un sistema dichiarato **incompleto rispetto alla fonte che l'ha prodotto**,
non due sistemi in contraddizione. F14 conta quattro e non corregge: scegliere
significherebbe decidere quale delle due fonti vale.

**Verifiche.** 113 test (erano 109). `verifica`: 0 errori, 8 avvisi. Equivalenza
Python/JavaScript: 12 frasi, 0 divergenze. Nessuna risorsa esterna, nessun
carattere fuori dal latino.

## 0.11 — 2026-10-03 · Una voce che sa dire la grafia e non finge di sapere il parlato

**Perché.** Il gioco ha bisogno di far ascoltare, e il progetto non aveva
nessuno strumento per passare dalla grafia al suono. Il file
`dati/fonetica.jsonl` dichiarava un sistema di regole di lettura e nessuno lo
applicava: le regole erano scritte per essere controllate a mano, e la prima
misura che le ha usate davvero ha trovato tre difetti.

**Cosa c'è.** Il modulo `legge` applica le regole dichiarate e, dove nessuna
fonte dichiara niente, **si ferma e lo dichiara**; il modulo `voce` le passa
nell'alfabeto di `espeak-ng` e produce un wav in locale. Il comando
`voce magnàr --suona` scrive il suono. Nessuna rete, nessuna dipendenza nel
pacchetto: se `espeak-ng` non è installato il comando **dice che manca** e non
inventa un suono.

**I tre difetti trovati misurando, non ragionando.**

1. *La `g` e la `c` velari mancavano.* La regola 4 copriva solo il caso
   palatale (`gh'è` → /dʒ/), e ogni `g` o `c` finale cadeva nell'«ignota»:
   `magnàr` diventava `/ma/`, un terzo della parola, senza avviso.
2. *L'apostrofo troncava.* `gh'è` finiva a `/g/`, `n'è` a `/n/`, `n'agh` a
   `/n/`. Le elisioni sono frequenti in ferrarese, e il modulo si fermava
   sull'apostrofo come se fosse una lettera ignota.
3. *Il segno di accento non entrava nella IPA.* Era costruito, contato,
   dichiarato nel campo `accento` — e poi scartato: la stringa finale era senza
   `ˈ`. Una IPA senza accento non dice quale sillaba è tonica.

**Una cosa che ho deciso con la prova, non con l'opinione.** Il modulo scriveva
`è` → /e/, e il file lo scrive /ɛ/ in quattro righe contro due (`ghe` = /ge/,
`ved` = /ved/). Se la marcatura accentata cambiasse la vocale, /e/ e /ɛ/ non
sarebbero due suoni distinti e la regola 1 perderebbe il senso. Quindi la `e`
accentata è aperta e quella senza accento è chiusa, che è l'opposto di come si
scrive di solito, ed è per questo che il criterio è dichiarato a carattere.

**Il difetto che resta aperto e dichiarato: l'accento.** 20 delle 28
trascrizioni non coincidono con le regole dichiarate. Non è un difetto del
programma: le righe citano Biondelli 1853, che ha un sistema suo — l'accento
sulla vocale finale **non** tonica con la tonica ritirata sulla penultima
(`/maˈɲnar/`), la vocale finale atonica ridotta (`principiar` = /-jar/) e il
/ɲ/ anche davanti a vocale non anteriore. Non si possono fondere le due cose
senza attribuire a Biondelli un sistema che non è il suo, quindi il controllo
**F14** misura la distanza e la dichiara senza correggere. È un avviso che
resta finché la questione non è chiusa.

> **Corretto dalla 0.12.** La diagnosi qui sopra è **sbagliata**, e la 0.12
> dice perché. Biondelli non ha una convenzione diversa sull'accento: il suo
> testo a pagina 205 lo mette sull'ultima sillaba come tutti, e le due fonti
> concordano. Il numero vero è 4 su 28, non 20, e la causa non era l'accento ma
> un confronto che contava come suono diverso una differenza di
> sillabificazione. Il fatto che F14 restasse un avviso anche quando il numero
> era sbagliato è la parte utile: un avviso che non sparisce quando dovrebbe
> sparisce fa notare che qualcosa non torna, ed è così che si è arrivati alla
> fonte.

**La cosa che la voce non è.** Non è un parlante ferrarese, e il wav non
verifica niente: le righe restano `attendibilita: "I"` e `da_verificare: true`.
Il suono esce in `raccolta/lavorato/voci/`, che non è tracciata, e **non** in
`web/audio/`, perché copiare lì significa pubblicare e la regola A1-A10 vuole
consenso, licenza e `pubblicabile` — e qui nessuna persona ha parlato.

**Il punto in cui `espeak-ng` è più pericoloso di quanto sembri.** Accetta
fonemi in ingresso, ma con il *proprio* alfabeto: `tʃ` e `ɲ` non esistono, e
non danno errore — **tagliano la parola** e producono un wav che sembra
parlato e sta zoppicando. Per questo la traduzione non prova e basta: ogni
simbolo che non sa tradurre ferma la generazione e lo dichiara. È un test.

## 0.10 — 2026-10-03 · Le parole trovate online esistono davvero in un file

**Perché.** La 0.9 aveva scritto che cinque parole trovate online «vanno in
attesa, nessuna entra nel glossario attivo» — e non le aveva messe in
attesa. Le parole erano **sparite fra la lista e i dati**: `lacune.md` diceva
«trovata» e nessun file del repository le conteneva. Il progetto aveva
imparato a misurare le proprie lacune e proprio li' aveva scritto una frase
che nessuno aveva controllato. È la versione che chiude quel buco.

- **V10400-V10404** sono in `dati/da_verificare/glossario.jsonl`, con la fonte
  dichiarata e `attendibilita D`: `Furzina` = forchetta (S014), `Guciara` =
  cucchiaio (S014), `Piron` = coltello (S014), `Capunàra` = testa (S013),
  `Barsacca` = borsa (S013). Sono le parole del quotidiano che il vocabolario
  del 1889 non ha e che un gioco usa subito. Il controllo **D1** le tiene
  fuori dai dati attivi: escono quando la fonte si chiarisce, non prima;
- `lacune.md` ora porta l'id accanto a ogni parola «trovata», cosi' il
  documento e i dati si controllano a vicenda;
- l'intestazione di `da_verificare/glossario.jsonl` diceva ancora solo di
  V0023/V0024: il file documentava una cosa diversa da quello che conteneva.
  Aggiornata;
- **`TestAtteseOnline`** collega il documento ai dati: ogni parola che
  `lacune.md` chiama «trovata» deve esistere o nel glossario attivo o fra
  quelle in attesa. Se un giorno sparisce di nuovo, il test lo dice e dice
  quale. E controlla che ogni riga in attesa dichiari da dove viene, e che
  nessuna sia anche nei dati attivi.

**Il difetto è il tipo che questo progetto ha il dovere di trovare.** Una riga
in attesa che non riporta la fonte non dice a nessuno cosa aspettare, e una
lista che promette una riga che nessun file ha fa credere che il lavoro sia
fatto. Non è un errore che rompesse qualcosa: è un errore che faceva
credere. Sono i peggiori.

**Cosa ha tirato fuori il test sui file di dati.** Scrivendo il primo ho
controllato, per abitudine, che ogni `.jsonl` finisca con un a capo — e **cinque
non lo facevano**: `da_verificare/glossario`, `da_verificare/coppie`,
`da_verificare/fonetica`, `audio`, `fonetica` e `proposte/proposte`. Non è un
dettaglio: appendere a un file che non finisce con l'a capo attacca la nuova
riga alla precedente e il file diventa **una riga sola lunghissima**. Nessun
controllo di sintassi lo dice, perché `json.loads` su una riga sola è
valido. `TestFileDati` guarda l'ultimo carattere di ogni file di dati, e
l'ho verificato togliendo un a capo di proposito: il test lo prende e dice
quale file.

**Verifiche.** 92 test (erano 88). `verifica`: 0 errori, **7 avvisi** (erano 2:
le cinque nuove voci in attesa sono un avviso D2 ciascuna, ed è il
comportamento giusto — finche' l'avviso c'è, nessuno deve crederle
documentate). Equivalenza Python/JavaScript: 12 frasi, 0 divergenze.

## 0.9 — 2026-10-03 · Misurare quanto italiano copre il glossario, e dire quali parole mancano

**Perché.** Il glossario era passato a 10387 voci e sembrava, per il numero,
un vocabolario. Non lo era: era un vocabolario **di una stanza sola**. Nessuno
poteva dirlo, perché il numero delle voci non dice quanto italiano copre, e il
progetto non aveva nessuno strumento che lo dicesse. Il primo tentativo di
misurarlo ha prodotto un numero **falso**, ed è la parte instructive di questa
versione.

- **`copertura.py` confronta il glossario con i lemmi dell'ItWaC** (Baroni,
  Bernardini, Ferraresi, Zanchetta 2009, via `franfranz/Word_Frequency_Lists_ITA`,
  licenza MIT): **23,7% dei lemmi italiani frequenti sono coperti**, 8197 da
  cercare. Il comando è `traduttore.cli copertura`, anche lui con `--json`;
- **la prima versione dava 10,8% e il numero era falso.** Usava una lista di
  frequenza ricavata dai *sottititoli*, e le parole più frequenti «mancanti»
  erano `sono`, `ho`, `stato`, `mangi`. Il glossario non le contiene perché
  contiene `essere`, `avere`, `stato`, `mangiare`: un vocabolario è fatto di
  **lemmi**, e confrontare un lemma con una coniugazione è come concludere che
  manca «cane» perché nella lista c'era «cani». Il metro è passato agli elenchi
  **già lemmatizzati**, dove la riga `"anni"` porta il lemma `anno`;
- `TestCopertura` blocca il metro al suo posto: se la copertura scende sotto il
  20% il test fallisce, perché a quel punto o il metro è rotto o il glossario
  ha perso voci. E c'è il test sulla **codifica**: i CSV dell'ItWaC sono in
  **latin-1**, non UTF-8, e leggerli in UTF-8 fa cadere lo script a metà elenco
  su una riga che sembra normale (`attività` = due byte `0xe0`);
- **`dati/da_verificare/lacune.md`** è la lista documentata delle parole
  importanti che mancano, divisa per corpo, casa, cucina, abbigliamento,
  oggetti e scuola, con per ogni riga lo stato: trovata online, non trovata, o
  **già nel glossario**. Non è un calcolo: è un documento, perché il calcolo
  dice *quante* mancano e il documento dice *quali* e *perché quelle contano*;
- **ricerca online**. Le attestazioni trovate sono poche e tutte con fonti
  senza licenza verificabile, quindi **nessuna entra nel glossario attivo** e
  vanno in attesa (regola D1, come per S003): `furzina` = forchetta,
  `guciara` = cucchiaio, `piron` = coltello (listone.it, 2014);
  `capunàra` = testa, `barsacca` = borsa (dizionariopopolare.blogspot.com,
  2011). La `scarana` = sedia era già dentro (V7636) e la ricerca online l'ha
  **confermata**: robertobigoni.it scrive testualmente «la sedia per i Ferraresi
  è la skaràna». Quattro fonti nuove in `fonti.json`: **S013** (il dizionario
  del blog), **S014** (l'articolo con i commenti), **S015** (le note linguistiche
  di Bigoni), tutte con licenza non verificata;
- **S016** è la fonte che chiuderebbe metà della lista: il *Vocabolario
  Italiano-Ferrarese* (Vincenzi, Ridolfi, Guidetti, 2007) e il *Vocabolario
  Ferrarese-Italiano* dell'**AR.PA.DIA.**, l'archivio del Comune di Ferrara.
  È un'istituzione pubblica: la fonte con la provenienza più chiara di tutte
  quelle che il progetto conosce. Non è copiabile e non si copia, ma si
  **consulta in biblioteca** e le voci che se ne ricavano entrano con la fonte
  dichiarata. Copre il lessico contemporaneo — `televisione`, `telefono`,
  `chiave` — che il Ferri del 1889 non può avere.

**Perché la copertura è bassa e non è un difetto del vocabolario.** Il Ferri
(1889) è un libro di casa e di bottega: pane, mestiere, arredi, animali, modi
di dire. Non copre `anno`, `numero`, `risposta`, `televisione`, e non
potrebbe: sono le parole che nel 1889 o non esistevano o non si scrivevano
così. Coprirle non è attingere al vocabolario del Ferri, è un altro lavoro, e
la metà delle frequenze alte è anche la meno urgente: `decreto` e `regionale`
non sono le parole di cui si accorge chi sta giocando.

**Verifiche.** 88 test (erano 83). `verifica`: 0 errori, 2 avvisi D2.
Equivalenza Python/JavaScript: 12 frasi, 0 divergenze. Nessuna risorsa esterna,
nessun carattere fuori dal latino.

## 0.8 — 2026-10-03 · Una voce con piu' resi si trova da ciascuno dei suoi resi

**Perché.** La 0.7 aveva portato dentro 10000 voci e aveva dichiarato il
difetto che ne era venuto fuori, senza correggerlo: il glossario indicizzava
il lato italiano sull'intero campo `italiano`. «Maladir → Maledire,
esacràre» era una voce che il libro scrive e che il motore non trovava
cercando «maledire». Erano **1663 voci su 10387**. Il sintomo e' quello che
si vede subito e che sembra assurdo: la parola c'e', la risposta c'e', e
chi scrive «maledire» riceve «nessuna voce». Un vuoto cosi' non e' un vuoto:
e' una voce presente ma irraggiungibile, che e' la specie peggiore, perche'
si presenta come informazione.

- **`Voce._chiavi_resi()`** indicizza ogni resi separato da virgola o punto e
  virgola, piu' `principale_italiano` quando c'e'. Le **1663 voci irraggiungibili
  sono 0**;
- si divide su virgola e punto e virgola, **non sugli spazi**. «con calma»
  deve trovarsi cercando «con calma» e **non** cercando «calma», che e'
  un'altra voce (V0025) e che perderebbe il contesto in cui il libro la
  scrive. E' un test (`test_un_pezzo_non_e_una_parola_del_glossario`);
- **il testo intero resta una chiave**: chi incolla dal libro la voce per come
  e' scritta deve trovarla. La prima stesura della correzione aveva sostituito
  la chiave intera con i pezzi, e il test
  `test_il_reso_intero_resta_raggiungibile` l'ha fatto vedere: si perdeva la
  voce proprio dove si cercava di ritrovarla. Difetto della correzione,
  corretto prima di metterla dentro;
- la stessa logica e' scritta in `modello.html` (`chiaviResi`), nella stessa
  versione, e `prove/controlla_equivalenza.py` continua a dare 0 divergenze
  sulle dodici frasi. Il primo giro del confronto ne aveva trovata una — la
  pagina era rigenerata con il vecchio script — ed e' il motivo per cui la
  rigenerazione va fatta **prima** del confronto, non dopo.

**Verifiche.** 83 test (erano 77). `verifica`: 0 errori, 2 avvisi D2. Equivalenza
Python/JavaScript: 12 frasi, 0 divergenze. Sul campione di 26 traduzioni,
0 risposte cambiate: la correzione rende raggiungibile quello che prima non lo
era, senza spostare quello che gia' rispondeva.

## 0.6 — 2026-10-03 · I buchi prendono un numero

**Perché.** Il progetto sapeva cosa non sapeva, ma lo sapeva a parole: «non
abbiamo le trascrizioni IPA», «la forma popolare dei proverbi non e' ancora
documentata». Sono frasi vere e utili, ma non si possono correggere: nessuno
lavorava una frase che non ha un numero dentro. Il giorno in cui qualcuno
aggiunge una riga, la frase non cambia e il lavoro sembra non essere stato
riconosciuto. Un buco senza numero è un'oblazione, e un'oblazione non si
riduce da sola.

- nasce **`verifica_dati.buchi_dichiarati()`**: non un controllo e non un
  errore, una funzione che conta quello che manca e **scrive perché**
  manca. Ogni riga porta `nome`, `quanti`, `totale` (quando ha senso) e `nota`;
  una riga senza nota non dice niente e sta peggio che non esserci;
- nasce il **comando `buchi`** (con `--json`), che stampa quei numeri dal
  terminale e non fallisce mai: qui non c'è niente da correggere, c'è solo
  da sapere. I cinque numeri di adesso sono 206 locuzioni, 210 voci su 234
  senza IPA, 28 trascrizioni su 28 non verificate da un parlante, 28 proverbi
  su 28 senza forma `popolare`, 3 voci su 234 dichiarate da verificare;
- la **pagina** ha la sezione «E che cosa non sa», subito sotto il pannello,
  con gli stessi numeri e le stesse note. I numeri non sono ricalcolati in
  JavaScript: arrivano da `buchi_dichiarati()` insieme al resto dei dati, perché
  un numero calcolato in due posti è un numero che dopo un mese non è più vero
  per nessuno;
- **due numeri scritti a mano erano sbagliati** e il comando li ha smascherati:
  le locuzioni erano 206 e non 210 (il conto guarda il lato ferrarese, che è
  quello che il motore accorpa), e in fila d'attesa ci sono due voci e due
  frasi, non quattro voci. Il `README` li corregge. Il numero dei proverbi
  coincideva già, ed è l'unico modo che si aggiorni da solo.

**Difetto trovato e corretto scrivendo i test.** Il conto delle coppie senza
fonte guardava `Coppia.valida()`, che controlla anche i due lati, mentre il
controllo **C4** guarda solo la fonte: i due numeri potevano divergere senza
che nessuno se ne accorgesse. Ora la funzione conta come C4, e un test
(`test_le_coppie_senza_fonte_sono_quelle_che_il_controllo_C4_conta`) mette le
due cose nello stesso test, così se un giorno divergono fallisce.

**Cosa è rimasto fuori, dichiarato.** `buchi` non corregge niente e non lo
promette: chiude il conto, non il buco. Le 210 voci senza IPA e i 28 proverbi
senza `popolare` aspettano una persona, non una funzione.

## 0.5 — 2026-10-03 · Le locuzioni diventano usabili, e si controlla che la pagina dica come il motore

**Perché.** La versione 0.4 aveva portato dentro 210 locuzioni e aveva
dichiarato il buco che ne nasceva: `cerca` le trovava, `traduci` no. Un
glossario che non si puo' usare e' un elenco, e un elenco e' una promessa non
mantenuta. E mentre si chiudeva quel buco, un controllo nuovo ha trovato che
le due copie della logica non dicevano la stessa cosa da prima.

- il motore **accorpa le locuzioni** prima di tradurre parola per parola, in
  modo avido — dalla frase piu' lunga a piu' parole, fino a due — nelle due
  direzioni (`motore.py`, `_accorpa`). «a braccia aperte» adesso diventa
  `a brazz avèrti` invece di tre buchi, ed e' la stessa cosa che fa chi
  guarda la voce nel vocabolario;
- nasce **`prove/controlla_equivalenza.py`**: esegue la pagina con Node e
  confronta le risposte con quelle del motore Python, frase per frase, sulle
  stesse dodici frasi in entrambe le direzioni. Confronta le risposte e non
  il codice, perche' le due copie possono essere scritte diversamente e
  vanno bene finche' dicono la stessa cosa. Va nel workflow `Verifica`;
- **la regola che era scritta e non controllata ora e' un controllo.** Il
  primo giro del confronto ha trovato due difetti veri nella copia
  JavaScript: il tokenizzatore **spezzava l'apostrofo**, cosi' `pesce d'aprile`
  diventava due parole e la locuzione non combaciava piu'; e il livello 2 del
  corpus **confrontava un lato con se stesso**, cosi' una parola italiana che
  somigliava a una parola italiana di una coppia rispondeva «dal corpus»
  senza che il corpus avesse detto niente. Entrambi corretti nella pagina e
  verificati dal confronto;
- **`cerca` trova anche i proverbi**, e stampa la forma dei libri, quella che
  si dice e il significato insieme al fonte. Il confronto e' a finestre di
  parole, non sul testo intero: nessuno cerca «non tutte le ciambelle» e si
  aspetta la traduzione ferrarese di un proverbio italiano di quindici
  parole. Fino a ieri i 28 proverbi erano un file che nessuno poteva aprire;
- la pagina ha una **tabella dei proverbi** con ricerca, e accanto la colonna
  `popolare` che riporta la scritta «non ancora documentata» per tutti e
  ventotto. Il vuoto e' dichiarato anche in pagina, non solo nel file;
- i documenti sono allineati: `LICENZE.md` riportava Ferri 1885 e Nannini
  senza anno, `RACCOLTA.md` citava un id che non esiste.

**Cosa è rimasto fuori, dichiarato.** L'accorpamento guarda il lato da cui si
parte: se il glossato italiano di una voce e' una parola sola, quella voce si
trova dalla parte ferrarese e non dall'italiana. Non e' un difetto da
correggere: e' quello che c'e' nel vocabolario. Nessuna delle 234 voci ha una
trascrizione **verificata** da un parlante, e 210 non hanno neanche una
trascrizione; nessuno dei 28 proverbi ha la forma `popolare`. (Il numero delle
voci senza IPA e' entrato nel comando `buchi` nella 0.6: prima qui era
scritto 210 accanto a «nessuna delle 210», che era tautologico.)

## 0.4 — 2026-10-03 · Il vocabolario del 1889 entra, e con lui le locuzioni

**Perché.** Il glossario aveva ventiquattro parole, tutte singole e tutte da
due fonti, e la parte più ricca del ferrarese scritto — le locuzioni, i modi di
dire, i proverbi — era tutta fuori. Erano già segnalate come la voce piu'
preziosa dell'elenco e non erano state affrontate: si sapeva che il libro di
Ferri era testo-immagine e quindi da digitare. Era una diagnosi sbagliata.

- **S004 (Ferri 1889) passa da `esaminata` ad `acquisita`** con la licenza
  verificata. Il libro non e' testo-immagine: archive.org ne pubblica
  l'OCR, ed e' leggibile. L'autore e' **Luigi Ferri (1826-1895)**, non «Luigi
  Ferri, 1885» come diceva la scheda: il titolo porta l'anno giusto e la
  prefazione e' firmata. Il nome «Enrico Ferri» che si legge sul
  frontespizio e' una lettura sbagliata dell'OCR, e il progetto adesso lo
  dice perche' qualcuno lo rileggera' e si chiedera';
- nascono **210 voci** (V0027-V0236), di cui la meta' sono locuzioni e
  modi di dire, piu' 8 coppie (F0011-F0018) e **28 proverbi** (P0001-P00028),
  che fino a ieri erano un file commentato e vuoto. I proverbi hanno
  `letterario` e `popolare` separati come sempre, e `popolare` vuoto: nessuno
  ci ha detto come si dicono, e un campo vuoto dichiarato vale piu' di una
  forma inventata solo per simmetria;
- ogni voce porta il **numero di pagina** ricostruito dagli originali a
  stampa. Il numero puo' essere sbagliato di una pagina, perche' viene
  dall'OCR: e' dichiarato in `dati/fonti.json` invece di essere nascosto;
- nasce `raccolta/`: `pdf_testo.py` (l'estrattore di PDF senza librerie
  esterne), `estrai_ferri.py`, `filtra_candidati.py`, `lettura_ferri.py`
  (la lista scelta a mano) e `costruisci_da_ferri.py` (la porta dentro
  `dati/`). I grezzi e il mezzo non sono tracciati: sono quasi 35 megabyte
  ricreabili con una riga, e un repository che si trascina dietro i libri
  interi non dice niente di piu';
- **S010** (il vocabolario domestico del blog) entra come `esaminata`: la
  prima pagina dichiara pubblico dominio, ma la dichiarazione e' della copia
  digitale e non dell'autore, quindi la licenza resta non verificata. Il suo
  testo si e' aperto e **non e' utilizzabile**: l'estrattore minimo legge i
  flussi ma il file non conserva le coordinate dei glifi, quindi le parole
  vengono fuori incollate. E' il piu' grande dei quattro e il primo da
  recuperare;
- **S011** (l'opuscolo di Aruba) entra come `esclusa`, con due motivi scritti:
  il file non contiene testo e' una stampa di schermata, e di chi sia
  l'opuscolo non si sa. Il testo e' di quelli che si trovano copie lontane
  dall'originale, ed e' esattamente il caso in cui una fonte senza
  provenienza non entra.

**Cosa è rimasto fuori, dichiarato.** Le 210 voci sono nella grafia del 1889,
non in quella di oggi, e non sono state verificate da un parlante: sono
verificabili aprendo il libro alla pagina indicata, e solo cosi'. Nessuna
delle 210 ha una trascrizione IPA, quindi i vuoti di `dati/fonetica.jsonl`
sono passati da 28 a 238 e la pagina continua a dirlo. E il motore non sa
ancora usare le locuzioni in una frase: `cerca` le trova, `traduci` no.

## 0.3 — 2026-10-03 · Le varietà, il suono, e quello che era solo dichiarato

**Perché.** Il ferrarese non è una lingua sola, e il progetto non poteva
continuare a trattarlo come se lo fosse: senza sapere in quale varietà è una
parola, una voce di Bondeno finisce sulla bocca di uno studente di Ferrara città
senza che nessuno se ne accorga. E la parte del suono era incominciata a metà:
c'era il manifesto dei brani ma non c'era la traccia di pronuncia.

- `varieta` diventa **obbligatoria** in voci e coppie (controlli G8, G9, C7, C8)
  e nasce `dati/varieta.json`, con i cinque codici, i territori e la fonte
  dichiarata (Wikipedia, CC BY-SA 4.0);
- i territori che la fonte elenca in due gruppi — Fiscaglia, Ostellato,
  Occhiobello, Goro — restano **dichiarati come sovrapposti** invece di essere
  separati arbitrariamente;
- nasce `dati/fonetica.jsonl` con 28 trascrizioni IPA e il sistema dichiarato
  nell'intestazione; tutte `attendibilita: "I"` e `da_verificare: true`, perché
  sono una lettura della grafia e non un ascolto (controlli F1–F14);
- nasce il **riproduttore** nella pagina: IPA accanto alla parola, varietà
  dichiarata, e audio solo con consenso + licenza + `pubblicabile`;
- nasce `dati/audio.jsonl` e `audio/README.md`, con i tre controlli che
  rendono vero il divieto di pubblicare una voce senza consenso (A1–A10);
- i dati con **licenza non verificata** (traduzione della Dichiarazione
  universale, S003) passano in `dati/da_verificare/` e diventano inutilizzabili
  per errore grazie ai controlli D1 e D2;
- `dati/proposte/` smette di essere una promessa: il livello IA scrive davvero
  la sua coda di revisione, e i controlli M1–M4 vietano a una proposta di
  portarsi dentro un campo `fonte`.

**Cosa è rimasto fuori, dichiarato.** Quattro varietà su cinque sono vuote. Il
glossario copre la città e nient'altro, e `varieta` lo dice in ogni comando.

## 0.2 — 2026-10-03 · Il motore smette di rispondere con la frase intera

**Perché.** Il corpus rispondeva con l'intera coppia a ogni parola che le
assomigliava: data la coppia «non c'è pane» / «an ghè brisa pan», la parola
«non» riceveva l'intera frase, che è una traduzione della frase e non della
parola. In una frase lunga la stessa risposta compariva tre volte.

- `Corpus.frammento()` restituisce **il singolo pezzo** che combacia, e
  `None` se nessuno combacia a soglia;
- le regole morfologiche si imparano come **radice + desinenza** e non come
  prefisso + suffisso, perché `cantare` / `cantar` non ha suffissi uguali;
- una regola generalizzata viene **riapplicata ai suoi stessi esempi** e se
  sbaglia non viene salvata;
- la catena di risoluzione è dichiarata in una tabella, con la confidenza di
  ogni livello e la soglia sopra la quale il risultato è pubblicabile.

## 0.1 — 2026-10-03 · Il primo motore

**Perché.** Senza il traduttore i dati del gioco si raccolgono a mano e non si
controllano. Il progetto parte da quattro livelli e da una regola sola: quando
non sa, lo dichiara.

- glossario, corpus parallelo, morfologia appresa, livello IA facoltativo;
- i controlli sui dati che **non correggono**: segnalano, e la correzione la fa
  una persona;
- la pagina statica, che funziona da `file://` e non chiede nulla a nessuno.

## Cosa non finisce qui

Tre cose restano aperte e nessuna si chiude scrivendo codice. Sono in
`AGENTS.md` §6 e qui basta il nome:

1. **quante ore di registrazione servono** — la stima e la sua aritmetica
   sono in `STIMA-AUDIO.md`, ed è una stima, non una misura;
2. **chi approva** le proposte del livello IA e le trascrizioni IPA;
3. **le quattro varietà vuote**, che si riempiono parlando con le persone di
   quei posti.