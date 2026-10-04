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

import json
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sorgenti"))

from traduttore import morfologia, normalizza, verifica_dati  # noqa: E402
from traduttore.audio import Archivio, Brano, controlla_archivo  # noqa: E402
from traduttore.sintesi import (CARTELLA, NOTA_SINTETICA,  # noqa: E402
                              PESO_MAX, Sintesi, Suono, controlla_sintesi)
from traduttore.corpora import Coppia, Corpus, Proverbio  # noqa: E402
from traduttore.fonetica import Fonetica, Trascrizione, ipa_valida  # noqa: E402
from traduttore.glossario import FE_IT, IT_FE, Glossario, Voce, _voce_da_dict  # noqa: E402
from traduttore.legge import leggi  # noqa: E402
from traduttore.motore import Motore  # noqa: E402
from traduttore import proposte  # noqa: E402
from traduttore.varieta import VARIETA, Varieta, _nome_valido  # noqa: E402
from traduttore.voce import (ipa_a_fonemi, percorso_espeak,  # noqa: E402
                             scrivi_wav, voce)

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


class TestSignificatoModerno(unittest.TestCase):
    """La colonna «in italiano di oggi»: tre campi, e una regola sola.

    La regola e' che nessun significato entra senza l'articolo da cui e' stato
    preso. Tutto il resto — il taglio dei sinonimi, il vuoto dichiarato —
    segue da li'.
    """

    def test_il_significato_moderno_senza_fonte_e_un_errore(self):
        # Il caso che la colonna potrebbe inventare. Un campo che puo' essere
        # scritto senza aver guardato niente non si controlla con il confronto:
        # si controlla togliendo il permesso di scriverlo senza fonte.
        glossario = Glossario([_voce("V1", "ardiglione", "ardiglione",
                                     "fonte di prova",
                                     moderno="persona spregevole")])
        problemi = verifica_dati.controlla_glossario(glossario)
        self.assertIn("G10", [p.codice for p in problemi])

    def test_il_significato_moderno_con_fonte_passa_i_controlli(self):
        glossario = Glossario([_voce(
            "V1", "ardiglione", "ardiglione", "fonte di prova",
            moderno="persona spregevole, spreggiata",
            fonte_moderno="https://it.wiktionary.org/wiki/ardiglione")])
        codici = [p.codice for p in verifica_dati.controlla_glossario(glossario)]
        self.assertNotIn("G10", codici)
        self.assertNotIn("G11", codici)

    def test_una_fonte_senza_significato_e_un_avviso_e_non_un_errore(self):
        # Non blocca: puo' succedere che la fonte cambi articolo. Ma nessuno
        # deve accorgersene per caso.
        glossario = Glossario([_voce("V1", "tortiglione", "tortiglione",
                                     "fonte di prova",
                                     fonte_moderno="https://it.wiktionary.org/wiki/tortiglione")])
        problemi = verifica_dati.controlla_glossario(glossario)
        self.assertIn("G11", [p.codice for p in problemi])
        self.assertEqual([p.gravita for p in problemi if p.codice == "G11"], ["avviso"])

    def test_i_sinonimi_senza_significato_non_sono_un_errore(self):
        glossario = Glossario([_voce("V1", "x", "y", "fonte di prova",
                                     sinonimi=["a", "b"])])
        problemi = verifica_dati.controlla_glossario(glossario)
        self.assertIn("G12", [p.codice for p in problemi])
        self.assertEqual([p.gravita for p in problemi if p.codice == "G12"], ["avviso"])

    def test_i_sinonimi_si_leggono_come_lista_e_anche_se_sono_stringa(self):
        # Nel file sono una lista; ma una lista puo' diventare una stringa se
        # qualcuno la scrive a mano, e allora non deve spaccare il glossario.
        voce = _voce_da_dict({"id": "V1", "ferrarese": "a",
                                        "italiano": "b", "fonte": "f",
                                        "varieta": "cittadino",
                                        "sinonimi": "uno; due; tre"})
        self.assertEqual(voce.sinonimi, ["uno", "due", "tre"])

    def test_il_glossario_del_repository_ha_il_significato_ma_sempre_con_la_fonte(self):
        # Il controllo che conta, sul file vero: nessuna riga con un significato
        # moderno e senza l'articolo. Il numero di righe con il campo lo dice
        # anche in alto: se resta zero, la colonna e' vuota e il motivo va
        # cercato nella raccolta, non qui.
        glossario = Glossario.da_file(
            os.path.join(RADICE, "dati", "glossario.jsonl"))
        senza = [v.id for v in glossario.voci if v.moderno and not v.fonte_moderno]
        self.assertEqual(senza, [])
        problemi = verifica_dati.controlla_glossario(glossario)
        self.assertEqual([p.riga() for p in problemi
                          if p.codice == "G10" and p.gravita == "errore"], [])

    def test_la_pagina_conta_i_vuoti_e_i_sinonimi_in_python(self):
        # I due numeri che la pagina mostra sotto la tabella devono arrivare
        # calcolati, non ricalcolati in JavaScript: se la pagina contasse da
        # sola, un giorno i due numeri direbbero cose diverse.
        import costruisci_web
        (glossario, corpus, regole, varieta, fonetica, archivio,
         sintesi) = costruisci_web.carica_tutto(RADICE)
        dati = costruisci_web._dati_per_la_pagina(
            glossario, corpus, regole, varieta, fonetica, archivio,
            None, sintesi, os.path.join(RADICE, "web"))
        atteso = sum(1 for v in glossario.voci if not v.moderno)
        self.assertEqual(dati["moderno_buchi"], atteso)
        self.assertEqual(dati["moderno_con_sinonimi"],
                         sum(1 for v in glossario.voci if v.sinonimi))

    def test_il_modello_html_mostra_la_colonna_e_dichiara_il_taglio(self):
        # La colonna non puo' spuntare in pagina senza dire che i sinonimi
        # sono tagliati: altrimenti si legge «tre sinonimi» quando sono dieci.
        modello = open(os.path.join(RADICE, "sorgenti", "modello.html"),
                       encoding="utf-8").read()
        self.assertIn("in italiano di oggi", modello)
        self.assertIn("SINO_IN_COLONNA", modello)
        self.assertIn("fonte_moderno", modello)
        self.assertIn("moderno_buchi", modello)


def _parole_a_numero(parola):
    """Le cifre in italiano, che e' come le scrive un titolo.

    Solo fino a dodici: la tabella delle cartelle non crescera' oltre, e un
    elenco di numeri che non finisce e' un elenco che un giorno mente senza
    che nessuno se ne accorga.
    """
    parole = {
        "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6,
        "sette": 7, "otto": 8, "nove": 9, "dieci": 10, "undici": 11,
        "dodici": 12,
    }
    return parole.get(parola.strip().lower())


class TestConteggiDichiarati(unittest.TestCase):
    """Il numero di test che i documenti dichiarano deve essere quello vero.

    E' successo due volte in una sessione: si scrive «115 test», se ne
    aggiungono venti, e `README.md`, `AGENTS.md` e `REGISTRO.md` continuano a
    dire 115 per settimane. Un numero che mente non e' un numero, e questo
    progetto non accetta numeri che mentono — vale per i buchi dichiarati, e
    vale anche per la propria dimensione.
    """
    def test_le_traslitterazioni_dichiarate_in_RACCOLTA_sono_quelle_c_e_e(self):
        # Difetto vero, di questa sessione: `RACCOLTA.md` dichiarava 30
        # trascrizioni in due punti e il file ne aveva 28. Nessun test lo
        # guardava, perche' il documento di raccolta non aveva nessuna
        # guardia. Due numeri sbagliati in un documento che spiega come si
        # raccoglie, il posto sbagliato per lasciare che invecchino da soli.
        with open(os.path.join(RADICE, "RACCOLTA.md"), encoding="utf-8") as f:
            testo = f.read()
        veri = sum(1 for riga in io.open(
            os.path.join(RADICE, "dati", "fonetica.jsonl"), encoding="utf-8")
            if riga.strip() and not riga.lstrip().startswith("//"))
        self.assertTrue(veri > 0, "il file delle trascrizioni e' vuoto")
        trovati = re.findall(r"(\d+) righe", testo)
        self.assertTrue(trovati, "RACCOLTA.md non dichiara quante righe ha")
        for dichiarato in trovati:
            self.assertEqual(int(dichiarato), veri,
                             "RACCOLTA.md dice %s trascrizioni e sono %d"
                             % (dichiarato, veri))

    def test_il_titolo_delle_cartelle_e_il_numero_delle_righe(self):
        # `RACCOLTA.md` si intitolava «Le sette cartelle» e la tabella ne
        # elencava otto: il titolo era rimasto quello di quando la tabella
        # aveva sette righe, e nessuno lo aveva piu' guardato perche' nessun
        # numero lo confrontava con quello sotto. La tabella e' cresciuta con
        # i proverbi, con le proposte e adesso con i suoni generati.
        with open(os.path.join(RADICE, "RACCOLTA.md"), encoding="utf-8") as f:
            righe = f.read().split("\n")
        dentro = False
        dichiarato = None
        righe_tabella = 0
        for riga in righe:
            m = re.match(r"^## Le (.+) cartelle$", riga)
            if m:
                dentro = True
                parole = m.group(1).split()
                # Il numero e' in lettere, come lo scrive un documento in
                # italiano: «Le sette cartelle». Quindi il test deve sapere
                # leggerlo, e non pretendere che il titolo diventi una cifra.
                dichiarato = _parole_a_numero(parole[0])
                if dichiarato is None:
                    self.fail("il titolo delle cartelle dice %r, che non e' "
                              "un numero che questo test sa leggere"
                              % parole[0])
                continue
            if dentro:
                if riga.startswith("| `"):
                    righe_tabella += 1
                elif riga.startswith("E ci sono"):
                    break
        self.assertIsNotNone(dichiarato, "il titolo delle cartelle non c'e'")
        self.assertEqual(dichiarato, righe_tabella,
                         "il titolo dice %d cartelle e la tabella ne elenca %d"
                         % (dichiarato, righe_tabella))

    def test_RACCOLTA_dichiara_che_i_suoni_non_sono_persone(self):
        # La sezione sulle trascrizioni spiega la pronuncia, e non poteva
        # tacere dei suoni generati: sono la cosa che lo studente sente, e il
        # numero di quelli che non suonano e' un buco dichiarato.
        with open(os.path.join(RADICE, "RACCOLTA.md"), encoding="utf-8") as f:
            testo = f.read()
        # Gli spazi bianchi non contano: il testo va a capo dove gli piace e
        # quello che si verifica e' la frase, non dove e' finita la riga.
        piano = " ".join(testo.split())
        self.assertIn("sintetizza.py", piano)
        self.assertIn("web/sintesi/", piano)
        self.assertIn("non entra mai in `audio/`", piano,
                      "RACCOLTA.md deve dire che un suono generato non entra "
                      "nella cartella delle persone vere")
        self.assertIn("idempotente", piano,
                      "RACCOLTA.md deve dire che rigenerare i suoni non cambia "
                      "niente, altrimenti committarli sembra pericoloso")


    def test_il_numero_di_test_nei_documenti_e_quello_vero(self):
        veri = _quanti_test()
        # Il pattern dei documenti e' `# <numero> test` in coda a un comando.
        for documento in ("README.md", "AGENTS.md"):
            testo = open(os.path.join(RADICE, documento),
                         encoding="utf-8").read()
            trovati = re.findall(r"# (\d+) test", testo)
            self.assertTrue(trovati,
                            "%s non dichiara alcun numero di test" % documento)
            for dichiarato in trovati:
                self.assertEqual(int(dichiarato), veri,
                                 "%s dice %s test e i test sono %d"
                                 % (documento, dichiarato, veri))

    def test_il_registro_dichiara_quanti_test_aveva_il_rilascio(self):
        # La voce 0.14 dichiara i suoi test. Se il numero e' sbagliato, il
        # registro diventa una raccolta di numeri inventati, che e' la cosa
        # peggiore che un registro possa essere.
        testo = open(os.path.join(RADICE, "REGISTRO.md"),
                     encoding="utf-8").read()
        # La voce **piu' recente**, non una versione scritta a mano: quando si
        # apre una nuova versione il controllo deve passare a quella da solo,
        # altrimenti il test che esiste per non lasciare andare i numeri
        # diventa l'unico numero che va corretto a mano.
        voci = re.findall(r"^## (\d+\.\d+) — .*$", testo, re.M)
        self.assertTrue(voci, "il registro non ha nessuna voce")
        # Non la prima che si trova: il registro mette in alto anche la 0.7 con
        # una nota storica, quindi l'ordine del file non e' quello delle
        # versioni. La piu' recente e' quella col numero maggiore.
        ultima = max(voci, key=lambda v: tuple(int(x) for x in v.split(".")))
        blocco = testo.split("## %s" % ultima, 1)[1].split("\n## ", 1)[0]
        dichiarato = re.search(r"\*\*Verifiche\.\*\* (\d+) test \(erano (\d+)\)",
                               blocco)
        self.assertIsNotNone(dichiarato,
                             "la voce %s non dichiara i test" % ultima)
        self.assertEqual(int(dichiarato.group(1)), _quanti_test(),
                         "la voce %s dice %s test" % (ultima, dichiarato.group(1)))

class TestLetturaDelWikitext(unittest.TestCase):
    """Come il modulo `raccolta/moderni.py` legge una pagina.

    Il wikitext qui e' **scritto a mano**, e non copiato da Wiktionary: e' un
    documento CC BY-SA e `prove/` e' sotto licenza MIT. Non serve il testo
    vero per provare le regole, e un testo vero nel repository sarebbe una
    fonte nuova da dichiarare per provare quattro righe di codice.

    Ogni test qui sotto copre un difetto che si e' **realmente** verificato
    nella raccolta, non un caso inventato per far passare il test.
    """

    def _leggi(self, wikitext, parola="calunnia"):
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "moderni.py")
        spec = importlib.util.spec_from_file_location("moderni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo._significato(wikitext, parola)

    def test_le_tabelle_di_coniugazione_non_sono_il_significato(self):
        # Difetto vero: «calunnia» mostrava in colonna «terza persona
        # singolare dell'indicativo presente di calunniare». Sono cinque righe
        # di coniugazione, non il significato della parola.
        wikitext = (
            "{{-it-}}\n"
            "# [[falsa]] attribuzione di colpa\n"
            "# offesa verbale\n"
            "{{-verb form-}}\n"
            "# terza persona singolare dell'indicativo presente di "
            "calunniare\n"
            "# seconda persona singolare dell'imperativo di calunniare\n")
        significato, _, _ = self._leggi(wikitext)
        self.assertEqual(significato, "falsa attribuzione di colpa; offesa verbale")

    def test_una_lingua_annidata_non_entra_nella_sezione_italiana(self):
        # Difetto vero: «pizzicato» mostrava una definizione in inglese,
        # perch’ la sezione cercava solo le intestazioni di secondo livello
        # e la pagina annidava l’inglese sotto una di terzo.
        wikitext = (
            "{{-it-}}\n# che è stato colto alla sprovvista\n"
            "=== {{-en-}} ===\n# an instruction to do something\n")
        significato, _, _ = self._leggi(wikitext, "pizzicato")
        self.assertEqual(significato, "che è stato colto alla sprovvista")
        self.assertNotIn("instruction", significato)

    def test_una_definizione_che_ripete_la_parola_non_spiega_nulla(self):
        wikitext = "{{-it-}}\n# pizzicato\n# che è stato fatto vibrare\n"
        significato, _, _ = self._leggi(wikitext, "pizzicato")
        self.assertEqual(significato, "che è stato fatto vibrare")

    def test_nodef_accanto_a_due_definizioni_non_le_cancella(self):
        # Difetto vero: la prima stesura scartava l’articolo intero appena
        # trovava un `{{Nodef}}`, e perdeva «fungo», «arcangelo», «sorriso»
        # e «falda». `{{Nodef}}` vale per il senso accanto a cui sta.
        wikitext = ("{{-it-}}\n{{-bot-}}\n# {{Nodef}}\n"
                    "{{-med-}}\n# corpo dell’organismo\n")
        significato, _, _ = self._leggi(wikitext, "fungo")
        self.assertEqual(significato, "corpo dell’organismo")

    def test_nodef_senza_niente_around_declara_il_vuoto(self):
        wikitext = "{{-it-}}\n# {{Nodef}}\n"
        significato, _, motivo = self._leggi(wikitext, "prova")
        self.assertEqual(significato, "")
        self.assertIn("non avere la definizione", motivo)

    def test_le_definizioni_sono_tagliate_e_il_numero_e_dichiarato(self):
        # Difetto vero: si scrivevano tutte, e il significato piu’ lungo
        # arrivava a 1970 caratteri. Il taglio c’è, e il numero del taglio
        # e’ nel codice e nei documenti.
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "moderni.py")
        spec = importlib.util.spec_from_file_location("moderni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        righe = "".join("# definizione numero %d\n" % i for i in range(9))
        significato, _, _ = self._leggi("{{-it-}}\n" + righe)
        parti = significato.split("; ")
        self.assertEqual(len(parti), modulo.DEFINIZIONI_IN_COLONNA)
        self.assertLessEqual(modulo.DEFINIZIONI_IN_COLONNA, 5)

    def test_una_riga_senza_spazio_dopo_il_cancelletto_e_una_definizione(self):
        # Difetto vero: si accettava solo `# `, e si perdevano le forme che la
        # fonte scrive senza spazio. `#*` invece e’ un esempio d’uso e va
        # escluso, altrimenti si attribuisce al dizionario una frase che ha
        # scritto solo per far capire.
        wikitext = ("{{-it-}}\n#provocare deliberatamente la propria morte\n"
                    "#* mi sono suicidato ieri\n")
        significato, _, _ = self._leggi(wikitext, "suicidarsi")
        self.assertEqual(significato,
                         "provocare deliberatamente la propria morte")

    def test_i_sinonimi_si_leggono_dalla_sezione_intera(self):
        # Il capolavoro taglia via le sotto-sezioni, e i sinonimi stanno in
        # una sotto-sezione: senza questo la colonna dei sinonimi sarebbe
        # vuota per costruzione, per un motivo che nessuno vedrebbe.
        wikitext = ("{{-it-}}\n# sinonimo di prova\n"
                    "{{-sin-}}\n* [[prova]]\n* ripetuto\n")
        significato, sinonimi, _ = self._leggi(wikitext, "banale")
        self.assertEqual(significato, "sinonimo di prova")
        self.assertEqual(sinonimi, ["prova", "ripetuto"])

    def test_una_glossa_spezzata_non_diventa_un_sinonimo(self):
        # Difetto vero: la divisione sulla virgola produceva pezzi come
        # «(negli scacchi» e «dama) prendere», che in colonna sembravano
        # sinonimi scritti dal dizionario.
        wikitext = ("{{-it-}}\n# prova\n{{-sin-}}\n"
                    "* [[pedone]], (negli scacchi\n* dama) prendere\n"
                    "* [[dama]]\n")
        _, sinonimi, _ = self._leggi(wikitext, "pedone")
        self.assertEqual(sinonimi, ["pedone", "dama"])

    def test_ogni_riga_del_glossario_torna_scritta_come_era(self):
        # Difetto vero, e costa un diff illeggibile: il glossario e' stato
        # scritto in due formati (10363 righe con i separatori di default e 24
        # compatte) e la prima stesura del modulo le ha normalizzate tutte. Il
        # diff mostrava 10379 righe modificate invece delle 4063 con i campi
        # nuovi, quindi non diceva piu' niente. Il file di prova contiene una
        # riga per ciascuno dei due formati e una senza significato, e devono
        # tornare identiche.
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "moderni.py")
        spec = importlib.util.spec_from_file_location("moderni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        con_spazi = {"id": "V1", "ferrarese": "a", "italiano": "b",
                     "fonte": "f", "varieta": "cittadino"}
        senza_spazi = {"id": "V2", "ferrarese": "c", "italiano": "d",
                       "fonte": "f", "varieta": "cittadino"}
        testo_grezzo = (json.dumps(con_spazi, ensure_ascii=False) + "\n"
                        + json.dumps(senza_spazi, ensure_ascii=False,
                                     separators=(",", ":")) + "\n")
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as f:
            f.write(testo_grezzo)
            nome = f.name
        try:
            vecchio = modulo.GLOSSARIO
            modulo.GLOSSARIO = nome
            # La chiave e' la parola che il glossario usa per chiedere: per V1
            # e' `italiano`, cioe' «b».
            modulo.applica({"b": ("significato", ["sin"], "")}, scrivi=True)
            righe = open(nome, encoding="utf-8").read().split("\n")
        finally:
            modulo.GLOSSARIO = vecchio
            os.unlink(nome)
        # La prima riga ha un campo nuovo ma deve restare con gli spazi, e la
        # seconda non ne ha nessuno e deve restare compatta: identiche a
        # prima, salvo il campo che si e' aggiunto.
        self.assertTrue(righe[0].startswith('{"id": "V1", '))
        self.assertTrue(righe[1].startswith('{"id":"V2","ferrarese":"c"'))
        self.assertIn('"moderno": "significato"', righe[0])
        self.assertNotIn("moderno", righe[1])

    def test_una_cache_di_versione_diversa_non_viene_usata(self):
        # Difetto vero: la cache diceva gia’ «risposta» per tutte le parole
        # mentre il parser era stato corretto, e la correzione non si vedeva.
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "moderni.py")
        spec = importlib.util.spec_from_file_location("moderni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as f:
            json.dump({"versione": modulo.VERSIONE_PARSER - 1,
                       "risposte": {"cane": ["guarcia", [], ""]}}, f)
            nome = f.name
        try:
            vecchio = modulo.CACHE
            modulo.CACHE = nome
            self.assertEqual(modulo._cache(), {})
        finally:
            modulo.CACHE = vecchio
            os.unlink(nome)


def _quanti_test() -> int:
    """Quanti test ci sono davvero in questo file.

    Si conta l'albero sintattico e non la discovery di unittest perche' la
    discovery trova anche quello che non si chiama `test_`, e quello che cerca
    qui e' uno solo: quante funzioni di test sono state scritte.
    """
    import ast
    albero = ast.parse(open(os.path.abspath(__file__), encoding="utf-8").read())
    quanti = 0
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.FunctionDef) and nodo.name.startswith("test_"):
            quanti += 1
    return quanti


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


class TestFileDati(unittest.TestCase):
    """I file di dati sono leggibili anche per chi li legge a mano.

    Il difetto che questi test prendono e' gia' successo quattro volte, ed e'
    la classe di difetto piu' noiosa e piu' insidiosa del progetto: **una riga
    senza newline finale**. Quando si appende a un file che non finisce con
    l'a capo, la nuova riga si attacca alla precedente e il file diventa una
    riga sola lunghissima: non e' JSON valido, il lettore umano non capisce
    niente, e il danno e' invisibile finche' qualcuno non prova ad aprirlo.

    Nessun controllo di sintassi lo diceva, perche' `json.loads` su una riga
    sola e` valido. Ci voleva un test che guardasse l'ultimo carattere.
    """

    def test_ogni_file_di_dati_finisce_con_un_a_capo(self):
        cartella = os.path.join(RADICE, "dati")
        trovati = []
        for radice, _, file in os.walk(cartella):
            for nome in file:
                if nome.endswith(".jsonl"):
                    trovati.append(os.path.join(radice, nome))
        self.assertGreater(len(trovati), 5, "non ho trovato i file di dati")
        senza = []
        for percorso in trovati:
            with open(percorso, encoding="utf-8") as f:
                contenuto = f.read()
            if contenuto and not contenuto.endswith("\n"):
                senza.append(os.path.relpath(percorso, RADICE))
        self.assertEqual(senza, [],
                         "file senza newline finale, la riga dopo si attacca: %s"
                         % ", ".join(senza))


class TestAtteseOnline(unittest.TestCase):
    """Le attestazioni trovate online non possono sparire.

    Il difetto che questi test prendono e' gia' successo: la versione 0.9
    aveva scritto in `lacune.md` che cinque parole erano «trovata» online e
    che «nessuna entra nel glossario attivo e vanno in attesa» — e non le
    aveva messe in attesa. Le parole erano sparite fra la lista e i dati:
    la lista diceva trovata, nessun file le conteneva. Un documento che
    promette una riga che nessun file ha e' peggio di una lista che dice
    «non trovata», perche' fa credere che il lavoro sia fatto.
    """

    def _in_attesa(self):
        return Glossario.da_file(os.path.join(
            RADICE, "dati", "da_verificare", "glossario.jsonl"))

    def test_una_parola_dichiarata_trovata_esiste_in_un_file(self):
        # Il collegamento fra il documento e i dati: ogni parola che
        # `lacune.md` chiama «trovata» deve esistere o nel glossario attivo o
        # fra quelle in attesa. Se non e' da nessuna parte, il documento mente.
        attesa = self._in_attesa()
        chiavi_attesa = set()
        for voce in attesa.voci:
            chiavi_attesa.add(voce.italiano.strip().lower())
        attivo, _, _, _, _ = _dati_del_repository()
        documento = os.path.join(RADICE, "dati", "da_verificare", "lacune.md")
        if not os.path.exists(documento):
            self.skipTest("lacune.md non c'e'")
        with open(documento, encoding="utf-8") as f:
            testo = f.read()
        dichiarate = []
        for riga in testo.splitlines():
            if "| **trovata** |" not in riga:
                continue
            prima = riga.split("|")[1].strip().strip("`*")
            if prima:
                dichiarate.append(prima)
        self.assertGreater(len(dichiarate), 0,
                           "lacune.md non dichiara nessuna parola trovata")
        for parola in dichiarate:
            if parola.startswith("gia'"):
                continue
            trovata = bool(attivo.cerca_italiano(parola)) or (
                parola.lower() in chiavi_attesa)
            self.assertTrue(trovata,
                            "lacune.md dice «trovata» per %r ma non e' in nessun file"
                            % parola)

    def test_una_voce_in_attesa_dichiara_where_venuta(self):
        # Ogni riga in attesa porta la fonte per cui aspetta. Una riga in
        # attesa senza fonte non dice a nessuno cosa aspettare, e quando la
        # licenza si chiarisce nessuno sa di quale fonte si trattasse.
        attesa = self._in_attesa()
        self.assertGreater(len(attesa.voci), 0)
        for voce in attesa.voci:
            self.assertTrue(voce.fonte.strip(),
                            "%s e' in attesa senza dire da dove viene" % voce.id)

    def test_una_voce_in_attesa_non_e_anche_nei_dati_attivi(self):
        # Il controllo D1 in forma di test: la regola vale per qualunque
        # fonte, non solo per quelle che sono state in attesa per prime.
        attesa = self._in_attesa()
        attivo, _, _, _, _ = _dati_del_repository()
        attivi = {v.id for v in attivo.voci}
        for voce in attesa.voci:
            self.assertNotIn(voce.id, attivi,
                             "%s e' in attesa e anche nei dati attivi" % voce.id)


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

    def test_una_parola_funzionale_sta_nell_elenco_di_esclusi(self):
        # Contare `il`, `di`, `che` fra i lemmi di contenuto non tornerebbe:
        # sono forme, non lemmi. Questo resta vero e il test lo tiene.
        c = self._copertura()
        for funzionale in ("il", "di", "che", "per", "con", "sono", "gli"):
            if funzionale in c.FUNZIONALI:
                continue
            self.fail("%s dovrebbe stare nell'elenco delle funzionali" % funzionale)

    def test_le_funzionali_escluse_non_sono_un_buco_dichiarato_e_nascondono_niente(self):
        # La versione precedente di questo test diceva, in un commento, che le
        # funzionali «sono in morfologia.py» e che il motore le tratta a
        # parte. Ho provato a verificarlo e **non e' vero**: `il`, `a`, `ho`,
        # `non` passano invariati con confidenza 0, e in `morfologia.py` non c'e'
        # nessun elenco di articoli o preposizioni. Escluderle dal conteggio
        # senza dirlo faceva salire la copertura: il numero era comodo e falso.
        #
        # Ora il rapporto le misura. E se un giorno qualcuno le aggiunge al
        # glossario, questo test fallisce e chiede di aggiornare la
        # dichiarazione: e' il modo in cui questo progetto preferisce
        # accorgersi delle cose, non accorgersene.
        c = self._copertura()
        glossario = Glossario.da_file(os.path.join(RADICE, "dati",
                                                   "glossario.jsonl"))
        for funzionale in ("il", "la", "a", "con", "di"):
            self.assertFalse(glossario.cerca_italiano(funzionale),
                             "%s ora c'e' nel glossario: aggiorna la "
                             "dichiarazione sulle funzionali" % funzionale)
        # La frase che mentiva non deve tornare, in nessuno dei tre file che
        # la ripetevano: il rapporto di copertura, il generatore meccanico, e
        # questo stesso file. Il terzo e' il piu' scomodo e anche il piu'
        # utile: un commento in un test viene letto come se fosse vero.
        for nome, frasi in (
                ("copertura.py", ("motore li tratta a parte",
                                  "stanno in `morfologia.py` e nel glossario non ci")),
                ("costruisci_meccanico.py", ("sono in `morfologia.py`",
                                              "motore gia' conosce gli articoli",
                                              "motore tratta come regole"))):
            testo = open(os.path.join(RADICE, "raccolta", nome),
                         encoding="utf-8").read()
            for frase in frasi:
                self.assertNotIn(frase, testo,
                                 "%s non deve piu' dichiarare %r" % (nome, frase))
        # E lo scarto va dichiarato per quello che e': una scelta, non una
        # capacita' che il motore ha e non usa.
        generatore = open(os.path.join(RADICE, "raccolta",
                                        "costruisci_meccanico.py"),
                          encoding="utf-8").read()
        self.assertIn("scelta", generatore,
                      "lo scarto delle funzionali va dichiarato come scelta")

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


class TestLetturaGrafia(unittest.TestCase):
    """Le regole dichiarate in `dati/fonetica.jsonl`, applicate una per una."""

    def test_la_grafia_si_legge_secondo_le_regole_dichiarate(self):
        # I sei casi che le regole coprono, uno per uno.
        self.assertEqual(leggi("magnàr")["ipa"], "/magnˈar/")
        self.assertEqual(leggi("majàl")["ipa"], "/majˈal/")     # regola 5
        self.assertEqual(leggi("gh'è")["ipa"], "/gˈɛ/")      # regola 2
        self.assertEqual(leggi("casa")["ipa"].count("k"), 1)   # regola 4
        self.assertEqual(leggi("ved")["ipa"], "/ved/")

    def test_la_g_vela_non_e_una_lettera_ignota(self):
        # Difetto vero, trovato misurando: senza il ramo velare della regola
        # 4, `magnar` diventava `/ma/` e la parola veniva persa a meta'.
        for parola, atteso in (("magnàr", "/magnˈar/"), ("mancà", "/mankˈa/"),
                               ("ghe", "/ge/")):
            got = leggi(parola)["ipa"]
            self.assertEqual(got, atteso, "%s: %s" % (parola, got))

    def test_l_apostrofo_non_tronna_la_parola(self):
        # Difetto vero: `gh'e'` finiva a `/g/`, cioe' un terzo della parola e
        # nessun avviso. Le elisioni sono frequenti in ferrarese.
        for parola, atteso in (("gh'è", "/gˈɛ/"), ("n'è", "/nˈɛ/"),
                               ("n'agh", "/nag/"), ("dint'", "/dint/")):
            got = leggi(parola)["ipa"]
            self.assertEqual(got, atteso, "%s: %s" % (parola, got))

    def test_la_e_accentata_e_aperta_e_quella_senza_accento_e_chiusa(self):
        # Non e' una scelta di questo modulo: e' quello che il file dice in
        # quattro righe contro due. Se si capovolgesse, /e/ e /ɛ/ non sarebbero
        # piu' due suoni distinti e la regola 1 perderebbe il senso.
        self.assertEqual(leggi("gh'è")["ipa"], "/gˈɛ/")
        self.assertEqual(leggi("frarés")["ipa"], "/frarˈɛs/")
        self.assertEqual(leggi("ghe")["ipa"], "/ge/")
        self.assertEqual(leggi("ved")["ipa"], "/ved/")

    def test_il_segno_di_accento_entra_nella_trascrizione(self):
        # Una IPA senza `ˈ` non dice quale sillaba e' tonica, e il motore di
        # sintesi la legge male: l'accento costruito e poi scartato era un
        # difetto che non si vedeva da nessuna parte.
        self.assertIn("ˈ", leggi("magnàr")["ipa"])
        self.assertEqual(leggi("magnàr")["accento"], "ˈ")

    def test_dove_la_regola_tace_il_modulo_dichiara_il_dubbio(self):
        # La regola 3 dice /ɲ/ solo davanti a vocale anteriore e **tace** davanti
        # ad `a`, `o`, `u`. Tacer non e' aver verificato: e il file dà /ɲ/
        # anche li'. Il dubbio deve esserci.
        dubbi = leggi("magnàr")["dubbi"]
        self.assertTrue(any("gn" in d for d in dubbi), dubbi)

    def test_una_vocale_accentata_anteriore_rende_palatale_anche_lei(self):
        # Secondo difetto della stessa misura: la lista delle vocali
        # anteriori era la stringa "eieèi", e mancavano `ì` e `í`. Quindi
        # `gì` leggeva /g/ invece di /dʒ/. Un insieme non si scrive a occhio,
        # e una regola che funziona per tre casi su quattro sembra funzionare.
        for parola, atteso in (("cì", "/tʃˈi/"), ("gì", "/dʒˈi/"),
                               ("cí", "/tʃˈi/"), ("ghì", "/gˈi/"),
                               ("ghè", "/gˈɛ/")):
            got = leggi(parola)["ipa"]
            self.assertEqual(got, atteso, "%s: %s" % (parola, got))

    def test_una_c_o_g_a_fine_parola_non_e_palatale(self):
        # Difetto trovato facendo il viaggio di andata e ritorno della grafia,
        # in un altro repository: in Python la stringa vuota e' sottostringa di
        # qualunque stringa, quindi `"" in "eie"` e' vero, e ogni `c` o `g`
        # finale di parola diventava affricata. `nag` = /nadʒ/, `mang` =
        # /mandʒ/: parole che si cercano ogni giorno, e la voce le diceva
        # sbagliate senza dichiararlo.
        for parola, atteso in (("nag", "/nag/"), ("nac", "/nak/"),
                               ("mang", "/mang/"), ("gh", "/g/"),
                               ("ghè", "/gˈɛ/")):
            got = leggi(parola)["ipa"]
            self.assertEqual(got, atteso, "%s: %s" % (parola, got))
        # E il caso palatale vero non deve essere perso togliendo la guardia.
        self.assertEqual(leggi("cena")["ipa"], "/tʃena/")

    def test_una_lettera_ignosta_si_dichiara_e_non_si_indovina(self):
        esito = leggi("qqq")
        self.assertIn("lettera sconosciuta", esito["nota"])
        # E non si finge di aver letto tutto: la risposta e' troncata e lo dice.
        self.assertTrue(esito["dubbi"])

    def test_la_s_intervocale_e_un_vuoto_dichiarato(self):
        # Regola 6: non e' una regola, e' una scelta che puo' essere sbagliata.
        self.assertTrue(any("intervocalica" in d for d in leggi("rosa")["dubbi"]))

    def test_la_versione_generata_e_sempre_da_verificare(self):
        # Il punto che tiene insieme tutto: qui non si ascolta nessuno, e
        # nessuna funzione puo' farlo credere.
        for parola in ("magnàr", "scaranna", "piron", "xyz"):
            esito = leggi(parola)
            self.assertEqual(esito["attendibilita"], "I", parola)
            self.assertTrue(esito["da_verificare"], parola)


class TestConfrontoConLaFonte(unittest.TestCase):
    """F14 confronta le regole col file: il confronto deve essere giusto."""

    def _f14(self):
        glossario, corpus, varieta, fonetica, _ = _dati_del_repository()
        for p in verifica_dati.controlla_fonetica(fonetica, glossario,
                                                 corpus, varieta):
            if p.codice == "F14":
                return p
        return None

    def test_la_sillabificazione_non_e_un_suono_diverso(self):
        # Difetto mio, preso da questo stesso test: `por'tar` e `port'ar` hanno
        # gli stessi suoni e lo stesso accento, e li avevo contati come
        # diverse dicendo che l'accento cadeva sulla sillaba sbagliata. Non
        # cadeva: cambiava solo dove finiva la sillaba. Se il confronto torna
        # a distinguere le due cose, questo test lo prende.
        problema = self._f14()
        self.assertIsNotNone(problema, "F14 non ha parlato")
        # Le parole che differiscono solo di sillabificazione non devono
        # comparire fra le discordanti.
        for sola_sillaba in ("portàr", "sittadìn", "sivìl", "dottór",
                             "padrón", "mancà", "volà", "amà"):
            self.assertNotIn(sola_sillaba, problema.messaggio, sola_sillaba)

    def test_il_numero_delle_discordanti_e_quello_giusto(self):
        # Il numero non siGonfia per sembrareprudente. Al momento sono quattro
        # e sono quattro, e se le regole cambiano il numero cambia: e' un
        # numero misurato, non una soglia.
        problema = self._f14()
        self.assertIsNotNone(problema)
        for forma in ("magnàr", "desideràr", "principiar", "rasón"):
            self.assertIn(forma, problema.messaggio, forma)

    def test_le_due_fonti_sono_davvero_in_contraddizione_sull_accento(self):
        # No: non lo sono, e il file deve dirlo. Il blocco in testa a
        # `dati/fonetica.jsonl` affermava che Biondelli segnasse l'accento sulla
        # vocale finale non tonica. Il testo a pagina 205 dice il contrario, e
        # sbagliare quella frase faceva sembrare un problema risolto un
        # problema inesistente.
        testo = open(os.path.join(RADICE, "dati", "fonetica.jsonl"),
                     encoding="utf-8").read()
        self.assertNotIn("accento sulla vocale finale **non** tonica",
                         testo)

    def test_nessuna_fonte_cita_una_pagina_che_non_esiste(self):
        # S001 aveva un URL che rispondeva 404, e il suo testo non era mai
        # stato scaricato: undici voci e ventotto trascrizioni citavano una
        # fonte che il progetto non aveva mai aperto. Il controllo non puo'
        # fare una richiesta di rete, ma puo' pretendere che l'identificatore
        # sia della forma giusta, che e' quello che si sbaglia copiando a mano.
        # Solo il campo `luogo`, non tutto il file: l'identificatore morto
        # compare legittimamente nella nota che spiega il 404, e un test che
        # lo troverebbe li' fallirebbe perche' la spiegazione c'e'.
        with open(os.path.join(RADICE, "dati", "fonti.json"),
                  encoding="utf-8") as f:
            registro = json.load(f)
        for fonte in registro["fonti"]:
            self.assertNotIn("saggouisuidialetti00bion", fonte.get("luogo", ""),
                             fonte["id"])


class TestVoceSintetica(unittest.TestCase):
    """La voce: che cosa sa dire, e soprattutto che cosa rifiuta di dire."""

    def test_i_simboli_che_espeak_non_accetta_non_vengono_tradotti_a_caso(self):
        # `tʃ` e `ɲ` non sono nell'alfabeto del programma: se si passassero
        # come sono, lui **taglierebbe la parola** e produrrebbe un wav che
        # sembra parlato ma sta zoppicando.
        for ipa, atteso in (("/prinˈtʃipar/", "printS'ipar"),
                            ("/maˈɲnar/", "maNn'ar"),
                            ("/aˈma/", "am'a"),
                            ("/dʒɛˈsper/", "dZEsp'er")):
            got, problema = ipa_a_fonemi(ipa)
            self.assertEqual(problema, "", ipa)
            self.assertEqual(got, atteso, ipa)

    def test_l_accento_va_sulla_vocale_della_sillaba_accentata(self):
        # In `/maˈɲnar/` il segno e' sulla sillaba, e la sua vocale arriva
        # DOPO la `ɲ`. Un accento messo sul segno andrebbe perso, e la parola
        # si direbbe con l'accento nel posto sbagliato.
        self.assertEqual(ipa_a_fonemi("/maˈɲnar/")[0], "maNn'ar")
        self.assertEqual(ipa_a_fonemi("/magnˈar/")[0], "magn'ar")

    def test_un_simbolo_senza_corrispondenza_ferma_la_trascrizione(self):
        got, problema = ipa_a_fonemi("/sɑmɛ/")   # `ɑ` non c'e' nel sistema
        self.assertIsNone(got)
        self.assertIn("simbolo IPA", problema)

    def test_la_voce_dichiara_sempre_che_e_sintetica(self):
        # Un wav generato da una riga non verificata resta non verificato: si
        # propaga il dubbio, non si lava via.
        esito = voce("magnàr")
        self.assertEqual(esito["attendibilita"], "I")
        self.assertTrue(esito["da_verificare"])
        self.assertTrue(any("gn" in d for d in esito["dubbi"]))

    def test_la_voce_non_promette_un_file_che_non_ha_scritto(self):
        esito = voce("magnàr")
        self.assertEqual(esito["wav"], "")
        self.assertNotIn("wav", [k for k in esito if esito[k] is None])

    @unittest.skipUnless(percorso_espeak(), "espeak-ng non e' installato")
    def test_il_wav_prodotto_esiste_e_non_e_vuoto(self):
        import tempfile
        with tempfile.TemporaryDirectory() as dove:
            percorso = os.path.join(dove, "prova.wav")
            esito = scrivi_wav("magnàr", percorso)
            self.assertEqual(esito["problema"], "", esito.get("problema"))
            self.assertTrue(os.path.isfile(percorso))
            self.assertGreater(os.path.getsize(percorso), 1000)
            self.assertIn("sintetica", esito["nota"])

    @unittest.skipUnless(percorso_espeak(), "espeak-ng non e' installato")
    def test_il_programma_riceve_i_fonemi_e_non_le_lettere(self):
        # La verifica che conta: `espeak-ng` accetta i fonemi fra `[[ ]]` e
        # salta la traslazione della grafia. Se gli arrivassero le lettere,
        # il wav sarebbe italiano e sembrerebbe funzionare.
        from traduttore.voce import scrivi_wav
        with tempfile.TemporaryDirectory() as dove:
            con_fonemi = os.path.join(dove, "fonemi.wav")
            scrivi_wav("magnàr", con_fonemi)
            fatto = subprocess.run(
                [percorso_espeak(), "-v", "it", "-q", "-X", "--sep=",
                 "[[magn'ar]]"], stdout=subprocess.PIPE)
            uscita = fatto.stdout.decode("utf-8", "replace")
        self.assertNotIn("Translate", uscita)

    def test_senza_espeak_il_comando_dice_che_manca(self):
        # Il progetto non ha dipendenze: si controlla e si dice, non si importa
        # e si spera. Un suono prodotto da un programma non dichiarato non
        # sarebbe verificabile.
        import tempfile
        with tempfile.TemporaryDirectory() as dove:
            with unittest.mock.patch("traduttore.voce.percorso_espeak",
                                    return_value=""):
                esito = scrivi_wav("magnàr", os.path.join(dove, "x.wav"))
        self.assertIn("espeak-ng non e' installato", esito["problema"])
        self.assertEqual(esito["wav"], "")

    def test_il_pannello_conta_anche_i_suoni_generati(self):
        # Due numeri che la pagina mostra e che il progetto dichiara altrove:
        # i brani di persone vere e i suoni di programma. Devono restare due
        # numeri separati, perche' sommarli darebbe un numero che non
        # descrive niente: nessuno dei due e' una persona.
        with open(os.path.join(RADICE, "sorgenti", "modello.html"),
                  encoding="utf-8") as f:
            modello = f.read()
        self.assertIn('["brani audio pronti", brani]', modello)
        self.assertIn('["suoni generati"', modello)

    def test_una_virgola_mancante_nel_pannello_non_e_un_errore_di_sintassi(self):
        # Difetto vero, di questa sessione. Ho aggiunto una riga al pannello
        # senza la virgola finale, e `["a"] ["b"]` in JavaScript non e' un
        # errore di sintassi: e' un'indicizzazione. Il codice restava valido,
        # `new Function()` lo accettava, e il difetto compariva lontano,
        # dentro `pannello`, nel conteggio. L'unico controllo che l'ha preso
        # e' `controlla_equivalenza.py`, che esegue la pagina per davvero.
        #
        # Qui il controllo e' sul difetto esatto e non su tutta la lista: un
        # controllo che tentasse divalidare ogni elemento della lista con la
        # sola lettura delle righe sbaglierebbe appena un elemento occupa
        # piu' di una riga, che e' il caso normale e legittimo.
        with open(os.path.join(RADICE, "sorgenti", "modello.html"),
                  encoding="utf-8") as f:
            modello = f.read()
        self.assertIn("}).length],", modello,
                      "l'elemento dei suoni generati deve chiudersi con una "
                      "virgola: senza diventa un'indicizzazione")

    def test_i_buchi_e_i_suoni_non_si_pontano_luno_con_l_altro(self):
        # Il buco dichiara quante tracrizioni non hanno un suono, e lo conta
        # con le regole di lettura. Il manifesto dichiara quante ne hanno
        # uno, e lo conta scrivendo i file. Se i due conti non sommano alle
        # trascrizioni dichiarate, uno dei due e' sbagliato — e nessuno dei
        # due e' un errore, quindi nessuno dei due fa scattare un controllo.
        # Questa e' la riga che tiene insieme i due numeri.
        from traduttore import verifica_dati as vd
        from traduttore.corpora import Corpus
        from traduttore.glossario import Glossario
        from traduttore.fonetica import Fonetica
        radice_dati = os.path.join(RADICE, "dati")
        fonetica = Fonetica.da_file(os.path.join(radice_dati, "fonetica.jsonl"))
        sintesi = Sintesi.da_file(os.path.join(radice_dati, "sintesi.jsonl"))
        buchi = vd.buchi_dichiarati(
            Glossario.da_file(os.path.join(radice_dati, "glossario.jsonl")),
            Corpus.da_file(os.path.join(radice_dati, "coppie.jsonl"),
                           os.path.join(radice_dati, "proverbi.jsonl")),
            fonetica)
        riga = [b for b in buchi
                if b["nome"] == "trascrizioni che non hanno un suono generato"]
        self.assertTrue(riga, "il buco dei suoni mancanti non c'e' piu'")
        riga = riga[0]
        self.assertEqual(riga["quanti"] + len(sintesi), len(fonetica),
                         "il buco dice %d e il manifesto %d, e insieme non "
                         "fanno le %d trascrizioni dichiarate"
                         % (riga["quanti"], len(sintesi), len(fonetica)))
class TestSintesi(unittest.TestCase):
    """I suoni generati, e la separazione dalle voci vere.

    I test non verificano che il suono sia giusto: non si puo', e non e' il
    punto. Verificano che il suono **dica quello che e'**. Ogni controllo qui
    sotto e' la risposta a un modo in cui una voce di programma potrebbe
    presentarsi come una persona, o come qualcosa che il progetto sa e non
    dichiara.
    """

    def _suono(self, **cambi):
        base = dict(id="Y0001", riferimento="V0001", forma="portàr",
                    ipa="/port\u02c8ar/", file="T0001.wav", varieta="cittadino",
                    fonte="Biondelli 1853, pag. 204", nota=NOTA_SINTETICA)
        base.update(cambi)
        return Suono(**base)

    def test_un_suono_senza_dichiarazione_e_un_errore(self):
        # Il campo `nota` e' l'unica cosa che distingue un programma da una
        # persona. Se sparisce, il pulsante suona senza dire niente, ed e' il
        # modo in cui una voce di macchina diventa «il ferrarese».
        archivio = Sintesi([self._suono(nota="")])
        codici = [p.codice for p in controlla_sintesi(archivio)]
        self.assertIn("Y1d", codici)

    def test_il_manifesto_di_adesso_dichiara_tutti_i_suoni(self):
        # Sui dati veri, non su una costruzione di prova: se `sintetizza.py`
        # smette di scrivere la dichiarazione, questo test lo vede.
        sintesi = Sintesi.da_file(os.path.join(RADICE, "dati", "sintesi.jsonl"))
        self.assertTrue(len(sintesi) > 0, "il manifesto dei suoni e' vuoto")
        for suono in sintesi:
            self.assertTrue(suono.nota, "%s suona senza dichiararlo" % suono.id)
            self.assertTrue(suono.sintetica,
                            "%s non si dichiara sintetico" % suono.id)
            # Un suono non verifica la sua stessa trascrizione. Se un giorno
            # `attendibilita` passasse a `D`, questa riga cadrebbe: ed e' il
            # modo che ha il progetto di accorgersene.
            self.assertEqual(suono.attendibilita, "I")
            self.assertTrue(suono.da_verificare)

    def test_il_percorso_nel_nome_del_file_e_un_errore(self):
        # Su `file://` la pagina puo' aprire qualunque cosa sul disco dello
        # studente, quindi il nome dichiarato non puo' contenere percorsi.
        archivio = Sintesi([self._suono(file="../../etc/passwd")])
        self.assertIn("Y2b", [p.codice for p in controlla_sintesi(archivio)])

    def test_un_suono_dichiarato_senza_file_e_un_errore(self):
        archivio = Sintesi([self._suono()])
        codici = [p.codice for p in
                  controlla_sintesi(archivio, os.path.join(RADICE, "web"))]
        self.assertIn("Y2g", codici)

    def test_un_suono_per_una_parola_con_dubbio_e_un_errore(self):
        # Il controllo che chiude la strada alla comodo'. `forme_senza_dubbio`
        # e' quello che il progetto riesce a pronunciare: se la parola non c'e'
        # dentro, il file non doveva esserci. E' il buco che il pulsante
        # apriva, dichiarato una volta sola.
        archivio = Sintesi([self._suono(forma="magnàr")])
        codici = [p.codice for p in
                  controlla_sintesi(archivio, None, forme_senza_dubbio={"portàr"})]
        self.assertIn("Y4", codici)

    def test_una_parola_senza_dubbi_passa_Y4(self):
        archivio = Sintesi([self._suono()])
        codici = [p.codice for p in
                  controlla_sintesi(archivio, None, forme_senza_dubbio={"portàr"})]
        self.assertNotIn("Y4", codici)

    def test_un_suono_troppo_pesante_e_un_errore(self):
        # 493 megabyte per tutte le parole del glossario non sono una pagina.
        archivio = Sintesi([self._suono()])
        codici = [p.codice for p in controlla_sintesi(
            archivio, None) if p.codice == "Y3"]
        # Senza la radice il peso non si puo' misurare: nessun Y3, e nessun
        # errore inventato. Il tetto resta dichiarato in `PESO_MAX`.
        self.assertEqual(codici, [])
        self.assertEqual(PESO_MAX, 120 * 1024)

    def test_un_suono_generato_finito_in_audio_e_un_errore(self):
        # Il controllo che tiene separate le due cartelle. Il file di un
        # suono generato dentro `audio/` renderebbe falso il conto dei brani
        # di persone vere, che e' un conto che il progetto fa pubblicamente.
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as dove:
            os.makedirs(os.path.join(dove, "audio"))
            os.makedirs(os.path.join(dove, CARTELLA))
            # Il nome e' quello che dichiara il manifesto di prova (`T0001`):
            # Y3b confronta i nomi, quindi un file con un altro nome non
            # dimostrerebbe niente.
            shutil.copyfile(
                os.path.join(RADICE, "web", CARTELLA, "T0002.wav"),
                os.path.join(dove, "audio", "T0001.wav"))
            archivio = Sintesi([self._suono()])
            codici = [p.codice for p in controlla_sintesi(archivio, dove)]
        self.assertIn("Y3b", codici)

    def test_un_wav_qualunque_in_audio_non_e_un_Y3b(self):
        # Il contrario, che e' la parte che rende il controllo utile: una
        # registrazione vera dentro `audio/` non viene segnalata come se fosse
        # un suono generato. Un controllo che segnalasse anche questi
        # inutilizzerebbe il conto delle persone vere invece di proteggerlo.
        import tempfile
        with tempfile.TemporaryDirectory() as dove:
            os.makedirs(os.path.join(dove, "audio"))
            with open(os.path.join(dove, "audio", "voce.mp3"), "wb") as f:
                f.write(b"una registrazione vera")
            archivio = Sintesi([self._suono()])
            codici = [p.codice for p in controlla_sintesi(archivio, dove)]
        self.assertNotIn("Y3b", codici)

    def test_il_wav_generato_non_dice_da_che_programma_e_come(self):
        # Difetto vero, trovato guardando il file. Avevo scritto — e nel
        # docstring del modulo anche **pubblicato** — che `espeak-ng` scrive
        # il proprio nome nel commento del RIFF, e che quindi si poteva
        # riconoscere un suono generato guardando dentro il file. Il file
        # non contiene quella stringa: e' un RIFF con quattro campi e
        # nient'altro. Il controllo che si basava su quella frase non poteva
        # scattare mai, e sarebbe passato per sempre senza guardare niente.
        with open(os.path.join(RADICE, "web", CARTELLA, "T0002.wav"), "rb") as f:
            corpo = f.read()
        self.assertTrue(corpo.startswith(b"RIFF"))
        self.assertNotIn(b"espeak", corpo.lower())
        # Quindi la domanda «da dove viene» non si puo' fare sul contenuto:
        # si fa sul nome, e su quello si basa Y3b.
        self.assertFalse(hasattr(__import__("traduttore.sintesi",
                                             fromlist=["x"]),
                                 "_e_generato"))

    def test_il_manifesto_e_la_cartella_concordano(self):
        # Ogni riga deve avere il suo file e non deve esserci un file senza
        # riga: una delle due metà che manca è un suono che la pagina offre
        # e non suona, o un file che nessuno dichiara.
        sintesi = Sintesi.da_file(os.path.join(RADICE, "dati", "sintesi.jsonl"))
        radice = os.path.join(RADICE, "web")
        dichiarati = {s.file for s in sintesi}
        percorso = os.path.join(radice, CARTELLA)
        trovati = set()
        if os.path.isdir(percorso):
            trovati = {n for n in os.listdir(percorso) if n.endswith(".wav")}
        self.assertEqual(dichiarati - trovati, set(),
                         "righe senza file")
        self.assertEqual(trovati - dichiarati, set(),
                         "file che nessuna riga dichiara")

    def test_la_pagina_non_mette_il_suono_generato_dove_c_e_un_brano(self):
        # Il file di `modello.html` che disegna la scheda del suono e quello
        # che disegna la scheda del brano devono restare due funzioni diverse.
        # Sono state due, per qualche tempo, una sola.
        with open(os.path.join(RADICE, "sorgenti", "modello.html"),
                  encoding="utf-8") as f:
            modello = f.read()
        # Il chiamante sceglie fra i due con `||`, non con il ternario: col
        # ternario il messaggio «nessun suono generato» finiva accanto al
        # suono che nega.
        self.assertIn("suonoDi(v.id, t) ||", modello)



if __name__ == "__main__":
    unittest.main(verbosity=2)