---
description: Start a working session the way the project expects: check the state, choose the next items, and plan the batch
---

Follow `docs/guides/continue-the-work.md`; in short:

1. **Start clean.** `git checkout main && git pull`; `git status` must be empty; `gh pr list` must show no open pull request. If one is
   open, finish it first: `gh pr checks <n>`, read the failure (`gh run view <id> --log-failed`), fix it on its branch, and ship again with
   `tools/ship.py ... --skip-checks`.
2. **Read the state**: `CLAUDE.md` (whole, the first time), section 0 of `docs/plan/07-programma-operativo.md` (done and open items),
   section 8.4 of `docs/plan/06-roadmap-rischi-backlog.md` (the order), `gh issue list` (open issues and their milestones), and the facts
   block of `README.en.md`.
3. **Choose** the first open items that do not wait for the owner (`owner-decision`, `blocked`); the owner wants several in one pull
   request. Read each one's entry in the program: what, why, how, files, acceptance.
4. **Plan**: list the files you will touch, layer by layer (section 5 of the handbook), and say the plan in one or two lines, in Italian,
   before you start. Do not wait for an answer: the owner delegated the design decisions.
5. Then work on a branch (`feat/...`), run the checks of section 6 of the handbook, update the documents (spec, changelog, roadmap 8.3
   and 8.4, the program's section 0 and its "Fatto" notes), and ship with `tools/ship.py`.
