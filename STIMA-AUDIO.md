---
titolo: Quante ore di registrazione servono
versione: 0.3
data: 2026-10-03
---

# Quante ore di registrazione servono

Questo file risponde alla domanda che `AGENTS.md` §6 dichiara aperta e che
`REGISTRO.md` chiama «la più importante». La risposta è **una stima con la sua
aritmetica in chiaro**, non una misura: nessuno ha ancora registrato niente, e
un numero che sembra misurato ma è coniettato è il tipo di numero che questo
progetto rifiuta.

Sei mesi fa la domanda giusta era «quante ore?». Dopo aver scritto il
protocollo di registrazione, la domanda giusta è un'altra: **quante
*persone*, e di che varietà**. Le ore sono la parte facile.

## Che cosa chiede il gioco, in numeri

I numeri vengono da `i-cinque-duchi/docs/videogioco-5-duchi-lingue.md` e non
da qui, e sono la base di tutta la stima:

- **900 livelli** in cinque anni, ma sono **sei lingue × 150 livelli**: al
  ferrarese ne toccano **150**, non 900. Confondere i due numeri gonfierebbe la
  stima di sei volte;
- ogni livello linguistico ha **nove componenti obbligatorie**, e la terza è il
  **testo autentico**. Per il ferrarese il documento è esplicito: «per il
  ferrarese significa *una trascrizione di un parlante*»;
- il livello 30 di ogni anno non è un argomento ma un **compito**, e per il
  ferrarese è «una vera ricerca sul dialetto, con registrazione e
  trascrizione»;
- i livelli 25–29 dell'anno 2 sono già dichiarati «testimonianze orali»,
  «variazione generazionale», «variazione geografica», «ascolto di parlanti».

Quindi: **150 livelli ferraresi, ciascuno con almeno un testo autentico che
deve essere una voce vera.** Non serve registrare 150 brani: serve registrare
abbastanza materiale perché ogni livello ne possa prendere un pezzo, e perché
le parole di quei brani finiscano nel glossario.

## L'aritmetica

Gli ipotesi sono dichiarati uno per uno, perché il numero vale quanto le sue
ipotesi.

| # | Ipotesi | Valore | Perché questo valore |
|---|---|---|---|
| H1 | parole nuove per livello ferrarese | 10 | un livello è un nucleo, non un capitolo: dieci parole con contesto sono gia' un livello |
| H2 | minuti di audio **pulito** per livello | 1 | il testo autentico si ascolta e si ri-ascolta; sopra i 2 minuti comincia a essere un brano, non un esercizio |
| H3 | minuti di parlato grezzo per minuto di audio pulito | 3 | le pause, i «eh», il cambio d'idea, il rumore: si tiene un terzo |
| H4 | parole nuove per sessione di 20 minuti | 120 | lista di parole a circa 10 secondi l'una (parola, pausa, ripetizione) |
| H5 | minuti di audio pulito per sessione di 20 minuti | 6 | H3 applicato, e in una stanza tranquilla il grezzo tiene |
| H6 | ore per trascrivere un'ora di audio pulito | 4 | in italiano standard, con le forme dialettali da capire e la punteggiatura da scegliere: è il lavoro vero |
| H7 | minuti per verificare all'ore la trascrizione IPA di una parola | 10 | la parola, due volte, la domanda «come si dice davvero?»; sotto i 10 minuti si risponde «come mi sembra» |

Da questi, i numeri:

```
parole nuove per tutta la progressione     150 × 10            = 1 500
audio pulito per tutta la progressione     150 × 1  min         ≈ 150  min ≈ 2 h 30
audio grezzo da registrare                 150 × 3  min         ≈ 7 h 30
ore di trascrizione                        7 h 30 × 4            ≈ 30 ore
ore di verifica IPA (1 500 parole)         1 500 × 10 s         ≈ 4 ore
```

## I tre scenari

Non un numero solo: la differenza fra «il minimo che si può usare» e «il
progetto finito» è quasi tutta una decisione di didattica, non una misura.

| Scenario | Livelli | Persone | Sessioni | Audio grezzo | Trascrizione |
|---|---|---|---|---|---|
| **Minimo utile** — solo l'anno 1 | 30 | 5 | 5 | 2 h 30 | 10 ore |
| **Anno 1 e 2** | 60 | 10 | 10 | 5 ore | 20 ore |
| **Progressione intera** | 150 | 25–30 | 25–30 | 12 h 30 – 15 ore | 50 – 60 ore |

**Il minimo utile è la prima riga, e questa è la notizia buona**: trenta
livelli si coprono con cinque persone e due ore e mezza di registrazione. Il
gioco ha un anno di contenuti ferraresi funzionabili molto prima di aver tutto.

**La progressione intera resta sotto le quindici ore di registrazione**, e
sono poche. Il problema non è il tempo di registrarsi: è trovare trenta
persone che parlino ferrarese di cui cinque varietà diverse, che diano il
permesso, e che si lascino registrare da uno studente di quindici anni.

## Il vincolo vero: le persone, non le ore

Il glossario ha oggi **24 voci** e la progressione ne vuole **1 500**: un
fattore sessanta. Nessuna ora di registrazione produce 1 500 voci, e nessun
modello linguistico le produce: il limite è che **le voci ferraresi esistono
soprattutto nella memoria di persone che hanno settant'anni e pochi minuti
liberi**. Per questo nel progetto ci sono due cose che non si possono
comprare e non si possono generare:

1. **la varietà.** Quattro su cinque sono vuote. Il primo posto dove andare è
   l'occidentale, dove la differenza dal cittadino si sente di più e dove
   chiunque del posto lo sa;
2. **il consenso.** Un'ora di registrazione senza consenso scritto non è un
   dato: è una persona di cui si è serviti.

## La resa di una sessione, che è il numero che conta davvero

Se una sessione di 20 minuti con una persona rende, in modo verificabile:

- **6 minuti** di audio pulito;
- **120 parole** nuove, di cui forse 40 recuperabili da un vocabolario e 80
  che richiedono di essere sentite da un secondo parlante;
- **2 varietà confrontate** nella stessa frase, che è l'unico modo per sapere
  che una parola è di Bondeno e non di Ferrara;
- **una trascrizione IPA** verificata da qualcuno che lo dice ad alta voce.

Allora il progetto non ha un problema di ore: ha un problema di **quarta
sessione**. Il percorso che porta a un anno di gioco è: cinque persone, una
settimana, `audio/SESSIONE.md` seguito alla lettera.

## Che cosa questo file non fa

Non promette che i quindici minuti per parola siano giusti: sono un'ipotesi,
e se la verifica IPA richiederà mezz'ora per parola il totale raddoppia e
diventa un'altra domanda. Non stima quante persone si trovino, che è un fatto e
non una stima: fin qui non è stato trovato **nessun** corpus di parlato
spontaneo ferrarese consultabile (`dati/fonti.json`, S009).

E non chiude la domanda. La chiude solo chi ha registrato la prima sessione e
sa quanto tempo ci è voluto davvero: il primo dato vero **sostituisce** questa
stima, e la stima va nel cassetto con la sua data.