#!/usr/bin/env python3
"""
Ingest WDNR's own per-lake fish list (and abundance) from their lake pages.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
WDNR publishes, for each lake, a list like:

    Panfish (Abundant), Largemouth Bass (Common), Northern Pike (Common),
    Smallmouth Bass (Present), Trout (Present), Walleye (Present)

That is genuinely better than this project's stocking-derived presence in
two ways: it is WDNR's own assessment rather than an inference, and it
carries an **abundance** WDNR never exposes anywhere else this project
reads. It also catches self-sustaining populations that are never stocked
-- exactly the blind spot of stocking-only evidence.

But it is **coarser than species level**. The entire published vocabulary
is nine categories:

    Panfish, Largemouth Bass, Smallmouth Bass, Northern Pike, Walleye,
    Musky, Trout, Catfish, Sturgeon

"Trout (Present)" does not say brook, brown or rainbow -- and those have
materially different thermal thresholds (brook trout is the least
heat-tolerant of the three). "Panfish" covers bluegill, crappie and
yellow perch, which this app models separately.

So this data is stored and displayed as WDNR's own answer to "what is in
this lake", **never expanded into specific species** to drive physiology
matching. Turning "Trout (Present)" into a brook-trout temperature match
would be inventing a fact WDNR did not state.

HOW A LAKE IS IDENTIFIED
------------------------
WDNR's lake pages are keyed by WBIC, which this project does not hold.
WBIC is resolved by point-in-polygon against WDNR's own regulations layer
using a real access-point coordinate -- the same approach, and the same
reasoning, as v2_fishing_regulations: Wisconsin has eleven unrelated
waters named "Devils Lake", so name matching would silently pick one.

Usage:
    python analysis/v2_wdnr_lake_species.py --limit 20   # try a subset
    python analysis/v2_wdnr_lake_species.py              # full ingest (resumable)
"""

import argparse
import datetime
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v2_fishing_regulations as regs  # noqa: E402

DB_PATH = Path(__file__).parent.parent / "data" / "v1" / "v1_full_run_results.db"
LAKE_PAGE_URL = "https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic={}"
USER_AGENT = "fishin/1.0 (non-commercial; Wisconsin fishing conditions)"

# Polite spacing between requests to a public agency server.
THROTTLE_SECONDS = 0.5

# The complete published vocabulary, recorded so a future reader can see
# that the coarseness is WDNR's, not a parsing artefact.
KNOWN_CATEGORIES = {
    "Panfish", "Largemouth Bass", "Smallmouth Bass", "Northern Pike",
    "Walleye", "Musky", "Trout", "Catfish", "Sturgeon",
}


def init_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS wdnr_wbic_map (
            waterbody_name TEXT NOT NULL,
            county TEXT NOT NULL,
            wbic INTEGER,
            resolved_via TEXT NOT NULL,
            resolved_at TEXT NOT NULL,
            PRIMARY KEY (waterbody_name, county)
        );
        CREATE TABLE IF NOT EXISTS wdnr_lake_species (
            wbic INTEGER NOT NULL,
            lake_name TEXT,
            acres REAL,
            category TEXT NOT NULL,
            abundance TEXT,
            retrieved_at TEXT NOT NULL,
            PRIMARY KEY (wbic, category)
        );
        CREATE TABLE IF NOT EXISTS wdnr_lake_fetch_log (
            wbic INTEGER PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_wbic_map_wbic ON wdnr_wbic_map(wbic);
        """
    )
    conn.commit()


def waters_needing_wbic(conn: sqlite3.Connection, limit: int | None = None) -> list:
    """One representative real coordinate per distinct water, preferring the
    matched V1 waterbody name so the result joins to existing records."""
    query = """
        SELECT
            COALESCE(matched_waterbody_name, waterbody_name) AS waterbody_name,
            COALESCE(matched_county, county) AS county,
            AVG(latitude) AS lat, AVG(longitude) AS lon
        FROM access_points
        GROUP BY waterbody_name, county
        HAVING waterbody_name IS NOT NULL
        ORDER BY waterbody_name
    """
    rows = [dict(r) for r in conn.execute(query)]
    done = {
        (r[0], r[1])
        for r in conn.execute("SELECT waterbody_name, county FROM wdnr_wbic_map")
    }
    pending = [r for r in rows if (r["waterbody_name"], r["county"]) not in done]
    return pending[:limit] if limit else pending


def resolve_wbic(conn: sqlite3.Connection, row: dict) -> int | None:
    """WBIC for one water, by point-in-polygon against WDNR's regulations
    layer. Returns None when the point matches no regulated water, or when
    it matches more than one -- guessing between them is the failure mode
    this whole approach exists to avoid."""
    result = regs.get_regulations(conn, row["lat"], row["lon"])
    if not result or result.get("status") != "ok":
        return None
    wbic = result["waters"][0].get("wbic")
    return int(wbic) if wbic else None


def parse_lake_page(html: str) -> dict:
    """Pull the fish list, name and acreage out of a lake page.

    The markup is a stable, plainly-structured block:
        <h3>Fish</h3><ul class='fishBullets'><li>Panfish (Abundant)</li>...
    """
    name_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    lake_name = re.sub(r"<[^>]+>", "", name_match.group(1)).strip() if name_match else None

    acres = None
    # The real wording is "is a 374 acre lake located in Sauk County" --
    # singular "acre", so a plural-only pattern silently finds nothing.
    acres_match = re.search(r"(?i)\ba\s+([\d,]+)\s*acre\b", html)
    if acres_match:
        try:
            acres = float(acres_match.group(1).replace(",", ""))
        except ValueError:
            acres = None

    species = []
    block = re.search(r"<ul class='fishBullets'>(.*?)</ul>", html, re.S)
    if block:
        for item in re.findall(r"<li>(.*?)</li>", block.group(1), re.S):
            text = re.sub(r"<[^>]+>", "", item).strip()
            if not text:
                continue
            abundance = None
            paren = re.search(r"\(([^)]+)\)\s*$", text)
            if paren:
                abundance = paren.group(1).strip()
                text = text[: paren.start()].strip()
            species.append({"category": text, "abundance": abundance})

    return {"lake_name": lake_name, "acres": acres, "species": species}


def fetch_lake_page(wbic: int, timeout: int = 30) -> str:
    request = urllib.request.Request(
        LAKE_PAGE_URL.format(wbic), headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def run(limit: int | None = None, skip_wbic: bool = False) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    init_tables(conn)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Phase 1: resolve WBIC for waters we don't have one for ---
    if not skip_wbic:
        pending = waters_needing_wbic(conn, limit)
        print(f"Resolving WBIC for {len(pending)} waters...", file=sys.stderr)
        for i, row in enumerate(pending, 1):
            try:
                wbic = resolve_wbic(conn, row)
                via = "spatial" if wbic else "unresolved"
            except Exception as e:  # noqa: BLE001 -- one water must not halt the run
                wbic, via = None, f"error:{type(e).__name__}"
            conn.execute(
                "INSERT OR REPLACE INTO wdnr_wbic_map (waterbody_name, county, wbic, resolved_via, resolved_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["waterbody_name"], row["county"], wbic, via, now),
            )
            if i % 25 == 0:
                conn.commit()
                print(f"  [{i}/{len(pending)}] {row['waterbody_name']} -> {wbic}", file=sys.stderr)
            time.sleep(THROTTLE_SECONDS)
        conn.commit()

    # --- Phase 2: fetch each distinct lake page once ---
    wbics = [
        r[0] for r in conn.execute(
            "SELECT DISTINCT wbic FROM wdnr_wbic_map WHERE wbic IS NOT NULL "
            "AND wbic NOT IN (SELECT wbic FROM wdnr_lake_fetch_log) ORDER BY wbic"
        )
    ]
    if limit:
        wbics = wbics[:limit]

    print(f"Fetching {len(wbics)} lake pages...", file=sys.stderr)
    ok = failed = 0
    for i, wbic in enumerate(wbics, 1):
        try:
            parsed = parse_lake_page(fetch_lake_page(wbic))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            conn.execute(
                "INSERT OR REPLACE INTO wdnr_lake_fetch_log (wbic, fetched_at, status) VALUES (?, ?, ?)",
                (wbic, now, f"error:{type(e).__name__}"),
            )
            failed += 1
            time.sleep(THROTTLE_SECONDS)
            continue

        for entry in parsed["species"]:
            conn.execute(
                "INSERT OR REPLACE INTO wdnr_lake_species "
                "(wbic, lake_name, acres, category, abundance, retrieved_at) VALUES (?, ?, ?, ?, ?, ?)",
                (wbic, parsed["lake_name"], parsed["acres"], entry["category"], entry["abundance"], now),
            )
        conn.execute(
            "INSERT OR REPLACE INTO wdnr_lake_fetch_log (wbic, fetched_at, status) VALUES (?, ?, ?)",
            (wbic, now, "ok" if parsed["species"] else "no_fish_section"),
        )
        ok += 1
        if i % 25 == 0:
            conn.commit()
            print(f"  [{i}/{len(wbics)}] wbic {wbic}: {len(parsed['species'])} categories", file=sys.stderr)
        time.sleep(THROTTLE_SECONDS)

    conn.commit()

    total_species = conn.execute("SELECT COUNT(*) FROM wdnr_lake_species").fetchone()[0]
    lakes = conn.execute("SELECT COUNT(DISTINCT wbic) FROM wdnr_lake_species").fetchone()[0]
    unknown = conn.execute(
        "SELECT DISTINCT category FROM wdnr_lake_species"
    ).fetchall()
    surprises = sorted({r[0] for r in unknown} - KNOWN_CATEGORIES)

    print(f"\nPages fetched: {ok} ok, {failed} failed", file=sys.stderr)
    print(f"Stored {total_species} species rows across {lakes} lakes", file=sys.stderr)
    if surprises:
        print(f"Categories outside the documented vocabulary: {surprises}", file=sys.stderr)
    conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=None, help="only process the first N waters/pages")
    parser.add_argument("--skip-wbic", action="store_true", help="skip WBIC resolution, only fetch pages")
    args = parser.parse_args()
    return run(limit=args.limit, skip_wbic=args.skip_wbic)


if __name__ == "__main__":
    sys.exit(main())
