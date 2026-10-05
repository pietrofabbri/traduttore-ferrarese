---
titolo: Istruzioni per chi lavora al progetto
versione: 0.10
data: 2026-10-03
autore: progetto «I cinque duchi»
---

# Istruzioni per chi lavora al progetto (persone e IA)

Leggi questo prima di modificare qualsiasi cosa. Vale per i due progetti:
«I cinque duchi» e il traduttore.

## 1. La regola che governa tutto

**Nessuna risposta senza fonte. Nessun vuoto riempito a caso.**

Nel traduttore una parola che nessuna fonte conosce resta com'e' e viene
dichiarata un buco. In un glossario una voce senza fonte non entra. In un
elenco di proverbi una riga senza informatore non e' un proverbio.

La ragione e' tecnica, non morale. Il danno di una parola ferrarese inventata non
si vede a occhio: `ca` per «casa» sembra giusta, e per vent'anni nessuno la
corregge perche' nessuno ha un altro modo di sapere che e' sbagliata. Un
traduttore di una lingua che sta morendo che sbaglia in silenzio e' peggio di
un dizionario che non esiste.

## 2. Le regole tecniche che non si cambiano senza chiedere

- **Nessuna richiesta di rete a runtime.** La pagina web funziona da `file://`,
  il gioco funziona offline. E' la condizione che li rende distribuibili in
  una classe.
- **Un rimando non e' una richiesta.** Nella pagina si puo' mettere un
  `<a href>` verso la fonte di una voce — e nella colonna del significato
  moderno c'e', perche' una fonte citata e non cliccabile e' una dichiarazione.
  Quello che non si puo' mettere e' `src=` verso l'esterno, e non si puo' fare
  `fetch()` dal codice. Il controllo nella CI guarda le risorse e le chiamate,
  non i collegamenti, e guarda il motivo per cui esiste: se il divieto si
  allargasse ai rimandi, l'unica cosa che si perderebbe e' la possibilità di
  andare a verificare una fonte.
- **Nessun account, nessun server, nessuna telemetria.**
- **Niente dati degli studenti nel repository.** Vale anche per le voci dei
  compagni di classe, che sono la cosa che il progetto vorrebbe di piu' e che
  non ci devono stare.
- **Le due copie della logica devono essere identiche.** Il motore esiste in
  Python (`sorgenti/traduttore/motore.py`) e in JavaScript
  (`sorgenti/modello.html`). Non e' una duplicazione tollerata: e' un rischio
  dichiarato. Se le due divergono la pagina mente, e chi legge la pagina ha
  ragione di crederle. Se cambi un livello, cambi entrambi, nello stesso
  commit, e poi lanci `prove/controlla_equivalenza.py`, che confronta le
  risposte delle due copie frase per frase sulle stesse frasi. Il confronto
  e' sulle risposte e non sul codice: le due copie possono essere scritte
  diversamente e vanno bene finche' dicono la stessa cosa.
- **Il livello IA non e' una fonte.** Non entra nel glossario, non entra nel
  corpus, e non si usa senza chiave. Se qualcuno lo toglie, il progetto
  funziona lo stesso: e' il test che garantisce che sia davvero facoltativo.
  Quello che produce viene scritto in `dati/proposte/` e li resta finche' una
  persona non lo verifica: **una proposta non si dichiara documentata**, e i
  controlli M1 e M2 falliscono se qualcuno le mette dentro un `fonte`.

## 3. Prima di dichiarare finito

```bash
cd traduttore-ferrarese
export PYTHONPATH=sorgenti
python3 -m traduttore.cli verbi            # le forme verbali attestate e i buchi
python3 prove/test_traduttore.py           # 337 test
python3 -m traduttore.cli italiano         # che cos'e' una parola in
                                           # italiano, e il buco
python3 prove/ci_locale.py                 # i passi del workflow, in locale
python3 prove/scanner.py                   # caratteri sbagliati
python3 -m traduttore.cli verifica         # i controlli sui dati
python3 prove/controlla_equivalenza.py     # la pagina dice come il motore
python3 prove/controlla_mutazioni.py       # i test prendono le
                                           # decisioni rotte? quattro
                                           # minuti e mezzo
```

I tre devono uscire senza errori. Se hai toccato `dati/`, aggiungi anche:

```bash
python3 -m traduttore.cli impara     # rigenera dati/regole.json
python3 -m traduttore.cli web        # rigenera TUTTE le pagine in web/
python3 -m traduttore.cli buchi      # i numeri di quello che manca
```

`web` non genera una pagina ma **ventisei**: la home, il traduttore, l'indice
del glossario, ventuno fette, le frasi e i suoni. Il comando stampa il peso di
ognuna, e quel peso e' un numero che va guardato: una pagina che torna a
diversi megabyte e' la divisione annullata da qualche parte. Le pagine si
aggiungono in `PAGINE` dentro `sorgenti/costruisci_web.py`, mai a mano.

`prove/controlla_equivalenza.py` confronta Python e JavaScript su
`web/traduttore.html`, che e' l'unica pagina con il motore e i dati che il
motore usa. Se lo sposti, sposta anche quella riga.

E se hai toccato `dati/fonetica.jsonl`, anche i suoni generati, che sono un
file generato come gli altri e va committato insieme al manifesto:

```bash
python3 raccolta/sintetizza.py       # rigenera web/sintesi/ e dati/sintesi.jsonl
python3 raccolta/bigoni.py           # raccoglie il vocabolario di R. Bigoni
```

`raccolta/bigoni.py` parla con la rete e scrive in `raccolta/grezzi/`, che
non e' tracciato perche' si ricrea con una riga. Non scrive mai il
glossario: raccoglie, e quello che diventa voce e' una decisione che passa
dai controlli. Lo script **non scrive niente** se quello che arriva non
tiene: una raccolta vuota sembrerebbe una raccolta riuscita.

Il comando esce con un codice diverso da zero e **non scrive niente** se
`espeak-ng` non e' installato: un suono prodotto da un programma non
dichiarato non sarebbe verificabile da nessuno.

`buchi` non e' un controllo e non fallisce mai: conta quello che il progetto
sa di non sapere e scrive **perche'** manca. Se hai aggiunto una riga che
chiude un buco, il numero deve scese: se non scende, o il numero e' sbagliato o
la riga non chiude il buco che dice di chiudere.

E committa anche i due file generati. Un repository in cui il file delle
regole non corrisponde a quello che i dati produrrebbero mente sul proprio
contenuto, e il workflow `verifica.yml` lo segnala.

E se la modifica cambia il comportamento o i dati, **una riga in
`REGISTRO.md`**: la versione, e il motivo in una frase. Una versione senza un
motivo e' un numero, e il motivo di una decisione non si ricava dal codice.

Se hai toccato una voce, la copia le due cose che viaggiano con lei:
la sua **varieta'** (`dati/varieta.json` e `dati/glossario.jsonl`) e la sua
**trascrizione IPA** (`dati/fonetica.jsonl`). Una voce nuova senza varieta'
fallisce G8; una voce nuova senza IPA non fallisce niente, e va comunque
segnalata come un buco.

## 4. I controlli non correggono

`verifica_dati.py` segnala, non corregge. Il motivo e' dichiarato nel modulo: il
glossario e' un fatto, e un fatto non si corregge in automatico. Se un
controllo segnala un problema, la correzione la fa una persona e la risolve
nel campo giusto.

I codici da conoscere:

| Codice | Controllo |
|---|---|
| G1, G2 | voce senza id, id duplicato |
| G3 | voce con un lato solo |
| **G4** | **attendibilita `D` senza fonte** |
| G5 | attendibilita fuori dall'insieme |
| G6 | fonte troppo breve per essere controllabile |
| G7 | voce non verificata ma dichiarata documentata |
| **G8** | **voce senza `varieta'`** |
| G9 | `varieta` fuori dall'insieme delle cinque |
| **G10** | **significato moderno senza `fonte_moderno`** |
| G11, G12 | fonte del significato moderno senza significato, sinonimi senza significato (avvisi) |
| V1&ndash;V6 | tassonomia: codici duplicati, nomi che non nominano, senza territorio, senza fonte, varieta' assente |
| C1&ndash;C6 | coppie: id, lati, fonte, tipo, attendibilita |
| **C7, C8** | **coppia senza `varieta'`, `varieta` fuori dall'insieme** |
| P1&ndash;P5 | proverbi: id, lati, forme letteraria e popolare, fonte |
| R1, R2 | regole sotto soglia, regole con un solo esempio |
| F1&ndash;F14 | IPA: id, forma, vuoto, simboli che non sono IPA, riferimento ignoto, attendibilita, `D` senza fonte, varieta' discordi dalla voce, due trascrizioni della stessa scrittura, varieta' con parole e senza suoni |
| A1&ndash;A10 | audio: id, file, `pubblicabile` senza consenso o senza licenza, varieta', contesto, livello CEFR, consenso senza voce dichiarata, file che non c'e' |
| **D1** | **id in `dati/da_verificare/` che compare anche nei dati attivi** |
| D2 | voce in attesa che si dichiara documentata (avviso) |
| M1&ndash;M4 | proposte IA: stato fuori dall'insieme, **campo `fonte` o `attendibilita D` su una proposta**, id citato inesistente, promozione che non esiste |

## 5. Le cose che non si fanno

- **Non si scrive una regola morfologica a mano.** Si mette la coppia nel
  corpus e si rilancia `impara`. Una regola senza esempi non ha accordo, e
  senza accordo non viene salvata.
- **Non si aggiunge una voce al glossario senza la fonte.** Se la fonte non si
  conosce, la voce non entra. Punto.
- **Non si tira fuori niente da `dati/da_verificare/` per usarlo.** Quel
  materiale e' nostro e non pubblicabile finche' la licenza della sua fonte
  non e' verificata. Il posto giusto di una voce con licazi non verificata e'
  quella fila, non il glossario: «lo metto su e poi se ne parla» e' il modo in
  cui una fonte non verificata finisce pubblicata.
- **Non si tira a indovinare.** Se una parola non si trova, il motore restituisce
  la parola di partenza e un buco, ed e' il comportamento giusto.
- **Non si registra audio senza consenso scritto.** E non si pubblica un brano
  senza consenso, nemmeno in un repository privato, nemmeno «solo per prova».
  Le tre condizioni sono `consenso`, `licenza` e `pubblicabile`, e servono
  tutte e tre: copiare un file in `web/audio/` **e' pubblicarlo**. Il
  consenso si firma prima di premere il pulsante, con
  `audio/modello-consenso.txt`, e la copia firmata non entra nel repository.
- **Non si scrive una trascrizione IPA come se fosse stata ascoltata.** Il
  campo `fonte` dice da dove viene la **scrittura**. Una trascrizione con
  `attendibilita: "D"` senza il nome di chi ha ascoltato, dove e quando e' una
  dichiarazione falsa, e il controllo **F9** la blocca.
- **Non si scrive una regola fonetica che nessuna fonte dichiari.** Dove le
  fonti non dicono niente (la `z` intervocalica, la `s` intervocalica) si
  lascia la nota e si resta `da_verificare`. E non si mette l'accento tonico
  se la fonte non lo marca.
- **Non si usa una voce ferrarese come se fosse un'altra varieta'.** Le cinque
  sono `cittadino`, `centrale`, `occidentale`, `orientale`, `transpadano`, e
  ogni voce porta la sua. Non si aggiunge una sesta: un elenco aperto
  finisce per voler dire qualunque cosa.
- **Non si scrive un significato moderno di testa.** `moderno` e' l'unico
  campo del glossario che puo' essere riempito senza aver guardato un
  dizionario, e per questo porta **sempre** con se' `fonte_moderno`: l'articolo
  da cui la definizione e' presa. Il controllo **G10** lo blocca. E vale
  anche per i sinonimi: si mettono quelli che la fonte dà, non quelli che
  verrebbero bene.

## 6. Le domande aperte, e dove stanno

Le questioni aperte di questo progetto sono poche, e nessuna e' bloccante per
lavorare:

1. ~~**Quante ore di registrazione servono**~~ **Risposto il 2026-10-03**, non
   chiuso: la stima e la sua aritmetica sono in `STIMA-AUDIO.md`. Il gioco ha
   **150 livelli di ferrarese** (i 900 sono la somma delle sei lingue) e serve
   circa un'ora di audio pulito ogni trenta livelli: **due ore e mezza per
   l'anno 1, quindici per tutta la progressione**. Il numero che non e' un
   numero e' **quante persone**: trenta, di cinque varietà diverse, che
   dicano di sì. La stima va rifatta con il primo dato vero.
2. ~~**Il glossario deve contenere solo il ferrarese cittadino o anche le
   altre varieta'.**~~ **Deciso il 2026-10-03: tutte e cinque, distinte.**
   `varieta` e' un campo obbligatorio del glossario e delle coppie (controlli
   G8, G9, C7, C8), `dati/varieta.json` tiene la tassonomia con i territori
   e la fonte, e quattro varieta' su cinque sono **vuote dichiarate**. La
   domanda che resta e' chi le riempi e come: comincia dall'occidentale, dove
   la differenza dal cittadino si sente di piu'.
3. **Chi approva le proposte del livello IA.** La destinazione esiste e
   funziona: `dati/proposte/proposte.jsonl`, con il modulo `proposte.py`, i
   controlli M1&ndash;M4 e il comando `proposte`. Resta aperto **chi** approva e
   con quale criterio: fino a che non e' deciso, la regola e' la piu'
   conservatrice possibile — una proposta resta `da rivedere` e nessuno la
   tocca.
4. **Chi verifica le trascrizioni IPA e con quale criterio di pagamento.** Le
   30 righe di `dati/fonetica.jsonl` sono tutte `I` e `da_verificare`: sono
   una lettura della grafia, non un ascolto. Passarle a `D` richiede un
   parlante, e il progetto non ha ancora deciso chi sia e come si faccia a
   registrare il fatto.
5. **Quale fonte dichiara che una parola e' antica.** La colonna «in italiano di
   oggi» risponde a «che cosa vuol dire *ardiglione*», ma non a «*ardiglione*
   e' una parola antica?». Wiktionary non marchia l'obsoleto: non esiste un
   template che lo dichiari, quindi non si puo' chiedere alla fonte e il modulo
   `raccolta/moderni.py` **non prova a indovinarlo con la grafia** — nessun
   segno ortografico distingue «ardiglione», che e' arcaico, da «cane», che
   non lo e'. La domanda che resta aperta e' se il progetto debba comprare un
   vocabolario che marchi l'obsoleto, o se basta la definizione.
6. **Le ventisei pagine sono giuste?** Il sito e' stato diviso perche' la
   pagina unica pesava 6,2 megabyte, e la divisione ha funzionato. Restano
   pero' due scelte che sono di Pietro e non dello script: `VOCI_PER_FETTA` in
   `costruisci_web.py` e' 500 e da li' dipende quanto pesa una pagina, e la
   ricerca guarda solo la fetta aperta. Se in classe si cercano parole sparse
   e si finisce a girare di fetta in fetta, il numero da cambiare e' il primo.
   Come si chiude il limite della ricerca — un indice delle parole senza la
   voce dentro — e' una scelta, perche' un indice del glossario intero
   riporterebbe il peso che si e' appena tolto.

7. **Un suono generato puo' passare per una voce?** La domanda ha gia' una
   risposta — no — ma il **come** merita di stare scritto, perche' e' il punto
   dove questo progetto rischia di mentire. Le due cartelle di suoni sono
   separate dal manifesto e dai **nomi dei file**, non dal contenuto: dentro
   un `wav` generato non c'e' la parola «espeak» e un controllo che la
   cercasse passerebbe per sempre senza guardare niente. I tre controlli che
   tengono la separazione sono **Y1d** (ogni suono dichiara che e' generato),
   **Y3b** (nessun nome di un suono generato dentro `web/audio/`) e **Y4**
   (nessun suono per una parola con un dubbio dichiarato). Se un giorno
   diventassero solo una convenzione scritta qui, il conto dei brani di persone
   vere diventerebbe falso e nessuno se ne accorgerebbe.

8. **Le parole funzionali entrano nel glossario o no.** Il glossario non ne
   ha quasi nessuna: fra 131 parole funzionali dell'elenco di `copertura.py`,
   38 ci sono e 93 passano invariate, quindi una frase come «il cane e' a casa»
   esce con due buchi. La domanda **non e'** «quale fonte le dichiara»: la
   fonte c'e' gia' ed e' la piu' forte del progetto. Il Ferri 1889 dichiara
   `Sòra` (sopra, pag. 386), `Fora` (fuori, pag. 150), `Còl` (col e collo,
   pag. 92), `Fra` (frate e fra/tra, pag. 151), `Con` (pag. 94), `In` (pag. 187),
   `Tra` (pag. 439), `La` (pag. 213), `Se` (pag. 364), `Che` (pag. 87) e `Un`
   (pag. 450). Sono state **scartate di proposito** dal generatore meccanico, e
   il motivo della scelta e' in `raccolta/costruisci_meccanico.py`: due motivi
   buoni (una voce per «La» fa scrivere «La porta» anche quando il soggetto e'
   un nome proprio, e le voci non distinguono le due lingue) e un costo
   dichiarato (una frase intera non e' traducibile).
   
   La domanda aperta e' quindi di **policy**, non di fonte: si tiene la scelta
   e si vive con il buco, oppure si ammette un elenco separato di forme
   funzionali con la pagina, sapendo che il motore non le tratta e che il
   gioco dovrebbe accettarle come riempimento. Finche' la risposta non c'e',
   il buco resta dichiarato e non si aggiunge niente a mano.

## 7. Il rapporto con «I cinque duchi»

Il gioco non incorpora il traduttore: il gioco usa i **dati**, cioe' il
glossario, le coppie e i brani. Il traduttore e' lo strumento con cui quei dati
si producono e si controllano.

Quindi la domanda giusta davanti a una modifica non e' «funziona?» ma «**il
gioco la puo' usare cosi'?**». Una traduzione con un buco non si puo' mettere
in un livello. Ecco perche' il motore calcola `da_pubblicare` e il perche'
quel campo esiste: e' il confine fra quello che si puo' mostrare a uno
studente e quello che va ancora verificato.

Per il resto vale `i-cinque-duchi/AGENTS.md`, che non si riassume qui.