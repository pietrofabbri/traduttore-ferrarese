"""I controlli sui dati.

Il glossario e' una base di dati che qualcuno riempie a mano, e una base di
dati riempita a mano si rovina in tre modi: con le voci duplicate, con le
voci senza fonte e con le voci che dicono una cosa e il glossario dice
un'altra. I controlli qui sotto cercanoono esattamente questi tre guasti e
nient'altro: non un controllo che puo' fallire per un motivo estetico.

Un controllo che segnala un problema che non c'e' e' peggio di nessun
controllo, perche' quando smette di essere credibile nessuno lo legge piu'.

**I controlli non correggono:** segnalano. La correzione la fa una persona,
perche' il glossario e' un fatto e i fatti non si correggono in automatico.
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass

from .corpora import TIPI
from .fonetica import ipa_valida, leggi_sistema
from .glossario import ATTENDIBILITA
from .varieta import VARIETA, _nome_valido, codice_valido


@dataclass
class Problema:
    codice: str
    dove: str
    messaggio: str
    gravita: str = "errore"  # `errore` o `avviso`

    def riga(self) -> str:
        marchio = "ERRORE" if self.gravita == "errore" else "avviso"
        return "[%s] %s %s - %s" % (marchio, self.codice, self.dove, self.messaggio)


def controlla_varieta(varieta) -> list:
    """Le cinque varieta' ci sono, sono cinque e sappiamo da dove vengono.

    Una tassonomia che perde una varieta' non perde una riga: perde la meta'
    del territorio. E' il controllo che rende impossibile dimenticare
    l'occidentale o il transpadano perche' nel frattempo il glossario si
    riempie di parole cittadine.
    """
    problemi = []
    visti = []
    for voce in varieta.voci:
        codice = voce.get("codice", "")
        dove = codice or "(senza codice)"
        if codice in visti:
            problemi.append(Problema("V1", dove, "varieta' dichiarata due volte"))
        visti.append(codice)
        if not codice_valido(codice):
            problemi.append(Problema(
                "V2", dove, "codice %r fuori dall'insieme %s"
                % (codice, ", ".join(VARIETA))))
            continue
        if not _nome_valido(voce.get("nome", "")):
            problemi.append(Problema(
                "V3", dove, "il nome %r non nomina nessuna delle cinque varieta'"
                % voce.get("nome", "")))
        if not voce.get("territori"):
            # Senza territorio la varieta' e' una parola. Non e' un errore da
            # cui non si possa uscire, ma e' un errore da non dimenticare.
            problemi.append(Problema(
                "V4", dove, "varieta' senza territorio: non si sa dove si parla",
                gravita="avviso"))
        if voce.get("attendibilita") == "D" and not voce.get("fonte"):
            problemi.append(Problema("V5", dove, "varieta' documentata senza fonte"))
    mancanti = [c for c in VARIETA if c not in visti]
    if mancanti:
        problemi.append(Problema(
            "V6", ", ".join(mancanti),
            "le varieta' assenti da dati/varieta.json: dichiarale anche vuote"))
    return problemi


def controlla_glossario(glossario) -> list:
    problemi = []
    visti = set()
    # Una voce senza la sua parte ferrarese o italiana non e' una voce: e' un
    # appunto. Si segnala e non si indice, perche' un indice con dentro una
    # voce a meta' fa tradurre cose a caso.
    for voce in glossario.voci:
        dove = voce.id or "(senza id)"
        if not voce.id:
            problemi.append(Problema("G1", dove, "voce senza id"))
        elif voce.id in visti:
            problemi.append(Problema("G2", dove, "id duplicato nel glossario"))
        visti.add(voce.id)

        if not voce.ferrarese or not voce.italiano:
            problemi.append(Problema(
                "G3", dove, "voce con un lato solo: %r / %r" % (voce.ferrarese, voce.italiano)))
            continue

        # Il controllo piu' importante del progetto: nessuna voce si dichiara
        # documentata se non dice da dove viene.
        if voce.attendibilita == "D" and not voce.fonte:
            problemi.append(Problema(
                "G4", dove,
                "attendibilita D senza fonte: o si mette la fonte, o "
                "l'attendibilita scende a I o M"))
        if voce.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "G5", dove, "attendibilita %r fuori dall'insieme %s"
                % (voce.attendibilita, ", ".join(ATTENDIBILITA))))
        if voce.fonte and len(voce.fonte) < 6:
            problemi.append(Problema(
                "G6", dove, "fonte troppo breve per essere controllabile: %r" % voce.fonte))
        # Una voce dichiarata `da verificare` che si dichiara anche `D` e' una
        # contraddizione: si sta affermando un fatto che non e' ancora stato
        # controllato. Non e' un errore che blocca, ma e' il tipo di errore che
        # si propaga di voce in voce e dopo venti passaggi sembra un fatto.
        if voce.da_verificare and voce.attendibilita == "D":
            problemi.append(Problema(
                "G7", dove,
                "voce non verificata ma dichiarata documentata: o si verifica, "
                "o l'attendibilita scende", gravita="avviso"))
        # La varieta' e' obbligatoria perche' una parola senza varieta' e' una
        # parola che non si sa a chi servire. Non e' un campo che si riempie
        # «per completezza»: e' quello che distingue una parola di Bondeno da
        # una parola che si dice anche a Ferrara.
        if not voce.varieta:
            problemi.append(Problema(
                "G8", dove,
                "voce senza varieta': dichiara in quale delle cinque vale "
                "(%s)" % ", ".join(VARIETA)))
        elif not codice_valido(voce.varieta):
            problemi.append(Problema(
                "G9", dove, "varieta' %r fuori dall'insieme %s"
                % (voce.varieta, ", ".join(VARIETA))))
        # Il significato moderno e' l'unica colonna del progetto che puo'
        # essere scritta da qualcuno che non ha guardato nessun dizionario:
        # nessun controllo meccanico puo' accorgersene, quindi l'unica difesa
        # e' strutturale: nessuna riga entra senza l'indirizzo da cui e' stata
        # presa. Senza questo controllo `moderno` e' l'unico campo del glossario
        # che puo' inventare, e sarebbe una colonna di definizioni inventate
        # accanto a 10.387 voci che portano la fonte.
        if voce.moderno and not voce.fonte_moderno:
            problemi.append(Problema(
                "G10", dove,
                "significato moderno senza fonte: si rimuove il significato, "
                "o si scrive l'articolo da cui e' stato preso"))
        # Il contrario: una fonte senza significato e' un resto di raccolta. Non
        # e' un errore che blocca, perche' puo' succedere che la fonte cambi
        # articolo, ma nessuno deve accorgersene per caso: e' un avviso.
        if voce.fonte_moderno and not voce.moderno:
            problemi.append(Problema(
                "G11", dove,
                "fonte del significato moderno senza significato: resta vuoto",
                gravita="avviso"))
        # I sinonimi da soli non spiegano niente: dicono «e' come altre parole»
        # senza dire quali. Se il significato non c'e', i sinonimi non hanno
        # niente a cui appigliarsi e vengono persi in tavola.
        if voce.sinonimi and not voce.moderno:
            problemi.append(Problema(
                "G12", dove,
                "sinonimi senza significato moderno: restano inutilizzabili",
                gravita="avviso"))
    return problemi


def controlla_fonetica(fonetica, glossario, corpus, varieta=None) -> list:
    """Le trascrizioni IPA: quattro cose, e sono tutte verificabili.

    Una trascrizione e' un documento che si mette accanto a una parola e che
    qualcuno, magari fra vent'anni, leggerà per far dire a uno studente come
    si dice. Quindi deve dire **di cosa sta parlando** (F1), **come si
    scrive** (F2), **a chi si riferisce** (F4) e **quanto e' sicura** (F3).

    Il controllo F2 e' l'unico puramente meccanico, e serve a prendere la
    disattenzione piu' comune: mettere la parola italianaaccentata dentro il
    campo IPA e credere di aver trascritto qualcosa.
    """
    problemi = []
    visti = set()
    conosciute = {v.id for v in glossario.voci} | {c.id for c in corpus.coppie}
    coppie_varieta = {c.id: c.varieta for c in corpus.coppie}
    voci_varieta = {v.id: v.varieta for v in glossario.voci}
    for t in fonetica.trascrizioni:
        dove = t.id or "(senza id)"
        if not t.id:
            problemi.append(Problema("F1", dove, "trascrizione senza id"))
        elif t.id in visti:
            problemi.append(Problema("F2", dove, "id duplicato nelle trascrizioni"))
        visti.add(t.id)

        if not t.forma:
            problemi.append(Problema("F3", dove, "trascrizione senza la forma scritta"))
        if not t.ipa:
            problemi.append(Problema("F4", dove, "trascrizione senza IPA"))
        else:
            valida, sospetti = ipa_valida(t.ipa)
            if not valida:
                problemi.append(Problema(
                    "F5", dove,
                    "campi IPA con caratteri che non sono simboli IPA: %s. "
                    "Probabilmente la grafia rimessa al suo posto."
                    % " ".join(sospetti)))
        if not t.riferimento:
            problemi.append(Problema("F6", dove, "trascrizione senza riferimento"))
        elif t.riferimento not in conosciute:
            problemi.append(Problema(
                "F7", dove,
                "riferimento %r che non e' nel glossario ne' nel corpus: la "
                "trascrizione non descrive niente" % t.riferimento))
        if t.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "F8", dove, "attendibilita %r non valida" % t.attendibilita))
        if t.attendibilita == "D" and not t.fonte:
            problemi.append(Problema(
                "F9", dove,
                "trascrizione documentata senza fonte: per `D` la fonte deve "
                "dire chi ha ascoltato, dove e quando"))
        if t.da_verificare and t.attendibilita == "D":
            problemi.append(Problema(
                "F10", dove,
                "trascrizione non verificata ma dichiarata documentata",
                gravita="avviso"))
        if not codice_valido(t.varieta):
            problemi.append(Problema(
                "F11", dove, "varieta' %r fuori dall'insieme %s"
                % (t.varieta or "", ", ".join(VARIETA))))
        # La stessa parola in due varieta' ha due trascrizioni, e non una:
        # e' la ragione per cui questa tabella esiste.
        attesa = voci_varieta.get(t.riferimento) or coppie_varieta.get(t.riferimento)
        if attesa and t.varieta and attesa != t.varieta:
            problemi.append(Problema(
                "F12", dove,
                "trascrizione %s in varieta' %r, ma %s e' dichiarata %r"
                % (t.forma, t.varieta, t.riferimento, attesa), gravita="avviso"))
    # F13 cerca **due trascrizioni della stessa forma scritta**, non due
    # forme simili: `brisa` e `brisà` sono due scelte di scrittura e hanno
    # due suoni diversi, e non e' un conflitto. Il conflitto e' quando la
    # stessa scrittura ha due risposte, e allora bisogna sapere quale vale.
    per_forma = {}
    for t in fonetica.trascrizioni:
        chiave = (t.riferimento,
                  (t.forma or "").strip().lower().replace("'", "").replace("’", ""))
        per_forma.setdefault(chiave, []).append(t)
    for (riferimento, forma), trovate in per_forma.items():
        if len(trovate) > 1:
            problemi.append(Problema(
                "F13", riferimento or "(senza riferimento)",
                "la forma scritta %r ha %d trascrizioni (%s): due persone hanno "
                "scritto due suoni per la stessa scrittura, e va deciso quale "
                "dei due vale"
                % (trovate[0].forma, len(trovate),
                   ", ".join("%s %s" % (t.id, t.ipa) for t in trovate)),
                gravita="avviso"))
    if varieta is not None:
        problemi += _controlla_varieta_delle_trascrizioni(fonetica, glossario, varieta)
    problemi += _controlla_grafia_contro_trascrizione(fonetica)
    problemi += _controlla_voci_dichiarate(fonetica)
    return problemi


def _controlla_voci_dichiarate(fonetica) -> list:
    """**F15**: il riproduttore che suona e' uno che qualcuno ha dichiarato.

    `dati/fonetica.jsonl` dichiara in una riga quale voce suona il sistema e
    fra quali nomi si puo' scegliere. Il controllo chiede tre cose, e sono le
    tre cose che rendono la dichiarazione vera:

    1. la riga c'e' e dice qualcosa. Una dichiarazione assente non e' una
       dichiarazione neutra: e' una scelta che nessuno ha preso, e il file
       deve dirlo invece di lasciare che il codice ne prenda una per conto
       suo;
    2. ogni voce — quella del sistema e quella di una riga — sta fra i voti.
       Un nome che non e' fra i voti e' un nome che nessuno ha messo in
       confronto, quindi una scelta fatta a caso;
    3. il programmatore di sintesi, **se c'e'**, conosce quel nome. Il terzo
       punto e' un avviso e non un errore perche' la stessa macchina puo'
       avere un `espeak-ng` diverso: dire che il dato e' sbagliato quando e'
       l'installazione a essere diversa sarebbe un controllo che segnala
       una cosa che non c'e'.
    """
    problemi = []
    dichiarazione = leggi_sistema()
    dove = "dati/fonetica.jsonl"
    if not dichiarazione["dichiarata"]:
        problemi.append(Problema(
            "F15", dove,
            "il file non dichiara la voce che suona: %s. Senza la riga "
            "`// SISTEMA` il progetto usa il ripiego e non lo sa."
            % (dichiarazione["problema"] or "la dichiarazione e' vuota")))
        return problemi

    voti = dichiarazione["voti"]
    if not dichiarazione["velocita"] > 0:
        problemi.append(Problema(
            "F15", dove,
            "velocita' dichiarata %r: una velocita' di %d parole al minute fa "
            "suonare tutto uguale"
            % (dichiarazione["velocita"], dichiarazione["velocita"])))

    scelte = [("il sistema", dichiarazione["voce"])]
    for t in fonetica.trascrizioni:
        if t.voce:
            scelte.append((t.id or t.forma or "(senza id)", t.voce))
    for chi, nome in scelte:
        if nome not in voti:
            problemi.append(Problema(
                "F15", dove if chi == "il sistema" else chi,
                "voce %r scelta da %s che non e' fra i voti dichiarati (%s)"
                % (nome, chi, ", ".join(voti))))

    from . import voce
    if not voce.percorso_espeak():
        return problemi
    conosciute = voce.voci_espeak("it")
    if not conosciute:
        return problemi
    ignoti = []
    for _, nome in scelte:
        if nome not in conosciute and nome not in ignoti:
            ignoti.append(nome)
    if ignoti:
        problemi.append(Problema(
            "F15", dove,
            "voci scelte che questo espeak-ng non conosce: %s. Se il nome e' "
            "giusto, l'installazione e' quella che non le ha."
            % ", ".join(ignoti), gravita="avviso"))
    return problemi


def _controlla_grafia_contro_trascrizione(fonetica) -> list:
    """Le regole dichiarate che non riproducono le trascrizioni gia' nel file.

    Il file `dati/fonetica.jsonl` porta in testa un sistema di regole di
    lettura, e il modulo `legge` lo applica. Se il sistema fosse giusto, ogni
    riga del file uscirebbe fuori da `legge.leggi` senza differenze.

    Il confronto pero' va fatto con criterio, e la prima stesura di questo
    controllo sbagliava in un modo che costava un avviso intero: contava
    `por'tar` e `port'ar` come diverse e le chiamava «l'accento cade sulla
    sillaba diversa». Non era l'accento: era la **sillabificazione**.
    `por.tar` e `port.ar` hanno gli stessi suoni e lo stesso accento, e dove
    finisca il confine fra due consonanti e' una scelta della fonte, non una
    differenza di suono. Per questo qui si confronta la sequenza dei simboli
    **senza il segno di accento e senza confini di sillaba**: quello che resta
    e' un suono davvero diverso, e nient'altro.

    La lezione resta scritta dentro perche' torni. Un controllo che grida per
    una scelta di sillabificazione smette di essere letto, e un controllo che
    grida per niente fa dubitare delle regole vere. Un numero che non si puo'
    spiegare non va fatto piu' grande per sembrareprudente: va spiegato.

    Quello che resta e' un problema aperto e vero, e il controllo lo dice senza
    risolverlo. Le righe citano Biondelli 1853, che a pagina 205 scrive forme
    con la vocale finale ridotta — `leggere` = `lezar`, `godere` = `godar` —
    cosa che le regole dichiarate qui non descrivono affatto, e rende la `z`
    aspra /s/ dove la regola 6 la lascia come e' scritta. Serve il testo della
    fonte per stabilire quale delle due abbia ragione: questo controllo
    segnala, non sceglie al posto di chi conosce la fonte.
    """
    from .legge import leggi
    problemi = []
    discordi = []
    for t in fonetica.trascrizioni:
        if not (t.forma and t.ipa):
            continue
        ottenuta = leggi(t.forma)["ipa"]
        if ottenuta == t.ipa:
            continue
        if _senza_accento(ottenuta) == _senza_accento(t.ipa):
            # Stessi suoni, stessa tonica, confine di sillaba diverso: non e'
            # un problema e non deve rumorare l'avviso.
            continue
        discordi.append((t.id or "(senza id)", t.forma, t.ipa, ottenuta))
    if not discordi:
        return problemi
    dettaglio = "; ".join(
        "%s %s: nel file %s, dalle regole %s"
        % (ident, forma, ipa, ottenuta)
        for ident, forma, ipa, ottenuta in discordi)
    problemi.append(Problema(
        "F14", "dati/fonetica.jsonl",
        "%d trascrizioni su %d hanno suoni diversi rispetto alle regole "
        "dichiarate in testa al file (%s). Le altre %d coincidono e "
        "coincidono anche nell'accento: quello che le divide dalle prime e' "
        "solo la sillabificazione, che non e' un suono. Le %d che restano "
        "hanno tutte la stessa natura: la fonte (Biondelli 1853, pag. 205) "
        "ha forme con la vocale finale ridotta e rende la `z` aspra /s/, e "
        "le regole qui dichiarate non descrivono ne' l'una ne' l'altra."
        % (len(discordi), len(fonetica.trascrizioni), dettaglio,
           len(fonetica.trascrizioni) - len(discordi), len(discordi)),
        gravita="avviso"))
    return problemi


def _senza_accento(ipa: str) -> str:
    """La IPA pronta per il confronto: senza accento e senza varieta' di carta.

    Il carattere `ɡ` (U+0261, «script g») e la `g` (U+0067) sono lo stesso
    suono scritti in due modi, e in un file di trascrizioni di centottocento
    anni e' normale che le due forme convivano. Senza questa normalizzazione
    il controllo direbbe «suono diverso» dove il suono e' lo stesso, e un
    avviso che grida per niente smette di essere letto.
    """
    return ipa.replace("ˈ", "").replace("'", "").replace("ɡ", "g").strip("/")


def _controlla_varieta_delle_trascrizioni(fonetica, glossario, varieta) -> list:
    """Le varieta' che hanno parole ma non suoni.

    E' il controllo che rende utile la parte audio: senza di esso si puo'
    avere un glossario con trenta parole e venti suoni e l'idea che si stia
    coprendo il territorio. In realta' una varieta' puo' avere parole e
    nessun suono, e quello e' un buco che va detto.

    Una varieta' **senza parole** non si segnala: e' un vuoto noto,
    dichiarato dalla tassonomia, e un controllo che segnala sempre e' un
    controllo che dopo tre settimane nessuno legge piu'.
    """
    problemi = []
    con_suono = {t.varieta for t in fonetica.trascrizioni}
    conteggi = varieta.conteggi(glossario=glossario)
    for codice in VARIETA:
        if codice in con_suono:
            continue
        if conteggi.get(codice, {}).get("glossario", 0) > 0:
            problemi.append(Problema(
                "F14", codice,
                "%d voci in questa varieta' e nessuna trascrizione: le parole ci "
                "sono, i suoni no" % conteggi[codice]["glossario"],
                gravita="avviso"))
    return problemi


DATI = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "dati")


def fonti_dichiarate(percorso: str = None) -> list:
    """Le fonti di `dati/fonti.json`, come lista di dizionari.

    Va qui e non nella CLI perche' un controllo che non sa da solo quali sono
    le fonti dichiarate va chiamato con una lista che qualcuno ha passato a
    mano, e basta un richiamo sbagliato perche' il controllo diventi verde
    perche' nessuno gli ha dato niente da controllare. Se il file non c'e', la
    lista e' vuota e **il controllo se ne accorge**: e' il caso peggiore, e lo
    dice perche' e' meglio di un controllo che passa sul vuoto.
    """
    percorso = percorso or os.path.join(DATI, "fonti.json")
    if not os.path.exists(percorso):
        return []
    with io.open(percorso, encoding="utf-8") as f:
        return json.load(f).get("fonti", [])


def controlla_verbi(verbi, fonti=None, percorso: str = None) -> list:
    """**F16**: le forme verbali attestate sono verificabili una per una.

    Il controllo non guarda se la coniugazione e' giusta — quello lo fa un
    parlante, e nessun programma lo puo' fare al posto suo. Guarda tre cose
    che sono verificabili meccanicamente e che, se mancano, rendono la riga
    inutilizzabile:

    - **la fonte** e' fra quelle dichiarate in `dati/fonti.json`, e la sua riga
      dice **dove** scrive la forma: una forma senza pagina e senza riga non si
      puo' controllare, e chi la legge fra vent'anni non puo' tornare a
      guardarla;
    - **la persona** e' fra quelle dichiarate, o e' vuota e il tempo e' uno dei
      due che non hanno persona (gerundio e participio): una casella inventata
      e' una riga che nessuno potra' usare;
    - **il tempo** e' fra quelli dichiarati.

    E poi una cosa che non e' un errore ma un disaccordo: due fonti che scrivono
    la stessa casella in due modi diversi. Non e' un errore perche' il progetto
    non sceglie fra due fonti, e segnalarlo come errore obbligherebbe a scegliere.
    """
    from . import verbi as verbi_modulo
    problemi = []
    # Il percorso e' un parametro perche' un controllo che si puo' chiamare
    # solo sul file dichiarato si puo' provare solo sul file dichiarato, e
    # quindi non si puo' provare con un file che abbia un difetto. Il parametro
    # serve per quello, e non a girare il controllo su un file qualsiasi.
    sistema, righe = verbi_modulo.leggi(percorso or verbi_modulo.PERCORSO)
    if not sistema:
        return [Problema(
            "F16", percorso or verbi_modulo.PERCORSO,
            "manca la riga `// SISTEMA`: senza di essa il modulo non sa che "
            "persone e tempi esistono, e ogni ricerca su una forma coniugata "
            "risponde «non so» per la ragione sbagliata",
            gravita="avviso")]

    persone = sistema.get("persone") or []
    tempi = sistema.get("tempi") or []
    # Quali tempi non hanno persona e' una **dichiarazione del file**, non una
    # costante del codice: se un giorno una fonte documenta il gerundio con
    # una persona, la riga che lo dice e' quella giusta e va cambiata la' con
    # la fonte, non qui.
    senza_persona = sistema.get("senza_persona") or []
    if not senza_persona:
        problemi.append(Problema(
            "F16", percorso or verbi_modulo.PERCORSO,
            "la riga SISTEMA non dichiara `senza_persona`: senza sapere quali "
            "tempi non hanno persona il controllo non puo' distinguere una "
            "forma finita senza persona — che e' una casella inventata — da un "
            "participio che ce l'ha per natura",
            gravita="avviso"))
    conosciute = {f.get("id"): f for f in (fonti or [])}

    for riga in righe:
        dove = riga.get("id", "senza id")
        fonte = riga.get("fonte", "")
        if fonte not in conosciute:
            problemi.append(Problema(
                "F16", dove,
                "la fonte %r non è fra quelle dichiarate in dati/fonti.json: "
                "una forma che non si può attribuire a nessuna fonte non entra"
                % fonte))
        elif not (riga.get("dove") or "").strip():
            problemi.append(Problema(
                "F16", dove,
                "la fonte %s c'è, ma la riga non dice **dove** la fonte scrive "
                "la forma: senza pagina e riga il dato non si può controllare"
                % fonte))
        if riga.get("tempo") not in tempi:
            problemi.append(Problema(
                "F16", dove,
                "il tempo %r non è fra quelli dichiarati (%s)"
                % (riga.get("tempo"), ", ".join(tempi))))
        persona = riga.get("persona") or ""
        if persona and persona not in persone:
            problemi.append(Problema(
                "F16", dove,
                "la persona %r non è fra quelle dichiarate (%s)"
                % (persona, ", ".join(persone))))
        if not persona and riga.get("tempo") not in senza_persona:
            problemi.append(Problema(
                "F16", dove,
                "la persona è vuota e il tempo %r non è fra %s: una forma "
                "finita senza persona è una casella inventata"
                % (riga.get("tempo"), ", ".join(senza_persona))))

    # Il disaccordo fra due fonti. Due righe con la stessa chiave e due fonti
    # diverse non sono un errore: sono due attestazioni che il progetto non
    # sa mettere d'accordo, e che deve tenere visibili.
    per_casella = {}
    for riga in righe:
        chiave = verbi_modulo.chiave_forma(riga["lemma"], riga.get("persona", ""),
                                          riga["tempo"], riga.get("clitico", ""))
        per_casella.setdefault(chiave, []).append(riga)
    for chiave, gruppo in sorted(per_casella.items()):
        fonti_diverse = {r["fonte"] for r in gruppo}
        if len(fonti_diverse) > 1:
            forme = ", ".join("%s (%s)" % (r["forma"], r["fonte"])
                              for r in gruppo)
            problemi.append(Problema(
                "F16", gruppo[0].get("id", "senza id"),
                "la casella %s è scritta da %d fonti diverse: %s. Il progetto "
                "non sceglie e le due forme restano; decidere spetta a un "
                "parlante" % (chiave.replace("|", " "), len(fonti_diverse),
                              forme),
                gravita="avviso"))
    return problemi


def controlla_corpora(corpus) -> list:
    problemi = []
    visti = set()
    for coppia in corpus.coppie:
        dove = coppia.id or "(senza id)"
        if not coppia.id:
            problemi.append(Problema("C1", dove, "coppia senza id"))
        elif coppia.id in visti:
            problemi.append(Problema("C2", dove, "id duplicato nel corpus"))
        visti.add(coppia.id)

        if not coppia.ferrarese or not coppia.italiano:
            problemi.append(Problema("C3", dove, "coppia con un lato solo"))
            continue
        if not coppia.fonte:
            # Non e' un errore che blocca: e' un errore che isola. La coppia
            # resta nel file ma non entra nel motore, e `Corpus.coppie_valide`
            # fa gia' questo lavoro. Lo segnaliamo perche' il file e' la
            # promessa di una collezione e una voce senza fonte e' una promessa
            # non mantenuta.
            problemi.append(Problema(
                "C4", dove,
                "coppia senza fonte: resta nel file ma il motore non la usa",
                gravita="avviso"))
        if coppia.tipo not in TIPI:
            problemi.append(Problema(
                "C5", dove, "tipo %r fuori dall'insieme %s" % (coppia.tipo, ", ".join(TIPI))))
        if coppia.attendibilita not in ATTENDIBILITA:
            problemi.append(Problema(
                "C6", dove, "attendibilita %r non valida" % coppia.attendibilita))
        if not coppia.varieta:
            problemi.append(Problema(
                "C7", dove,
                "coppia senza varieta': una frase raccolta fuori citta' insegnerebbe "
                "il dialetto di un posto solo a chi e' di un altro"))
        elif not codice_valido(coppia.varieta):
            problemi.append(Problema(
                "C8", dove, "varieta' %r fuori dall'insieme %s"
                % (coppia.varieta, ", ".join(VARIETA))))
    for proverbio in corpus.proverbi:
        dove = proverbio.id or "(senza id)"
        if not proverbio.id:
            problemi.append(Problema("P1", dove, "proverbio senza id"))
        if not proverbio.italiano:
            problemi.append(Problema("P2", dove, "proverbio senza il lato italiano"))
        if not proverbio.ferrarese and not proverbio.popolare:
            problemi.append(Problema(
                "P3", dove, "proverbio senza forma ferrarese: due lati vuoti"))
        if proverbio.ferrarese and proverbio.popolare and proverbio.ferrarese == proverbio.popolare:
            problemi.append(Problema(
                "P4", dove,
                "forma letteraria e popolare uguali: o una delle due e' messa a "
                "torto, o il campo letterario e' inutile qui"))
        if proverbio.attendibilita == "D" and not proverbio.fonte:
            problemi.append(Problema("P5", dove, "proverbio documentato senza fonte"))
    return problemi


def controlla_regole(regole, soglia: float = 0.70) -> list:
    problemi = []
    for regola in regole:
        if regola.accordo < soglia:
            problemi.append(Problema(
                "R1", regola.etichetta(),
                "accordo %0.2f sotto la soglia %0.2f: questa regola non dovrebbe "
                "esistere" % (regola.accordo, soglia), gravita="avviso"))
        if regola.supporto < 2:
            problemi.append(Problema(
                "R2", regola.etichetta(),
                "un solo esempio: non e' una regola, e' un caso"))
    return problemi


def controlla_tenuta(glossario, corpus, in_attesa_glossario=None,
                     in_attesa_corpus=None) -> list:
    """I dati in attesa non entrano e non restano dentro.

    `dati/da_verificare/` e' la fila d'attesa del materiale che non ha ancora
    il diritto di essere pubblicato. Il controllo fa due cose, e sono le due
    sole che contano:

    - **D1**: un id che e' in attesa e anche nel glossario attivo e' un
      errore. Una voce che aspetta la verifica della licenza e che intanto
      viene usata e' il modo piu' economico di pubblicare dati di provenienza
      ignota, e nessuna intenzione cosi' finisce bene;
    - **D2**: una voce in attesa che si dichiara `D` con la sua fonte non
      e' un errore - e' il caso normale, perche' la fonte c'e' ed e' proprio
      quella che non e' verificata - ma e' un avviso, perche' finche' quel
      avviso sta li' nessuno deve crederla documentata.

    Il controllo e' volutamente noioso: due righe di confronto e nient'altro.
    """
    problemi = []
    attese_glossario = {v.id: v for v in (in_attesa_glossario.voci
                                          if in_attesa_glossario else [])}
    attese_corpus = {c.id: c for c in (in_attesa_corpus.coppie
                                      if in_attesa_corpus else [])}
    attive = {v.id for v in glossario.voci} | {c.id for c in corpus.coppie}
    for identificatore in sorted(set(attese_glossario) | set(attese_corpus)):
        if identificatore not in attive:
            continue
        problema = Problema(
            "D1", identificatore,
            "id in attesa di verifica e anche nei dati attivi: si sceglie. O "
            "esce dalla fila d'attesa, o si verifica la licenza della fonte")
        if identificatore in attese_glossario:
            voce = attese_glossario[identificatore]
            if voce.attendibilita == "D" and voce.fonte:
                problema.messaggio += (
                    " (fonte dichiarata: %s, attendibilita %s)"
                    % (voce.fonte, voce.attendibilita))
        problemi.append(problema)
    for voce in (in_attesa_glossario.voci if in_attesa_glossario else []):
        if voce.attendibilita == "D":
            problemi.append(Problema(
                "D2", voce.id,
                "in attesa di licenza verificata e dichiarata documentata "
                "(%s): la riga non si usa, quindi l'attendibilita non conta "
                "ancora" % (voce.fonte or "senza fonte"), gravita="avviso"))
    return problemi


def riepilogo(problemi: list) -> dict:
    errori = [p for p in problemi if p.gravita == "errore"]
    return {
        "errori": len(errori),
        "avvisi": len(problemi) - len(errori),
        "ok": not errori,
    }


def buchi_dichiarati(glossario, corpus, fonetica=None) -> list:
    """Quello che manca, in numeri, con il motivo per cui manca.

    Non e' un controllo e non lo e' diventato: un controllo che segnala un
    buco che il progetto ha dichiarato fa fallire la CI per sempre, e il
    progetto non vuole fallire, vuole dire. Quello che vuole e' che il buco sia
    **un numero che si aggiorna**, perche' «non abbiamo le trascrizioni IPA» e'
    un fatto e «ne abbiamo 28 su 234» e' un fatto che si puo' correggere.

    Ogni riga porta `nome`, `quanti`, `totale` (quando ha senso) e `nota`:
    il motivo per cui quel numero non si riduce da solo. Una riga senza nota
    non dice niente e sta peggio che non esserci.

    La stessa funzione alimenta il comando `buchi` e il pannello della pagina:
    un numero che ognuno calcola per conto suo e' un numero che dopo un mese
    non e' piu' vero per nessuno.
    """
    buchi = []

    def aggiungi(nome, quanti, nota, totale=None):
        if not quanti:
            return
        riga = {"nome": nome, "quanti": quanti, "nota": nota}
        if totale is not None:
            riga["totale"] = totale
        buchi.append(riga)

    voci = glossario.voci
    locuzioni = [v for v in voci if " " in (v.ferrarese or "")]
    aggiungi("locuzioni nel glossario", len(locuzioni),
             "una voce di piu' parole: il motore le accorpa prima di tradurre, "
             "ma restano piu' difficili da mettere in un livello di gioco")

    if fonetica is not None:
        con_suono = {t.riferimento for t in fonetica.trascrizioni}
        senza = [v for v in voci if v.id not in con_suono]
        aggiungi("voci senza trascrizione IPA", len(senza),
                 "si aggiunge una riga in dati/fonetica.jsonl; senza un "
                 "parlante non si puo' fare, e la pagina lo dice accanto "
                 "alla parola", totale=len(voci))
        verificate = fonetica.quante_verificate()
        aggiungi("trascrizioni non verificate da un parlante",
                 len(fonetica.trascrizioni) - verificate,
                 "attendibilita I con da_verificare: sono una lettura della "
                 "grafia, non un ascolto", totale=len(fonetica.trascrizioni))

    senza_popolare = [p for p in corpus.proverbi if not p.popolare]
    aggiungi("proverbi senza la forma che si dice", len(senza_popolare),
             "il campo `popolare`: serve qualcuno che dica come li si dice, "
             "e finche' quel campo e' vuoto il proverbio ha una forma sola",
             totale=len(corpus.proverbi))

    aggiungi("proverbi senza significato",
             sum(1 for p in corpus.proverbi if not p.significato),
             "il significato e' la parte che il motore non sa tradurre: "
             "senza, il proverbio e' una frase con due lati e nessun ponte")

    # La stessa condizione del controllo C4, non quella di `Coppia.valida()`:
    # C4 conta le coppie senza fonte, e un numero che non coincide con il
    # controllo che lo nomina e' un numero che non si puo' correggere.
    coppie_senza_fonte = [c for c in corpus.coppie if not (c.fonte or "").strip()]
    aggiungi("coppie senza fonte", len(coppie_senza_fonte),
             "restano nel file ma il motore non le usa: il controllo C4 lo dice",
             totale=len(corpus.coppie))

    da_verificare = [v for v in voci if v.da_verificare]
    aggiungi("voci dichiarate da verificare", len(da_verificare),
             "attendibilita I: la scrittura c'e' ma nessuno l'ha ancora "
             "controllata con un informatore", totale=len(voci))

    # Il numero di parole che la fonte non spiega. Va detto perche' e' l'unico
    # modo di distinguere «questa parola non ha un significato» da «non
    # abbiamo chiesto bene»: il vuoto e' dichiarato, e dichiararlo stanca
    # piu' che confessarlo una volta sola. La colonna «in italiano di oggi» e'
    # l'unica che si riempie da una fonte esterna, quindi e' l'unica in cui
    # il buco puo' essere un difetto di raccolta invece che un dato assente.
    senza_moderno = [v for v in voci if not v.moderno]
    aggiungi("voci senza significato moderno in fonte", len(senza_moderno),
             "la fonte non ha l'articolo, o dichiara di non averne la "
             "definizione: non e' una parola senza significato, e' una parola "
             "che quella fonte non spiega", totale=len(voci))

    # Le parole che non suonano. Il numero e' dichiarato perche' la pagina
    # mette un pulsante solo dove suona, e uno studente che cerca «magnàr» e
    # non trova niente deve sapere che il motivo non e' che la parola non
    # esiste. Il numero si riduce quando il dubbio si risolve, quindi e' un
    # numero che si puo' correggere, che e' la condizione per stare qui.
    #
    # Il conto viene dalle stesse regole di lettura che producono i suoni,
    # non dal manifesto: se il manifesto dicesse 12 e le regole ne dicessero
    # 15, il numero giusto sarebbe 15 e un altro buco — quello che nessuno
    # guarda perche' non e' un errore.
    if fonetica is not None and fonetica.trascrizioni:
        from . import voce
        muti = []
        for t in fonetica.trascrizioni:
            esito = voce.voce(t.forma)
            if esito["problema"] or esito["dubbi"]:
                muti.append(t)
        aggiungi("trascrizioni che non hanno un suono generato", len(muti),
                 "una parola con un dubbio dichiarato non suona: suonarla "
                 "insegnerebbe il suono sbagliato. Il numero scende quando il "
                 "dubbio si risolve, e non quando qualcuno decide di suonarla "
                 "lo stesso", totale=len(fonetica.trascrizioni))

    return buchi
