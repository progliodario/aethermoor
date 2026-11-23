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

- [ ] The artifacts of the CI run of the release commit are downloaded: the Windows build, the Linux build and the APK.
- [ ] `THIRD_PARTY_NOTICES.md`, `LICENSE`, `LICENSE-CONTENT.md` and the credits are in every package.
- [ ] Each artifact has its SHA-256 written down (until the release pipeline, item E3.1, writes `SHA256SUMS`).

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
- [ ] The frames per second on the owner's phone are written in the release issue (risk R4; item C4.2 measures them in CI).

## 4. The decision

- [ ] The owner has read the list and says yes on the release issue.
- [ ] Only then: the tag `v<version>` is pushed, the draft of the release is filled with the artifacts and their checksums, and the
      owner publishes it.

## After the release

- [ ] Section 8 of the [roadmap](../plan/06-roadmap-rischi-backlog.md) says which release is out.
- [ ] The milestone of the release is closed on GitHub.
