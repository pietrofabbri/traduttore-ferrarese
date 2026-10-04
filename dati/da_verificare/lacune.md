# Le parole importanti che al glossario mancano

Questa è la lista delle **parole italiane frequenti che il glossario non
traduce**, cioè quelle per cui il motore, a chi le scrive, risponde «nessuna
voce». Non è un elenco di tutto quello che manca: è l'elenco delle mancanze
che, se restassero, renderebbero il traduttore inutile per il suo uso.

## Che cosa c'è dentro e che cosa non c'è

Dentro ci sono le **mancanze concrete**: il corpo, la casa, il cibo, la
scuola, i mezzi. Sono le parole che un gioco di lingua usa quando chiede
«traduci questa frase» e le parole che uno studente scrive quando racconta
la giornata. Fuori restano le frequenze alte ma astratte — «decreto»,
«regionale», «informazione» — che sono le più numerose e le meno urgenti:
non sono le parole di cui si accorge qualcuno che sta giocando.

La misura della copertura è di `raccolta/copertura.py`, che confronta il
glossario con i **lemmi** dell'ItWaC (Baroni, Bernardini, Ferraresi,
Zanchetta 2009, via `franfranz/Word_Frequency_Lists_ITA`, licenza MIT). Il
numero di oggi: **38,4% dei lemmi frequenti italiani sono coperti**.

## Perché la copertura è bassa e non è un difetto del vocabolario

Il vocabolario del Ferri (1889) è un libro di casa e di bottega: pane,
mestiere, arredi, animali, modo di dire. Non è un vocabolario di scuola, e
non copre — e non potrebbe coprire — `anno`, `numero`, `risposta`,
`televisione`. Sono le parole che nel 1889 o non esistevano o non si
scrivevano cosi. Coprirle non è attingere al vocabolario del Ferri: è un
altro lavoro, e va detto.

## Lo stato di ogni riga

- **trovata** — la parola c'è in una fonte online, elencata sotto con la
  fonte. Quando la fonte ha una **licenza verificata**, la riga entra nel
  glossario attivo; quando non ce l'ha, la riga va in
  `dati/da_verificare/` e il controllo **D1** le tiene fuori dai dati attivi
  finche' la fonte non e' chiara. Le cinque attestazioni online sono
  **V10400-V10404** e sono tutte in attesa: nessuna entra nei dati attivi e
  nessuna e' usata dal motore.
- **non trovata** — la ricerca online non ha dato niente di utilizzabile, e
  la parola resta un buco dichiarato. Un buco dichiarato vale piu' di una
  parola inventata.

## Le parole importanti e dove siamo

### Corpo

| italiano | situazione | nota |
|---|---|---|
| testa | **trovata** | `capunàra` = **V10403**, in attesa (S013) |
| braccio | non trovata | |
| spalla | non trovata | |
| gamba | non trovata | |
| piede | non trovata | |
| orecchio | non trovata | |
| dito | non trovata | |
| ventre | non trovata | |
| schiena | non trovata | |

### Casa e arredi

| italiano | situazione | nota |
|---|---|---|
| sedia | **gia' nel glossario** | `V7636` = `scaràna`; confermata anche da robertobigoni.it |
| tavolo | non trovata | |
| porta | non trovata | |
| muro | non trovata | |
| pavimento | non trovata | |
| specchio | non trovata | |
| divano | non trovata | |
| armadio | non trovata | |
| lampada | non trovata | |
| sapone | non trovata | |

### Cucina

| italiano | situazione | nota |
|---|---|---|
| forchetta | **trovata** | `furzina` = **V10400**, in attesa (S014) |
| cucchiaio | **trovata** | `guciara` = **V10401**, in attesa (S014) |
| coltello | **trovata** | `piron` = **V10402**, in attesa (S014) |
| bicchiere | non trovata | |
| tazza | non trovata | |
| padella | non trovata | |
| piatto | non trovata | |
| carne | non trovata | |
| burro | non trovata | |
| mela | non trovata | |
| pomodoro | non trovata | |
| carota | non trovata | |
| uva | non trovata | |
| miele | non trovata | |
| farina | non trovata | |
| sale | non trovata | |

### Abbigliamento

| italiano | situazione | nota |
|---|---|---|
| scarpa | non trovata | |
| abito | non trovata | |
| cintura | non trovata | |
| occhiale | non trovata | |
| cappello | non trovata | |

### Oggetti e mezzi

| italiano | situazione | nota |
|---|---|---|
| chiave | non trovata | |
| borsa | **trovata** | `barsacca` = **V10404**, in attesa (S013) |
| carta | non trovata | |
| penna | non trovata | |
| telefono | non trovata | |
| televisione | non trovata | |
| orologio | non trovata | |
| macchina | non trovata | |
| bicicletta | non trovata | |
| treno | non trovata | |
| aereo | non trovata | |
| nave | non trovata | |

### Scuola

| italiano | situazione | nota |
|---|---|---|
| maestro | non trovata | |
| risposta | non trovata | |
| domanda | non trovata | |
| numero | non trovata | |
| cognome | non trovata | |

## Le fonti online usate, e il loro stato di licenza

Nessuna di queste ha una licenza che il progetto possa verificare. Per la
regola che gia' vale per S003, quindi, vanno in `dati/da_verificare/` e non
nel glossario attivo.

- **dizionariopopolare.blogspot.com** — dizionario ferrarese raccolto da un
  appassionato (Matteo, 2011). Fonte ricchissima di modi di dire e di lessico
  domestico. **Licenza: nessuna dichiarata.** Registro come **S013**.
- **listonemag.it** — articolo del 2014 con un invito pubblico a raccogliere
  parole ferraresi; le glosse sono nei commenti dei lettori. E' la prova che
  il dialetto e' vivo e che le persone lo scrivono, ma un commento non e' una
  fonte. **Licenza: nessuna dichiarata.** Registro come **S014**.
- **robertobigoni.it** — note linguistiche sul ferrarese (R. Bigoni).
  Utilissime per la fonetica e per l'etimologia, e cita esplicitamente
  «la sedia per i Ferraresi e' la skaràna». **Licenza: nessuna dichiarata.**
  Registro come **S015**.

## La fonte che chiuderebbe davvero

Nei commenti di listone.it un lettore segnala un libro vero:
**«Vocabolario Italiano-Ferrarese» di Luigi Vincenzi, Alberto Ridolfi e
Floriana Guidetti** (Edizioni Cartografica, 2007), e l'**AR.PA.DIA.
(Archivio Padano dei Dialetti)**, l'archivio del Comune di Ferrara che ha
promosso il **Vocabolario Ferrarese-Italiano** e la **Grammatica ragionata
del dialetto ferrarese**.

E' un'istituzione pubblica e un lavoro di specialisti: se project's regola e'
una fonte con la sua provenienza, questa e' la fonte che copre il lessico
contemporaneo, cioe' `televisione`, `telefono`, `chiave`. Non e' nel
pubblico dominio e non si puo' copiare, ma si puo' **citare** e si puo'
**consultare in biblioteca**. Va registrata come fonte e consultata: e' la
strada che chiude metà di questa lista.

## Come si tiene viva questa lista

`raccolta/copertura.py` la ricalcola. Quando una riga passa dal «non
trovata» al «trovata», o quando il glossario copre una parola, la lista va
aggiornata a mano: **è un documento, non un calcolo**. Il calcolo dice
quante mancano; il documento dice quali e perché quelle contano.