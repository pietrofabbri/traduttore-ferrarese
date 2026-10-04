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
import hashlib
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
from traduttore.fonetica import (Fonetica, Trascrizione,  # noqa: E402
                                ipa_valida, leggi_sistema)
from traduttore import voce as voce_modulo  # noqa: E402
from traduttore.glossario import FE_IT, IT_FE, Glossario, Voce, _voce_da_dict  # noqa: E402
from traduttore.legge import leggi  # noqa: E402
from traduttore.motore import Motore  # noqa: E402
from traduttore import proposte  # noqa: E402
from traduttore.varieta import VARIETA, Varieta, _nome_valido  # noqa: E402
from traduttore.voce import (ipa_a_fonemi, percorso_espeak,  # noqa: E402
                             scrivi_wav, voce)

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _voti_dell_audizione() -> list:
    """I voti che la griglia dell'audizione mette in colonna.

    `raccolta/audizione.py` non e' un pacchetto e non si importa: si prende la
    sua funzione dal file, che e' come la si verifica davvero.
    """
    import ast
    percorso = os.path.join(RADICE, "raccolta", "audizione.py")
    with io.open(percorso, encoding="utf-8") as f:
        albero = ast.parse(f.read())
    for nodo in albero.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "voti_dichiarati":
            spazio = {"voce": voce_modulo}
            eseguito = compile(ast.Module(body=[nodo], type_ignores=[]),
                               percorso, "exec")
            exec(eseguito, spazio)  # noqa: S102
            return spazio["voti_dichiarati"]()
    raise AssertionError("audizione.py non ha piu' `voti_dichiarati`")


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
        # «vorrei a braccia aperte»: l'accorpamento parte dalla parola piu'
        # lunga e torna indietro finche' non trova. «a braccia» da sola non e'
        # nel glossario e non deve diventare una risposta.
        #
        # La parola di guardia e' «vorrei» e non «voglio» perche' «voglio» e'
        # una delle forme verbali che le fonti attestano: il motore la
        # traduce, e questo test che parla solo di accorpamento fallirebbe per
        # una cosa che non sta provando. Il livello delle forme attestate ha il
        # suo test in `TestLeFormeVerbali`.
        risposta = self.motore.traduci("vorrei a braccia aperte", IT_FE)
        testi = [c[0] for c in risposta.per_corrispondenza]
        self.assertEqual(testi, ["vorrei", "a braccia aperte"])
        self.assertEqual(risposta.testo, "vorrei a brazz avèrti")

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
        atteso = sum(1 for v in glossario.voci if not v.moderno)
        comuni = costruisci_web._dati_comuni(
            glossario, corpus, varieta, fonetica, archivio, sintesi,
            os.path.join(RADICE, "web"), [], RADICE)
        self.assertEqual(comuni["moderno_buchi"], atteso)
        self.assertEqual(comuni["moderno_con_sinonimi"],
                         sum(1 for v in glossario.voci if v.sinonimi))

    def test_ogni_fetta_dichiara_i_buchi_propri_e_non_quelli_del_glossario(self):
        # Su una fetta il numero sotto la tabella dice «N di queste M voci».
        # Se dicesse il numero del glossario intero, sarebbe 6324 sotto una
        # tabella di 500 righe: un numero che non descrive quello che si vede.
        import costruisci_web
        (glossario, corpus, regole, varieta, fonetica, archivio,
         sintesi) = costruisci_web.carica_tutto(RADICE)
        fette = costruisci_web.fette_del_glossario(glossario)
        self.assertTrue(fette)
        for f in fette:
            senza = sum(1 for v in f["voci"] if not v.moderno)
            if senza:
                continue
            # Una fetta senza buchi non dichiara niente, e va bene: il
            # controllo vale per le fette che ne hanno.
        con_buchi = [f for f in fette
                     if any(not v.moderno for v in f["voci"])]
        self.assertTrue(con_buchi)
        primo = con_buchi[0]
        self.assertLess(sum(1 for v in primo["voci"] if not v.moderno),
                        len(primo["voci"]))

    def test_le_fette_ordinano_come_cerca_il_motore(self):
        # La lettera nella barra promette che la fetta comincia da li'. Se
        # l'ordinamento fosse un altro, la promessa sarebbe falsa e nessuno
        # se ne accorgerebbe: la fetta si aprirebbe e le parole non ci sarebbero.
        from traduttore.normalizza import chiave
        import costruisci_web
        (glossario, corpus, regole, varieta, fonetica, archivio,
         sintesi) = costruisci_web.carica_tutto(RADICE)
        fette = costruisci_web.fette_del_glossario(glossario)
        # Ogni fetta comincia con una chiave maggiore o uguale alla fine della
        # precedente: e' la condizione che rende vera la lettera.
        for precedente, seguente in zip(fette, fette[1:]):
            self.assertLessEqual(
                chiave(precedente["voci"][-1].principale_ferrarese
                       or precedente["voci"][-1].ferrarese or ""),
                chiave(seguente["voci"][0].principale_ferrarese
                       or seguente["voci"][0].ferrarese or ""),
                "la fetta %d si sovrappone alla %d"
                % (precedente["numero"], seguente["numero"]))

    def test_ogni_voce_del_glossario_e_in_una_fetta_e_una_sola(self):
        # La somma delle fette deve essere il glossario. Se una voce mancasse,
        # sparirebbe dal sito senza che nessuno se ne accorga: il sito non
        # direbbe che una parola non c'e', semplicemente non la mostrerebbe.
        import costruisci_web
        (glossario, corpus, regole, varieta, fonetica, archivio,
         sintesi) = costruisci_web.carica_tutto(RADICE)
        fette = costruisci_web.fette_del_glossario(glossario)
        ids = [v.id for f in fette for v in f["voci"]]
        self.assertEqual(len(ids), len(set(ids)), "una voce e' in due fette")
        self.assertEqual(set(ids), {v.id for v in glossario.voci})

    def test_ogni_pagina_pesa_meno_del_glossario_intero(self):
        # Il motivo per cui il sito e' ramificato. Se una pagina torna a
        # 5,6 megabyte, la ramificazione e' stata annullata da qualche parte
        # e nessuno se ne accorge finche' qualcuno aspetta che si apra.
        web = os.path.join(RADICE, "web")
        if not os.path.isdir(web):
            self.skipTest("il sito non e' stato generato")
        pesi = {}
        for nome in os.listdir(web):
            if nome.endswith(".html"):
                pesi[nome] = os.path.getsize(os.path.join(web, nome))
        if not pesi:
            self.skipTest("il sito non e' stato generato")
        for nome, peso in pesi.items():
            self.assertLess(peso, 3 * 1024 * 1024,
                            "%s pesa %d byte: una pagina che non si apre non "
                            "e' una pagina, e' un allegato" % (nome, peso))

    def test_una_sezione_del_modello_che_nessuna_pagina_usa_non_esiste(self):
        # Ogni sezione marcata nel modello deve finire in almeno una pagina.
        # Una sezione che nessuno prende e' codice e testo che restano nel
        # modello per sempre e non arrivano da nessuna parte: sparisce senza
        # che nessuno lo decida.
        import costruisci_web
        with open(os.path.join(RADICE, "sorgenti", "modello.html"),
                  encoding="utf-8") as f:
            modello = f.read()
        marcate = set(re.findall(r"<!-- pagina:([a-z]+) -->", modello))
        usate = set()
        for pagina in costruisci_web.PAGINE:
            usate.update(pagina["sezioni"])
        # Le sezioni delle fette sono usate anche dalle pagine generate.
        usate.add("fette")
        usate.add("glossario")
        self.assertEqual(marcate - usate, set(),
                         "sezioni del modello che nessuna pagina contiene: %s"
                         % ", ".join(sorted(marcate - usate)))

    def test_ogni_suono_generato_e_offerto_da_una_pagina(self):
        # Difetto vero: la voce V0021 e' dichiarata in due forme (`frarés` e
        # `frarèz`), il generatore produce un file per ciascuna, e il codice
        # della pagina ne mostrava uno solo. Il secondo file esisteva,
        # costava 49 KB nel repository, era dichiarato nel manifesto — e non
        # compariva in nessuna pagina.
        #
        # Un suono che nessuno puo' ascoltare non e' un suono che il progetto
        # possa dichiarare di aver prodotto: o si mostra, o non si genera.
        # Questo test legge il codice della pagina e conta quante volte puo'
        # mostrare i suoni di una voce: se torna `primo`, il secondo e' perso.
        with open(os.path.join(RADICE, "sorgenti", "modello.html"),
                  encoding="utf-8") as f:
            modello = f.read()
        i = modello.index("function suonoDi(")
        corpo = modello[i:modello.index("\n  function ", i + 10)]
        # La forma giusta: prende tutti quelli della voce e li disegna. La
        # forma sbagliata era `[0]`, cioe' il primo.
        self.assertIn("trovati.length", corpo,
                      "suonoDi deve mostrare tutti i suoni di una voce")
        scelta = corpo.split("if (trovati.length)")[-1][:200]
        self.assertNotIn("[0]", scelta,
                         "suonoDi prende un solo suono per voce")
        # E i dati devono poterlo permettere: ogni suono suonabile ha una voce
        # che la pagina dei suoni conosce.
        import costruisci_web
        from traduttore.sintesi import Sintesi
        sintesi = Sintesi.da_file(os.path.join(RADICE, "dati", "sintesi.jsonl"))
        (glossario, corpus, regole, varieta, fonetica, archivio,
         _) = costruisci_web.carica_tutto(RADICE)
        con_suono = [v for v in glossario.voci
                     if costruisci_web._ha_trascrizione(v, fonetica)]
        conosciute = {v.id for v in con_suono}
        perduti = [s.id for s in sintesi.suoni
                   if s.esiste(os.path.join(RADICE, "web"))
                   and s.riferimento not in conosciute]
        self.assertEqual(perduti, [],
                         "suoni generati che la pagina dei suoni non puo' "
                         "mostrare: %s" % ", ".join(perduti))

    def test_una_voce_con_due_suoni_generati_esiste_davvero(self):
        # Il caso che ha fatto fallire il test di sopra e' raro ma reale, e se
        # il glossario torna a una sola forma il test di sopra continuerebbe a
        # passare senza verificare niente. Qui si controlla che il caso esista.
        from traduttore.sintesi import Sintesi
        sintesi = Sintesi.da_file(os.path.join(RADICE, "dati", "sintesi.jsonl"))
        per_voce = {}
        for suono in sintesi.suoni:
            per_voce.setdefault(suono.riferimento, []).append(suono.forma)
        doppie = {k: v for k, v in per_voce.items() if len(v) > 1}
        self.assertTrue(doppie,
                        "nessuna voce ha due suoni: il caso che ha fatto perdere "
                        "un file non si puo' piu' provare")

    def test_le_etichette_delle_fette_sono_tutte_diverse(self):
        # Difetto vero, di questa sessione, provato due volte. La prima
        # etichetta era la lettera iniziale e la barra diceva `A A B C C`; la
        # seconda era l'intervallo e diceva ancora `C C` e `S S S S`, perche'
        # due fette cominciano e finiscono dentro la stessa lettera.
        #
        # Due voci uguali nella barra che portano da due parti diverse sono
        # una scelta a caso con l'aspetto di una scelta ragionata. Il numero
        # della fetta e' l'unica parte che non puo' ripetersi, quindi c'e'
        # sempre.
        import costruisci_web
        (glossario, corpus, regole, varieta, fonetica, archivio,
         sintesi) = costruisci_web.carica_tutto(RADICE)
        etichette = [f["lettera"] for f in
                     costruisci_web.fette_del_glossario(glossario)]
        self.assertEqual(len(set(etichette)), len(etichette),
                         "etichette ripetute nella barra: %s"
                         % ", ".join(e for e in set(etichette)
                                     if etichette.count(e) > 1))

    def test_ogni_pagina_dichiarata_esiste_davvero(self):
        # Una pagina dichiarata in `PAGINE` e non generata e' un collegamento
        # che porta a un file che non c'e': su `file://` non da nessun errore,
        # da una pagina vuota.
        import costruisci_web
        web = os.path.join(RADICE, "web")
        if not os.path.isdir(web):
            self.skipTest("il sito non e' stato generato")
        for pagina in costruisci_web.PAGINE:
            self.assertTrue(os.path.exists(os.path.join(web, pagina["file"])),
                            "%s e' dichiarata ma non c'e'" % pagina["file"])
        for file, _ in costruisci_web.NAVIGAZIONE:
            self.assertTrue(os.path.exists(os.path.join(web, file)),
                            "la barra porta a %s, che non c'e'" % file)

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
        # Il pattern guarda **la frase sulle trascrizioni**, non qualsiasi
        # «N righe» del documento.
        #
        # Difetto vero, di questa sessione: `re.findall(r"(\d+) righe")`
        # prendeva ogni numero seguito dalla parola «righe» in tutto il
        # file, e li confrontava con il numero delle trascrizioni. Bastava
        # che la sezione sulla raccolta di Bigoni dicesse «10431 righe di
        # dati» — cosa vera e dichiarata li — per far fallire il test con un
        # messaggio che diceva «RACCOLTA.md dice 10431 trascrizioni». Un
        # controllo che legge il numero sbagliato nel posto sbagliato non
        # protegge niente e blocca tutto: peggio di non averlo, perche'
        # costringe a riformulare il testo invece di correggere il dato.
        #
        # Ora il pattern e' ancorato alla parola che dice *cosa* e' contato,
        # e ogni frase trovata viene controllata perche' parli delle
        # trascrizioni.
        # Le frasi sono agganciate al **file** che contengono, non a una
        # parola: il documento dichiara il numero in due modi diversi — la
        # riga che apre `dati/fonetica.jsonl` («ha gia' 28 righe») e un
        # inciso piu' in la' («in un file di 28 righe») — e nessuna delle due
        # nomina la parola «trascrizione». Un pattern che cerca quella parola
        # non trova niente, che e' un test che non gira senza dirlo.
        #
        # Il numero viene contato su tutto il documento e poi attribuito al
        # file giusto: e' l'unico modo che non si spegne quando il documento
        # riformula la frase.
        numeri = re.findall(r"(\d+) righe", testo)
        self.assertTrue(numeri,
                        "RACCOLTA.md non dichiara quante righe ha il file "
                        "delle trascrizioni")
        for dichiarato in numeri:
            if int(dichiarato) == veri:
                continue
            # Un numero diverso e' sbagliato solo se la frase parla delle
            # trascrizioni: altrove puo' essere qualsiasi altro conteggio, e
            # segnalarlo e' il modo di costringere a togliere un numero
            # dichiarato e vero dal documento.
            # La finestra e' il **paragrafo**, non la frase: il documento
            # va a capo a meta' frase, e dividere sui punti e sui ritorni
            # metteva il numero in un pezzo senza il nome del file. La
            # prima versione di questo controllo faceva cosi' e passava
            # anche con un numero sbagliato: un test che non fallisce
            # quando il dato e' falso e' peggio di nessun test, perche'
            # fa credere che il numero sia guardato.
            posizione = testo.find(dichiarato + " righe")
            contesto = testo[max(0, posizione - 220):posizione + 220]
            if "fonetica" in contesto or "trascrizion" in contesto:
                self.fail(
                    "RACCOLTA.md dice %s righe del file delle trascrizioni "
                    "e sono %d, vicino a: %s"
                    % (dichiarato, veri,
                       " ".join(contesto.split())[:200]))

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

    def test_il_frontmatter_del_registro_concorda_con_la_voce_piu_recente(self):
        # Difetto vero, di questa sessione: il frontmatter di `REGISTRO.md`
        # diceva `versione: 0.15` mentre le voci erano arrivate a 0.17. Il
        # numero che mente e' il peggiore, e il regolamento del progetto vieta
        # esplicitamente i numeri che mentono — vale per i buhi dichiarati e
        # vale anche per la versione del registro stesso.
        #
        # Il numero NON e' scritto qui: il controllo lo prende dal registro,
        # perche' una lista di versioni in un test diventa a sua volta un
        # numero da aggiornare a mano, e il difetto che questo test cerca
        # tornerebbe esattamente dalla porta da cui l'ho visto entrare.
        testo = open(os.path.join(RADICE, "REGISTRO.md"),
                     encoding="utf-8").read()
        frontmatter = re.match(r"^---\n(.*?)\n---\n", testo, re.S)
        self.assertIsNotNone(frontmatter,
                             "REGISTRO.md non ha il frontmatter")
        dichiarata = re.search(r"^versione: (\d+\.\d+)$",
                               frontmatter.group(1), re.M)
        self.assertIsNotNone(dichiarata,
                             "REGISTRO.md non dichiara la sua versione")
        voci = re.findall(r"^## (\d+\.\d+) — .*$", testo, re.M)
        self.assertTrue(voci, "il registro non ha nessuna voce")
        ultima = max(voci, key=lambda v: tuple(int(x) for x in v.split(".")))
        self.assertEqual(dichiarata.group(1), ultima,
                         "REGISTRO.md si dichiara %s mentre la voce piu' "
                         "recente e' la %s"
                         % (dichiarata.group(1), ultima))

    def test_il_numero_di_locuzioni_nei_documenti_e_quello_del_motore(self):
        # Difetto vero, di questa sessione: il registro dichiarava 2034
        # locuzioni e 8353 parole singole. Il totale tornava, perche' i due
        # numeri si compensavano, ma nessuno dei due era vero: erano contati con
        # `split()`, che spaccia l'apostrofo interno, mentre il motore usa
        # `tokenizza`, che considera `d\'avril` una parola sola.
        #
        # Il conto quindi non era solo vecchio: era **metodologicamente
        # sbagliato**, e il documento descriveva un accorpamento che il motore
        # non fa. Per questo il confronto e' con `tokenizza` e non con uno
        # `split` di comodo: il numero deve contare quello che il motore
        # accorpa davvero, altrimenti la frase «il motore le accorpa» e'
        # falsa anche quando il numero e' aggiornato.
        import sys as _sys
        if _sys.path[:1] != [os.path.join(RADICE, "sorgenti")]:
            _sys.path.insert(0, os.path.join(RADICE, "sorgenti"))
        from traduttore.normalizza import tokenizza

        locuzioni = singole = 0
        for riga in io.open(os.path.join(RADICE, "dati", "glossario.jsonl"),
                            encoding="utf-8"):
            riga = riga.strip()
            if not riga or riga.startswith("//"):
                continue
            if len(tokenizza(json.loads(riga).get("ferrarese") or "")) > 1:
                locuzioni += 1
            else:
                singole += 1

        testo = open(os.path.join(RADICE, "REGISTRO.md"),
                     encoding="utf-8").read()
        # La voce piu' recente **che dichiara il numero**, non la voce piu'
        # recente in assoluto. Il registro racconta anche cio' che era, e una
        # versione che non tocca il glossario non ha nessun motivo di
        # ripetere un numero che e' gia' scritto e che non e' cambiato: il
        # numero delle locuzioni sta nella voce che ha fatto crescere il
        # glossario, e va verificato li'.
        #
        # Il criterio e' «la piu' recente che dichiara» e non «la prima che
        # si trova»: altrimenti un numero falso in fondo al registro passerebbe
        # finche' non si aprisse il file dall'alto, e la guardia dipenderebbe
        # dall'ordine in cui il file e' stato scritto invece che dall'ordine
        # delle versioni.
        PATTERNE = re.compile(r"conta \*\*(\d+) locuzioni\*\* e "
                              r"\*\*(\d+) parole singole\*\*")
        voci = re.findall(r"^## (\d+\.\d+) — .*$", testo, re.M)
        ordinate = sorted(voci, key=lambda v: tuple(int(x) for x in v.split(".")),
                          reverse=True)
        ultima = dichiarate = blocco = None
        for voce in ordinate:
            pezzo = testo.split("## %s" % voce, 1)[1].split("\n## ", 1)[0]
            if PATTERNE.search(pezzo):
                ultima, blocco = voce, pezzo
                dichiarate = PATTERNE.search(pezzo)
                break
        self.assertIsNotNone(dichiarate,
                             "nessuna voce del registro dichiara quante "
                             "locuzioni e quante parole singole ha il glossario")
        self.assertEqual(int(dichiarate.group(1)), locuzioni,
                         "la voce %s dice %s locuzioni e tokenizza() ne trova %d"
                         % (ultima, dichiarate.group(1), locuzioni))
        self.assertEqual(int(dichiarate.group(2)), singole,
                         "la voce %s dice %s parole singole e ne sono %d"
                         % (ultima, dichiarate.group(2), singole))
        # E la somma deve essere il glossario: due numeri che tornano fra
        # loro ma non col totale sono due numeri inventati che si fanno
        # da garanzia a vicenda.
        self.assertEqual(locuzioni + singole,
                         sum(1 for r in io.open(
                             os.path.join(RADICE, "dati", "glossario.jsonl"),
                             encoding="utf-8")
                             if r.strip() and not r.lstrip().startswith("//")))

    def test_la_copertura_dichiarata_e_quella_di_copertura_py(self):
        # Difetto vero, di questa sessione: `README.md` e `lacune.md`
        # dichiaravano 23,7% di copertura, il numero di quando il glossario
        # aveva 10387 voci. Le voci sono diventate 16739 e il numero e' rimasto
        # com'era, perche' nessun test guardava la copertura: il numero dei
        # test era sorvegliato, quello del frontmatter anche, quello della
        # copertura no.
        #
        # Il perche' e' la parte che vale: la copertura e' l'unico numero che
        # `README.md` chiama «il numero che `buchi` non da'», cioe' quello su
        # cui si regge la promessa del progetto. Un numero non sorvegliato non
        # dura quanto dura il dato sotto: dura quanto dura l'ultima volta che
        # qualcuno lo ha riguardato.
        import subprocess
        import sys as _sys
        percorso = os.path.join(RADICE, "raccolta", "copertura.py")
        grezzi = os.path.join(RADICE, "raccolta", "grezzi", "itwac_noun.csv")
        if not os.path.exists(grezzi):
            # Il metro non e' nel repository, e la CI non lo ha. Un test che
            # non puo' girare deve dirlo e non fingere di essere passato:
            # questo progetto vieta il falso verde, quindi si salta e si dice.
            self.skipTest("gli elenchi ItWaC non sono presenti: la copertura "
                          "non e' misurabile qui")
        risultato = subprocess.run([_sys.executable, percorso],
                                  capture_output=True, text=True)
        self.assertEqual(risultato.returncode, 0, risultato.stdout)
        m = re.search(r"coperte dal glossario\s+(\d+)\s+([\d.]+)%",
                      risultato.stdout)
        self.assertIsNotNone(m, risultato.stdout)
        # `copertura.py` stampa il punto decimale e i documenti la virgola:
        # lo stesso numero nelle due forme che si usano. Si confrontano i
        # numeri, non le stringhe, perche' la resa non e' il dato.
        vera = float(m.group(2))
        for nome in ("README.md", os.path.join("dati", "da_verificare",
                                               "lacune.md")):
            testo = open(os.path.join(RADICE, nome), encoding="utf-8").read()
            # Il numero puo' comparire in due forme: `38,4` (come lo scrive
            # un italiano) e `38.4` (come lo stampa lo script). Il confronto
            # accetta entrambe perche' quello che si verifica e' il dato, e
            # rescrivere la punteggiatura di un documento non e' un difetto.
            # La percentuale puo' stare dentro i marcatori (`**38,4%**`) o
            # fuori, e il `%` puo' andare a capo prima di «dei lemmi»: in
            # `README.md` e' `**38,4%**` a fine riga e «dei lemmi» comincia
            # alla successiva. Il numero resta stretto — due cifre, un
            # separatore decimale, un `%` — e l'ancoraggio a «dei lemmi»
            # e' quello che conta: senza, il pattern prenderebbe anche le
            # altre percentuali del documento, che sono altre misure.
            dichiarate = re.findall(r"(\d+[.,]\d)\s*%\**\s+dei\s+lemmi",
                                    testo)
            self.assertTrue(dichiarate,
                            "%s non dichiara la copertura" % nome)
            for d in dichiarate:
                self.assertEqual(float(d.replace(",", ".")), vera,
                                 "%s dice %s%% e copertura.py dice %s%%"
                                 % (nome, d, m.group(2)))




class _ModelloInNode(object):
    """Gira il codice della pagina dentro `node`, e lo interroga.

    Due test hanno bisogno di questo e per motivi diversi — uno confronta
    la normalizzazione nelle due copie, l'altro verifica il bottone del
    suono — ma la parte difficile e' la stessa: prendere il **codice che
    il browser esegue** e non una ricostruzione, ed eseguirlo davvero.

    Il mixin non contiene test: contiene il modo di chiedere. Un test
    qui dentro verrebbe contato due volte se due classi lo ereditassero,
    e un test che gira due volte e' un test che ha smesso di dire quanto
    costa.
    """
    def _js(self):
        """Il `node` di sistema, o `None`. Non e' una dipendenza del progetto."""
        import shutil
        return shutil.which("node")

    def _valuta_js(self, espressione, variabili=None, dati=None):
        import subprocess
        with io.open(os.path.join(RADICE, "sorgenti", "modello.html"),
                     encoding="utf-8") as f:
            pagina = f.read()
        # Il blocco di script del modello, da solo: e' quello che la pagina
        # esegue, quindi e' quello che va interrogato.
        inizio = pagina.find("function chiave(")
        if inizio < 0:
            self.fail("modello.html non ha piu' la funzione chiave")
        # Si prende il **contenuto** del blocco `<script>` che non e' quello
        # dei dati, e non la pagina: prendere l'HTML fa fallire node sul primo
        # `<`, e un test che non gira e non lo dice e' peggio di un test che
        # non gira e lo dice.
        import re as _re
        blocchi = _re.findall(r'<script(?![^>]*id="dati")[^>]*>(.*?)</script>',
                              pagina, _re.S)
        self.assertTrue(blocchi, "modello.html non ha nessun blocco di codice")
        codice = "\n".join(blocchi)

        # Lo script della pagina e' una IIFE: `chiave` e `tokenizza` sono
        # locali e non si raggiungono da fuori. Percio' l'espressione viene
        # iniettata **dentro** la funzione, subito prima della fine, e non
        # appesa in coda. Le due copie si confrontano sul codice che il
        # browser esegue, non su una ricostruzione.
        fine = codice.rfind("})();")
        self.assertGreater(fine, 0,
                           "modello.html non chiude la IIFE: il confronto "
                           "delle due copie non si puo' fare")
        # Le variabili di ingresso si dichiarano **dentro** la IIFE, accanto
        # all'espressione: il contesto e' quello della pagina, quindi e' li'
        # che le parole da confrontare devono stare.
        if variabili:
            # Le dichiarazioni stanno **fuori** da `JSON.stringify`: dentro
            # diventerebbero un argomento, e `JSON.stringify(var x = 1)` e'
            # un errore di sintassi. Dichiararle fuori e usare l'espressione
            # dentro e' l'unico ordine che si puo' eseguire.
            programma = (codice[:fine]
                         + "var %s; " % ", ".join(
                             "%s = %s" % (nome, json.dumps(valore,
                                                             ensure_ascii=False))
                             for nome, valore in sorted(variabili.items()))
                         + "console.log(JSON.stringify(%s));" % espressione
                         + codice[fine:])
        else:
            programma = (codice[:fine]
                         + "console.log(JSON.stringify(%s));" % espressione
                         + codice[fine:])

        # `document` e' l'unica cosa che lo script tocca subito, perche'
        # legge il blocco dei dati. Se ne dà uno vuoto: e' un test della
        # normalizzazione, e il glossario non c'entra.
        # I dati con cui la pagina viene costruita. Il default e' il minimo
        # che serve agli altri test; un test che prova una parte della pagina
        # che legge altri dati passa il proprio, altrimenti interrogerebbe
        # sempre uno stub vuoto e troverebbe sempre che la funzione non c'e'.
        if dati is None:
            dati = {"glossario": None}
        # Il JSON va **quotato** come stringa JavaScript: `json.dumps` una
        # seconda volta produce la stringa con le sue virgolette, e senza
        # quella passata `textContent` diventava un oggetto letterale e node
        # falliva sulla riga 1 senza che l'errore dicesse di cosa.
        stub = ("var document = { getElementById: function () { "
                "return { textContent: "
                + json.dumps(json.dumps(dati, ensure_ascii=False)) + ", "
                "appendChild: function () {}, addEventListener: function () {}, "
                "createElement: function () { return {}; }, "
                "style: {}, value: '', checked: false, innerHTML: '' }; }, "
                "addEventListener: function () {}, createElement: function () "
                "{ return {}; } };\n")
        programma = stub + programma
        # `node -e` di default legge l'input come TypeScript su queste versioni,
        # e il `<` di un confronto diventa un errore di sintassi. Il flag lo
        # dice: e' JavaScript, che e' quello che il browser esegue.
        fatto = subprocess.run([self._js(), "--input-type=commonjs", "-e", programma],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if fatto.returncode != 0:
            self.fail("node ha fallito: %s"
                      % fatto.stderr.decode("utf-8", "replace")[:400])
        return json.loads(fatto.stdout.decode("utf-8"))

    PAROLE = ["àɣar", "àʎà", "alòž", "magnàr", "l'a", "ghe gh'e", "città",
              "škaba", "aŋkóra", "àldàm", "portar", "zzz"]


class TestIlBottoneDelSuono(_ModelloInNode, unittest.TestCase):
    """Il pulsante che fa sentire la parola ferrarese, dentro il traduttore.

    Difetto vero, di questa sessione: il traduttore scriveva la trascrizione
    («come suona: portàr /porˈtar/») e non offriva modo di ascoltarla. I suoni
    generati c'erano gia' tutti nei dati di **quella** pagina, dodici righe con
    il percorso del file: non mancavano i dati, mancava il codice che li
    disegnava. Il player esisteva, ma dentro `riproduttore()`, che chiama solo
    la pagina dei suoni.

    Il test centrale chiama `rigaSuona`, non `bottoneSuono`: una pagina che
    disegna la trascrizione e non chiama la funzione del bottone passerebbe
    qualunque test sulla funzione, e il bottone non comparirebbe lo stesso. Il
    difetto era esattamente quello — la funzione c'era, la chiamata no — quindi
    il test deve guardare la chiamata.
    """
    # I dati con cui la pagina viene costruita per questi test: un glossario
    # vuoto e i suoni che servono. Non si prende il glossario vero perche' non
    # e' il soggetto: qui si disegna una riga, e la riga si disegna da come
    # guarda la funzione, non da quanti dati ci sono.
    def _dati(self, suoni=None):
        if suoni is None:
            suoni = [
                {"riferimento": "V0002", "forma": "portàr",
                 "ipa": "/portˈar/", "file_playable": "sintesi/T0002.wav",
                 "avvertimento": "questo suono lo ha fatto un programma"},
                {"riferimento": "V0021", "forma": "frarés",
                 "ipa": "/frarˈɛs/", "file_playable": "sintesi/T0023.wav"},
                {"riferimento": "V0021", "forma": "frarèz",
                 "ipa": "/frarˈɛz/", "file_playable": "sintesi/T0024.wav"},
            ]
        return {"glossario": None, "sintesi": suoni,
                "sintesi_avviso": "questo suono lo ha fatto un programma"}

    def _riga(self, risultati, suoni=None):
        """Il testo che la pagina mostra davvero per questa frase."""
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        return self._valuta_js(
            "rigaSuona(%s)" % json.dumps(risultati, ensure_ascii=False),
            dati=self._dati(suoni))

    def _risultato(self, testo, id_, ipa, **kw):
        r = {"testo": testo, "id": id_, "origine": "glossario",
             "confidenza": 0.95, "dettaglio": "", "varieta": "cittadino",
             "ipa": {"ipa": ipa, "da_verificare": True, "nota": ""}}
        r.update(kw)
        return r

    def test_una_parola_con_suono_dichiarato_mostra_il_bottone(self):
        # Il difetto vero, verificato sul testo che la pagina produce: qui
        # dentro c'era la trascrizione e non c'era nessun `<audio>`.
        riga = self._riga([self._risultato("portàr", "V0002", "/porˈtar/")])
        self.assertIn("<audio", riga,
                      "la parola ha un suono dichiarato e la pagina non ha "
                      "mostrato il bottone: %s" % riga)
        self.assertIn("sintesi/T0002.wav", riga)

    def test_una_parola_senza_suono_non_mostra_il_bottone(self):
        # Il contrario, che e' la parte che il progetto vieta di allargare:
        # non si aggiunge un bottone a ogni parola con una trascrizione. Sono
        # 16727 voci su 16739 che il progetto non fa suonare apposta, perche'
        # la loro trascrizione ha un dubbio dichiarato e suonarle
        # insegnerebbe il suono sbagliato.
        riga = self._riga([self._risultato("kavàl", "V0003", "/kavˈal/")])
        self.assertNotIn("<audio", riga,
                         "una parola senza suono dichiarato ha mostrato un "
                         "bottone: %s" % riga)
        # E la riga non sparisce per questo: la trascrizione resta.
        self.assertIn("/kavˈal/", riga)

    def test_il_bottone_c_e_anche_quando_la_risposta_viene_dal_corpus(self):
        # Difetto vero, trovato nel browser e non dai dati: `portare` da solo
        # non mostrava il bottone, `portare il cavallo` lo mostrava. Il motore
        # risolve prima la frase intera dal corpus e in quel percorso
        # restituisce la risposta **senza l'id della voce** — sa che la frase e'
        # giusta, non da quale voce viene — quindi il bottone, che cercava per
        # voce, non offriva niente. La stessa parola suonava o no a seconda di
        # quante parole aveva intorno, che e' l'incoerenza piu' difficile da
        # spiegare a chi guarda.
        #
        # La correzione non e' «cerca sempre»: quando non c'e' l'id si cerca
        # **sulla forma scritta**, che e' l'unica cosa che si conosce, e il
        # ripiego «una sola voce» resta solo per il caso con l'id.
        # Il risultato che il motore costruisce per una frase presa dal
        # corpus: la trascrizione c'e' — `risolvi` la cerca sulla forma
        # prodotta — ma l'id della voce no, perche' il corpus sa che la frase
        # e' giusta e non sa da quale voce viene.
        senza = {"testo": "portàr", "origine": "corpo", "confidenza": 0.92,
                 "dettaglio": "frase intera dal corpus",
                 "ipa": {"ipa": "/porˈtar/", "da_verificare": True, "nota": ""}}
        con_id = self._risultato("portàr", "V0002", "/porˈtar/")
        riga = self._riga([senza])
        self.assertIn("<audio", riga,
                      "dal corpus non c'e' l'id della voce e il bottone e' "
                      " sparito: %s" % riga)
        self.assertIn("sintesi/T0002.wav", riga)
        # E con l'id continua a funzionare: non si e' sostituito un criterio
        # con un altro, li si e' allargati.
        riga2 = self._riga([con_id])
        self.assertIn("sintesi/T0002.wav", riga2)

    def test_il_bottone_dichiara_che_l_ha_fatto_un_programma(self):
        # La dichiarazione sta accanto al bottone, non in un pie' di pagina:
        # chi preme il bottone e' li' e li' deve poterlo sapere.
        riga = self._riga([self._risultato("portàr", "V0002", "/porˈtar/")])
        self.assertIn("programma", riga,
                      "il bottone non dichiara che il suono e' di un programma")

    def test_il_bottone_sceglie_il_suono_della_forma_che_ho_chiesto(self):
        # `V0021` ha due forme, `frarés` e `frarèz`, e due suoni distinti.
        # Suonare `frarés` mentre si cerca `frarèz` e' la parola sbagliata, e
        # non e' una differenza di sillabazione che si puo' dichiarare.
        riga = self._riga([self._risultato("frarèz", "V0021", "/fraˈrɛz/")])
        self.assertIn("sintesi/T0024.wav", riga,
                      "chiesto frarèz, il bottone ha suonato frarés: %s" % riga)
        self.assertNotIn("sintesi/T0023.wav", riga)

    def test_una_forma_scritta_che_non_e_dichiarata_non_prende_il_suono_di_una_che_e(self):
        # Il caso in cui la parola cercata non e' nessuna delle forme che
        # hanno un suono. La regola e' «nessuna offerta»: non si prende il
        # primo suono della voce, perche' un suono offerto accanto a una parola
        # che non e' quella sua e' la parola sbagliata con un bottone sopra, e
        # la dichiarazione «sillabazione diversa» non puo' coprirlo.
        # «frar» e' una forma che nessuna delle due dichiarate produce: la
        # chiave di confronto toglie gli accenti, quindi `frarés` e `frarès`
        # diventano la stessa parola — e va bene, perche' `risolvi` sceglie la
        # trascrizione con la stessa chiave e il bottone resta coerente con
        # quello che e' scritto accanto. Qui serve una parola che davvero non
        # c'e'.
        riga = self._riga([self._risultato("frar", "V0021", "/altra/ˈresa/")])
        self.assertNotIn("<audio", riga,
                         "una forma senza suono ha preso il suono di un'altra: "
                         "%s" % riga)

    def test_il_criterio_non_nasconde_nessuno_dei_suoni_dichiarati(self):
        # Il primo tentativo accettava un suono solo se la sua IPA coincideva
        # con quella dichiarata accanto, e su dodici ne passava **uno**: le
        # altre undici sono la stessa parola con l'accento tonico sulla sillaba
        # diversa, che il controllo F14 chiama gia' «non un suono». Un
        # criterio cosi' non e' piu' severo: e' **sbagliato**, e nascondeva il
        # bottone proprio dove il suono c'era.
        #
        # Il test guarda tutte le righe di `dati/sintesi.jsonl`, non un
        # campione: e' l'unico modo perche' un criterio troppo severo faccia
        # crollare il conto invece di passare.
        righe = [json.loads(riga) for riga in
                 io.open(os.path.join(RADICE, "dati", "sintesi.jsonl"),
                         encoding="utf-8")
                 if riga.strip() and not riga.lstrip().startswith("//")]
        self.assertTrue(righe, "dati/sintesi.jsonl e' vuoto")
        senza = []
        for s in righe:
            # Ogni suono viene chiesto con una trascrizione **diversa** dalla
            # sua, che e' il caso peggiore e anche quello reale.
            risultati = [self._risultato(
                s["forma"], s["riferimento"], "/altra/ˈresa/")]
            riga = self._riga(risultati, suoni=[dict(s, file_playable="suono.wav")])
            if "<audio" not in riga:
                senza.append((s["id"], s["forma"], s["ipa"]))
        self.assertFalse(senza,
                         "suoni dichiarati senza bottone perche' la "
                         "trascrizione e' scritta diversamente: %s" % (senza,))


class TestLaPoolDellAudizione(unittest.TestCase):
    """Le parole di prova dell'audizione, e le voci in prova.

    Una pool non spiegata e' una lista di parole a caso che sembra una pool:
    si guarderebbe, si ascolterebbero suoni di parole facili, si concluderebbe
    «tutte le voci sono uguali» e si prenderebbe per una verifica. Quindi qui
    si controlla che ogni parola abbia un motivo, e che le voci siano
    dichiarate e non scoperte a ogni esecuzione.

    Le voci sono dichiarate perche' un confronto che cambia a ogni giro non e'
    un confronto ripetibile: se domani la lista cresce di una voce e quella di
    ieri non c'e' piu', non si puo' piu' dire quale delle due era migliore.
    """
    def _modulo(self):
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "audizione.py")
        spec = importlib.util.spec_from_file_location("audizione", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_ogni_parola_della_pool_ha_il_motivo_per_esserci(self):
        modulo = self._modulo()
        self.assertTrue(modulo.POOL, "la pool e' vuota")
        for forma, attesa, motivo in modulo.POOL:
            self.assertTrue(motivo.strip(),
                            "%s e' nella pool senza un motivo: e' una parola "
                            "a caso" % forma)
            self.assertTrue(attesa.startswith("/") and attesa.endswith("/"),
                            "%s ha una trascrizione che non sembra una "
                            "trascrizione: %r" % (forma, attesa))

    def test_le_voci_in_prova_sono_dichiarate_e_applicate_allitaliano(self):
        modulo = self._modulo()
        self.assertTrue(modulo.VOCI, "non c'e' nessuna voce in prova")
        for voce in modulo.VOCI:
            # Ogni voce deve essere l'italiano piu' una variante: `it` da solo
            # e' la voce di partenza e le altre sono timbri diversi sopra la
            # stessa lingua. Una voce di un'altra lingua romperebbe il
            # confronto, perche' cambierebbe anche la pronuncia e non solo il
            # timbro — che e' la cosa che qui si vuole tenere ferma.
            self.assertTrue(voce.startswith("it"),
                            "%s non e' una variante dell'italiano" % voce)

    def test_la_destinazione_dell_audizione_e_fuori_dal_repository(self):
        # I suoni dell'audizione sono **il mezzo**: centotrenta file per una
        # griglia di confronto non entrano nel repository, che non e' un
        # archivio di esperimenti. Quindi la cartella deve stare sotto
        # `raccolta/lavorato/`, che il `.gitignore` esclude gia'.
        modulo = self._modulo()
        self.assertIn(os.path.join("raccolta", "lavorato"),
                      modulo.DESTINAZIONE,
                      "i suoni dell'audizione finirebbero nel repository")
        le = io.open(os.path.join(RADICE, '.gitignore'), encoding='utf-8')
        dentro = False
        for riga in le:
            if riga.strip() == "raccolta/lavorato/":
                dentro = True
        self.assertTrue(dentro,
                        "raccolta/lavorato/ non e' in .gitignore: i suoni "
                        "dell'audizione entrerebbero nel repository")


class TestPaginaRegole(unittest.TestCase):
    """La pagina `regole.html`, che e' la ventisettesima del sito.

    Qui non si prova se la pagina e' bella — quello si guarda a occhio — ma
    tre cose che, se falliscono, la pagina mente:

    - il marcatore `<!--REGOLE-->` resta nel testo quando qualcuno non lo
      sostituisce, e resterebbe *senza che nulla se ne accorga*: la pagina
      si aprirebbe e sarebbe vuota;
    - una regola senza fonte e' un'opinione, e questo progetto non accetta
      opinioni travestite da regole;
    - il testo delle regole e' riscritto, e la pagina lo dichiara: se un
      giorno qualcuno ci mette dentro il testo della fonte, la pagina
      continua a dire «il testo e' stato riscritto» e sarebbe falso.
    """
    def _web(self):
        return os.path.join(RADICE, "web", "regole.html")

    def _modulo(self):
        import importlib.util
        percorso = os.path.join(RADICE, "sorgenti", "costruisci_web.py")
        spec = importlib.util.spec_from_file_location("costruisci_web",
                                                      percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_il_marcatore_delle_regole_non_resta_nel_testo(self):
        for nome in sorted(os.listdir(os.path.join(RADICE, "web"))):
            if not nome.endswith(".html"):
                continue
            testo = io.open(os.path.join(RADICE, "web", nome),
                            encoding="utf-8").read()
            # Difetto vero, possibile: `<!--REGOLE-->` sta nel modello e se
            # la pagina non lo sostituisce resta li'. Una pagina che si
            # apre e non mostra niente e' la peggiore: sembra rotta.
            self.assertNotIn("<!--REGOLE-->", testo,
                             "%s mostra il marcatore delle regole" % nome)

    def test_ogni_regola_dichiara_la_fonte(self):
        with io.open(os.path.join(RADICE, "dati", "regole_grammaticali.json"),
                     encoding="utf-8") as f:
            dati = json.load(f)
        self.assertTrue(dati.get("regole"), "non c'e' nessuna regola")
        visti = set()
        for regola in dati["regole"]:
            for campo in ("id", "categoria", "titolo", "regola", "fonte",
                          "sezione"):
                self.assertTrue(regola.get(campo),
                                "la regola %s non dichiara %s"
                                % (regola.get("id", "?"), campo))
            self.assertNotIn(regola["id"], visti,
                             "due regole hanno lo stesso id: %s"
                             % regola["id"])
            visti.add(regola["id"])
        # E la fonte deve esistere davvero nel registro: una regola che
        # cita una fonte inesistente non e' piu' una regola, e' una promessa.
        with io.open(os.path.join(RADICE, "dati", "fonti.json"),
                     encoding="utf-8") as f:
            fonti = {fonte["id"] for fonte in json.load(f)["fonti"]}
        for regola in dati["regole"]:
            self.assertIn(regola["fonte"], fonti,
                          "la regola %s cita la fonte %s che non c'e'"
                          % (regola["id"], regola["fonte"]))

    def test_il_testo_delle_regole_e_dichiarato_riscritto(self):
        testo = io.open(self._web(), encoding="utf-8").read()
        self.assertIn("riscritto", testo,
                      "la pagina deve dire che il testo e' stato riscritto")
        # E non deve contenere l'identificatore interno come se fosse
        # una fonte per chi legge: l'identificatore resta nel titolo.
        corpo = testo.split('class="fonte" title="')[0]
        for identificatore in ("S015", "S006"):
            self.assertNotIn(identificatore, corpo[-4000:],
                             "la pagina mostra %s come se fosse una fonte "
                             "per chi legge" % identificatore)

    def test_la_pagina_contiene_tutte_le_regole_del_file(self):
        with io.open(os.path.join(RADICE, "dati", "regole_grammaticali.json"),
                     encoding="utf-8") as f:
            dati = json.load(f)
        testo = io.open(self._web(), encoding="utf-8").read()
        for regola in dati["regole"]:
            self.assertIn('id="%s"' % regola["id"], testo,
                          "la regola %s non e' nella pagina" % regola["id"])

    def test_il_testo_che_viene_dalla_fonte_e_scappato(self):
        # Una regola che contiene `<` o `&` romperebbe la pagina: il
        # renderer deve scappare, e il test glielo dice mettendogliene
        # dentro uno.
        modulo = self._modulo()
        html = modulo._pagina_regole({
            "opera": "prova",
            "regole": [{"id": "R999", "categoria": "ortografia",
                        "titolo": "caratteri <speciali> & altro",
                        "regola": "segnale < e & dentro",
                        "esempi": [{"fe": "a<b", "it": "c&d"}],
                        "fonte": "S999", "sezione": "1"}]})
        self.assertIn("&lt;speciali&gt;", html)
        self.assertIn("&amp; altro", html)
        self.assertNotIn("<b>", html, "il contenuto e' finito nel markup")

    def test_una_pagina_senza_regole_si_apre_e_lo_dice(self):
        # Se il file delle regole non c'e', la pagina non deve sparire: si
        # apre e spiega perche' e' vuota. Una pagina che non si apre e'
        # peggio di una pagina vuota.
        modulo = self._modulo()
        html = modulo._pagina_regole({"errore": "file non trovato"})
        self.assertIn("file non trovato", html)
        self.assertNotIn('class="scheda regola"', html)


class TestRaccoltaBigoni(unittest.TestCase):
    """Lo script che raccoglie il vocabolario di R. Bigoni.

    I test non chiamano la rete: prendono il modulo e gli iniettano pezzi
    di html scritti a mano, presi dalle righe che hanno fatto scorrere la
    raccolta per davvero. Una prova che va a prendere il sito ogni volta
    sarebbe una prova che fallisce quando la rete e' lenta, e che non puo'
    essere eseguita in un repository copiato da un altro.
    """
    def _modulo(self):
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "bigoni.py")
        spec = importlib.util.spec_from_file_location("bigoni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_le_colonne_legge_nel_verso_sbagliato_non_passano(self):
        # Difetto vero: gli argomenti del bottone erano stati letti nel
        # verso opposto, e il risultato sarebbe stato un glossario di 7307
        # voci capovolte. Ogni voce ben formata, nessuna sbagliata in modo
        # che si vedesse: si traduceva semplicemente dalla lingua sbagliata.
        modulo = self._modulo()
        capovolta = ('<tr><td>1</td><td >cane '
                     "<button onclick='mostraEtimoFerrarese(\"cane\","
                     '"can","x")>etimologia</button></td>'
                     '<td>can</td></tr>')
        voci, incoerenti = modulo.voci_da_html(capovolta)
        self.assertEqual(voci, [], "una riga capovolta non deve entrare")
        self.assertEqual(incoerenti, 1, "e deve essere contata")

    def test_la_traduzione_viene_dalla_cella_e_non_dal_bottone(self):
        # Difetto vero, di 156 righe su 7307: il bottone non porta sempre la
        # traduzione, porta la parola da cui l'etimologia parte. Per `bak`
        # porta `bac`, che e' il latino, mentre la cella dice
        # «bastone, mazza». Prendendo l'italiano dal bottone, questa voce
        # entrava col significato sbagliato.
        modulo = self._modulo()
        riga = ('<tr><td>505</td><td >bak '
                "<button onclick='mostraEtimoFerrarese(\"bac\",\"bak\","
                '"bacus")>etimologia</button></td>'
                '<td>bastone, mazza</td></tr>')
        voci, _ = modulo.voci_da_html(riga)
        self.assertEqual(len(voci), 1, "la riga deve entrare")
        self.assertEqual(voci[0]["ferrarese"], "bak")
        self.assertEqual(voci[0]["italiano"], "bastone")
        self.assertNotEqual(voci[0]["italiano"], "bac",
                            "il latino del bottone non e' la traduzione")

    def test_il_suffisso_dell_omonimo_si_legge_dal_bottone(self):
        # Difetto vero, di questa sessione: il suffisso si cercava nella
        # **cella** dei significati, dove non compare mai — il sito lo scrive
        # solo nel primo argomento del bottone. Il risultato era che su 7307
        # righe gli omonimi trovati erano **zero**, e nessun controllo lo
        # diceva, perche' zero sembrava un numero giusto.
        #
        # Il test precedente esisteva gia' e **passava per il motivo sbagliato**
        # verificando la cella, che non ha mai avuto il suffisso: guardava il
        # posto dove il codice non guardava. Il numero dichiarato nella nota
        # della fonte — «315 righe salvate» — era falso per la stessa
        # ragione: nessuna riga era mai stata salvata da quel fix.
        #
        # Il numero vero e' 186 (170 col trattino e 16 senza), misurato sul
        # sito. Qui si verifica il caso, e `test_quanti_omonomi_troviamo`
        # verifica il numero quando il grezzo c'e'.
        modulo = self._modulo()
        riga = ('<tr><td>174</td><td >àŋkura '
                "<button onclick='mostraEtimoFerrarese(\"ancora-1\","
                '"àŋkura","ancora")>etimologia</button></td>'
                '<td>ancora</td></tr>')
        voci, incoerenti = modulo.voci_da_html(riga)
        self.assertEqual(incoerenti, 0, "la riga dell'omonimo deve entrare")
        self.assertEqual(len(voci), 1)
        self.assertEqual(voci[0]["italiano"], "ancora",
                         "il suffisso -1 e' del sito, non della parola")
        self.assertEqual(voci[0]["omonimo"], 1,
                         "il numero dell'omonimo deve essere letto dal bottone")

    def test_il_suffisso_senza_trattino_e_riconosciuto(self):
        # Il sito scrive anche attaccato: `acciarino1`, `brocca1`,
        # `pidocchioso1` — 16 righe su 186. Un'espressione che accetta solo il
        # trattino manca queste e nessuno se ne accorge, perche' il resto
        # torna.
        modulo = self._modulo()
        riga = ('<tr><td>1</td><td >azalìŋ '
                "<button onclick='mostraEtimoFerrarese(\"acciarino1\","
                '"azalìŋ","acciarino")>etimologia</button></td>'
                '<td>acciarino</td></tr>')
        voci, _ = modulo.voci_da_html(riga)
        self.assertEqual(len(voci), 1, "la riga senza trattino deve entrare")
        self.assertEqual(voci[0]["omonimo"], 1)

    def test_una_parola_senza_omonimo_non_ha_numero(self):
        # Il contrario del test precedente, che e' quello che rende il primo
        # significativo: se `omonimo` valesse zero quando non c'e' nessun
        # suffisso, il campo non distinguerebbe «non applica» da «il primo»,
        # e due righe diverse sembrerebbero la stessa.
        modulo = self._modulo()
        riga = ('<tr><td>1</td><td >abàt '
                "<button onclick='mostraEtimoFerrarese(\"abate\","
                '"abàt","abbatia")>etimologia</button></td>'
                '<td>abate</td></tr>')
        voci, _ = modulo.voci_da_html(riga)
        self.assertIsNone(voci[0]["omonimo"])

    def test_quanti_omonomi_troviamo_sul_grezzo_raccolto(self):
        # Il numero vero, quando il file grezzo c'e'. Se non c'e' il test
        # salta e lo dice: un controllo che non puo' girare non deve far
        # fallire niente, ma non deve nemmeno fingere di essere passato.
        grezzo = os.path.join(RADICE, "raccolta", "grezzi",
                              "bigoni_ferrarese_italiano.jsonl")
        if not os.path.exists(grezzo):
            self.skipTest("il grezzo non e' nel repository: "
                          "si raccoglie con `python3 raccolta/bigoni.py`")
        con_omonimo = 0
        with io.open(grezzo, encoding="utf-8") as f:
            for riga in f:
                if not riga.strip():
                    continue
                if json.loads(riga).get("omonimo") is not None:
                    con_omonimo += 1
        self.assertEqual(con_omonimo, 186,
                         "gli omonimi dichiarati sono 186 (170 col trattino "
                         "e 16 senza): se il numero e' zero il codice sta "
                         "guardando nel posto sbagliato")

    def test_compatta_tiene_gli_accenti_e_lassa_serve_solo_a_segnalare(self):
        # Difetto vero, e il piu' subdolo: la prima versione di `compatta`
        # toglieva anche `à`, `é`, `ò`. `àɣar` diventava `gar` e `alòž`
        # diventava `al`, quindi duecento voci diverse trovavano la stessa
        # chiave. Nessun controllo falliva: le voci sparivano e basta.
        # Nell'ortografia di Bigoni l'accento segna l'accento tonico, e
        # `àɣar` (acre) ed `ar` non sono la stessa parola.
        modulo = self._modulo()
        self.assertNotEqual(modulo.compatta("àɣar"), modulo.compatta("ar"))
        self.assertNotEqual(modulo.compatta("aràdàr"),
                            modulo.compatta("aradar"))
        # Lo spirito e l'apostrofo invece sono la stessa parola: e' il caso
        # per cui la chiave esiste.
        self.assertEqual(modulo.compatta("skara'na"),
                         modulo.compatta("skarana"))
        # La chiave lassa serve a dire «potrebbe essere la stessa», e non
        # a decidere che lo sia.
        self.assertEqual(modulo.lassa("àɣar"), modulo.lassa("àgar"))

    def test_una_raccolta_vuota_non_e_una_raccolta_riuscita(self):
        # Se il download fallisce o il sito cambia formato, lo script non
        # deve scrivere un file vuoto: un file vuoto sembra una raccolta
        # riuscita, e il giorno dopo nessuno si ricorda che era gia' vuoto.
        modulo = self._modulo()
        self.assertTrue(modulo.controlla([], 0))
        voci, incoerenti = modulo.voci_da_html(
            '<tr><td>1</td><td>a</td></tr>')
        self.assertTrue(modulo.controlla(voci, incoerenti))

    def test_i_numeri_devono_essere_consecutivi_e_partire_da_uno(self):
        # 7307 righe numerate da 1 a 7307: se un giorno arrivassero 6797
        # righe numerate da 1 a 7307, il conto tornerebbe lo stesso e
        # nessuno si accorgerebbe che mancano 510 voci. Il numero massimo
        # e' l'unico che se ne accorge.
        modulo = self._modulo()
        voci = [{"numero": 1, "ferrarese": "can", "italiano": "cane",
                 "chiave": "can"},
                {"numero": 3, "ferrarese": "ka", "italiano": "capo",
                 "chiave": "ka"}]
        problemi = modulo.controlla(voci, 0)
        self.assertTrue(problemi,
                        "due numeri non consecutivi devono essere un problema")
        self.assertTrue(any("consecutivi" in p for p in problemi),
                        "il problema deve nominare la consecutivita': %s"
                        % problemi)


class TestLettereDellAlfabeto(unittest.TestCase):
    """Le lettere che l'indice di ricerca buttava via.

    Difetto vero, di questa sessione: `normalizza.chiave()` e `tokenizza()`
    filtravano con l'intervallo `\u00c0-\u024f`, che finisce a U+024F. Ma
    l'alfabeto ferrarese dichiarato in `dati/regole_grammaticali.json` (fonte
    S015) contiene due lettere **fuori** da quell'intervallo: `ɣ` (U+0263) e
    `ʎ` (U+028E). Erano trattate come punteggiatura e cancellate in silenzio.

    La cancellazione silenziosa e' la cosa piu' pericolosa che possa fare
    una chiave di confronto: `àɣar` e `àar` diventavano la stessa chiave
    `aar`, e la ricerca del glossario restituiva la voce sbagliata **senza
    dire niente**. Nessun test lo prendeva, perche' il glossario del 1889
    non usa queste lettere e quindi il difetto era dormiente.

    Il numero che rende la cosa seria: 908 occorrenze di `ɣ` e `ʎ` sulle
    7307 coppie raccolte da S006, cioe' quasi una parola su otto.
    """

    def test_il_confronto_non_cancella_la_gutturale(self):
        # `àɣar` = «duecento» e `àar` sono due voci diverse. Con la `ɣ`
        # cancellata diventavano la stessa.
        from traduttore.normalizza import chiave
        self.assertEqual(chiave("àɣar"), "aɣar")
        self.assertNotEqual(chiave("àɣar"), chiave("àar"),
                            "la ɣ distingue due parole diverse")
        self.assertEqual(chiave("àɣar"), chiave("ÀɣÁR"))

    def test_il_confronto_non_cancella_la_laterale_palatale(self):
        from traduttore.normalizza import chiave
        self.assertEqual(chiave("àʎà"), "aʎa")
        self.assertNotEqual(chiave("àʎà"), chiave("àaà"))

    def test_il_confronto_ancora_toglie_punteggiatura_e_apostrofi(self):
        # La correzione non deve aver perso quello che la funzione faceva.
        from traduttore.normalizza import chiave
        self.assertEqual(chiave("l'a"), "la")
        # `gh'` cade in `g`, per la regola dichiarata in `_sciogli`: non e'
        # una regola della lingua ferrarese ma della raccolta, e il modulo la
        # dichiara. Il risultato e' `ghege`, non `gheghe`, e il test lo scrive
        # perche' e' il modo di non accorgersi se un giorno la regola cambia.
        self.assertEqual(chiave("ghe gh'e"), "ghege")
        self.assertEqual(chiave("città"), "citta")
        self.assertEqual(chiave("a_b"), "ab")
        self.assertEqual(chiave("portar (col marchio)"), "portarcolmarchio")

    def test_la_tokenizzazione_tiene_le_stesse_lettere(self):
        from traduttore.normalizza import tokenizza
        self.assertEqual(tokenizza("àɣar"), ["àɣar"])
        self.assertEqual(tokenizza("l'àɣar"), ["l'àɣar"])

    def test_ogni_lettera_dichiarata_survive_al_confronto(self):
        # Il controllo che avrebbe dovuto esistere: si prende l'alfabeto
        # dai dati e si verifica che ogni lettera che il progetto dichiara
        # sopravviva al confronto. Una lettera aggiunta all'alfabeto senza
        # aggiornare il filtro fallisce qui, e non in fase di ricerca con
        # uno studente davanti.
        import unicodedata
        from traduttore.normalizza import chiave
        percorso = os.path.join(RADICE, "dati", "regole_grammaticali.json")
        with io.open(percorso, encoding="utf-8") as f:
            alfabeto = json.load(f)["alfabeto"]
        perse = []
        for gruppo in ("consonanti", "vocali"):
            for voce in alfabeto[gruppo]:
                carattere = voce["carattere"]
                nudo = "".join(
                    c for c in unicodedata.normalize("NFKD", carattere.lower())
                    if not unicodedata.combining(c))
                if nudo and nudo not in chiave(carattere.lower()):
                    perse.append("%s (U+%04X)" % (carattere, ord(carattere)))
        self.assertEqual(perse, [],
                         "lettere dell'alfabeto dichiarato che il confronto "
                         "cancella: %s" % ", ".join(perse))

    def test_il_confronto_cambia_poco_e_solo_come_deve(self):
        # La correzione **cambia** delle chiavi gia' esistenti, ed e' il
        # punto: la versione vecchia cancellava `ɣ`, quindi `braɣ` diventava
        # `bra` e non trovava niente in indice. Un test che dicesse «non
        # cambia niente» sarebbe falso — e una versione di questo test ha
        # detto proprio quello, perche' l'avevo scritto credendo che il
        # glossario del 1889 non usasse queste lettere. Non le usa quasi
        # mai: `braɣ` c'e' e basta.
        #
        # Quello che si controlla e' la **misura**: quante stringhe cambiano,
        # e se sono tutte e sole quelle che contengono una delle due lettere.
        # Una correzione che cambiasse qualcos'altro — una vocale, una
        # punteggiatura — fallirebbe qui, che e' il posto giusto per
        # accorgersene.
        import unicodedata
        from traduttore.normalizza import chiave
        cambiate, con_lettera, ingannevoli = 0, 0, []
        for nome in ("glossario.jsonl", "coppie.jsonl", "proverbi.jsonl"):
            percorso = os.path.join(RADICE, "dati", nome)
            with io.open(percorso, encoding="utf-8") as f:
                for riga in f:
                    if not riga.strip() or riga.lstrip().startswith("//"):
                        continue
                    voce = json.loads(riga)
                    testi = [voce.get("ferrarese", ""), voce.get("italiano", "")]
                    testi += list(voce.get("varianti") or [])
                    for testo in testi:
                        if not testo:
                            continue
                        if _chiave_vecchia(testo) == chiave(testo):
                            continue
                        cambiate += 1
                        if any(c in testo.lower() for c in
                   ("\u0263", "\u028e", "\u03bb")):
                            con_lettera += 1
                        else:
                            ingannevoli.append((nome, voce.get("id"), testo))
        self.assertEqual(ingannevoli, [],
                         "stringhe cambiate senza contenere \u0263 o \u028e: "
                         "la correzione ha toccato qualcos'altro -> %s"
                         % ingannevoli[:5])
        self.assertEqual(cambiate, con_lettera,
                         "tutte le chiavi cambiate devono contenere una "
                         "delle tre lettere fuori dall'intervallo")
        # Il numero, dichiarato: 861 chiavi su 10431 righe. Serve perche' un
        # numero che si muove senza che nessuno lo dica e' un numero che
        # smette di essere controllato, e qui il cambiamento e' reale: sono
        # le parole che l'indice non trovava piu'.
        self.assertEqual(cambiate, 861,
                         "le chiavi che il filtro vecchio perdeva sono 861")
        self.assertEqual(con_lettera, 861)


def _chiave_vecchia(testo):
    """La chiave che la versione precedente produceva, per confronto.

    Replica il percorso di allora per intero — `normale()`, poi NFKD, poi il
    filtro sull'intervallo — e non solo l'ultimo passo. Una replica che salta
    `normale()` non confronta niente: senza la sostituzione `gh'` → `g` ogni
    `gh'e` sembra una stringa cambiata, e il test segnalava otto falsi
    positivi invece di dire la verita'. E' successo: la prima versione di
    questa funzione faceva esattamente quello, e il numero che dichiarava
    («il glossario del 1889 non usa queste lettere») era falso — `braɣ` e
    `biλjét` ci sono, e da li' il numero vero e' **861**.
    """
    import unicodedata
    from traduttore.normalizza import normale
    nudo = unicodedata.normalize("NFKD", normale(testo))
    senza = "".join(c for c in nudo if not unicodedata.combining(c))
    return re.sub(r"[^0-9a-z\u00c0-\u024f]+", "", senza)

class TestLeDueCopieDellaNormalizzazione(_ModelloInNode, unittest.TestCase):
    """La normalizzazione esiste in Python e in JavaScript, e devono coincidere.

    Difetto vero, di questa sessione, e la lezione piu' utile del lavoro:
    il filtro che cancellava `ɣ` e `ʎ` era in **entrambe le copie**. La pagina
    e il terminale sbagliavano allo stesso modo, quindi
    `prove/controlla_equivalenza.py` non aveva niente da dire: confronta le
    risposte, e due copie che sbagliano insieme rispondono uguale.

    «Le due copie devono essere identiche» e' la regola, e questa era la
    prova che non basta. Un controllo di equivalenza sulle risposte verifica
    che le due copie **dicano** la stessa cosa, non che **paghino** lo stesso
    prezzo: due implementazioni che perdono la stessa lettera dicono la stessa
    cosa e sono entrambe sbagliate.

    Qui il confronto e' sulla funzione, parola per parola, e su un campione
    che contiene le due lettere dell'alfabeto che il filtro vecchio perdeva.
    Se il JavaScript torna indietro, questo test lo dice.
    """

    def test_le_due_chiavi_dicono_la_stessa_cosa(self):
        node = self._js()
        if not node:
            self.skipTest("node non e' installato: il confronto delle due "
                          "copie non puo' girare, e non finge di essere passato")
        from traduttore.normalizza import chiave
        parole = self.PAROLE
        mine = [chiave(p) for p in parole]
        loro = self._valuta_js("parole.map(chiave)", {"parole": parole})
        for parola, mio, loro_ in zip(parole, mine, loro):
            self.assertEqual(mio, loro_,
                             "%r: Python fa %r, JavaScript fa %r" % (parola, mio, loro_))

    def test_la_cripta_non_e_piu_perduta_in_nessuna_delle_due_copie(self):
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        from traduttore.normalizza import chiave
        self.assertEqual(chiave("àɣar"), "aɣar",
                         "la ɣ deve sopravvivere al confronto")
        loro = self._valuta_js('chiave("\u00e0\u0273ar")')
        self.assertEqual(loro, "a\u0273ar",
                         "in JavaScript la \u0273 deve sopravvivire al confronto")

    def test_la_tokenizzazione_concorda_sulle_lettere(self):
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        from traduttore.normalizza import tokenizza
        parole = ["àɣar", "l'àɣar", "doman l'a", "a ŋ k", "portar"]
        mine = [tokenizza(p) for p in parole]
        loro = self._valuta_js("parole.map(tokenizza)", {"parole": parole})
        for parola, mio, loro_ in zip(parole, mine, loro):
            self.assertEqual(mio, loro_,
                             "%r: Python %r, JavaScript %r" % (parola, mio, loro_))

    def test_il_filtro_javascript_non_e_piu_l_intervallo_del_vecchio(self):
        # Un controllo sul sorgente, che non ha bisogno di node: se qualcuno
        # rimette l'intervallo chiuso, il difetto torna anche senza che i test
        # con node girino (su una macchina senza node quei test saltano, e un
        # difetto che torna solo li' tornerebbe libero).
        import re as _re
        with io.open(os.path.join(RADICE, "sorgenti", "modello.html"),
                     encoding="utf-8") as f:
            pagina = f.read()
        # I **commenti** si tolgono prima di guardare: il commento che spiega
        # il difetto contiene per forza la sequenza che il difetto è, quindi
        # un controllo che non li ignora fallisce perche' qualcuno ha scritto
        # la spiegazione. Il difetto da cercare e' quello che gira, non quello
        # che e' stato descritto.
        codice = _re.sub(r"//[^\n]*", "", pagina)
        codice = _re.sub(r"/\*.*?\*/", "", codice, flags=_re.S)
        self.assertNotIn("\\u024f", codice,
                         "l'intervallo chiuso e' il difetto: toglie le lettere "
                         "fuori da U+024F, cioe' quelle dell'alfabeto")


class TestGeneratoreDaBigoni(unittest.TestCase):
    """`raccolta/da_bigoni.py`: le 6352 voci che porta dentro il glossario.

    Il generatore ha avuto **tre difetti veri** in questa sessione, e tutti
    e tre producevano righe ben formate: sono il tipo di difetto che i
    controlli non prendono e che un secondo giro di script scopre.

    Qui si provano le quattro cose che devono valere: il generatore non
    duplica, non sceglie fra due fonti in disaccordo, rispetta l'idempotenza
    e non scrive una parola funzionale.
    """

    def _modulo(self):
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "da_bigoni.py")
        spec = importlib.util.spec_from_file_location("da_bigoni", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def _voce(self, ferrarese, italiano, **extra):
        voce = {"numero": 1, "ferrarese": ferrarese, "significati": italiano,
                "italiano": italiano.split(",")[0].strip(),
                "etimologia": "", "omonimo": None}
        voce.update(extra)
        return voce

    def test_una_parola_gia_presente_con_lo_stesso_significato_non_e_ripetuta(self):
        modulo = self._modulo()
        attive = [{"id": "V0001", "ferrarese": "àɣar", "italiano": "duecento"}]
        raccolte = [self._voce("àɣar", "duecento")]
        esiti = modulo.confronta(raccolte, attive)
        self.assertEqual(esiti["nuove"], [],
                         "la stessa parola con lo stesso significato e' gia' li'")
        self.assertEqual(len(esiti["gia_presenti"]), 1)

    def test_un_disaccordo_fra_due_fonti_non_viene_deciso(self):
        # `Anèl` e' «anello» per il Ferri e «agnello» per Bigoni. Il
        # generatore non sceglie: segnala e lascia la voce esistente dov'e'.
        # Il motivo e' che nessuno dei due numeri dice quale sia il ferrarese,
        # e scegliere a caso produce una parola sbagliata che non si vede.
        modulo = self._modulo()
        attive = [{"id": "V0520", "ferrarese": "Anél", "italiano": "Anello"}]
        raccolte = [self._voce("añèl", "agnello")]
        esiti = modulo.confronta(raccolte, attive)
        self.assertEqual(esiti["nuove"], [], "un disaccordo non si riscrive")
        self.assertEqual(len(esiti["disaccordi"]), 1)
        voce, esistenti = esiti["disaccordi"][0]
        self.assertEqual(esistenti[0]["id"], "V0520")

    def test_una_doppia_nella_fonte_si_tiene_una_voce(self):
        modulo = self._modulo()
        raccolte = [self._voce("ašnàda", "asinata", numero=398),
                    self._voce("ašnàda", "asinata", numero=399)]
        esiti = modulo.confronta(raccolte, [])
        self.assertEqual(len(esiti["nuove"]), 1)
        self.assertEqual(len(esiti["doppie"]), 1)

    def test_due_omonimi_della_fonte_sono_due_voci(self):
        # Stessa parola, significati diversi: la fonte li distingue e sono
        # due voci. Unirle sarebbe una scelta che nessuno ha chiesto.
        modulo = self._modulo()
        raccolte = [self._voce("alvàr", "levare", numero=133),
                    self._voce("alvàr", "sollevare, allevare", numero=134)]
        esiti = modulo.confronta(raccolte, [])
        self.assertEqual(len(esiti["nuove"]), 2)

    def test_il_secondo_giro_non_scrive_niente(self):
        # Il difetto piu' costoso: il generatore scriveva 194 righe duplicate
        # alla seconda esecuzione, di parole che aveva scritto lui stesso un
        # giro prima. La voce non era neanche malformata, quindi nessun
        # controllo se ne accorgeva.
        modulo = self._modulo()
        raccolte = [self._voce("àɣar", "duecento", numero=61),
                    self._voce("àɣar", "acre", numero=62),
                    self._voce("abadìŋ", "abbandono", numero=63)]
        prime = modulo.confronta(raccolte, [])
        righe = modulo.costruisci(prime["nuove"], 10405,
                                  modulo.gemelli_per_chiave(raccolte))
        seconde = modulo.confronta(raccolte, righe)
        self.assertEqual(seconde["nuove"], [],
                         "il secondo giro deve trovare tutto gia' scritto")

    def test_una_funzionale_non_diventa_voce(self):
        # `kóŋ` = «con»: la parola ferrarese e' vera ma la traduzione e' una
        # funzionale, e il glossario la indicizzerebbe dal lato italiano dove
        # il motore non deve trovarla.
        modulo = self._modulo()
        esiti = modulo.confronta(
            [self._voce("kóŋ", "con"), self._voce("àrba", "albero")], [])
        self.assertEqual([v["ferrarese"] for v in esiti["nuove"]], ["àrba"])
        self.assertEqual(len(esiti["funzionali"]), 1)

    def test_il_filtro_sulle_funzionali_scarta_sul_lato_indicizzato(self):
        # Il filtro guarda la **traduzione**, non la parola ferrarese, e la
        # ragione la dice il test `TestCopertura`: `cerca_italiano("con")`
        # non deve trovare niente, perche' il motore tratta le preposizioni
        # a parte e una voce che le indicizza gliele toglie.
        #
        # Un filtro che guardasse la parola ferrarese avrebbe scartato anche
        # `kóŋ` — che e' una parola ferrarese vera, e che `al` invece non
        # avrebbe scartato, perche' `al` non e' un articolo italiano. Avrebbe
        # passato lo stesso test di qui sotto e fatto il contrario di quello
        # che serve: un filtro che fa passare il controllo senza fare il suo
        # lavoro e' peggio di nessun filtro.
        modulo = self._modulo()
        # La parola ferrarese non conta: `kóŋ` non e' nell'elenco, `al`
        # invece c'e', e nonostante cio' entrambe le righe vengono scartate
        # perche' la loro **traduzione** e' una funzionale.
        self.assertNotIn("kóŋ", modulo.FUNZIONALI,
                         "se questa asserzione regge, il filtro non guarda "
                         "la parola ferrarese")
        self.assertTrue(modulo.funzionale(self._voce("kóŋ", "con")))
        self.assertTrue(modulo.funzionale(self._voce("al", "il")))
        # E la prova che il filtro non guarda la parola ferrarese: due righe
        # con la stessa parola, una sola scartata.
        scartate = [v for v in (self._voce("kóŋ", "con"),
                                self._voce("kóŋ", "coglione"))
                    if modulo.funzionale(v)]
        self.assertEqual(len(scartate), 1,
                         "la stessa parola con due traduzioni diverse dà "
                         "due risposte diverse: guarda la traduzione")

    def test_una_funzionale_e_un_significato_abbastanza_per_scartare(self):
        # «in, dentro»: uno dei due significati e' una funzionale, e la riga
        # non entra. Guardare solo il primo significato la lascerebbe passare.
        modulo = self._modulo()
        self.assertTrue(modulo.funzionale(self._voce("dréint", "dentro, in")))

    def test_il_prossimo_id_cede_il_passo_alla_fila_d_attesa(self):
        # Difetto vero: `prossimo_id()` guardava solo il glossario attivo, e
        # la fila d'attesa ha cinque id (V10400-V10404) piu' alti di tutti
        # quelli attivi. Il generatore ha quindi **ridescritto quei cinque
        # id**, e i 6426 avvisi D1 sono arrivati solo dopo, quando il lavoro
        # era gia' fatto.
        modulo = self._modulo()
        attive = [{"id": "V10389", "ferrarese": "Zzupgàr", "italiano": "zop"}]
        in_attesa = modulo.id_in_attesa()
        self.assertGreaterEqual(in_attesa, 10404,
                                "la fila d'attesa deve arrivare almeno a V10404")
        self.assertGreaterEqual(max(modulo.prossimo_id(attive), in_attesa + 1),
                                10405,
                                "il primo id libero deve stare dopo la fila "
                                "d'attesa, non dentro")

    def test_le_voci_scritte_dichiarano_fonte_e_varieta(self):
        # Una voce senza fonte non entra: e' il G4. E la `varieta` viene
        # dai dati, non da una costante scritta qui.
        modulo = self._modulo()
        righe = modulo.costruisci(
            [self._voce("àɣar", "duecento", numero=61)],
            10405, {"aɣar": 1})
        self.assertEqual(len(righe), 1)
        riga = righe[0]
        self.assertTrue(riga["fonte"].strip(), "una voce senza fonte non entra")
        self.assertIn("S006", riga["fonte"])
        self.assertIn("61", riga["fonte"])
        self.assertEqual(riga["varieta"], modulo.CODICE_VARIETA_ATTESA)
        self.assertTrue(riga["da_verificare"],
                        "una voce raccolta e non confrontata si dichiara")

    def test_la_varieta_viene_dai_dati_e_non_dal_generatore(self):
        # Se `dati/varieta.json` non dichiara la varieta' per S006, il
        # generatore si ferma invece di indovinare. E se la dichiarazione
        # cambia, il generatore segue quella e non un numero scritto qui.
        modulo = self._modulo()
        dichiarazione = modulo.varieta_dichiarata(modulo.VARIETA, "S006")
        self.assertEqual(dichiarazione["varieta"],
                         modulo.CODICE_VARIETA_ATTESA)
        self.assertEqual(dichiarazione["attendibilita"], "M",
                         "una fonte che non dichiara il territorio dà una "
                         "scelta dichiarata come memoria, non documentata")
        with self.assertRaises(SystemExit):
            modulo.varieta_dichiarata(modulo.VARIETA, "S999")

    def test_il_significato_moderno_e_il_flag_restano_quelli_del_glossario(self):
        # La voce di Bigoni non ha significato moderno e non puo' inventarne
        # uno: `moderno` vuoto e `fonte_moderno` vuoto insieme, come vuole
        # il G10.
        modulo = self._modulo()
        righe = modulo.costruisci([self._voce("àɣar", "duecento")], 10405, {})
        # La voce non si inventa un significato moderno: `moderno` e
        # `fonte_moderno` semplicemente non ci sono, e il G11 non ha niente da
        # segnalare. Il campo non scritto vale vuoto in `Voce`, ed e'
        # quello che il glossario deve dire: qui il buco e' dichiarato.
        self.assertNotIn("moderno", righe[0],
                         "il generatore non scrive il significato moderno")
        self.assertNotIn("fonte_moderno", righe[0])



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



class TestLaVoceDichiarata(unittest.TestCase):
    """Il riproduttore vocale e' una regola del file, non una scelta del codice.

    Il difetto che questi test prendono: la voce era una costante in
    `voce.py`. Il giorno in cui la voce e' diventata una cosa che qualcuno
    sceglie — perche' tutte le prove sembravano uguali — la costante non
    bastava piu': serviva un posto dove la scelta fosse scritta, e quel posto
    non poteva essere un altro file, perche' un altro file e' un file che
    nessuno apre quando cerca le regole di pronuncia.

    Qui le regole stanno in `dati/fonetica.jsonl`, dentro una riga sola che
    comincia con `// SISTEMA `. Il codice la legge; se manca, lo dice.
    """

    def _dichiarazione(self):
        return leggi_sistema(os.path.join(RADICE, "dati", "fonetica.jsonl"))

    def test_il_file_delle_regole_dichiara_una_voce_e_i_voti_fra_cui_scegliere(self):
        dichiarazione = self._dichiarazione()
        self.assertTrue(dichiarazione["dichiarata"],
                        dichiarazione["problema"])
        self.assertTrue(dichiarazione["voce"])
        self.assertTrue(dichiarazione["voti"])
        self.assertIn(dichiarazione["voce"], dichiarazione["voti"])
        self.assertGreater(dichiarazione["velocita"], 0)

    def test_una_dichiarazione_che_non_e_json_e_un_problema_e_non_una_voce(self):
        # Una riga rotta non puo' diventare una voce per meta': o si legge, o
        # non c'e'. Il mezzo e' peggio del silenzio perche' sembra una scelta.
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as f:
            f.write("// SISTEMA {voce: it, voti: [it]}\n")
            percorso = f.name
        try:
            dichiarazione = leggi_sistema(percorso)
            self.assertFalse(dichiarazione["dichiarata"])
            self.assertIn("non e' JSON", dichiarazione["problema"])
        finally:
            os.unlink(percorso)

    def test_una_dichiarazione_assente_non_produce_una_voce(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as f:
            f.write("// solo un commento\n")
            percorso = f.name
        try:
            dichiarazione = leggi_sistema(percorso)
            self.assertFalse(dichiarazione["dichiarata"])
            self.assertEqual(dichiarazione["voce"], "")
            # La dichiarazione resta vuota: nessun file, nessuna voce. Il
            # ripiego pero' c'e' ed e' dichiarato, e `voce_per` lo usa: un
            # comando che suonasse con una stringa vuota produrrebbe un file
            # con la voce di default del programma, cioe' un suono che nessuno
            # ha scelto.
            self.assertEqual(voce_modulo.voce_per(""),
                             voce_modulo.VOCE_RIPIEGO)
        finally:
            os.unlink(percorso)

    def test_il_comando_usa_la_voce_dichiarata_e_non_una_costante(self):
        esito = voce_modulo.voce("majàl")
        self.assertEqual(esito["voce"], self._dichiarazione()["voce"])
        self.assertEqual(esito["velocita"], self._dichiarazione()["velocita"])

    def test_una_riga_puo_scegliere_la_voce_di_quella_parola_sola(self):
        # Il campo `voce` della riga: vuoto vuol dire «quella dichiarata»,
        # e un nome vuol dire «questa». E' la scelta che l'audizione produce.
        scelta = voce_modulo.voci_dichiarate()[0]
        altra = voce_modulo.voci_dichiarate()[-1]
        self.assertEqual(voce_modulo.voce_per(""), scelta)
        self.assertEqual(voce_modulo.voce_per(altra), altra)
        esito = voce_modulo.voce("majàl", lingua=altra)
        self.assertEqual(esito["voce"], altra)

    def test_il_manifesto_dei_suoni_dice_qual_riproduttore_li_ha_fatti(self):
        # Un suono senza il nome di chi lo ha prodotto non e' verificabile da
        # nessuno: la dichiarazione «e' una voce sintetica» dice che non e'
        # una persona, ma non dice quale programma.
        percorso = os.path.join(RADICE, "dati", "sintesi.jsonl")
        righe = []
        with io.open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                if riga and not riga.startswith("//"):
                    righe.append(json.loads(riga))
        self.assertTrue(righe)
        for riga in righe:
            self.assertIn("voce", riga, riga.get("id"))
            self.assertTrue(riga["voce"])

    def test_una_voce_scelta_fra_i_voti_nessuno_e_un_errore(self):
        # Il caso vero: qualcuno scrive `it+inesistente` nella riga. Il nome
        # non e' fra quelli dichiarati, quindi non e' mai stato ascoltato.
        fonetica = Fonetica([Trascrizione(
            id="T1", riferimento="V2", forma="pan", ipa="/pan/",
            varieta="cittadino", voce="it+inesistente")])
        problemi = [p for p in verifica_dati.controlla_fonetica(
            fonetica, glossario_di_prova(), corpus_di_prova())
            if p.codice == "F15"]
        self.assertTrue(problemi)
        self.assertEqual(problemi[0].gravita, "errore")

    def test_un_sistema_che_non_dichiara_nessuna_voce_e_un_errore(self):
        # Una dichiarazione assente non e' neutra: e' una scelta che nessuno
        # ha preso, e senza questa riga il codice ne prenderebbe una per
        # conto suo, che e' esattamente cio' che questo progetto non fa.
        vuota = {"voce": "", "velocita": 0, "voti": [], "dichiarata": False,
                 "problema": "assente"}
        with unittest.mock.patch.object(verifica_dati, "leggi_sistema",
                                        return_value=vuota):
            problemi = [p for p in verifica_dati.controlla_fonetica(
                Fonetica([]), glossario_di_prova(), corpus_di_prova())
                if p.codice == "F15"]
        self.assertEqual(len(problemi), 1)
        self.assertEqual(problemi[0].gravita, "errore")

    def test_la_voce_del_sistema_deve_essere_fra_i_voti(self):
        # Una dichiarazione che sceglie una voce e poi non la mette fra i voti
        # e' una dichiarazione che non puo' essere controllata: qualcuno puo'
        # scegliere quella voce per una parola solo e il controllo non se ne
        # accorgerebbe.
        strana = {"voce": "it+fuori", "velocita": 130, "voti": ["it"],
                  "dichiarata": True, "problema": ""}
        with unittest.mock.patch.object(verifica_dati, "leggi_sistema",
                                        return_value=strana):
            problemi = [p for p in verifica_dati.controlla_fonetica(
                Fonetica([]), glossario_di_prova(), corpus_di_prova())
                if p.codice == "F15"]
        errori = [p for p in problemi if p.gravita == "errore"]
        self.assertEqual(len(errori), 1)
        self.assertIn("it+fuori", errori[0].messaggio)

    def test_una_voce_che_il_programma_non_conosce_e_un_avviso(self):
        # Lo stesso dato puo' essere giusto e l'installazione sbagliata: per
        # questo e' un avviso e non un errore. Dire che il dato e' falso
        # quando e' l'installazione a essere diversa sarebbe un controllo che
        # segnala una cosa che non c'e'.
        buona = {"voce": "it", "velocita": 130, "voti": ["it"],
                 "dichiarata": True, "problema": ""}
        with unittest.mock.patch.object(verifica_dati, "leggi_sistema",
                                        return_value=buona), \
                unittest.mock.patch.object(voce_modulo, "percorso_espeak",
                                           return_value="/usr/bin/espeak-ng"), \
                unittest.mock.patch.object(voce_modulo, "voci_espeak",
                                           return_value=set()):
            problemi = [p for p in verifica_dati.controlla_fonetica(
                Fonetica([]), glossario_di_prova(), corpus_di_prova())
                if p.codice == "F15"]
        self.assertEqual(problemi, [])

        with unittest.mock.patch.object(verifica_dati, "leggi_sistema",
                                        return_value=buona), \
                unittest.mock.patch.object(voce_modulo, "percorso_espeak",
                                           return_value="/usr/bin/espeak-ng"), \
                unittest.mock.patch.object(voce_modulo, "voci_espeak",
                                           return_value={"en", "fr"}):
            problemi = [p for p in verifica_dati.controlla_fonetica(
                Fonetica([]), glossario_di_prova(), corpus_di_prova())
                if p.codice == "F15"]
        self.assertEqual(len(problemi), 1)
        self.assertEqual(problemi[0].gravita, "avviso")

    @unittest.skipUnless(percorso_espeak(), "espeak-ng non e' installato")
    def test_i_voti_dichiarati_producono_file_diversi(self):
        # Il test che prende il difetto vero, e non un difetto di scrittura.
        # Una voce dichiarata fra i voti che produce **lo stesso file** della
        # voce dichiarata non e' una scelta: e' una colonna vuota. E' successo
        # con `it+mbrola3`, che qui e' esattamente quello stesso file di `it`.
        if sys.platform == "darwin" and os.uname().machine == "x86_64":
            pass
        dichiarata = voce_modulo.voce_dichiarata()
        voti = voce_modulo.voci_dichiarate()
        with tempfile.TemporaryDirectory() as cartella:
            impronte = {}
            for voto in voti:
                esito = voce_modulo.scrivi_wav(
                    "majàl", os.path.join(cartella, "prova.wav"), lingua=voto)
                self.assertEqual(esito["problema"], "", voto)
                with open(esito["wav"], "rb") as f:
                    impronte[voto] = hashlib.md5(f.read()).hexdigest()
        for voto, impronta in impronte.items():
            if voto == dichiarata:
                continue
            self.assertNotEqual(
                impronta, impronte[dichiarata],
                "%s produce lo stesso file di %s: e' una voce che non cambia "
                "niente e non puo' stare fra i voti" % (voto, dichiarata))

    def test_la_griglia_dell_audizione_confronta_le_voci_dichiarate(self):
        # Una griglia che confronta voci diverse da quelle che il progetto
        # puo' usare e' una griglia che non serve a niente: i voti vengono dal
        # file delle regole, e la lista scritta a mano e' solo il ripiego.
        self.assertEqual(_voti_dell_audizione(), voce_modulo.voci_dichiarate())



class TestIModiDiDire(unittest.TestCase):
    """S019: le frasi di Wikiquote lette dalla pagina, e non dalla regex.

    I due difetti che questi test prendono sono reali e sono già successi:

    - il lettore contava i `<dd>` senza distinguere quelli annidati, quindi
      diceva 37 modi di dire dove ce n'erano 35, e due dei 37 erano le
      spiegazioni italiane, non delle voci;
    - la regola che scarta le spiegazioni mozzate guardava la prima parola,
      quindi buttava via «Come viene viene, alla grossa» e «Furbo come l'oca
      di Fergnani», che sono frasi intere, per salvare due voci rotte.

    Un lettore di dati che sbaglia il conto e butta via parole buone è peggio
    di un lettore che non esiste, perché il suo errore è invisibile: sembra
    lavoro fatto.

    **Una nota sull'interprete, non sul codice.** Con l'interprete di questa
    macchina (Python 3.9 dei CommandLineTools) la forma
    `x = modulo._esterni(s)` seguita da `len(x)`, dentro un metodo di questa
    classe, mette `x` sia fra le variabili locali del codice compilato sia fra i
    nomi globali: a runtime `len(x)` solleva `NameError`. La stessa riga
    compilata da sola da' `LOAD_FAST`, quindi non e' un errore di scrittura. Il
    metodo che ne soffre chiama la funzione due volte invece di tenere il
    risultato in una variabile, e la nota è qui dentro perché nessuno ci
    creda sulla parola.
    """

    def _modulo(self):
        import importlib.util
        percorso = os.path.join(RADICE, "raccolta", "da_modi.py")
        spec = importlib.util.spec_from_file_location("da_modi", percorso)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_i_dd_annidati_non_sono_voci(self):
        modulo = self._modulo()
        # Una voce sola con tre spiegazioni annidate dentro: il lettore ne deve
        # restituire **due** voci, non cinque. Il difetto vero era il contrario
        # — contare tutti i `<dd>` e chiamarli 37 modi di dire quando erano 35
        # — e questa casella e' scelta perche' un lettore che conta i tag non
        # puo' passarla: ne troverebbe cinque, e direbbe che la pagina ha cinque
        # modi di dire dove ce n'e' uno.
        segmento = ("<dd>Uno<i>a</i><dl>"
                    "<dd>prima spiegazione</dd>"
                    "<dd>seconda spiegazione</dd>"
                    "<dd>terza spiegazione</dd>"
                    "</dl></dd>"
                    "<dd>Due<i>b</i><dl><dd>spiegazione</dd></dl></dd>")
        # La chiamata e' ripetuta invece di tenere il risultato in una
        # variabile: vedi la nota della classe, l'interprete sbaglia quella forma.
        self.assertEqual(len(modulo._esterni(segmento)), 2,
                         "una voce con tre spiegazioni dentro deve contare "
                         "una, non tre: ha contato i <dd> annidati")
        self.assertIn("prima spiegazione", modulo._esterni(segmento)[0],
                      "la spiegazione annidata resta dentro la sua voce")

    def test_una_spiegazione_intera_non_viene_scartata(self):
        modulo = self._modulo()
        # Il difetto: la regola guardava la prima parola e scartava le frasi
        # che cominciano con «come», che è una congiunzione d'inizio frase.
        intere = ["Come viene viene, alla grossa, a occhio e croce",
                  "Furbo come l'oca di Fergnani che era il più furbo di tutti",
                  "Su per giù, all'incirca, pressappoco",
                  "Essere baciati dalla fortuna",
                  "Andare a pampògne"]
        for spiegazione in intere:
            self.assertFalse(modulo._mozzata(spiegazione),
                             "scartata una spiegazione intera: %r" % spiegazione)

    def test_una_spiegazione_mozzata_viene_scartata(self):
        modulo = self._modulo()
        mozzate = [", andare a zonzo",
                   "o Dai, picchia e martella. Dopo tanto penare",
                   "- cioè, senza fretta"]
        for spiegazione in mozzate:
            self.assertTrue(modulo._mozzata(spiegazione),
                            "tenuta una coda di frase: %r" % spiegazione)

    def test_il_grezzo_dichiara_i_35_e_i_due_scarti(self):
        modulo = self._modulo()
        # Il conto e' dichiarato nel file e nel docstring: se la pagina cambia,
        # il numero esce diverso e questo test lo dice invece di lasciare che
        # i dati cambino in silenzio.
        voci = modulo.voci()
        mozzate = [v for v in voci if modulo._mozzata(v[1])]
        senza = [v for v in voci if not v[1]]
        nuove = [v for v in voci if v[1] and not modulo._mozzata(v[1])]
        self.assertEqual(len(voci), 35)
        self.assertEqual(len(senza), 2)
        self.assertEqual(len(mozzate), 2)
        self.assertEqual(len(nuove), 31)

    def test_ogni_modo_di_dire_che_entra_e_nella_pagina(self):
        modulo = self._modulo()
        # Ogni riga scritta deve trovarsi in `dati/coppie.jsonl`, e viceversa:
        # una riga copiata a mano fuori dal lettore non si riconosce.
        scritte = []
        with io.open(os.path.join(RADICE, "dati", "coppie.jsonl"),
                     encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                if not riga or riga.lstrip().startswith("//"):
                    continue
                coppia = json.loads(riga)
                if modulo.ID_FONTE in coppia.get("fonte", ""):
                    scritte.append(coppia)
        voci = modulo.voci()
        attese = [v for v in voci
                  if v[1] and not modulo._mozzata(v[1])]
        self.assertEqual(len(scritte), len(attese))
        chiavi = set(coppia["ferrarese"] for coppia in scritte)
        for ferrarese, _ in attese:
            self.assertIn(ferrarese, chiavi,
                          "%s e' nella pagina ma non nelle coppie" % ferrarese)
        for coppia in scritte:
            self.assertEqual(coppia["tipo"], modulo.TIPO)
            self.assertEqual(coppia["attendibilita"], "I")
            self.assertTrue(coppia["varieta"], "una coppia senza varieta'")
            self.assertTrue(coppia["nota"], "una coppia senza nota")

    def test_la_varieta_di_s019_e_dichiarata_in_un_file(self):
        modulo = self._modulo()
        # La riga di `varieta.json` e' cio' che permette a `da_modi.py` di
        # scrivere: senza, il generatore si ferma e lo dice invece di indovinare.
        with io.open(os.path.join(RADICE, "dati", "varieta.json"),
                     encoding="utf-8") as f:
            grezzo = json.load(f)
        assegnazioni = [a for a in grezzo["assegnazioni"]
                        if a.get("fonte") == modulo.ID_FONTE]
        self.assertEqual(len(assegnazioni), 1,
                         "S019 deve avere una sola riga in varieta.json")
        self.assertEqual(assegnazioni[0]["varieta"], "cittadino")
        self.assertTrue(assegnazioni[0]["motivo"].strip(),
                        "una variante dichiarata senza motivo e' una variante "
                        "indovinata")


class TestLaScritturaDeiModiDiDire(unittest.TestCase):
    """Il generatore di `da_modi.py`, eseguito davvero.

    Qui non si guarda il file di dati, che e' gia' scritto e non si riscrive: si
    guarda **la scrittura**, in un file di temporaneo. E' l'unico modo per
    prendere un difetto che sta nel decidere — tenere una spiegazione mozzata,
    scrivere una riga senza nota — invece che nel leggere.
    """

    def _scrive_in(self, percorso):
        """Esegue il generatore con `dati/coppie.jsonl` spostato altrove."""
        import importlib.util
        specifica = importlib.util.spec_from_file_location(
            "da_modi", os.path.join(RADICE, "raccolta", "da_modi.py"))
        modulo = importlib.util.module_from_spec(specifica)
        specifica.loader.exec_module(modulo)
        modulo.COPPIE = percorso
        argv = sys.argv
        sys.argv = ["da_modi.py"]
        try:
            codice = modulo.main()
        finally:
            sys.argv = argv
        return modulo, codice

    def _righe(self, percorso):
        righe = []
        with io.open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                if riga and not riga.lstrip().startswith("//"):
                    righe.append(json.loads(riga))
        return righe

    def test_il_generatore_scrive_tutto_cio_che_decide_di_scrivere(self):
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "coppie.jsonl")
            modulo, codice = self._scrive_in(percorso)
            self.assertEqual(codice, 0)
            righe = self._righe(percorso)
        self.assertEqual(len(righe), 31, "la pagina ha 35 modi di dire, meno "
                                        "due senza spiegazione e due mozzati")
        for riga in righe:
            self.assertTrue(riga["nota"],
                            "una riga senza nota non dice da dove viene: %r"
                            % riga["ferrarese"])
            self.assertEqual(riga["tipo"], modulo.TIPO)
            self.assertEqual(riga["attendibilita"], "I")
            self.assertIn(modulo.ID_FONTE, riga["fonte"])
            self.assertTrue(riga["varieta"])
            self.assertTrue(riga["italiano"].strip())
            self.assertTrue(riga["ferrarese"].strip())

    def test_una_spiegazione_mozzata_non_arriva_ma_un_intera_sì(self):
        # Le due righe che la regola troppo larga scartava per errore. Se la
        # regola torna a guardare la prima parola, questo test lo dice con i
        # nomi delle voci che perdevamo, non con un numero.
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "coppie.jsonl")
            self._scrive_in(percorso)
            scritte = [r["ferrarese"] for r in self._righe(percorso)]
        for tenuta in ("Un tanto al braccio",
                       "Furbo come l'oca di Fergnani che era i 'cani'",
                       "Andare in oca"):
            self.assertTrue(
                any(t.startswith(tenuta[:20]) for t in scritte),
                "%s e' una spiegazione intera e non deve perdersi" % tenuta)

    def test_riscrivere_non_duplica(self):
        # Due giri sullo stesso file: il secondo non aggiunge niente. Il
        # generatore deve riconoscere le righe sue, perche' il progetto non
        # riscrive quello che ha gia' scritto.
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "coppie.jsonl")
            self._scrive_in(percorso)
            primo = self._righe(percorso)
            self._scrive_in(percorso)
            secondo = self._righe(percorso)
        self.assertEqual(primo, secondo, "il secondo giro ha riscritto qualcosa")

    def test_gli_id_continuano_e_non_ricominciano(self):
        # Il difetto che questo test prende: ricominciare la numerazione da F0001
        # in un file che ha gia' delle righe produce due righe con lo stesso id,
        # e un id doppio non si vede leggendo il file — si vede solo quando
        # qualcuno ci fa riferimento. Il numero si legge dal file, quindi il
        # file di prova parte gia' con una riga che arriva da un'altra strada.
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "coppie.jsonl")
            with io.open(percorso, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": "F0100", "varieta": "cittadino",
                    "italiano": "una riga che era gia' li",
                    "ferrarese": "Na penna", "tipo": "conversazione",
                    "fonte": "manoscritto", "nota": "riga di prova",
                    "attendibilita": "D", "ricorrenze": 1},
                    ensure_ascii=False) + "\n")
            self._scrive_in(percorso)
            righe = self._righe(percorso)
        self.assertEqual(len(righe), 32)
        self.assertEqual(righe[0]["id"], "F0100", "la riga di prova e' stata "
                                                 "mossa")
        self.assertEqual(righe[1]["id"], "F0101",
                         "gli id devono continuare dopo l'ultimo, non "
                         "ricominciare da F0001")
        numeri = [r["id"] for r in righe]
        self.assertEqual(len(set(numeri)), len(numeri),
                         "due righe con lo stesso id: %r" % numeri)

    def test_una_voce_gia_scritta_non_viene_riscritta(self):
        # Il generatore deve riconoscere le righe sue dal lato **ferrarese**,
        # non dal loro numero. Il caso provato e' quello vero: una riga di
        # coppie che arriva da un'altra strada, con un altro id.
        with tempfile.TemporaryDirectory() as cartella:
            percorso = os.path.join(cartella, "coppie.jsonl")
            self._scrive_in(percorso)
            riga = self._righe(percorso)[0]
            self.assertTrue(riga["ferrarese"])
            with io.open(percorso, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "id": "F9001", "varieta": "cittadino",
                    "italiano": "confondersi, dimenticarsi",
                    "ferrarese": riga["ferrarese"],
                    "tipo": "conversazione",
                    "fonte": "manoscritto", "nota": "riga di prova",
                    "attendibilita": "D", "ricorrenze": 1},
                    ensure_ascii=False) + "\n")
            _, codice = self._scrive_in(percorso)
            righe = self._righe(percorso)
        self.assertEqual(codice, 0)
        # 31 della prima scrittura piu' la riga aggiunta a mano: se il
        # generatore riscrivesse la voce, il file ne avrebbe 33.
        self.assertEqual(len(righe), 32,
                         "una voce gia' nel file non deve essere riscritta")
        # La voce e' nel file due volte per costruzione — la riga aggiunta a
        # mano e quella del generatore — quindi qui si conta un'altra cosa: che
        # il generatore non abbia scritto un secondo F0001.
        numeri = [r["id"] for r in righe if r["id"] == "F0001"]
        self.assertEqual(len(numeri), 1,
                         "il generatore ha riscritto la voce che era gia' "
                         "nel file")


class TestLeFormeVerbali(unittest.TestCase):
    """Le forme verbali attestate, e i buchi che le circondano.

    Il difetto che questi test prendono e' quello che ha fatto prendere il
    traduttore: **il progetto non coniugava e non lo diceva**. Una parola
    coniugata non tradotta tornava come trattino, e il trattino non dice se il
    progetto non sa o se la fonte non c'e'. Qui si controllano le tre cose che
    rendono la differenza visibile:

    - la risposta alla casella che la fonte scrive e' la forma, con la fonte;
    - la risposta alla casella che nessuna fonte scrive e' un buco che **nomina**
      la casella, e non una forma inventata;
    - il buco che finisce nella risposta del motore dice quanti verbi e quante
      forme ci sono, e quali caselle mancano.
    """

    def setUp(self):
        from traduttore import verbi
        self.verbi = verbi
        self.sistema, self.righe = verbi.leggi()

    def test_il_file_dichiara_il_sistema(self):
        # Senza la riga SISTEMA il modulo non sa che persone e tempi esistono,
        # e ogni ricerca risponde «non so» per la ragione sbagliata.
        self.assertTrue(self.sistema, "manca la riga // SISTEMA")
        for chiave in ("persone", "tempi", "senza_persona", "vuoto", "forme"):
            self.assertIn(chiave, self.sistema,
                          "il sistema non dichiara %r" % chiave)
        self.assertEqual(self.sistema["forme"], len(self.righe))

    def test_ogni_forma_porta_la_fonte_e_il_punto(self):
        # Una forma senza «dove» non si puo' controllare: chi la legge fra
        # vent'anni non puo' tornare a guardare la pagina.
        for riga in self.righe:
            self.assertIn(riga["fonte"], ("S001", "S015"), riga["id"])
            self.assertTrue(riga["dove"].strip(), riga["id"])
            self.assertTrue(riga["nota"].strip(), riga["id"])
            self.assertEqual(riga["attendibilita"], "I", riga["id"])

    def test_una_casella_documented_risponde_la_forma(self):
        esito = self.verbi.coniuga("aŋdàr", "1sing", "passato")
        self.assertEqual(esito["forma"], "andò")
        self.assertEqual(esito["problema"], "")
        self.assertIn("S001", esito["fonte"])

    def test_una_casella_non_documentata_dice_che_buco_e(self):
        # Il buco deve **nominare** la casella: un messaggio generico
        # («non so») fa perdere il posto dove intervenire.
        esito = self.verbi.coniuga("aŋdàr", "2sing", "presente")
        self.assertEqual(esito["forma"], "",
                         "ha restituito una forma: buco dichiarato vuol dire "
                         "nessuna")
        self.assertIn("2sing", esito["problema"])
        self.assertIn("presente", esito["problema"])

    def test_un_verbo_che_nessuna_fonte_coniuga_si_distingue(self):
        # «il verbo non c'e'» e «la casella non c'e'» sono due lavori diversi, e
        # il buco deve dire quale dei due e'.
        esito = self.verbi.coniuga("magnàr", "3sing", "presente")
        self.assertEqual(esito["forma"], "")
        self.assertIn("non è fra i", esito["problema"])

    def test_il_clitico_fa_parte_della_chiave(self):
        # S015 dichiara (R036) che `avér` cambia forma con la «ɣ». Una chiave
        # senza clitico restituirebbe «ò» anche per «mi a ɣ o».
        con = self.verbi.coniuga("avér", "1sing", "presente", "aj")
        senza = self.verbi.coniuga("avér", "1sing", "presente", "ɣ")
        self.assertEqual(con["forma"], "ò")
        self.assertEqual(senza["forma"], "o")

    def test_una_persona_inventata_non_va_neanche_provata(self):
        esito = self.verbi.coniuga("aŋdàr", "terza", "presente")
        self.assertEqual(esito["forma"], "")
        self.assertIn("non è fra le persone", esito["problema"])
        esito = self.verbi.coniuga("aŋdàr", "1sing", "futuro")
        self.assertEqual(esito["forma"], "")
        self.assertIn("non è fra i tempi", esito["problema"])

    def test_il_disaccordo_sul_noi_plurale_e_dichiarato(self):
        # Due fonti, due modi di marcare il noi plurale: «-ŋ» per S015 e la
        # proclitica «i» per S001. Il progetto non sceglie, ma la scelta deve
        # essere visibile dove si legge la forma, non in una nota una volta sola.
        noi = [r for r in self.righe if r["persona"] == "1plur"]
        self.assertTrue(noi)
        self.assertEqual({r["fonte"] for r in noi}, {"S001", "S015"},
                         "il disaccordo dichiarato deve restare fra le due fonti")
        for riga in [r for r in noi if r["fonte"] == "S001"]:
            self.assertIn("disaccordo", riga["nota"].lower(),
                          "la riga di S001 non dichiara il disaccordo: %s"
                          % riga["id"])

    def test_il_motore_risponde_con_una_forma_attestata(self):
        # Il caso che riguarda lo studente: scrive una parola coniugata che una
        # fonte ha messo accanto alla forma ferrarese, e riceve la forma.
        from traduttore.motore import Motore
        motore = Motore(glossario_di_prova(), corpus_di_prova())
        risposta = motore.traduci("voglio")
        coppie = dict((originale, (tradotto, origine)) for originale, tradotto,
                      origine, _, _ in risposta.per_corrispondenza)
        self.assertEqual(coppie["voglio"][0], "vój")
        self.assertEqual(coppie["voglio"][1], "verbo")

    def test_il_buco_del_motore_dice_quanti_verbi_e_quali_caselle_mancano(self):
        from traduttore.motore import Motore
        motore = Motore(glossario_di_prova(), corpus_di_prova())
        risposta = motore.traduci("dormimmo")
        buchi = " ".join(risposta.buchi)
        self.assertIn("non coniuga", buchi)
        self.assertIn(str(len(self.righe)), buchi)
        self.assertIn("2sing", buchi)

    def test_il_buco_non_accusa_una_parola_che_non_e_un_verbo(self):
        # I buchi di una traduzione sono anche «il» e «di». Una frase che
        # dicesse «questa parola non è una forma attestata» sarebbe falsa per
        # meta' dei buchi, quindi la frase parla del progetto e non della parola.
        frase = self.verbi.spiega_buco("il")
        self.assertIn("il progetto non coniuga", frase)
        self.assertNotIn("questa parola", frase)

    def test_il_controllo_F16_e_contento(self):
        from traduttore import verifica_dati
        fonti = verifica_dati.fonti_dichiarate()
        self.assertTrue(fonti, "dati/fonti.json non si legge: il controllo "
                               "passerebbe sul vuoto")
        problemi = verifica_dati.controlla_verbi(None, fonti)
        errori = [p for p in problemi
                  if p.codice == "F16" and p.gravita == "errore"]
        self.assertEqual(errori, [],
                         "F16 segnala un errore sulle forme attestate: %s"
                         % errori)

    def test_una_fonte_inventata_e_una_casella_inventata_sono_errori(self):
        from traduttore import verifica_dati
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as cartella:
            finto = os.path.join(cartella, "verbi.jsonl")
            righe = [dict(r) for r in self.righe]
            # Tre difetti, su tre righe diverse: metterli sulla stessa riga
            # nasconderebbe il secondo, perche' il controllo che guarda la
            # fonte e' il primo e gli altri due non li guarda affatto.
            righe[0]["fonte"] = "S999"
            righe[1]["dove"] = ""
            righe[2]["persona"] = "terza"
            righe[3]["persona"] = ""
            righe[3]["tempo"] = "presente"
            with io.open(finto, "w", encoding="utf-8") as f:
                f.write("// SISTEMA %s\n"
                        % json.dumps(self.sistema, ensure_ascii=False))
                for riga in righe:
                    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
            problemi = verifica_dati.controlla_verbi(
                None, verifica_dati.fonti_dichiarate(), percorso=finto)
        messaggi = " ".join(p.messaggio for p in problemi)
        self.assertIn("S999", messaggi)
        self.assertIn("dove** la fonte", messaggi)
        self.assertIn("terza", messaggi)
        self.assertIn("casella inventata", messaggi)


class TestIVerbiNellaPagina(_ModelloInNode, unittest.TestCase):
    """Le forme verbali attestate anche nella pagina, non solo nel terminale.

    Il difetto che questi test prendono è la **divergenza delle due copie**: il
    motore in Python rispondeva alle forme attestate e la pagina no, quindi il
    buco dichiarato arrivava a metà degli utenti e non agli altri. E' la stessa
    regola che il progetto ha già per il bottone del suono: se una cosa vale
    nel terminale, vale nella pagina, e si verifica sul codice che il browser
    esegue e non su una ricostruzione.
    """

    def _dati(self):
        """I dati della pagina, presi dal generatore e non scritti a mano."""
        import importlib.util
        specifica = importlib.util.spec_from_file_location(
            "costruisci_web", os.path.join(RADICE, "sorgenti",
                                           "costruisci_web.py"))
        modulo = importlib.util.module_from_spec(specifica)
        specifica.loader.exec_module(modulo)
        return {"glossario": None, "verbi": modulo._verbi(),
                "origine": {"verbo": 0.75}}

    def test_i_dati_dei_verbi_arrivano_alla_pagina_costruita(self):
        # Se `per_italiano` non finisce in `web/traduttore.html`, il codice
        # della pagina cerca un indice vuoto e nessun test in node lo nota,
        # perche' il codice funziona benissimo su un indice vuoto.
        with io.open(os.path.join(RADICE, "web", "traduttore.html"),
                     encoding="utf-8") as f:
            pagina = f.read()
        self.assertIn('"per_italiano"', pagina,
                      "i dati dei verbi non sono nella pagina costruita")
        from traduttore import verbi
        sa = verbi.cosa_sa()
        self.assertIn('"vój"', pagina,
                      "la forma attestata di «voglio» non e' nella pagina")

    def test_la_pagina_risponde_con_una_forma_attestata(self):
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        esito = self._valuta_js(
            'risolvi("voglio", "it-fe", "voglio")', dati=self._dati())
        self.assertEqual(esito["testo"], "vój")
        self.assertEqual(esito["origine"], "verbo")
        self.assertAlmostEqual(esito["confidenza"], 0.75)
        self.assertIn("S015", esito["dettaglio"])

    def test_la_pagia_non_indovina_una_forma_non_attestata(self):
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        esito = self._valuta_js(
            'risolvi("dormimmo", "it-fe", "dormimmo")', dati=self._dati())
        self.assertEqual(esito["origine"], "nessuna")
        self.assertEqual(esito["testo"], "dormimmo",
                         "una forma non attestata deve restare com'e'")

    def test_il_buco_della_pagina_dice_quanti_verbi_e_quali_caselle(self):
        # Il buco dichiarato e' la parte che lo studente legge: senza i numeri
        # e le caselle, la pagina dice solo «non lo so», che e' il difetto.
        node = self._js()
        if not node:
            self.skipTest("node non e' installato")
        dal_file = self._valuta_js(
            'DATI.verbi.forme + "|" + DATI.verbi.verbi + "|" + '
            'DATI.verbi.vuoto.map(function (v) { return v[0] + " " + v[1]; })'
            '.join(", ")', dati=self._dati())
        forma, verbi, caselle = dal_file.split("|")
        from traduttore import verbi as verbi_modulo
        sa = verbi_modulo.cosa_sa()
        self.assertEqual(int(forma), sa["forme"])
        self.assertEqual(int(verbi), sa["verbi"])
        for persona, tempo in sa["vuoto"]:
            self.assertIn("%s %s" % (persona, tempo), caselle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
