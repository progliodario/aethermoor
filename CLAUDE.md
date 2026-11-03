# CLAUDE.md

Guide for Claude (and humans) working in this repo. The project owner mostly changes the game by asking Claude, so this file is the source of working rules.

## What this is

**Aethermoor** (working title): top-down real-time isekai fantasy action RPG, 2D vector graphics, open world, 8+ playable protagonists, single player, offline.
Two native clients with **separate code** and **shared data and specs**:

- `desktop/`: C++20, SDL3, ThorVG. Windows and Linux.
- `android/`: Kotlin, libGDX. Android 11+ (minSdk 30).

Full plan: `docs/plan/README.md` (Italian). Decisions: `docs/adr/`.

## Golden rules

1. **Spec first.** Gameplay rules are written in `docs/spec/` before or together with the code.
2. **Data driven.** Never hardcode names, texts, balance numbers or content in code. Content is JSON under `data/`; visible text only via `$i18n:` keys, always in `it` **and** `en`.
3. **Two clients, one behavior.** A change to rules touches: spec, reference (`tools/reference/`), conformance vectors, `desktop/`, `android/`. If a client lags, open a `parity-debt` issue and use a feature gate. Do not silently diverge.
4. **Never hand-edit** `tests/conformance/*.json`: regenerate with `tools/gen_conformance.py`.
5. **Determinism.** World generation uses only integer / Q16.16 math and the hash/PCG32 defined in the spec. No `float`, `sin`, `cos`, `pow`, `sqrt` there. Never use `-ffast-math`; keep `-ffp-contract=off` (GCC/Clang) and `/fp:strict` (MSVC).
6. **Gameplay math is integer** (percent and permille) plus data tables. No `pow` in formulas: use tables.
7. **Stable IDs.** `namespace:category/name`. Renaming an ID needs a save migration.
8. **No network, no telemetry, no secrets** in the repo (keystores, tokens).
9. **Licenses.** Code GPL-3.0-or-later, content CC BY-SA 4.0. Only add GPLv3-compatible dependencies.
10. **Core stays headless.** `core/data/sim/worldgen` must not import graphics, audio, input, UI or platform code.

## Repo map

```
docs/{plan,spec,design,dev,adr,guides,modding}   documentation
schemas/            JSON Schemas for data
data/base/          official content pack (pack.json, i18n, ...)
tests/{conformance,golden,scenarios}
tools/              Python: validate_data.py, reference/, generators
desktop/            C++ client (CMake + vcpkg)
android/            Kotlin client (Gradle): core (pure JVM), game (libGDX), app (launcher)
```

## Commands

```bash
# Data validation (always before committing data/schema changes)
python tools/validate_data.py

# Regenerate the conformance vectors (parallel, about 20 s) and the stamps (quiet; --show draws them)
python tools/gen_conformance.py
python tools/make_stamps.py

# Ship a change in one go: checks, signed-off commit, push, PR, wait for CI, squash merge, refresh the play build
python tools/ship.py "feat: title" --body-file body.md --play <play folder>

# Desktop (needs CMake >= 3.28, Ninja, vcpkg; see docs/dev/setup.md)
cmake --preset windows-release     # or linux-release
cmake --build --preset windows-release
ctest --preset windows-release

# Android (needs JDK 17+, Android SDK; see docs/dev/setup.md)
cd android && gradle :core:test :app:assembleDebug
```

## Definition of Done

- [ ] Spec updated (`docs/spec/`) and ADR if architectural
- [ ] Data and schema updated; `python tools/validate_data.py` passes
- [ ] i18n keys present in `it` and `en`
- [ ] Conformance vectors regenerated if rules changed; tests pass on both clients
- [ ] Desktop and Android implemented, or `parity-debt` issue linked and feature gated
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] Docs updated in the same PR

## Style

- C++: `PascalCase` types, `snake_case` functions/variables, `m_name_` members, `kConstant`, namespace `aether`. `clang-format` config in `desktop/.clang-format`.
- Kotlin: official style, ktlint + detekt. Package `io.github.progliodario.aethermoor`.
- JSON: 2 spaces, `snake_case` keys, `$schema` in every file, fractional values as integers (`_x100`, `_pm`).
- Commits: Conventional Commits, scope per area, `Signed-off-by` (DCO).
- Branches: `feat/...`, `fix/...`, `docs/...`, `content/...`, `chore/...`. Squash merge.

## How to work

- If a request is ambiguous about game design, **ask** instead of guessing; the owner decides story, tone and balance.
- Before a multi-file change, state the plan and the list of files.
- Report honestly what was run and what was not (e.g. "desktop not built locally").
- Prefer small PRs, one concern each. Spec/format changes go alone.

## Common tasks

- **Add enemy / item / skill / quest:** copy the closest file in `data/base/`, follow its schema in `schemas/`, add i18n keys (it+en), run the validator.
- **Add protagonist:** use the content template in `docs/plan/03-game-design.md` section 16.
- **Change a rule:** `docs/spec` → `tools/reference` → `tools/gen_conformance.py` → desktop → android.
- **Add a language:** new folder `data/base/i18n/<lang>/`, add it to `pack.json` languages.

## Slash commands (`.claude/commands/`)

`/validate`, `/spec-change`, `/parity-check`. More are planned (`/add-enemy`, `/add-quest`, `/add-protagonist`, `/release`).
