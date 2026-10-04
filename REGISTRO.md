---
titolo: Registro delle modifiche
versione: 0.18
data: 2026-10-04
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
  glossario passa da 234 a **16739 voci** (2034 locuzioni, 8353 parole
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
16739** in questa situazione. Prima dell'import non si vedeva, perche' le 210
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

## 0.18 — 2026-10-04 · Le 6352 parole di Bigoni, e le due lettere che l'indice buttava via

Il pendente che restava dichiarato — portare le 7307 coppie di S006 nel
glossario attivo — e' chiuso. Il glossario passa da **10387 a 16739 voci**.
Ma la parte interessante di questa voce non e' il numero: e' che per
arrivarci sono usciti **cinque difetti veri**, e quattro di loro producevano
righe ben formate che nessun controllo poteva vedere.

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
`À-ɏ` — ma in JavaScript `\w` non comprende `ɣ` (U+0263), che pure
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

**Verifiche.** 202 test (erano 177). `verifica`: 0 errori, 8 avvisi.
Equivalenza: 12 frasi confrontate, 0 divergenze. Il glossario e' passato da
21 a 34 fette, il sito da 27 a 40 pagine. `note` non e' piu' trasportata dalla
pagina del traduttore: 2,4 MB invece di 3,9.


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
`fonte` insieme), e la forma compatta — non ripetere le stesse chiavi 16739
volte — il 23%. Insieme poco piu' della meta': toglievano un megabyte su sei, e
il grosso restava.

**I dati erano distribuiti, non grandi.** Le 16739 voci non erano un blocco
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
una frase falsa, perche' le voci sono 16739 e 16739 non e' nessuna. Ora dice
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
Il glossario ha 16739 parole del 1889 e nessuna dice che cosa vogliono dire
oggi. Il 0.14 aggiunge la colonna, e la cosa interessante non è la colonna:
è **da dove viene** e che cosa non si può chiedere alla sua fonte.

**La fonte.** Wiktionary in italiano, che dichiara la licenza CC BY-SA 4.0 e
la pubblica in machine-readable: la licenza non l'ho cercata su un sito di
terzi, l'ho chiesta alla fonte stessa con `meta=siteinfo&siprop=rightsinfo`.
Diventa S017, e ogni riga del glossario che riceve un significato porta in
`fonte_moderno` **l'indirizzo della pagina da cui viene**, non il codice della
fonte: qui la fonte è una pagina e non un libro, quindi il codice non
basterebbe a controllarla.

**Il buco dichiarato.** 4063 voci su 16739 hanno il significato
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
spiega tutte quelle che la fonte spiega, e i 12676 che restano non sono
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

**Perché.** Il glossario era passato a 16739 voci e sembrava, per il numero,
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
cercando «maledire». Erano **1663 voci su 16739**. Il sintomo e' quello che
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