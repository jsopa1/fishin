#!/usr/bin/env python3
"""
A repeatable pipeline that inspects the current, real state of this repo
-- not a description of what was built, a live check of what's actually
true right now. Every section either runs a real command/query against
this checkout or explicitly says it couldn't.

Run: python inspect_state.py
Exit code is non-zero if anything genuinely actionable was found (a
dirty tree, a failing test, an out-of-sync doc claim) -- 0 means clean.
"""

import re
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent
PROBLEMS: list[str] = []


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def run(cmd: list[str], cwd: Path = REPO_ROOT) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


# ---------------------------------------------------------------------------
# 1. Git state
# ---------------------------------------------------------------------------

def check_git() -> None:
    section("1. Git")
    _, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, status = run(["git", "status", "--porcelain"])
    print(f"Branch: {branch}")
    if status:
        print(f"Working tree: DIRTY\n{status}")
        PROBLEMS.append("uncommitted changes in the working tree")
    else:
        print("Working tree: clean")

    run(["git", "fetch", "origin"])
    _, ahead = run(["git", "log", "origin/main..HEAD", "--oneline"])
    _, behind = run(["git", "log", "HEAD..origin/main", "--oneline"])
    if ahead:
        print(f"Ahead of origin/main:\n{ahead}")
        PROBLEMS.append("local commits not pushed to origin/main")
    if behind:
        print(f"Behind origin/main (pull needed):\n{behind}")
        PROBLEMS.append("origin/main has commits not merged locally")
    if not ahead and not behind:
        print("In sync with origin/main")

    _, log = run(["git", "log", "--oneline", "-8"])
    print(f"\nLast 8 commits:\n{log}")


# ---------------------------------------------------------------------------
# 2. Test suite
# ---------------------------------------------------------------------------

def check_tests() -> int | None:
    section("2. Test suite")
    code, output = run([sys.executable, "-m", "pytest", "-q"])
    tail = "\n".join(output.splitlines()[-8:])
    print(tail)
    match = re.search(r"(\d+) passed", output)
    count = int(match.group(1)) if match else None
    if code != 0:
        PROBLEMS.append("test suite is failing")
    if "failed" in output.lower() and "0 failed" not in output.lower():
        PROBLEMS.append("one or more tests failing")
    return count


# ---------------------------------------------------------------------------
# 3. Content database (data/v1/v1_full_run_results.db)
# ---------------------------------------------------------------------------

def check_content_db() -> None:
    section("3. Content database")
    db_path = REPO_ROOT / "data" / "v1" / "v1_full_run_results.db"
    if not db_path.exists():
        print("NOT FOUND -- app cannot serve any data without this file")
        PROBLEMS.append("content database missing")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        run_row = conn.execute(
            "SELECT run_timestamp, total_waterbodies FROM runs ORDER BY run_timestamp DESC LIMIT 1"
        ).fetchone()
        print(f"Latest run: {run_row[0]} -- {run_row[1]} waterbodies" if run_row else "No runs found")

        access_points = conn.execute("SELECT COUNT(*) FROM access_points").fetchone()[0]
        print(f"Access points: {access_points:,}")

        wdnr_lakes = conn.execute("SELECT COUNT(DISTINCT wbic) FROM wdnr_lake_species").fetchone()[0]
        print(f"WDNR lake-species records: {wdnr_lakes:,} lakes")

        refresh = conn.execute(
            "SELECT finished_at FROM temperature_refreshes ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
        print(f"Last temperature refresh: {refresh[0] if refresh else 'never'}")
    except sqlite3.OperationalError as e:
        print(f"Query failed: {e}")
        PROBLEMS.append(f"content database query failed: {e}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. User database (webapp/user_data.py -- feedback + analytics only)
# ---------------------------------------------------------------------------

def check_user_db() -> None:
    section("4. User database (feedback + analytics)")
    db_path = REPO_ROOT / "data" / "v1" / "user_data.db"
    if not db_path.exists():
        print("Not created yet (no /feedback submissions or page views recorded locally)")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        print(f"Tables: {sorted(tables)}")
        if {"users", "catches", "login_attempts"} & tables:
            PROBLEMS.append("stale accounts tables still present in user_data.db (schema not cleaned up)")
        if "feedback" in tables:
            n = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            print(f"Feedback submissions: {n}")
        if "events" in tables:
            n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            print(f"Analytics events logged: {n}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. Route inventory -- what the app actually serves right now
# ---------------------------------------------------------------------------

def check_routes() -> None:
    section("5. Live routes (parsed from webapp/app.py + webapp/*.py)")
    routes = []
    for py_file in (REPO_ROOT / "webapp").glob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        routes += re.findall(r'@\w+\.route\("([^"]+)"', text)
    routes = sorted(set(routes))
    print("\n".join(routes))

    should_not_exist = {"/login", "/signup", "/account"}
    leftover = should_not_exist & set(routes)
    if leftover:
        print(f"\nWARNING: account routes still registered: {leftover}")
        PROBLEMS.append(f"account routes still present: {leftover}")
    else:
        print("\nConfirmed: no /login, /signup, or /account route registered")


# ---------------------------------------------------------------------------
# 6. Live server health (best-effort -- skipped if nothing is running)
# ---------------------------------------------------------------------------

def check_live_server() -> None:
    section("6. Live dev server (best-effort)")
    try:
        with urllib.request.urlopen("http://localhost:5000/healthz", timeout=2) as resp:
            print(f"http://localhost:5000/healthz -> {resp.status}: {resp.read().decode()}")
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        print("No dev server reachable on :5000 -- skipped (this is fine if nothing is running)")


# ---------------------------------------------------------------------------
# 7. Doc-drift check -- do README's claimed numbers match reality?
# ---------------------------------------------------------------------------

def check_doc_drift(actual_test_count: int | None) -> None:
    section("7. Documentation drift")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    badge_match = re.search(r"(\d+) tests passing", readme)
    if badge_match and actual_test_count is not None:
        claimed = int(badge_match.group(1))
        if claimed != actual_test_count:
            print(f"README claims {claimed} tests, pytest just counted {actual_test_count}")
            PROBLEMS.append(f"README test-count badge is stale ({claimed} vs actual {actual_test_count})")
        else:
            print(f"README test count ({claimed}) matches actual ({actual_test_count})")

    decisions_text = (REPO_ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    actual_decisions = len(re.findall(r"^## \d{3} ", decisions_text, re.MULTILINE))
    claimed_match = re.search(r"has (\d+) dated, rationale-backed entries", readme)
    if claimed_match:
        claimed = int(claimed_match.group(1))
        if claimed != actual_decisions:
            print(f"README claims {claimed} DECISIONS.md entries, actually {actual_decisions}")
            PROBLEMS.append(f"README decision-count is stale ({claimed} vs actual {actual_decisions})")
        else:
            print(f"README decision count ({claimed}) matches actual ({actual_decisions})")


def main() -> int:
    check_git()
    test_count = check_tests()
    check_content_db()
    check_user_db()
    check_routes()
    check_live_server()
    check_doc_drift(test_count)

    section("Summary")
    if PROBLEMS:
        print(f"{len(PROBLEMS)} thing(s) worth a look:")
        for p in PROBLEMS:
            print(f"  - {p}")
        return 1
    print("Clean -- nothing actionable found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
