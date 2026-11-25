# Release checklist

What must be true before a release is proposed (Alpha 0.1 first; the gates of every release are in section 6.3 of the
[operating program](../plan/07-programma-operativo.md)). Publishing a release, tagging it and signing the packages are decisions of
the owner ([`CLAUDE.md`](../../CLAUDE.md), "How to work"; issue G1): this list prepares the decision, it does not take it.

Work down the list in order. Every line is a yes or a no; a no stops the release until it is fixed or the owner accepts it in writing
(a comment on the release issue).

## 1. The repository

- [ ] `main` is clean and every pull request of the release is merged; no pull request is open.
- [ ] The last run of `ci-data`, `ci-desktop` (Windows MSVC and Linux GCC) and `ci-android` on `main` is green.
- [ ] Locally: `python tools/validate_data.py`, `python -m pytest -q tools/tests`, `python tools/gen_conformance.py --check`,
      `python tools/make_facts.py --check`, `python tools/make_parity.py --check`, `python tools/licenses.py --check` and
      `python tools/make_save_fixtures.py --check` all pass.
- [ ] `docs/design/balance.md` has no fight too hard or too slow (the fights stay easy on purpose: `CLAUDE.md`, "Fights must be too easy").
- [ ] `docs/design/translations.md` has no text left in the other language.
- [ ] `CHANGELOG.md`: the section `[Unreleased]` becomes the section of the version, with its date.
- [ ] The version is the same in `project.json` (the desktop build and the Android `versionName` read it from there),
      `data/base/pack.json` and `desktop/vcpkg.json`; the `versionCode` of `android/app/build.gradle.kts` is larger than the last one.

## 2. The builds

- [ ] A dry run of the release workflow is green: `gh workflow run release.yml` on `main` (it builds every package with the workflows
      of the pull requests, names the files after the version, writes `SHA256SUMS` and the bill of materials, checks the sums and keeps
      the files as the artifact `release-files` of the run; it creates no release).
- [ ] The files of the dry run are downloaded (`gh run download <id> -n release-files`): the Windows zip, the Linux tar.gz, the APK, the
      SBOM and `SHA256SUMS`; `sha256sum -c SHA256SUMS` passes.
- [ ] `THIRD_PARTY_NOTICES.md`, `LICENSE`, `LICENSE-CONTENT.md` and the credits are in every package.
- [ ] The last run of the nightly workflow (the game on the emulator of API 30 and 34) is green.
- [ ] The APK is the debug build: it is signed with a key of the CI that changes, so an APK of a new release does not install over the
      old one until the packages are signed (item E3.2, a decision of the owner).

## 3. Played by the owner

- [ ] Windows: a new game from the title screen to the first guardian, a save, quitting and continuing.
- [ ] Linux: the same.
- [ ] Android: the same, plus turning the phone, sending the app to the background and back, and the touch controls of every panel.
- [ ] A save exported on one platform (`X` on the title screen, Export on Android) is imported on another and continues there
      (spec 12, "Export and import").
- [ ] A save of the previous release still loads (spec 12, "Fixtures of the save": the frozen copies prove it for the reference and the
      tests; the owner proves it with a real save).
- [ ] The language is changed in the settings and every panel follows it.
- [ ] Nothing is heard that should not be: music and ambience are off (`CLAUDE.md`).
- [ ] The frames per second on the owner's phone, in Fenwick, in a village and in a big fight, with the quality used, are written in
      [`docs/design/performance.md`](../design/performance.md) and in the release issue (risk R4; item C4.2).
- [ ] The three levels of the quality of the graphics (spec 13, "Quality") are tried on a phone and on a PC: the game looks right at each.

## 4. The decision

- [ ] The owner has read the list and says yes on the release issue.
- [ ] Only then: the tag `v<version>` is pushed (it must be the version of `project.json`, or the release workflow stops); the workflow
      builds everything again from the tag and creates the **draft** of the release with all the files and `SHA256SUMS` attached; the
      owner reads it and publishes it.

## After the release

- [ ] Section 8 of the [roadmap](../plan/06-roadmap-rischi-backlog.md) says which release is out.
- [ ] The milestone of the release is closed on GitHub.
