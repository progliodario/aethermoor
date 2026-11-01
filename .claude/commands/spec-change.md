---
description: Guide a gameplay-rule or data-format change across spec, reference, vectors and both clients
argument-hint: <what to change>
---

Change request: $ARGUMENTS

Follow this order and stop to ask if a design decision is missing:

1. Read the relevant file in `docs/spec/` and the matching schema in `schemas/`.
2. State the plan and the list of files to touch (spec, schema, data, `tools/reference/`, vectors, `desktop/`, `android/`, i18n, changelog).
3. Update the spec first (precise formulas, integer math, rounding rules).
4. Update the Python reference and regenerate conformance vectors (never edit vectors by hand).
5. Update schemas and data; run `python tools/validate_data.py`.
6. Implement in `desktop/` and `android/`, or open a `parity-debt` issue and gate the feature.
7. Run the tests of each area and report what was and was not run.
8. If the save format changes: bump `save_version`, add a migration and a migration test.
