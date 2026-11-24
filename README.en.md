# Aethermoor

> Working title. A top-down, real-time isekai fantasy action RPG in vector graphics. Free, open source, offline, no ads.
>
> Versione italiana: [README.md](README.md)

Eight people from our world are brought to Aethermoor by the goddess Lyra, each with a **gift** that breaks the rules. Choose who to be: the tone of the story, the way you fight and the companion who follows you change with it. There is one world, huge, and you explore it as you like.

As in every good isekai, **the protagonist is far stronger than what they meet**: fights are meant to be easy and spectacular, not to block you.

## Contents

- [Where it stands](#where-it-stands)
- [What is in the game](#what-is-in-the-game)
- [The protagonists](#the-protagonists)
- [How to try it](#how-to-try-it)
- [Controls](#controls)
- [How the project is built](#how-the-project-is-built)
- [Folder layout](#folder-layout)
- [For developers](#for-developers)
- [How work is done here (with an AI too)](#how-work-is-done-here-with-an-ai-too)
- [Documentation](#documentation)
- [What is missing](#what-is-missing)
- [Contributing and license](#contributing-and-license)

## Where it stands

**Playable test build** (0.0.1, not yet released). It plays from start to end on Windows, Linux and Android 11+: CI builds and tests all three on every change, and the owner play-tests them.

The numbers of the game, counted from the data (never written by hand: `python tools/make_facts.py` updates them, and a test fails when they are stale):

<!-- facts:begin -->
| What | How many (counted from the data by `tools/make_facts.py`) |
|---|---|
| World | 8 regions, 46 hand-made sites (dungeons, lairs, outposts, sanctums, Fenwick, the Guest's cottage, Aldermere) and about 130 generated settlements |
| Protagonists | 8, each with a companion, 4 more companions who may join the party, and a story of six acts (120 story quests) |
| Creatures | 83, of which 27 guardians and 8 Echoes |
| Quests | 407 (24 tales of the villagers) |
| Items and recipes | 290 items, 86 recipes (8 secret) |
| Progression | 50 titles, 8 tags, 16 talents, 29 deeds |
| Named people | 58 in the world data, besides the generated villagers |
| Sound | 174 synthesized sound effects (music and ambience are off) |
| Texts | 4283 keys, in Italian and English |
| Same rules on both clients | 31 files of conformance vectors, 634 cases, run by the C++ and the Kotlin tests |
| Documents | 19 specs, 14 ADRs |
<!-- facts:end -->

**Done and to do, one line per part** (item by item in [section 8 of the roadmap](docs/plan/06-roadmap-rischi-backlog.md#8-stato-e-prossimi-passi), in Italian):

| Part | Done | To do |
|---|---|---|
| Foundations, rules, CI | all, the smoke-test frames checked in CI too | ktlint and detekt in CI |
| Graphics | anime art for everything, people seen from the front, the side and behind, the light of the hour, wind, water, shadows, the pack's font | — |
| Combat | complete: elements, statuses, parry, stagger, guardians, abilities on command | touches, always toward easy fights |
| World | huge, eight regions, towns, dungeons, weather that hides and slows, wind that pushes, fog and storms | performance measured on a phone |
| Quests and stories | a story in six acts for every protagonist, tales of the villagers, guild, legends, bounties, Gideon's Dungeon | nothing |
| Life | gathering, fishing, hunting, gardens, animals, shared chests, the Guest's cottage and its furniture, pedlars, secret recipes, food with effects | wagons seen travelling, a bigger house |
| Companions | one per protagonist with commands, bond and care; Haruka tames a second one; a party with the four strays of the cottage, one at a time | the abilities of pairs |
| Progression | talents with abilities, titles with effects, bestiary, reincarnation with an heirloom, deeds that give echoes, runes on the weapons, tags to wear, weapons and armors with rolled affixes (also on twenty-four common pieces) tempered at an anvil or by the smiths, pieces with two affixes, gifts of the deeds | affixes to choose |
| Accessibility | hints, damage numbers and flashes can be turned off, large text, configurable keys | — |
| Release | test builds from CI | Alpha 0.1 and then 1.0 (the owner decides) |

## What is in the game

The full catalog, generated from the data, is [`docs/design/catalog.md`](docs/design/catalog.md).

**World**

- An open world of 16384 x 16384 tiles generated from a seed (always the same for the same seed), streamed as you walk; eight regions with their own terrain, creatures, shops and way of speaking.
- Day and night, four seasons, weather: rain and night hide you from creatures, rain and snow slow them, rain makes the gardens grow sooner, the wind at your back makes you walk faster, fog hides you, in storms the lightning strikes the creatures that chase you.
- Generated settlements and hand-made sites: dungeons and lairs with a guardian, nests, eight outposts (each with a wayfarer, a local and a pedlar), eight sanctums of the Echoes, **Fenwick** (where you start), **the Guest's cottage** east of Fenwick and **Aldermere**, the town of the mother guild.
- Threshold Stones to heal and travel; a world map with zoom, a goal to mark and a minimap; every quest marks where to go.

**Combat**

- Attack, a power strike that costs mana, a dodge roll with a moment of invulnerability, a parry that stuns.
- Six elements with weaknesses and resistances, statuses (burn, chill, stun, weaken) on creatures and player, stagger.
- Guardians with their bar at the top of the screen, and eight Echoes, the personal bosses of the protagonists.
- Easy on purpose: the protagonist is overpowered, and that is the theme of the game.

**People and quests**

- A guild with ranks and a board, shops, inns, elders' errands, innkeepers' favors, workshops, the Book of Legends, bounties on every guardian.
- The villagers of every region tell their troubles in three quests; named people in Fenwick (Bran, Odile, Tobin, Nana Brin), in Aldermere (Hestia, Rook, Selwyn, Wendel, Sister Maren, Corvin) and at the outposts.
- Four factions (the Guild, the Ring of Wayfarers, the Chroniclers, the Folk) with titles and gifts; renown in a region lowers its prices and changes how people greet you.

**Life**

- Gathering from trees, bushes, rocks and the small scenery of the wild; fishing in the reeds; hunting boars, elks and dune foxes.
- Gardens in every village, hen coops and goat pens; recipes at the campfire and the anvil, fine work, a secret dish per region taught by the shopkeeper.
- Food and brews that fortify, ward, regenerate or speed you up; a draught that cleanses.
- A **chest** in every village and town: they all hold the same things.
- **The Guest's cottage**: a chest, a campfire, an anvil, gardens, hens, a goat and a Threshold Stone; Nana Brin gives it to you after her three favours. Ten rugs, in the house and in the garden, wait for the **furniture** you make at an anvil (a bed, a weapon rack, a bookshelf, a drying rack, a training dummy, a work table, a bench, a scarecrow, an archery target, a stone lantern), and each one helps you everywhere like a title.
- **Residents**: once a region knows you (six quests finished there), somebody moves to its outpost, greets you and gives you a rune; with eight, a settler comes to every village of the region, with a trade (baker, stonemason, ice fisher...), a quest and a workshop.
- Shops with market days, goods from other regions, rare wares for friends; they pay less when you sell too much of one thing. Corvin in Aldermere and a pedlar at every outpost bring the goods of a different region every day.

**Progression**

- Levels, a talent tree with abilities (two used with a key of their own), titles that change the game, a bestiary with weaknesses; **runes** made at an anvil to engrave on your weapon, which then hits harder and with the element of the rune; **tags**, traits earned by how you play, worn one at a time; **affixes**: every region has a weapon and an armor with a bonus more, left by its guardians, with an affix rolled at random (100 to 160%).
- A profile shared by all games: titles, past lives and **deeds** give "echoes" (more health in every game); every deed done leaves a gift in the bag of every new game; from level 10 a game can **reincarnate** and leave half its gold and its weapon to the next.
- A companion per protagonist that follows, fights, stays, comes back and heals; Haruka tames creatures, and the last one stays with her.

## The protagonists

Each has a prologue with Lyra, a gift, two attack skills, two personal quests and a story in five acts given by Sister Maren in Aldermere: "The First Echo" in Verdalis, the second and third in other regions, the epilogue against their own **Echo** (the moment that brought them here, grown into a creature, in one of the eight sanctums around the start) and "A Life Here", the first steps of the new life.

| Protagonist | Who they were | Gift | Tone | Companion |
|---|---|---|---|---|
| Ren Takahashi | office worker, hit by a truck | sees the numbers of what attacks him (Analyze) | light comedy | Orb, a wisp |
| Sakura Mori | physics student | huge mana, strikes with magic | comic | Newton, an owl |
| Daichi Okabe | firefighter | a shield that saves him from death | drama | Ember, a wolf |
| Haruka Aizawa | veterinarian | understands, heals and tames creatures | cozy | Pip, a slime |
| Marco Ferri | engineer and cook | the knowledge of the modern world | adventure | Pot, a crab |
| Yuki Shirogane | art thief | a pocket nobody can search | noir | Shade, a bat |
| Lena Voss | coroner | sees what kills, and gets a second chance | grim | Mort, a spider |
| Gideon Valmor | the Demon King, reincarnated | creatures fear him, his companion hits twice as hard | dark comedy | Gloom, a shadow wolf |

Rules and numbers of each: [spec 18](docs/spec/18-protagonists.md).

## How to try it

There is no release yet: the test builds are the **CI artifacts** on GitHub (*Actions* page, last successful run on `main`, kept 30 days).

| Platform | Artifact | How to start |
|---|---|---|
| Windows | `aethermoor-windows-msvc` | unzip and run `aethermoor.exe`, keeping the `data` folder next to it |
| Linux | `aethermoor-linux-gcc` | unzip and run `./aethermoor`, with the `data` folder next to it |
| Android 11+ | `aethermoor-debug-apk` | install the APK (allow apps from unknown sources) |

The game picks Italian or English from the system language (`F2` switches). It opens on three games; a new game asks who to be. [`desktop/PLAY.txt`](desktop/PLAY.txt), included in the test build, lists every control and what to try.

## Controls

**Keyboard** (gamepad too: left stick, `A` attack, `X` talk, `RB` power strike, `LB` parry, `B` dodge)

| Action | Key | Action | Key |
|---|---|---|---|
| Move | `WASD` or arrows | Bag | `I` |
| Attack | `J` or `Space` | Journal with status, titles, bestiary | `Q` or `V` |
| Power strike | `K` | World map / minimap | `M` / `N` |
| Dodge | `L` or `Shift` | Crafting, and talents with `Tab` | `C` |
| Parry | `U` | Companion: stay / follow, come back | `H`, `G` |
| Talk, touch a stone, gather, tend a plot, open a chest | `E` | Shockwave / Mend (talents) | `R` / `T` |
| Analyze (Ren) | `Z` | Tame (Haruka) | `B` |
| Quick save / load | `F5` / `F9` | Settings (volumes, accessibility, large text) | `F10` |
| Your own keys | `F4` | Sound on / off, language | `F8`, `F2` |
| Close a panel, back to the games | `Esc` | Deeds (games screen) | `A` |

The words above what is near you say what `E` will do. Every action can have one more key of your choice (`F4`, or the file `keys.json` next to the settings).

**Android:** the left half of the screen is a stick that appears where you touch; a tap on the right attacks; the buttons at the bottom right are dodge, power strike and parry; at the top are bag, map, journal, language, sound, crafting and companion; the options of accessibility are at the bottom of the journal. Back closes a panel or returns to the games. All details: [spec 16](docs/spec/16-input.md).

## How the project is built

Two **separate** programs, in two languages, that must behave **identically**:

| Client | Folder | Technology |
|---|---|---|
| Windows and Linux | [`desktop/`](desktop) | C++20, SDL3, an in-house vector rasterizer ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, the same rasterizer written again in Kotlin |

What keeps them the same:

1. **The specs** in [`docs/spec/`](docs/spec/README.md): every rule of the game is written there before the code.
2. **A reference implementation in Python** in [`tools/reference/`](tools/reference), running the same rules.
3. **The conformance vectors** in [`tests/conformance/`](tests/conformance): inputs and expected results generated by the reference and run by the tests of both clients; if a client drifts, CI fails.
4. **The data** in [`data/`](data): creatures, items, quests, dialogues, art, sounds, world and texts are JSON read by both clients. The code holds no names, texts or balance numbers.

Gameplay math is **integer only** (percent and permille), world generation is **deterministic** (integers and fixed point), the graphics are **vector recipes** in JSON written by Python tools, and the sounds are synthesized recipes too. Architecture decisions are in the [ADRs](docs/adr/README.md).

## Folder layout

```text
AGENTS.md, CLAUDE.md  working rules for AI assistants (and useful to anyone changing the project)
docs/        documentation (index: docs/index.md)
  plan/        project plan, roadmap and status (Italian)
  spec/        normative rules for both clients (English)
  design/      art style; catalog, balance and translations (generated)
  adr/         architecture decisions
  guides/      how to add content
  dev/         how to set up and build
schemas/     a JSON Schema for every kind of data
data/base/   the official pack: art, sounds, creatures, items, quests, dialogues, world, texts (it, en)
tests/       shared conformance vectors (generated: never edited by hand)
tools/       Python: validation, the reference of the rules, generators, ship.py (guide: tools/README.md)
desktop/     Windows and Linux client (C++, CMake, vcpkg)
android/     Android client (Kotlin, Gradle): core (rules, pure JVM), game (libGDX), app (launcher)
```

## For developers

Python 3.12 or newer for data and tools; to build the clients, CMake, Ninja and vcpkg (desktop) and JDK 17 with the Android SDK (Android). The full guide is [`docs/dev/setup.md`](docs/dev/setup.md).

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # on Linux: .venv/bin/pip
python tools/validate_data.py                         # data, schemas, references, texts
python -m pytest -q tools/tests                       # reference, content, documents
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

What every script does, which ones can be run again and what to run after changing something: [`tools/README.md`](tools/README.md). To add an item, a creature, a quest, a recipe, a title, a place, a region or a language there is the [guide](docs/guides/add-content.md): almost everything is data only.

## How work is done here (with an AI too)

The project is developed by the owner together with Claude, an AI assistant that writes code, data and documents. The working rules are in [`CLAUDE.md`](CLAUDE.md) ([`AGENTS.md`](AGENTS.md) points other assistants there); in short:

- **Spec first**, then reference, vectors, desktop and Android in the same change.
- **Everything is data**: no names, texts or numbers in code; every text in Italian **and** English.
- **Generated is generated**: the vectors, the catalog, the numbers of the READMEs and much of the data come out of tools; change the source and run the tool again.
- **Big PRs**: at every request Claude moves many roadmap items forward together and ships them in one PR with `tools/ship.py`, merged only on green CI.
- Design decisions are delegated to Claude; publishing and repository governance stay with the owner, who play-tests every change.

## Documentation

| Looking for | Where |
|---|---|
| Index of all the documentation | [`docs/index.md`](docs/index.md) |
| The plan, the roadmap and the state of the milestones | [`docs/plan/`](docs/plan/README.md) (Italian) |
| The rules of the game, one per document | [`docs/spec/`](docs/spec/README.md) |
| All the content in tables | [`docs/design/catalog.md`](docs/design/catalog.md) |
| How to add content | [`docs/guides/add-content.md`](docs/guides/add-content.md) |
| What every script does | [`tools/README.md`](tools/README.md) |
| Why the project is built this way | [`docs/adr/`](docs/adr/README.md) |
| What changed | [`CHANGELOG.md`](CHANGELOG.md) |
| Accessibility: what the game does and what is missing | [`docs/dev/accessibility.md`](docs/dev/accessibility.md) |

## What is missing

The next things, in order. The full program, with the batches, the files and the acceptance of each item, is in [docs/plan/07-programma-operativo.md](docs/plan/07-programma-operativo.md) (in Italian); the short list of the roadmap is in [section 8.4](docs/plan/06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine).

- **Soon:** a detekt baseline down to zero.
- **Middle term:** streaming on a worker thread and measures on Android; a synthesizer for music and ambience (only if the owner wants it).
- **Toward 1.0:** quality settings; controls and layout on Android; signed packages; loading mods in the game (the guide and the check of a mod are there).
- **The owner decides:** when to publish the first release (Alpha 0.1), the repository settings, the signing keys and the other decisions listed in the program.

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), [GOVERNANCE.md](GOVERNANCE.md) and [SECURITY.md](SECURITY.md).

Code: [GPL-3.0-or-later](LICENSE). Content (data, texts, art, design documents): [CC BY-SA 4.0](LICENSE-CONTENT.md). Third-party components: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
