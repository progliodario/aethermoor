# Aethermoor

> Working title. A top-down, real-time isekai fantasy action RPG in vector graphics. Free, open source, offline, no ads.
>
> Versione italiana: [README.md](README.md)

Eight people from our world are brought to Aethermoor by the goddess Lyra, each with a **gift** that breaks the rules. Choose who to be: the tone of the story, the way you fight and the companion at your side all change. There is one world, a huge one, and you explore it as you like.

As in any good isekai, **the protagonist is far stronger than what they meet**: fights are meant to be easy and showy, not to stop you.

## Contents

- [Where it stands](#where-it-stands)
- [What is in the game](#what-is-in-the-game)
- [The protagonists](#the-protagonists)
- [How to try it](#how-to-try-it)
- [Controls](#controls)
- [How the project is built](#how-the-project-is-built)
- [Folder layout](#folder-layout)
- [For developers](#for-developers)
- [How work is done here](#how-work-is-done-here)
- [Documentation](#documentation)
- [What is missing](#what-is-missing)
- [Contributing and license](#contributing-and-license)

## Where it stands

**A playable test version** (0.0.1, not published as a release yet). It can be played from the start on three platforms: Windows, Linux and Android.

| | State |
|---|---|
| Windows and Linux | built and tested by CI on every change; play-tested by the owner |
| Android 11+ | debug APK built and tested by CI; play-tested by the owner |
| Game rules | the same on both clients: 30 groups of conformance vectors (435 cases) run by both |
| Languages | Italian and English, complete |
| Sound | sound effects synthesized by the game; music and ambience loops are written but **switched off** until they sound right |

## What is in the game

**World**

- An open world of 16384 x 16384 tiles generated from a seed, always the same for the same seed, loaded in pieces as you walk.
- Eight regions with their own land, creatures, shops and way of speaking; day and night, four seasons, weather.
- About 130 settlements and 44 hand-made places (dungeons with a guardian, lairs, nests, outposts with a wayfarer and their story), and two hand-written towns: **Fenwick**, the village where you start, and **Aldermere**, the town of the mother guild, with named people and quests of their own.
- Threshold Stones to heal and to travel between places you have visited.
- A world map with zoom, a goal to mark and a small map; the land is revealed in a square of 5 x 5 cells (640 tiles) around you.

**Combat**

- An attack, a power strike that costs mana, a dodge roll with a moment of invulnerability, a parry that stuns whoever hits you.
- Six elements (fire, water, wind, earth, light, dark): weapons and skills have one, creatures have weaknesses and resistances.
- Status effects on creatures and on the player: burn, chill, stun, weaken.
- Stagger: hits fill a bar under a creature's health; when it is full the creature is broken for two seconds and takes more damage.
- 68 creatures with different behaviors, 27 guardians and 8 Echoes, the personal bosses of the protagonists.

**Life and progression**

- An adventurers' guild with a board and commissions, 198 quests, shops, inns, jobs from the elders.
- 145 items; gathering from bushes, trees, rocks and cacti; 16 recipes (potions, cooked dishes, gear).
- A companion for each protagonist: it follows you, fights, stays where you tell it, and its bond grows with its victories.
- Talents: one point a level to spend on attack, health, mana or defense (ten ranks each).
- A bestiary, 15 titles that raise your attack, and a profile shared by all your games: every title you ever earned gives a little more health to every game (the "echoes"), and a game that reached level 10 can be **reincarnated**: it ends, every past life gives +3% health to all the ones after it, and half of its gold is an heirloom for your next new game.
- Three separate games, automatic saving, export and import of a game as one file.

The full catalog of the content, generated from the data, is in [`docs/design/catalog.md`](docs/design/catalog.md).

## The protagonists

Each one has a prologue with Lyra, a gift, two attack skills, two personal quests and a whole story in three acts, given by Sister Maren in Aldermere: "The First Echo" in Verdalis, "The Second Echo" and "The Last Echo" in other regions (Ren in the mines of Ironspine and the Obsidian Vault, Sakura at the observatory of Lumeria, Gideon in his old kingdom...), three quests an act, each closed by a guardian, and an epilogue against their own **Echo**: the moment that brought them to Aethermoor, grown into a creature, in one of the eight sanctums around the start.

| Protagonist | Who they were | Gift | Tone | Companion |
|---|---|---|---|---|
| Ren Takahashi | an office worker, hit by a truck | sees the numbers of what attacks him (Analyze) | light comedy | Orb, a wisp |
| Sakura Mori | a physics student | a huge pool of mana, hits with magic | slapstick | Newton, an owl |
| Daichi Okabe | a firefighter | a shield that saves him from death | drama | Ember, a wolf |
| Haruka Aizawa | a vet | understands and heals creatures | cozy | Pip, a slime |
| Marco Ferri | an engineer and a cook | the knowledge of the modern world | adventure | Pot, a crab |
| Yuki Shirogane | an art thief | a pocket no one can search | noir | Shade, a bat |
| Lena Voss | a forensic doctor | sees what kills, and gets one more try | dark | Mort, a spider |
| Gideon Valmor | the Demon King, reincarnated | creatures fear him | dark comedy | Gloom, a shadow wolf |

The rules and numbers of each: [spec 18](docs/spec/18-protagonists.md).

## How to try it

There is no release yet: the test versions are the **CI artifacts** on GitHub (the *Actions* page, the last successful run on `main`, kept for 30 days).

| Platform | Artifact | How to start it |
|---|---|---|
| Windows | `aethermoor-windows-msvc` | unpack and run `aethermoor.exe`, keeping the `data` folder next to it |
| Linux | `aethermoor-linux-gcc` | unpack and run `./aethermoor`, with the `data` folder next to it |
| Android 11+ | `aethermoor-debug-apk` | install the APK (apps from unknown sources must be allowed) |

The game picks Italian or English from the system language (`F2` switches). It opens on three games: a new game asks who to be. The file [`desktop/PLAY.txt`](desktop/PLAY.txt), included in the test version, lists every control and what to try.

## Controls

**Keyboard** (a gamepad works too: left stick, `A` attacks, `X` talks, `RB` power strike, `LB` parry, `B` dodge)

| Action | Key | Action | Key |
|---|---|---|---|
| Move | `WASD` or arrows | Bag | `I` |
| Attack | `J` or `Space` | Journal with status, titles, bestiary | `Q` or `V` |
| Power strike | `K` | World map | `M` |
| Dodge roll | `L` or `Shift` | Small map | `N` |
| Parry | `U` | Crafting, and talents with `Tab` | `C` |
| Talk, touch a stone, gather | `E` | Companion: stay / follow | `H` |
| Analyze (Ren) | `Z` | Volumes | `F10` |
| Quick save / load | `F5` / `F9` | Sound on / off | `F8` |
| Close a panel, back to the games | `Esc` | Language | `F2` |

The hint over what is near you says what `E` will do: *Talk*, *Touch the stone* or *Gather*. Every action can have one more key of your choice: fill in the file `keys.json` next to the settings (it is created at the first start) with, for example, `"attack": "F"`.

**Android:** the left half of the screen is a stick that appears where you touch; a touch on the right attacks; the buttons in the bottom right are dodge, power strike and parry; in the top left are bag, map, journal, language, sound, crafting and the companion button. The Back key closes a panel or goes back to the games. Every detail: [spec 16](docs/spec/16-input.md).

## How the project is built

Two **separate** programs, written in two languages, that must behave **identically**:

| Client | Folder | Technology |
|---|---|---|
| Windows and Linux | [`desktop/`](desktop) | C++20, SDL3, an in-house vector rasterizer ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, the same rasterizer rewritten in Kotlin |

What keeps them the same:

1. **The specifications** in [`docs/spec/`](docs/spec): every game rule is written there before the code.
2. **A reference implementation in Python** in [`tools/reference/`](tools/reference), which runs the same rules.
3. **The conformance vectors** in [`tests/conformance/`](tests/conformance): cases with inputs and expected results, generated by the reference. The tests of both clients run all of them; if a client drifts, CI fails.
4. **The data** in [`data/`](data): creatures, items, quests, dialogues, art, sounds, the world and the texts are JSON files read by both clients. There are no names, texts or balance numbers in the code.

Other choices that matter: gameplay math is **integer only** (percent and permille), world generation is **deterministic** (integers and fixed point, no `float`), the graphics are **vector recipes** in JSON drawn by the rasterizer, and the sounds too are recipes synthesized by the game. The architecture decisions are in the [ADRs](docs/adr/README.md).

## Folder layout

```text
docs/        documentation
  plan/        project plan, roadmap, risks (Italian)
  spec/        normative rules for both clients (English)
  design/      art style, content catalog and balance report (generated)
  adr/         architecture decisions
  guides/      how to add content
  dev/         how to set up and build
schemas/     JSON Schema of every kind of data
data/base/   the official pack: art, sounds, creatures, items, skills, protagonists, companions,
             quests, dialogues, the world, recipes, titles, texts in Italian and English
tests/       shared conformance vectors (generated: never edited by hand)
tools/       Python scripts: validation, the rule reference, data and art generators, ship.py
desktop/     Windows and Linux client (C++, CMake, vcpkg)
android/     Android client (Kotlin, Gradle): core (rules, pure JVM), game (libGDX), app (launcher)
```

## For developers

Python 3.12 or newer is needed for the data and the tools; building the clients needs CMake, Ninja and vcpkg (desktop) and JDK 17 with the Android SDK (Android). The full guide is [`docs/dev/setup.md`](docs/dev/setup.md).

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # on Linux: .venv/bin/pip
python tools/validate_data.py                         # checks data, schemas and texts
python tools/gen_conformance.py --check               # do the vectors match the reference?
```

```bash
# desktop
cmake --preset windows-release        # or linux-release
cmake --build --preset windows-release
ctest --preset windows-release

# android
cd android && gradle :core:test :app:assembleDebug
```

The everyday scripts are described in [`tools/README.md`](tools/README.md). The most used:

| Script | What it is for |
|---|---|
| `validate_data.py` | checks every data file against its schema, the IDs and the texts in both languages |
| `gen_conformance.py` | regenerates the conformance vectors from the Python reference |
| `make_*.py` | data generators from tables in code (recipes, titles, companions, prologues, sounds, art, the stamps of places) |
| `make_catalog.py`, `balance_report.py` | write the content catalog and the balance report |
| `ship.py` | checks, signed-off commit, PR, waiting for CI and merge in one command |

To add an item, a creature, a quest, a recipe, a title, a place, a region or a language there is the [guide](docs/guides/add-content.md): almost everything is data only.

## How work is done here

The project is developed by its owner together with Claude, an AI assistant that writes the code, the data and the documents. The working rules are in [`CLAUDE.md`](CLAUDE.md); in short:

- **Spec first**, then reference, vectors, desktop and Android in the same change.
- **Everything is data**: no names, texts or numbers in code; every text in Italian **and** English.
- **Small PRs**, one concern each, merged only when CI is green.
- Design decisions (story, tone, balance) are delegated to Claude; publishing and repository governance stay with the owner.
- Play-testing, on Windows, Linux and Android, is done by the owner.

## Documentation

| Looking for | Where |
|---|---|
| The plan, the roadmap and the state of the milestones | [`docs/plan/`](docs/plan/README.md) (Italian) |
| The game rules, one document each | [`docs/spec/`](docs/spec/README.md) |
| All the content in tables | [`docs/design/catalog.md`](docs/design/catalog.md) |
| How to add content | [`docs/guides/add-content.md`](docs/guides/add-content.md) |
| Why the project is built this way | [`docs/adr/`](docs/adr/README.md) |
| What changed | [`CHANGELOG.md`](CHANGELOG.md) |
| The index of all the documentation | [`docs/index.md`](docs/index.md) |

## What is missing

What comes next, in order (details in the [roadmap](docs/plan/06-roadmap-rischi-backlog.md), in Italian):

- **Soon:** a screen to choose the keys inside the game, more automatic checks on the graphics.
- **Toward Alpha 0.1:** real skill trees (today the talents are four, in a row), tags, a choice of what to carry into a reincarnation, item quality and workbenches, a better synthesizer to bring ambience and music back.
- **Toward 1.0:** a base and residents, farming and fishing, a dynamic economy, accessibility, more languages, tools for modders.

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), [GOVERNANCE.md](GOVERNANCE.md) and [SECURITY.md](SECURITY.md).

Code: [GPL-3.0-or-later](LICENSE). Content (data, texts, art, design documents): [CC BY-SA 4.0](LICENSE-CONTENT.md). Third-party components: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
