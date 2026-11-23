# Aethermoor documentation

Start here. For what the game is, read the [README](../README.en.md) ([italiano](../README.md)); for the rules of work (people and AI assistants alike), [`CLAUDE.md`](../CLAUDE.md).

| Section | Language | Purpose |
|---|---|---|
| [plan/](plan/README.md) | Italian | Full project plan; [section 8 of the roadmap](plan/06-roadmap-rischi-backlog.md#8-stato-e-prossimi-passi) is where the project stands; the [operating program](plan/07-programma-operativo.md) says what comes next, batch by batch |
| [spec/](spec/README.md) | English | Normative rules shared by both clients, one document per area |
| [adr/](adr/README.md) | English | Architecture decision records: why the project is built this way |
| [design/](design/README.md) | English | Art style ([art-style.md](design/art-style.md)); generated reports: the [catalog](design/catalog.md) of the content, the [balance](design/balance.md) model, the [translations](design/translations.md) to look at |
| [guides/](guides/README.md) | English | How to add content ([adding content](guides/add-content.md)) |
| [dev/](dev/setup.md) | English | Setup, build, debugging; [the style of the Kotlin](dev/kotlin-style.md) (ktlint and detekt in CI); [the release checklist](dev/release-checklist.md) |
| [modding/](modding/README.md) | English | Mod authoring |
| [glossary](glossary.md) | IT/EN | Shared terminology |
| [tools](../tools/README.md) | English | What every script of `tools/` does, which can run again, what to run after a change |
| [changelog](../CHANGELOG.md) | English | What changed, version by version |

## Where to find...

| Question | Where |
|---|---|
| How many quests, creatures, items...? | the facts block of the [README](../README.en.md#where-it-stands) (counted from the data) |
| Every creature, item, quest and site | [design/catalog.md](design/catalog.md) |
| How a rule works (damage, drops, farming, chests, saves...) | the spec of its area in [spec/](spec/README.md) |
| Which file of which client implements a rule | [`CLAUDE.md`](../CLAUDE.md#where-to-change-what), "Where to change what" |
| What the next work is | the [operating program](plan/07-programma-operativo.md) (batches, files, acceptance, decisions), and [roadmap, section 8.4](plan/06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine) |
| What a player can press | [spec 16](spec/16-input.md) and [`desktop/PLAY.txt`](../desktop/PLAY.txt) |
