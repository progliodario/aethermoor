# Security policy

Aethermoor is an offline single-player game with no network code, no accounts and no telemetry.
Relevant issues are still possible (malicious mod packs, corrupted or crafted save files, unsafe file handling, supply-chain problems).

## Reporting

Please **do not open a public issue** for a vulnerability. Use GitHub's
"Report a vulnerability" (Security tab, private advisories) on this repository.
You can expect an answer within 7 days.

## Scope

- Crashes or memory-safety bugs when loading packs, saves or imports
- A pack or save escaping its folder (path traversal)
- Dependency or release-pipeline issues (unsigned artifacts, leaked secrets)

## Supported versions

Only the latest release.
