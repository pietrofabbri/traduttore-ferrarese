"""L'analisi grammaticale dell'italiano, che viene **prima** della traduzione.

Il motore, fino a adesso, ha lavorato **sulla parola**: una regola imparata dal
corpus dice «questa desinenza si scrive cosi'» e la applica a qualunque parola
finisca in quella desinenza. Il difetto e' che una desinenza non appartiene a
una sola classe. `-are` chiude un infinito (`cantare`), ma anche un nome
dall'azione (`il mangiare`), e una parola come `capitare` puo' essere un verbo
o un nome a seconda della frase. Riscrivere per somiglianza, senza sapere che
cos'e' la parola, e' esattamente il pattern matching che questo progetto non
vuole: una regola che applicata alla parola sbagliata produce una parola che
sembra giusta e non lo e'.

Quindi qui la domanda e' una sola, e ha una risposta sola: **che cos'e' questa
parola in italiano**. La risposta porta con se' tre cose che non si possono
inventare — la **classe** (`nome`, `verbo`, `aggettivo`, `pronome`, ...), la
**fonte** che lo dice, e se quel giudizio e' documentato o interpretato. Dove
la fonte non c'e', la risposta e' `ignota`, e `ignota` non e' una classe che
fa funzionare qualcosa: e' la parola «non so», e chi chiama questo modulo ha
l'obbligo di dirlo.

**Le fonti, in quest'ordine, e perche' in quest'ordine.**

1. `dati/italiano.jsonl` — l'analisi dal corpus annotato italiano di Universal
   Dependencies, scelto perche' annota parole **in frasi** e non di parola
   isolata, e perche' nella release 2.16 il treebank italiano e' **ParlaMint**,
   cioe' trascrizioni di parlato parlamentare: un italiano che qualcuno ha
   **detto**, che e' la sola lingua che questo progetto considera. Sono **1072
   analisi**, raccolte dalla release r2.16. Il raccoglitore e'
   `raccolta/italiano.py`; i file del treebank non li scarica il progetto, li
   scarica qualcuno e li dichiara.
2. `campo` del glossario — la classificazione che ogni voce porta gia' con se',
   con la fonte della voce accanto. Copre 2946 voci su 17370: e' un terzo, e il
   terzo e' dichiarato, non aggregato con gli altri due terzi.
3. `dati/verbi.jsonl` — il lemma di un verbo e' un infinito per definizione
   dichiarata, non per supposizione.

**Il buco e' la parte importante di questo modulo.** 13022 voci su 17370 non
hanno nessuna di queste tre fonti, e su quelle parole il progetto non sa che
cosa siano. Il numero e' stampato e contato (`Italiano.copertura`), e il
comando `italiano` lo mostra: un buco che non ha numero smette di essere un
buco e diventa uno spazio vuoto in cui si puo' infilare una parola con la
sostanza sbagliata.
"""
from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, field

from . import normalizza

# Le classi del progetto. Sono poche, sono quelle che il glossario dichiara
# gia' in `campo`, e sono volutamente larghe: qui non si decide se una parola
# e' un singolare o un plurale, si decide **che cos'e'**, e le due domande non
# si confondono.
NOMINALE = "nominale"
VERBO = "verbo"
PARTICIPIO = "participio"
AGGETTIVO = "aggettivo"
AVVERBIO = "avverbio"
PRONOME = "pronome"
CONGIUNZIONE = "congiunzione"
PREPOSIZIONE = "preposizione"
LOCUZIONE = "locuzione"
IGNOTA = "ignota"

TUTTE = (NOMINALE, VERBO, PARTICIPIO, AGGETTIVO, AVVERBIO, PRONOME,
         CONGIUNZIONE, PREPOSIZIONE, LOCUZIONE, IGNOTA)

# Dal tag UPOS di Universal Dependencies alle classi di questo progetto. La
# fonte dichiara tutti e 17 i tag universali, e qui si tiene solo quello che il
# progetto sa usare: gli altri arrivano come `ignota`, che e' il posto giusto
# dove mettere cio' che non si sa, e non quello dove mettere cio' che si e'
# indovinato.
MAPPA_UPOS = {
    "NOUN": NOMINALE,
    "PROPN": NOMINALE,
    "VERB": VERBO,
    "AUX": VERBO,
    "ADJ": AGGETTIVO,
    "ADV": AVVERBIO,
    "PRON": PRONOME,
    "CCONJ": CONGIUNZIONE,
    "SCONJ": CONGIUNZIONE,
    "ADP": PREPOSIZIONE,
}

# Da `campo` del glossario alle classi di questo progetto. `campo` e' un campo
# che viene dalla fonte e puo' dire anche cose che qui non servono
# («modo di dire», «gioco»): quelle non sono classi e non entrano, restano
# `ignota`, e il fatto che restino ignote e' la risposta giusta invece di
# inventare una classe che la fonte non ha scritto.
MAPPA_CAMPO = {
    "sostantivo": (NOMINALE, ""),
    "verbo": (VERBO, "infinito"),
    "aggettivo": (AGGETTIVO, ""),
    "avverbio": (AVVERBIO, ""),
    "pronome": (PRONOME, ""),
    "congiunzione": (CONGIUNZIONE, ""),
    "preposizione": (PREPOSIZIONE, ""),
    "locuzione": (LOCUZIONE, ""),
    "participio passato": (PARTICIPIO, "passato"),
}


@dataclass
class Analisi:
    """Che cos'e' una parola italiana, e chi lo dice.

    `fonte` vuota e `classe` `ignota` non sono un caso raro: sono il risultato
    della maggior parte delle voci del glossario, e il modulo li dichiara
    invece di riempirli.
    """
    forma: str = ""
    classe: str = IGNOTA
    dettaglio: str = ""
    fonte: str = ""
    attendibilita: str = ""
    motivo: str = ""
    alternative: list = field(default_factory=list)

    @property
    def nota(self) -> bool:
        return self.classe != IGNOTA

    def come_dict(self) -> dict:
        return {
            "forma": self.forma,
            "classe": self.classe,
            "dettaglio": self.dettaglio,
            "fonte": self.fonte,
            "attendibilita": self.attendibilita,
            "motivo": self.motivo,
        }


def compatibile(classe_parola: str, classe_regola: str) -> bool:
    """Una regola vale solo per le parole della sua classe.

    Il caso che chiude la porta e' `ignota`: una parola di cui non si sa che
    cosa sia **non** e' un caso in cui la regola va applicata «per sicurezza»,
    perche' applicarla e' il difetto che questo modulo esiste per evitare. Il
    progetto preferisce non rispondere a una risposta che non sa dare, e il
    numero delle parole lasciate fuori e' stampato: un buco che si vede e' un
    buco che si chiude.
    """
    if classe_parola == IGNOTA or classe_regola == IGNOTA:
        return False
    return classe_parola == classe_regola


class Italiano:
    """Le tre fonti dell'analisi, e nient'altro."""

    PERCORSO = os.path.join("dati", "italiano.jsonl")

    def __init__(self, analisi_file=None, glossario=None, verbi=None):
        self.da_corpus = analisi_file or {}
        self.da_glossario = {}
        self.da_verbi = {}
        if glossario is not None:
            for voce in glossario.voci:
                mappata = MAPPA_CAMPO.get((voce.campo or "").strip().lower())
                if not mappata:
                    continue
                classe, dettaglio = mappata
                self.da_glossario.setdefault(normalizza.chiave(voce.italiano), []).append(
                    Analisi(voce.italiano, classe, dettaglio, voce.fonte,
                            voce.attendibilita))
        if verbi is not None:
            for riga in verbi.get("righe", []):
                if riga.get("lemma"):
                    self.da_verbi[normalizza.chiave(riga["lemma"])] = Analisi(
                        riga["lemma"], VERBO, "infinito",
                        "dati/verbi.jsonl, il lemma di un verbo e' un infinito "
                        "per dichiarazione", "D")

    # ------------------------------------------------------------- il file
    @classmethod
    def da_file(cls, percorso=None, glossario=None, verbi=None) -> "Italiano":
        """Legge `dati/italiano.jsonl` se c'e', e se non c'e' lo dice.

        Un file assente non e' un errore: e' una raccolta che non e' ancora
        avvenuta, e il modulo funziona con le altre due fonti. Quello che non
        e' accettato e' un file presente con righe senza fonte: quello e'
        un'analisi inventata, e lo prende `verifica_dati` (F19).
        """
        raccolto = {}
        percorso = percorso or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), cls.PERCORSO)
        if os.path.exists(percorso):
            with io.open(percorso, encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if not riga or riga.startswith("//"):
                        continue
                    d = json.loads(riga)
                    forma = d.get("forma", "")
                    if not forma:
                        continue
                    # Le righe portano il **tag** universale della fonte, non
                    # una classe di questo progetto: la traduzione e' la mappa
                    # `MAPPA_UPOS`. Il difetto che questo leggeva male era
                    # invisibile e perverso — chiedeva un campo che la fonte non
                    # scrive, quindi **ogni** riga del corpus tornava `ignota`
                    # e il progetto perdeva 1047 voci senza che nessun numero
                    # dicesse che le stava perdendo.
                    tag = ""
                    conteggio = 0
                    for classe in d.get("classi") or []:
                        nome_tag = classe.get("tag") if isinstance(classe, dict) else classe
                        if nome_tag and classe.get("conteggio", 0) >= conteggio:
                            tag = nome_tag
                            conteggio = classe.get("conteggio", 0)
                    raccolto[normalizza.chiave(forma)] = Analisi(
                        forma, MAPPA_UPOS.get(tag, IGNOTA), tag,
                        d.get("fonte", ""), d.get("attendibilita", ""),
                        "" if tag else "nessun tag nella riga", d.get("classi"))
        return cls(raccolto, glossario, verbi)

    # ------------------------------------------------------------- la domanda
    def analizza(self, parola: str) -> Analisi:
        """Che cos'e' `parola` in italiano, o `ignota` con il motivo.

        Il motivo dell'`ignota` non e' decorativo: e' la frase che dice al
        chiamante **perche'** il progetto non sa, e il chiamante la stampa.
        """
        k = normalizza.chiave(parola)
        if not k:
            return Analisi(parola, IGNOTA, "", "", "",
                           "una parola vuota non si analizza")
        # **Una fonte che non sa rispondere non copre una che sa.** Il corpus
        # annotato dichiara un tag per quasi ogni parola, ma il progetto sa
        # usare solo una parte dei tag universali: `DET`, `NUM`, `PART` e
        # `PUNCT` non hanno una classe di questo progetto. Se una riga di quelle
        # vincesse sulle altre, una parola che il glossario dichiara come
        # pronome diventerebbe `ignota` perche' il corpus l'ha annotata come
        # articolo determinativo — che e' un'altra cosa, non una informazione
        # migliore. Quindi una risposta non utilizzabile viene **saltata**, e
        # l'ordine delle fonti resta quello dichiarato.
        for archivio, nome in ((self.da_corpus, "corpus annotato"),
                               (self.da_glossario, "glossario"),
                               (self.da_verbi, "verbi")):
            if k not in archivio:
                continue
            risposta = archivio[k][0] if isinstance(archivio[k], list) else archivio[k]
            if not risposta.nota and nome != "verbi":
                continue
            trovate = archivio[k] if isinstance(archivio[k], list) else [risposta]
            if len(trovate) > 1:
                risposta.alternative = [
                    {"classe": a.classe, "fonte": a.fonte} for a in trovate
                    if a is not risposta]
            return risposta
        return Analisi(
            parola, IGNOTA, "", "", "",
            "nessuna delle tre fonti dichiara questa parola: il corpus "
            "annotato non la contiene, il glossario non ha `campo` per questa "
            "voce, e non e' il lemma di un verbo dichiarato")

    # ------------------------------------------------------------- il conto
    def copertura(self, glossario) -> dict:
        """Quante voci del glossario il progetto sa classificare, e quante no.

        Il numero che conta non e' quello delle voci con una classe, e' quello
        delle voci **senza**: e' la misura di quanto resta da raccogliere.
        """
        per_classe = {}
        senza = []
        for voce in glossario.voci:
            analisi = self.analizza(voce.italiano)
            if analisi.nota:
                per_classe[analisi.classe] = per_classe.get(analisi.classe, 0) + 1
            else:
                senza.append(voce.id)
        return {
            "voci": len(glossario.voci),
            "classificate": len(glossario.voci) - len(senza),
            "senza_classe": len(senza),
            "per_classe": per_classe,
            "esempi_senza": senza[:12],
        }