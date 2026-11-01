# ADR 0005: Deterministic world generation with fixed-point math

- Status: accepted
- Date: 2026-11-01

## Context

Saves must be copyable between platforms, so the same seed must give the same world on C++, Kotlin and Python.

## Decision

World generation is a pure function of seed and coordinates, uses integer and Q16.16 math, PCG32 and a SplitMix64 coordinate hash, in two levels (macro map and 32x32 chunks).

## Consequences

No floating point in worldgen; compiler flags that forbid FMA contraction and fast-math. Verified by chunk-hash conformance vectors.
