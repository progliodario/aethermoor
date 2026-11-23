# ADR 0008: Declarative UI in JSON

- Status: accepted. Not built yet: the screens are written in the code of each client. The decision to defer the declarative UI is planned as ADR 0014 (item B1.2 of the [operating program](../plan/07-programma-operativo.md)).
- Date: 2026-11-01

## Context

Writing every screen twice is costly and error prone.

## Decision

Screens, themes and layouts are JSON with a small widget set, flex layout, breakpoints (compact/regular/expanded, portrait/landscape) and restricted data bindings. Behavior stays in code as named commands.

## Consequences

Less duplicated work and moddable UI. Risk: toolkit complexity; fallback is hand-written critical screens following the same spec.

## Implementation (2026-11-03)

Not started: the fallback is what exists. The HUD and every panel (title, bag, shop, board, stones, journal, map, dialogue) are drawn by code in each client (`desktop/src/app/main.cpp`, `android/game/.../AethermoorGame.kt`), with all their text in the i18n files. Spec 15 (UI layout) is not written; the two clients are kept alike by hand and by looking at frames.
