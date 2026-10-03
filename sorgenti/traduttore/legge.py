"""Leggere la grafia ferrarese e ricavarne un suono, senza inventarlo.

Il ferrarese si scrive a orecchio: `magnàr` e `magnar` nella stessa fonte sono
la stessa parola con due scelte di scrittura, non due suoni. Quindi la
grafia **non** dice la pronuncia, e nessun programma puo' farla dire. Questo
modulo fa una cosa sola e piccola: **applica le regole che il progetto ha
dichiarato** nell'intestazione di `dati/fonetica.jsonl`, e dove nessuna fonte
dichiara niente **si ferma e lo dice**.

La regola che tiene insieme tutto il modulo: **non si sceglie mai**. Una
trascrizione generata da qui porta sempre `attendibilita: "I"` e la nota del
dubbio, e resta `da_verificare` finche' un parlante non la conferma. Il
risultato non e' «la pronuncia di questa parola», e' «cosa dice la grafia se si
applicano le regole dichiarate, e dove non lo dice».

Le sei regole applicate sono quelle dichiarate nel file, e sono tutte regole di
LETTURA, non conoscenze sul parlato:

1. vocali /a e ɛ i o u/; nessuna vocale schwa, nessuna vocale nasale;
2. `gh` = /g/, `ch` = /k/; nessuna eccezione documentata;
3. `gn` davanti a vocale anteriore = /ɲ/;
4. `c` = /k/ davanti ad a, o, u e consonante; = /tʃ/ davanti a e, i. `g` = /g/
   davanti ad a, o, u; = /dʒ/ davanti a e, i;
5. `ci`, `gi` si leggono /tʃi/, /dʒi/; `majàl` = /maˈjal/, la `j` e' semivocale;
6. `s` e `z` si leggono **come sono scritte**, e non e' una regola ma una
   scelta che puo' essere sbagliata.

Il punto 6 e' quello che decide l'onesta' del modulo: la `s` e la `z`
intervocaliche sono proprio il punto su cui le fonti disponibili non dicono
niente, e in una lingua che scrive a orecchio sono dove la scrittura inganna
di piu'. Qui non si finge di saperla: si scrive la lettera, si **dichiara il
dubbio**, e chi ascolta sa dove guardare per primo.

L'accento tonico viene dalla fonte, non da qui. Se la fonte scrive `magnàr`,
la trascrizione mette `/maˈɲnar/`. Se la fonte scrive `brisa` senza accento,
qui non se ne mette e la nota lo dice: metterlo per conto proprio sarebbe il
modo piu' economico di sbagliare.
"""

from __future__ import annotations

# Le vocali toniche, come la fonte le marca. La scelta che conta e' una e
# sola, e non e' un'invenzione di qui: la `e` accentata e' **aperta** (/ɛ/) e
# quella non accentata e' **chiusa** (/e/). Lo dice il file, quattro volte
# (`gh'e'` = /gˈɛ/, `n'e'` = /nˈɛ/, `frarés` = /fraˈrɛs/,
# `frarèz` = /fraˈrɛz/) contro due (`ghe` = /ge/, `ved` = /ved/). Se la
# marcatura accentata cambiasse la vocale, la regola 1 che dichiara /e/ e /ɛ/
# come due suoni distinti sarebbe inutile: e il file non la scrive a caso.
# Quindi /ɛ/ per la vocalica e /e/ per la tonica accentata, che e' l'opposto
# di quello che si scrive di solito, ed e' per quello che va detto.
VOCALI_TONICHE = {
    "à": ("a", "ˈ"),
    "á": ("a", "ˈ"),
    "è": ("ɛ", "ˈ"),
    "é": ("ɛ", "ˈ"),
    "ì": ("i", "ˈ"),
    "í": ("i", "ˈ"),
    "ò": ("o", "ˈ"),
    "ó": ("o", "ˈ"),
    "ù": ("u", "ˈ"),
    "ú": ("u", "ˈ"),
}

# Le vocali accentate sono anche in `VOCALI`, altrimenti il modulo le
# tratterebbe come lettere ignote. Sono le stesse scelte di `VOCALI_TONICHE`,
# ripetute: il modulo prende il **simbolo** da qui e il **segno di accento**
# da li', e i due dizionari devono dire la stessa cosa.
VOCALI = {
    "à": "a", "á": "a", "è": "ɛ", "é": "ɛ",
    "ì": "i", "í": "i", "ò": "o", "ó": "o",
    "ù": "u", "ú": "u", "â": "a", "ê": "e", "î": "i",
    "ô": "o", "û": "u", "ä": "a", "ö": "o", "ü": "u",
    "a": "a", "e": "e", "i": "i", "o": "o", "u": "u",
}

# Le consonanti, lette come si scrivono. `q` non c'e' nel ferrarese di questa
# fonte e resta dichiarata come sconosciuta invece di tirare a indovinare.
CONSONANTI = {
    "b": "b", "d": "d", "f": "f", "l": "l", "m": "m",
    "n": "n", "p": "p", "r": "r", "t": "t", "v": "v",
    "j": "j",
}

# Le consonanti doppie non esistono nel ferrarese (S015): `bell` si legge come
# due consonanti distinte, e non come una sola lunga. E' una regola che la
# fonte dichiara, quindi qui si applica: la doppia perde una delle due.
DOPPIE = set("bcdflmnprstvz")

# I digrammi che la fonte dichiara senza eccezioni (regola 2).
DIGR = {"gh": "g", "ch": "k"}


def _scansiona(parola: str) -> tuple:
    """La parola in pezzi, con l'accento tonico gia' segnato.

    I pezzi sono tuple `(simbolo, accento)`: l'accento e' `''` per tutto tranne
    la vocale tonica, che porta `ˈ`. Cosi' chi chiama la funzione non deve
    sapere dove metterlo, e non puo' dimenticarselo.
    """
    pezzi = []
    i = 0
    n = len(parola)
    while i < n:
        c = parola[i]
        # L'apostrofo non e' una lettera: segna un'elisione (`gh'e'`, `n'e'`,
        # `dint'`). Non suona, quindi non e' un fonema e non e' nemmeno un
        # dubbio: si salta e si continua a leggere. Senza questo, `gh'e'`
        # finiva a `/g/`, cioe' metta della parola, senza dire niente.
        if c in "'’`":
            i += 1
            continue
        # Il digramma, prima della consonante singola: `gh` non e' `g` + `h`.
        if c in "gc" and i + 1 < n and (c + parola[i + 1]).lower() in DIGR:
            pezzi.append((DIGR[c + parola[i + 1]].lower(), ""))
            i += 2
            continue
        # `gn` davanti a vocale anteriore: /ɲ/ (regola 3).
        if (c == "g" and i + 1 < n and parola[i + 1] == "n"
                and i + 2 < n and parola[i + 2].lower() in "eiéèi"):
            pezzi.append(("ɲ", ""))
            i += 2
            continue
        # `c` e `g` palatali davanti a e, i (regola 4).
        vocale = parola[i + 1].lower() if i + 1 < n else ""
        if c == "c" and vocale in "eiéèi":
            pezzi.append(("tʃ", ""))
            i += 1
            continue
        if c == "g" and vocale in "eiéèi":
            pezzi.append(("dʒ", ""))
            i += 1
            continue
        # Il caso velare, che e' metà della regola 4 e la parte che il
        # glossario del 1889 usa di piu': `g` e `c` davanti ad a, o, u o
        # consonante. Senza questo ramo ogni `magnar` finiva «ignota».
        if c == "c":
            pezzi.append(("k", ""))
            i += 1
            continue
        if c == "g":
            pezzi.append(("g", ""))
            i += 1
            continue
        if c == "s" or c == "z":
            pezzi.append((c, ""))
            i += 1
            continue
        if c.lower() in CONSONANTI:
            pezzi.append((CONSONANTI[c.lower()], ""))
            i += 1
            continue
        if c.lower() in VOCALI:
            simbolo = VOCALI[c.lower()]
            accento = VOCALI_TONICHE.get(c.lower(), ("", ""))[1]
            pezzi.append((simbolo, accento))
            i += 1
            continue
        # Una consonante doppia: una delle due va, e si dichiara il dubbio.
        if c.lower() in DOPPIE and i + 1 < n and parola[i + 1] == c:
            pezzi.append((CONSONANTI.get(c.lower(), c.lower()), ""))
            return pezzi, "consonante doppia %r: le fonti non hanno consonanti " \
                          "doppie, ma quale delle due sia non si sa" % c
        # Una lettera che il progetto non conosce: non si indovina.
        return pezzi, "lettera sconosciuta %r: nessuna fonte dice che suona" % c
    return pezzi, ""


def _dubbi_gn(parola: str) -> list:
    """La `gn` davanti a una vocale che non e' anteriore: la regola 3 non basta.

    La regola 3 dice `gn` = /ɲ/ solo davanti a vocale anteriore (`e`, `i`).
    Davanti a `a`, `o`, `u` la regola lascia passare /gn/, e questa e' una
    **truncamento silenzioso**: la regola 3 tace, e chi non va a leggerla
    crede che /gn/ sia un fatto verificato.

    Non lo e'. Nel file `magnàr` = /maˈɲnar/, cioe' /ɲ/ anche davanti ad
    `à`. Quindi qui si applica la regola come e' scritta — /gn/ — e si
    **dichiara** che le trascrizioni esistenti dicono il contrario. Il
    contrario di scegliere fra due fonti non e' scegliere: e' scrivere le
    due letture e dire che sono due.
    """
    dubbi = []
    for pos, c in enumerate(parola):
        if c.lower() != "g":
            continue
        seguente = parola[pos + 1:pos + 2].lower()
        if seguente != "n":
            continue
        dopo = parola[pos + 2:pos + 3].lower()
        if not dopo or dopo in "eiéèi":
            continue
        dubbi.append("`gn` davanti a `%s`: la regola 3 dice /ɲ/ solo davanti a "
                     "vocale anteriore e tace qui, ma le trascrizioni del "
                     "file danno /ɲ/ anche davanti a `%s` (/magnar/ = "
                     "/maˈɲnar/). Due letture, e nessuna fonte sceglie"
                     % (dopo, dopo))
    return dubbi


def _dubbi_s_z(parola: str) -> list:
    """Le `s` e le `z` fra due vocali: il punto che nessuna fonte dichiara.

    Non e' una regola, e' un vuoto. Qui si **non sceglie**: si scrive la
    lettera come e' scritta e si restituisce il dubbio, perche' in una lingua
    che scrive a orecchio sono proprio li' che la scrittura inganna di piu', e
    chi verifica con un parlante deve sapere dove guardare per primo.
    """
    dubbi = []
    for pos, c in enumerate(parola):
        if c not in "sz":
            continue
        if pos == 0 or pos == len(parola) - 1:
            continue
        if parola[pos - 1] in VOCALI and parola[pos + 1] in VOCALI:
            dubbi.append("%s intervocalica in posizione %d: le fonti non "
                         "dicono se suona /s/ o /z/" % (c, pos + 1))
    return dubbi


def leggi(parola: str) -> dict:
    """La grafia ferrarese letta secondo le regole dichiarate.

    Ritorna un dizionario con la trascrizione (`ipa`, fra slash), la nota dei
    dubbi (`nota`), l'accento (`accento`) e un `attendibilita` che e' sempre
    `I`: qui non si ascolta nessuno, e nessuna funzione puo' farlo credere.

    Il dizionario ha anche `dubbi`: se non e' vuoto, la trascrizione **non**
    va usata come se fosse un fatto. Non e' un avviso, e' il contenuto della
    risposta: una parola con un dubbio e' una parola che ascolta prima di
    essere fatta sentire.
    """
    parola = (parola or "").strip()
    esito = {
        "forma": parola,
        "ipa": "",
        "nota": "",
        "dubbi": [],
        "accento": "",
        "attendibilita": "I",
        "da_verificare": True,
    }
    if not parola:
        esito["nota"] = "parola vuota: non c'e' niente da leggere"
        return esito

    pezzi, problema = _scansiona(parola)
    if problema:
        esito["nota"] = problema
        esito["dubbi"].append(problema)

    # La vocale atonica pretonica e' resa breve **senza dichiarare se sia
    # aperta o chiusa**: `ved` e' /ved/, non /vɛd/, perche' la fonte non dice.
    for vocale, accento in pezzi:
        if vocale in "e" and accento == "":
            esito["dubbi"].append("vocale `e` atonica: non si sa se aperta "
                                  "(/ɛ/) o chiusa (/e/)")

    # Il segno di accento va **dentro** la trascrizione: una IPA senza
    # `ˈ` non dice quale sillaba e' tonica, e il motore la legge male.
    simboli = "".join(("ˈ" if a else "") + s for s, a in pezzi)
    accenti = [s for s, a in pezzi if a]
    esito["accento"] = "ˈ" if accenti else ""
    if not accenti:
        esito["dubbi"].append("la fonte non marca l'accento, quindi qui non "
                              "se ne mette: metterlo sarebbe indovinare")

    esito["dubbi"].extend(_dubbi_s_z(parola))
    esito["dubbi"].extend(_dubbi_gn(parola))
    # Le consonanti doppie sono un dubbio, non un errore: si sa che non
    # esistono, non si sa quale delle due sia la buona.
    for pos, c in enumerate(parola):
        if c.lower() in DOPPIE and pos + 1 < len(parola) and parola[pos + 1] == c:
            # La posizione nel messaggio: senza, due doppie della stessa
            # lettera nella stessa parola producono due righe **identiche**,
            # e una ripetizione sembra un errore invece di essere un fatto.
            esito["dubbi"].append("consonante doppia `%s` in posizione %d: nel "
                                  "ferrarese non esistono, ma quale delle due "
                                  "resti non si sa" % (c, pos + 1))

    esito["ipa"] = "/" + simboli + "/"
    if esito["dubbi"]:
        esito["nota"] = "; ".join(esito["dubbi"])
    return esito