---
titolo: Registro delle modifiche
versione: 0.10
data: 2026-10-03
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