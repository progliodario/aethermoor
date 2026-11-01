# 00. Conventions

Status: **v1** (spec_version 1). Normative for both clients.

## Units

| Quantity | Unit | Notes |
|---|---|---|
| Space | **tile** | 1 tile = 1.0 world unit = 32 logical render units |
| Origin / axes | top-left, **y points down** | |
| Time | **tick** = 1/60 s | durations in data are in ticks unless named `_s` |
| Game day | 86 400 ticks | 24 real minutes; 1 real minute = 1 game hour |
| Fractions in data | integers | `_x100` (hundredths), `_pm` (per mille), `_pct` (percent) |

Positions and velocities are `float` in code (not specified bit by bit) but **never** in data files: data uses integers.

## Identifiers

`namespace:category/name[/more]`

- `namespace`: `[a-z][a-z0-9_]*` (the pack id, e.g. `base`).
- `category`: `[a-z][a-z0-9_]*` (`enemy`, `item`, `skill`, ...).
- every following segment: `[a-z0-9_]+`, non-empty.
- There must be at least one `/`, exactly one `:`.

The reference algorithm is `tools/reference/ids.py::valid_id`; it is written without regular expressions so that the clients implement exactly the same checks. Conformance suite: `ids`.

IDs are stable. Renaming an ID requires a save migration.

## Localizable text

Data never contains visible text. A text field holds `$i18n:<key>` where `<key>` is `[a-z0-9_]+(\.[a-z0-9_]+)*`. See `17-localization.md`.

## Integer rules

See `01-numerics.md`. In short: gameplay values are integers; divisions floor; 64-bit intermediates.

## Files

JSON, UTF-8 without BOM, LF line endings, two-space indent, `snake_case` keys, `$schema` in every file.

## Compatibility versions

| Version | Where | Meaning |
|---|---|---|
| `spec_version` | `project.json`, conformance files | Version of these rules |
| `data_format_version` | pack manifest | Version of the data formats / schemas |
| `save_version` | save files | Version of the save format |

A client refuses a pack whose `data_format_version` is greater than it supports.
