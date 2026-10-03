---
titolo: Raccolta dei materiali ferraresi
versione: 0.2
data: 2026-10-03
autore: progetto «I cinque duchi»
---

# Dove si accumulano vocabolari, testi e registrazioni

Questa e' la pagina a cui tornare ogni volta che si trova qualcosa di
ferrarese. Risponde a sette domande, e le sette risposte sono in
corrispondenza con le cartelle di `dati/`.

## La regola che precede tutte

**Ogni cosa che entra nel progetto porta con se' due cose: da dove viene e
se si puo' usare.** Una terza, facoltativa ma importante: chi l'ha messa.

Il motivo e' gia' noto in «I cinque duchi»: una ricerca che restituisce un
file non ha trovato la cosa che cercavi. Nel caso del ferrarese la cosa e'
peggio, perche' la maggior parte del materiale che si trova online e' o un
elenco di un appassionato senza fonte, o una copia di un vocabolario
dell'Ottocento senza crediti. Entrambi sembrano un glossario e non lo sono.
Un glossario senza fonte non e' un glossario e' un'opinione, e un'opinione
in un gioco didattico diventa una nota che si legge come un fatto.

## Le sette cartelle

| Cartella | Cosa contiene | Chi decide |
|---|---|---|
| `dati/glossario.jsonl` | **Le parole**, una per riga, con la fonte e la varieta' | Pietro, o chi dichiara la fonte |
| `dati/coppie.jsonl` | **Le frasi** nelle due lingue, con la fonte e la varieta' | chi le ha raccolte, verificando la fonte |
| `dati/proverbi.jsonl` | **I proverbi**, con forma letteraria e popolare | chi li ha sentiti, dichiarando dove |
| `dati/varieta.json` | **Le cinque varieta'** e i loro territori | chi tiene la fonte delle varieta' |
| `dati/fonetica.jsonl` | **Le trascrizioni IPA**, con il sistema dichiarato | chi ha ascoltato la parola |
| `dati/audio.jsonl` + `audio/` | **Le voci**, con consenso | la persona che ha parlato, o chi esercita la responsabilita' |

E ci sono due registri che non sono contenuti ma che li tengono in ordine:

- **`dati/fonti.json`** dice che cosa si puo' usare e che cosa no. Una fonte
  esiste (`reperto`), e' stata aperta (`esaminata`), e' nel repository con la
  licenza verificata (`acquisita`), oppure e' esclusa e il motivo e' scritto.
  **Solo `acquisita` alimenta il glossario.**
- **`dati/audio.jsonl`** e' il manifest dei brani: senza consenso scritto il
  brano non si pubblica, e non si pubblica neanche nel gioco.

## La varieta' va decisa prima della fonte

Una voce nuova senza `varieta` **non entra**: il controllo **G8** lo blocca,
ed e' un blocco giusto, perche' una parola che non si sa a chi serve e' una
parola che si rischia di dare al posto sbagliato.

Gli attuali 26 voci sono tutte `cittadino`, perche' e' l'unica varieta' che
le fonti disponibili documentano davvero: non e' che le altre non esistano, e'
che le fonti non le raggiungono. Le altre quattro sono **vuote dichiarate** e
`python3 -m traduttore.cli varieta` le stampa come `VUOTA`.

Il lavoro che le riempi e' diverso da quello delle parole nuove, e forse piu'
facile: non serve un vocabolario dell'Ottocento, serve **una persona del
posto**. Per cominciare dall'occidentale (Bondeno, Vigarano Mainarda,
Sermide e Felonica, parti di Terre del Reno e Poggio Renatico), che e' la
varieta' in cui la differenza dal cittadino si sente di piu' e quindi la piu'
divertente da registrare.

## 1. I vocabolari stampati

Sono la fonte **piu' preziosa e la piu' ignorata**, e il motivo e' che sono in
pubblico dominio dal Novecento e nessuno li ha digitalizzati.

I due da cominciare, gia' identificati in `dati/fonti.json`:

- **Luigi Ferri, *Vocabolario ferrarese-italiano*, 1885.** Scaricabile da
  archive.org. Intero in pubblico dominio (l'autore e' morto nel 1895). E'
  un vocabolario di fine Ottocento, quindi le sue forme sono **contemporanee
  a chi le ha raccolte**: e' il problema dei vocabolari moderni non si pone.
- **Francesco Nannini, *Vocabolario portatile ferrarese-italiano*.** Secondo
  vocabolario della stessa epoca. Serve come confronto: dove Ferri e Nannini
  concordano la voce e' solida, dove discordano c'e' una varieta' e va
  dichiarata come tale.

**Il lavoro che manca e' la trascrizione.** Le copie su archive.org sono
testo-immagine, quindi vanno digitate. E' la parte piu' noiosa e piu'
 importante del progetto, e si puo' dividere: una pagina per volta, con un
volontario per volta, in un repository pubblico, e ogni pagina con il nome
di chi l'ha fatta.

Come si riempie il glossario da un vocabolario:

```json
{"id":"V0312","varieta":"cittadino","ferrarese":"…","italiano":"…","campo":"verbo",
 "note":"voce 47 del vocabolario; il libro dà anche la forma breve «…»",
 "fonte":"Ferri, Vocabolario ferrarese-italiano, 1885, p. 47",
 "attendibilita":"D","da_verificare":false}
```

Se il vocabolario distingue le varieta' interne (e Ferri potrebbe farlo, per
esempio con una voce di Bondeno), la voce va messa **due volte**, con due id e
due `varieta`, e non una volta con due varieta' dentro: una riga sola che
dichiara «cittadino e occidentale» non dice quale delle due forme si scrive
come nel libro.

Il campo `fonte` **deve** avere l'edizione e la pagina. `attendibilita: D`
senza pagina non passa il controllo, e il controllo esiste perche' una voce
senza pagina non si puo' ritoccare fra vent'anni.

## 2. I testi scritti

Dove si trovano, in ordine di valore:

1. **Wikisource**, per i testi in pubblico dominio. Il progetto conosce gia'
   la lezione: il testo vive nella zona `Pagina:` e non nei titoli dei canti,
   e va scaricato in lotti. Lo stesso vale per un vocabolario antico.
2. **Internet Archive**, che ospita quasi tutti i vocabolari e le raccolte
   ottocentesche. La verifica di pubblico dominio si fa guardando la data di
   morte dell'autore: sotto i 70 anni dalla morte in Italia l'opera non e'
   libera, e questa e' la ragione per cui un testo del 1928 non si puo' usare
   come se fosse del 1853.
3. **La BEIC e le biblioteche digitali** per i fondi ferraresi stampati.
4. **Le voci locali**: gruppi, podcast, televisione locale. Qui la raccolta
   non e' scaricare: e' chiedere. Vedi il punto 4.

Un testo parallelo vale piu' di un testo solo, e le frasi parallele sono la
seconda cosa da costruire dopo le parole. Il modello da cui partire esiste
gia': l'articolo 1 della Dichiarazione universale dei diritti umani tradotto
in ferrarese, che e' in `dati/coppie.jsonl` e permette di controllare
parola per parola senza sapere il ferrarese, perche' il testo italiano si
conosce.

## 3. Il portale della Regione Emilia-Romagna

`dati/fonti.json` segnala la pagina dei dialetti
(`patrimonioculturale.regione.emilia-romagna.it/dialetti/risorse-online`),
che annuncia **testi e audio di autori e autrici nei dialetti del territorio
ferrarese**, fra cui Floriana Guidetti con «Storie dei nostri dialetti».

Non e' ancora nel repository perche' la pagina non ha reso testo leggibile
nella sede in cui e' stata cercata. Va aperta a mano. Una richiesta che non
arriva **non** e' una risposta negativa: e' una richiesta che non e' arrivata.

Se dentro ci sono registrazioni, la domanda prima non e' «sono in pubblico
dominio» ma **«di chi sono le voci e hanno acconsentito»**. Un archivio
sonoro regionale puo' avere il diritto di ascolto e non quello di
ripubblicare, e con i minori il consenso e' di chi esercita la responsabilita'.

## 4. Le voci: la parte lenta e quella che conta

Il gioco ha bisogno di **ascolto** e di **parlato**, e per il ferrarese non
esiste un modello vocale, non esiste un riconoscimento del parlato
affidabile, e non esiste un corpus di parlato spontaneo consultabile. L'unica
strada e' registrare persone, e farlo bene.

**Come si registra.** Telefono, stanza tranquilla, il parlante il piu' vicino
possibile, mezz'ora di conversazione libera (non una lista di parole: il
parlato spontaneo e' quello che serve e l'unico che non si sa produrre). Poi
una lista di venti parole, perche' la lista allinea l'audio al glossario.
`ffmpeg -i grezzo.m4a -ac 1 -ar 44100 -c:a libmp3lame -b:a 64k brano.mp3`
basta ed e' abbondante.

**Le quattro cose che ogni brano deve dichiarare**, in `dati/audio.jsonl`:

| Campo | Perche' |
|---|---|
| `voce` | chi ha parlato, e con quale nome vuole essere citato |
| `luogo` | dove e in che anno: il ferrarese cambia di paese in paese |
| `varieta` | cittadino, centrale, occidentale, orientale, transpadano. Una voce cittadina non insegna il ferrarese di Bondeno, e dirlo e' l'unico modo per non confonderli |
| `consenso` | `scritto` o `verbale`. Se e' vuoto, il brano non si pubblica |

**I dati degli studenti non entrano nel repository.** Vale per «I cinque
duchi» e vale qui: le voci dei compagni di classe restano fuori. Se un
ragazzo vuole contribuire, la registrazione si tiene in locale e nel
repository finisce solo il testo trascritto.

## 5. Le trascrizioni IPA: la parte che si puo' fare subito

Mentre l'audio non si muove, **la pronuncia si puo' scrivere adesso**, e non
serve nessun permesso: una trascrizione IPA non e' una registrazione, e' una
lettura della grafia dichiarata.

`dati/fonetica.jsonl` ha gia' 30 righe e le regole del sistema sono
dichiarate nell'intestazione del file. Le tre cose da non fare:

1. **non scrivere `attendibilita: "D"` senza aver ascoltato.** Il `D` vuol
   dire che qualcuno ha detto «si' e' cosi'», e il campo `fonte` deve dire
   chi, dove e quando. Il controllo **F9** lo blocca;
2. **non scrivere una regola fonetica che nessuna fonte dichiari.** La `z`
   intervocalica e la `s` intervocalica sono il punto cieco di tutte le fonti
   disponibili: finche' qualcuno non le verifica, la nota resta e la riga
   resta `da_verificare`;
3. **non mettere l'accento tonico se la fonte non lo marca.** `brisa` e
   `pan` non hanno accento in Wikipedia, e quindi la trascrizione non ce lo
   mette: dichiarare un accento che la fonte non dichiara e' l'errore piu'
   economico da commettere in un file di 30 righe.

Quello che ci vuole davvero, e che e' la cosa piu' preziosa che si possa
aggiungere a questo progetto nelle prossime settimane: **una mezz'ora con una
persona che parla ferrarese e un minuto di registrazione per voce**. Il primo
passaggio e' scrivere `confermato da [nome], [paese], 2026` nel campo
`fonte`, cambiare `I` in `D` e `da_verificare` in `false`. Il secondo e'
il brano audio, che ha bisogno anche del consenso.

**Il buco grande e dichiarato:** un corpus di parlato spontaneo ferrarese non
esiste e non si scarica da nessuna parte (`dati/fonti.json`, S009). Non si
puo' fingere che ci sia e non si puo' costruire per download. Si costruisce
registrando.

## Come si aggiunge qualcosa, in pratica

1. **Una parola** → una riga in `dati/glossario.jsonl`, con `id` nuovo
   (`V0312`, mai riutilizzato), la `varieta`, la fonte, e `attendibilita`
   onesto. Poi `python3 -m traduttore.cli verifica`.
2. **Una frase** → una riga in `dati/coppie.jsonl`, con la `varieta`. Se la
   frase e' in italiano e non ha un equivalente ferrarese, si lascia il campo
   vuoto: e' un vuoto dichiarato, che e' informazione.
3. **Un proverbio** → una riga in `dati/proverbi.jsonl`, con `letterario`,
   `popolare` e `fonte`. Se le due forme coincidono, il controllo P4 lo dice:
   vuol dire che una delle due e' sbagliata, e non si sa quale.
4. **Una trascrizione** → una riga in `dati/fonetica.jsonl`, con `riferimento`
   (la voce), `forma` (come la scrive la fonte), `ipa`, `varieta`, la fonte
   **della scrittura** e la nota sul dubbio. Con `attendibilita: "I"` e
   `da_verificare: true` va bene cosi' com'e'.
5. **Una voce** → il file in `audio/`, la riga in `dati/audio.jsonl`, e il
   consenso da parte. Senza consenso la riga c'e' ma `pubblicabile` e'
   `false` per sempre.
6. **Una varieta' nuova** → non si aggiunge: i cinque codici sono chiusi e
   sono quelli della fonte dichiarata. Quello che si aggiunge sono le voci di
   una varieta' gia' esistente.
7. **Una fonte nuova** → una riga in `dati/fonti.json` con lo stato
   `reperto`. Non nel glossario: nel registro. Il glossario riceve solo
   quello che e' `acquisita`.

Dopo aver toccato i dati:

```bash
export PYTHONPATH=sorgenti
python3 -m traduttore.cli verifica     # i controlli
python3 -m traduttore.cli impara       # rigenera le regole
python3 prove/test_traduttore.py       # i test
python3 -m traduttore.cli web          # rigenera la pagina
```

E non si fa nessun commit senza che i quattro comandi di sopra escano senza
errori. Per la parte audio e la fonetica si guarda anche:

```bash
python3 -m traduttore.cli varieta     # le cinque, e quante voci ha ciascuna
python3 -m traduttore.cli pronuncia --tutte   # le trascrizioni e il loro stato
python3 -m traduttore.cli audio       # i brani e quelli pubblicabili
```

## L'ordine in cui conviene procedere

1. **Ferri 1885**, pagina per pagina. E' la fonte piu' grande e piu' facile da
   usare, e senza il vocabolario non c'e' glossario.
2. **Nannini**, per il confronto e per le varieta'.
3. **Le frasi** del quotidiano, raccolte parlando con chi lo parla ancora.
4. **L'audio**, che richiede tempo e persone, e va avviato per primo fra
   tutti perche' e' quello che non si puo' accelerare.
5. **Una mezz'ora con un parlante** per portare le prime trascrizioni IPA da
   `I` a `D`. Costa poco ed e' la cosa che rende vera la parte fonetica.

Il primo, il quarto e il quinto si possono fare in parallelo, e il quarto e'
quello che manca di piu'.