# 01. Architettura e repository

> **Stato (novembre 2026).** Il principio di fondo è rispettato (spec-first, dati, due client, nucleo senza grafica). Differenze dall'originale: il vettoriale non usa ThorVG né `android.graphics` ma un rasterizzatore proprio (ADR 0012); non si usano SDL3_ttf né miniz (il testo desktop è il font di debug di SDL, vedi `desktop/README.md`); i moduli reali sono `aether_core`, `aether_data`, `aether_vector`, `aether_sim` (desktop) e `core`, `game`, `app` (Android), non l'albero di questo documento; ECS, Tracy e `tools/licenses.py` non esistono. Le dipendenze vere sono in `THIRD_PARTY_NOTICES.md`.

## 1. Principi architetturali

1. **Spec-first.** Ogni regola di gioco è scritta in `docs/spec/` prima di essere implementata. Se codice e specifica divergono, si corregge uno dei due nello stesso PR.
2. **Data-driven.** Contenuti, bilanciamento, testi, UI e arte stanno in `data/`. Il codice implementa solo il "motore": non contiene mai nomi di mostri, testi visibili o numeri di bilanciamento.
3. **Due client nativi, un solo contenuto.** `desktop/` (C++) e `android/` (Kotlin) leggono lo stesso `data/`. Non c'è codice condiviso tra i due, solo specifiche e dati.
4. **Core senza piattaforma.** La simulazione non dipende da grafica, audio o input. Si testa senza finestra (headless) in CI.
5. **Parità tracciata.** Una funzionalità è completa quando ha specifica, dati, test e **entrambi** i client. Un ritardo di un client è ammesso solo con un issue `parity-debt` e un feature gate (sezione 6).
6. **Nessuna rete.** Niente account, telemetria o pubblicità. Privacy per progetto.
7. **Determinismo mirato.** Solo la generazione del mondo è deterministica (sezione 5 del documento 02). Il resto (combattimento, effetti) può usare RNG con seed iniettabile per i test.
8. **Piccoli passi verificabili.** Ogni milestone termina con qualcosa che si può eseguire sulle tre piattaforme.

## 2. Mappa dei moduli e corrispondenza C++ ↔ Kotlin

| Livello | Responsabilità | Desktop (C++) | Android (Kotlin) |
|---|---|---|---|
| core | log, assert, ID, RNG PCG32, punto fisso, matematica, eventi, risultati/errori | `desktop/src/core` | `android/core/.../core` |
| data | caricamento pack, JSON, validazione leggera, i18n, riferimenti incrociati | `src/data` | `core/.../data` |
| sim | entità (ECS), sistemi, combattimento, quest, dialoghi, inventario, economia, tempo, IA, salvataggi | `src/sim` | `core/.../sim` |
| worldgen | macro-mappa, chunk, biomi, stamp, strade | `src/worldgen` | `core/.../worldgen` |
| gfx | camera, rasterizzazione ricette, atlanti, rig, luci, particelle, font | `src/gfx` | `game/.../gfx` |
| audio | sintetizzatore, sequencer, mixer | `src/audio` | `game/.../audio` |
| input | azioni astratte, tastiera/mouse, gamepad, touch | `src/input` | `game/.../input` |
| ui | toolkit, temi, layout, schermate dichiarative | `src/ui` | `game/.../ui` |
| platform | percorsi, finestra, ciclo di vita, share/export | `src/platform/{windows,linux}` | `app/` |

**Regola:** i livelli `core`, `data`, `sim`, `worldgen` non importano nulla da `gfx`, `audio`, `input`, `ui`, `platform`.

## 3. Albero del repository

```text
aethermoor/
├─ README.md                 README italiano
├─ README.en.md              README inglese
├─ LICENSE                   GPL-3.0
├─ LICENSE-CONTENT.md        CC BY-SA 4.0 per data/, docs/design/
├─ THIRD_PARTY_NOTICES.md    generato dalla CI
├─ CHANGELOG.md              Keep a Changelog
├─ CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md  GOVERNANCE.md
├─ CLAUDE.md                 regole per lavorare con Claude (vedi doc 05)
├─ project.json              nome del gioco, versione, application id, versioni dei formati
├─ .editorconfig  .gitattributes  .gitignore
├─ .github/
│  ├─ workflows/             ci-data, ci-desktop, ci-android, release, codeql, docs, labeler
│  ├─ ISSUE_TEMPLATE/        bug, feature, content, parity-debt, spec-change
│  ├─ PULL_REQUEST_TEMPLATE.md
│  ├─ dependabot.yml  labeler.yml  CODEOWNERS
├─ .claude/                  comandi e skill di progetto (vedi doc 05)
├─ docs/
│  ├─ index.md
│  ├─ adr/                   Architecture Decision Records (0001-...)
│  ├─ spec/                  specifiche delle regole (inglese)
│  │  ├─ 00-conventions.md   unità, tick, coordinate
│  │  ├─ 01-numerics.md      interi, punto fisso, RNG, hash, rumore
│  │  ├─ 02-entities-components.md
│  │  ├─ 03-systems-order.md
│  │  ├─ 04-stats-and-combat.md
│  │  ├─ 05-skills-status-elements.md
│  │  ├─ 06-items-crafting-economy.md
│  │  ├─ 07-quests-dialogue.md
│  │  ├─ 08-world-time-weather-npc.md
│  │  ├─ 09-worldgen.md
│  │  ├─ 10-companions-ai.md
│  │  ├─ 11-progression-titles-tags-reincarnation.md
│  │  ├─ 12-save-format.md
│  │  ├─ 13-vector-art.md
│  │  ├─ 14-audio-synth.md
│  │  ├─ 15-ui-layout.md
│  │  ├─ 16-input.md
│  │  └─ 17-localization.md
│  ├─ design/                documenti narrativi e di design (italiano)
│  │  ├─ gdd.md  world.md  regions/  protagonists/  companions/
│  │  ├─ antagonists.md  guild.md  reincarnation.md  tone-guide.md
│  ├─ modding/               guida ai mod, riferimento JSON auto-generato
│  ├─ dev/                   setup Windows/Linux/Android, debug, profiling
│  └─ guides/                "come aggiungere un protagonista / quest / oggetto"
├─ schemas/                  JSON Schema 2020-12, uno per tipo di dato
├─ data/
│  ├─ base/                  pack ufficiale
│  │  ├─ pack.json           manifest
│  │  ├─ protagonists/  companions/  npcs/  enemies/  bosses/
│  │  ├─ skills/  skill_trees/  statuses/  elements.json
│  │  ├─ items/  recipes/  loot_tables/  shops/  crops/  animals/
│  │  ├─ quests/  dialogues/  guild/  titles/  tags/  achievements/
│  │  ├─ regions/  world.json  maps/  stamps/  biomes/  poi/
│  │  ├─ prefabs/  behaviors/
│  │  ├─ tables/             xp_table.json, price_tables.json, ...
│  │  ├─ art/                ricette vettoriali, rig, clip, palette, particelle
│  │  ├─ audio/              patch sintetizzatore, ricette SFX, pattern musicali
│  │  ├─ ui/                 temi, schermate, layout, icone
│  │  ├─ i18n/               it.json, en.json (+ file per dominio)
│  │  └─ overrides/          SVG/PNG/OGG che sostituiscono le ricette (inizialmente vuoto)
│  └─ examples/              pack di esempio per i modder
├─ tests/
│  ├─ conformance/           vettori di test condivisi (JSON)
│  ├─ golden/                immagini di riferimento per i test visivi
│  └─ scenarios/             scenari headless (input scriptato → asserzioni)
├─ tools/                    Python 3.12
│  ├─ validate_data.py       schema + riferimenti incrociati + i18n completo
│  ├─ gen_conformance.py     usa tools/reference per generare i vettori
│  ├─ reference/             implementazione di riferimento (RNG, noise, formule, worldgen)
│  ├─ gen_schema_docs.py     documentazione JSON per i modder
│  ├─ new_content.py         scaffolding (protagonista, quest, oggetto)
│  ├─ pack_build.py          impacchetta data/ in base.pack
│  ├─ licenses.py            THIRD_PARTY_NOTICES
│  └─ requirements.txt
├─ desktop/
│  ├─ CMakeLists.txt  CMakePresets.json  vcpkg.json
│  ├─ cmake/                 moduli CMake, flag di compilazione deterministici
│  ├─ src/{app,core,data,sim,worldgen,gfx,audio,input,ui,platform}/
│  ├─ tests/{unit,conformance,scenarios}/
│  ├─ packaging/{windows,linux}/   Inno Setup, AppImage, .desktop, icone
│  └─ resources/             icone, manifest Windows
└─ android/
   ├─ settings.gradle.kts  build.gradle.kts  gradle/libs.versions.toml
   ├─ core/                  modulo Kotlin/JVM puro (sim, data, worldgen)
   ├─ game/                  libGDX: gfx, audio, input, ui (modulo Android library)
   ├─ app/                   launcher, manifest, risorse, firma
   └─ config/{detekt,ktlint}/
```

Note:

- `data/` **non viene copiato** nei client: i build lo includono (CMake: copia accanto all'eseguibile o in `base.pack`; Gradle: sorgente `assets` dell'app).
- Niente file binari pesanti nel repo. Le immagini golden sono piccole e versionate con Git LFS solo se superano 5 MB totali.

## 4. Stack tecnologico

### Desktop (C++20)

| Componente | Scelta | Licenza | Ruolo |
|---|---|---|---|
| Compilatori | MSVC 2022, GCC ≥ 13, Clang ≥ 17 | n/a | Windows x64 e Linux x86_64 |
| Build | CMake ≥ 3.28 + Presets | BSD | Un solo sistema per entrambi |
| Pacchetti | vcpkg manifest mode (versioni bloccate) | MIT | Riproducibilità |
| Finestra/input/audio | **SDL3** | zlib | Finestra, gamepad, audio stream, tempo |
| Testo | SDL3_ttf (con HarfBuzz/FreeType) | zlib | Font vettoriali. **Non usato:** si disegna con il font di debug di SDL (solo ASCII, gli accenti sono disegnati a mano) |
| Vettoriale | ~~ThorVG~~ rasterizzatore proprio (ADR 0012) | GPL-3.0-or-later | Rasterizzazione delle ricette |
| JSON | nlohmann/json | MIT | Lettura dati e salvataggi |
| Test | Catch2 v3 | BSL-1.0 | Unit e conformità |
| Compressione | miniz | MIT | Pack e export salvataggi. **Non usato** (l'export non esiste ancora) |
| Profiling | Tracy (opzionale) | BSD-3 | Analisi |
| ECS | implementazione propria minimale | n/a | Deve rispecchiare la specifica; niente EnTT per evitare dipendenza dal modello |

### Android (Kotlin)

| Componente | Scelta | Licenza | Ruolo |
|---|---|---|---|
| Linguaggio | Kotlin (ultima stabile), JVM 17 | Apache-2.0 | Tutto il codice |
| Build | Gradle (Kotlin DSL), version catalog | Apache-2.0 | `gradle/libs.versions.toml` |
| Motore | **libGDX** (backend Android) | Apache-2.0 | Loop, OpenGL ES 3, input, audio device |
| Serializzazione | kotlinx.serialization (JSON) | Apache-2.0 | Dati e salvataggi |
| Vettoriale | `android.graphics` (`Path`, `Canvas`, `Shader`) | AOSP | Rasterizzazione delle ricette in `Bitmap` |
| Font | gdx-freetype | Apache-2.0 | Font da TTF |
| Test | JUnit 5 + Kotest assertions | EPL/Apache | Unit e conformità sulla JVM |
| Lint | ktlint, detekt | MIT/Apache | Stile |
| SDK | `minSdk 30` (Android 11), `compileSdk` e `targetSdk` = ultimi richiesti da Google Play, ABI `arm64-v8a` + `x86_64` | n/a | Compatibilità |

### Strumenti

Python 3.12 (con `jsonschema`, `pytest`), Tiled (mappe), un editor di testo con JSON Schema. Tutto gratuito.

## 5. Modello a runtime (valido per entrambi i client)

- **Loop a passo fisso 60 Hz** con accumulatore, massimo 5 passi di recupero per frame, render con interpolazione.
- **Thread:** un thread principale (simulazione + render). Thread di lavoro per: generazione chunk, rasterizzazione/bake, I/O dei salvataggi, caricamento audio. Il lavoro è a funzioni pure; i risultati tornano al thread principale tramite una coda. L'upload GPU resta sul thread principale (e sul thread GL su Android).
- **Entità:** ID numerici a runtime (indice + generazione), componenti dati puri, sistemi senza stato interno (lo stato sta nei componenti o nelle risorse globali). Gli ID testuali (`base:enemy/slime_green`) si risolvono in indici all'avvio.
- **Eventi:** bus di eventi tipizzati con coda, svuotata a ordine fisso a fine fase del tick.
- **Ordine dei sistemi per tick** (vincolante, vedi `docs/spec/03-systems-order.md`):
  1. Input → intenzioni
  2. IA → intenzioni
  3. Movimento e collisioni
  4. Abilità e skill (cooldown, costi, spawn hitbox/proiettili)
  5. Rilevamento colpi
  6. Danni, guarigione, stati alterati
  7. Morte, bottino, XP
  8. Trigger, dialoghi, quest
  9. Tempo del mondo, meteo, routine PNG
  10. Spawn/despawn, streaming chunk
  11. Animazione
  12. Camera
  13. Presentazione (render, UI, audio) con gli eventi del tick
- **Errori:** nessuna eccezione nel gioco C++ per il flusso normale: `Result<T,E>`. In Kotlin si usano le stesse regole (tipo `Result`/sealed). I dati non validi non fanno crashare: vengono scartati con log e messaggio nel registro dei problemi del pack.
- **Log:** livelli trace/debug/info/warn/error, categorie per modulo, file di log ruotato (5 file × 1 MB) nella cartella dei dati utente. Nessun dato personale.
- **Percorsi dati utente:** Windows `%APPDATA%/Aethermoor`, Linux `$XDG_DATA_HOME/aethermoor` (fallback `~/.local/share`), Android storage interno dell'app, con import/export tramite Storage Access Framework.

## 6. Strategia di parità e feature gating

- Il manifest di ogni pack dichiara `requires_features: ["vector_art_v1", "weather_v1", ...]`.
- Ogni client dichiara le funzionalità supportate in un elenco costante (`supported_features`). Se un pack richiede una funzionalità non supportata, il contenuto che la usa viene saltato e viene mostrato un avviso nel menu "Contenuti".
- Ogni funzionalità ha un issue di parità con checklist: spec, schema, dati, test conformità, desktop, Android.
- Il PR template contiene la checklist di parità. Un PR può passare con "Android in ritardo" solo se apre un issue `parity-debt` con scadenza (milestone).
- Una tabella `docs/dev/parity-matrix.md` (generata da un piccolo script a partire dai `supported_features`) mostra lo stato.

## 7. Convenzioni

### Generali

- Lingua: **inglese** per codice, file, commit, issue tecnici, `docs/spec` e `docs/dev`. **Italiano** per `docs/design` e README principale. Stringhe di gioco solo in `i18n/`.
- Commit: **Conventional Commits** (`feat(desktop): ...`, `fix(data): ...`). Scope ammessi: `desktop`, `android`, `data`, `spec`, `docs`, `tools`, `ci`, `art`, `audio`, `ui`, `i18n`.
- Branch: `main` sempre verde e protetto. Branch di lavoro `feat/<area>-<breve>`, `fix/...`, `docs/...`, `content/...`. Merge con **squash**. Release con tag `vX.Y.Z`.
- Versioni: SemVer per il gioco. In più tre versioni indipendenti: `data_format_version` (manifest), `save_version` (intero), `spec_version`. Matrice di compatibilità in `docs/dev/compat.md`.

### C++

- Standard C++20; nessuna estensione compilatore nel codice di gioco. Namespace `aether`.
- Tipi `PascalCase`, funzioni e variabili `snake_case`, membri `m_name_`, costanti `kConstantName`, file `snake_case.{hpp,cpp}`.
- `clang-format` (basato su Google con colonna 100) e `clang-tidy`. Sanitizer (ASan/UBSan) in CI su Linux.
- **Flag per il determinismo:** MSVC `/fp:strict`, GCC/Clang `-ffp-contract=off` e mai `-ffast-math`; il codice worldgen non usa `float`/`double`.
- Nessuna allocazione dinamica nel passo di simulazione dove evitabile (pool e vettori riservati).

### Kotlin

- Stile ufficiale Kotlin, `ktlint` + `detekt`. Package base `io.github.progliodario.aethermoor`. Moduli `core` e `game` separati; `core` non importa `com.badlogic.gdx` né `android.*`.
- Gli interi a 64 bit e le divisioni seguono la specifica (divisione intera arrotondata verso zero o floor secondo spec: verificare con i vettori).

### JSON

- UTF-8 senza BOM, indentazione 2 spazi, chiavi `snake_case`, ID `namespace:category/name` minuscoli.
- Ogni file ha `"$schema"` che punta allo schema in `schemas/`.
- Testi visibili **mai** nei dati: solo chiavi i18n (`"name": "$i18n:protagonist.ren.name"`).

## 8. Build e setup (riassunto, i dettagli andranno in `docs/dev/`)

- **Windows:** Visual Studio 2022 (workload C++) o Build Tools, CMake, vcpkg; `cmake --preset windows-release`, `cmake --build --preset windows-release`.
- **Linux:** gcc o clang, CMake, Ninja, dipendenze di SDL3 (X11/Wayland, ALSA/PulseAudio/PipeWire); `cmake --preset linux-release`.
- **Android:** Android Studio, JDK 17, SDK; `./gradlew :app:assembleDebug`, `./gradlew :core:test`.
- **Python:** `python -m venv .venv && pip install -r tools/requirements.txt`; `python tools/validate_data.py`.
- Script di convenienza per ogni piattaforma in `tools/` (`build.ps1`, `build.sh`) che espongono gli stessi comandi: `build`, `test`, `run`, `package`.

## 9. Licenze e legale

- **Codice:** GPL-3.0-or-later. Compatibile con SDL (zlib), nlohmann (MIT), libGDX (Apache-2.0), kotlinx (Apache-2.0). Una libreria incompatibile con GPLv3 non può essere aggiunta: la CI verifica con `tools/licenses.py`.
- **Contenuti** (`data/`, testi, `docs/design/`): CC BY-SA 4.0 (decisione D13, da confermare). **Font:** solo OFL o equivalenti, con licenza copiata in `data/base/ui/fonts/LICENSES/`.
- **Contributi:** **DCO** (`Signed-off-by`), nessun CLA.
- **Distribuzione su Google Play:** consentita con GPL se il sorgente è pubblico; la keystore di firma non è mai nel repo.
- **Marchi e nomi:** nessun riferimento a opere protette (niente personaggi o nomi di anime esistenti). Gli omaggi al genere (es. il "camion") sono generici o parodistici.
- **Privacy:** nessun SDK di terze parti. `SECURITY.md` indica come segnalare vulnerabilità.

## 10. ADR iniziali (da scrivere in M0)

| ADR | Titolo |
|---|---|
| 0001 | Monorepo con due client nativi |
| 0002 | Spec-first e conformità con riferimento Python |
| 0003 | Contenuti in JSON dichiarativo, nessuno scripting |
| 0004 | Pipeline di arte vettoriale a ricette |
| 0005 | Worldgen deterministico a punto fisso, due livelli |
| 0006 | Aritmetica di gioco intera e tabelle |
| 0007 | Formato e versionamento dei salvataggi |
| 0008 | UI dichiarativa in JSON |
| 0009 | Feature gating e debito di parità |
| 0010 | Licenze: GPL-3.0 per il codice, CC BY-SA 4.0 per i contenuti |
| 0011 | Lingue di progetto |
