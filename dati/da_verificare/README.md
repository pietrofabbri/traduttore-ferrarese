# `dati/da_verificare/` — i dati che il progetto non usa (per ora)

Questa cartella è il posto dove finisce **il materiale che è buono ma non ha
ancora il diritto di essere pubblicato**. Non è un cestino e non è un
archivio: è una fila d'attesa dichiarata.

## Perché esiste

Una fonte entra nel glossario solo se ha la licenza verificata. Ma durante la
ricerca si trovano cose che servono e che hanno un problema solo di
provenienza: il testo c'è, la traduzione parallela c'è, e non si sa di chi è.

Fanno parte di questa cartella le voci e le coppie che vengono dalla
**traduzione ferrarese dell'articolo 1 della Dichiarazione universale dei
diritti umani** (`dati/fonti.json`, S003): l'autore non è identificato, la
fonte primaria non è stata rintracciata, e quindi la licenza è «da
verificare».

Finché è qui dentro, il progetto:

- **non le usa**: il glossario attivo non le contiene, il motore non le
  vede, la pagina non le mostra;
- **non le dimentica**: sono qui, con la stessa identità (`V0023`, `V0024`,
  `F0006`, `F0007`, `T0027`, `T0028`), e tornano nel glossario attivo senza
  perdere la fonte né il resto dei metadati;
- **non finge**: `dati/fonti.json` dice ancora che la fonte è `acquisita` con
  `licenza_verificata: false`, che è la verità.

Il controllo **D1** fallisce la CI se un id di questa cartella compare anche
nel glossario attivo: una voce in attesa che si usa è il modo più economico
di pubblicare dati di provenienza ignota.

## Quando escono

Quando qualcuno rintraccia la fonte primaria — un dialettario, un archivio, il
giornale o la rivista in cui la traduzione è comparsa — si scrive il nome, si
verifica la licenza, si cambia `licenza_verificata` in `dati/fonti.json` e le
righe si spostano nei file attivi così come sono, senza riscriverle.

Il caso più probabile non è una scoperta ma una constatazione: se la
traduzione si rivela anonima e non rintracciabile, **non esce e resta qui**,
e il progetto continua senza. Un vuoto dichiarato costa meno di una fonte
copiata.

## Che cosa non si fa qui dentro

- non si aggiunge una voce **nuova** in questa cartella: qui dentro finisce
  solo materiale già raccolto con un problema di licenza;
- non si «migliora» una riga per renderla pubblicabile: il lavoro di verifica
  è sulla fonte, non sulla riga;
- non si cita questa cartella come fonte di una voce del glossario attivo.