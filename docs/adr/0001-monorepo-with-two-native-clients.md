# ADR 0001: Monorepo with two native clients

- Status: accepted
- Date: 2026-11-01

## Context

The game must run on Windows, Linux and Android, with separate codebases per system (owner requirement).

## Decision

One public monorepo containing `desktop/` (C++), `android/` (Kotlin), shared `data/`, `schemas/`, `docs/`, `tests/`, `tools/`.

## Consequences

Shared data, specs and tests are versioned atomically with both clients. Cost: two implementations to keep aligned (see ADR 0002 and 0009).
