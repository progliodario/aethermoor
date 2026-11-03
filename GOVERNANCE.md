# Governance

- The **project owner** has final say on game direction (story, tone, scope) and on releases.
- **Maintainers** review and merge pull requests; `.github/CODEOWNERS` names the owner as the reviewer of everything. The intended rule is at least one review and green CI before a squash merge into `main`; the repository does not enforce it yet (branch protection is not enabled, and the owner has authorized Claude to merge its own pull requests when every CI check is green).
- Architectural changes go through an **ADR** in `docs/adr/`.
- Rule changes go through the **spec**: change `docs/spec/`, the Python reference, the conformance vectors, then both clients.
- Disagreements: discuss in the issue or PR; the owner decides if there is no consensus.
- The project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
