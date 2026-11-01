# ADR 0009: Feature gating and parity debt

- Status: accepted
- Date: 2026-11-01

## Context

One client may lag temporarily without breaking content.

## Decision

Pack manifests declare `requires_features`; clients declare `supported_features`. Content that needs an unsupported feature is skipped with a notice. Lagging features are tracked with `parity-debt` issues, checked in CI.

## Consequences

Parity is explicit and visible instead of accidental.
