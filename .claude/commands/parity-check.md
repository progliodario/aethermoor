---
description: Compare desktop and Android feature support and list parity debt
---

1. Read `supported_features` from `project.json` and the feature lists declared by each client (`desktop/src/app/features.hpp` and `android/core/src/main/kotlin/io/github/progliodario/aethermoor/core/Features.kt`, once they exist).
2. List features present in one client and missing in the other.
3. For each gap, check that a `parity-debt` issue exists (if `gh` is available) and give its milestone.
4. Report a table: feature, desktop, android, debt issue, milestone. Say clearly what you could not verify.
