# ADR 0009: Feature gating and parity debt

- Status: accepted
- Date: 2026-11-01

## Context

One client may lag temporarily without breaking content.

## Decision

Pack manifests declare `requires_features`; clients declare `supported_features`. Content that needs an unsupported feature is skipped with a notice. Lagging features are tracked with `parity-debt` issues, checked in CI.

## Consequences

Parity is explicit and visible instead of accidental.

## Implementation (2026-11-03)

The mechanism is in place but unused: `supported_features` is an empty list in `project.json`, in `desktop/src/app/features.hpp` and in `android/core/.../Features.kt`, no pack has `requires_features`, there is no `parity-check` job in CI (only the `/parity-check` command and the `parity_debt` issue template), and no `parity-debt` issue is open. Both clients have been kept equal by the shared specs and the conformance vectors, one change at a time.
