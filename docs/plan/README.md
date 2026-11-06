# Piano di progetto: Aethermoor (titolo provvisorio)

> Stato: **piano approvato e in esecuzione.** Scritto il 2026-11-01 come bozza v0.1; questo file e gli altri della cartella sono il piano originale, mantenuto come riferimento. Dove l'esecuzione ha preso un'altra strada lo dice una nota ("Stato") in testa a ogni documento e la tabella D1-D15 qui sotto. Per sapere **dove siamo oggi** vedi [06-roadmap-rischi-backlog.md](06-roadmap-rischi-backlog.md), sezione 8, `CHANGELOG.md` e `docs/design/catalog.md`. Le specifiche che valgono sono quelle in `docs/spec/`.

## 1. Sintesi

Un **action RPG top-down in tempo reale, open world, 2D vettoriale**, a tema **isekai fantasy**.
Si sceglie tra **8 o più protagonisti**, ognuno con un "cheat" diverso, una trama, un tono e una regione di partenza propri.
Il mondo è condiviso. Include gilda degli avventurieri con ranghi, status window, titoli, tag, legami con i compagni, reincarnazione come meta-progressione, vita in villaggio (agricoltura, cucina, costruzione), dungeon e boss.

Esistono **due implementazioni native separate** che leggono gli **stessi dati**:

| Client | Linguaggio | Tecnologia | Piattaforme |
|---|---|---|---|
| `desktop/` | C++20 | SDL3 + rasterizzatore proprio (era: ThorVG, vedi D2) | Windows e Linux |
| `android/` | Kotlin | libGDX | Android 11+ |

Per tenerle allineate si usano quattro strumenti:

1. **Specifiche scritte** in `docs/spec/`.
2. **Dati condivisi** in JSON in `data/`.
3. **Schemi JSON** in `schemas/`.
4. **Test di conformità** in `tests/conformance/`, generati da un riferimento in Python.

Il repo è un monorepo pubblico, con licenza GPL-3.0 e release automatiche tramite GitHub Actions.

## 2. Indice dei documenti

| File | Contenuto |
|---|---|
| [01-architettura-e-repository.md](01-architettura-e-repository.md) | Principi, moduli, albero del repo, dipendenze, convenzioni, licenze |
| [02-dati-specifiche-e-formati.md](02-dati-specifiche-e-formati.md) | Formati JSON con esempi, cataloghi condizioni/effetti, regole numeriche, formule, worldgen, salvataggi, conformità, modding |
| [03-game-design.md](03-game-design.md) | Mondo, 8 protagonisti, compagni, sistemi RPG, reincarnazione, gilda, titoli, tag, relazioni, vita nel villaggio, contenuti |
| [04-grafica-audio-ui-input.md](04-grafica-audio-ui-input.md) | Pipeline vettoriale, animazione, luci, audio sintetizzato, UI dichiarativa, input adattivo |
| [05-qualita-ci-release-workflow.md](05-qualita-ci-release-workflow.md) | Test, CI/CD, release, GitHub, `CLAUDE.md`, come lavoreremo insieme |
| [06-roadmap-rischi-backlog.md](06-roadmap-rischi-backlog.md) | Milestone M0-M12 con criteri di accettazione, rischi, backlog iniziale, valvole di portata |

## 3. Decisioni già prese (le tue risposte)

| Tema | Decisione |
|---|---|
| Genere | Action RPG, tempo reale, top-down, open world |
| Grafica | 2D vettoriale/minimal, **generata da codice**, sostituibile con file |
| Android | Kotlin + libGDX, Android 11+, orientamento verticale e orizzontale adattivo |
| Windows e Linux | C++ con **SDL3** |
| Multiplayer | Nessuno (solo single player) |
| Dati | JSON dichiarativo, nessuno scripting; moddabile e documentato |
| Mondo | Città e punti chiave a mano + natura procedurale deterministica |
| Salvataggi | Stesso formato ovunque, copiabili a mano; autosave + slot manuali; morte con penalità lieve |
| Lingue | Gioco in italiano e inglese; codice, file e commit in inglese |
| Repo | Monorepo pubblico, GPL-3.0, Actions, branch per funzionalità, SemVer |
| Documentazione | README IT+EN, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, template issue/PR, `CLAUDE.md`, documenti di design |
| Prima milestone | Prima dati e specifiche, poi codice |
| Protagonisti | 8 o più, trame separate, toni diversi |
| Audio | Sintetizzato da codice, sostituibile con file |
| Conformità | Specifica + test condivisi su calcoli, salvataggi, quest e mondo; tolleranza su resa visiva |

## 4. Decisioni nuove che ho preso io (da approvare)

| # | Decisione | Perché |
|---|---|---|
| D1 | **Pipeline vettoriale a "ricette"**: l'arte è descritta in JSON (forme, path SVG, gradienti, contorni, parti animabili). Ogni client la rasterizza in atlanti di texture all'avvio, alla scala del dispositivo. | Grafica ricca e nitida a qualsiasi risoluzione, nessun file immagine, sostituibile con SVG/PNG |
| D2 | Rasterizzatore: **ThorVG su desktop** e **`android.graphics` (Skia) su Android**. **Cambiata dall'ADR 0012:** un rasterizzatore proprio, specificato in `docs/spec/13-vector-art.md` e scritto due volte (C++ e Kotlin) | Con due librerie diverse i client si potevano confrontare solo con immagini di riferimento e tolleranze larghe; con una specifica sola le sonde sono identiche e girano in test JVM. ThorVG può tornare come backend alternativo senza toccare i dati |
| D3 | Animazione a **parti rigide con rig e clip** (stile cutout), senza ri-rasterizzare ogni frame | Veloce su mobile e identica nei due client |
| D4 | **Illuminazione 2D** (giorno/notte, luci puntiformi, ombre morbide) con profili di qualità | Atmosfera senza costo alto |
| D5 | **UI dichiarativa**: le schermate sono in JSON (layout, tema, binding), disegnate dai due client | Evita di scrivere due volte ogni schermata e la rende moddabile |
| D6 | Matematica di gioco **in interi** (percentuali e permille) e **tabelle** (es. tabella XP) | Risultati identici su C++ e Kotlin |
| D7 | Worldgen in **aritmetica a punto fisso Q16.16** e RNG PCG32, a due livelli (macro + chunk) | Mondo identico su ogni piattaforma, quindi salvataggi portabili |
| D8 | **Riferimento in Python** (`tools/reference/`) che genera i vettori di test | Terza opinione indipendente: se C++ e Kotlin concordano con Python, sono corretti |
| D9 | **Feature gating** nel manifest dei pack | Un client può restare indietro senza rompere il contenuto |
| D10 | Moduli `core` senza grafica in entrambi i client (C++ `aether_core`, Kotlin `core` JVM puro) | Test veloci in CI, headless |
| D11 | Mappe a mano in **formato Tiled (TMJ)** | Editor maturo e gratuito |
| D12 | Documentazione tecnica in **inglese**, documenti narrativi (GDD) in **italiano** | Contributor internazionali per il codice, tu per la storia |
| D13 | Licenza contenuti (storia, dati, testi) **CC BY-SA 4.0**, codice GPL-3.0 | Compatibile con GPLv3 e utile per i mod. Da confermare |
| D14 | Protagonisti sbloccati progressivamente tramite la reincarnazione | Lega meta-progressione e trama intrecciata |
| D15 | Difficoltà regionale **relativa alla regione di partenza** del protagonista | Open world sensato con 8 punti di partenza |

## 5. Domande aperte residue

1. **Nome definitivo** del gioco (proposte sotto).
2. **Owner GitHub** e nome repo, per l'application ID Android (`io.github.progliodario.aethermoor`).
3. Conferma della **licenza contenuti** CC BY-SA 4.0 (D13).
4. **Rating** di riferimento: propongo PEGI 12 / Teen come tetto, tutti i personaggi adulti, nessun contenuto esplicito.
5. Distribuzione: **Google Play**, itch.io, GitHub Releases, Flathub? Propongo GitHub Releases + itch.io all'inizio e Play Store più avanti.
6. Firma del codice Windows (SignPath gratuito per open source) e firma Android: chi custodisce la keystore?
7. Ti va bene il tetto di **valvole di portata** per l'1.0 (vedi documento 06)?

## 6. Proposte di nome

- **Aethermoor: Cronache dell'Altro Mondo** (il mio preferito: il nome del mondo è già nel titolo)
- **Reincarnata**
- **Status Window**
- **Eight Fates, One World**
- **Heroes of Another Sky**

Il nome vive in **un solo file** (`data/base/pack.json` e `project.json`) e va cambiato in un solo posto.

## 7. Prossimo passo

Fatto: M0 (fondazioni), M1 (specifiche e conformità), M2 (motore e arte), M3 (combattimento, quasi tutto: schivata, mana, magie), M4 (dialoghi, quest, salvataggi, otto protagonisti con la scelta all'inizio, quasi tutto), M5 (mondo aperto, quasi tutto) e l'inizio di M6 (oggetti, negozi, equipaggiamento, mana). Lo stato aggiornato, i prossimi passi in ordine e ciò che resta al proprietario (governance e pubblicazione) sono in [06-roadmap-rischi-backlog.md](06-roadmap-rischi-backlog.md), sezione 8.
