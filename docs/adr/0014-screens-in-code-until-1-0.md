# ADR 0014: The screens stay in the code of each client until 1.0

- Status: accepted (defers ADR 0008)
- Date: 2026-11-23

## Context

ADR 0008 chose screens, themes and layouts in JSON with a small widget set and data bindings, so that the two clients would not write
every screen twice. It was never built. Today the HUD and some twenty panels (title, chooser, bag, shop and chests, board, stones,
craft, talents, journal and status window, map, dialogue, hints, settings, keys, credits, deeds) are written by hand in
`desktop/src/app/main.cpp` and `android/game/.../AethermoorGame.kt`, with all their texts in the i18n files. They are kept alike by the
shared theme and places of spec 15, by the frames checked in the desktop CI and by the owner, who plays both clients.

Building the declarative UI now would mean a layout engine and a widget set written twice (C++ and Kotlin), with no compiler on the
machine where the work is done and no way to see the result except the frames of the CI. Every panel would be rewritten while the
game keeps growing. The risk (R1 of the plan, two engines that drift) is lower for the screens than for the rules: a screen that looks
a little different on Android breaks nothing, a rule that differs breaks the game.

## Decision

- Until 1.0 the screens stay in the code of each client. Spec 15 is the contract they follow: units, the "System window" theme (the
  panel, the accents, the bars), where every panel is, and a list of the known differences.
- Every visible text of a screen is still an i18n key in both languages, and every number of the game still comes from the data.
- A new panel, or a change of the look of one, changes both clients in the same pull request and spec 15 when it moves something it
  describes; otherwise spec 15 says which client waits.
- The declarative UI of ADR 0008 is reconsidered after 1.0, when the screens stop changing every week and the modders ask for them.

## Consequences

- Each new panel is written twice. It is the cost of the two native clients (ADR 0001) and is accepted.
- Mods cannot change the screens; they change the content, the texts and the art, which is what the plan promised for 1.0.
- The theme of M4 ("System window") exists as a written theme (spec 15), not as a file of data.
- If the owner wants the declarative UI earlier, this ADR is replaced and an item is added to the program.
