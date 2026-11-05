# -*- coding: utf-8 -*-
"""Una grafia sola: le forme di Bigoni scritte all'italiana, e il suono in IPA.

**Il problema.** Il vocabolario di Bigoni (S006) e le sue note (S015) scrivono
il ferrarese con un alfabeto fonetico suo, un segno per ogni suono (`kaŋtàr`,
`aɣóst`, `abitazjóŋ`); il Ferri, Musacchi e le altre fonti scrivono
all'italiana (`Biànch`, `Làgh`, `Abitazion`). Nella stessa frase tradotta
convivevano le due scritture.

**La scelta (0.42, decisa da chi usa il sito).** Si scrive tutto
all'italiana, come scrive il Ferri; la precisione di Bigoni non si butta: passa
nella trascrizione IPA, che un segno per suono lo ha. Cosi':

- la forma che si legge e' `bianch`, `agóst`, `abitazión`;
- la forma della fonte resta nella voce (`grafia_fonte`) e si puo' cercare;
- la pronuncia `/ˈbjaŋk/` si ricava dalla forma della fonte con una tabella
  dichiarata, ed e' `I` e da verificare come ogni lettura di una grafia.

**Il file di dati non cambia.** `dati/glossario.jsonl` scrive quello che la
fonte scrive; la conversione si fa quando il glossario si legge
(`glossario._voce_da_dict`), e quindi vale uguale nel motore, nella pagina e
nelle fette del glossario. Le regole sono in `dati/conversione_bigoni.json`, e
gli esempi di quel file sono controllati dai test.

**Le regole di contesto**, quelle che una tabella lettera per lettera non
poteva dire:

- `k` e `ɣ` (c e g dure) davanti a e, i, j si scrivono `ch`, `gh`; in fondo alla
  parola anche, come il Ferri scrive `Biànch` e `Làgh`;
- `c` e `g` (c e g dolci) davanti ad a, o, u si scrivono `ci`, `gi`;
- la `j` fra una consonante e una vocale si scrive `i` (`abitazjóŋ` →
  `abitazión`), come il Ferri; all'inizio, fra due vocali e in fondo resta `j`;
- le vocali atone aperte o chiuse (`ě`, `ê`, `ǒ`, `ô`) si scrivono senza
  accento: l'accento nella grafia all'italiana dice dove cade la voce, e su una
  sillaba atona direbbe una cosa falsa. Il timbro resta nell'IPA;
- `s` seguita dalla `c` dolce si scrive `s'c` (`scaf` → `s'ciaf`), perche'
  `sci` all'italiana si leggerebbe come in «scena»;
- `š` e `ž` (s e z sonore) si scrivono `s` e `z`; `ŋ` si scrive `n`; `ñ` `gn`;
  `ʎ` `gli`. La sonorita' e la nasale velare restano nell'IPA.

**La maiuscola del lemma.** Il Ferri e Musacchi scrivono ogni lemma con la
maiuscola, che e' una convenzione tipografica del vocabolario e non della
parola: nella frase tradotta usciva `i Càn`. La maiuscola si toglie, salvo
quando la voce e' un nome proprio secondo Bigoni (che scrive minuscolo e mette
la maiuscola solo ai nomi propri). Un nome proprio che Bigoni non ha perde la
maiuscola: e' un limite dichiarato.

La copia nella pagina e' in `modello.html` (`daBigoni`, `ipaDaBigoni`) ed e'
confrontata su tutte le voci di S006 da `prove/controlla_equivalenza.py`.
"""
from __future__ import annotations

import re
import unicodedata

# L'identificativo che dice che una voce e' scritta nell'alfabeto di Bigoni.
FONTI_BIGONI = ("(S006)",)
# Le fonti che scrivono il lemma con la maiuscola tipografica.
FONTI_LEMMA_MAIUSCOLO = ("Luigi Ferri", "Maurizio Musacchi")

# Le vocali, e quelle davanti a cui c e g si leggono dolci in italiano.
VOCALI = "aeiouàèéìíòóùúáěêǒô"
ANTERIORI = "eiéèìíěêj"
POSTERIORI = "aouàòóùúáǒô"
# Le atone di Bigoni, che nella grafia all'italiana perdono l'accento.
ATONE = {"ě": "e", "ê": "e", "ǒ": "o", "ô": "o"}
# La «λ» che compare due volte in S006 e' la «ʎ» della sua tabella.
REFUSI = {"λ": "ʎ", "á": "à", "í": "ì"}
SEMPLICI = {"ŋ": "n", "š": "s", "ž": "z", "ñ": "gn"}


def _minuscola(c: str) -> str:
    return c.lower()


def _maiuscola_come(originale: str, resa: str) -> str:
    if originale[:1].isupper() and resa:
        return resa[:1].upper() + resa[1:]
    return resa


def _parola(p: str) -> str:
    """Una parola di Bigoni, senza spazi, nella grafia all'italiana."""
    s = "".join(REFUSI.get(c, c) for c in p)
    fuori = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        b = c.lower()
        dopo = s[i + 1].lower() if i + 1 < n else ""
        prima = s[i - 1].lower() if i > 0 else ""
        if b == "k" or b == "ɣ":
            lettera = "c" if b == "k" else "g"
            if dopo == "" or dopo in ANTERIORI or dopo == "'":
                lettera += "h"
            fuori.append(_maiuscola_come(c, lettera))
        elif b == "c" or b == "g":
            # «s» + «c» dolce: «sci» in italiano si leggerebbe /ʃ/, e la
            # grafia emiliana scrive «s'c» («scaf» di Bigoni → «s'ciaf»).
            stacco = "'" if (b == "c" and prima == "s") else ""
            if dopo and dopo in POSTERIORI:
                fuori.append(stacco + _maiuscola_come(c, b + "i"))
            else:
                fuori.append(stacco + c)
        elif b == "ʎ":
            # «ʎj» e «ʎi»: la i c'e' gia'.
            fuori.append("gl" if dopo in ("i", "ì") else "gli")
        elif b == "j":
            if prima and prima not in VOCALI and prima != "'" and \
                    dopo and dopo in VOCALI:
                # dopo «gli» e «gn» il suono palatale e' gia' scritto
                if not "".join(fuori).endswith(("gli", "gn")):
                    fuori.append("i")
            else:
                fuori.append(c)
        elif b in ATONE:
            fuori.append(_maiuscola_come(c, ATONE[b]))
        elif b in SEMPLICI:
            fuori.append(_maiuscola_come(c, SEMPLICI[b]))
        else:
            fuori.append(c)
        i += 1
    return "".join(fuori)


def da_bigoni(forma: str) -> str:
    """La forma di Bigoni nella grafia all'italiana del progetto."""
    forma = unicodedata.normalize("NFC", forma or "")
    forma = forma.replace("[", "").replace("]", "")
    pezzi = re.split(r"([\s,/;()'’.-]+)", forma)
    # L'apostrofo resta attaccato alla parola che lo precede («ɣ'è»): e' nei
    # separatori, quindi si guarda la lettera dopo il pezzo.
    fuori = []
    for k, pezzo in enumerate(pezzi):
        if k % 2 == 1 or not pezzo:
            fuori.append(pezzo)
            continue
        seguente = pezzi[k + 1] if k + 1 < len(pezzi) else ""
        if seguente[:1] in ("'", "’") and pezzo[-1:].lower() in ("k", "ɣ"):
            fuori.append(_parola(pezzo + "'")[:-1])
        else:
            fuori.append(_parola(pezzo))
    return unicodedata.normalize("NFC", "".join(fuori))


def facoltative(forma: str) -> list:
    """Le forme senza le parti che Bigoni mette fra parentesi quadre."""
    if "[" not in (forma or ""):
        return []
    corta = re.sub(r"\[[^\]]*\]", "", forma)
    return [corta] if corta.strip() and corta != forma else []


def e_di_bigoni(fonte: str) -> bool:
    return any(s in (fonte or "") for s in FONTI_BIGONI)


def lemma_maiuscolo(fonte: str) -> bool:
    return any((fonte or "").startswith(s) for s in FONTI_LEMMA_MAIUSCOLO)


def senza_maiuscola(testo: str) -> str:
    """Toglie la maiuscola iniziale, se non e' una sigla («ABC»)."""
    if len(testo) > 1 and testo[0].isupper() and not testo[1].isupper():
        return testo[0].lower() + testo[1:]
    return testo


# --- la giunzione: radice e desinenza ---------------------------------------
#
# All'italiana la stessa consonante si scrive in due modi secondo la vocale che
# segue: `amìga` ma `amìghi`, `zarcàr` ma `nu a zarchén`. Quando il motore
# attacca una desinenza a una radice (un plurale, una forma per analogia) la
# grafia della radice va rifatta, e il suono si riconosce dalla parola intera.

def giunta(radice: str, seguito: str, desinenza: str) -> str:
    """`radice` + `desinenza`, con la c e la g scritte per il suono giusto.

    `seguito` e' quello che veniva dopo la radice nella parola da cui e' stata
    presa (`à r` di `zarcàr`, `a` di `amìga`, niente in `vèc`): dice se la c o
    la g finale e' dura o dolce.
    """
    basso = radice.lower()
    dopo = seguito[:1].lower()
    # (Una stringa vuota e' «dentro» ogni stringa: `dopo` si guarda prima.)
    posteriore = bool(dopo) and dopo in POSTERIORI
    duro = None
    nucleo = radice
    if basso.endswith(("ch", "gh")):
        duro, nucleo = True, radice[:-1]
    elif basso.endswith(("ci", "gi")) and posteriore:
        duro, nucleo = False, radice[:-1]
    elif basso.endswith(("c", "g")):
        duro = posteriore
    if duro is None:
        return radice + desinenza
    inizio = desinenza[:1].lower()
    if duro and (not desinenza or inizio in ANTERIORI):
        return nucleo + "h" + desinenza
    if not duro and inizio and inizio in POSTERIORI:
        return nucleo + "i" + desinenza
    return nucleo + desinenza


# --- la pronuncia ------------------------------------------------------------
#
# L'alfabeto di Bigoni ha un segno per suono, quindi l'IPA si legge segno per
# segno. Le scelte sono quelle della sua tabella (S015, «Fonetica») e sono in
# `dati/conversione_bigoni.json` alla voce `ipa`.

IPA = {
    "a": "a", "à": "a", "á": "a", "è": "ɛ", "é": "e", "ě": "ɛ", "ê": "e",
    "e": "e", "ì": "i", "í": "i", "i": "i", "ò": "ɔ", "ó": "o", "ǒ": "ɔ",
    "ô": "o", "o": "o", "ù": "u", "ú": "u", "u": "u",
    "b": "b", "d": "d", "f": "f", "l": "l", "m": "m", "n": "n", "p": "p",
    "r": "r", "t": "t", "v": "v", "k": "k", "c": "tʃ", "ɣ": "g", "g": "dʒ",
    "j": "j", "ʎ": "ʎ", "λ": "ʎ", "ŋ": "ŋ", "ñ": "ɲ", "s": "s", "š": "z",
    "z": "ts", "ž": "dz", "q": "k", "x": "ks", "h": "",
}
TONICHE = "àèéìíòóùúá"
# Le coppie che stanno insieme all'inizio di una sillaba: occlusiva o f/v
# seguita da r, l, j; e qualunque consonante seguita da j.
LIQUIDE = ("r", "l", "j", "w")
OSTRUENTI = set("bdfgkptvcɣq")


def ipa_da_bigoni(forma: str) -> str:
    """La trascrizione IPA di una forma di Bigoni, fra barre.

    L'accento tonico va dove Bigoni scrive la vocale accentata, all'inizio
    della sua sillaba; se la fonte non scrive l'accento (le parole di una
    sillaba, e poche altre) la trascrizione non lo mette. Una forma con piu'
    parole si trascrive parola per parola.
    """
    forma = unicodedata.normalize("NFC", (forma or "").lower())
    forma = forma.replace("[", "").replace("]", "")
    # Le alternative («abitùdaŋ / abitùdiŋ»): si trascrive la prima.
    forma = re.split(r"\s*[,/;]\s*", forma.strip())[0]
    # L'apostrofo lega due pezzi di una parola sola («ɣ'è» si dice /gɛ/).
    parole = [p.replace("'", "").replace("’", "")
              for p in forma.split() if p.strip("'’")]
    return "/" + " ".join(_ipa_parola(p) for p in parole) + "/"


def _ipa_parola(parola: str) -> str:
    segni = []          # (ipa, e' vocale, e' tonica)
    lettere = [c for c in parola if c in IPA or c in "ʎλ"]
    i = 0
    while i < len(lettere):
        c = lettere[i]
        if c == "q" and i + 1 < len(lettere) and lettere[i + 1] == "u":
            segni.append(("k", False, False))
            segni.append(("w", False, False))
            i += 2
            continue
        suono = IPA.get(c, "")
        # La u atona fra una consonante e una vocale e' una semivocale,
        # come nell'italiano «cuoco»: /w/.
        if c == "u" and segni and not segni[-1][1] and \
                i + 1 < len(lettere) and lettere[i + 1] in VOCALI:
            segni.append(("w", False, False))
            i += 1
            continue
        if suono:
            segni.append((suono, c in VOCALI, c in TONICHE))
        i += 1
    if not any(t for _, _, t in segni):
        return "".join(s for s, _, _ in segni)
    posizione = max(k for k, (_, _, t) in enumerate(segni) if t)
    inizio = posizione
    consonanti = []
    k = posizione - 1
    while k >= 0 and not segni[k][1]:
        consonanti.append(k)
        k -= 1
    if consonanti:
        if k < 0:
            inizio = consonanti[-1]           # inizio di parola: tutte
        else:
            inizio = consonanti[0]            # l'ultima consonante
            if len(consonanti) >= 2:
                ultima = segni[consonanti[0]][0]
                penultima = segni[consonanti[1]][0]
                if ultima in LIQUIDE and (penultima[:1] in OSTRUENTI or
                                          ultima in ("j", "w")):
                    inizio = consonanti[1]
                    if ultima in ("j", "w") and len(consonanti) >= 3 and \
                            segni[consonanti[1]][0] in ("r", "l") and \
                            segni[consonanti[2]][0][:1] in OSTRUENTI:
                        inizio = consonanti[2]
    testo = ""
    for k, (s, _, _) in enumerate(segni):
        if k == inizio:
            testo += "ˈ"
        testo += s
    return testo
