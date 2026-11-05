# -*- coding: utf-8 -*-
"""Le correzioni dei parlanti, e quello che se ne puo' inferire.

**Che cosa e' una correzione.** Una persona che parla ferrarese legge una
traduzione del motore, la trova sbagliata e scrive come si dice: la frase
intera, e se vuole la pronuncia fra parentesi quadre, `[al ˈkan]`. La pagina
prepara la riga, la persona la consegna (copiata, scaricata o in una
segnalazione su GitHub), e chi tiene il repository la importa. La pagina non
manda niente da sola: e' la regola del progetto, nessuna richiesta di rete.

**Una correzione e' una fonte; un'inferenza no.** E' la linea che regge il
modulo, ed e' la stessa che separa il glossario dalle proposte del livello IA:

- una correzione che dice **chi** l'ha scritta, **che varieta'** parla e che
  ha il **consenso** a stare nel repository e' un dato documentato. Applicata
  (`applica`), diventa una coppia `D` se e' una frase, una voce `D` del
  glossario che **corregge** la voce sbagliata se e' una parola, e una
  trascrizione `D` fra quadre se porta la pronuncia. Il traduttore la usa
  subito: una voce che ne corregge un'altra viene prima di lei;
- un'**inferenza** e' quello che il programma ricava confrontando la forma
  sbagliata con quella giusta: «la `ŋ` finale di S006 il parlante la scrive
  `n`». Il programma cerca le altre voci della stessa fonte dove la stessa
  differenza si ripete e le scrive in `dati/correzioni/inferenze.jsonl`, con
  quante correzioni la sostengono e quante la smentiscono. **Non tocca il
  glossario.** Le inferenze si leggono — le legge chi tiene il repository, o
  Claude quando glielo si chiede — e diventano dati solo quando un parlante le
  conferma.

**Perche' le inferenze servono.** Il glossario ha diciassettemila voci quasi
tutte non verificate, e un parlante ne correggera' qualche decina. Ma una
correzione di grafia di solito non riguarda una parola: riguarda il modo in
cui una fonte scrive un suono, e quindi centinaia di voci. L'inferenza dice
**dove guardare**; la conferma resta di una persona.

I codici dei controlli sono X1–X10 per le correzioni e Z1–Z3 per le inferenze.
"""
from __future__ import annotations

import difflib
import io
import json
import os
import re
import unicodedata

from . import normalizza
from .fonetica import ipa_valida
from .glossario import IT_FE
from .varieta import codice_valido

RADICE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CARTELLA = os.path.join(RADICE, "dati", "correzioni")
PERCORSO = os.path.join(CARTELLA, "correzioni.jsonl")
PERCORSO_INFERENZE = os.path.join(CARTELLA, "inferenze.jsonl")

STATI = ("da_verificare", "applicata", "respinta")
# I tipi di differenza fra la parola proposta e quella corretta.
TIPI = ("confermata", "forma", "sostituzione", "buco", "aggiunta", "tolta")
# Una differenza di forma con piu' di tante regole non e' una grafia diversa:
# e' un'altra parola, e non se ne inferisce niente.
MASSIMO_REGOLE = 3
# Quante voci candidate si scrivono per esteso in un'inferenza. Il numero
# totale c'e' sempre.
ESEMPI = 25

TESTATA_CORREZIONI = (
    "// Le correzioni dei parlanti: una riga per correzione, scritta da\n"
    "// `python3 -m traduttore.cli correzioni importa`, mai a mano. Il\n"
    "// protocollo e' in dati/correzioni/README.md.\n")
TESTATA_INFERENZE = (
    "// Le inferenze ricavate dalle correzioni: file GENERATO da\n"
    "// `python3 -m traduttore.cli correzioni inferisci`, non si modifica a\n"
    "// mano. Un'inferenza non e' una fonte: dice dove guardare, e diventa un\n"
    "// dato solo quando un parlante conferma la voce. Vedi\n"
    "// dati/correzioni/README.md.\n")


# --- lettura e scrittura ------------------------------------------------------

def leggi(percorso: str = PERCORSO) -> list:
    righe = []
    if not os.path.exists(percorso):
        return righe
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.startswith("//"):
                righe.append(json.loads(riga))
    return righe


def scrivi(righe: list, percorso: str = PERCORSO,
           testata: str = TESTATA_CORREZIONI) -> None:
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    with io.open(percorso, "w", encoding="utf-8", newline="\n") as f:
        f.write(testata)
        for riga in righe:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")


def righe_dal_testo(testo: str) -> list:
    """Le righe di correzione dentro un testo qualsiasi.

    Le righe arrivano incollate in un messaggio o in una segnalazione su
    GitHub, quindi tutto quello che non e' un oggetto JSON con
    `"tipo": "correzione"` si salta, come fa `campione importa`.
    """
    trovate = []
    for riga in (testo or "").splitlines():
        riga = riga.strip().strip("`")
        if not riga.startswith("{"):
            continue
        try:
            oggetto = json.loads(riga)
        except ValueError:
            continue
        if isinstance(oggetto, dict) and oggetto.get("tipo") == "correzione":
            trovate.append(oggetto)
    return trovate


# --- i controlli --------------------------------------------------------------

def _problema(codice, dove, messaggio, gravita="errore"):
    from .verifica_dati import Problema
    return Problema(codice, dove, messaggio, gravita=gravita)


def controlla_riga(riga: dict, dove: str = "") -> list:
    """I controlli che valgono per una riga, prima e dopo l'importazione."""
    dove = dove or riga.get("id") or "(senza id)"
    problemi = []
    if not (riga.get("chi") or "").strip():
        problemi.append(_problema(
            "X2", dove, "correzione senza `chi`: una correzione e' una fonte "
            "solo se dice chi l'ha scritta"))
    if not codice_valido(riga.get("varieta") or ""):
        problemi.append(_problema(
            "X3", dove, "varieta' %r fuori dalle cinque: una forma di Bondeno "
            "data a uno studente di Ferrara e' una forma sbagliata"
            % riga.get("varieta")))
    if not (riga.get("italiano") or "").strip() or \
            not (riga.get("ferrarese") or "").strip():
        problemi.append(_problema(
            "X5", dove, "correzione senza l'italiano o senza il ferrarese"))
    ipa = (riga.get("ipa") or "").strip()
    if ipa:
        if not (ipa.startswith("[") and ipa.endswith("]")):
            problemi.append(_problema(
                "X6", dove, "la pronuncia %r non e' fra parentesi quadre: una "
                "pronuncia ascoltata si scrive [cosi'], le barre /cosi'/ sono "
                "le letture della grafia di dati/fonetica.jsonl" % ipa))
        valida, sospetti = ipa_valida(ipa)
        if not valida:
            problemi.append(_problema(
                "X6", dove, "la pronuncia %r usa simboli che non sono IPA: %s"
                % (ipa, " ".join(sospetti))))
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", riga.get("data") or ""):
        problemi.append(_problema(
            "X9", dove, "data %r non nella forma AAAA-MM-GG"
            % riga.get("data")))
    return problemi


def controlla(righe: list, ids_esistenti=None) -> list:
    """X1–X10 su tutte le correzioni del file."""
    problemi, visti = [], set()
    ids_esistenti = ids_esistenti or set()
    for riga in righe:
        identificatore = riga.get("id") or ""
        if not re.match(r"^X\d{4}$", identificatore):
            problemi.append(_problema("X1", identificatore or "(senza id)",
                                      "correzione senza id nella forma X0000"))
        elif identificatore in visti:
            problemi.append(_problema("X1", identificatore, "id duplicato"))
        visti.add(identificatore)
        problemi.extend(controlla_riga(riga, identificatore))
        stato = riga.get("stato")
        if stato not in STATI:
            problemi.append(_problema(
                "X7", identificatore, "stato %r fuori da %s"
                % (stato, ", ".join(STATI))))
        if stato == "applicata":
            create = riga.get("crea") or []
            if not create:
                problemi.append(_problema(
                    "X8", identificatore, "correzione applicata che non dice "
                    "che cosa ha creato"))
            mancanti = [c for c in create if c not in ids_esistenti]
            if ids_esistenti and mancanti:
                problemi.append(_problema(
                    "X8", identificatore, "correzione applicata che rimanda a "
                    "righe che non ci sono: %s" % ", ".join(mancanti)))
        if stato == "respinta" and not (riga.get("motivo") or "").strip():
            problemi.append(_problema(
                "X10", identificatore, "correzione respinta senza il motivo"))
    return problemi


def controlla_regole_frase(regole: list, correzioni_ids=None) -> list:
    """Z4–Z5: una regola di frase viene da correzioni, e ha un contesto vero."""
    problemi = []
    for regola in regole:
        dove = "regola di frase «%s» %s" % (regola.get("italiano"),
                                           regola.get("contesto"))
        if regola.get("contesto") not in ("vocale", "consonante", "fine"):
            problemi.append(_problema(
                "Z4", dove, "contesto fuori da vocale, consonante, fine"))
        if not regola.get("da") or not regola.get("fonte"):
            problemi.append(_problema(
                "Z5", dove, "regola di frase senza le correzioni da cui viene: "
                "non si scrive a mano"))
        elif correzioni_ids is not None:
            mancanti = [i for i in regola["da"] if i not in correzioni_ids]
            if mancanti:
                problemi.append(_problema(
                    "Z5", dove, "rimanda a correzioni che non ci sono: %s"
                    % ", ".join(mancanti)))
    return problemi


def controlla_inferenze(inferenze: list, ids_esistenti=None) -> list:
    """Z1–Z3: un'inferenza non si dichiara una fonte."""
    problemi = []
    for inferenza in inferenze:
        dove = inferenza.get("id") or "(senza id)"
        if "fonte" in inferenza or inferenza.get("attendibilita") == "D":
            problemi.append(_problema(
                "Z1", dove, "un'inferenza con `fonte` o `attendibilita D`: "
                "un'inferenza dice dove guardare, non e' un dato"))
        if not inferenza.get("da"):
            problemi.append(_problema(
                "Z2", dove, "inferenza che non dice da quali correzioni viene"))
        if ids_esistenti:
            for esempio in inferenza.get("esempi", []):
                if esempio.get("voce") not in ids_esistenti:
                    problemi.append(_problema(
                        "Z3", dove, "inferenza su una voce che non c'e': %s"
                        % esempio.get("voce")))
                    break
    return problemi


# --- l'importazione -------------------------------------------------------------

def _chiave_correzione(riga: dict) -> tuple:
    return (normalizza.chiave(riga.get("italiano") or ""),
            normalizza.chiave(riga.get("ferrarese") or ""),
            normalizza.chiave(riga.get("chi") or ""))


# Chi scrive e che varieta' parla, quando la riga non lo dice. Dal 0.40 il sito
# lo usa solo chi lo tiene (vedi `AGENTS.md` §2), e la pagina non chiede piu'
# nome e consenso a ogni correzione.
CHI_PREDEFINITO = "titolare del sito"
VARIETA_PREDEFINITA = "cittadino"


def importa(testo: str, percorso: str = PERCORSO, origine: str = "",
            oggi: str = "") -> dict:
    """Aggiunge al file le correzioni valide del testo; dice che cosa ha fatto.

    Ogni correzione entra **archiviata e da verificare** (`stato:
    "da_verificare"`, `da_verificare: true`): non fa ancora parte del
    traduttore. Ne fa parte quando `promuovi` trova abbastanza conferme dei
    suoi elementi, o quando qualcuno la conferma (`conferma_correzione`).
    `origine` dice da dove e' arrivata (per esempio «segnalazione #12»).
    """
    esistenti = leggi(percorso)
    gia = {_chiave_correzione(r) for r in esistenti}
    maggiore = max([int(r["id"][1:]) for r in esistenti
                    if re.match(r"^X\d{4}$", r.get("id") or "")] or [0])
    nuove, ripetute, scartate = [], [], []
    for riga in righe_dal_testo(testo):
        riga = dict(riga)
        riga.setdefault("chi", CHI_PREDEFINITO)
        if not (riga.get("chi") or "").strip():
            riga["chi"] = CHI_PREDEFINITO
        if not riga.get("varieta"):
            riga["varieta"] = VARIETA_PREDEFINITA
        if not riga.get("data") and oggi:
            riga["data"] = oggi
        problemi = controlla_riga(riga, "(riga da importare)")
        if problemi:
            scartate.append((riga, problemi))
            continue
        if _chiave_correzione(riga) in gia:
            ripetute.append(riga)
            continue
        gia.add(_chiave_correzione(riga))
        maggiore += 1
        pulita = {"id": "X%04d" % maggiore, "stato": "da_verificare",
                  "da_verificare": True}
        if origine:
            pulita["origine"] = origine
        for campo in ("data", "chi", "luogo", "varieta",
                      "italiano", "proposta", "ferrarese", "ipa", "nota",
                      "parole", "versione"):
            if campo in riga and riga[campo] not in (None, ""):
                pulita[campo] = riga[campo]
        nuove.append(pulita)
    if nuove:
        scrivi(esistenti + nuove, percorso)
    return {"nuove": nuove, "ripetute": ripetute, "scartate": scartate}


def conferma(inferenza: dict, voci: list, chi: str, varieta: str, data: str,
             dove: str, glossario, percorso: str = PERCORSO,
             forme: dict = None) -> list:
    """Le voci candidate di un'inferenza che un parlante ha confermato.

    Ogni voce confermata diventa una correzione `da_verificare` **di quella
    voce** (campo `voce`), con il nome di chi l'ha confermata e il posto dove
    l'ha detto (`dove`: una segnalazione, un messaggio, una sessione). E' cosi'
    che un'inferenza smette di essere un'inferenza: non perche' il programma
    l'ha trovata, ma perche' una persona ha detto «si', si dice cosi'».
    `forme` permette al parlante di dare una forma diversa da quella proposta.
    """
    per_id = {v.id: v for v in glossario.voci}
    proposte = {e["voce"]: e["proposta"] for e in inferenza.get("esempi", [])}
    esistenti = leggi(percorso)
    maggiore = max([int(r["id"][1:]) for r in esistenti
                    if re.match(r"^X\d{4}$", r.get("id") or "")] or [0])
    nuove = []
    for voce_id in voci:
        voce = per_id.get(voce_id)
        forma = (forme or {}).get(voce_id) or proposte.get(voce_id)
        if voce is None or not forma:
            raise ValueError("%s non e' fra le candidate di %s"
                             % (voce_id, inferenza.get("id")))
        maggiore += 1
        nuove.append({
            "id": "X%04d" % maggiore, "stato": "da_verificare", "data": data,
            "chi": chi, "varieta": varieta, "da_verificare": True,
            "italiano": voce.italiano,
            "proposta": voce.ferrarese, "ferrarese": forma, "voce": voce.id,
            "inferenza": inferenza.get("id"), "dove": dove,
            "nota": "Confermata da un parlante sull'inferenza %s (%s)."
                    % (inferenza.get("id"), inferenza.get("descrizione", ""))})
    if nuove:
        scrivi(esistenti + nuove, percorso)
    return nuove


# --- l'allineamento ---------------------------------------------------------------

_ID_VOCE = re.compile(r"^(V\d+)\b")


def allinea(motore, correzione: dict) -> list:
    """Parola per parola: che cosa ha proposto il motore e che cosa e' giusto.

    Il motore ritraduce l'italiano oggi, e non si fida di quello che la pagina
    ha scritto nella riga: se nel frattempo il glossario e' cambiato, conta
    quello che il motore risponde adesso. Le due sequenze di parole si
    allineano per chiave con `difflib`, e ogni pezzo ha un tipo (`TIPI`).
    """
    risposta = motore.traduci(correzione["italiano"], IT_FE)
    proposte = []   # (parola ferrarese proposta, unita' da cui viene)
    for testo, tradotto, origine, _, dettaglio in risposta.per_corrispondenza:
        m = _ID_VOCE.match(dettaglio or "")
        unita = {"italiano": testo, "origine": origine,
                 "voce": m.group(1) if (m and origine == "glossario") else ""}
        for parola in normalizza.tokenizza(tradotto) or [tradotto]:
            proposte.append((parola, unita))
    corrette = normalizza.tokenizza(correzione["ferrarese"])
    a = [normalizza.chiave(p) for p, _ in proposte]
    b = [normalizza.chiave(p) for p in corrette]
    coppie = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            # Uguali per chiave, ma la chiave toglie gli accenti: «càn» e
            # «can» sono la stessa chiave e due grafie, e la differenza e' un
            # dato. Le maiuscole del Ferri («Càn») invece non lo sono.
            for i, j in zip(range(i1, i2), range(j1, j2)):
                uguali = _minuscola(proposte[i][0]) == _minuscola(corrette[j])
                coppie.append(_coppia(proposte[i], corrette[j],
                                      "confermata" if uguali else "forma"))
        elif op == "replace" and (i2 - i1) == (j2 - j1):
            for i, j in zip(range(i1, i2), range(j1, j2)):
                coppie.append(_coppia(proposte[i], corrette[j], None))
        elif op == "replace":
            unita = proposte[i1][1]
            coppie.append({
                "italiano": " ".join(u["italiano"] for _, u in
                                     _uniche(proposte[i1:i2])),
                "proposto": " ".join(p for p, _ in proposte[i1:i2]),
                "corretto": " ".join(corrette[j1:j2]),
                "origine": unita["origine"], "voce": unita["voce"]
                if (i2 - i1) == 1 else "", "tipo": "sostituzione"})
        elif op == "insert":
            coppie.append({"italiano": "", "proposto": "",
                           "corretto": " ".join(corrette[j1:j2]),
                           "origine": "", "voce": "", "tipo": "aggiunta"})
        elif op == "delete":
            for i in range(i1, i2):
                coppia = _coppia(proposte[i], "", "tolta")
                coppie.append(coppia)
    return coppie


def _uniche(proposte):
    viste, uniche = set(), []
    for parola, unita in proposte:
        if id(unita) not in viste:
            viste.add(id(unita))
            uniche.append((parola, unita))
    return uniche


def _coppia(proposta, corretta: str, tipo):
    parola, unita = proposta
    if tipo is None:
        if unita["origine"] == "nessuna":
            tipo = "buco"
        elif normalizza.somiglianza(parola, corretta) >= 0.5:
            tipo = "forma"
        else:
            tipo = "sostituzione"
    return {"italiano": unita["italiano"], "proposto": parola,
            "corretto": corretta, "origine": unita["origine"],
            "voce": unita["voce"], "tipo": tipo}


# --- le regole di grafia ------------------------------------------------------------

def _minuscola(testo: str) -> str:
    return unicodedata.normalize("NFC", (testo or "").lower())


def differenze(vecchia: str, nuova: str) -> list:
    """Le sostituzioni che portano da una forma all'altra, con il contesto.

    Ogni regola e' `{sinistra, vecchio, nuovo, destra}`: una lettera di
    contesto per parte, `^` e `$` per l'inizio e la fine della parola. E' il
    minimo che serve perche' una regola dica qualcosa («la `ŋ` in fine di
    parola») senza dire troppo («ogni `ŋ`»).
    """
    a, b = _minuscola(vecchia), _minuscola(nuova)
    regole = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        regole.append({"sinistra": a[i1 - 1] if i1 > 0 else "^",
                       "vecchio": a[i1:i2], "nuovo": b[j1:j2],
                       "destra": a[i2] if i2 < len(a) else "$"})
    return regole


def _modello(regola: dict):
    sinistra = "^" if regola["sinistra"] == "^" else \
        "(?<=%s)" % re.escape(regola["sinistra"])
    destra = "$" if regola["destra"] == "$" else \
        "(?=%s)" % re.escape(regola["destra"])
    return re.compile(sinistra + re.escape(regola["vecchio"]) + destra)


def applica_regola(forma: str, regola: dict):
    """La forma con la regola applicata, o None se la regola non la tocca."""
    minuscola = _minuscola(forma)
    nuova = _modello(regola).sub(regola["nuovo"], minuscola)
    if nuova == minuscola:
        return None
    if forma[:1].isupper():
        nuova = nuova[:1].upper() + nuova[1:]
    return nuova


def descrivi(regola: dict) -> str:
    dove = {"^": "a inizio parola", "$": "a fine parola"}
    contesto = []
    if regola["sinistra"] == "^":
        contesto.append(dove["^"])
    else:
        contesto.append("dopo «%s»" % regola["sinistra"])
    if regola["destra"] == "$":
        contesto.append(dove["$"])
    else:
        contesto.append("prima di «%s»" % regola["destra"])
    return "«%s» → «%s» %s" % (regola["vecchio"] or "∅",
                               regola["nuovo"] or "∅", ", ".join(contesto))


def famiglia(fonte: str) -> str:
    """La fonte di una voce, ridotta a quello che ne decide la grafia.

    Le voci di S006 portano l'id fra parentesi; quelle del Ferri portano il
    titolo e la pagina. Due voci della stessa famiglia sono scritte con la
    stessa grafia, ed e' fra loro che una regola di grafia si cerca.
    """
    m = re.search(r"\(?(S\d{3})\)?", fonte or "")
    if m:
        return m.group(1)
    return re.split(r",\s*pag\.|\s*\(", fonte or "", 1)[0].strip()


# --- le inferenze ------------------------------------------------------------------

def prove(motore, glossario, correzioni: list, giudizi=None) -> list:
    """Le coppie (forma della fonte, forma del parlante) da cui si inferisce.

    Vengono da due posti: le correzioni non respinte, allineate con il motore,
    e i giudizi della verifica a campione con il campo `come_si_dice` (un
    parlante che dice «si dice, ma si scrive cosi'» ha fatto una correzione di
    grafia). Una coppia uguale e' una **conferma** e serve a contare chi
    smentisce una regola.
    """
    per_id = {v.id: v for v in glossario.voci}
    risultato = []
    for correzione in correzioni:
        if correzione.get("stato") == "respinta":
            continue
        for coppia in allinea(motore, correzione):
            voce = per_id.get(coppia["voce"])
            if voce is None or coppia["tipo"] not in ("forma", "confermata"):
                continue
            risultato.append({"da": correzione["id"], "voce": voce.id,
                              "famiglia": famiglia(voce.fonte),
                              "vecchia": coppia["proposto"],
                              "nuova": coppia["corretto"],
                              "conferma": coppia["tipo"] == "confermata"})
    for giudizio in giudizi or []:
        voce = per_id.get(giudizio.get("voce"))
        if voce is None or giudizio.get("esito") != "si_dice":
            continue
        come = (giudizio.get("come_si_dice") or "").strip()
        uguale = not come or normalizza.chiave(come) == \
            normalizza.chiave(voce.ferrarese)
        risultato.append({"da": giudizio.get("id", ""), "voce": voce.id,
                          "famiglia": famiglia(voce.fonte),
                          "vecchia": voce.ferrarese,
                          "nuova": voce.ferrarese if uguale else come,
                          "conferma": uguale})
    return risultato


def inferisci(motore, glossario, correzioni: list, giudizi=None,
              tutte_le_candidate: bool = False) -> list:
    """Le regole di grafia, con chi le sostiene, chi le smentisce e dove valgono.

    Per ogni regola: `supporto` sono le correzioni che la mostrano, `contro`
    le conferme in cui la regola si sarebbe potuta applicare e il parlante ha
    tenuto la forma com'era. `candidate` sono le voci della stessa fonte che
    la regola cambierebbe, e `esempi` le prime per esteso. Nessuna e'
    applicata: e' il lavoro da proporre a un parlante.
    """
    tutte = prove(motore, glossario, correzioni, giudizi)
    regole = {}
    for prova in tutte:
        if prova["conferma"]:
            continue
        trovate = differenze(prova["vecchia"], prova["nuova"])
        if not trovate or len(trovate) > MASSIMO_REGOLE:
            continue
        for regola in trovate:
            k = (prova["famiglia"], regola["sinistra"], regola["vecchio"],
                 regola["nuovo"], regola["destra"])
            voce = regole.setdefault(k, {"regola": regola,
                                         "famiglia": prova["famiglia"],
                                         "da": [], "attestate": []})
            if prova["da"] not in voce["da"]:
                voce["da"].append(prova["da"])
            voce["attestate"].append({"voce": prova["voce"],
                                      "prima": prova["vecchia"],
                                      "dopo": prova["nuova"]})
    risultato = []
    for numero, k in enumerate(sorted(regole), 1):
        dati = regole[k]
        regola = dati["regola"]
        attestate = {a["voce"] for a in dati["attestate"]}
        contro = sorted({p["da"] for p in tutte if p["conferma"]
                         and p["famiglia"] == dati["famiglia"]
                         and applica_regola(p["vecchia"], regola)})
        candidate = []
        for voce in glossario.voci:
            if voce.id in attestate or famiglia(voce.fonte) != dati["famiglia"]:
                continue
            proposta = applica_regola(voce.ferrarese, regola)
            if proposta:
                candidate.append({"voce": voce.id, "ora": voce.ferrarese,
                                  "proposta": proposta,
                                  "italiano": voce.italiano})
        risultato.append({
            "id": "I%04d" % numero,
            "regola": regola, "descrizione": descrivi(regola),
            "famiglia": dati["famiglia"],
            "da": sorted(dati["da"]), "supporto": len(dati["da"]),
            "contro": contro,
            "attestate": dati["attestate"],
            "candidate": len(candidate), "esempi": candidate[:ESEMPI],
            **({"tutte": candidate} if tutte_le_candidate else {}),
            "stato": "da rivedere",
            "giudizio": _giudizio(len(dati["da"]), len(contro)),
        })
    return risultato


def _giudizio(supporto: int, contro: int) -> str:
    if contro and contro >= supporto:
        return ("smentita quanto e' sostenuta: e' probabilmente una parola, "
                "non una regola della grafia")
    if supporto == 1:
        return ("una sola correzione: e' un indizio, da far confermare a un "
                "parlante su qualche voce candidata prima di crederci")
    return ("%d correzioni la sostengono%s: e' un buon candidato, ma ogni voce "
            "va confermata" % (supporto, " e %d la smentiscono" % contro
                               if contro else ""))


# --- l'applicazione ------------------------------------------------------------

def _leggi_jsonl(percorso: str) -> list:
    righe = []
    if os.path.exists(percorso):
        with io.open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = riga.strip()
                if riga and not riga.startswith("//"):
                    righe.append(json.loads(riga))
    return righe


def _prossimo(righe: list, prefisso: str) -> int:
    numeri = [int(r["id"][1:]) for r in righe
              if re.match(r"^%s\d+$" % prefisso, r.get("id") or "")]
    return max(numeri or [0]) + 1


def _appendi(percorso: str, riga: dict) -> None:
    with io.open(percorso, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")


def fonte_di(correzione: dict) -> str:
    luogo = (" di %s" % correzione["luogo"]) if correzione.get("luogo") else ""
    return ("correzione %s: %s%s, parlante del ferrarese %s, %s"
            % (correzione["id"], correzione["chi"], luogo,
               correzione["varieta"], correzione["data"]))


def applica(motore, correzione: dict, percorsi: dict,
            anche_buchi: bool = False) -> list:
    """Scrive i dati che la correzione documenta, e dice quali righe ha creato.

    - la frase intera, se l'italiano ha piu' di una parola: una coppia `D` in
      `coppie.jsonl`, cosi' la prossima volta il motore trova la frase gemella;
    - ogni parola che il parlante ha corretto (tipo `forma` o `sostituzione`,
      una parola italiana per una ferrarese): una voce `D` del glossario, con
      `corregge` che punta alla voce sbagliata. La voce sbagliata **non si
      cancella**: e' quello che la fonte scrive, ed e' un fatto anche quando e'
      sbagliato;
    - le parole che il motore **non sapeva** (tipo `buco`) restano nella frase
      e non diventano voci, a meno di `anche_buchi`: sono quasi sempre parole
      funzionali («il» → `al`), su cui `AGENTS.md` §6 punto 8 lascia aperta la
      decisione, e una voce «il → al» da sola sbaglierebbe davanti a vocale;
    - la pronuncia fra quadre, se c'e': una trascrizione `D` in
      `fonetica.jsonl`, riferita alla coppia o alla voce nuova.

    `percorsi` ha `glossario`, `coppie` e `fonetica`. La correzione stessa la
    aggiorna chi chiama, con lo stato e l'elenco delle righe create.
    """
    fonte = fonte_di(correzione)
    create = []
    voci = _leggi_jsonl(percorsi["glossario"])
    per_id = {v["id"]: v for v in voci}
    numero_voce = _prossimo(voci, "V")
    riferimento = ""
    parole_italiane = normalizza.tokenizza(correzione["italiano"])
    if len(parole_italiane) > 1 and not correzione.get("voce"):
        coppie = _leggi_jsonl(percorsi["coppie"])
        nuova = {"id": "F%04d" % _prossimo(coppie, "F"),
                 "varieta": correzione["varieta"],
                 "italiano": correzione["italiano"].strip(),
                 "ferrarese": correzione["ferrarese"].strip(),
                 "tipo": "conversazione", "fonte": fonte,
                 "nota": "Frase corretta da un parlante." + (
                     " Il traduttore proponeva «%s»." % correzione["proposta"]
                     if correzione.get("proposta") else ""),
                 "attendibilita": "D", "ricorrenze": 1}
        _appendi(percorsi["coppie"], nuova)
        create.append(nuova["id"])
        riferimento = nuova["id"]
    if correzione.get("voce"):
        # Una correzione di una voce precisa (una conferma di un'inferenza):
        # non si ritraduce niente, si corregge quella voce.
        vecchia = per_id.get(correzione["voce"])
        coppie_da_scrivere = [{
            "tipo": "forma", "italiano": correzione["italiano"],
            "proposto": (vecchia or {}).get("ferrarese", ""),
            "corretto": correzione["ferrarese"].strip(),
            "voce": correzione["voce"]}]
    else:
        coppie_da_scrivere = allinea(motore, correzione)
    for coppia in coppie_da_scrivere:
        tipi = ("forma", "sostituzione", "buco") if anche_buchi else \
            ("forma", "sostituzione")
        if coppia["tipo"] not in tipi:
            continue
        if not coppia["italiano"]:
            continue
        # Una locuzione («a brazz avèrti») e' una voce sola solo quando la
        # correzione e' di quella voce; in una frase, piu' parole ferraresi per
        # una italiana sono un allineamento che il programma non sa fare.
        if " " in coppia["corretto"] and not correzione.get("voce"):
            continue
        vecchia = per_id.get(coppia["voce"])
        nuova = {"id": "V%04d" % numero_voce,
                 "ferrarese": coppia["corretto"],
                 "italiano": coppia["italiano"],
                 "campo": (vecchia or {}).get("campo", ""),
                 "varieta": correzione["varieta"],
                 "note": "Correzione di un parlante: il traduttore proponeva "
                         "«%s»." % coppia["proposto"],
                 "fonte": fonte, "attendibilita": "D",
                 "da_verificare": False}
        if vecchia is not None:
            nuova["corregge"] = vecchia["id"]
            if correzione.get("voce") and vecchia.get("principale_italiano"):
                nuova["principale_italiano"] = vecchia["principale_italiano"]
        numero_voce += 1
        _appendi(percorsi["glossario"], nuova)
        create.append(nuova["id"])
        if not riferimento:
            riferimento = nuova["id"]
    ipa = (correzione.get("ipa") or "").strip()
    if ipa and riferimento:
        trascrizioni = _leggi_jsonl(percorsi["fonetica"])
        nuova = {"id": "T%04d" % _prossimo(trascrizioni, "T"),
                 "riferimento": riferimento,
                 "forma": correzione["ferrarese"].strip(),
                 "ipa": ipa, "varieta": correzione["varieta"],
                 "fonte": fonte, "attendibilita": "D",
                 "nota": "Pronuncia ascoltata, scritta fra quadre da chi ha "
                         "corretto: e' un ascolto, non una lettura della "
                         "grafia.",
                 "da_verificare": False}
        _appendi(percorsi["fonetica"], nuova)
        create.append(nuova["id"])
    return create


# --- la promozione: quando una correzione entra nel traduttore -----------------
#
# Dal 0.40 una correzione entra **archiviata e da verificare**, e il traduttore
# non la usa. Ne usa gli **elementi** quando hanno un margine: abbastanza
# correzioni concordi e nessuna contraria. Gli elementi sono tre:
#
# - `parola`: una parola italiana che il parlante traduce diversamente dal
#   glossario («casa» → `ca`). Promossa, e' una voce `D` che corregge la voce
#   sbagliata;
# - `funzionale`: una parola che il glossario non aveva («il» → `al`), con il
#   suo contesto — davanti a vocale, a consonante, in fine di frase — perche'
#   «il» e' `al` davanti a consonante e `l'` davanti a vocale. Promossa, e' una
#   **regola di frase** in `dati/regole_frase.json`, che il motore applica
#   guardando la parola che segue;
# - `grafia`: una regola dell'inferenza («`ŋ` → `n` dopo `a`, prima di `d`»).
#   Promossa, cambia le voci candidate della stessa fonte, ma le nuove voci
#   restano `I` e `da_verificare`: sono la regola applicata, non un ascolto.
#
# Le soglie sono in `dati/correzioni/soglie.json`. Una correzione confermata a
# mano (`conferma_correzione`) passa senza soglia: chi conferma e' il margine.

PERCORSO_SOGLIE = os.path.join(CARTELLA, "soglie.json")
PERCORSO_REGOLE_FRASE = os.path.join(RADICE, "dati", "regole_frase.json")
SOGLIE_PREDEFINITE = {"parola": 2, "funzionale": 2, "grafia": 3}
VOCALI = "aeiouàèéìíòóùúh"


def soglie(percorso: str = PERCORSO_SOGLIE) -> dict:
    valori = dict(SOGLIE_PREDEFINITE)
    if os.path.exists(percorso):
        with io.open(percorso, encoding="utf-8") as f:
            valori.update({k: int(v) for k, v in json.load(f).items()
                           if k in SOGLIE_PREDEFINITE})
    return valori


def contesto(seguente: str) -> str:
    """Davanti a che cosa sta una parola: `vocale`, `consonante` o `fine`.

    E' la stessa funzione di `frase.contesto` e di `contestoDi` nella pagina:
    guarda la prima lettera della parola **italiana** che segue, perche' quando
    il motore decide la parola ferrarese che segue non c'e' ancora. La «h» conta
    come vocale: «hanno», «ho» cominciano con un suono vocalico.
    """
    testo = _minuscola(seguente or "").strip()
    if not testo:
        return "fine"
    return "vocale" if testo[0] in VOCALI else "consonante"


def elementi(motore, correzione: dict) -> list:
    """Gli elementi di una correzione, con la chiave che li confronta."""
    coppie = allinea(motore, correzione)
    risultato = []
    for i, c in enumerate(coppie):
        italiano = (c["italiano"] or "").strip()
        if not italiano or " " in italiano:
            continue
        if c["tipo"] in ("forma", "sostituzione"):
            gruppo = "parola|" + chiave_italiano(italiano)
            risultato.append({"tipo": "parola", "gruppo": gruppo,
                              "italiano": italiano,
                              "ferrarese": c["corretto"],
                              "proposto": c["proposto"], "voce": c["voce"]})
        elif c["tipo"] == "buco":
            seguente = next((d["italiano"] for d in coppie[i + 1:]
                             if d["italiano"] and d["italiano"] != italiano),
                            "")
            ctx = contesto(seguente.split(" ")[0] if seguente else "")
            gruppo = "funzionale|%s|%s" % (chiave_italiano(italiano), ctx)
            risultato.append({"tipo": "funzionale", "gruppo": gruppo,
                              "italiano": _minuscola(italiano),
                              "contesto": ctx, "ferrarese": c["corretto"]})
        elif c["tipo"] == "confermata":
            risultato.append({"tipo": "conferma",
                              "gruppo": "parola|" + chiave_italiano(italiano),
                              "italiano": italiano,
                              "ferrarese": c["corretto"]})
    for e in risultato:
        e["elemento"] = "%s|%s" % (e["gruppo"], _minuscola(e["ferrarese"]))
    return risultato


def chiave_italiano(parola: str) -> str:
    """La parola italiana come chiave, con l'accento (come `verbi`)."""
    from .verbi import chiave_italiano as chiave
    return chiave(parola)


def valuta(motore, correzioni: list, soglie_usate: dict = None) -> dict:
    """Per ogni elemento: chi lo sostiene, chi lo smentisce, se e' pronto.

    Una correzione **sostiene** un elemento se lo contiene; lo **smentisce** se
    per la stessa parola (e lo stesso contesto) scrive un'altra forma, o se la
    conferma com'era. Un elemento e' pronto quando i sostenitori arrivano alla
    soglia e nessuno lo smentisce, oppure quando una delle sue correzioni e'
    stata confermata a mano.
    """
    soglie_usate = soglie_usate or SOGLIE_PREDEFINITE
    per_gruppo, per_elemento = {}, {}
    for correzione in correzioni:
        if correzione.get("stato") == "respinta":
            continue
        for e in elementi(motore, correzione):
            per_gruppo.setdefault(e["gruppo"], []).append(
                (correzione["id"], e))
            if e["tipo"] == "conferma":
                continue
            dati = per_elemento.setdefault(e["elemento"], {
                "elemento": e, "da": [], "contro": [], "confermata": False})
            if correzione["id"] not in dati["da"]:
                dati["da"].append(correzione["id"])
            if correzione.get("confermata"):
                dati["confermata"] = True
    for chiave, dati in per_elemento.items():
        gruppo = dati["elemento"]["gruppo"]
        forma = _minuscola(dati["elemento"]["ferrarese"])
        dati["contro"] = sorted({cid for cid, e in per_gruppo.get(gruppo, [])
                                 if _minuscola(e["ferrarese"]) != forma
                                 and cid not in dati["da"]})
        soglia = soglie_usate.get(dati["elemento"]["tipo"], 2)
        dati["pronto"] = dati["confermata"] or (
            len(dati["da"]) >= soglia and not dati["contro"])
    return per_elemento


def leggi_regole_frase(percorso: str = PERCORSO_REGOLE_FRASE) -> dict:
    if not os.path.exists(percorso):
        return {"_nota": "", "regole": []}
    with io.open(percorso, encoding="utf-8") as f:
        return json.load(f)


def _scrivi_regole_frase(dati: dict, percorso: str) -> None:
    dati["_nota"] = (
        "Le regole di frase: una parola funzionale italiana e la sua resa "
        "ferrarese davanti a vocale, a consonante o in fine di frase. File "
        "scritto da `correzioni promuovi`, mai a mano: ogni regola viene da "
        "correzioni di parlanti che la sostengono e che nessuna smentisce. "
        "Vedi dati/correzioni/README.md.")
    dati["regole"].sort(key=lambda r: (r["italiano"], r["contesto"]))
    with io.open(percorso, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)
        f.write("\n")


def promuovi(motore, correzioni: list, percorsi: dict, oggi: str,
             soglie_usate: dict = None, glossario=None) -> dict:
    """Porta nel traduttore gli elementi pronti, e le correzioni complete.

    Scrive: le voci `D` delle parole pronte, le regole di frase pronte, le voci
    `I` delle regole di grafia pronte, e per ogni correzione i cui elementi
    sono tutti nel traduttore (o confermata a mano) la frase intera e la
    pronuncia. Non scrive mai due volte la stessa cosa: ogni riga scritta
    porta il suo `elemento`. Le correzioni cambiate le aggiorna nella lista;
    salvarle e' di chi chiama.
    """
    soglie_usate = soglie_usate or SOGLIE_PREDEFINITE
    valutati = valuta(motore, correzioni, soglie_usate)
    voci = _leggi_jsonl(percorsi["glossario"])
    gia = {v.get("elemento") for v in voci if v.get("elemento")}
    per_id = {v["id"]: v for v in voci}
    regole = leggi_regole_frase(percorsi["regole_frase"])
    gia |= {r.get("elemento") for r in regole["regole"]}
    numero = _prossimo(voci, "V")
    fatto = {"parole": [], "regole_frase": [], "grafia": [], "correzioni": []}
    per_correzione = {c["id"]: c for c in correzioni}

    def fonte_elemento(ids):
        chi = sorted({per_correzione[i].get("chi", "") for i in ids})
        return ("correzioni %s (%s), %d concordi e nessuna contraria"
                % (", ".join(ids), ", ".join(chi), len(ids)))

    for chiave, dati in sorted(valutati.items()):
        e = dati["elemento"]
        if not dati["pronto"] or chiave in gia:
            continue
        prima = per_correzione[dati["da"][0]]
        if e["tipo"] == "parola":
            vecchia = per_id.get(e["voce"])
            nuova = {"id": "V%04d" % numero, "ferrarese": e["ferrarese"],
                     "italiano": e["italiano"],
                     "campo": (vecchia or {}).get("campo", ""),
                     "varieta": prima["varieta"],
                     "note": "Correzione di un parlante: il traduttore "
                             "proponeva «%s»." % e["proposto"],
                     "fonte": fonte_elemento(dati["da"]),
                     "attendibilita": "D", "da_verificare": False,
                     "elemento": chiave, "da_correzioni": dati["da"]}
            if vecchia is not None:
                nuova["corregge"] = vecchia["id"]
            numero += 1
            _appendi(percorsi["glossario"], nuova)
            fatto["parole"].append(nuova["id"])
        elif e["tipo"] == "funzionale":
            regole["regole"].append({
                "italiano": e["italiano"], "contesto": e["contesto"],
                "ferrarese": e["ferrarese"], "varieta": prima["varieta"],
                "fonte": fonte_elemento(dati["da"]), "da": dati["da"],
                "elemento": chiave, "data": oggi})
            fatto["regole_frase"].append(chiave)
        gia.add(chiave)
    if fatto["regole_frase"]:
        _scrivi_regole_frase(regole, percorsi["regole_frase"])

    # Le regole di grafia, dalle inferenze con il loro margine.
    if glossario is not None:
        for inferenza in inferisci(motore, glossario, correzioni,
                                   tutte_le_candidate=True):
            if inferenza["supporto"] < soglie_usate["grafia"] or \
                    inferenza["contro"]:
                continue
            for esempio in inferenza["tutte"]:
                chiave = "grafia|%s|%s|%s" % (inferenza["famiglia"],
                                              inferenza["descrizione"],
                                              esempio["voce"])
                if chiave in gia:
                    continue
                vecchia = per_id.get(esempio["voce"]) or {}
                nuova = {"id": "V%04d" % numero,
                         "ferrarese": esempio["proposta"],
                         "italiano": esempio["italiano"],
                         "campo": vecchia.get("campo", ""),
                         "varieta": vecchia.get("varieta", "cittadino"),
                         "note": "Regola di grafia applicata alla voce %s: %s."
                                 % (esempio["voce"], inferenza["descrizione"]),
                         "fonte": "regola di grafia ricavata dalle " +
                                  fonte_elemento(inferenza["da"]),
                         "attendibilita": "I", "da_verificare": True,
                         "corregge": esempio["voce"], "elemento": chiave,
                         "da_correzioni": inferenza["da"]}
                numero += 1
                _appendi(percorsi["glossario"], nuova)
                gia.add(chiave)
                fatto["grafia"].append(nuova["id"])

    # Le correzioni complete: la frase intera e la pronuncia.
    for correzione in correzioni:
        if correzione.get("stato") != "da_verificare":
            continue
        propri = [e for e in elementi(motore, correzione)
                  if e["tipo"] != "conferma"]
        if not correzione.get("confermata") and (
                not propri or any(e["elemento"] not in gia for e in propri)):
            continue
        create = _frase_e_pronuncia(correzione, percorsi, voci_nuove=[
            v for v in _leggi_jsonl(percorsi["glossario"])
            if correzione["id"] in (v.get("da_correzioni") or [])])
        correzione["stato"] = "applicata"
        correzione["da_verificare"] = False
        correzione["applicata_il"] = oggi
        correzione["crea"] = create + [
            v["id"] for v in _leggi_jsonl(percorsi["glossario"])
            if correzione["id"] in (v.get("da_correzioni") or [])]
        fatto["correzioni"].append(correzione["id"])
    return fatto


def _frase_e_pronuncia(correzione: dict, percorsi: dict,
                       voci_nuove: list) -> list:
    fonte = fonte_di(correzione)
    create, riferimento = [], ""
    if len(normalizza.tokenizza(correzione["italiano"])) > 1:
        coppie = _leggi_jsonl(percorsi["coppie"])
        nuova = {"id": "F%04d" % _prossimo(coppie, "F"),
                 "varieta": correzione["varieta"],
                 "italiano": correzione["italiano"].strip(),
                 "ferrarese": correzione["ferrarese"].strip(),
                 "tipo": "conversazione", "fonte": fonte,
                 "nota": "Frase corretta da un parlante." + (
                     " Il traduttore proponeva «%s»." % correzione["proposta"]
                     if correzione.get("proposta") else ""),
                 "attendibilita": "D", "ricorrenze": 1}
        _appendi(percorsi["coppie"], nuova)
        create.append(nuova["id"])
        riferimento = nuova["id"]
    elif voci_nuove:
        riferimento = voci_nuove[0]["id"]
    ipa = (correzione.get("ipa") or "").strip()
    if ipa and riferimento:
        trascrizioni = _leggi_jsonl(percorsi["fonetica"])
        nuova = {"id": "T%04d" % _prossimo(trascrizioni, "T"),
                 "riferimento": riferimento,
                 "forma": correzione["ferrarese"].strip(), "ipa": ipa,
                 "varieta": correzione["varieta"], "fonte": fonte,
                 "attendibilita": "D",
                 "nota": "Pronuncia ascoltata, scritta fra quadre da chi ha "
                         "corretto: e' un ascolto, non una lettura della "
                         "grafia.",
                 "da_verificare": False}
        _appendi(percorsi["fonetica"], nuova)
        create.append(nuova["id"])
    return create
