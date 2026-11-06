# 05. Qualità, CI/CD, release e modo di lavorare

> **Stato (novembre 2026).** Questo documento è il piano; ecco che cosa esiste davvero.
>
> | Area | Esiste | Non ancora |
> |---|---|---|
> | Test | validazione dati (`tools/validate_data.py`), test del riferimento e dei contenuti (`pytest`, `ruff`), 23 file di vettori di conformità eseguiti da entrambi i client, test di scenari di combattimento e di storia, smoke test del client desktop con fotogrammi | golden visivi (`tests/golden`), scenari headless a parte (`tests/scenarios`), fuzz, performance, test strumentati Android, regola di copertura |
> | Qualità del codice | `pre-commit` (file grandi, fine riga, ruff, gitleaks, validazione dati), `clang-format` (`desktop/.clang-format`, anche in `tools/ship.py`), `-Werror` nel C++, `ruff`, Dependabot mensile (le salite di Kotlin, libGDX e AGP si fanno a mano) | `clang-tidy`, sanitizzatori, `ktlint`, `detekt`, Android Lint, CodeQL |
> | CI | `ci-data` (ruff, validazione, pytest, vettori aggiornati), `ci-desktop` (Windows MSVC e Linux GCC: configure, build, ctest, pacchetto giocabile, fotogrammi, cache di vcpkg), `ci-android` (`:core:test`, `assembleDebug`, APK come artifact), `labeler`, `release` (solo una bozza di Release) | `nightly`, `codeql`, `docs`, il job `parity-check`, clang e sanitizzatori su Linux |
> | GitHub | modelli di issue (5) e di PR, label, CODEOWNERS, Dependabot | branch protection e revisione obbligatoria (decisione del proprietario), Discussions (disattivate), sito di documentazione. La wiki del repository è attiva, il piano la voleva spenta |
> | Release | nessun tag e nessuna release pubblicata; la CI produce lo zip Windows e il tar.gz Linux di prova | installer, AppImage, APK firmato, `SHA256SUMS`, SBOM, firma del codice |
> | Come si lavora | `CLAUDE.md`, i comandi in `.claude/commands/` (`/validate`, `/spec-change`, `/parity-check`), `tools/ship.py` per commit, PR e merge in un colpo | gli altri comandi (`/add-enemy`, ... `/release`) |

## 1. Strategia di test

| Livello | Cosa | Dove | Quando |
|---|---|---|---|
| Validazione dati | Schema JSON, riferimenti incrociati (ogni ID esiste), i18n completo, limiti di lunghezza, grafi di quest raggiungibili, loop di dialogo | `tools/validate_data.py` | pre-commit + CI |
| Unit | Funzioni pure: RNG, hash, rumore, formule, condizioni, effetti, parser | Catch2 / JUnit | ogni PR |
| Conformità | Vettori condivisi eseguiti da C++ e Kotlin | `tests/conformance` | ogni PR |
| Riferimento | Il riferimento Python si confronta con vettori fissi e con proprietà (es. distribuzioni del noise) | `tools/reference/tests` | ogni PR che tocca la spec |
| Golden visivi | Rasterizzazione di ricette e rig campione, UI campione, con tolleranza | `tests/golden` | ogni PR di grafica/UI |
| Scenari headless | Partenza di partita, combattimento contro un nemico, completamento quest, salvataggio/caricamento, cambio chunk | `tests/scenarios` | ogni PR + notturno |
| Fuzz/robustezza | JSON malformati, salvataggi corrotti, pack con riferimenti rotti | `tests/fuzz` | notturno |
| Performance | Tempi di generazione chunk, frame time in scenari scriptati, memoria | `tests/scenarios/perf_*` | notturno |
| Strumentati Android | Avvio, rotazione, pausa/ripresa, perdita contesto GL, import/export salvataggi | Android emulator (GitHub Actions, API 30 e 34) | notturno + release |
| Manuali | Checklist di rilascio su 1 PC Windows, 1 Linux, 2 telefoni | `docs/dev/release-checklist.md` | prima di ogni release |

**Regola di copertura:** logica di `core/sim/worldgen`: ≥ 85% di righe; funzioni pure matematiche: 100% dei rami. Nessun obbligo percentuale per `gfx/audio/ui` (si usano golden e scenari).

## 2. Qualità del codice

- **Pre-commit** (framework `pre-commit`): `validate_data`, `ruff`, `clang-format`, controllo dimensione file, controllo segreti (gitleaks), line endings.
- **C++:** `clang-tidy`, warning come errori (`/W4 /WX`, `-Wall -Wextra -Wpedantic -Werror`), ASan/UBSan e TSan (su test di thread) in CI Linux. Analisi statica `cppcheck` facoltativa.
- **Kotlin:** `ktlint`, `detekt`, `-Werror` su warning del compilatore, Android Lint.
- **Dipendenze:** Dependabot (vcpkg, Gradle, Actions, pip). Rinnovo mensile, upgrade major con ADR.
- **Sicurezza:** CodeQL (C++ e Kotlin), scansione segreti, `SECURITY.md`, risposta alle segnalazioni entro 7 giorni.
- **Revisione:** tutti i PR passano la checklist; Claude può fare la revisione, un essere umano approva il merge su `main`.

## 3. CI (GitHub Actions)

| Workflow | Trigger | Passi |
|---|---|---|
| `ci-data.yml` | PR e push che toccano `data/`, `schemas/`, `tools/`, `tests/conformance/` | Python 3.12, `validate_data.py`, `gen_conformance.py --check` (i vettori committati coincidono con quelli rigenerati), schema docs aggiornati |
| `ci-desktop.yml` | PR e push che toccano `desktop/`, `data/`, `tests/` | Matrice: `windows-2022` (MSVC), `ubuntu-24.04` (gcc 13 e clang 17), vcpkg con cache binaria, configure, build, ctest (unit + conformance + scenari), ASan/UBSan su Linux, `clang-tidy` su file modificati, artifact dei log |
| `ci-android.yml` | PR e push che toccano `android/`, `data/`, `tests/` | JDK 17, Gradle con cache, `ktlintCheck`, `detekt`, `lint`, `:core:test` (incluse conformità), `:app:assembleDebug`, test strumentati su emulatore nel notturno |
| `release.yml` | Tag `v*` | Vedi sezione 5 |
| `nightly.yml` | cron giornaliero | Fuzz, performance, strumentati completi, build "nightly" non pubblicate (artifact) |
| `codeql.yml` | PR + settimanale | CodeQL C++/Kotlin |
| `docs.yml` | push su `main` | Genera docs (MkDocs Material) e pubblica su GitHub Pages |
| `labeler.yml` | PR | Assegna label da percorsi toccati |

Un job `parity-check` confronta `supported_features` dei due client e fallisce se una funzionalità `released` è mancante in uno dei due senza un issue `parity-debt` collegato.

**Requisiti per il merge su `main`:** `ci-data`, `ci-desktop` (tutti i runner), `ci-android`, almeno 1 revisione, branch aggiornato, cronologia lineare (squash).

## 4. GitHub: configurazione del repo

- **Branch protection** su `main`: PR obbligatoria, status check obbligatori, no force-push, firme opzionali.
- **Template:** `bug_report`, `feature_request`, `content_request`, `parity-debt`, `spec_change`; PR template con checklist.
- **Label:** `area:desktop|android|data|spec|docs|art|audio|ui|i18n|tools|ci`, `type:feature|bug|chore|content|refactor`, `priority:p0..p3`, `parity-debt`, `good first issue`, `help wanted`, `needs-design`, `needs-spec`, `blocked`.
- **Milestone** = milestone della roadmap (M0…M12). **Project board** (GitHub Projects) con colonne Backlog → Specifica → In sviluppo → Revisione → Fatto.
- **Discussions** attive (idee, domande dei modder), **Wiki** disattivata (le docs sono nel repo).
- **Pagine:** sito di docs e pagina di download sulle ultime release.
- **Sponsors/Donazioni:** opzionale, non necessario per l'1.0.

## 5. Release

### Versioni

- `0.x.y` fino alla beta; `1.0.0` alla milestone M11. Ogni release ha note da `CHANGELOG.md` (Keep a Changelog) generate dai Conventional Commits con `git-cliff`.
- **Canali:** *stable* (tag `vX.Y.Z`), *beta* (`vX.Y.Z-beta.N`), *nightly* (solo artifact).

### Artefatti

| Piattaforma | Artefatti | Note |
|---|---|---|
| Windows x64 | `Aethermoor-<ver>-win64.zip` (portatile), `Aethermoor-<ver>-setup.exe` (Inno Setup) | Firma con SignPath (OSS) quando disponibile; fino ad allora avviso SmartScreen documentato |
| Linux x86_64 | `Aethermoor-<ver>-linux-x86_64.AppImage`, `.tar.gz` | Build su Ubuntu 22.04 per compatibilità glibc; Flatpak/Flathub a valle dell'1.0; testato su Steam Deck |
| Android | `Aethermoor-<ver>.apk` (arm64-v8a), `.aab` per Google Play | Firma con keystore in GitHub Secrets (`ANDROID_KEYSTORE_B64`, `…_PASSWORD`, `…_ALIAS`); R8 attivo |
| Tutti | `SHA256SUMS`, attestazione di provenienza (GitHub artifact attestations), SBOM | |
| Dati/mod | `base.pack` (zip del pack base) | Per modder e strumenti |

### Processo di rilascio

1. Branch `release/vX.Y.Z` da `main`, `CHANGELOG.md` aggiornato, versioni bump (`project.json`, Gradle, CMake).
2. Checklist manuale (`docs/dev/release-checklist.md`).
3. Tag `vX.Y.Z` → `release.yml` costruisce, testa e crea la Release GitHub (bozza).
4. Verifica degli artefatti, pubblicazione.
5. Eventuale pubblicazione su itch.io (`butler`) e Google Play (internal → closed → open → production).

## 6. Come lavoreremo insieme (Claude + tu)

Visto che modificherai quasi tutto chiedendo a Claude, il repo è progettato per essere **leggibile da un'IA** e per ridurre errori:

### `CLAUDE.md` (radice) conterrà

1. **Che cos'è il progetto** in 10 righe, e i 4 vincoli: spec-first, data-driven, due client, parità.
2. **Mappa del repo** (albero commentato) e dove si fa cosa.
3. **Comandi**: build, test, validate, run, package per ogni piattaforma.
4. **Regole d'oro:**
   - mai testi o numeri di bilanciamento nel codice;
   - ogni cambio di regola = spec + dati + test + entrambi i client (o un `parity-debt`);
   - nessun `float` nel worldgen; flag del compilatore non modificabili;
   - ID stabili; rinomina = migrazione;
   - nuove stringhe in `it` **e** `en`;
   - non toccare `tests/conformance/*.json` a mano: si rigenerano;
   - niente dipendenze con licenza incompatibile con GPLv3;
   - mai segreti nel repo.
5. **Definition of Done** (checklist).
6. **Flusso per i cambi comuni** (aggiungere un nemico, una quest, un protagonista, una skill, una lingua).
7. **Stile** (C++/Kotlin/JSON) e convenzioni di commit.
8. **Come chiedere chiarimenti**: quando la richiesta è ambigua, fare domande invece di indovinare.
9. **Dove sono le decisioni** (ADR) e come proporne di nuove.

### `.claude/` con comandi pronti

| Comando | Cosa fa |
|---|---|
| `/add-enemy`, `/add-skill`, `/add-item`, `/add-quest`, `/add-dialogue` | Crea il file dati dallo schema, aggiunge testi i18n in italiano e inglese, esegue la validazione |
| `/add-protagonist` | Scaffolding completo (dato, albero, prologo, quest, compagni, i18n, arte placeholder) con il template di contenuto del documento 03 |
| `/spec-change` | Guida un cambio di regola: spec → riferimento Python → vettori → entrambi i client |
| `/parity-check` | Confronta lo stato dei due client e produce l'elenco del debito |
| `/release` | Esegue la checklist di rilascio fino alla bozza |
| `/validate` | `tools/validate_data.py` + test di conformità |

Hook di progetto (opzionali): `PostToolUse` su modifiche a `data/` che esegue la validazione veloce; `PreToolUse` che impedisce di modificare i vettori generati a mano.

### Ruoli e flusso

- **Tu:** direzione creativa, approvazioni, storia e bilanciamento. Dici "voglio un boss di fuoco nella foresta" e basta.
- **Claude:** traduce in spec/dati/codice, esegue test, apre PR in branch `feat/...`, aggiorna changelog e docs.
- **Loop tipico:** (1) richiesta → (2) breve piano con la lista di file da toccare → (3) implementazione in un branch → (4) CI e test → (5) tu provi la build → (6) merge.

### Sessioni parallele

Dopo M2, i cambi indipendenti (contenuti di un protagonista, arte, localizzazione) possono procedere in sessioni separate su branch distinti, purché non tocchino gli stessi file; le modifiche a spec/formati restano in sessioni singole per evitare conflitti.

## 7. Documentazione

- **Per giocatori:** README (IT/EN), pagina di download, guida ai controlli, FAQ, risoluzione problemi.
- **Per sviluppatori:** `docs/dev/` (setup, architettura, debug), `docs/spec/`, ADR, glossario.
- **Per modder:** guida "Il tuo primo mod", riferimento JSON auto-generato dagli schemi, esempi.
- **Per contenuti:** GDD, bibbia del mondo, guida al tono, template di contenuto.
- **Policy:** le docs si aggiornano nello stesso PR del cambiamento (controllo nella checklist).
- **Glossario condiviso** (`docs/glossary.md`) con ogni termine IT/EN (Dono/Gift, Soglia/Threshold, Echi/Echoes, Status window, ecc.) per coerenza nelle traduzioni.

## 8. Privacy, sicurezza, store

- Nessuna raccolta dati; permessi Android minimi: nessuno per lo storage interno, nessuna connessione rete (`INTERNET` non dichiarato).
- Salvataggi leggibili (JSON): nessuna cifratura; checksum solo contro corruzione, non anti-cheat.
- Politica sulla privacy minima nei README e sulle schede dello store.
- Classificazione contenuti: questionari IARC/PEGI/ESRB compilati con il tono scelto (Teen/PEGI 12).
- Licenze di terze parti elencate nel gioco (schermata Crediti) e in `THIRD_PARTY_NOTICES.md`.
