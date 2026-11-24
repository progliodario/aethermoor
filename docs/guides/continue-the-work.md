# Continuing the work

The handbook for whoever picks up Aethermoor next: a person or an AI assistant, with or without the history of earlier sessions. It
says what to read, where the project stands, how to choose the next piece of work, how to carry a change through every layer, how to
ship it, and what to do when something breaks. The rules themselves are in [`CLAUDE.md`](../../CLAUDE.md); the map of the code is in
[`docs/dev/architecture.md`](../dev/architecture.md). This page ties them together.

## 1. Read in this order

| Minutes | Read | To learn |
|---|---|---|
| 5 | [`README.en.md`](../../README.en.md) (or [`README.md`](../../README.md) in Italian) | what the game is, the numbers of today, what is missing |
| 15 | [`CLAUDE.md`](../../CLAUDE.md), whole | the rules of work, the commands, the pitfalls already met, where to change what |
| 10 | [`docs/dev/architecture.md`](../dev/architecture.md) | the layers, the folders, the files of each client, how a rule travels from the spec to the screen |
| 10 | [the operating program](../plan/07-programma-operativo.md), section 0 | which items are done, which are open, which wait for the owner |
| 5 | [roadmap, section 8.4](../plan/06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine) | the short list of what comes next, in order |
| as needed | [`docs/spec/`](../spec/README.md) | the rule of the area you will touch |
| as needed | [`tools/README.md`](../../tools/README.md) | which script writes which file, and what to run after a change |

The plan (`docs/plan/`) and `README.md` are in Italian; everything else is in English. The owner writes in Italian: answer in
Italian.

## 2. Where the project stands, and where that is written

Nothing about the state of the project is kept in one's memory: it is all in the repository, and much of it is counted from the data.

| Question | The source of truth |
|---|---|
| How many creatures, items, quests, people, cases of the vectors...? | the facts blocks (`<!-- facts:begin -->`) of the READMEs, `CLAUDE.md` and the roadmap, written by `tools/make_facts.py` from the data |
| Every creature, item, quest and site | [`docs/design/catalog.md`](../design/catalog.md), written by `tools/make_catalog.py` |
| What the game does, area by area | [roadmap, section 8.3](../plan/06-roadmap-rischi-backlog.md#83-che-cosa-è-stato-fatto-per-area) (Italian) |
| What changed, batch by batch | [`CHANGELOG.md`](../../CHANGELOG.md), section `[Unreleased]` |
| Which items of the program are done or open | the program, [section 0](../plan/07-programma-operativo.md#0-stato-delle-voci); GitHub issues and milestones |
| What the owner must still decide | the program, [section 8](../plan/07-programma-operativo.md#8-decisioni-del-proprietario), and issue `#234` |
| Which client runs which suite of vectors | [`docs/design/parity.md`](../design/parity.md) |
| Fights too hard or too slow | [`docs/design/balance.md`](../design/balance.md) (there must be none) |
| Texts left in the other language, or terms of the glossary not kept | [`docs/design/translations.md`](../design/translations.md) (there must be none) |

Check the state before you trust a document: `git log --oneline -10`, `gh pr list`, `gh issue list`, and the facts.

## 3. The loop of a session

1. **Start clean.** `git checkout main && git pull`; `git status` is empty; `gh pr list` shows no open pull request. If one is open,
   finish it first: read its checks (`gh pr checks <n>`), fix on its branch, ship it again.
2. **Choose the work.** Take the first items of [8.4](../plan/06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine) that do
   not wait for the owner (`owner-decision`, `blocked`), and read their entry in the program: what, why, how, files, acceptance. The
   owner wants **big pull requests**: several items in one branch (`CLAUDE.md`, "Big PRs").
3. **Plan.** Write down the files you will touch (the "File" line of the item, and [§5](#5-a-change-through-every-layer) below). Say
   the plan to the owner in one or two lines and go on: the owner delegated every design decision.
4. **Branch.** `git checkout -b feat/<topic>` (or `content/`, `fix/`, `docs/`, `chore/`).
5. **Do the work, layer by layer** ([§5](#5-a-change-through-every-layer)), running the checks of [§6](#6-the-checks-and-the-generators)
   as you go.
6. **Write it down**: the spec, `CHANGELOG.md`, the roadmap (take the item out of 8.4, add it to 8.3, in Italian), the program (a
   "Fatto" note under the item with what differs from the plan, and its row in section 0), `tools/README.md` for a new tool,
   `CLAUDE.md` for a new rule of work or a new pitfall.
7. **Ship** with `tools/ship.py` ([§7](#7-shipping)).
8. **Tell the owner**, in Italian: what changed in the game, what was checked (CI, tests), what was not (nothing is seen on screen from
   a machine without the game), and what to look at when playing.

## 4. Choosing between kinds of work

| Kind | Examples | Size | Where the rules are |
|---|---|---|---|
| A new rule of the simulation | the affix choice, the party, the defense of the Dungeon | L | §5 below; the spec of its area |
| New content on existing rules | a creature, an item, a quest, a person, a place | S-M | [`add-content.md`](add-content.md) |
| A change of the interface only | a panel, a button, a HUD line | M | [spec 15](../spec/15-ui-layout.md), [spec 16](../spec/16-input.md); both clients |
| Code health | the detekt baseline (B1.1), a refactor | S-M | [`docs/dev/kotlin-style.md`](../dev/kotlin-style.md) |
| Documents and tools | a generator, a check, a guide | S-M | [`tools/README.md`](../../tools/README.md) |

A batch can mix them. A batch that changes a rule of the simulation should carry only one or two such rules: each one touches about
fifteen files in five layers.

## 5. A change through every layer

The order below is the one that keeps the work checkable at every step. The worked example is the **affix choice** (item C1.2, pull
request #265): with an affix prism, at an anvil, the worn common piece becomes the same piece with another affix, chosen among three.

| # | Layer | What to do | In the example |
|---|---|---|---|
| 1 | **Spec** (`docs/spec/NN-*.md`) | write the rule as a normative text: data, refusals, the order of the draws, what is saved, the conformance scenario | spec 06, "Choosing an affix" |
| 2 | **Reference** (`tools/reference/*.py`) | implement it in the Python reference, the source of the truth for both clients | `CombatSim.affix_offers`, `choose_affix` in `combat.py` |
| 3 | **Scenario** (`tools/conformance_m3.py` and the others) | a scenario with a script of segments that exercises every branch, refusals included; print its checkpoints and read them | `affix_choice`, with test items and an anvil |
| 4 | **Save splits** (`SAVE_SPLITS` of `tools/conformance_m4.py`) | when the state is saved, one or two splits of the scenario; `tools/make_save_fixtures.py` appends them to the frozen copy | `"affix_choice": (3, 5)` |
| 5 | **Vectors** | `python tools/gen_conformance.py`; `python tools/make_save_fixtures.py`; `gen_conformance.py` again | `combat.json`, `save.json`, `save_fixtures.json`, `tests/saves/v1.json` |
| 6 | **Desktop simulation** (`desktop/src/sim/`) | the same rule in C++: the data of the setup (`combat.hpp`), the loader (`combat_loader.cpp`), the simulation (`world.hpp`, `world.cpp`), a story effect if any (`story.hpp`, `story.cpp`), the save (`save.cpp`) | `ItemDef::affix_family`, `WorldSim::affix_offers`, `choose_affix` |
| 7 | **Desktop harness** (`desktop/tests/conformance_test.cpp`) | parse the new fields of the scenario, run the new commands, compare the new fields of the checkpoints | `choose_affix`, `affix_offers` |
| 8 | **Android simulation** (`android/core/.../core/sim/`) | the same in Kotlin: `Combat.kt`, `CombatLoader.kt`, `World.kt`, `Story.kt`, `Save.kt` | `ItemDef.affixFamily`, `WorldSim.affixOffers` |
| 9 | **Android harness** (`android/core/src/test/.../ScenarioSupport.kt`) | the same as step 7 | `chooseAffix`, `affix_offers` |
| 10 | **Data** (`data/base/`, through the generators of `tools/`) | the content of the base pack, written by a generator; the schema of the new fields (`schemas/`); the texts in `it` **and** `en` | `make_common_affixes.py` (families), `make_furnishings.py` (the prism) |
| 11 | **Interface** (`desktop/src/app/main.cpp`, `android/game/.../AethermoorGame.kt`) | what the player sees and presses, on both clients; the keys in spec 16 | the third page of the crafting panel |
| 12 | **Generated documents** | `make_catalog.py`, `balance_report.py`, `check_translations.py`, `make_parity.py`, `make_suites_map.py`, `make_facts.py` | the catalog and the facts |
| 13 | **Documents by hand** | changelog, roadmap, program, READMEs, `tools/README.md` | the "Fatto" note of C1.2 |

Rules that save work:

- **The reference first, then the clients.** The vectors are the contract: once the reference and the scenario are right, the two
  clients are a translation, and their harnesses tell CI whether the translation is exact.
- **Integer math in the rule**, the same rounding everywhere (`//` in Python is a floor; C++ and Kotlin divide toward zero: for
  negative numbers write it out, as `div_trunc` of `tools/reference/story.py` does).
- **A new field of a checkpoint** appears only when the scenario has the data that needs it (`**({...} if self.<thing> else {})` in
  `snapshot`), so the old vectors do not change.
- **A new field of the save** is optional (absent when it holds nothing), so the version does not change; it needs a case in the frozen
  copy (`SAVE_SPLITS`), or `make_save_fixtures.py --check` fails.
- **Never hand-edit a generated file** (`CLAUDE.md`, "Generated files"). Change its generator, run it, and check that a second run
  changes nothing.

## 6. The checks and the generators

Run these before every push (`tools/ship.py` runs the first four again):

```bash
python tools/validate_data.py           # schemas, references between ids, texts in both languages
python -m ruff check tools              # the style of the Python
python -m pytest -q tools/tests         # the reference, the content, the documents (links, tools listed, facts)
python tools/gen_conformance.py --check # the committed vectors are the ones the reference writes
python tools/make_save_fixtures.py --check
python tools/make_parity.py --check     # both clients run every suite
python tools/make_suites_map.py --check
python tools/check_translations.py --check
python tools/licenses.py --check
python tools/make_facts.py --check
```

Which generator to run after which change is the table at the top of [`tools/README.md`](../../tools/README.md). The usual chains:

| You changed | Run, in this order |
|---|---|
| a rule of the reference or a scenario | `gen_conformance.py`; with a new save split also `make_save_fixtures.py`, then `gen_conformance.py` again |
| the world data (`overworld.json`, a stamp, a landmark, a person) | `make_stamps.py` (for a stamp), `gen_conformance.py` (the world vectors), then the client tests that count stamps and people |
| art recipes (`tools/art_*.py`) | `make_art.py <kind>`, then look at them: `art_preview.py <pattern> --out sheet.html` |
| content of any kind | the generator of that content, `validate_data.py`, `make_catalog.py`, `balance_report.py`, `make_facts.py` |
| a text | `check_translations.py` |
| a test of a client, or a suite | `make_parity.py` |

## 7. Shipping

```bash
python tools/ship.py "feat: <title>" --body-file <body.md> --trailer "Co-Authored-By: <name> <email>"
```

It checks, formats the C++ (clang-format), commits with a sign-off, pushes, opens the pull request, waits for CI, squash merges,
deletes the branch on both sides, prunes the old CI caches and copies the Windows build into the play folder (`../aethermoor-play`).
The body of the pull request says what changed in the game, how it works, what was checked and what was not, and `Closes #N` for
every issue it finishes. CI takes about ten minutes.

When CI fails, `ship.py` stops with "not merged" and leaves the pull request open:

1. `gh pr checks <n>` says which job failed.
2. `gh run list --branch <branch> --limit 5` gives the id of the run; `gh run view <id> --log-failed | grep -E "error|FAILED"` gives
   the error.
3. Fix it on the same branch, then ship again with `--skip-checks` (the local checks already passed).

## 8. When something breaks

| Symptom | Cause, and the fix |
|---|---|
| MSVC: `C4244`, `C4267`, a conversion from `size_t` or `int64_t` | warnings are errors: cast explicitly (`static_cast<int>(...)`) |
| GCC: `missing-field-initializers` | a brace initializer of an aggregate without every field: give them all, or assign the fields one by one |
| C++: `redefinition of struct` | an edit script ran twice and inserted a block twice; edit scripts must check that the new text is not already there |
| C++: `... is private within this context` on a call that looked public | a private method has the same name as a public accessor (the overload of the non-const object wins): rename the private one |
| detekt: `CyclomaticComplexMethod`, `NestedBlockDepth`, `LoopWithTooManyJumpStatements` | take a branch out into a function of its own; never add to the baseline. A function already in the baseline may grow, but the entry is keyed by its signature: changing the signature orphans the entry |
| ktlint | imports in order (uppercase before lowercase, `java`, `javax`, `kotlin` after the others), no blank line among them; the arguments of a call one per line once they do not fit; trailing commas in multi-line lists |
| a client test counts stamps, people or tiles | update `desktop/tests/combat_test.cpp` and `android/core/src/test/.../WorldGenTest.kt` (and the others that grep finds) in the same change as the data |
| "Check the smoke-test frames" | the start of the game looks different: if it is on purpose, `gh run download <id> -n screenshots-windows-msvc`, look at the frames, then `tools/check_frames.py --write` and push. A new person near Fenwick moves them: put people where the start view does not reach |
| vcpkg fails to download in CI | a flake: `gh run rerun <id> --failed`, then `ship.py --skip-checks` |
| `OSError: [Errno 22] Invalid argument` in a generator | Windows holds the file for a moment: run it again |
| a text written by a shell heredoc lost a backslash | write scripts with an editor (or the Write tool), never through a heredoc |
| `test_the_generators_write_lf_line_endings` | `newline="\n"` must be on the same line as `.write_text(` |
| `make_save_fixtures.py --check`: a field of the save no case holds | add a save split of a scenario that has the field (`SAVE_SPLITS`) and run `make_save_fixtures.py` |
| the vectors of the world changed after a data change | expected when the world data or a stamp changed: commit them; both clients read the same data |

## 9. Working without compilers

The machine the project is developed on has no C++ or Kotlin compiler: CI is the only build. What helps:

- **Write the C++ and the Kotlin as a translation of the reference**, next to the function that does the closest thing (the temper
  code was the model of the affix choice, the furniture code the model of the rooms).
- **Read the diff before shipping**, looking for the errors of the table above: names that exist, includes and imports, casts,
  every field of an aggregate, `const` correctness, the order of declarations.
- **Keep edits scriptable and idempotent**: an edit script replaces an exact block once and does nothing when the new text is already
  there. Check that each anchor occurs exactly once.
- **Expect one round of CI fixes** for a large change, and say so to the owner.

## 10. Working with the owner

- The owner plays every change on Windows, Linux and Android and reports what is wrong; the owner never edits files or runs tools.
- The owner delegated every design decision. Decide, say what was chosen, go on. Ask only when a choice is truly the owner's taste
  (the form of Gideon's Dungeon was such a choice), and never wait for the answer if other work can go on.
- What stays with the owner: a public release, the settings of the repository, signing keys, licenses of outside material
  (program, section 8).
- Two standing wishes: **fights must be too easy** (the protagonist is overpowered), and **music and ambience stay off**.
- Report honestly: what was run, what was not ("not built locally", "not seen on screen").
