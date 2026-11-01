# ADR 0003: Declarative JSON content, no scripting

- Status: accepted
- Date: 2026-11-01

## Context

Content must be moddable and identical on both clients; embedding a scripting runtime twice (C++ and JVM) doubles risk.

## Decision

All content is JSON validated by JSON Schema. Behavior uses closed catalogs of conditions and effects defined in the spec.

## Consequences

Mods cannot add new mechanics; new mechanics need a new engine and format version, gated by features (ADR 0009).
