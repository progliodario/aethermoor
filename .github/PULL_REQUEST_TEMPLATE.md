## What and why

<!-- One short paragraph. Link the issue: Closes #123 -->

## Checklist

- [ ] Spec updated (`docs/spec/`) / ADR added if architectural
- [ ] Data and schema updated; `python tools/validate_data.py` passes
- [ ] i18n keys in both `it` and `en`
- [ ] Conformance vectors regenerated (not hand-edited) if rules changed
- [ ] **Desktop** implemented and tested, or N/A
- [ ] **Android** implemented and tested, or N/A
- [ ] If one client lags: `parity-debt` issue linked and feature gated: #
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] Generated documents refreshed (`make_catalog.py`, `make_facts.py`); `python -m pytest -q tools/tests` passes
- [ ] Docs updated (spec, `tools/README.md` for a new script, `CLAUDE.md` for a new rule of work)
- [ ] Commits are Conventional Commits and signed off (DCO)

## How I tested

<!-- Commands run, platforms tried. Say what was NOT tested. -->
