---
titolo: Traduttore italiano-ferrarese
versione: 0.3
data: 2026-10-03
autore: progetto «I cinque duchi»
---

# Traduttore italiano &ndash; ferrarese

Un traduttore fra l'italiano e il **ferrarese**, costruito per il gioco
«I cinque duchi» e per chi vuole imparare la lingua di Ferrara.

La caratteristica di questo progetto non e' che traduce bene. E' che **quando
non sa, dice che non sa**, e dice anche *perche'* non lo sa e *che cosa
servirebbe* per saperlo. Con ventiquattro voci in un glossario, tutte di una
sola varieta' e tutte da due fonti, questa e' la proprieta' piu' importante che
ha.

## Come si usa

```bash
export PYTHONPATH=sorgenti

python3 -m traduttore.cli traduci "non c'è pane"
python3 -m traduttore.cli traduci "brisa" --direzione fe-it
python3 -m traduttore.cli cerca magnar
python3 -m traduttore.cli varieta
python3 -m traduttore.cli pronuncia magnar
python3 -m traduttore.cli audio
python3 -m traduttore.cli proposte
python3 -m traduttore.cli stato
python3 -m traduttore.cli verifica
python3 -m traduttore.cli impara
python3 -m traduttore.cli web
```

E la pagina: `python3 -m traduttore.cli web` scrive `web/index.html`, che si
apre con un doppio clic e funziona **senza connessione**. Nessun account,
nessun server, nessuna richiesta di rete. Su GitHub la pubblica il workflow
`pagine.yml`.

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
cittadino    cittadino                       24 voci   8 coppie, 0 brani
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

```bash
python3 -m traduttore.cli pronuncia magnar
python3 -m traduttore.cli audio
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

## Struttura

```
traduttore-ferrarese/
  README.md            questo file
  RACCOLTA.md          dove si accumulano vocabolari, testi e registrazioni
  AGENTS.md            istruzioni per chi ci lavora, persone e IA
  dati/
    glossario.jsonl    le parole, con la fonte e la varieta'
    coppie.jsonl       le frasi parallele, con la fonte e la varieta'
    proverbi.jsonl     i proverbi, modello commentato e vuoto
    varieta.json       le cinque varieta' del ferrarese, con i territori
    fonetica.jsonl     le trascrizioni IPA, con il sistema dichiarato
    regole.json        generato da `impara`, non si modifica a mano
    fonti.json         il registro delle fonti e delle loro licenze
    audio.jsonl        il manifesto dei brani, con il consenso
    da_verificare/     i dati con la licenza non ancora verificata: li
                       possediamo, non li pubblichiamo, e il controllo D1
                       controlla che non vengano usati per errore
    proposte/          la coda di revisione delle risposte del livello IA
  audio/               i brani registrati: adesso c'e' solo il README
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
  `audio/` contiene solo il protocollo. Le 28 trascrizioni IPA ci sono, ma
  nessuna e' verificata da un parlante (`attendibilita D`): finche' vale
  zero, la pronuncia non e' documentata da nessuna parte e la pagina lo dice.
- **Quattro voci e due frasi sono in una fila d'attesa**,
  `dati/da_verificare/`: vengono dalla traduzione ferrarese della
  Dichiarazione universale dei diritti umani (S003), e la licenza di quella
  fonte non e' verificata. Non le usa nessuno, non sono nella pagina e il
  controllo **D1** fallisce se finiscono nei file attivi. Il glossario ha
  quindi **24 voci**, tutte da due fonti e **tutte di una sola varieta'**, il
  cittadino. Quattro varieta' su cinque sono vuote dichiarate. Non e' un
  dizionario e non si presenta come tale.

## I controlli

```bash
python3 prove/test_traduttore.py     # 55 test
python3 -m traduttore.cli verifica   # i controlli sui dati
```

I controlli non correggono: segnalano. La correzione la fa una persona,
perche' il glossario e' un fatto e i fatti non si correggono in automatico.

## License

- codice: MIT, testo in `LICENSE`, spiegazione in `LICENZE.md`;
- dati: la licenza e' **per voce**, e la dichiara il campo `fonte` di ogni
  voce. Una voce la cui fonte non e' in pubblico dominio non si pubblica.