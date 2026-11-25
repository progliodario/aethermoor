# Design documents

Narrative and design notes. The first draft of world, protagonists and systems is in [`../plan/03-game-design.md`](../plan/03-game-design.md).

The cooldowns, the mana and the skills of the protagonist are described in [spec 05](../spec/05-combat-v1.md). The rules of the graphics are in [`art-style.md`](art-style.md). How fast the game is, how it is measured (the budgets of the tests, the test on the emulator, the numbers of the CI and of the owner's phone): [`performance.md`](performance.md). Generated from the data of the base pack (do not edit by hand): [`catalog.md`](catalog.md) (`tools/make_catalog.py`: regions, creatures, items, quests and sites in tables) and [`balance.md`](balance.md) (`tools/balance_report.py`: a rough model of every fight, to find the ones too hard or too slow) and [`translations.md`](translations.md) (`tools/check_translations.py`: texts that may be left in the other language) and [`parity.md`](parity.md) (`tools/make_parity.py`: the suites of conformance vectors and the test of each client that runs them) and [`suites.md`](suites.md) (`tools/make_suites_map.py`: where each category of conformance tests named by the plan is among the real suites).

The protagonists, as they are in the game today, are in [spec 18](../spec/18-protagonists.md) and in the catalog of the pack.
