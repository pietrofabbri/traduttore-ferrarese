---
titolo: Traduttore italiano-ferrarese
versione: 0.16
data: 2026-10-03
autore: progetto «I cinque duchi»
---

# Traduttore italiano &ndash; ferrarese

Un traduttore fra l'italiano e il **ferrarese**, costruito per il gioco
«I cinque duchi» e per chi vuole imparare la lingua di Ferrara.

La caratteristica di questo progetto non e' che traduce bene. E' che **quando
non sa, dice che non sa**, e dice anche *perche'* non lo sa e *che cosa
servirebbe* per saperlo. Con diecimilatrecentoottantasette voci in un glossario,
tutte di una sola varieta' e tutte da tre fonti, questa e' la proprieta' piu'
importante che ha.

## Come si usa

```bash
export PYTHONPATH=sorgenti

python3 -m traduttore.cli traduci "non c'è pane"
python3 -m traduttore.cli traduci "brisa" --direzione fe-it
python3 -m traduttore.cli cerca magnar
python3 -m traduttore.cli varieta
python3 -m traduttore.cli pronuncia magnar
python3 -m traduttore.cli voce magnàr
python3 -m traduttore.cli audio
python3 -m traduttore.cli proposte
python3 -m traduttore.cli stato
python3 -m traduttore.cli buchi
python3 -m traduttore.cli copertura
python3 -m traduttore.cli verifica
python3 -m traduttore.cli impara
python3 -m traduttore.cli web
```

E la pagina: `python3 -m traduttore.cli web` scrive `web/index.html`, che si
apre con un doppio clic e funziona **senza connessione**. Nessun account,
nessun server, nessuna richiesta di rete. Su GitHub la pubblica il workflow
`pagine.yml`.

`buchi` non e' un controllo e non fallisce mai: qui non c'e' niente da
correggere, c'e' solo da sapere. Stampa quello che il progetto **sa di non
sapere**, con il numero accanto e il motivo per cui quel numero non si riduce
da solo — «10363 voci su 10387 senza trascrizione IPA» e' una frase che qualcuno
puo' correggere lunedi', «non abbiamo le trascrizioni IPA» e' una frase che
resta vera per sempre. Gli stessi numeri compaiono sotto «E che cosa non sa»
nella pagina.

`copertura` dice **quanto italiano copre il glossario**: è il numero che
`buchi` non dà, perché `buchi` sa quello che il progetto *sa* di non sapere,
mentre `copertura` sa quello che il progetto *non sapeva di non sapere*. Il
metro sono i **lemmi** dell'ItWaC (Baroni 2009, licenza MIT): oggi **23,7%**
dei lemmi italiani frequenti sono coperti. Le parole mancanti sono elencate in
`dati/da_verificare/lacune.md`, con quello che la ricerca online ha trovato e
quello che non ha trovato. Senza quei file il comando dice che mancano e non
stampa un numero: meglio nessun numero che un numero sbagliato.

Una voce con piu' resi si trova da **ciascuno** dei suoi resi: il Ferri scrive
«Maladir → Maledire, esacràre», e chi cerca «maledire» trova la voce, come chi
cerca «esacràre». Si divide su virgola e punto e virgola, non sugli spazi:
«con calma» si trova con «con calma» e non con «calma», che e' un'altra voce.

`cerca` guarda **in entrambi i lati** per default, e dice da quale lato ha
trovato la parola. Serve a due persone diverse: a chi scrive una frase e cerca
la parola italiana, e a chi ha davanti un vocabolario dell'Ottocento e cerca
cosa vuol dire una parola ferrarese. Con `--direzione it-fe` o `--direzione
fe-it` si guarda un lato solo.

E se non e' una parola ma un **proverbio**, `cerca` lo trova lo stesso: prova
la forma dei libri, quella che si dice e il significato, e stampa le tre cose
insieme al fonte. Un proverbio non e' una voce e non si presenta come tale.

```bash
python3 -m traduttore.cli cerca "lupo non mangia di lupo"
python3 -m traduttore.cli traduci "a braccia aperte"   # a brazz avèrti
```

## I quattro livelli, e il quinto

Una parola attraversa il motore sempre nella stessa direzione, e ogni risposta
porta con se' **da dove viene** e **quanto si e' sicuri**:

| Livello | Origine | Confidenza | Quando |
|---|---|---|---|
| 1 | `glossario` | 0.95 | la voce c'e' nel glossario |
| 2 | `corpo` | 0.80 &ndash; 0.92 | la frase c'e' nel corpus parallelo, o c'e' il pezzo che combacia |
| 3 | `regola` | 0.55 &times; accordo | una regola morfologica imparata dal corpus |
| 4 | `modello` | 0.50 | un modello linguistico, solo con chiave API |
| 5 | `nessuna` | 0 | **non lo so** |

Il livello 5 non e' un errore: e' una risposta. Il motore restituisce la parola
di partenza e registra il buco, invece di tirare a indovinare. Il motivo e'
dichiarato in `sorgenti/traduttore/motore.py` e vale per una lingua che sta
morendo: **una lingua piccola non si traduce inventando, si traduce dentro un
perimetro dichiarato.**

## Le cinque varieta': il ferrarese non e' uno

Il glossario ha un campo `varieta` **obbligatorio** e i cinque codici sono
`cittadino`, `centrale` (arioso), `occidentale`, `orientale`, `transpadano`.
Non e' un dettaglio da dizionario: una parola di Bondeno data a uno studente
di Ferrara citta' e' una parola sbagliata, e senza il campo non c'e' modo di
accorgersene. Il controllo **G8** fa fallire la CI se una voce non lo dichiara.

```bash
python3 -m traduttore.cli varieta
```

```
cittadino    cittadino                      10387 voci  16 coppie, 0 brani
centrale     centrale, detto anche arioso    VUOTA     0 coppie, 0 brani
occidentale  occidentale                     VUOTA     0 coppie, 0 brani
orientale    orientale                       VUOTA     0 coppie, 0 brani
transpadano  transpadano, ibrido col polesano VUOTA   0 coppie, 0 brani

varieta' ancora vuote: centrale, occidentale, orientale, transpadano
```

**Quattro varieta' su cinque sono vuote, e questa e' la riga piu' importante
del progetto.** Non e' un difetto nascosto: e' il numero che dice che il
glossario copre la citta' e nient'altro. Le tassonomie stanno in
`dati/varieta.json`, con i territori e la fonte (Wikipedia «Dialetto
ferrarese», CC BY-SA 4.0); i territori che la fonte elenca in due gruppi
(Fiscaglia, Ostellato, Occhiobello, Goro) sono dichiarati come sovrapposti e
non vengono arbitrariamente separati.

## Le parole che non si usano piu': il significato moderno

Una voce come «ardiglione» o «tortiglione» arriva a uno studente con un
italiano che non scrive piu'. Non lo puo' intuire, e la pagina glielo
spiegava con un trattino.

Il glossario porta adesso tre campi nuovi, e vengono da una fonte che li
dichiara: **Wiktionary in italiano** (S017, CC BY-SA 4.0, licenza letta dalla
fonte stessa con `meta=siteinfo&siprop=rightsinfo`).

| Campo | Che cos'e' |
|---|---|
| `moderno` | che cosa vuol dire la parola in italiano di oggi |
| `fonte_moderno` | l'indirizzo della pagina da cui e' stato preso |
| `sinonimi` | gli equivalenti che la fonte dà |

**Nessun significato entra senza la sua fonte.** `moderno` e' l'unico campo
del glossario che si puo' scrivere senza aver aperto un dizionario, quindi il
controllo **G10** lo blocca: una riga con il significato e senza l'indirizzo
e' un errore, e non un avviso. Non e' una difesa contro gli errori di
significato — quelle li fa la fonte — e' una difesa contro la definizione
inventata.

```bash
python3 -u raccolta/moderni.py --daemon   # raccoglie, in locale, con cache
python3 raccolta/moderni.py --scrivi     # mette i risultati nel glossario
```

- **Tre definizioni in colonna, non tutte.** La fonte ne scrive anche dodici e
  il significato piu' lungo arrivava a 1970 caratteri, che nessuno legge. Il
  file tiene quello che la fonte ha scritto; la colonna ne mostra tre e **dichiara**
  il taglio, perche' una colonna che mostra tre pezzi senza dirlo sembra
  mostrarne tre di dieci che ci sono.
- **Tre sinonimi in colonna, non tutti** (in media la fonte ne dà dodici, e
  arrivano a centosessantatre). Anche questi stanno tutti nel file.
- **4063 voci su 10387 hanno il significato moderno**, e
  3235 hanno anche i sinonimi. Le altre sono un **buco dichiarato**,
  e sotto la tabella la pagina dice quante sono e perche': non «la fonte non
  ha l'articolo» e basta, ma la somma dei quattro motivi distinti, che sono
  quattro cose diverse.
- **Nessun filtro mio su «e' una parola antica».** Wiktionary non marchia
  l'obsoleto, quindi non si puo' chiedere alla fonte; e nessun segno
  ortografico distingue «ardiglione», che e' arcaico, da «cane», che non lo
  e'. Quindi la colonna non finge di separare le parole antiche: spiega
  tutte quelle che la fonte spiega. E' la domanda che resta aperta, ed e' il
  punto 5 di `AGENTS.md`.
- **La fonte non distingue il verbo dal nome.** In «mangiare» la prima
  definizione e' quella del **sostantivo**. Scegliere il senso giusto
  richiederebbe sapere quale parte del discorso sia la parola, e questo
  progetto non lo sa per tutte le voci: quindi si scrive quello che la fonte
  scrive, che e' la fonte e non una scelta mia.

## Il suono: le trascrizioni IPA e il riproduttore

Due cose, distinte, che non si confondono:

- **`dati/fonetica.jsonl` — come si scrive il suono.** 28 trascrizioni per
  ora. Il campo `fonte` dice da dove viene la **scrittura**, non il suono, e
  ogni riga porta `attendibilita: "I"` e `da_verificare: true`, perche' una
  trascrizione scritta qui dentro e' una lettura della grafia, non un ascolto.
  Il passaggio a `D` e' una riga da scrivere quando un parlante la conferma:

  ```json
  {"id":"T0001","fonte":"confermato da [nome], Bondeno, 2026","attendibilita":"D","da_verificare":false}
  ```

- **`dati/audio.jsonl` — la voce.** Adesso **zero brani**, e non e' un posto
  da riempire: e' un elenco di persone che hanno parlato. Un brano entra
  nella pagina solo con tre condizioni insieme (`consenso`, `licenza`,
  `pubblicabile`), e il file in `audio/` viene copiato in `web/audio/` solo se
  le tre ci sono. Il protocollo e' in `audio/README.md`.

- **`dati/sintesi.jsonl` — il suono di un programma, dichiarato come tale.**
  Dodici parole suonano, e accanto al pulsante c'e' scritto che le ha fatte
  `espeak-ng`. Non e' un brano e non entra mai in `web/audio/`: sta in
  `web/sintesi/`, porta `sintetica: true` e la dichiarazione in pagina. Vedi
  la sezione sotto.

```bash
python3 -m traduttore.cli pronuncia magnar
python3 -m traduttore.cli audio
python3 -m traduttore.cli sintesi
```

```
magnàr     /maˈɲnar/
           voce V0001 | varieta' cittadino | attendibilita I | DA VERIFICARE
           scrittura da: Bernardino Biondelli, Saggio sui dialetti gallo-italici, 1853
           nota: La `gn` e' resa /ɲ/ per la regola 3. Se la lingua parlata
                 raddoppia la consonante palatale la trascrizione e' mezza.
```

Il sistema di trascrizione e' dichiarato per intero nell'intestazione del
file, e le sue regole sono **regole di lettura della grafia**, non conoscenze
sul parlato. Dove le fonti disponibili non dicono niente - la `z`
intervoclica, la `s` intervocalica - il file **non sceglie**: lascia la nota e
resta `da_verificare`. E l'accento tonico viene dalla fonte: se la fonte non
lo marca, la trascrizione non lo mette, perche' metterlo sarebbe stato il modo
piu' economico di sbagliare.

**Nessuna voce sintetica al posto di una persona.** Nella pagina c'e' un
tasto per far leggere l'italiano con la voce del browser, e sta **spento**:
non e' una voce ferrarese, in alcuni browser usa una connessione, e serve solo
a sentire il ritmo dell'italiano mentre si guarda il ferrarese. Il gioco deve
usare registrazioni vere e dichiarare che sono vere.

Il comando `voce` produce un suono **sintetico in locale** con `espeak-ng`, e
qui va detto che cosa sia e che cosa non sia:

```bash
python3 -m traduttore.cli voce magnàr            # legge, non scrive nulla
python3 -m traduttore.cli voce magnàr --suona    # scrive il wav
```

```
magnàr       /magnˈar/
fonemi per il sintetizzatore: magn'ar
da chiarire prima di fidarsi:
  - `gn` davanti a `à`: la regola 3 dice /ɲ/ solo davanti a vocale anteriore
attendibilita I | da verificare: si
questa e' una voce sintetica: non e' un parlante ferrarese, e non verifica la trascrizione.
```

Una voce sintetica conosce le regole di **lettura** di una grafia, e il
parlato non le segue: non sa che la `s` intervocalica si dice come si vuole,
e non sa come suona `scaranna` detta da chi e' nato a Ferrara. Per questo il
wav non verifica niente, e i file escono in `raccolta/lavorato/voci/` che non
e' tracciata, **mai** in `web/audio/`: copiare li' significa pubblicarli, e la
regola A1-A10 vuole consenso, licenza e `pubblicabile`, e qui nessuna persona
ha parlato, quindi nessuno ha acconsentito a nulla.

## Il pulsante che fa sentire la parola, e che cosa non è

Nella pagina, accanto a una parola con una trascrizione dichiarata, c'è un
tasto che la fa suonare. **Non è una persona.** È `espeak-ng` che legge la
grafia attraverso le regole di `dati/fonetica.jsonl`, e la pagina lo scrive
accanto al pulsante, non in un documento che nessuno legge.

La distinzione che regge tutto è fra due cartelle che non si toccano mai:

| | `web/audio/` | `web/sintesi/` |
|---|---|---|
| chi ha parlato | una persona | un programma |
| cosa serve per entrarci | consenso, licenza, decisione di pubblicazione | una trascrizione dichiarata **senza dubbi** |
| com'è dichiarato | `consenso`, `licenza`, `pubblicabile` | `sintetica: true` e la dichiarazione in pagina |
| quante adesso | **0** | **12** |

**Perché dodici e non tutte.** Suonare tutte le 10401 parole del glossario
costerebbe circa **493 megabyte**, che non è una pagina. Quindi il suono esiste
solo dove il progetto ha già scritto *come* la parola si pronuncia: le 28
trascrizioni dichiarate. E anche lì non tutte: delle 28, **16 non suonano**,
perché hanno un dubbio che le regole di lettura segnalano. Una parola con un
dubbio non ha un file, e la pagina dice perché.

La ragione è che suonare una pronuncia che il progetto *non sa* dare è peggio
che non suonare: lo studente impara il suono sbagliato con la stessa efficacia
con cui avrebbe imparato quello giusto, e non ha modo di accorgersene. Il
controllo **Y4** verifica che nessun file sia comparso per una parola con un
dubbio: è il buco che il pulsante avrebbe aperto, chiuso e dichiarato.

Si generano con un comando, e il manifesto è generato insieme:

```bash
python3 raccolta/sintetizza.py            # scrive i wav e dati/sintesi.jsonl
python3 raccolta/sintetizza.py --prova    # dice i numeri, non scrive
```

**Che cosa non cambia.** Un suono generato non verifica niente. Le righe di
`dati/fonetica.jsonl` restano `attendibilita: "I"` e `da_verificare: true`, i
suoni restano `I`, e l'unica cosa che chiude la domanda è un parlante ferrarese
che dica la parola.

**Una cosa che non si può fare.** Il suono non dice da quale programma è stato
prodotto: dentro il `wav` non c'è la parola «espeak» nemmeno una volta, e il
formato è un RIFF con quattro campi e nient'altro. Un controllo che volesse
distinguere le due cartelle guardando il contenuto del file non potrebbe
funzionare, e passerebbe per sempre senza aver guardato niente. La separazione
è quindi sui **nomi** e sui **manifesti**, ed è il controllo Y3b a tenerla.

## Le regole morfologiche si imparano, non si scrivono

In `sorgenti/traduttore/morfologia.py` non c'e' nessuna regola scritta a mano.
Una regola nasce da coppie reali, e per nascere deve:

1. essere **spezzata in radice piu' desinenza**, non in prefisso piu' suffisso,
   perche' `cantare` / `cantar` non ha suffissi uguali e un learner che cerca
   suffissi uguali non trova niente;
2. essere sorretta da **almeno due coppie** e da **almeno due radici diverse**,
   altrimenti non e' una regola ma un caso;
3. **sopravvivere alla propria generalizzazione**: viene riapplicata ai suoi
   stessi esempi, e se produce una parola diversa da quella che il testo
   documenta, l'accordo scende sotto la soglia e la regola viene buttata.

Il terzo punto e' quello che protegge dalla classe di errore piu' pericolosa di
un traduttore: una parola lunga, plausibile e sbagliata. Il test
`test_la_generalizzazione_che_sbaglia_non_diventa_regola` verifica proprio
che una regola `are` &rarr; `ar` imparata da `cantare` e `camminare` **non**
venga salvata, perche' su `camminare` produce `camminar` dove il testo dice
`caminar`.

## L'IA c'e', ma non e' necessaria

Il livello 4 usa l'API Anthropic ed e' **facoltativo**. Senza chiave il motore
funziona lo stesso, e funziona peggio ma funziona:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python3 -m traduttore.cli traduci "qualcosa di nuovo" --ia
```

Tre regole, che il codice fa rispettare:

- il modello **non e' una fonte**: non entra mai nel glossario ne' nel corpus, e
  quello che produce viene scritto in `dati/proposte/`, la coda di revisione;
- riceve il contesto (glossario vicino, coppie simili, regole) e gli si chiede
  esplicitamente di rispondere `non_so` quando non sa;
- una risposta sotto la soglia **non viene usata**: il motore torna al livello
  3, che e' quello verificato.

```bash
python3 -m traduttore.cli proposte
```

La coda si riempie da sola quando si usa `--ia` (e non si scrive con
`--no-proposte`). Il file si **append-e**, quindi non si perde niente, e i
controlli **M1&ndash;M4** fanno fallire la CI se una proposta si dichiara
documentata o si porta dentro un campo `fonte`: la risposta di un modello non
diventa una fonte scrivendogli il nome in un campo, e a farlo deve essere una
persona che ha aperto il vocabolario. Il protocollo e' in
[dati/proposte/README.md](dati/proposte/README.md).

## Quanto costa l'audio

La domanda che il progetto si porta da più tempo — «quante ore di registrazione
servono?» — ha una risposta con l'aritmetica in [STIMA-AUDIO.md](traduttore-ferrarese/STIMA-AUDIO.md).
In breve: il gioco ha **150 livelli di ferrarese** (i 900 sono le sei lingue),
ciascuno con un testo autentico che per il ferrarese è «una trascrizione di un
parlante».

| Scenario | Persone | Audio grezzo | Trascrizione |
|---|---|---|---|
| anno 1 (30 livelli) | 5 | 2 h 30 | 10 ore |
| progressione intera (150 livelli) | 25–30 | 12 h 30 – 15 ore | 50 – 60 ore |

Quindici ore di registrazione non sono un problema. Trovare trenta persone che
parlino ferrarese di cinque varietà diverse e che diano il permesso, sì. Il
percorso per un anno di gioco è cinque persone e una settimana, e la pagina che
si segue è `audio/SESSIONE.md`.

## Struttura

```
traduttore-ferrarese/
  dati/sintesi.jsonl    i suoni generati: generato, non scritto a mano
  web/sintesi/          i dodici wav che la pagina fa suonare
  README.md            questo file
  RACCOLTA.md          dove si accumulano vocabolari, testi e registrazioni
  REGISTRO.md          che cosa e' cambiato, e perche'
  STIMA-AUDIO.md       quante ore di registrazione servono, con l'aritmetica
  AGENTS.md            istruzioni per chi ci lavora, persone e IA
  dati/
    glossario.jsonl    le parole, con la fonte, la varieta' e il
                       significato moderno (con la sua fonte)
    coppie.jsonl       le frasi parallele, con la fonte e la varieta'
    proverbi.jsonl     i proverbi, con la forma dei libri e quella che si dice
    varieta.json       le cinque varieta' del ferrarese, con i territori
    fonetica.jsonl     le trascrizioni IPA, con il sistema dichiarato
    regole.json        generato da `impara`, non si modifica a mano
    fonti.json         il registro delle fonti e delle loro licenze
    audio.jsonl        il manifesto dei brani, con il consenso
    da_verificare/     i dati con la licenza non ancora verificata: li
                       possediamo, non li pubblichiamo, e il controllo D1
                       controlla che non vengano usati per errore
    proposte/          la coda di revisione delle risposte del livello IA
  audio/               i brani registrati, il protocollo di sessione e il
                       modello di consenso: adesso non c'e' nessun brano
  sorgenti/
    traduttore/        il pacchetto
      normalizza.py    due livelli di normalizzazione, e quando usare ciascuno
      glossario.py     le voci, indicizzate per le due direzioni
      corpora.py       coppie e proverbi, e il confronto parola per parola
      varieta.py       le cinque varieta' e quello che c'e' in ciascuna
      fonetica.py      le trascrizioni IPA e il controllo dei simboli
      audio.py         il manifesto dei brani e le tre condizioni di pubblicazione
      morfologia.py    l'apprendimento delle regole
      motore.py        i quattro livelli, il buco, la confidenza
      modello.py       il livello IA, facoltativo
      proposte.py      la coda di revisione del livello IA
      verifica_dati.py i controlli sui dati
      cli.py           la riga di comando
    modello.html       il modello della pagina
    costruisci_web.py  la generazione della pagina
  prove/               i test
  raccolta/            gli strumenti per passare da un libro a dei dati:
                         pdf_testo.py     l'estrattore di PDF senza librerie
                         estrai_ferri.py  stacca le voci dall'OCR di Ferri
                         filtra_candidati.py  tiene solo quello che si legge
                         lettura_ferri.py la lista scelta a mano, voce per voce
                         costruisci_da_ferri.py  la porta dentro `dati/`
                         moderni.py         il significato moderno da
                                           Wiktionary: l'unico punto di questo
                                           progetto che usa la rete, e la usa
                                           per chiedere, non per scaricare
                       `grezzi/` e `lavorato/` non sono nel repository: sono
                       i libri e il mezzo, entrambi ricreabili con una riga
  web/                 la pagina generata
  .github/workflows/   verifica continua e pubblicazione
```

## Il livello 4 non e' nella pagina

La pagina web e' statica e non ha chiavi dentro. Chi la usa vede i livelli
1, 2, 3 e 5. E' una scelta deliberata: la pagina si distribuisce con un
doppio clic e funziona senza rete, il che significa che nessuna chiave puo'
esserci dentro.

## I dati, e dove metterli

`RACCOLTA.md` e' il documento da leggere quando si trova qualcosa di
ferrarese. In breve:

- `dati/fonti.json` dice che cosa si puo' usare: **solo lo stato `acquisita`
  alimenta il glossario**, e `acquisita` vuol dire che il file e' nel
  repository con la licenza verificata;
- il glossario accetta solo voci con la fonte, e il controllo **G4** fa
  fallire la CI se una voce si dichiara documentata senza nominare libro e
  pagina;
- `REGISTRO.md` tiene **perché** ogni versione è quella che è: un numero di
  versione senza un motivo è un numero, e il motivo è la parte che non si
  ricava dal codice;
- **una fonte con licenza non verificata non si pubblica**: le voci e le coppie
  che ne derivano stanno in `dati/da_verificare/`, fuori dai dati attivi, e
  il controllo **D1** verifica che non vengano usate per errore;
- l'audio senza consenso scritto non si pubblica, e i dati degli studenti non
  entrano nel repository.

## Cosa non c'e' (e va detto)

- **Non esiste un corpus di parlato spontaneo ferrarese** consultabile, e non
  si puo' costruire per download: si costruisce registrando persone, con il
  consenso. E' il buco piu' grande del progetto ed e' dichiarato in
  `dati/fonti.json` (S009).
- **Non c'e' riconoscimento del parlato ferrarese.** Whisper ha un modello
  italiano, non ferrarese. Su parole ferraresi sbaglia, e su parole italiane
  sbaglia in modo sistematico (`ghe` diventa `che`, `brisa` diventa
  `brisa` per caso e non per merito). Va usato come **indizio da valutare**
  dal docente, mai come giudizio automatico.
- **Non c'e' sintesi vocale ferrarese**, e non e' un progetto: nessun modello
  esiste, costruirne uno richiederebbe decine di ore di registrazione pulite,
  che sono anche le ore che servirebbero per l'ascolto. Il gioco deve quindi
  usare **registrazioni vere**, non voci sintetiche, e dichiarare che sono
  vere.
- **Non c'e' nessuna registrazione**: `dati/audio.jsonl` e' vuoto e
  `audio/` contiene il protocollo e il modello di consenso, non un brano. Le
  28 trascrizioni IPA ci sono, ma nessuna e' verificata da un parlante
  (`attendibilita D`), e le altre **10363 voci su 10387 non hanno nessuna
  trascrizione**: `buchi` stampa i due numeri. Finche' il secondo vale zero,
  la pronuncia non e' documentata da
  nessuna parte e la pagina lo dice. Quanto tempo ci vuole davvero e' in
  `STIMA-AUDIO.md`: quindici ore di registrazione per tutta la progressione,
  e il vincolo non sono le ore, sono le persone.
- **Due voci, due frasi e due trascrizioni sono in una fila d'attesa**,
  `dati/da_verificare/`: vengono dalla traduzione ferrarese della
  Dichiarazione universale dei diritti umani (S003), e la licenza di quella
  fonte non e' verificata. Non le usa nessuno, non sono nella pagina e il
  controllo **D1** fallisce se finiscono nei file attivi. Il glossario ha
  quindi **10387 voci**, **tutte di una sola varieta'**, il cittadino, e
  **10156 non verificate da un informatore** (`attendibilita I`,
  `da_verificare`): sono la trascrizione meccanica del vocabolario, non una
  voce controllata. Quattro varieta' su cinque sono vuote dichiarate. Non e'
  un dizionario e non si presenta come tale.
- **Le locuzioni si cercano solo dalla parte che le contiene.** Duemila
  trentaquattro delle 10387 voci hanno piu' di una parola **dal lato
  ferrarese**, e il motore
  le accorpa prima di tradurre parola per parola: «a braccia aperte» diventa
  `a brazz avèrti` e non tre buchi. Ma l'accorpamento guarda il lato da cui
  si parte: se scrivi in italiano «a braccia aperte» trova la voce, e se
  scrivi in italiano «sicuramente» per la voce che il Ferri traduce
  `a man salva`, non la trova, perche' in quel glossato l'italiano e' una
  parola sola. Non e' un difetto da correggere: e' quello che c'e' nel
  vocabolario. Il conto lo stampa `buchi`.
- **I proverbi sono in pagina e si cercano**, e `popolare` e' vuoto per tutti
  e ventotto. La forma che si dice non l'ha ancora detta nessuno, e un campo
  vuoto dichiarato vale piu' di una forma inventata per simmetria.
- **La grafia e' del 1889.** Le voci prese dal vocabolario di Ferri sono
  nella grafia del libro, con l'accento sui toni come il Ferri lo intendeva.
  Non e' la grafia di oggi e non e' quella che si sente: le forme sono
  verificabili aprendo il libro alla pagina indicata, non ascoltando un
  parlante.
- **Non ci sono articoli, preposizioni ne' ausiliari.** Su 131 parole
  funzionali dell'elenco di `copertura.py`, 38 sono nel glossario e **93 passano
  invariate**: `il`, `a`, `con`, `ho`, `non` non vengono tradotti e finiscono
  nei buchi. Quindi «sono seduto sulla sedia» esce `son seduto Sslà Scaràna` e
  «il cane e' a casa» esce con due buchi. Non si aggiungono a mano: ogni voce
  ha bisogno di una fonte e nessuna fonte aperta le contiene. Il punto 6 di
  `AGENTS.md` dice quale fonte controllare per prima.
- **Non ci sono forme finite dei verbi.** Il glossario contiene lemmi, non
  coniugazioni: `sedarsi` c'e', `seduto` no. Riconoscere un participio dalla
  radice del verbo e' **morfologia**, non vocabolario, ed e' la strada giusta —
  ma non ci sono esempi in `dati/regole.json` che la insegnino. Il buco e'
  dichiarato e non aggirato: il motore lascia la parola come sta e registra
  il buco, che e' il comportamento giusto per un vocabolario che non sa.
- **Non si sa quali parole sono antiche.** La colonna «in italiano di oggi» dice
  che cosa *vuol dire* una parola, non che *quella parola non si usa piu'*:
  nessuna fonte aperta finora marchia l'obsoleto. Su 4063 voci si ha
  il significato moderno e su 6324 no, e quel numero non e' la misura di
  quanto e' antico il glossario: e' la misura di quanto ne sa la fonte che si
  e' aperta. Perci' la pagina lo dichiara e non lo nasconde.

## I controlli

```bash
python3 prove/test_traduttore.py     # 152 test
python3 -m traduttore.cli verifica   # i controlli sui dati
```

I controlli non correggono: segnalano. La correzione la fa una persona,
perche' il glossario e' un fatto e i fatti non si correggono in automatico.

## License

- codice: MIT, testo in `LICENSE`, spiegazione in `LICENZE.md`;
- dati: la licenza e' **per voce**, e la dichiara il campo `fonte` di ogni
  voce. Una voce la cui fonte non e' in pubblico dominio non si pubblica.