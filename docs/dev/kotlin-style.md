# The style of the Kotlin

The Kotlin of `android/` is checked in CI by the job `kotlin-style` of `.github/workflows/ci-android.yml`, as `clang-format` keeps the C++.

- **ktlint** 1.3.1, with the rules of `.editorconfig` (the section `[*.{kt,kts}]`): the code style `intellij_idea`, no limit on the
  length of a line, and a few rules off that would only move comments around or rename things the specs name (file names, the names
  of properties and functions, the place of the comments). Every finding fails the job.
- **detekt** 1.23.6, with the default rules and `android/config/detekt.yml` on top (the long draw functions, the many fields of the
  setups and the numbers of the art are on purpose). The findings in the code written before detekt came are listed in
  `android/config/detekt-baseline.xml`; a new finding fails the job.

When ktlint fails, the job also runs `ktlint --format` and leaves in its artifact `kotlin-style` the patch it made
(`ktlint-format.patch`) and what it could not fix (`ktlint-left.txt`). This machine has no Kotlin toolchain, so the way to fix a
failure is:

```bash
gh run download <run id> -n kotlin-style -D <a new empty folder>
git apply <that folder>/ktlint-format.patch     # then fix by hand what ktlint-left.txt lists
```

When `android/config/detekt-baseline.xml` is missing the job writes it (to the same artifact) and fails; commit it. Write the baseline
again only for code that is old; new code should pass detekt as it is.
