# `dati/campioni/` — la verifica a campione

Questa cartella risponde a una domanda sola: **quanto ci si può fidare di una
fonte del glossario?** Non verificando ogni voce, ma giudicandone poche,
estratte a caso, e ricavandone un tasso di errore con il suo intervallo.

## Perché esiste

Il 2026-10-08 il titolare del progetto ha dichiarato due cose che vanno tenute
insieme (`AGENTS.md` §6, punto 11):

1. il progetto deve diventare **il punto di accesso a tutta la conoscenza
   disponibile sul ferrarese**;
2. la verifica umana deve essere **a campione e la minima possibile**.

Il glossario ha 17370 voci e 17139 sono `attendibilita: I` (trascritte da una
fonte, mai controllate da un parlante). Controllarle una per una non
succederà. Quello che si può sapere con poco lavoro è *quante* ne sbaglia
ciascuna fonte: per questo basta un campione.

## I due file

| File | Che cosa contiene | Chi lo scrive |
|---|---|---|
| `estrazioni.json` | le voci estratte a caso, per fonte, con il **seme** e la dimensione della fonte al momento dell'estrazione | il comando `campione estrai`, mai a mano |
| `giudizi.jsonl` | un giudizio per riga: quale voce, quale esito, chi, quando | il comando `campione importa`, dalle righe prodotte dalla pagina |

Un'estrazione:

```json
{"id": "E0001", "fonte": "S004", "n": 20, "seme": "2026-10-29-S004-1",
 "data": "2026-10-29", "popolazione": 10363, "motivo": "...",
 "voci": ["V0038", "V0416", "..."]}
```

Un giudizio:

```json
{"id": "K0001", "estrazione": "E0001", "voce": "V0038", "esito": "si_dice",
 "chi": "Pietro Fabbri, parlante nativo (cittadino)", "data": "2026-10-30",
 "come_si_dice": "facoltativo: la forma che il parlante usa", "nota": "facoltativa"}
```

## Che cosa si chiede a chi giudica

Una domanda da parlante, non da filologo: **la voce si dice così, con questo
significato?** Non serve aprire il libro. Gli esiti sono tre:

| Esito | Che cosa vuol dire | Conta nel tasso di errore? |
|---|---|---|
| `si_dice` | è ferrarese e vuol dire quello che il glossario dice. Una grafia diversa non è un errore: si scrive in `come_si_dice` | sì, come giusta |
| `non_si_dice` | la forma o il significato sono sbagliati | sì, come errata |
| `non_la_conosco` | il parlante non la conosce | **no**: non è un giudizio sulla voce. È però il primo dato che il progetto ha su quali parole non si usano più |

## Come si fa, passo per passo

1. **Estrarre** (chi tiene il repository):

   ```bash
   export PYTHONPATH=sorgenti
   python3 -m traduttore.cli campione estrai --fonte S004 --n 20 --seme 2026-10-29-S004-1
   python3 -m traduttore.cli web        # la pagina mostra le voci nuove
   ```

   Il seme si sceglie *prima* di vedere le voci, e si scrive. Di default è la
   data, la fonte e un numero d'ordine.
2. **Giudicare** (il parlante): aprire `web/verifica.html`, che si apre anche dal
   telefono e anche senza rete. Scrivere il proprio nome in alto, scegliere
   un esito per ogni voce, premere «Copia le righe» o «Scarica». I progressi
   restano nel browser, quindi si può fare un pezzo alla volta.
3. **Importare** (chi tiene il repository), con le righe ricevute anche dentro
   un messaggio, perché le righe che non cominciano con `{` si saltano:

   ```bash
   python3 -m traduttore.cli campione importa giudizi.jsonl
   python3 -m traduttore.cli campione   # il tasso per fonte
   python3 -m traduttore.cli verifica   # i controlli K1–K9
   python3 -m traduttore.cli web
   ```

   Una riga su una voce non estratta viene scartata. Una riga già importata con
   lo stesso esito non si importa due volte.

## Come si legge il numero

Per ogni fonte: errate / (giuste + errate), con l'**intervallo di Wilson al 95%**.
Le estrazioni della stessa fonte si sommano. Con venti voci l'intervallo è
largo, e va letto così: zero errori su venti vuol dire che la fonte può
sbagliare **fino a circa il 16%**, non che non sbaglia mai. Per stringerlo si fa
un'altra estrazione della stessa fonte con un seme nuovo. A titolo di misura:
con sessanta voci e zero errori il massimo scende a circa il 6%.

## I controlli (`verifica`)

| Codice | Che cosa blocca | Gravità |
|---|---|---|
| K1 | estrazione senza id o con id ripetuto | errore |
| K2 | fonte non dichiarata in `fonti.json`, seme vuoto, `n` diverso dalle voci elencate | errore |
| K3 | voce estratta che non esiste nel glossario | errore |
| K4 | voce estratta che non è della fonte dell'estrazione | errore |
| **K5** | **giudizio su una voce che l'estrazione non contiene**: è il controllo che impedisce di «verificare a campione» le voci che si sa già essere giuste | errore |
| K6 | esito fuori dai tre | errore |
| K7 | giudizio senza chi o senza data | errore |
| K8 | due giudizi sulla stessa voce: vale l'ultimo, ma la storia si vede | avviso |
| K9 | l'estrazione, ripetuta col suo seme, non dà le stesse voci (solo se la fonte non è cambiata di dimensione) | avviso |

## Che cosa questa cartella non fa

- **Non cambia il glossario.** Una voce giudicata `si_dice` resta
  `attendibilita: I`. Se e come un giudizio debba promuovere una voce è una
  decisione aperta (`AGENTS.md` §6, punto 11), non un effetto collaterale.
- **Non controlla la fedeltà al libro.** Il giudizio è da parlante: una voce
  trascritta male dal Ferri ma giusta come ferrarese risulta `si_dice`. La
  fedeltà alla fonte si controlla aprendo il libro, ed è un'altra misura.
- **Non misura le varietà che il parlante non parla.** Chi parla il ferrarese
  di città giudica il cittadino. Le altre quattro varietà sono vuote, e una
  voce di Bondeno giudicata da Ferrara città direbbe poco.

## Come si attribuisce una voce alla sua fonte

Le voci non hanno un campo con il codice della fonte: hanno il testo della
fonte. `sorgenti/traduttore/campioni.py` (`fonte_della_voce`) cerca prima il
codice fra parentesi, per esempio «(S006)», e poi l'autore o l'indirizzo
(Ferri → S004, Biondelli → S001, Wikipedia «Dialetto ferrarese» → S002,
Nannini → S005). Un test verifica che nessuna voce resti senza fonte.
