# Le verifiche dei parlanti

Una voce del glossario passa da `I` (letta da una fonte) a `D` (documentata) in due
modi soli: qualcuno la confronta con il libro alla pagina citata, oppure **un
parlante ferrarese dichiara che è corretta**. Questo file registra il secondo modo.

`verifiche.jsonl` ha una riga per voce:

| campo | che cosa |
|---|---|
| `voce` | l'id della voce in `dati/glossario.jsonl` |
| `esito` | `corretta` |
| `chi` | il nome del parlante |
| `fonte` | la fonte del registro che lo descrive (`S022` per il titolare) |
| `varieta` | la varietà che parla |
| `data` | il giorno della dichiarazione |
| `insieme` | l'insieme su cui ha dichiarato (`conferme`, `S024`, …) |
| `come` | come l'ha detto, con le sue parole |

La voce verificata porta nel glossario `attendibilita: "D"`, `da_verificare: false`
e `verificata: "data, chi (fonte, varietà)"`. Le scrive
`raccolta/registra_verifica.py`; a mano non si scrive niente.

**Una verifica in blocco è dichiarata come tale.** Il 2026-11-09 il titolare, Pietro
Fabbri, parlante del ferrarese cittadino, ha dichiarato corrette due insiemi: le 21
voci di FEdetails (S024) e le voci confermate da due fonti indipendenti (3151, di
cui 3 erano già fra le prime). La riga dice `insieme` e riporta la frase: chi legge
sa che non è un controllo fatto voce per voce in una data diversa, ma una
dichiarazione su un insieme fissato quel giorno.

Se una voce verificata si rivela sbagliata, si corregge con il pulsante «Invia»: la
correzione entra come voce che corregge e viene prima di lei.
