# 17. Localization

Status: **v1**. Reference: `tools/reference/i18n.py`. Conformance suite: `i18n_format`.

## Files

`data/<pack>/i18n/<lang>/*.json`: flat objects `key -> message`. All files of a language are merged; a duplicate key is an error. The set of keys must be identical in every language declared by the pack (checked by `tools/validate_data.py`), and the top-level placeholders of each message must match across languages.

Fallback at runtime: selected language, then `en`, then the key itself.

## Message syntax

| Syntax | Meaning |
|---|---|
| `{name}` | argument substitution; integers as decimal, strings as is |
| `{n, plural, =0 {...} one {...} other {...}}` | plural by integer `n`; `#` inside a branch is replaced by `n` |
| `{k, select, a {...} other {...}}` | selection by string value |
| `{{` and `}}` | literal braces (top level only, not inside branches) |

Rules:

- A placeholder whose argument is missing is kept verbatim (`{who}`).
- `plural` looks for an exact `=N` branch first, then the category, then `other`. Italian and English share the categories: `one` when `n == 1`, otherwise `other`.
- `select` falls back to `other`; with no match, the result is empty.
- Branches are formatted recursively, so they may contain placeholders.
- An unclosed `{` is copied verbatim to the end of the message.
- `#` outside a plural branch is a normal character.

## Text in data

Data fields hold `$i18n:<key>`. Resolution happens at display time with the current language.

## Adding a language

Create `data/base/i18n/<lang>/`, translate every key, add `<lang>` to `languages` in `pack.json`.
