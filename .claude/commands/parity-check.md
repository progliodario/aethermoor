---
description: Compare desktop and Android feature support and list parity debt
---

0. Run `python tools/make_parity.py --check` (on this machine `.venv/Scripts/python.exe`): it writes nothing and fails when a client runs no test for a suite of `tests/conformance/`; `docs/design/parity.md` is the matrix it generates (suite by suite, the test of each client). `ci-data` runs the same check on every pull request.
1. Read `supported_features` from `project.json` and the feature lists declared by each client (`desktop/src/app/features.hpp` and `android/core/src/main/kotlin/io/github/progliodario/aethermoor/core/Features.kt`; both exist and are empty today, so also compare the specs and the conformance suites each client runs, and say that gating is not in use).
2. List features present in one client and missing in the other.
3. For each gap, check that a `parity-debt` issue exists (if `gh` is available) and give its milestone.
4. Report a table: feature, desktop, android, debt issue, milestone. Say clearly what you could not verify.
