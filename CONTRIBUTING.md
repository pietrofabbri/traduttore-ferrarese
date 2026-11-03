---
titolo: Come si collabora
versione: 0.1
data: 2026-11-02
autore: progetto «I cinque duchi»
---

# Come si collabora (persone e IA)

Questo file dice **come** una modifica arriva su `main`. **Che cosa** si può
cambiare e quali controlli devono passare lo dice `AGENTS.md`, e vale sempre:
qui non si ripete, si rimanda.

Il motivo per cui il file esiste: fino alla 0.35 il progetto aveva una persona
sola e un ramo solo, e ogni modifica andava dritta su `main`. Con più persone
non basta più, perché **ogni push su `main` pubblica il sito** (`pagine.yml`): una
modifica non rivista diventa subito una pagina che uno studente può aprire.

## 1. La regola

**Su `main` non si scrive direttamente. Ogni modifica passa da un ramo e da una
pull request, e la unisce una persona diversa da chi l'ha scritta.**

Il controllo `Verifica` gira già su ogni pull request (`verifica.yml`): una pull
request rossa non si unisce.

## 2. Il ramo

Un ramo per argomento, con il nome di chi ci lavora davanti:

```
pietro/parole-funzionali
claude/grafia-comune
mario/occidentale-bondeno
```

- `claude/…` è il prefisso delle sessioni di Claude. Claude **non** unisce le
  proprie pull request e non scrive su `main`.
- Un ramo piccolo si rivede, uno grande si approva per stanchezza. Se un ramo
  tocca dati e motore insieme senza bisogno, si divide.
- Prima di cominciare, una **issue** dice chi lavora su che cosa (§5). Due rami
  sullo stesso pezzo di `dati/` sono due conflitti sicuri.

## 3. La pull request

Il modello si apre da solo (`.github/pull_request_template.md`) e chiede tre cose:

1. **perché**, in una frase, come la voce di `REGISTRO.md`;
2. **che cosa** è cambiato: dati, motore, pagina, documenti;
3. **la lista dei controlli** di `AGENTS.md` §3, spuntata davvero.

Chi rivede guarda prima di tutto la regola di `AGENTS.md` §1: **c'è una voce
senza fonte? un vuoto riempito?** Se sì, la pull request non passa, anche se la
CI è verde: i controlli guardano la forma, la fonte la guarda una persona.

## 4. I file generati e la versione: dove i rami si scontrano

Due rami che toccano `dati/` vanno quasi sempre in conflitto, e non sui dati:

- sui **file generati**, `dati/regole.json` e le quarantadue pagine di `web/`;
- sul **numero di versione**, che sta in `pyproject.toml`,
  `sorgenti/traduttore/__init__.py`, nella frontmatter di `README.md` e in
  testa a `REGISTRO.md` (i test controllano che i quattro concordino).

Un conflitto in un file generato **non si risolve a mano**: si rigenera.
Quindi la regola è:

1. **Durante il lavoro** il ramo committa i dati e il codice, e può committare
   i generati quando servono per far passare la CI.
2. **Subito prima dell'unione**, chi ha scritto il ramo lo aggiorna su `main`:

   ```bash
   git fetch origin
   git rebase origin/main          # oppure merge, come si preferisce
   # nei conflitti su web/ e dati/regole.json: prendere una qualunque delle
   # due versioni, tanto si buttano
   export PYTHONPATH=sorgenti
   python3 -m traduttore.cli impara
   python3 -m traduttore.cli web
   ```

3. **La versione si assegna in quel momento**, non all'inizio: il ramo prende
   il numero successivo all'ultimo di `main`. Così l'ordine delle versioni è
   l'ordine in cui le modifiche sono entrate, e due rami non si contendono lo
   stesso numero.
4. Se nel frattempo un'altra pull request è stata unita, si rifà il punto 2.

Una pull request che cambia **solo documenti** (come quella che ha aggiunto
questo file) non cambia la versione: la regola 3 di `REGISTRO.md` lega la
versione al comportamento e ai dati.

## 5. Le issue: chi fa che cosa

Il lavoro aperto sta nelle issue di GitHub, non nella testa di qualcuno.
Etichette consigliate:

| etichetta | per |
|---|---|
| `dati` | glossario, coppie, proverbi, fonetica |
| `fonti` | una fonte nuova o la sua licenza (`dati/fonti.json`, `RACCOLTA.md`) |
| `motore` | `sorgenti/traduttore/` e la copia JavaScript in `modello.html` |
| `pagina` | `web/` e `costruisci_web.py` |
| `decisione` | una delle domande aperte di `AGENTS.md` §6 |

Chi prende una issue la assegna a sé. Una issue `decisione` non si chiude con
del codice: si chiude scrivendo la risposta in `AGENTS.md` §6, con la data e chi
ha deciso.

## 6. Chi approva

| che cosa | chi |
|---|---|
| unire una pull request su `main` | il titolare (Pietro Fabbri), o chi lui indica qui |
| una voce nuova, o una fonte nuova | chi rivede controlla la fonte, non solo la CI |
| le proposte del livello IA (`dati/proposte/`) | **ancora da decidere**: è la domanda 3 di `AGENTS.md` §6, e finché non è decisa nessuno le promuove |

Se cambia chi approva, si cambia questa tabella in una pull request.

## 7. Come si entra

- **Chi ha i permessi di scrittura** sulla repository crea il ramo direttamente
  qui. Si chiedono al titolare, che li dà da *Settings → Collaborators*.
- **Chi non li ha** fa un *fork*, lavora su un ramo del fork e apre la pull
  request verso `main` di questa repository. Le regole sono le stesse.

## 8. Impostazioni della repository (per il titolare)

Perché la regola del §1 non resti un desiderio, va fatta rispettare da GitHub:
*Settings → Branches → Add branch protection rule* su `main`:

- *Require a pull request before merging*, con almeno un'approvazione;
- *Require status checks to pass*, con il controllo `controlli` di `Verifica`;
- *Do not allow bypassing the above settings*, se si vuole che valga anche per
  il titolare.

Finché queste impostazioni non ci sono, la regola vale per accordo e non per
controllo, e va detto.
