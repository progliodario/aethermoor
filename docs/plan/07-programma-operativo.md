# 07. Programma operativo: a breve, medio e lungo termine

> **Stato:** scritto il 23 novembre 2026, dopo una verifica completa di repository, documenti, CI e impostazioni di GitHub (sezione 2). È il programma da seguire. La [roadmap](06-roadmap-rischi-backlog.md) (sezione 8) dice **dove siamo**; questo documento dice **che cosa si fa**, in quale ordine, con quali file, con quali criteri di accettazione, e quali decisioni servono al proprietario.
>
> Ogni voce ha una issue su GitHub, nella milestone del suo periodo (sezione 9). Quando un batch è fatto, questo documento, la roadmap e le issue si aggiornano nella stessa PR (sezione 11). **Dove siamo adesso: la [sezione 0](#0-stato-delle-voci).** Le sezioni 2 e 3 descrivono lo stato di partenza del 23 novembre e restano come storia.

## 0. Stato delle voci

Aggiornato al 24 novembre 2026, dopo la PR #269. Una voce fatta ha la nota "Fatto" sotto la sua descrizione, con ciò che differisce dal
progetto; la sua issue è chiusa. Questa tabella si aggiorna in ogni PR che fa una voce (sezione 11).

| Voce | Che cosa | Stato | PR | Issue |
|---|---|---|---|---|
| B1.1 | Baseline di detekt a zero | **in corso**: da 104 a 73 | #258, #265, #268, #271, batch 14 | #224 aperta |
| B1.2 | Spec 15 e ADR 0014 | fatta | #258 | #225 |
| B1.3 | Licenze in CI | fatta | #258 | #226 |
| B1.4 | Matrice di parità | fatta | #258 | #227 |
| B1.5 | Copie dei salvataggi e migrazioni | fatta | #258 | #228 |
| B1.6 | Lista di rilascio | fatta | #258 | #229 |
| B2.1 | Il tempo che cambia i prezzi | fatta | #258 | #230 |
| B3.1 | Viaggiatori che camminano | fatta | #264 | #231 |
| B3.2 | Paesani alla festa | fatta | #260 | #232 |
| B4.1 | Missioni a tempo e prove delle stagioni | fatta | #259 | #233 |
| G1 | Decisioni del proprietario (sezione 8) | **aperta**: aspetta il proprietario | | #234 aperta |
| C1.1 | Stanze del cottage | fatta | #266 | #235 |
| C1.2 | Affissi scelti | fatta | #265 | #236 |
| C2.1 | Compagni scelti (il gruppo) | fatta | #267 | #237 |
| C3.1 | Dungeon di Gideon, forma ridotta | fatta | #268 (spec), #269 | #238 |
| C4.1 | Streaming con thread | **fatta** | batch 14 | #239 chiusa |
| C4.2 | Misure su Android | **quasi fatta**: mancano i numeri del telefono del proprietario | batch 13 | #240 aperta |
| C5.1 | Una settimana di gioco | fatta | #264 | #241 |
| C6.1 | Sintetizzatore | **bloccata**: solo con il sì del proprietario | | #242 aperta |
| D1-D4 | Storie laterali degli otto protagonisti | fatte | #261, #262, #263 | #243-#246 |
| E1.1 | Modalità qualità | **fatta** | batch 13 | #247 chiusa |
| E1.2 | Log dei crash | fatta | #265 | #248 |
| E1.3 | Traduzioni e accessibilità | fatta | #268 | #249 |
| E2.1 | Rimappatura su Android | **fatta** | batch 14 | #250 chiusa |
| E2.2 | Controller su Android | **fatta** | batch 13 | #251 chiusa |
| E3.1 | Pipeline di rilascio | **fatta**; la prova con un tag la decide il proprietario | batch 13 | #252 chiusa |
| E3.2 | Firma del codice | **bloccata**: decisione e chiavi del proprietario | | #253 aperta |
| E4.1 | Documentazione per i mod | fatta | #263 | #254 |
| E4.2 | Pagina di download | **aperta**: decisione del proprietario | | #255 aperta |
| F1 | Dopo la 1.0 | **aperta** (lungo termine) | | #256 aperta |

**Le prossime voci, nell'ordine consigliato:** B1.1 a ogni batch (un po' alla volta); i numeri del telefono di C4.2, che misura il
proprietario; le voci fuori dal programma sono nella sezione 8.4 della roadmap (il colpo di coppia è fatto).
Le voci bloccate o del proprietario aspettano la sua risposta e non fermano le altre.

## 1. Come leggere questo programma

- **Batch**: un ramo e una PR grande, spedita con `tools/ship.py`. Il proprietario non vuole PR piccole (`CLAUDE.md`, "Big PRs"): ogni batch porta più voci insieme. La descrizione della PR dice `Closes #N` per ogni issue delle sue voci, così le issue si chiudono da sole al merge.
- **Voce**: un pezzo di lavoro con un ID (B1.1, C2.1, D1...), una taglia e criteri di accettazione. Ogni voce ha la sua issue, con lo stesso ID nel titolo.
- **Taglie**: relative, non di calendario (come nella roadmap). S piccola, M media, L grande, XL più batch.
- **Fatta**: una voce è fatta quando rispetta la *Definition of Done* di `CLAUDE.md`, i suoi criteri di accettazione qui sotto, e la CI è verde su Windows, Linux e Android.
- **Bloccata**: la voce aspetta una decisione del proprietario (sezione 8). Le altre voci vanno avanti.
- Ogni voce descrive: **Cosa**, **Perché**, **Come** (il progetto di massima), **File** (da elencare prima di iniziare, come chiede `CLAUDE.md`), **Accettazione**, **Rischi**, **Dipende da**.

## 2. Stato di partenza (verificato il 23 novembre 2026)

| Che cosa | Stato | Come lo si è verificato |
|---|---|---|
| Repository | `main` a `ecd4a4d` (PR [progliodario/aethermoor#223](https://github.com/progliodario/aethermoor/pull/223)); albero pulito; nessuna PR aperta; nessun tag; nessuna release; sul server solo il ramo `main` | `git status`, `gh pr list`, `git ls-remote` |
| Issue | nessuna aperta; una chiusa ([progliodario/aethermoor#181](https://github.com/progliodario/aethermoor/issues/181)). Le voci del programma sono state aperte in questo batch | `gh issue list` |
| CI su `main` | verde: `ci-data` (51 s) sull'ultimo merge; `ci-desktop` e `ci-android` verdi sul merge di [progliodario/aethermoor#222](https://github.com/progliodario/aethermoor/pull/222) e sulla PR [progliodario/aethermoor#223](https://github.com/progliodario/aethermoor/pull/223) | `gh run list` |
| Dati | `validate_data.py` OK (un pacchetto) | Python 3.13 del `.venv` |
| Strumenti | 73 test passati | `pytest -q tools/tests` |
| Documenti generati | `make_facts --check` e `gen_conformance --check` OK (30 file di vettori); catalogo, bilanciamento (0 valori anomali) e traduzioni (0 testi da guardare) rigenerati senza differenze | eseguiti in locale |
| Codice | circa 21 mila righe C++ (desktop, test inclusi) e circa 16 mila righe Kotlin (Android). Non compilato qui: il compilatore è la CI | `wc -l` |
| Debito Kotlin | baseline di detekt: 104 voci (96 dopo il primo batch, 90 dopo il terzo) | `android/config/detekt-baseline.xml` |
| GitHub (decisioni del proprietario, non toccate) | protezione del ramo `main` assente; alert di vulnerabilità e aggiornamenti di sicurezza di Dependabot disattivati; wiki attiva; Discussions disattivate; merge commit e rebase consentiti oltre allo squash; cancellazione automatica dei rami disattivata (la fa `ship.py`); secret scanning e push protection attivi | `gh api repos/progliodario/aethermoor` |
| Label | cinque label presenti su GitHub mancavano in `.github/labels.json` | confronto con `gh label list` |

## 3. Batch B0: ordine del repository (questo batch)

Questo batch porta il documento e sistema quello che i documenti dicevano e non era più vero. Ogni riga è una correzione fatta in questa PR.

| # | Dove | Che cosa non andava | Correzione |
|---|---|---|---|
| 1 | `docs/plan/02` (stato) | diceva che le specifiche 10, 11, 14 e 15 "devono ancora nascere" | aggiornato: 10, 11, 14, 16, 17 e 18 sono scritte; manca la 15 (B1.2) |
| 2 | `docs/plan/03` (stato) | diceva che nel gioco c'è un solo protagonista (Ren) | aggiornato: otto protagonisti, compagni, reincarnazione, titoli, tag, base |
| 3 | `docs/plan/04` (stato) | diceva "nessun suono" e "luci puntiformi non ancora" | aggiornato: 174 effetti sonori; le luci sono in `data/base/lights.json` |
| 4 | `docs/plan/05` (tabella di stato) | "23 file di vettori" (sono 30); citava la lista di rilascio come se esistesse; diceva che la wiki "il piano la voleva spenta" | aggiornato; la lista di rilascio è in B1.6; la wiki è in G1 |
| 5 | `docs/plan/README.md` | stato "al 13 novembre"; indice senza il documento 07; domande aperte già risposte (repository e identificativo Android) | aggiornati |
| 6 | `docs/plan/06`, rischio R1 | "23 suite di vettori" | 30 file |
| 7 | `docs/plan/06`, sezione 8.4, voce 1 | "quasi tutte funzioni lunghe" | 72 su 104 sono complessità ciclomatica: i numeri esatti sono in B1.1 |
| 8 | `docs/plan/01`, `desktop/README.md`, `THIRD_PARTY_NOTICES.md` | dicevano che il testo del desktop usa il font di debug di SDL | il desktop disegna con il font del pacchetto (spec 13); il font di debug è solo il ripiego |
| 9 | `README.md` e `README.en.md`, "Che cosa manca" | l'elenco non coincideva con la roadmap (i carri che viaggiano erano nel medio termine) | allineato alla sezione 8.4, con il rimando a questo documento |
| 10 | `.github/ISSUE_TEMPLATE/config.yml` | link alle Discussions, che sono disattivate: un link rotto per chi apre una domanda | sostituito con i link alla documentazione per i mod e a `CONTRIBUTING.md` |
| 11 | `.github/labels.json` | cinque label presenti su GitHub mancavano nel file sorgente (`accessibility`, `dependencies`, `github_actions`, `python`, `java`) | aggiunte; aggiunta anche `owner-decision` |
| 12 | `docs/adr/0008` | "accepted", ma le schermate sono scritte nel codice dei client | nota di stato; la decisione è in ADR 0014 (B1.2) |
| 13 | `docs/spec/README.md` | la spec 15 mancante non aveva un rimando al piano | rimando a B1.2 |
| 14 | `.github/workflows/release.yml` | il commento diceva "Skeleton (M0)" e che le build arrivano con i milestone | corretto: le build di prova esistono già in CI; la pipeline di rilascio è E3.1 |
| 15 | GitHub, issue e milestone | la roadmap (sezione 7) prometteva una issue per voce, ma non ne esisteva nessuna | create 33 issue (numeri 224-256) e 5 milestone, sezione 9 |
| 16 | tag `v0.0.1` | previsto da M0 e mai creato | non è un errore: pubblicare o taggare una release è decisione del proprietario (G1) |
| 17 | `CHANGELOG.md` | la modifica non c'era | voce nella sezione `Documentation` |
| 18 | `CLAUDE.md`, "Where things stand" | non diceva dove sta il programma | la riga "What comes next" rimanda a questo documento |
| 19 | `docs/index.md` | il documento 07 non era indicizzato | riga aggiunta, con il rimando "What comes next" |

## 4. Principi che valgono in ogni batch

1. **Spec prima.** Una regola nuova si scrive in `docs/spec/`, poi nel riferimento Python (`tools/reference/`), poi nei vettori di conformità, poi nei due client, dati e testi (IT ed EN) nello stesso batch.
2. **Un comportamento su due client.** Se un client resta indietro, si apre una issue `parity-debt` e si usa un gate di funzionalità (ADR 0009). Oggi il gate non è usato: lo si usa solo quando serve davvero.
3. **Mai modificare a mano i file generati** (lista in `CLAUDE.md`): si cambia la sorgente e si rigenera.
4. **Salvataggi.** Prima il banco di prova delle migrazioni (B1.5), poi il cambiamento; la copia della versione precedente resta nel repository.
5. **Combattimenti facili.** `balance_report` deve restare a zero valori anomali. Non si alza mai la difficoltà per bilanciare (`CLAUDE.md`, "Fights must be too easy").
6. **Musica e ambiente restano spenti** finché il proprietario non dice sì (C6.1).
7. **Niente compilatore qui.** C++ e Kotlin si scrivono con cura e si verificano in CI. Si fanno passi piccoli, un file alla volta, con i conteggi dei test aggiornati nello stesso commit dei dati.
8. **Il proprietario prova ogni batch** su Windows, Linux e Android. La descrizione della PR dice che cosa guardare e che cosa non si è potuto verificare (il suono, le prestazioni su telefono, ciò che si vede solo giocando a lungo).
9. **Un batch = un ramo, una PR, `tools/ship.py`.** CHANGELOG in inglese; le voci fatte passano da 06 §8.4 a 06 §8.3 in italiano; le issue si chiudono con `Closes`.
10. **Ci si ferma solo per le decisioni della sezione 8.** Una voce bloccata non blocca il resto del batch.

## 5. Le voci

Ogni periodo ha una milestone su GitHub (sezione 9). L'ordine dentro un periodo è quello di esecuzione.

### 5.1 A breve (B1-B4)

**Obiettivo:** ridurre il debito e il rischio prima dei cambiamenti grandi, e rendere visibile il mondo che c'è già. Sono i prossimi batch.

#### B1 Fondamenta (un batch, sei voci)

Batch unico con le voci B1.1-B1.6, più il lavoro di G1 che serve a sbloccare le decisioni. Il detekt (B1.1) è una voce lunga che continua nei batch successivi.

> **Stato (23 novembre 2026, primo batch del programma, con B2.1).** Fatte B1.2, B1.3, B1.4, B1.5 e B1.6, con i loro criteri di
> accettazione; B1.1 è avviata (baseline da 104 a 96: le due eccezioni ingoiate, le due voci inutilizzate, una funzione complessa e tre cicli con troppe
> uscite) e continua nei batch successivi. Differenze dal progetto: la copia dei salvataggi di B1.5 contiene anche un salvataggio del
> mondo generato con tutti i campi che solo i client scrivono, letto e riscritto dai due client; le licenze di B1.3 contano anche gli
> strumenti scaricati dalla CI (ktlint, detekt).

##### B1.1 Detekt
- **Cosa:** portare la baseline da 104 voci a zero (`android/config/detekt-baseline.xml`): 72 `CyclomaticComplexMethod`, 19 `NestedBlockDepth`, 9 `LoopWithTooManyJumpStatements`, 2 `SwallowedException`, 1 `UnusedPrivateProperty`, 1 `UnusedParameter`.
- **Perché:** la baseline è debito che cresce con ogni funzione nuova, e le eccezioni ingoiate nascondono errori veri.
- **Come:** prima le due `SwallowedException` (l'errore si registra o si rilancia), poi le due voci inutilizzate, poi le uscite dai cicli e l'annidamento (si estraggono funzioni), infine la complessità file per file, partendo dal file con più voci. Un commit per file, che toglie le sue voci dalla baseline. Mai aggiungere voci. A zero, il file si cancella e `docs/dev/kotlin-style.md` lo dice.
- **File:** `android/config/detekt-baseline.xml`, `android/core/src/main/kotlin/**`, `android/game/src/main/kotlin/**`, `docs/dev/kotlin-style.md`.
- **Accettazione:** `kotlin-style` verde; la baseline ha meno voci a ogni batch (il numero va nella descrizione della PR); a zero il file è cancellato.
- **Rischi:** senza compilatore locale ogni estrazione può rompere la build. Si fa un file alla volta. I test JVM (`:core:test`) coprono la logica del simulatore; il modulo `game` non ha test, quindi lì si fanno solo estrazioni meccaniche.
- **Taglia:** L, su più batch. **Dipende da:** niente. Issue: [progliodario/aethermoor#224](https://github.com/progliodario/aethermoor/issues/224).

##### B1.2 Spec 15 e ADR 0014
- **Cosa:** scrivere `docs/spec/15-ui-layout.md`, cioè le regole di layout che entrambi i client seguono (pannelli, margini, dimensioni del testo, i valori del tema "Finestra di sistema"). E l'ADR 0014: le schermate restano nel codice di ogni client fino alla 1.0; la UI dichiarativa dell'ADR 0008 è rinviata. L'ADR 0008 riceve la nota di stato.
- **Perché:** la spec 15 è l'unico documento della serie che manca. Il tema "Finestra di sistema" del piano (M4) non esiste come tema dichiarato: il suo aspetto è nel codice dei due client.
- **Come:** la spec descrive ciò che i client fanno oggi (leggendo `desktop/src/app/main.cpp` e le schermate Kotlin), non ciò che il piano immaginava. Le costanti (colori, margini, dimensioni) della spec devono coincidere con il codice. `check_frames` difende l'aspetto del desktop.
- **File:** `docs/spec/15-ui-layout.md` (nuovo), `docs/spec/README.md`, `docs/adr/0014-*.md` (nuovo), `docs/adr/README.md`, `docs/adr/0008-*.md`, `CHANGELOG.md`.
- **Accettazione:** la spec 15 e l'ADR 0014 sono indicizzati; `pytest` (documenti) verde; l'ADR 0008 punta all'ADR 0014.
- **Rischi:** la scelta di rinviare la UI dichiarativa è mia (autonomia). Se il proprietario la vuole prima della 1.0, si cambia l'ADR 0014 e si aggiunge una voce.
- **Taglia:** M. **Dipende da:** niente. Issue: [progliodario/aethermoor#225](https://github.com/progliodario/aethermoor/issues/225).

##### B1.3 Licenze in CI
- **Cosa:** `tools/licenses.py` e una tabella `tools/licenses.json` (una riga per dipendenza, da vcpkg, Gradle e pip, con la sua licenza). Il controllo fallisce se una dipendenza non ha una riga o se la sua licenza non è ammessa: MIT, BSD, Apache-2.0, zlib, BSL-1.0, OFL; EPL-2.0 solo nei test. Lo stesso strumento genera `THIRD_PARTY_NOTICES.md`.
- **Perché:** il rischio R10 del piano (licenze incompatibili con GPLv3) ha come mitigazione un controllo automatico in CI. Oggi il controllo non c'è, e `THIRD_PARTY_NOTICES.md` è scritto a mano: la sua frase "tools/licenses.py (planned)" è ancora vera.
- **File:** `tools/licenses.py`, `tools/licenses.json` (nuovi), `THIRD_PARTY_NOTICES.md`, `.github/workflows/ci-data.yml`, `tools/tests/`, `CLAUDE.md` (lista dei file generati).
- **Accettazione:** aggiungere una dipendenza senza riga fa fallire `ci-data`; un test in `tools/tests` lo verifica.
- **Taglia:** S-M. **Dipende da:** niente. Issue: [progliodario/aethermoor#226](https://github.com/progliodario/aethermoor/issues/226).

##### B1.4 Matrice di parità
- **Cosa:** `tools/make_parity.py` genera `docs/design/parity.md`: per ogni suite di `tests/conformance/`, il test di ciascun client che la esegue, letto dai sorgenti dei test. `--check` in `ci-data` fallisce se un client non esegue una suite.
- **Perché:** R1 (due motori che divergono) ha probabilità alta e impatto alto. Oggi la parità si regge sulle specifiche e sui vettori, ma nessun controllo verifica che entrambi i client eseguano tutte le suite. Il comando `/parity-check` non è in CI.
- **File:** `tools/make_parity.py`, `docs/design/parity.md` (generato), `.github/workflows/ci-data.yml`, `.claude/commands/parity-check.md`, `tools/tests/`, `docs/design/README.md`.
- **Accettazione:** la matrice è generata; togliere una suite da un client fa fallire `ci-data`; il comando `/parity-check` rimanda allo strumento.
- **Taglia:** M. **Dipende da:** niente. Issue: [progliodario/aethermoor#227](https://github.com/progliodario/aethermoor/issues/227).

##### B1.5 Migrazioni dei salvataggi
- **Cosa:** una copia del salvataggio di ogni versione in `tests/saves/`, scritta dal riferimento. Ciascun client e `pytest` la caricano e controllano lo stato. Un cambio del formato senza migrazione e senza la copia della versione precedente fa fallire la build.
- **Perché:** oggi c'è solo la versione 1. B4.1, C1.1, C1.2 e C2.1 cambiano il salvataggio. Il piano (R12) chiede migrazioni provate prima dei cambi.
- **Come:** la mappa dei campi è `SAVE_SPLITS` in `tools/conformance_m4.py`: un campo nuovo va registrato lì e ripristinato prima di ciò che lo legge (`CLAUDE.md`, "Pitfalls").
- **File:** `tests/saves/` (nuovo), `tools/reference/combat.py` (`save_state`, `load_state`), `tools/conformance_m4.py`, `desktop/tests/`, `android/core/src/test/`.
- **Accettazione:** la copia della versione 1 si carica nel riferimento, in C++ e in Kotlin; un campo nuovo senza copia fa fallire la build.
- **Taglia:** M. **Dipende da:** niente. Issue: [progliodario/aethermoor#228](https://github.com/progliodario/aethermoor/issues/228).

##### B1.6 Lista di rilascio
- **Cosa:** `docs/dev/release-checklist.md`: ciò che serve per dire "Alpha 0.1 è pronta". CI verde; artefatti di prova scaricati; gioco provato su Windows, Linux e Android; copia di un salvataggio tra piattaforme; conferma del proprietario. Il piano (documenti 05 e 06) la cita come esistente: da questo batch esiste davvero.
- **File:** `docs/dev/release-checklist.md` (nuovo), `docs/plan/05-*.md`, `docs/plan/06-*.md`.
- **Accettazione:** il file esiste ed è linkato; `pytest` (documenti) verde.
- **Taglia:** S. **Dipende da:** niente. Issue: [progliodario/aethermoor#229](https://github.com/progliodario/aethermoor/issues/229).

#### B2 Il tempo che cambia i prezzi (8.4, voce 2)

##### B2.1 Il tempo che cambia i prezzi

> **Fatta (23 novembre 2026).** Come progettato, con due scelte: anche il prezzo di vendita sale (il bottegaio paga di più ciò che la
> pioggia rende raro), e la neve è una regione con il suo rincaro (`region_rise_pm`, Frostveil). Le merci sono `time.weather.weather_goods`.
- **Cosa:** con la pioggia le merci di campagna (cibo, legna, erbe) costano il 10% in più nei negozi; con la neve il 20%. Il valore viene da una tabella nei dati e il prezzo non scende mai sotto quello base. Un suggerimento lo dice la prima volta che piove.
- **Perché:** il tempo c'è (pioggia, neve, nebbia, notte, vento, temporali, stagioni), ma non cambia l'economia. È la voce 2 di 8.4 e la più piccola che collega due sistemi già fatti.
- **Come:** la regola va in `docs/spec/06-items.md` (prezzi) e `docs/spec/08-world-time.md` (tempo). Il calcolo è nel riferimento (`tools/reference/combat.py`). Gli scenari nuovi (`combat_rain_prices`, `combat_snow_prices`) vanno in `tools/conformance_m3.py`, dove stanno gli scenari dei negozi (`combat_market_days`, `combat_renown_prices`).
- **File:** `docs/spec/06-items.md`, `docs/spec/08-world-time.md`, `tools/reference/combat.py`, `tools/conformance_m3.py`, `data/base/hints.json`, `data/base/i18n/it/`, `data/base/i18n/en/`, `desktop/src/sim/world.cpp`, `android/core/src/main/kotlin/io/github/progliodario/aethermoor/core/sim/World.kt`.
- **Accettazione:** i nuovi scenari passano in C++ e Kotlin; `balance_report` resta a zero valori anomali; i testi esistono in IT ed EN; `make_facts` è aggiornato.
- **Rischi:** il numero (10% e 20%) è una mia scelta di design: il proprietario lo sente giocando e può chiedere di cambiarlo, perché è un numero in dati.
- **Taglia:** M. **Dipende da:** B1.4. Issue: [progliodario/aethermoor#230](https://github.com/progliodario/aethermoor/issues/230).

#### B3 Il mondo che si vede (8.4, voci 4 e 5)

##### B3.1 Viaggiatori che camminano
- **Cosa:** tra due fermate del percorso (`route`), il viaggiatore cammina sulla strada. La sua posizione si calcola dall'orologio del mondo, lungo un percorso di caselle di strada scritto nel `route` da `tools/make_caravan.py`. Non si salva nulla, e il viaggiatore non è mai solido.
- **Perché:** oggi Odo, Brannoc e Lark *compaiono* alla fermata del giorno (`docs/spec/07`, "Viaggiatori"). Il piano (M6) voleva carri che si vedono viaggiare.
- **Come:** il percorso è generato dallo strumento con una ricerca sulle caselle di strada con ordine fisso dei vicini, così i due client concordano. Scritto nei dati, non calcolato a runtime. La posizione è una funzione del tempo di mondo con aritmetica intera. Scenario `traveller_walks` a orari fissati, nel modulo dei viaggiatori (`tools/conformance_m4.py`, dove sta già `traveller_moves`).
- **File:** `docs/spec/07-quests-and-dialogue.md`, `docs/spec/09-worldgen.md`, `tools/make_caravan.py`, `tools/reference/worldtime.py`, `tools/conformance_m4.py`, `desktop/src/sim/world.cpp`, `desktop/src/sim/world_map.cpp`, `android/core/src/main/kotlin/io/github/progliodario/aethermoor/core/sim/World.kt`.
- **Accettazione:** lo scenario passa in C++ e Kotlin; la posizione a un orario dato è identica nei tre (riferimento, C++, Kotlin); il proprietario vede i viaggiatori sulla strada.
- **Rischi:** la ricerca dei percorsi deve essere deterministica e il risultato va scritto nei dati, altrimenti il gioco paga il costo a ogni avvio.
- **Taglia:** L. **Dipende da:** B1.4. Issue: [progliodario/aethermoor#231](https://github.com/progliodario/aethermoor/issues/231).
- **Fatto (24 novembre 2026).** Differenza dal progetto: il viaggiatore cammina in linea retta, non sulle caselle di strada. Le strade del
  mondo dipendono dal seme (sono rumore, spec 09), quindi un percorso scritto nei dati varrebbe per un solo mondo; e la tappa è un
  avamposto fatto a mano, raggiunto da strade diverse a ogni seme. Il viaggiatore resta alla tappa da un quarto a tre quarti del giorno
  (`walk` nei dati, scritto da `tools/make_caravan.py`), cammina al passo vicino alle tappe e cambia tappa a mezzanotte, a metà strada,
  dove nessuno lo vede. Scenario `traveller_walks` nei tre; il proprietario deve ancora vederlo sullo schermo.

##### B3.2 Paesani alla festa

> **Fatta (23 novembre 2026, terzo batch).** Come progettato, con due scelte: le persone non camminano, la condizione di presenza è calcolata
> quando sono generate (`when`, spec 09), e i vettori `worldgen_chunks` la controllano per ogni persona invece di uno scenario a parte; e i
> paesani partono per la festa dei vicini (come già dicevano i loro dialoghi), mentre ogni città della regione in festa ha tre ospiti in
> piazza (tre posti nuovi dei timbri delle città, carattere `2`).
- **Cosa:** il giorno di festa di una regione, i paesani dei villaggi vicini vanno alla locanda della città per la giornata. Sono residenti con una condizione (giorno di festa e regione) e non sono solidi.
- **Perché:** oggi il paesano augura buona festa e dice che "metà del villaggio è andata alla festa", ma non ci va nessuno (voce 5 di 8.4).
- **Come:** si riusa il meccanismo dei residenti (`when` e `role_when` nei dati di mondo). Nessuno stato nuovo nel salvataggio. Il vicinato si definisce nel generatore degli insediamenti.
- **File:** `docs/spec/07-quests-and-dialogue.md`, `docs/spec/09-worldgen.md`, `tools/make_settlers.py`, `tools/make_feasts.py`, `data/base/worlds/`, `tools/conformance_m4.py`.
- **Accettazione:** lo scenario `feast_gathering` passa in C++ e Kotlin; nel test il villaggio è vuoto il giorno di festa; il proprietario lo vede.
- **Taglia:** M. **Dipende da:** niente. Issue: [progliodario/aethermoor#232](https://github.com/progliodario/aethermoor/issues/232).

#### B4 Sfide a tempo (8.4, voce 3)

##### B4.1 Sfide a tempo

> **Fatta (23 novembre 2026, secondo batch).** Due scelte diverse dal progetto: una missione scaduta non si consegna più (non conta e non
> paga) invece di dare solo il premio senza il di più, così il "di più" è tutto il premio (il pezzo raro); e il giorno di inizio è un campo
> facoltativo del progresso (`day`), che i lettori vecchi ignorano: per la spec 12 un campo facoltativo non cambia la versione, quindi il
> salvataggio resta alla versione 1 e la sua copia congelata ha due casi in più (`timed_quests`). Le quattro prove sono di `make_trials.py`.
- **Cosa:** una missione può avere un limite di tempo in giorni di mondo (`time_limit_days`; un giorno dura 20 minuti, `docs/spec/08`). Consegnata in tempo dà un premio in più; scaduta, si può ricominciare. Quattro sfide, una per stagione, pagate con un pezzo raro. Il diario mostra i giorni che restano.
- **Perché:** chi ha finito tutto non ha una ragione per tornare in fretta. Le taglie, le cacce delle stagioni e le botteghe si ripetono già, ma senza fretta.
- **Come:** un campo nuovo nello schema della missione (`schemas/quest.schema.json`); la regola in `docs/spec/07`; il conteggio nel riferimento (`tools/reference/story.py`); il timer nel salvataggio (versione 2, con la copia di B1.5).
- **File:** `schemas/quest.schema.json`, `docs/spec/07`, `docs/spec/08`, `tools/reference/story.py`, `tools/conformance_m4.py`, `desktop/src/sim/story.cpp`, `desktop/src/app/main.cpp`, `android/core/src/main/kotlin/io/github/progliodario/aethermoor/core/sim/Story.kt`, `data/base/quests/`.
- **Accettazione:** `timed_in_time` e `timed_expired` passano in C++ e Kotlin; `validate_data` controlla il campo; il salvataggio versione 2 si carica dalla copia.
- **Dipende da:** B1.5. Taglia: L. Issue: [progliodario/aethermoor#233](https://github.com/progliodario/aethermoor/issues/233).

#### Decisione di G1 che serve per il periodo A breve

Le decisioni dalla sezione 8 che servono subito (Alpha 0.1, protezione del ramo, impostazioni del repository) sono raccolte nell'issue [progliodario/aethermoor#234](https://github.com/progliodario/aethermoor/issues/234), con la raccomandazione del programma per ciascuna.

### 5.2 A medio (C1-C6): verso Alpha 0.2 e Beta 0.5

**Obiettivo:** chiudere le consegne di M5 (thread di streaming), M6 (vita), M7 (compagni), M8 (progressione) e le misure di M2 su Android.

#### C1 Casa e oggetti

##### C1.1 Stanze del cottage
- **Cosa:** tre stanze in più per il cottage, comprate da un falegname di Fenwick (una persona nuova nei dati del mondo) con oro, legna e ferro. Una stanza è una zona della stessa mappa e dà posti per i mobili (`data/base/home.json`). Il salvataggio tiene l'insieme delle stanze.
- **Perché:** oggi c'è una casa sola, con sei posti per i mobili e quattro in giardino. È la voce 6 di 8.4.
- **File:** `data/base/home.json`, `data/base/furnishings/`, `schemas/home.schema.json`, `docs/spec/06-items.md`, `tools/make_home.py`, `tools/make_furnishings.py`, `desktop/src/sim/world.cpp`, `android/core/.../sim/World.kt`.
- **Accettazione:** vettori per l'acquisto e la posa dei mobili; la copia di salvataggio versione 2 si carica; i due client disegnano i posti nuovi; `balance_report` non cambia.
- **Dipende da:** B1.5. Taglia: M. Issue: [progliodario/aethermoor#235](https://github.com/progliodario/aethermoor/issues/235).
- **Fatto (24 novembre 2026).** Differenze dal progetto: le stanze sono già nella mappa (un annesso a est della casa, nel timbro del
  cottage), e comprarle non cambia le caselle: una stanza è dell'Ospite quando ha il suo flag della storia, e solo allora i suoi
  tappeti (un'arte per stanza) sono posti per i mobili. Così il salvataggio non ha un campo nuovo (i flag ci sono già) e non serve la
  versione 2. Il falegname si chiama Garrick (c'è già un venditore Hobb) e sta al cottage, accanto all'annesso, non a Fenwick: lì
  sarebbe entrato nei fotogrammi del test di fumo. Lo scenario `cottage_rooms` è in `tools/conformance_m3.py`, accanto a
  `furniture_home`; il proprietario deve ancora vedere l'annesso sullo schermo.

##### C1.2 Affissi scelti
- **Cosa:** all'incudine, per un pezzo con un affisso tirato a sorte, si può pagare (oro e un materiale raro) per vedere altri tre affissi del suo tipo e tenerne uno, una sola volta per pezzo. L'olio di tempra resta com'è.
- **Perché:** è la voce 8 di 8.4 e chiude la parte di M8 sugli affissi.
- **File:** `docs/spec/06-items.md`, `tools/make_affixes.py`, `tools/make_common_affixes.py`, `tools/reference/combat.py`, `tools/conformance_m5.py`, `desktop/src/sim/world.cpp`, `android/core/.../sim/World.kt`.
- **Accettazione:** lo scenario `affix_choice` (costo, tre offerte estratte in modo deterministico, una tenuta) passa in C++ e Kotlin; il salvataggio tiene il tiro scelto; `balance_report` a zero valori anomali.
- **Dipende da:** B1.5. Taglia: M. Issue: [progliodario/aethermoor#236](https://github.com/progliodario/aethermoor/issues/236).
- **Fatto (24 novembre 2026).** Differenze dal progetto: il prezzo è un oggetto, il prisma degli affissi (fatto all'incudine con un
  nucleo di golem, due polveri di stelle e due minerali di ferro, venduto a Ironspine per 300 monete), così si usa come l'olio di tempra;
  non c'è il limite di una volta per pezzo, perché ogni cambio costa un prisma. I "tipi" sono famiglie nei dati (`affix_family`): i
  quattro affissi di ognuno dei sei pezzi comuni (tre offerte, nessuna estrazione) e le sei coppie dello spadone e della piastra da
  cavaliere (tre estratte su cinque). Le offerte si guardano su una copia del flusso `loot`, quindi guardare non costa nulla. Lo
  scenario `affix_choice` è in `tools/conformance_m3.py` (dove sta `temper_affix`), con due salvataggi. Il pannello è la terza
  pagina di quello di creazione, nei due client; il proprietario deve ancora vederlo sullo schermo.

#### C2 Compagni

##### C2.1 Compagni scelti
- **Cosa:** fino a tre compagni: quello del protagonista e due altri, scelti tra quattro persone del mondo che la storia già conosce. La proposta è Odo, Brannoc, Lark e Corvin, sbloccate da un atto della storia. Il compagno attivo si sceglie nel menu del gruppo. Vanno completate le abilità di coppia della spec 18.
- **Perché:** è la voce 7 di 8.4. Oggi c'è un compagno per protagonista (spec 10). M7 chiede anche il party da tre e le abilità di coppia, che non risultano fatte.
- **Come:** la spec 10 si estende a un gruppo di tre; la regola di seguire e combattere resta la stessa per ciascun compagno. Il salvataggio tiene il gruppo e il compagno attivo (versione 2, con la copia di B1.5).
- **File:** `docs/spec/10-companions.md`, `docs/spec/18-protagonists.md`, `tools/make_companions.py`, `tools/reference/combat.py`, `data/base/companions/`, `desktop/src/sim/world.cpp`, `android/core/.../sim/World.kt`, `desktop/src/app/main.cpp`.
- **Accettazione:** lo scenario `party_of_three` passa in entrambi i client; le abilità di coppia sono nei vettori; il menu funziona con tastiera, mouse e tocco.
- **Rischi:** più compagni significano più combattimento: il bilancio va ricontrollato con `balance_report` (combattimenti facili, sempre).
- **Dipende da:** B1.5. Taglia: L. Issue: [progliodario/aethermoor#237](https://github.com/progliodario/aethermoor/issues/237).
- **Fatto (24 novembre 2026).** Differenze dal progetto: segue un compagno alla volta (il "compagno attivo" del progetto), gli altri
  aspettano, e nessun limite di tre; non c'è un menu del gruppo, ma un comando che passa al prossimo (`O`, il pulsante `Altro`), come i
  tag. I compagni nuovi non sono Odo, Brannoc, Lark e Corvin (sono persone, e i compagni sono piccole creature disegnate con l'arte delle
  creature), ma i quattro randagi del cottage, che il vecchio Tam lascia portare via: Biscotto (il cane rimasto dalla carovana di
  Odo), Gufetto, Furbo e Brace. Ognuno tiene il suo legame. Le abilità di coppia della spec 18 non ci sono: restano da progettare.
  Scrivendo i salvataggi del gruppo è venuto fuori che il riferimento Python non salvava il compagno; ora lo salva. Scenario
  `party_of_companions` con due salvataggi.

#### C3 Gideon

##### C3.1 Dungeon di Gideon
- **Cosa:** la base di Gideon viene attaccata da ondate di avventurieri: cinque ondate, tre stanze, due tipi di trappola, una ricompensa di materiali e un titolo. La modalità è specificata prima di essere scritta (spec 18 e spec 05). La variante ridotta è il ripiego previsto dalla roadmap (sezione 4, valvola 4).
- **Perché:** è la voce 9 di 8.4 e la modalità che manca a M9.
- **File:** `docs/spec/18-protagonists.md`, `docs/spec/05-combat-v1.md`, `data/base/enemies/` (avventurieri, nuovi), `tools/make_*.py`, `desktop/src/sim/`, `android/core/.../sim/`.
- **Accettazione:** la sezione di spec è scritta e approvata dal proprietario; i vettori coprono una partita intera; la modalità è raggiungibile dalla base di Gideon nel gioco del proprietario.
- **Rischi:** è la voce più grande del periodo medio, e la più facile da allargare. Il proprietario decide la portata dopo la spec.
- **Dipende da:** niente (prima la spec). Taglia: L (XL senza la variante ridotta). Issue: [progliodario/aethermoor#238](https://github.com/progliodario/aethermoor/issues/238).
- **Fatto (24 novembre 2026), forma ridotta scelta dal proprietario.** Differenze dalla proposta: il Dungeon non è il trono della
  Cenere ma un sito nuovo accanto al Santuario della Cenere (un landmark e un timbro); le trappole non si posano come mobili ma sono
  fosse fisse del Dungeon, armate da Grubb in cambio di materiali (un flag per tipo); gli avventurieri non hanno abilità proprie (il
  chierico non cura), solo statistiche e l'arciere un attacco da quattro caselle, e marciano verso il nucleo finché il giocatore non si
  avvicina. Una difesa non si salva. Scenari `defense_won` e `defense_lost`; il proprietario deve ancora vederla sullo schermo.

#### C4 Prestazioni su Android e thread di streaming

##### C4.1 Streaming con thread
- **Cosa:** i chunk davanti al giocatore si generano su un thread di lavoro (desktop: un thread; Android: un thread in background). Il thread principale li consuma in un punto fisso del tick, in un ordine fisso: così la simulazione resta deterministica.
- **Perché:** è la consegna di M5 che manca (il piano la chiedeva, oggi la generazione è sul thread principale) e il rimedio del rischio R4 (prestazioni su mobile).
- **File:** `desktop/src/core/`, `desktop/src/data/world_data.cpp`, `desktop/src/app/main.cpp`, `android/core/.../WorldGen.kt`, `android/game/.../AethermoorGame.kt`, `docs/spec/03-systems-order.md`, `docs/spec/09-worldgen.md`.
- **Accettazione:** i vettori `chunk_window` e `worldgen_chunks` restano identici in entrambi i client; un test di tempo di frame nei test JVM; lo smoke test del desktop è verde; un job ThreadSanitizer gira di notte.
- **Rischi:** i bug di concorrenza non si vedono senza compilatore: la mitigazione è il punto di consegna fisso e il job di sanitizzazione. Il determinismo è difeso dai vettori.
- **Dipende da:** B1.4. Taglia: L. Issue: [progliodario/aethermoor#239](https://github.com/progliodario/aethermoor/issues/239).
- **Fatto (25 novembre 2026).** Differenza dal progetto: il thread non consegna la finestra, ma prepara l'anello dei 24 chunk a distanza
  3, chiesto dopo ogni spostamento della finestra; `keep_around`/`keepAround` prende un chunk pronto e genera subito quelli che non lo sono,
  nello stesso punto del tick di prima. Così il determinismo non dipende dal thread (la generazione è una funzione pura) e i vettori non
  cambiano. Desktop: un `std::thread` per archivio, con mutex e due variabili di condizione; Android: un esecutore a un thread, demone, per
  tutta l'app. Test: `[streaming]` in `desktop/tests/performance_test.cpp` e `theChunksMadeAheadOnAThreadAreTheChunksMadeAtOnce` in
  `PerformanceTest.kt`; il job notturno `thread sanitizer (streaming)` (opzioni CMake `AETHER_HEADLESS_ONLY` e `AETHER_WERROR`).

##### C4.2 Misure su Android
- **Cosa:** (a) test di prestazione nei test JVM, con budget ampi per la generazione dei chunk e per il tick; (b) un test strumentato di notte sull'emulatore (API 30 e 34): avvio, rotazione, pausa e ripresa, stato conservato; (c) gli atlanti si ricostruiscono dalla cache su CPU quando il contesto GL si perde (rischio R6); (d) il proprietario misura i frame su un telefono con la lista di rilascio.
- **Perché:** M2 e M5 chiedono 60 FPS e la prova della perdita del contesto GL, che oggi non sono misurati. Il rischio R4 è "non misurato" nel piano.
- **File:** `android/core/src/test/`, `android/app/src/androidTest/` (nuovo), `.github/workflows/nightly.yml` (nuovo), `android/game/.../TextureCache.kt`, `docs/dev/release-checklist.md`, `docs/design/performance.md` (nuovo).
- **Accettazione:** il workflow notturno è verde; i numeri stanno in `docs/design/performance.md`, scritti a partire dall'output della CI; i numeri del telefono del proprietario sono registrati nello stesso file.
- **Rischi:** l'emulatore non è un telefono. I numeri di CI servono per confrontare, non per dichiarare "60 FPS".
- **Dipende da:** C4.1 per i numeri finali. Taglia: M. Issue: [progliodario/aethermoor#240](https://github.com/progliodario/aethermoor/issues/240).
- **Fatto in parte (25 novembre 2026).** (a) `desktop/tests/performance_test.cpp` e `core/PerformanceTest.kt`: 300 chunk e 600 tick con
  budget di 25 ms e 4 ms, numeri stampati dalla CI. (b) `.github/workflows/nightly.yml` con `android/app/src/androidTest/.../LifecycleTest.kt`
  su API 30 e 34; gira anche sulle PR che cambiano il workflow o il test. Differenza dal progetto: il test non conserva una partita (parte
  dalla schermata del titolo) ma controlla che attività e gioco restino gli stessi e che le texture siano gestite. (c) Le texture dell'arte
  e del font sono gestite (`PixmapTextureData` con il pixmap tenuto). (d) Manca: i numeri del telefono del proprietario, in
  `docs/design/performance.md`.

#### C5 Una settimana di gioco

##### C5.1 Una settimana di gioco
- **Cosa:** una settimana di tempo di mondo a script (coltivare, cucinare, vendere, cacciare, una festa, cambi di tempo, viaggiatori) nel riferimento e nei due client, con invarianti: l'oro non va mai sotto zero, nessuna missione resta bloccata, i prezzi restano nei limiti, il salvataggio fa il giro completo. In più una tabella che collega i nomi delle suite della M1 e della M6 (nel piano) ai file reali (`docs/design/suites.md`).
- **Perché:** la M6 chiede "una settimana di gioco senza anomalie", e non esiste. I nomi delle suite del piano (`crafting_quality`, `economy_price`, `time_season`, `weather`, `stats_derived`, `xp_table`, `condition_eval`) non corrispondono ai file: i casi ci sono, con altri nomi.
- **File:** `tools/conformance_m5.py`, `tools/reference/`, `desktop/tests/conformance_test.cpp`, `android/core/src/test/`, `tools/make_suites_map.py` (nuovo).
- **Accettazione:** lo scenario `week_of_play` passa nelle tre implementazioni; `docs/design/suites.md` è generato e controllato in CI.
- **Dipende da:** B2.1 e B3.1. Taglia: M. Issue: [progliodario/aethermoor#241](https://github.com/progliodario/aethermoor/issues/241).
- **Fatto (24 novembre 2026).** Lo scenario `week_of_play` è nel modulo dei combattimenti (`tools/conformance_m3.py`, che ha già
  coltivare, cucinare e negozi), non in un `conformance_m5.py` nuovo: il suo caso è nella suite `combat`, eseguita dai due client, e
  due suoi salvataggi sono nelle copie congelate. Le invarianti sono un test del riferimento (`test_a_week_of_play_keeps_its_invariants`).
  Scrivendolo è venuto fuori un difetto: le missioni che chiedono oggetti si contavano solo a un'uccisione, a una parola o a una cassa;
  ora la borsa si conta a ogni tick (spec 07), nei tre.

#### C6 Musica e ambiente (bloccata)

##### C6.1 Sintetizzatore
- **Cosa:** un sintetizzatore costruito su rumore filtrato, per riaccendere musica e ambiente.
- **Perché:** il proprietario ha trovato la musica e l'ambiente sgradevoli. Restano spenti (`CLAUDE.md`): non si riaccendono senza il suo sì.
- **File (solo dopo il sì):** `docs/spec/14-audio.md`, `tools/make_sfx.py`, `tools/compose.py` (non si esegue senza il sì).
- **Accettazione:** il proprietario ha ascoltato un campione e ha detto sì. Solo allora la spec 14 e i due client.
- **Taglia:** M. **Bloccata** dal proprietario. Issue: [progliodario/aethermoor#242](https://github.com/progliodario/aethermoor/issues/242).

### 5.3 Contenuti (D1-D4): release 0.6, 0.7, 0.8, 0.9

**Obiettivo:** i protagonisti 1-8 completi, a ondate, con il template della roadmap (M9, punti 1-7). Un protagonista per volta, due per ondata, una release per ondata.

**Il modello di lavoro per ogni protagonista** (dalla roadmap, M9):

1. Specifica della storia laterale in `docs/spec/18-protagonists.md` (`/spec-change`).
2. Storia laterale: tre missioni, con un finale che il giocatore sceglie con un dialogo. Proposta: il finale cambia un titolo o un oggetto, non il finale della trama principale.
3. Arte (ricette e rig) solo se servono personaggi o luoghi nuovi.
4. Audio: solo effetti sonori (musica e ambiente restano spenti).
5. Testi IT ed EN.
6. Bilanciamento: `balance_report` a zero valori anomali; scenario di giocata.
7. Test di regressione: i test che contano i contenuti (desktop e Android) si aggiornano nello stesso batch.

#### D1 Ondata 9a

> **Fatta (23 novembre 2026, quarto batch).** Le due storie laterali sono di `tools/make_side_stories.py` (spec 18, "Side stories"), con
> due persone nuove ad Aldermere; un test (`tools/tests/test_side_stories.py`) le gioca dall'inizio a ciascuno dei due finali con il
> riferimento, al posto di uno scenario dei vettori (le storie usano solo condizioni ed effetti già coperti dai vettori `story`). Il
> controllo di Verdalis: tre sotterranei (Grunmoor Barrow, Mossveil Cellar e Mint Hollow, come li chiama il catalogo), più dei due chiesti; le
> sue creature vanno dal livello 1 al 4 e non al 12, perché i livelli salgono con il pericolo delle altre regioni (spec 09): la cosa
> resta così, i combattimenti devono restare facili.
- **Cosa:** per Ren e Haruka, una storia laterale ciascuno (tre missioni, un finale a scelta). Per Ren va controllato che Verdalis sia completa (livelli da 1 a 12, due sotterranei) confrontando il catalogo.
- **Perché:** M9 chiede altre storie per protagonista; la prima ondata è la più vicina a un'esperienza completa.
- **File:** `data/base/quests/`, `data/base/dialogues/`, `data/base/i18n/`, `docs/spec/18-protagonists.md`, `tools/make_stories.py` (o un generatore nuovo), `desktop/tests/`, `android/core/src/test/`.
- **Accettazione:** ciascuno dei due è giocabile dall'inizio alla fine nello scenario; il grafo delle missioni è raggiungibile (`validate_data`); `balance_report` a zero valori anomali.
- **Dipende da:** B1.4 e C5.1. Taglia: XL (per protagonista). Issue: [progliodario/aethermoor#243](https://github.com/progliodario/aethermoor/issues/243).

#### D2 Ondata 9b

> **Fatta (23 novembre 2026, quinto batch).** Con lo stesso generatore e lo stesso test di D1: Daichi ("The Bucket Brigade", la capitana
> Wren Hale) e Sakura ("The Unfinished Proof", l'astronoma Ottilie Brask), tutte e due ad Aldermere.
- **Cosa:** lo stesso modello per Daichi (Ironspine) e Sakura (Lumeria).
- **Dipende da:** D1. Taglia: XL (per protagonista). Issue: [progliodario/aethermoor#244](https://github.com/progliodario/aethermoor/issues/244).

#### D3 Ondata 9c

> **Fatta (23 novembre 2026, quinto batch, con D2).** Marco ("Salt of the Earth", la cuoca Bruna Calder) e Yuki ("The Honest Thief",
> la custode Ilse Marrow), ad Aldermere, con lo stesso generatore e lo stesso test.
- **Cosa:** lo stesso modello per Marco (Tidehaven) e Yuki (Sunscar).
- **Dipende da:** D2. Taglia: XL (per protagonista). Issue: [progliodario/aethermoor#245](https://github.com/progliodario/aethermoor/issues/245).

#### D4 Ondata 9d

> **Fatta (23 novembre 2026, sesto batch).** Lena ("The Last Diagnosis", il dottor Aurel Finch) e Gideon ("The Debts of a King", la
> fornaia Dorrit Ash), ad Aldermere. La storia di Gideon non dipende dal Dungeon (C3.1): racconta il suo passato di re attraverso i
> profughi delle Terre di Cenere, e il Dungeon resta una voce a sé.
- **Cosa:** lo stesso modello per Lena (Frostveil) e Gideon (Ashen Wastes). Per Gideon, la storia laterale si lega a C3.1 (il Dungeon) oppure alla sua variante ridotta.
- **Dipende da:** D3 e C3.1. Taglia: XL (per protagonista). Issue: [progliodario/aethermoor#246](https://github.com/progliodario/aethermoor/issues/246).

### 5.4 Verso la 1.0 (E1-E4)

**Obiettivo:** le consegne di M10 (rifinitura) e M11 (pacchetti, documentazione), con le decisioni del proprietario sulla firma e sulla pubblicazione.

#### E1 Qualità, log e lingue

##### E1.1 Modalità qualità
- **Cosa:** un'impostazione di qualità grafica (bassa, normale, alta): numero di passaggi di luce, ombre morbide, dimensione delle texture cotte, effetti. Al primo avvio il gioco propone la qualità in base al dispositivo. Un budget di memoria controllato dai test su desktop e Android.
- **Perché:** M10 la chiede; oggi non c'è. Serve per i telefoni deboli (rischio R4).
- **File:** `docs/spec/16-input.md`, `docs/spec/13-vector-art.md`, `desktop/src/app/main.cpp`, `android/game/.../AethermoorGame.kt`.
- **Accettazione:** l'impostazione è nel menu opzioni e si salva; il test del budget passa su entrambi i client.
- **Dipende da:** C4.2. Taglia: M. Issue: [progliodario/aethermoor#247](https://github.com/progliodario/aethermoor/issues/247).
- **Fatto (25 novembre 2026).** Spec 13 "Quality": tre livelli con il bucket più grande (64, 128, 256), l'acqua che si muove, gli angoli
  del terreno e le ombre lunghe; il budget delle texture (32, 128, 512 MiB) è controllato dal riferimento e dai due client. Differenza dal
  progetto: non ci sono "passaggi di luce" o "ombre morbide" da scalare (le luci sono un velo solo); la qualità tocca ciò che costa davvero.
  Al primo avvio il gioco sceglie (desktop alta, Android dalla memoria) e la scelta si vede nelle impostazioni.

##### E1.2 Log dei crash
- **Cosa:** a un errore non gestito, il gioco scrive un file di testo con l'errore e gli ultimi messaggi nella cartella dei salvataggi. Il menu opzioni lo apre o lo copia. Nessuna rete, nessun invio (`CLAUDE.md`, regola 8).
- **Perché:** M10 lo chiede ("crash reporter locale"). Il proprietario lo usa per segnalare i problemi che vede.
- **File:** `desktop/src/app/main.cpp`, `android/game/.../AethermoorGame.kt`, `docs/spec/12-save-format.md`.
- **Accettazione:** un errore forzato in un test scrive il file su entrambi i client; niente lascia il dispositivo.
- **Taglia:** S. Issue: [progliodario/aethermoor#248](https://github.com/progliodario/aethermoor/issues/248).
- **Fatto (24 novembre 2026).** Differenza dal progetto: Android non ha un menu delle opzioni, quindi il log non si apre da lì. All'avvio
  dopo l'errore la schermata del titolo, nei due client, dice una volta dov'è il file (rinominato `crash_last.txt`), e Android lo copia
  negli appunti. Il log tiene gli ultimi 40 avvisi mostrati. I test (`desktop/tests/crash_log_test.cpp`, `CrashLogTest.kt`) forzano un
  errore e rileggono il file.

##### E1.3 Traduzioni e accessibilità
- **Cosa:** rileggere tutti i testi in italiano e in inglese contro la guida al tono e correggere quello che non torna; scrivere `docs/dev/accessibility.md` (contrasto, dimensione del testo, l'opzione dei lampi, il tocco con una mano, un controllo per il daltonismo) e testare ciò che si può testare.
- **Perché:** M10 chiede la localizzazione revisionata e la checklist di accessibilità. Oggi il controllo è automatico (`check_translations`), la revisione no.
- **File:** `data/base/i18n/`, `docs/dev/accessibility.md` (nuovo), `docs/glossary.md`.
- **Accettazione:** `check_translations` dà 0 testi da guardare; la checklist è completa e linkata dai README.
- **Taglia:** M. Issue: [progliodario/aethermoor#249](https://github.com/progliodario/aethermoor/issues/249).
- **Fatto (24 novembre 2026).** Differenza dal progetto: la rilettura di tutti i testi non è stata fatta a mano da una persona; al suo
  posto il controllo delle traduzioni tiene ora i termini del glossario in ogni testo (dodici termini, `GLOSSARY` di
  `tools/check_translations.py`), e i testi che li usano in un altro senso sono elencati dopo uno sguardo. La lista di controllo
  (`docs/dev/accessibility.md`) dice che cosa c'è e che cosa manca; il contrasto dei testi è controllato da un test, il controllo per il
  daltonismo è la differenza di luminosità tra gli stati che il colore distingue. Il glossario è aggiornato.

#### E2 Comandi su Android

##### E2.1 Rimappatura su Android
- **Cosa:** il desktop ha la rimappatura dei tasti (F4). Android ne ha bisogno sua: posizione e dimensione dei pulsanti sul tocco, salvate nelle impostazioni, con un ripristino.
- **Perché:** M10 chiede la rimappatura e l'editor del layout tattile; su Android non ci sono.
- **File:** `docs/spec/16-input.md`, `android/game/.../InputController.kt`, `android/game/.../AethermoorGame.kt`.
- **Accettazione:** l'editor si apre dalle impostazioni; il layout sopravvive a un riavvio e a una rotazione.
- **Dipende da:** B1.2. Taglia: L. Issue: [progliodario/aethermoor#250](https://github.com/progliodario/aethermoor/issues/250).
- **Fatto (25 novembre 2026).** Differenza dal progetto: l'editor si apre dal pulsante `Disposizione` del diario (Android non ha un menu
  delle impostazioni) e muove i quattro pulsanti d'azione (Schivata, Colpo, Parata, Analizza), non quelli dei pannelli. La logica è in
  `core/TouchLayout.kt` (testata: il file delle impostazioni, la rotazione, i bordi dello schermo); la disposizione è in millesimi dello
  schermo, quindi resta dopo una rotazione. Non provato sullo schermo: lo prova il proprietario.

##### E2.2 Controller su Android
- **Cosa:** il piano (documento 04) dice che il controller su Android non c'è. Prima si verifica il codice (`InputController`), poi si mappa un controller con le stesse azioni del desktop (spec 16).
- **Perché:** M7 chiede "touch e controller" per i comandi dei compagni.
- **File:** `docs/spec/16-input.md`, `android/game/.../InputController.kt`.
- **Accettazione:** un controller gioca su Android con le stesse azioni e gli stessi tasti del desktop.
- **Taglia:** M. Issue: [progliodario/aethermoor#251](https://github.com/progliodario/aethermoor/issues/251).
- **Fatto (25 novembre 2026).** `game/GamePad.kt` con gdx-controllers 2.2.4: il primo controller collegato; i pulsanti dei pannelli
  arrivano al gioco come i tasti della tastiera per la stessa azione (`PadInput`), quelli del combattimento passano da `InputController.read`.
  Sul titolo `B` non fa nulla (Indietro uscirebbe dall'app). Non provato su un controller vero: lo prova il proprietario.

#### E3 Pacchetti e firma

##### E3.1 Pipeline di rilascio
- **Cosa:** su un tag `v*`: uno zip per Windows, un tar.gz per Linux (AppImage più avanti), l'APK o l'AAB per Android, `SHA256SUMS`, un SBOM e una bozza di release con i file allegati. La lista di rilascio (B1.6) va seguita.
- **Perché:** M11. Oggi `release.yml` crea solo la bozza, senza file.
- **File:** `.github/workflows/release.yml`, `.github/workflows/ci-desktop.yml`, `.github/workflows/ci-android.yml`, `docs/dev/release-checklist.md`.
- **Accettazione:** un tag di prova produce una bozza con tutti i file; i checksum corrispondono.
- **Dipende da:** B1.6. Taglia: L. Issue: [progliodario/aethermoor#252](https://github.com/progliodario/aethermoor/issues/252).
- **Fatto (25 novembre 2026).** `release.yml` chiama `ci-desktop` e `ci-android` (ora `workflow_call`), controlla che il tag sia la versione
  di `project.json`, scrive `SHA256SUMS` e l'SBOM SPDX (`tools/licenses.py --sbom`), ricontrolla le somme e crea la bozza con i file; a mano
  fa una prova senza bozza (artefatto `release-files`). Differenza dal progetto: niente AppImage e l'APK è quello di debug finché la firma
  (E3.2) non c'è. Il tag di prova lo spinge il proprietario quando vuole: è un'azione pubblica.

##### E3.2 Firma del codice
- **Cosa:** Windows: SignPath (gratuito per i progetti open source), richiesto dal proprietario. Android: la chiave la custodisce il proprietario e la passa al workflow come segreto di GitHub, mai nel repository (`CLAUDE.md`, regola 8).
- **Perché:** M11 chiede pacchetti firmati; il proprietario decide la custodia.
- **File:** `.github/workflows/release.yml`.
- **Accettazione:** il proprietario ha fatto la domanda e ha impostato i segreti; il workflow firma i file.
- **Dipende da:** E3.1 e una decisione del proprietario (sezione 8). Issue: [progliodario/aethermoor#253](https://github.com/progliodario/aethermoor/issues/253).

#### E4 Mod e pubblicazione

##### E4.1 Documentazione per i mod

> **Fatta (24 novembre 2026, sesto batch, con D4).** Come progettato. Il mod di esempio è una creatura (lo slime di miele) e una missione,
> con i testi nelle due lingue; il validatore accetta una cartella anche fuori dal repository e la controlla sopra i pacchetti di
> `depends`. Caricare i mod nel gioco resta dopo l'1.0 (F1): la documentazione lo dice.
- **Cosa:** completare `docs/modding/`; `tools/validate_data.py` accetta una cartella di pacchetto sulla riga di comando; un mod di esempio (una creatura e una missione) è validato in CI.
- **Perché:** M11 chiede la documentazione per chi fa mod. Oggi il validatore controlla solo il pacchetto base.
- **File:** `docs/modding/README.md`, `tools/validate_data.py`, `examples/mod-example/` (nuovo), `.github/workflows/ci-data.yml`.
- **Accettazione:** chi non conosce il progetto aggiunge una creatura seguendo solo la documentazione; il mod di esempio passa il validatore in CI.
- **Taglia:** M. Issue: [progliodario/aethermoor#254](https://github.com/progliodario/aethermoor/issues/254).

##### E4.2 Pagina di download
- **Cosa:** una pagina dove scaricare i pacchetti e leggere la documentazione. Due strade: GitHub Pages dalla cartella `docs/` (il proprietario attiva Pages), oppure itch.io (account del proprietario). Il programma prepara il sorgente; il proprietario decide il luogo.
- **Perché:** M11.
- **File:** `docs/` (sorgente del sito), `.github/workflows/` (un job di Pages, nuovo).
- **Accettazione:** il proprietario ha scelto il luogo; il sorgente si costruisce in CI.
- **Dipende da:** E3.1. Taglia: M. Issue: [progliodario/aethermoor#255](https://github.com/progliodario/aethermoor/issues/255).

### 5.5 Dopo la 1.0 (F1)

##### F1 Dopo la 1.0
L'elenco di M12+, come unica issue di ombrello. Ogni voce diventa una sua issue quando si comincia.

- Protagonisti 9 e 10 (Slime, Aurelia); "Tre Re" (tre re della storia); aste; fotografia; nuove regioni e nuovi sotterranei; un editor visuale dei dati; Flathub; Steam (decisione del proprietario); nuove lingue.
- **Avvertenza:** la "validazione online" della roadmap (M12+) non deve aggiungere una rete al gioco (`CLAUDE.md`, regola 8). Se si fa, è uno strumento web separato, fuori dal gioco, e lo decide il proprietario.
- **Taglia:** XL. Issue: [progliodario/aethermoor#256](https://github.com/progliodario/aethermoor/issues/256).

## 6. Ordine, dipendenze e porte di rilascio

### 6.1 Ordine

```text
B0 (ora) ──► B1 fondamenta ──► B2 prezzi ──► B3 viaggiatori e festa ──► B4 sfide a tempo
                 │                 │                 │
                 │                 └──────┬──────────┘
                 │                        ▼
                 │              C5 una settimana di gioco ──► Alpha 0.2
                 ▼
  C1 casa e affissi ──► C2 compagni ──► Beta 0.5
  C3 Dungeon di Gideon ─────────────────────────────┐
  C4 thread e misure su Android ────────────────────┤
                                                    ▼
                     D1 ─► D2 ─► D3 ─► D4 (release 0.6 ... 0.9)
                                                    ▼
          E1 qualità · E2 comandi Android · E3 pacchetti e firma · E4 mod e sito
                                                    ▼
                                                  1.0
```

Due tracce possono correre in parallelo (come dice la roadmap, sezione 3): i **contenuti** (D) se i sistemi sono stabili, e i **sistemi** (B, C, E). Le due tracce non toccano gli stessi file, salvo la spec dei protagonisti.

### 6.2 Dipendenze

| Se si fa | Prima serve |
|---|---|
| B4.1, C1.1, C1.2, C2.1 (cambi di salvataggio) | B1.5 (migrazioni provate) |
| qualsiasi regola nuova | B1.4 (matrice di parità) |
| E2.1 (editor del tocco) | B1.2 (spec 15) |
| C4.2 (misure su Android) | C4.1 (thread) per i numeri finali |
| C5.1 (una settimana di gioco) | B2.1 e B3.1 |
| D4 (Gideon) | C3.1 (Dungeon o variante ridotta) |
| E3.2 (firma) | E3.1 e il sì del proprietario |
| 1.0 | E1-E4, C4.2, decisioni di G1 |

### 6.3 Porte di rilascio

| Release | Gate (tutto vero prima di proporla) |
|---|---|
| **Alpha 0.1** (M4) | B1.6 fatta; CI verde; artefatti di prova scaricati; gioco provato dal proprietario; decisione G1 presa |
| **Alpha 0.2** (M6) | B2.1, B3.1, B3.2, C5.1 fatte; nessuna anomalia nella settimana di gioco |
| **Beta 0.5** (M8) | C1.2, C2.1, B4.1 fatte; decisione su Hardcore presa (G1) |
| **0.6 - 0.9** (M9) | D1-D4 in ordine, ognuna con il suo gate; D4 con C3.1 o la sua variante ridotta |
| **1.0** (M11) | C4.2 con i numeri del telefono del proprietario; E1-E4 fatte; decisioni di G1 su firma, licenza, nome, classificazione e distribuzione; lista di rilascio su 3 PC e 3 telefoni |

**Valvole di portata** (roadmap, sezione 4), nell'ordine: protagonisti 6-8 a 1.1-1.3; minigiochi extra; meteo estremo; Dungeon di Gideon ridotto (C3.1); viaggio rapido con le carovane; seconda lingua; base a slot. Si usano solo se il proprietario lo decide o se la data della release lo impone.

## 7. Ciò che manca rispetto al piano originale

Questo elenco confronta le consegne dei documenti 06 (M0-M12) con lo stato reale. Non cambia il piano originale: lo rende verificabile.

| Milestone | Consegna del piano | Stato oggi | Dove |
|---|---|---|---|
| M0 | tag `v0.0.1` | non creato | G1 |
| M2 | prova della perdita del contesto GL su Android | non provata | C4.2 |
| M2 | rotazione Android senza perdita di stato; 60 FPS nello scenario di prestazione | non misurati | C4.2 |
| M2 | golden con tolleranza sulle tre piattaforme | c'è la suite `raster` e il controllo dei fotogrammi del desktop; manca il confronto su Android | C4.2 |
| M4 | schermate dichiarative (ADR 0008) | non fatte: le schermate sono nel codice | B1.2 (ADR 0014) |
| M4 | tema "Finestra di sistema" | non dichiarato come tema | B1.2 |
| M4 | cambio di lingua a caldo | i due client hanno una scelta della lingua; il cambio a caldo va provato dal proprietario | checklist (B1.6) |
| M5 | streaming dei chunk con thread di lavoro | non fatto: la generazione è sul thread principale | C4.1 |
| M5 | persistenza dei delta per chunk | non fatta: il piano la rimandava alla reincarnazione (`docs/spec/12`) | G1: raccomandazione, non serve (sezione 8) |
| M5 | prestazioni: tempo di generazione entro budget, 60 FPS | non misurate | C4.2 |
| M6 | carri che si vedono viaggiare | non fatto | B3.1 |
| M6 | paesani che vanno alla festa | non fatto | B3.2 |
| M6 | scenario "una settimana di gioco senza anomalie" | non esiste | C5.1 |
| M6 | suite con i nomi del piano (`crafting_quality`, `economy_price`, `time_season`, `weather`) | i casi ci sono con altri nomi; la corrispondenza non è scritta | C5.1 |
| M7 | party da tre, abilità di coppia | non risulta fatto: c'è un compagno per protagonista | C2.1 |
| M7 | controller per i comandi dei compagni | non verificato; il piano lo dà come mancante | E2.2 |
| M8 | difficoltà e Hardcore | non fatte. Hardcore va contro la regola della facilità | G1: raccomandazione (sezione 8) |
| M8 | alberi di abilità con doni e classi | i doni ci sono; le classi no | G1: conferma che i doni sostituiscono le classi |
| M8 | affissi che si scelgono | non fatto | C1.2 |
| M9 | altre storie per protagonista | non fatte | D1-D4 |
| M9 | modalità Dungeon di Gideon | non fatta | C3.1 |
| M10 | modalità qualità; effetti visivi completi | non fatte | E1.1 |
| M10 | log dei crash in locale | non fatto | E1.2 |
| M10 | rimappatura e editor del layout tattile | la rimappatura è solo sul desktop; l'editor non c'è | E2.1 |
| M10 | localizzazione revisionata; checklist di accessibilità | il controllo automatico c'è; la revisione e la checklist no | E1.3 |
| M11 | pacchetti firmati; pagina di download; documentazione per i mod | non fatti | E3, E4 |

## 8. Decisioni del proprietario

Sono le sole cose che il programma non può decidere da solo. Per ciascuna, la raccomandazione: se il proprietario non risponde, il programma la usa, e lo scrive nella PR interessata.

| # | Decisione | Raccomandazione del programma |
|---|---|---|
| 1 | Pubblicare Alpha 0.1 (tag e pacchetti) | dopo B1.6, CI verde e una prova completa del proprietario; non prima |
| 2 | Protezione del ramo `main` (oggi assente) | attivarla con "CI obbligatoria" e senza revisione obbligatoria: il proprietario ha autorizzato Claude a unire con la CI verde, e `ship.py` deve poterlo fare |
| 3 | Wiki del repository (oggi attiva; il piano la voleva spenta) | spegnerla |
| 4 | Merge commit (oggi consentito) | spegnerlo: solo squash, come dice `CLAUDE.md` |
| 5 | Cancellazione dei rami dopo il merge (oggi spenta) | accenderla (`ship.py` cancella già il ramo: l'impostazione è una rete di sicurezza) |
| 6 | Discussions (oggi spente) | lasciarle spente: il modulo di segnalazione non le usa più |
| 7 | Alert di vulnerabilità e aggiornamenti di sicurezza di Dependabot (oggi spenti) | accenderli: sono gratuiti e non cambiano il codice da soli |
| 8 | Licenza dei contenuti CC BY-SA 4.0 (proposta D13) | confermarla prima della prima release pubblica (`LICENSE-CONTENT.md` lo dice) |
| 9 | Nome del gioco ("Aethermoor", provvisorio, `name_is_provisional` in `project.json`) | decidere prima dell'Alpha 0.1; il nome vive in `data/base/pack.json` e `project.json` |
| 10 | Classificazione PEGI 12 / Teen (proposta in `CONTRIBUTING.md`) | confermarla |
| 11 | Distribuzione | GitHub Releases e itch.io per primi; Play Store, Flathub e Steam dopo |
| 12 | Firma: SignPath per Windows, chiave Android | il proprietario fa la domanda a SignPath e custodisce la chiave (E3.2) |
| 13 | Modalità Hardcore (M8) | non farla come modalità obbligatoria; opzionale solo se il proprietario la vuole, senza toccare il bilanciamento di base |
| 14 | Classi (M8) | confermare che i doni dei protagonisti le sostituiscono |
| 15 | Delta dei chunk nel salvataggio (M5) | confermare che non servono: il mondo è rigenerato dal seme e i nodi raccolti tornano con il respawn (`docs/spec/08`) |
| 16 | Musica e ambiente | restano spenti; il sintetizzatore (C6.1) solo con il sì |
| 17 | Validazione online (M12+) | uno strumento web separato, fuori dal gioco, oppure niente |
| 18 | Valvole di portata (roadmap, sezione 4) | accettarle nell'ordine indicato, se servono alla data di una release |
| 19 | Forma del Dungeon di Gideon (C3.1) | **decisa il 24 novembre 2026: la forma ridotta**, fatta nella PR #269 |

Tutte le decisioni sono raccolte in [progliodario/aethermoor#234](https://github.com/progliodario/aethermoor/issues/234).

## 9. Organizzazione su GitHub

**Milestone** (cinque, una per periodo):

| Milestone | Voci | Issue |
|---|---|---|
| A breve (B1-B4) | B1.1-B1.6, B2.1, B3.1, B3.2, B4.1, G1 | [progliodario/aethermoor#224](https://github.com/progliodario/aethermoor/issues/224)-[progliodario/aethermoor#234](https://github.com/progliodario/aethermoor/issues/234) |
| A medio (C1-C6): Alpha 0.2 e Beta 0.5 | C1.1-C1.2, C2.1, C3.1, C4.1, C4.2, C5.1, C6.1 | [progliodario/aethermoor#235](https://github.com/progliodario/aethermoor/issues/235)-[progliodario/aethermoor#242](https://github.com/progliodario/aethermoor/issues/242) |
| Contenuti (D1-D4): 0.6-0.9 (chiusa il 24 novembre 2026: tutte le voci fatte) | D1-D4 | [progliodario/aethermoor#243](https://github.com/progliodario/aethermoor/issues/243)-[progliodario/aethermoor#246](https://github.com/progliodario/aethermoor/issues/246) |
| Verso la 1.0 (E1-E4) | E1.1-E1.3, E2.1-E2.2, E3.1-E3.2, E4.1-E4.2 | [progliodario/aethermoor#247](https://github.com/progliodario/aethermoor/issues/247)-[progliodario/aethermoor#255](https://github.com/progliodario/aethermoor/issues/255) |
| Dopo la 1.0 (F) | F1 | [progliodario/aethermoor#256](https://github.com/progliodario/aethermoor/issues/256) |

**Label**: quelle che esistono già (`type:*`, `area:*`, `priority:*`, `blocked`, `needs-design`, `accessibility`), più una nuova: `owner-decision` (le decisioni del proprietario, G1 e le voci che aspettano un suo sì). Il sorgente è `.github/labels.json`.

**Ciclo di una voce**: la issue nasce con la voce; il batch che la fa dice `Closes #N` nella descrizione della PR; al merge la issue si chiude; la milestone mostra l'avanzamento.

**Progetto**: non è stata creata una board di GitHub Projects. Si può aggiungere se il proprietario la vuole; per ora le milestone bastano.

## 10. Rischi del programma

| Rischio | Come si gestisce |
|---|---|
| Nessun compilatore qui: una build può rompersi solo in CI | passi piccoli, un file alla volta; una PR con la CI rossa non si unisce; si corregge sullo stesso ramo |
| Il proprietario è l'unico che sente il gioco: il "feel" di prezzi, viaggiatori, sfide e dungeon non si misura qui | ogni PR dice che cosa guardare; i numeri sono in dati, quindi si cambiano senza codice |
| Suono e prestazioni su telefono non sono verificabili qui | il suono resta spento; le misure su telefono le fa il proprietario con la lista di rilascio (C4.2) |
| Allargare lo scope: troppe voci in un batch | un batch porta al massimo quattro voci piccole, o una voce grande con le sue dipendenze |
| Contenuti: il tono lo decido io, e può non piacere | i contenuti sono dati e testi, quindi si cambiano senza toccare il codice; la guida al tono (`docs/design/`) è la misura |
| Il threading (C4.1) può rompere il determinismo | il punto di consegna è fisso; i vettori `chunk_window` e `worldgen_chunks` lo verificano in entrambi i client |
| Costo della CI | il test strumentato su emulatore (C4.2) gira di notte, mai su ogni PR |

## 11. Come si aggiorna questo documento

- **A ogni batch:** ogni voce fatta resta qui con una nota **"Fatto"** sotto la sua descrizione (la data, e ciò che differisce dal progetto) e cambia stato nella [sezione 0](#0-stato-delle-voci) (con il numero della PR); si toglie da [06, sezione 8.4](06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine) e si aggiunge alla sezione giusta di [06, sezione 8.3](06-roadmap-rischi-backlog.md#83-che-cosa-è-stato-fatto-per-area); le issue si chiudono con `Closes`; si rigenerano i fatti (`tools/make_facts.py`); il CHANGELOG si aggiorna.
- **Quando arriva una decisione del proprietario:** si aggiorna la sezione 8 e la issue [progliodario/aethermoor#234](https://github.com/progliodario/aethermoor/issues/234).
- **Ogni tre batch:** si rilegge la sezione 7 (ciò che manca) e si corregge.
- **Quando un'ipotesi di questo documento si rivela falsa** (un file che non c'è, un numero che non torna): si corregge qui e nel documento che la contiene, nella stessa PR.
