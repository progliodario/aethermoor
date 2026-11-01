# ADR 0002: Spec-first and conformance with a Python reference

- Status: accepted
- Date: 2026-11-01

## Context

Two independent implementations must behave the same for rules, saves and the generated world.

## Decision

Rules are written in `docs/spec/`. A Python reference in `tools/reference/` generates conformance vectors in `tests/conformance/`. Both clients run the same vectors in CI.

## Consequences

A third, independent opinion catches mistakes in either client. Visual and feel differences are tolerated; numeric rules are not.
