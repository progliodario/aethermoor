# ADR 0008: Declarative UI in JSON

- Status: accepted
- Date: 2026-11-01

## Context

Writing every screen twice is costly and error prone.

## Decision

Screens, themes and layouts are JSON with a small widget set, flex layout, breakpoints (compact/regular/expanded, portrait/landscape) and restricted data bindings. Behavior stays in code as named commands.

## Consequences

Less duplicated work and moddable UI. Risk: toolkit complexity; fallback is hand-written critical screens following the same spec.
