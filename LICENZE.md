---
titolo: Licenze e attribuzioni
versione: 0.2
data: 2026-10-03
---

# Licenze

## Codice

MIT. Il codice di `sorgenti/` e di `prove/` puo' essere ripreso, modificato e
usato, anche dentro un altro progetto, anche commerciale. Un progetto che
insegna una lingua che sta morendo non ha interesse a trattenere il codice
che lo fa funzionare.

Il testo della licenza e' nel file `LICENSE` in radice, **senza commenti**: e'
il testo del MIT, nient'altro, e GitHub lo riconosce e lo mostra accanto al
codice. Vale per `sorgenti/`, `prove/`, `web/` e `.github/`; **non** vale per
i dati, che hanno licenze diverse e le dichiarano una per una.

Quel che il `LICENSE` non puo' dire, perche' non e' una licenza ma una
premessa, e' qui: **un file solo per i dati non esisterebbe comunque.** I dati
verranno da Biondelli (pubblico dominio), da Wikipedia e da Wiktionary
(CC BY-SA 4.0) e da una traduzione dialettale anonima la cui licenza non
e' ancora verificata. Per quest'ultima i dati non sono pubblicati e stanno in
`dati/da_verificare/`.

## Dati

**La licenza e' per voce, e la dichiara il campo `fonte` di ogni riga.**

Non e' una licenza unica per il glossario, e il motivo e' che i dati vengono
da fonti diverse con diritti diversi. Chi scarica il repository riceve dati
con licenze diverse dentro lo stesso file, e deve saperlo dalla riga che sta
leggendo.

Il significato moderno fa un passo in piu': la sua fonte non e' il campo
`fonte`, che dice da dove viene **la voce ferrarese**, ma il campo
`fonte_moderno`, che dice da dove viene **la spiegazione** — ed e' un
indirizzo, non un codice, perche' qui la fonte e' una pagina e non un libro.
Una riga con `moderno` e senza `fonte_moderno` non entra: e' il controllo
**G10**, e senza di esso questa sarebbe l'unica colonna del progetto che puo'
inventare.

Le fonti attualmente nel registro (`dati/fonti.json`):

| Fonte | Licenza | Stato |
|---|---|---|
| Bernardino Biondelli, *Saggio sui dialetti gallo-italici*, 1853 | pubblico dominio | acquisita |
| «Dialetto ferrarese», Wikipedia in italiano | CC BY-SA 4.0 | acquisita |
| — di cui la **tassonomia delle cinque varieta'**, in `dati/varieta.json` | CC BY-SA 4.0 | acquisita |
| **Significati moderni e sinonimi**, da Wiktionary in italiano | CC BY-SA 4.0 | acquisita |
| Traduzione ferrarese della Dichiarazione universale dei diritti umani, art. 1 | **da verificare** | acquisita |
| Luigi Ferri (1826-1895), *Vocabolario ferrarese-italiano*, 1889 | pubblico dominio | acquisita |
| Francesco Nannini, *Vocabolario portatile ferrarese-italiano*, 1805 | pubblico dominio | esaminata |
| *Vocabolario domestico ferrarese-italiano*, copia su blog | pubblico dominio dichiarato dalla copia, non dall'autore | esaminata |
| «Scrìvar e l'èàr al frarés», opuscolo su Aruba | nessuna dichiarata | **esclusa** |
| Vocabolario online di Roberto Bigoni | da chiedere | reperto |
| Portale dei dialetti della Regione Emilia-Romagna | da verificare | reperto |
| Glossario di uno stabilimento di Ferrara | nessuna dichiarata | **esclusa** |
| Corpus di parlato spontaneo ferrarese | **non esiste** | esclusa |

## Le due regole che ne derivano

1. **Solo lo stato `acquisita` alimenta il glossario.** Una fonte `reperto` o
   `esaminata` puo' essere citata in una nota, non puo' diventare una voce.
2. **Una fonte con licenza non verificata non si pubblica.** Questo vale
   oggi per la traduzione della Dichiarazione (S003): e' una fonte
   utilissima, e finche' la sua provenienza non e' stata rintracciata le voci
   e le coppie che ne derivano stanno in `dati/da_verificare/`, fuori dai
   dati che il motore usa e dalla pagina. Il repository contiene quel
   materiale — e' dichiarato qui, in `dati/fonti.json` e in
   `dati/da_verificare/README.md` — ma non lo pubblica, e il controllo **D1**
   verifica che non venga usato per errore.

   Nota bene la differenza con la regola 1: S003 e' `acquisita` (il testo
   l'abbiamo, e sappiamo dove l'abbiamo preso) ma ha
   `licenza_verificata: false`. Essere in `acquisita` non vuol dire «libero»,
   vuol dire «dentro, con la provenienza dichiarata».

## Audio e immagini

Non ci sono ancora. Quando ci saranno:

- **ogni brano porta la licenza nel manifest**, e la licenza non e' quella del
  file: e' quella che la persona che ha parlato ha accettato;
- **nessun brano senza consenso scritto**, nemmeno in un repository privato;
- **copiare un file in `web/audio/` e' pubblicarlo**: la copia avviene solo se
  `consenso`, `licenza` e `pubblicabile` ci sono tutti e tre;
- **i dati degli studenti non entrano**, e con loro le voci dei compagni di
  classe;
- per i minori il consenso e' di chi esercita la responsabilita' e va messo per
  iscritto.

## Le trascrizioni IPA

Le 30 righe di `dati/fonetica.jsonl` sono **opere nostre**, non materiale di
terzi: sono la lettura della grafia che le fonti già nel registro scrivono, e
non copiano niente. La licenza e' quindi quella del progetto e non c'e' nessuna
attribuzione da fare a terzi.

Una cosa pero' va dichiarata, perche' riguarda chi potrebbe usarle per
insegnare: **nessuna di quelle 28 trascrizioni e' stata verificata da un
parlante.** Sono tutte `attendibilita: "I"`, che vuol dire «l'ho ricavato da
una grafia, non l'ho ascoltato». Un'insegnante che le usa come riferimento di
pronuncia deve saperlo, quindi la pagina lo dichiara accanto a ogni
trascrizione e non in una nota a pie' di pagina.

Passare a `D` non e' un problema di licenza ma di verita': serve una persona
che dica «si' e' cosi'», con nome, luogo e data nel campo `fonte`.

## Le proposte del livello IA

Le risposte del modello in `dati/proposte/` sono **opere nostre** e non hanno
licenza propria: sono cio' che esce da un servizio, e vengono tenute in
chiaro perche' una risposta di un modello che non si puo' riprendere come
fonte e' inutile. Il punto della cartella non e' la licenza: e' che sono
**proposte**, e i controlli M1&ndash;M4 impediscono che una di loro si porti
dentro un campo `fonte` e diventi, senza nessuna decisione, una voce del
glossario.

## Perche' tutto questo per ventisei voci

Perche' il giorno in cui il glossario avra' tremila voci, nessuno ricordera'
quali avevano una fonte, quali no, e in quale varieta'. La regola va scritta
adesso, quando fa scorrere le dita, non dopo.

Un glossario di una lingua minoritaria che mescola fatti e opinioni smette di
essere consultabile da chiunque, perche' non si sa piu' a chi chiedere. E a
quel punto il lavoro non e' perso, ma e' inutilizzabile: che e' il modo peggiore
in cui il lavoro di un progetto puo' finire.