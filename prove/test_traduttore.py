"""I test del traduttore.

Ogni test verifica una regola che il progetto dichiara per iscritto. Se una
regola non ha un test, non e' una regola: e' una speranza.

Le regole, per gruppo:

1. la normalizzazione toglie quello che non distingue e lascia l'accento;
2. il glossario risponde per entrambe le direzioni, e le voci vicine sono
   consultive e non risposte;
3. il glossario dichiara i campi che mancano, non li inventa: nessuna fonte
   diventata `D` per arte, nessuna varieta' inventata;
4. il motore risponde dal glossario quando la voce c'e', e quando la voce
   non c'e' **non indovina**: restituisce la parola e registra il buco;
5. il corpus risponde con il **frammento** che combacia e non con la frase
   intera, e la frase gemella viene resa per intero;
6. le regole morfologiche si imparano dal corpus, sopravvivono alla propria
   generalizzazione e non si applicano al glossario;
7. una risposta sotto soglia non e' pubblicabile;
8. le cinque varieta' sono cinque, una voce le dichiara obbligatoriamente, e
   le varieta' vuote si dicono;
9. una trascrizione IPA e' una trascrizione, e non si dichiara documentata
   senza che qualcuno abbia ascoltato;
10. un brano audio non si pubblica senza consenso, licenza e `pubblicabile`;
11. quello che aspetta la verifica della licenza non entra nei dati attivi;
12. una risposta del modello resta una proposta e non si porta dentro una
    fonte;
13. i controlli trovano quello che devono trovare, e i dati di questo
    repository li passano tutti.

Il test 4 e' il piu' importante del file. Un traduttore che sbaglia in
silenzio e' peggio di un dizionario che non c'e', perche' lo sbaglio una
volta propagato in un gioco didattico si fissa e non si vede piu'.

Il blocco finale, quello delle varieta' e della fonetica, verifica le regole
che sono venute dopo: una voce **deve** dire in quale varieta' e' attestata,
una trascrizione IPA deve essere una trascrizione e non la parola rimessa al
suo posto, e un brano audio non si pubblica senza consenso e licenza.

L'ultimo test del file e' quello che conta di piu' di tutti e non guarda una
funzione: `test_dati_del_repository_passano_i_controlli` prende i dati che ci
sono adesso e li sottopone a tutti i controlli. Se fallisce, il CI fallisce,
e il progetto non puo' essere pubblicato con i dati rotti dentro.
"""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sorgenti"))

from traduttore import morfologia, normalizza, verifica_dati  # noqa: E402
from traduttore.audio import Archivio, Brano, controlla_archivo  # noqa: E402
from traduttore.corpora import Coppia, Corpus, Proverbio  # noqa: E402
from traduttore.fonetica import Fonetica, Trascrizione, ipa_valida  # noqa: E402
from traduttore.glossario import FE_IT, IT_FE, Glossario, Voce  # noqa: E402
from traduttore.motore import Motore  # noqa: E402
from traduttore import proposte  # noqa: E402
from traduttore.varieta import VARIETA, Varieta, _nome_valido  # noqa: E402

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def glossario_di_prova():
    return Glossario([
        _voce("V1", "magnàr", "mangiare", "Biondelli 1853, pag. 204"),
        _voce("V2", "pan", "pane", "Wikipedia, sezione Caratteristiche"),
        _voce("V3", "brisa", "niente", "Wikipedia, sezione Caratteristiche"),
        # V4 ha la fonte vuota di proposito: serve al test 2.
        _voce("V4", "stanza", "camera", ""),
        # V5 e' una locuzione: serve al test di accorpamento.
        _voce("V5", "a brazz avèrti", "a braccia aperte", "Ferri 1889, pag. 8"),
        _voce("V6", "a man salva", "sicuramente", "Ferri 1889, pag. 20"),
    ])


def _voce(id_, fe, it, fonte="", attendibilita="D", **kwargs):
    kwargs.setdefault("varieta", "cittadino")
    return Voce(id=id_, ferrarese=fe, italiano=it, fonte=fonte,
                attendibilita=attendibilita, **kwargs)


def corpus_di_prova():
    return Corpus([
        _coppia("F1", "non c'e' pane", "an ghe brisa pan"),
        _coppia("F2", "il pane", "el pan"),
        _coppia("F3", "la porta", "la porta"),
    ])


def _coppia(id_, it, fe, fonte="prova", **kwargs):
    kwargs.setdefault("varieta", "cittadino")
    return Coppia(id=id_, italiano=it, ferrarese=fe, fonte=fonte, **kwargs)


class TestNormalizzazione(unittest.TestCase):
    def test_chiave_tolga_gli_accenti_e_l_apostrofo(self):
        self.assertEqual(normalizza.chiave("Fràra"), "frara")
        self.assertEqual(normalizza.chiave("ghe’va"), "gheva")

    def test_normale_conserva_l_accento(self):
        # La risposta che torna al lettore non deve perdere l'accento.
        self.assertIn("à", normalizza.normale("magnàr"))

    def test_tokenizza_tiene_l_apostrofo_interno(self):
        self.assertEqual(normalizza.tokenizza("l'a casa"), ["l'a", "casa"])

    def test_somiglianza(self):
        self.assertEqual(normalizza.somiglianza("magnar", "magnàr"), 1.0)
        self.assertGreater(normalizza.somiglianza("magnar", "mangiar"), 0.7)


class TestGlossario(unittest.TestCase):
    def setUp(self):
        self.glossario = glossario_di_prova()

    def test_risponde_italiano_ferrarese(self):
        voci = self.glossario.cerca("mangiare", IT_FE)
        self.assertEqual(len(voci), 1)
        self.assertEqual(voci[0].ferrarese, "magnàr")

    def test_risponde_ferrarese_italiano(self):
        voci = self.glossario.cerca("pan", "fe-it")
        self.assertEqual(voci[0].italiano, "pane")

    def test_dichiara_il_campo_mancante_e_non_lo_inventa(self):
        # Una voce senza fonte deve restare senza fonte, non diventare D.
        voce = self.glossario.per_id("V4")
        self.assertEqual(voce.fonte, "")
        problemi = verifica_dati.controlla_glossario(self.glossario)
        # Non e' un errore (il controllo G4 scatta solo su attendibilita D con
        # fonte mancante... quindi qui deve scattare), e quindi deve comparire.
        codici = [p.codice for p in problemi]
        self.assertIn("G4", codici)

    def test_vicine_sono_consultative_e_non_risposte(self):
        # Una parola che il glossario non ha non si risolve con una parola che
        # c'e'. «cerca» resta vuota e il consultivo propone, senza decidere.
        self.assertEqual(self.glossario.cerca("magnesi", IT_FE), [])
        vicine = self.glossario.vicine("mangiar", IT_FE, soglia=0.6)
        self.assertTrue(vicine)
        self.assertEqual(vicine[0][1].id, "V1")


class TestMotore(unittest.TestCase):
    def setUp(self):
        self.motore = Motore(glossario_di_prova(), corpus_di_prova(), regole=[])

    def test_risponde_dal_glossario(self):
        risposta = self.motore.traduci("mangiare pane", IT_FE)
        self.assertIn("magnàr", risposta.testo)
        self.assertIn("pan", risposta.testo)
        origini = [c[2] for c in risposta.per_corrispondenza]
        self.assertEqual(origini, ["glossario", "glossario"])
        self.assertTrue(risposta.da_pubblicare)

    def test_la_parola_che_manca_nel_glossario_resta_un_buco(self):
        # Il corpus ha la coppia «non c'e' pane» / «an ghe brisa pan», e «un»
        # somiglia a «non» dentro quella frase. Ma in quella frase non c'e' un
        # pezzo che valga come «un»: restituire tutta la coppia risponderebbe a
        # una domanda che non e' stata fatta.
        risposta = self.motore.traduci("un pane", IT_FE)
        self.assertIn("un", risposta.buchi)
        self.assertFalse(risposta.da_pubblicare)

    def test_la_frase_gemella_viene_resa_intera(self):
        risposta = self.motore.traduci("non c'e' pane", IT_FE)
        self.assertEqual(risposta.testo, "an ghe brisa pan")
        self.assertEqual(len(risposta.per_corrispondenza), 1)
        self.assertEqual(risposta.per_corrispondenza[0][2], "corpo")

    def test_una_locuzione_non_viene_smembrata(self):
        # «a braccia aperte» e' una voce sola nel glossario. Smembrata in tre
        # parole darebbe tre buchi dove c'e' una risposta, cioe' una traduzione
        # peggiore di non tradurre.
        risposta = self.motore.traduci("a braccia aperte", IT_FE)
        self.assertEqual(risposta.testo, "a brazz avèrti")
        self.assertEqual(len(risposta.per_corrispondenza), 1)
        self.assertEqual(risposta.per_corrispondenza[0][0], "a braccia aperte")
        self.assertEqual(risposta.per_corrispondenza[0][2], "glossario")
        self.assertEqual(risposta.buchi, [])

    def test_la_locuzione_viene_accordata_nella_due_direzioni(self):
        risposta = self.motore.traduci("a brazz avèrti", FE_IT)
        self.assertEqual(risposta.testo, "a braccia aperte")
        self.assertEqual(len(risposta.per_corrispondenza), 1)

    def test_l_accorpamento_e_avido_e_non_mangia_troppo(self):
        # «voglio a braccia aperte»: l'accorpamento parte dalla parola piu'
        # lunga e torna indietro finche' non trova. «a braccia» da sola non e'
        # nel glossario e non deve diventare una risposta.
        risposta = self.motore.traduci("voglio a braccia aperte", IT_FE)
        testi = [c[0] for c in risposta.per_corrispondenza]
        self.assertEqual(testi, ["voglio", "a braccia aperte"])
        self.assertEqual(risposta.testo, "voglio a brazz avèrti")

    def test_una_parola_sola_non_e_mai_un_accorpamento(self):
        # «mangiare» e' una voce da sola: l'accorpamento comincia da due
        # parole e non deve trasformare una parola in due pezzi.
        risposta = self.motore.traduci("mangiare", IT_FE)
        self.assertEqual(len(risposta.per_corrispondenza), 1)
        self.assertEqual(risposta.per_corrispondenza[0][0], "mangiare")

    def test_il_corpus_risponde_col_frammento_e_non_con_la_frase(self):
        # «pane» e' nel glossario di prova, quindi il livello 2 si controlla
        # chiamando il corpus direttamente, senza passare dal motore.
        pezzo = self.motore.corpus.frammento(
            _coppia("FX", "il pane", "el pan"), "pane", IT_FE)
        self.assertIsNotNone(pezzo)
        self.assertEqual(pezzo[0], "pan")
        # 0.75, non 1.0: «pane» e «pan» differiscono di una lettera finale, e il
        # punteggio lo deve dire, altrimenti il motore crede di aver trovato
        # un'identita' che non c'e'.
        self.assertLess(pezzo[1], 1.0)
        # E con una parola che non c'e' nel frammento, il frammento e' None.
        self.assertIsNone(
            self.motore.corpus.frammento(_coppia("FX", "non c'e' pane", "an ghe brisa pan"),
                                         "non", IT_FE))

    def test_non_indovina_e_dichiara_il_buco(self):
        # «zuppa» non e' nel glossario, non e' nel corpus, e nessuna regola la
        # produce. Il motore deve lasciarla com'e' e dichiararlo.
        risposta = self.motore.traduci("zuppa", IT_FE)
        self.assertEqual(risposta.testo, "zuppa")
        self.assertIn("zuppa", risposta.buchi)
        self.assertFalse(risposta.da_pubblicare)

    def test_il_buco_abbassa_la_confidenza(self):
        piena = self.motore.traduci("pane", IT_FE)
        con_buco = self.motore.traduci("pane e zuppa", IT_FE)
        self.assertGreater(piena.confidenza, con_buco.confidenza)

    def test_direzione_inversa(self):
        risposta = self.motore.traduci("magnàr", "fe-it")
        self.assertIn("mangiare", risposta.testo)


class TestProverbi(unittest.TestCase):
    """La ricerca nei proverbi, che e' quello che c'era dietro il vuoto.

    Un proverbio si cerca su pezzi, non sul testo intero, e dalla parte
    giusta: `letterario` e `popolare` sono forme ferraresi, e cercarle dalla
    parte italiana faceva comparire proverbi che non c'entravano.
    """
    def setUp(self):
        self.corpus = Corpus(proverbi=[
            Proverbio(id="P1", italiano="Non tutte le ciambelle riescono col buco.",
                      ferrarese="la n' è minga sèmpar cumpàgna",
                      letterario="La n' è minga sèmpar cumpàgna",
                      fonte="Ferri 1889, pag. 102", attendibilita="D"),
            Proverbio(id="P2", italiano="Lupo non mangia di lupo.",
                      ferrarese="can an magna ad can",
                      letterario="Can an magna ad can",
                      fonte="Ferri 1889, pag. 73", attendibilita="D"),
        ])

    def test_cerca_un_pezzo_e_trova_il_proverbio(self):
        trovati = self.corpus.cerca_proverbio("non tutte le ciambelle", IT_FE)
        self.assertEqual([p.id for _, p, _ in trovati], ["P1"])

    def test_cerca_un_proverbio_intero(self):
        trovati = self.corpus.cerca_proverbio("lupo non mangia di lupo", IT_FE)
        self.assertEqual([p.id for _, p, _ in trovati], ["P2"])

    def test_la_forma_dei_libri_si_cerca_solo_dalla_parte_ferrarese(self):
        # «magnàr» contro «magna» della forma ferrarese del P2. Dall'altra
        # parte non deve comparire niente: e' la forma dei libri, non quella
        # italiana, e cercarla li' faceva rispondere il proverbio del lupo a
        # una domanda su «mangiare».
        self.assertEqual(self.corpus.cerca_proverbio("magnàr", IT_FE), [])
        trovati = self.corpus.cerca_proverbio("can an magna ad can", FE_IT)
        self.assertEqual([p.id for _, p, _ in trovati], ["P2"])

    def test_una_ricerca_senza_risposta_e_una_ricerca_vuota(self):
        self.assertEqual(self.corpus.cerca_proverbio("gatti e cavalli", IT_FE), [])
        self.assertEqual(self.corpus.cerca_proverbio("", IT_FE), [])


class TestMorfologia(unittest.TestCase):
    def test_impara_la_desinenza_e_la_generalizza(self):
        # Tre infiniti con tre radici diverse e la stessa coppia di desinenze
        # `are` > `ar`: i dati stanno dicendo che la trasformazione non
        # dipende dalla radice, e la regola va scritta senza prefisso.
        corpus = Corpus([
            _coppia("A", "cantare", "cantar"),
            _coppia("B", "lavorare", "lavorar"),
            _coppia("C", "nuotare", "nuotar"),
        ])
        regole = morfologia.impara(corpus)
        self.assertTrue(regole, "nessuna regola imparata: il corpus dovrebbe bastare")
        generale = [r for r in regole if r.prefisso == "" and r.suffisso_italiano == "are"]
        self.assertTrue(generale, "manca la regola are > ar")
        self.assertEqual(generale[0].suffisso_ferrarese, "ar")
        self.assertEqual(generale[0].accordo, 1.0)

    def test_la_generalizzazione_che_sbaglia_non_diventa_regola(self):
        # `cantare` > `cantar` e `camminare` > `caminar` hanno la stessa
        # desinenza ma due radici diverse: i dati suggeriscono una regola
        # generale, e la regola generale sbaglia su `camminare`, che vuole
        # `caminar` e non `camminar`. Quindi la regola viene buttata, e questa
        # e' la difesa che impedisce al motore di produrre una parola lunga e
        # plausibile e sbagliata.
        corpus = Corpus([
            _coppia("A", "cantare", "cantar"),
            _coppia("B", "camminare", "caminar"),
        ])
        regole = morfologia.impara(corpus)
        for regola in regole:
            self.assertGreaterEqual(regola.accordo, morfologia.SOGLIA_ACCORDO)

    def test_una_sola_coppia_non_e_una_regola(self):
        corpus = Corpus([_coppia("A", "cantare", "cantar")])
        self.assertEqual(morfologia.impara(corpus), [])

    def test_allineamento_rifiuta_le_frasi_di_lunghezza_diversa(self):
        # Il motivo e' dichiarato nel modulo: l'allineamento per posizione su
        # due frasi di lunghezza diversa produce regole false.
        self.assertEqual(morfologia.allinea(["a", "b"], ["x"]), [])

    def test_applica_la_regola(self):
        regola = morfologia.Regola("", "are", "ar", [
            {"italiano": "cantare", "ferrarese": "cantar", "prodotto": "cantar", "attestato": True}])
        self.assertEqual(morfologia.applica("cantare", [regola]), "cantar")
        self.assertEqual(morfologia.applica("cercare", [regola]), "cercar")

    def test_senza_regole_applica_ritorna_l_originale(self):
        self.assertEqual(morfologia.applica("qualsiasi", []), "qualsiasi")


class TestControlli(unittest.TestCase):
    def test_trova_id_duplicate(self):
        glossario = glossario_di_prova()
        glossario.voci.append(_voce("V1", "altra", "altro", "fonte di prova"))
        codici = [p.codice for p in verifica_dati.controlla_glossario(glossario)]
        self.assertIn("G2", codici)

    def test_trova_voce_con_un_lato_solo(self):
        glossario = Glossario([_voce("V9", "solo", "", "fonte di prova", varieta="")])
        codici = [p.codice for p in verifica_dati.controlla_glossario(glossario)]
        self.assertIn("G3", codici)

    def test_coppia_senza_fonte_e_avviso_e_non_errore(self):
        corpus = Corpus([Coppia(id="F1", italiano="a", ferrarese="b", fonte="",
                             varieta="cittadino")])
        problemi = verifica_dati.controlla_corpora(corpus)
        self.assertEqual([p.codice for p in problemi], ["C4"])
        self.assertEqual(problemi[0].gravita, "avviso")
        # E soprattutto: la coppia non entra nel motore.
        self.assertEqual(corpus.coppie_valide(), [])

    def test_dati_del_repository_passano_i_controlli(self):
        # Il controllo che conta: i dati che ci sono adesso, non quelli di una
        # prova. Se fallisce, il CI fallisce.
        glossario, corpus, varieta, fonetica, archivio = _dati_del_repository()
        attesa_glossario, attesa_corpus = _dati_in_attesa()
        problemi = (verifica_dati.controlla_varieta(varieta)
                    + proposte.controlla_proposte(
                        proposte.leggi(os.path.join(RADICE, "dati", "proposte",
                                                    "proposte.jsonl")))
                    + verifica_dati.controlla_glossario(glossario)
                    + verifica_dati.controlla_corpora(corpus)
                    + verifica_dati.controlla_fonetica(fonetica, glossario, corpus, varieta)
                    + controlla_archivo(archivio)
                    + verifica_dati.controlla_tenuta(glossario, corpus,
                                                    attesa_glossario, attesa_corpus))
        errori = [p for p in problemi if p.gravita == "errore"]
        self.assertEqual([p.riga() for p in errori], [], "i dati del repository hanno errori")


def _dati_del_repository():
    dati = os.path.join(RADICE, "dati")
    return (
        Glossario.da_file(os.path.join(dati, "glossario.jsonl")),
        Corpus.da_file(os.path.join(dati, "coppie.jsonl"),
                       os.path.join(dati, "proverbi.jsonl")),
        Varieta.da_file(os.path.join(dati, "varieta.json")),
        Fonetica.da_file(os.path.join(dati, "fonetica.jsonl")),
        Archivio.da_file(os.path.join(dati, "audio.jsonl")),
    )


def _dati_in_attesa():
    dati = os.path.join(RADICE, "dati", "da_verificare")
    return (
        Glossario.da_file(os.path.join(dati, "glossario.jsonl")),
        Corpus.da_file(os.path.join(dati, "coppie.jsonl")),
    )


class TestFilaDAttesa(unittest.TestCase):
    """I dati che il progetto possiede e non usa.

    Il motivo e' dichiarato in `dati/da_verificare/README.md`: la traduzione
    ferrarese della Dichiarazione universale dei diritti umani non ha una
    fonte primaria rintracciata, quindi la sua licenza non e' verificata, quindi
    non si pubblica. La fila d'attesa e' il posto giusto per tenerla senza
    dimenticarla.
    """

    def test_un_id_in_attesa_che_e_anche_attivo_e_un_errore(self):
        # Il caso da cui nasce tutto: una voce che aspetta la verifica della
        # licenza e che intanto viene usata. E' il modo piu' economico di
        # pubblicare dati di provenienza ignora.
        attesa = Glossario([_voce("V1", "pan", "pane", "fonte di prova")])
        attivo = Glossario([_voce("V1", "pan", "pane", "fonte di prova")])
        codici = [p.codice for p in verifica_dati.controlla_tenuta(
            attivo, corpus_di_prova(), attesa)]
        self.assertIn("D1", codici)

    def test_una_voce_in_attesa_che_si_dichiara_documentata_e_un_avviso(self):
        attesa = Glossario([_voce("V9", "nass", "nasceri",
                                 "traduzione anonima, art. 1")])
        problemi = [p for p in verifica_dati.controlla_tenuta(
            glossario_di_prova(), corpus_di_prova(), attesa)
            if p.codice == "D2"]
        self.assertEqual(len(problemi), 1)
        self.assertEqual(problemi[0].gravita, "avviso")

    def test_la_fila_d_attesa_del_repository_non_sovrappone_il_glossario(self):
        attesa_glossario, attesa_corpus = _dati_in_attesa()
        glossario, corpus, varieta, fonetica, archivio = _dati_del_repository()
        problemi = verifica_dati.controlla_tenuta(glossario, corpus,
                                                 attesa_glossario, attesa_corpus)
        errori = [p for p in problemi if p.gravita == "errore"]
        self.assertEqual([p.riga() for p in errori], [],
                         "un id in attesa e' anche nei dati attivi")
        # E la fila non e' vuota: se si svuotasse, il controllo D1 non
        # controllerebbe piu' niente e sembrerebbe che il progetto sia a posto.
        self.assertTrue(attesa_glossario.voci or attesa_corpus.coppie)


class TestLineaDiComando(unittest.TestCase):
    """I comandi, perche' un comando che risponde «nessuna voce» a una parola
    che c'e' e' peggio di un comando assente.

    Il difetto che questi test prendono e' reale e gia' successo: `cerca`
    guardava **solo** il lato italiano per default, quindi chi cercava una
    parola ferrarese — cioe' chi legge un vocabolario dell'Ottocento e vuole
    sapere cosa vuol dire — riceveva «nessuna voce» per una parola che era
    li'. Non un vuoto vero: un vuoto fabbricato dalla bandierina, che e' la
    peggior specie di vuoto, perche' si vede come informazione.
    """

    def _esegui(self, argv):
        import io
        import contextlib
        from traduttore import cli
        uscita = io.StringIO()
        with contextlib.redirect_stdout(uscita):
            stato = cli.main(argv)
        return stato, uscita.getvalue()

    def test_cerca_trova_una_parola_ferrarese_senza_indicare_il_lato(self):
        stato, testo = self._esegui(["cerca", "magnàr"])
        self.assertEqual(stato, 0, testo)
        self.assertIn("V0001", testo)
        self.assertIn("dal lato ferrarese", testo)
        # E porta anche le cose che sono il punto: varieta' e suono.
        self.assertIn("cittadino", testo)
        self.assertIn("/", testo)

    def test_cerca_trova_anche_una_parola_italiana(self):
        stato, testo = self._esegui(["cerca", "mangiare"])
        self.assertEqual(stato, 0, testo)
        self.assertIn("dal lato italiano", testo)

    def test_cerca_restringuta_a_un_lato_e_rispettata(self):
        stato, testo = self._esegui(["cerca", "magnàr", "--direzione", "it-fe"])
        self.assertEqual(stato, 1)
        self.assertIn("nessuna voce", testo)

    def test_pronuncia_senza_parola_mostra_l_aiuto_e_non_esce_in_silenzio(self):
        stato, _ = self._esegui(["pronuncia"])
        self.assertEqual(stato, 1)

    def test_copertura_senza_i_file_ItWaC_lo_dice_e_non_indovina(self):
        # Il comando non deve mai produrre un numero con un metro che non ha:
        # 23,7% con i lemmi e 10,8% con le forme sono due numeri diversi, e
        # quello senza i file e' semplicemente falso. Meglio nessun numero.
        #
        # Il comando delega a `copertura.py` con `subprocess`, quindi qui non
        # si passa da `_esegui`: quello cattura lo stdout della CLI padre, e
        # la scrittura del figlio finisce fuori. Si chiama lo script
        # direttamente, che e' anche la cosa che il comando fa.
        import subprocess
        import sys as _sys
        percorso = os.path.join(RADICE, "raccolta", "copertura.py")
        risultato = subprocess.run([_sys.executable, percorso],
                                  capture_output=True, text=True)
        if os.path.exists(os.path.join(RADICE, "raccolta", "grezzi",
                                       "itwac_noun.csv")):
            self.skipTest("gli elenchi ItWaC sono presenti: niente da dichiarare")
        # `copertura.py` esce con 1 quando gli elenchi mancano.
        self.assertEqual(risultato.returncode, 1, risultato.stdout)
        self.assertIn("Mancano questi elenchi", risultato.stdout)
        # E soprattutto: nessun numero di copertura.
        self.assertNotIn("23.7", risultato.stdout)
        self.assertNotIn("10.8", risultato.stdout)
        self.assertNotIn("coperte dal glossario", risultato.stdout)

    def test_buchi_stampa_un_numero_e_il_motivo_per_ogni_buco(self):
        # Il comando non fallisce mai e non e' un controllo: qui non c'e'
        # niente da correggere, c'e' solo da sapere. Quindi esce 0 anche se
        # i buchi sono cinque, e ogni riga porta il numero E il motivo: una
        # riga che porta solo il numero non dice a nessuno cosa fare.
        #
        # Il totale non e' scritto qui: quando il glossario e' passato da 234
        # a 10401 voci, un numero scritto a mano nel test e' diventato falso
        # senza che nessuno lo toccasse. Ora viene dai dati.
        glossario, _, _, _, _ = _dati_del_repository()
        stato, testo = self._esegui(["buchi"])
        self.assertEqual(stato, 0, testo)
        self.assertIn("proverbi senza la forma che si dice", testo)
        self.assertIn("su %d" % len(glossario.voci), testo)
        self.assertIn("il campo `popolare`", testo)
        self.assertIn("Non sono errori", testo)

    def test_buchi_json_e_json_legibile_e_non_un_testo(self):
        # Il JSON serve a un altro programma, quindi non puo' contenere le
        # righe di spiegazione: se lo mescoli col testo, un utente che lo
        # passa a `jq` ottiene un errore invece dei numeri.
        import json as _json
        stato, testo = self._esegui(["buchi", "--json"])
        self.assertEqual(stato, 0, testo)
        dati = _json.loads(testo)
        self.assertTrue(dati)
        for riga in dati:
            self.assertIn("nome", riga)
            self.assertIn("quanti", riga)
            self.assertIn("nota", riga)


class TestProposte(unittest.TestCase):
    """La coda di revisione del livello IA.

    Il test che conta e' il secondo: una risposta del modello che si porta
    dentro un campo `fonte` e' il modo in cui il livello 4 diventa una fonte
    senza che nessuno lo decida, e la coda deve impedirlo meccanicamente.
    """

    def _proposta(self, **kwargs):
        risposta = {"traduzione": "magnar", "confidenza": 0.6,
                    "dettaglio": "nessuna voce nel contesto",
                    "sources": ["V0001"]}
        risposta.update(kwargs)
        return proposte.da_risposta("mangiare", IT_FE, risposta, quando="2026-10-03")

    def test_salva_e_legge_e_appende(self):
        import tempfile
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "sotto", "proposte.jsonl")
            proposte.salva(self._proposta(), percorso)
            proposte.salva(self._proposta(), percorso)
            lette = proposte.leggi(percorso)
            self.assertEqual(len(lette), 2, "la seconda scrittura ha sovrascritto la prima")
            self.assertEqual(lette[0].parola, "mangiare")
            self.assertEqual(lette[0].stato, "da rivedere")
            self.assertEqual(lette[0].fonti_citate, ["V0001"])

    def test_una_proposta_con_una_fonte_e_un_errore(self):
        # Il controllo che tiene separate le due cose: il modello dice, la
        # persona documenta. Una riga che fa le due e' una riga che ha gia'
        # deciso al posto di qualcun altro.
        p = self._proposta()
        p.grezzo["fonte"] = "Wikipedia, sezione Caratteristiche"
        codici = [x.codice for x in proposte.controlla_proposte([p])]
        self.assertIn("M2", codici)

    def test_una_proposta_documentata_e_un_errore(self):
        p = self._proposta()
        p.grezzo["attendibilita"] = "D"
        self.assertIn("M2", [x.codice for x in proposte.controlla_proposte([p])])

    def test_uno_stato_inventato_e_un_errore(self):
        p = self._proposta()
        p.stato = "probabilmente giusta"
        self.assertIn("M1", [x.codice for x in proposte.controlla_proposte([p])])

    def test_una_citazione_inesistente_e_un_avviso(self):
        # Il modello che cita una voce che non esiste ha risposto inventando, e
        # va detto: e' un avviso, non un errore, perche' resta una proposta.
        p = self._proposta(sources=["V9999"])
        problemi = proposte.controlla_proposte([p], conosciute={"V0001"})
        self.assertEqual([x.codice for x in problemi], ["M3"])
        self.assertEqual(problemi[0].gravita, "avviso")

    def test_una_promozione_che_non_esiste_e_un_avviso(self):
        p = self._proposta()
        p.promossa_a = "V0100"
        problemi = proposte.controlla_proposte([p], conosciute={"V0001"})
        self.assertEqual([x.codice for x in problemi], ["M4"])

    def test_la_coda_del_repository_e_vuota(self):
        percorso = os.path.join(RADICE, "dati", "proposte", "proposte.jsonl")
        self.assertTrue(os.path.exists(percorso),
                        "la coda di revisione dev'essere dichiarata anche vuota")
        self.assertEqual(proposte.leggi(percorso), [])


class TestVarieta(unittest.TestCase):
    """Le cinque varieta' e il vuoto che le distingue l'una dall'altra.

    Il test che conta e' l'ultimo: quattro varieta' su cinque non hanno una
    sola voce, e il progetto deve poterlo dire senza arrossire.
    """

    def test_una_voce_senza_varieta_e_un_errore(self):
        glossario = Glossario([_voce("V1", "pan", "pane", "fonte di prova",
                                    varieta="")])
        codici = [p.codice for p in verifica_dati.controlla_glossario(glossario)]
        self.assertIn("G8", codici)

    def test_una_varieta_inventata_e_un_errore(self):
        glossario = Glossario([_voce("V1", "pan", "pane", "fonte di prova",
                                    varieta="ferrarese antico")])
        problemi = verifica_dati.controlla_glossario(glossario)
        self.assertIn("G9", [p.codice for p in problemi])
        self.assertEqual([p for p in problemi if p.codice == "G9"][0].gravita,
                         "errore")

    def test_una_coppia_senza_varieta_e_un_errore(self):
        corpus = Corpus([Coppia(id="F1", italiano="a", ferrarese="b",
                                fonte="prova", varieta="")])
        self.assertIn("C7", [p.codice for p in verifica_dati.controlla_corpora(corpus)])

    def test_una_varieta_che_manca_dalla_tassonomia_e_un_errore(self):
        # Se una delle cinque sparisce dal file dei dati, il progetto non deve
        # accorgersene in silenzio: si accorge subito, perche' sparisce metà
        # del territorio e il pannello continuerebbe a dire «tutto cittadino».
        varieta = Varieta.da_file(os.path.join(RADICE, "dati", "varieta.json"))
        varieta.voci = [v for v in varieta.voci if v["codice"] != "transpadano"]
        codici = [p.codice for p in verifica_dati.controlla_varieta(varieta)]
        self.assertIn("V6", codici)

    def test_il_nome_deve_nominare_una_delle_cinque(self):
        self.assertTrue(_nome_valido("cittadino"))
        self.assertTrue(_nome_valido("centrale, detto anche arioso"))
        self.assertTrue(_nome_valido("transpadano, ibrido col polesano"))
        self.assertTrue(_nome_valido("ferrarese transpadano"))
        self.assertFalse(_nome_valido("ferrarese antico"))
        self.assertFalse(_nome_valido(""))

    def test_le_varieta_vuote_si_dicono_e_non_si_nascondono(self):
        glossario, corpus, varieta, _, _ = _dati_del_repository()
        conteggi = varieta.conteggi(glossario=glossario, coppie=corpus.coppie)
        # Chiamata senza dati la funzione direbbe che tutte e cinque sono
        # vuote: il test passa i dati perche' e' cosi' che si usa nel pannello.
        vuote = varieta.vuote(conteggi)
        self.assertEqual(vuote, ["centrale", "occidentale", "orientale", "transpadano"])
        self.assertEqual(conteggi["cittadino"]["glossario"], len(glossario))
        self.assertNotIn("cittadino", vuote)

    def test_i_codici_sono_cinque_e_non_di_piu(self):
        self.assertEqual(len(VARIETA), 5)


class TestFonetica(unittest.TestCase):
    def test_una_parola_italiana_accentata_non_e_una_trascrizione(self):
        # Il difetto piu' comune di questo file: rimettere la grafia dentro il
        # campo IPA e credere di aver scritto qualcosa.
        self.assertFalse(ipa_valida("/magnàr/")[0])
        self.assertEqual(ipa_valida("/magnàr/")[1], ["à"])
        self.assertTrue(ipa_valida("/maˈɲnar/")[0])
        self.assertTrue(ipa_valida("/ɡe")[0])

    def test_una_trascrizione_che_non_riferisce_niente_e_un_errore(self):
        fonetica = Fonetica([Trascrizione(id="T1", riferimento="V999",
                                         forma="pan", ipa="/pan/", varieta="cittadino")])
        problemi = verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova())
        self.assertIn("F7", [p.codice for p in problemi])

    def test_una_trascrizione_dichiarata_documentata_senza_fonte_e_un_errore(self):
        # Il punto in cui una trascrizione diventa un fatto: solo se qualcuno
        # ha ascoltato, e il campo `fonte` lo dice.
        fonetica = Fonetica([Trascrizione(
            id="T1", riferimento="V2", forma="pan", ipa="/pan/",
            varieta="cittadino", attendibilita="D", da_verificare=False)])
        codici = [p.codice for p in verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova())]
        self.assertIn("F9", codici)

    def test_la_varieta_della_trascrizione_deve_essere_quella_della_voce(self):
        # Una parola che in pagina si presenta come di Bondeno e suona come
        # una di città non e' un dettaglio: e' una parola falsa.
        fonetica = Fonetica([Trascrizione(
            id="T1", riferimento="V2", forma="pan", ipa="/pan/",
            varieta="occidentale")])
        problemi = verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova())
        self.assertIn("F12", [p.codice for p in problemi])

    def test_cerca_forma_tolera_l_apostrofo(self):
        fonetica = Fonetica([Trascrizione(id="T1", riferimento="V1",
                                         forma="gh'è", ipa="/ɡˈɛ/",
                                         varieta="cittadino")])
        self.assertEqual(len(fonetica.cerca_forma("gh'e")), 1)
        self.assertEqual(len(fonetica.cerca_forma("gh'è")), 1)
        self.assertEqual(fonetica.cerca_forma("brisa"), [])

    def test_una_varieta_con_parole_e_senza_suoni_e_un_avviso(self):
        # Il buco che conta: le parole ci sono, i suoni no. E' un avviso e non
        # un errore, perche' il vuoto e' dichiarato e il progetto continua.
        glossario = Glossario([_voce("V1", "magnàr", "mangiare",
                                     "Biondelli 1853, pag. 204",
                                     varieta="occidentale")])
        varieta = Varieta.da_file(os.path.join(RADICE, "dati", "varieta.json"))
        problemi = verifica_dati.controlla_fonetica(
            Fonetica([]), glossario, corpus_di_prova(), varieta)
        codici = [p.codice for p in problemi]
        self.assertIn("F14", codici)
        self.assertEqual([p for p in problemi if p.codice == "F14"][0].gravita,
                         "avviso")

    def test_due_trascrizioni_della_stessa_scrittura_sono_un_avviso(self):
        # Due persone che scrivono due suoni per la stessa scrittura: non e'
        # un errore, ma nessuno dei due puo' presentarsi come l'unico, e il
        # progetto non sceglie. Da decidere a voce.
        fonetica = Fonetica([
            Trascrizione(id="T1", riferimento="V2", forma="pan", ipa="/pan/",
                         varieta="cittadino"),
            Trascrizione(id="T2", riferimento="V2", forma="pan", ipa="/pãn/",
                         varieta="cittadino"),
        ])
        problemi = [p for p in verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova()) if p.codice == "F13"]
        self.assertEqual(len(problemi), 1)
        self.assertEqual(problemi[0].gravita, "avviso")
        # E due scelte di scrittura diverse non sono un conflitto.
        fonetica = Fonetica([
            Trascrizione(id="T1", riferimento="V3", forma="brisa", ipa="/brisa/",
                         varieta="cittadino"),
            Trascrizione(id="T2", riferimento="V3", forma="brisà", ipa="/briˈsa/",
                         varieta="cittadino"),
        ])
        codici = [p.codice for p in verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova())]
        self.assertNotIn("F13", codici)

    def test_nessuna_trascrizione_e_verificata_alla_prima(self):
        # Il numero che dice quanto il progetto sia onesto: finche' vale zero,
        # la pronuncia non e' documentata da nessuna parte.
        _, _, _, fonetica, _ = _dati_del_repository()
        self.assertGreater(len(fonetica), 0)
        self.assertEqual(fonetica.quante_verificate(), 0)


class TestCopertura(unittest.TestCase):
    """La misura di quanto italiano copre il glossario.

    Il difetto che questi test prendono e' gia' successo ed e' il motivo per
    cui questa classe esiste. La prima versione di `copertura.py` misurava
    la copertura con una lista di frequenza presa dai **sottotitoli**, e
    diceva che al glossario mancava l'89% dell'italiano. Il numero era falso
    e per un motivo preciso: la lista conteneva forme **coniugate** — `sono`,
    `ho`, `stato`, `mangi` — mentre il glossario contiene **lemmi**
    (`essere`, `avere`, `stato`, `mangiare`). Confrontare un lemma con una
    coniugazione e' come concludere che al vocabolario manca «cane» perche'
    nella lista c'era «cani».

    Un numero di copertura che dice il contrario della verita' e' peggio di
    nessun numero: fa sembrare il progetto molto piu' vuoto di quanto sia, e
    fa lavorare qualcuno sulle parole sbagliate.
    """

    def _copertura(self):
        sys.path.insert(0, os.path.join(RADICE, "raccolta"))
        try:
            import copertura
        finally:
            sys.path.pop(0)
        return copertura

    def test_una_forma_coniugata_non_e_un_lemma_e_non_si_conta(self):
        # Il caso che ha fatto il numero falso. Se il metro torna a forme
        # coniugate, `mangi` non e' piu' coperto dal fatto che `mangiare` lo
        # sia, e la copertura crolla di nuovo senza che nessuno se ne accorga.
        glossario = Glossario([_voce("V1", "magnàr", "mangiare", "Ferri 1889")])
        c = self._copertura()
        for forma in ("mangi", "mangiamo", "mangeranno", "mangiava"):
            chiave = forma.lower()
            if chiave in c.FUNZIONALI:
                continue
            # Il lemma c'e'; la forma no. E' cosi' che deve restare: la
            # copertura si misura sui lemmi, e la coniugazione e' un altro
            # problema, dichiarato altrove.
            self.assertTrue(glossario.cerca_italiano("mangiare"))
            self.assertFalse(glossario.cerca_italiano(forma),
                             "%s e' una forma, non un lemma" % forma)

    def test_una_parola_funzionale_non_e_una_lacuna(self):
        # Contare `il`, `di`, `che` fra le mancanze direbbe che il glossario
        # e' piu' vuoto di quanto sia: sono in `morfologia.py`.
        c = self._copertura()
        for funzionale in ("il", "di", "che", "per", "con", "sono", "gli"):
            if funzionale in c.FUNZIONALI:
                continue
            self.fail("%s dovrebbe stare nell'elenco delle funzionali" % funzionale)

    def test_il_glossario_copre_almeno_un_quarto_dei_lemmi_frequenti(self):
        # Il numero che il progetto puo' dichiarare, con il metro giusto.
        # Non e' un test di qualita': e' il test che il metro non e' rotto.
        # Se questo numero crolla, o il metro e' sbagliato (per colpa dei
        # CSV non scaricati, o della codifica) o il glossario ha perso voci.
        c = self._copertura()
        percorso = os.path.join(RADICE, "raccolta", "grezzi", "itwac_noun.csv")
        if not os.path.exists(percorso):
            self.skipTest("gli elenchi ItWaC non sono in raccolta/grezzi/ (MIT, si scaricano)")
        glossario, _, _, _, _ = _dati_del_repository()
        coppie = c.leggi_elenco(percorso, "lemma")
        esito = c.analizza(glossario, {"sostantivi": coppie})
        totale = len(esito["coperte"]) + len(esito["mancanti"])
        percentuale = 100.0 * len(esito["coperte"]) / max(totale, 1)
        self.assertGreater(totale, 1000, "l'elenco e' troppo piccolo per essere il metro")
        self.assertGreater(percentuale, 20.0,
                           "copertura %0.1f%%: metro rotto o glossario vuoto?" % percentuale)

    def test_il_elenco_si_legge_in_latin1_e_non_in_utf8(self):
        # Dettaglio che ha fatto fallire lo script a meta' elenco: i CSV
        # dell'ItWaC sono in latin-1 (`attività` = due byte 0xe0). Leggerli
        # in UTF-8 solleva `UnicodeDecodeError` su una riga che sembra
        # normale. Il test fissa la codifica giusta.
        c = self._copertura()
        percorso = os.path.join(RADICE, "raccolta", "grezzi", "itwac_noun.csv")
        if not os.path.exists(percorso):
            self.skipTest("gli elenchi ItWaC non sono in raccolta/grezzi/")
        coppie = c.leggi_elenco(percorso, "lemma")
        self.assertGreater(len(coppie), 100)
        accenti = [p for p, _ in coppie if p.endswith("à")]
        self.assertGreater(len(accenti), 10,
                           "gli accenti non arrivano: la codifica non e' quella giusta")


class TestVociMeccaniche(unittest.TestCase):
    """Le voci portate dentro dal filtro senza sceglierle una a una.

    Il difetto che questi test prendono e' successo davvero: l'import dei
    10153 candidati del Ferri aveva messo dentro la voce «La» -> «La», e da
    li' in poi il motore riscriveva con la grafia della fonte ogni «la» di
    ogni frase — «la porta» diventava «La portàr». Una voce che non
    distingue le due lingue, in un vocabolario di traduzione, non e' una voce
    utile: e' una voce che fa scrivere sbagliato.
    """

    def _dati(self):
        glossario, corpus, _, fonetica, _ = _dati_del_repository()
        return glossario, corpus, fonetica

    def test_una_parola_funzionale_non_deve_essere_una_voce(self):
        # Gli articoli e le preposizioni sono gia' in `morfologia.py`. Una voce
        # per «la» non aggiunge niente e toglie la parola al motore.
        #
        # «fra» e «tra» non sono in elenco perche' sono anche toponimi: V0022 e'
        # la voce curata «fra» = Ferrara e viene da Wikipedia, non
        # dall'import meccanico, e quella voce giusta resta. Il generatore,
        # che legge solo i candidati del Ferri, li esclude lo stesso.
        glossario, _, _ = self._dati()
        for voce in glossario.voci:
            self.assertNotIn(voce.ferrarese.strip().lower(),
                             {"il", "lo", "la", "i", "gli", "le", "un", "una",
                              "a", "al", "da", "di", "in", "con", "per",
                              "e", "o", "ma", "che", "come", "se"},
                             "una parola funzionale non deve essere una voce")

    def test_ogni_voce_nuova_dichiara_che_non_e_stata_verificata(self):
        # L'import e' meccanico per scelta e per onesta': ogni riga che viene
        # dal filtro porta `da_verificare`, cosi' nessuno la prende per una
        # voce controllata con un informatore.
        glossario, _, _ = self._dati()
        meccaniche = [v for v in glossario.voci if v.attendibilita == "I"]
        self.assertGreater(len(meccaniche), 0)
        for voce in meccaniche[:400]:
            self.assertTrue(voce.da_verificare, voce.id)

    def test_il_generatore_scarta_le_parole_funzionali(self):
        # La regola e' del generatore, non solo dei dati: se domani il file
        # dei candidati, il generatore deve comunque non scrivere «La».
        sys.path.insert(0, os.path.join(RADICE, "raccolta"))
        try:
            import costruisci_meccanico
        finally:
            sys.path.pop(0)
        self.assertIn("la", costruisci_meccanico.FUNZIONALI)
        self.assertEqual(costruisci_meccanico.voce_pulita("Tundìn sm"), "Tundìn")


class TestResiMultipli(unittest.TestCase):
    """Una voce con piu' resi deve trovarsi da ciascuno dei suoi resi.

    Il difetto che questi test prendono e' gia' stato dichiarato nella
    versione 0.7 e poi corretto: il glossario indicizzava il lato italiano
    sull'intero campo `italiano`, quindi «Maladir -> Maledire, esacràre»
    non si trovava cercando «maledire». Erano **1663 voci su 10387** in
    questa situazione, e non si vedeva perche' le 210 voci curate del
    1889 avevano resi brevi. L'import meccanico le ha fatte emergere.

    La riga e' la stessa che in `modello.html` (funzione `chiaviResi`): se
    le due copie divergono, `prove/controlla_equivalenza.py` lo dice.
    """

    def test_una_resa_dentro_una_voce_si_trova_cercandola_sola(self):
        # Il caso che riporta l'utente: la parola c'era, non si trovava.
        # Non e' la parola che manca, e' l'indice che non la guardava.
        glossario = Glossario([
            _voce("V1", "Maladir", "Maledire, esacràre", "Ferri 1889, pag. 234"),
        ])
        voci = glossario.cerca_italiano("maledire")
        self.assertEqual([v.id for v in voci], ["V1"])
        voci = glossario.cerca_italiano("esacràre")
        self.assertEqual([v.id for v in voci], ["V1"])

    def test_il_reso_intero_resta_raggiungibile(self):
        # Dividere i pezzi non deve far perdere la voce intera: chi cerca la
        # voce come sta scritta nel libro deve trovarla lo stesso.
        glossario = Glossario([
            _voce("V1", "a bada", "con calma, senza fretta", "Ferri 1889, pag. 8"),
        ])
        for cercato in ("con calma, senza fretta", "con calma", "senza fretta"):
            self.assertEqual([v.id for v in glossario.cerca_italiano(cercato)], ["V1"],
                             "cercando %r" % cercato)

    def test_un_pezzo_non_e_una_parola_del_glossario(self):
        # Il limite che la correzione NON deve superare: si divide su virgola
        # e punto e virgola, non sugli spazi. «con calma» deve trovarsi
        # cercando «con calma», e NON cercando «calma», che e' un'altra voce
        # (V0025) e che perderebbe il contesto in cui il libro la scrive.
        glossario = Glossario([
            _voce("V1", "a bada", "con calma, senza fretta", "Ferri 1889, pag. 8"),
            _voce("V2", "calma", "calma", "Ferri 1889, pag. 30"),
        ])
        self.assertEqual([v.id for v in glossario.cerca_italiano("calma")], ["V2"])
        self.assertNotIn("V1", [v.id for v in glossario.cerca_italiano("calma")])

    def test_principale_che_non_e_un_reso_mal_risponde_ancora(self):
        # `principale_italiano` vale anche quando non e' un pezzo della voce:
        # e' la forma da usare in frase. Se il campo c'e', la voce deve
        # trovarsi anche cercando quella.
        glossario = Glossario([_voce("V1", "gh'è", "c'è, è (presenza)",
                                     "Ferri 1889, pag. 40")])
        self.assertEqual([v.id for v in glossario.cerca_italiano("c'è")], ["V1"])
        self.assertEqual([v.id for v in glossario.cerca_italiano("è (presenza)")], ["V1"])

    def test_una_voce_non_occupa_due_volte_lo_stesso_indice(self):
        # Una voce i cui pezzi si normalizzano allo stesso modo («no, no»:
        # due forme diverse che diventano la stessa chiave) deve comparire
        # una volta sola, altrimenti il motore annuncerebbe «altre voci» che
        # sono la voce che ha gia' risposto.
        glossario = Glossario([_voce("V1", "a bada", "con calma, con calma",
                                     "Ferri 1889, pag. 8")])
        self.assertEqual(len(glossario.cerca_italiano("con calma")), 1)

    def test_ogni_voce_con_piu_resi_e_raggiungibile(self):
        # Il numero, non l'esempio. Se domani il file, questa riguarda tutte le
        # voci e fallisce sul primo caso, che e' quello che serve vedere.
        glossario, _, _, _, _ = _dati_del_repository()
        composte = [v for v in glossario.voci if "," in (v.italiano or "")
                    or ";" in (v.italiano or "")]
        self.assertGreater(len(composte), 100, "il glossario non ha piu' resi da dividere")
        for voce in composte:
            for pezzo in re.split(r"[,;]", voce.italiano):
                cercato = pezzo.strip()
                if not cercato:
                    continue
                self.assertTrue(glossario.cerca_italiano(cercato),
                                "%s non si trova cercando %r" % (voce.id, cercato))


class TestBuchiDichiarati(unittest.TestCase):
    """Le cose che il progetto sa di non sapere, con un numero accanto.

    «Non abbiamo le trascrizioni IPA» resta vero per sempre. «Ne abbiamo
    210 su 234» e' una frase che qualcuno puo' correggere lunedi'. Il
    difetto che questi test prendono e' gia' successo per meta': i numeri
    che non hanno un nome accanto smettono di essere numeri e diventano
    un'oblazione, e un'oblazione non si riduce da sola.
    """

    def test_ogni_buco_ha_il_motivo_per_cui_manca(self):
        # Una riga senza nota non dice niente e sta peggio che non esserci:
        # il lettore non puo' azzardare se sia un difetto o una scelta.
        glossario, corpus, _, fonetica, _ = _dati_del_repository()
        buchi = verifica_dati.buchi_dichiarati(glossario, corpus, fonetica)
        self.assertGreater(len(buchi), 0)
        for buco in buchi:
            self.assertTrue(buco["nome"], "un buco senza nome")
            self.assertGreater(buco["quanti"], 0, buco["nome"])
            self.assertTrue(buco["nota"], "un buco senza nota: %s" % buco["nome"])

    def test_una_trascrizione_per_voce_azzera_il_conto_delle_voci_senza_suono(self):
        # Il numero deve dipendere dai dati e non da un totale scritto a mano:
        # e' l'unico modo che si aggiorni da solo quando arriva una parola nuova.
        glossario = glossario_di_prova()
        suono = [Trascrizione(id="T" + v.id, riferimento=v.id,
                              forma=v.ferrarese, ipa="/pan/", varieta="cittadino")
                 for v in glossario.voci]
        buchi = verifica_dati.buchi_dichiarati(glossario, corpus_di_prova(),
                                               Fonetica(suono))
        senza = [b for b in buchi if b["nome"] == "voci senza trascrizione IPA"]
        self.assertEqual(senza, [])

        solo_una = Fonetica(suono[:1])
        senza = [b for b in verifica_dati.buchi_dichiarati(
            glossario, corpus_di_prova(), solo_una)
            if b["nome"] == "voci senza trascrizione IPA"]
        self.assertEqual(len(senza), 1)
        self.assertEqual(senza[0]["quanti"], len(glossario.voci) - 1)
        self.assertEqual(senza[0]["totale"], len(glossario.voci))

    def test_senza_il_file_dei_suoni_i_buchi_del_suono_non_compaiono(self):
        # La funzione accetta `fonetica=None`: quando non c'e' il file non si
        # deve scrivere «0 voci senza IPA», che e' un'affermazione, non un
        # vuoto. Il vuoto vero non si dichiara.
        glossario = glossario_di_prova()
        buchi = verifica_dati.buchi_dichiarati(glossario, corpus_di_prova(), None)
        nomi = [b["nome"] for b in buchi]
        self.assertNotIn("voci senza trascrizione IPA", nomi)
        self.assertNotIn("trascrizioni non verificate da un parlante", nomi)

    def test_i_proverbi_senza_la_forma_popolare_sono_contati_uno_per_uno(self):
        # Il campo `popolare` e' quello che aspetta la voce di qualcuno. Se il
        # conto e' sbagliato, nessuno sa di doverlo riempire.
        proverbi = [
            Proverbio(id="P1", italiano="uno", ferrarese="un",
                      letterario="un", popolare="un", fonte="Ferri 1889"),
            Proverbio(id="P2", italiano="due", ferrarese="doi",
                      letterario="doi", popolare="", fonte="Ferri 1889"),
        ]
        corpus = Corpus([], proverbi=proverbi)
        buchi = verifica_dati.buchi_dichiarati(glossario_di_prova(), corpus, None)
        senza = [b for b in buchi if b["nome"] == "proverbi senza la forma che si dice"]
        self.assertEqual(len(senza), 1)
        self.assertEqual(senza[0]["quanti"], 1)
        self.assertEqual(senza[0]["totale"], 2)

    def test_le_coppie_senza_fonte_sono_quelle_che_il_controllo_C4_conta(self):
        # Il numero e' solo utile se coincide con il controllo che lo nomina.
        # Qui una coppia ha i due lati e nessuna fonte, e una ha la fonte ma
        # un lato solo: il conto deve guardare alla fonte, come guarda C4, e
        # non a `Coppia.valida()`, che guarda anche ai lati.
        coppie = [
            _coppia("F1", "uno", "un", fonte="Ferri 1889"),
            _coppia("F2", "due", "doi", fonte=""),
            _coppia("F3", "", "tre", fonte="Ferri 1889"),
        ]
        corpus = Corpus(coppie)
        problemi = verifica_dati.controlla_corpora(corpus)
        attesi = len([p for p in problemi if p.codice == "C4"])
        buchi = verifica_dati.buchi_dichiarati(glossario_di_prova(), corpus, None)
        senza_fonte = [b for b in buchi if b["nome"] == "coppie senza fonte"]
        self.assertEqual(len(senza_fonte), 1)
        self.assertEqual(senza_fonte[0]["quanti"], attesi)
        self.assertEqual(senza_fonte[0]["totale"], len(coppie))


class TestAudio(unittest.TestCase):
    def test_pubblicabile_richiede_consenso_e_licenza(self):
        solo_flag = Brano(id="A1", file="A1.mp3", pubblicabile=True)
        self.assertFalse(solo_flag.publicabile())
        con_consenso = Brano(id="A1", file="A1.mp3", pubblicabile=True,
                             consenso="scritto")
        self.assertFalse(con_consenso.publicabile())
        completo = Brano(id="A1", file="A1.mp3", pubblicabile=True,
                         consenso="scritto", licenza="CC BY 4.0")
        self.assertTrue(completo.publicabile())

    def test_un_brano_pubblicabile_senza_consenso_e_un_errore(self):
        # Il caso piu' grave che questo progetto possa commettere: pubblicare
        # la voce di qualcuno che non ha detto di si'.
        archivio = Archivio([Brano(id="A1", file="A1.mp3", pubblicabile=True,
                                   varieta="cittadino", voce="una persona")])
        codici = [p.codice for p in controlla_archivo(archivio)]
        self.assertIn("A5", codici)

    def test_consenso_senza_voce_dichiarata_e_un_errore(self):
        archivio = Archivio([Brano(id="A1", file="A1.mp3", consenso="scritto",
                                   licenza="CC BY 4.0", pubblicabile=True,
                                   varieta="cittadino", voce="")])
        self.assertIn("A9", [p.codice for p in controlla_archivo(archivio)])

    def test_lo_stato_distingue_i_brani_dai_brani_pronti(self):
        archivio = Archivio([
            Brano(id="A1", file="A1.mp3", pubblicabile=True, consenso="scritto",
                  licenza="CC BY 4.0", varieta="cittadino"),
            Brano(id="A2", file="A2.mp3", consenso="verbale", varieta="occidentale"),
        ])
        stato = archivio.stato(os.path.join(RADICE, "audio"))
        # A1 e' dichiarato pubblicabile ma il file non c'e': quindi non e'
        # pronto. Il conto pronto non si gonfia e non si svuota per meta'.
        self.assertEqual(stato["pronti"], 0)
        self.assertEqual(stato["pubblicabili"], 1)
        self.assertEqual(stato["da_verificare"], 1)

    def test_il_manifesto_di_adesso_e_vuoto(self):
        # Non e' un test sul futuro: e' la dichiarazione che oggi non c'e'
        # nessuna registrazione, e che nessuno la può fare passare per vera.
        _, _, _, _, archivio = _dati_del_repository()
        self.assertEqual(len(archivio), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)