#!/usr/bin/env python3
"""Ships a change in one command: checks, commit, push, pull request, wait for CI, merge, refresh the play build.

    python tools/ship.py "feat: a title" --body-file body.md [--play DIR] [--no-merge] [--skip-checks]

Steps (each one stops the script when it fails):
  1. local checks, in parallel: data validation, ruff, the tool tests and the conformance vectors (`--skip-checks` omits them)
  2. `git add -A`, a signed-off commit (DCO) on the current branch, `git push -u`
  3. `gh pr create` (title and body as given), then wait for every check of the pull request
  4. squash merge and delete the branch when all checks pass (`--no-merge` stops before), back on an updated `main`
  5. with `--play DIR`: download the Windows build of the pull request and copy it over the play folder (a running game keeps its files: the data is
     still replaced, a note says the program was busy)

The commit trailer comes from `--trailer` (repeatable) or the `SHIP_TRAILERS` environment variable (lines separated by `|`).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(args: list[str], check: bool = True, capture: bool = False, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, text=True, encoding="utf-8",
                          stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT if capture else None)


def python_tool(*args: str) -> list[str]:
    venv = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    return [str(venv if venv.exists() else sys.executable), *args]


def checks() -> bool:
    jobs = {
        "validate": python_tool("tools/validate_data.py"),
        "ruff": python_tool("-m", "ruff", "check", "tools"),
        "tests": python_tool("-m", "pytest", "tools/tests", "-q", "-x"),
        "vectors": python_tool("tools/gen_conformance.py", "--check"),
    }
    ok = True
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {name: pool.submit(run, cmd, False, True) for name, cmd in jobs.items()}
        for name, future in futures.items():
            result = future.result()
            tail = (result.stdout or "").strip().splitlines()[-1:] or [""]
            print(f"  {'ok  ' if result.returncode == 0 else 'FAIL'} {name}: {tail[0]}")
            if result.returncode != 0:
                ok = False
                print(result.stdout)
    print(f"  checks took {time.time() - started:.0f}s")
    return ok


def current_branch() -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True).stdout.strip()


def format_cpp() -> None:
    """Formats the C++ files that changed with clang-format (desktop/.clang-format), when it is installed."""
    tool = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("clang-format.exe" if os.name == "nt" else "clang-format")
    if not tool.exists():
        return
    changed = run(["git", "diff", "--name-only", "HEAD"], capture=True).stdout.split()
    changed += run(["git", "ls-files", "--others", "--exclude-standard"], capture=True).stdout.split()
    files = [f for f in changed if f.startswith("desktop/") and f.endswith((".cpp", ".hpp")) and (ROOT / f).exists()]
    for f in files:
        run([str(tool), "-i", f])
    if files:
        print(f"  formatted {len(files)} C++ file(s)")


def commit(title: str, trailers: list[str]) -> None:
    message = title + ("\n\n" + "\n".join(trailers) if trailers else "")
    format_cpp()
    run(["git", "add", "-A"])
    if run(["git", "diff", "--cached", "--quiet"], check=False).returncode == 0:
        print("  nothing to commit; shipping the commits already on the branch")
        return
    run(["git", "commit", "--quiet", "-s", "-m", message])


def wait_for_checks(pr: str) -> tuple[bool, str]:
    """Waits until every check has finished; returns (all passed, a line per check)."""
    deadline = time.time() + 45 * 60
    time.sleep(20)  # the checks need a moment to be registered
    while time.time() < deadline:
        out = run(["gh", "pr", "checks", pr, "--json", "name,bucket"], check=False, capture=True).stdout
        try:
            rows = json.loads(out)
        except json.JSONDecodeError:
            rows = []
        if rows and all(r["bucket"] != "pending" for r in rows):
            summary = ", ".join(f"{r['name']} {r['bucket']}" for r in rows)
            return all(r["bucket"] in ("pass", "skipping") for r in rows), summary
        time.sleep(10)
    return False, "timed out"


def refresh_play(pr: str, play: Path) -> None:
    out = run(["gh", "pr", "checks", pr, "--json", "name,link"], capture=True).stdout
    link = next(r["link"] for r in json.loads(out) if r["name"] == "windows-msvc")
    run_id = re.search(r"/runs/(\d+)", link).group(1)
    with tempfile.TemporaryDirectory() as tmp:
        run(["gh", "run", "download", run_id, "-n", "aethermoor-windows-msvc", "-D", tmp])
        archive = next(Path(tmp).glob("*.zip"))
        with zipfile.ZipFile(archive) as z:
            z.extractall(Path(tmp) / "build")
        build = Path(tmp) / "build"
        shutil.rmtree(play / "data", ignore_errors=True)
        shutil.copytree(build / "data", play / "data")
        shutil.copy(build / "PLAY.txt", play / "PLAY.txt")
        busy = []
        for name in ("aethermoor.exe", "SDL3.dll"):
            try:
                shutil.copy(build / name, play / name)
            except PermissionError:
                busy.append(name)
        print(f"  play build refreshed in {play}" + (f" (the program was running: {', '.join(busy)} not replaced)" if busy else ""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("title", help="commit title and pull request title (Conventional Commits)")
    parser.add_argument("--body-file", help="file with the pull request description")
    parser.add_argument("--trailer", action="append", default=[], help="a line for the end of the commit message (repeatable)")
    parser.add_argument("--play", help="the play folder to refresh after the merge")
    parser.add_argument("--no-merge", action="store_true", help="stop once the checks have passed")
    parser.add_argument("--skip-checks", action="store_true", help="skip the local checks")
    args = parser.parse_args()
    trailers = args.trailer or [t for t in os.environ.get("SHIP_TRAILERS", "").split("|") if t]

    branch = current_branch()
    if branch in ("main", "master"):
        print("switch to a branch first (feat/..., fix/..., chore/...)")
        return 2
    print("1. local checks")
    if not args.skip_checks and not checks():
        return 1
    print("2. commit and push")
    commit(args.title, trailers)
    run(["git", "push", "--quiet", "-u", "origin", branch])
    print("3. pull request")
    existing = run(["gh", "pr", "view", branch, "--json", "url", "-q", ".url"], check=False, capture=True)
    if existing.returncode == 0 and existing.stdout.strip().startswith("http"):
        url = existing.stdout.strip()
    else:
        body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else ""
        url = run(["gh", "pr", "create", "--title", args.title, "--body", body], capture=True).stdout.strip().splitlines()[-1]
    print(f"  {url}")
    ok, summary = wait_for_checks(url)
    print(f"  {summary}")
    if not ok:
        print("the checks did not all pass: not merged")
        return 1
    if args.no_merge:
        return 0
    print("4. merge")
    run(["gh", "pr", "merge", url, "--squash", "--delete-branch"])
    run(["git", "checkout", "--quiet", "main"])
    run(["git", "pull", "--quiet"])
    print(f"  main is at {run(['git', 'log', '--oneline', '-1'], capture=True).stdout.strip()}")
    if args.play:
        print("5. play build")
        refresh_play(url, Path(args.play))
    return 0


if __name__ == "__main__":
    sys.exit(main())
