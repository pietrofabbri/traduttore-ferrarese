<!-- Le regole sono in CONTRIBUTING.md e AGENTS.md. Togli quello che non serve. -->

## Perché

<!-- Una frase, come la voce di REGISTRO.md. -->

## Che cosa cambia

- [ ] dati (`dati/`)
- [ ] motore (`sorgenti/traduttore/`) — se sì, anche `sorgenti/modello.html`, nello stesso commit
- [ ] pagina (`web/`, `costruisci_web.py`)
- [ ] solo documenti (la versione non cambia)

Issue collegata: #

## Controlli (AGENTS.md §3)

- [ ] `python3 prove/test_traduttore.py`
- [ ] `python3 -m traduttore.cli verifica` — 0 errori
- [ ] `python3 prove/scanner.py`
- [ ] `python3 prove/controlla_equivalenza.py` (se ho toccato motore o pagina)
- [ ] `python3 prove/ci_locale.py`

Se ho toccato `dati/`:

- [ ] ogni voce nuova ha `fonte` e `varieta`; nessun vuoto riempito a mano
- [ ] rigenerati `impara` e `web` **dopo** l'ultimo aggiornamento su `main` (CONTRIBUTING.md §4)
- [ ] versione nei quattro posti e voce in `REGISTRO.md`, con il motivo
- [ ] `python3 -m traduttore.cli buchi`: i numeri si muovono come dico

## Che cosa resta aperto

<!-- Quello che questa modifica non risolve, o i buchi nuovi che dichiara. -->
