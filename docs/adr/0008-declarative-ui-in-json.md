# ADR 0008: Declarative UI in JSON

- Status: deferred by [ADR 0014](0014-screens-in-code-until-1-0.md): the screens stay in the code of each client until 1.0, following [spec 15](../spec/15-ui-layout.md).
- Date: 2026-11-01

## Context

Writing every screen twice is costly and error prone.

## Decision

Screens, themes and layouts are JSON with a small widget set, flex layout, breakpoints (compact/regular/expanded, portrait/landscape) and restricted data bindings. Behavior stays in code as named commands.

## Consequences

Less duplicated work and moddable UI. Risk: toolkit complexity; fallback is hand-written critical screens following the same spec.

## Implementation (2026-11-03)

Not started: the fallback is what exists. The HUD and every panel (title, bag, shop, board, stones, journal, map, dialogue) are drawn by code in each client (`desktop/src/app/main.cpp`, `android/game/.../AethermoorGame.kt`), with all their text in the i18n files. The two clients are kept alike by [spec 15](../spec/15-ui-layout.md) (the layout and the "System window" theme), by the frames of the desktop CI and by playing.
