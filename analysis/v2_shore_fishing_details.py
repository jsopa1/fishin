#!/usr/bin/env python3
"""
V2 shore-fishing detail enrichment: real per-site info scraped from
WDNR's own shorefishing.aspx detail pages -- site directions, amenities,
ADA accessibility, and (the single most valuable field for this
project's "fill the species gap" goal) the "Available Fish Species" list
WDNR publishes for each site.

This matters specifically for shore-fishing sites that don't match a V1
waterbody (V1's own species data comes from stocking/survey records
scoped to its own waterbody universe): the species list here comes
directly from WDNR's shore-fishing inventory itself, independent of V1,
so it fills a real gap rather than leaving those sites with no species
information at all.

Source (live, one page per site -- the same DNR host already referenced
by MORE_INFO_URL on every shore_fishing row in access_points):
    https://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=<n>

This is server-rendered ASP.NET WebForms HTML, not a REST API -- there is
no JSON endpoint. Parsed with a small, precise regex matching this page's
consistent <td><b>LABEL</b></td><td><span>VALUE</span> row structure,
verified stable across multiple real site IDs (21, 5, 116) before writing
this -- appropriate for one specific, unchanging real page template, not
a general-purpose HTML parser.

Does NOT use this page's own Latitude/Longitude fields: WDNR's own data
has at least one verified data-entry error swapping lat/lon on a real
record (site ID 5, Namekagon Lake -- "Latitude: -91.08", "Longitude:
46.21", backwards for a Wisconsin site). This project already has a
trustworthy coordinate for every shore_fishing access point from the
live ArcGIS layer (analysis/v2_access_points.py); this script only adds
the real text fields that layer doesn't carry.

Keyed by more_info_url (stable, unique per site) rather than
access_points.id (an AUTOINCREMENT primary key that access_points.py
regenerates on every re-run) -- so this enrichment survives a future
access-points re-ingestion without silently attaching to the wrong site.

Usage:
    python analysis/v2_shore_fishing_details.py                # full live pull
    python analysis/v2_shore_fishing_details.py --limit 10      # smoke test
"""

import argparse
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v1_conditions_biology_forecast as v1  # noqa: E402

DB_PATH = v1.DATA_V1 / "v1_full_run_results.db"

FETCH_THROTTLE_SECONDS = 0.4

FIELD_PATTERN = re.compile(
    r'<td bgcolor="#DEE8F5"><font color="#333333"><b>([^<]+)</b></font></td>'
    r'<td><font color="#333333">\s*<span[^>]*>([^<]*)</span>',
    re.DOTALL,
)

# Raw WDNR label text -> our column name. Latitude/Longitude/WTM X/WTM Y
# deliberately excluded -- see module docstring. "Vehicle Stalls" and
# "Restrooms" appear twice on the page (general info vs. ADA section)
# under different exact label text ("No. of Vehicle Stalls" / "Type of
# Restrooms" vs. the bare "Vehicle Stalls" / "Restrooms" in the ADA
# table), so there's no collision walking the page top-to-bottom.
LABEL_MAP = {
    "Directions": "directions",
    "Fishing Trail": "fishing_trail",
    "Fixed Pier": "fixed_pier",
    "End of Pier Depth": "end_of_pier_depth",
    "Travel Route Surface": "travel_route_surface",
    "No. of Vehicle Stalls": "vehicle_stalls",
    "No. of Vehicle and Trailer Stalls": "vehicle_trailer_stalls",
    "Type of Restrooms": "restrooms",
    "Available Fish Species": "fish_species_raw",
    "Fish Cleaning Area": "fish_cleaning_area",
    "Additional Amenities": "additional_amenities",
    "Comments": "comments",
    "Vehicle Stalls": "ada_vehicle_stalls",
    "Vehicle / Trailer Stalls": "ada_vehicle_trailer_stalls",
    "Restrooms": "ada_restrooms",
    "Property Manager": "property_manager",
    "Phone #": "property_manager_phone",
}

DETAIL_COLUMNS = list(dict.fromkeys(LABEL_MAP.values()))  # dedupe, preserve order


# "no info" markers only, not fact corrections -- WDNR's own pages spell
# "unknown" three different ways across real records (verified: UKNOWN on
# site 109, UNKOWN on 2 others). Recognizing all three still shows every
# real fact verbatim; it only stops literal typo'd placeholder text like
# "UKNOWN" from rendering as if it were real data. Species text is never
# touched by this -- see parse_species_list's own no-"fixing" discipline.
PLACEHOLDER_VALUES = {"unknown", "uknown", "unkown", "none", "n/a", "na", ""}


def _clean(value: str):
    v = (value or "").strip()
    if v.lower() in PLACEHOLDER_VALUES:
        return None
    return v


def extract_site_id(more_info_url: str):
    if not more_info_url:
        return None
    parsed = urllib.parse.urlparse(more_info_url)
    qs = urllib.parse.parse_qs(parsed.query)
    ids = qs.get("ID")
    return ids[0] if ids else None


def parse_detail_page(html: str) -> dict:
    """Pure, testable: raw HTML -> {column_name: cleaned value}. Every
    WDNR label used as a LABEL_MAP key is textually distinct on the page
    (the ADA table's bare "Vehicle Stalls"/"Restrooms" differ from the
    general table's "No. of Vehicle Stalls"/"Type of Restrooms"), so each
    column is set at most once per page."""
    fields = {}
    for label, raw_value in FIELD_PATTERN.findall(html):
        column = LABEL_MAP.get(label.strip())
        if column:
            fields[column] = _clean(raw_value)
    return fields


def parse_species_list(fish_species_raw) -> list:
    """Splits WDNR's raw comma-separated species text into a list,
    verbatim -- no spelling correction, no canonicalization. WDNR's own
    text includes real inconsistencies (e.g. "NORTHEN" vs "NORTHERN")
    this project does not silently "fix": shown exactly as WDNR wrote
    it, per the project's no-fabrication/no-reinterpretation discipline.

    Only splits on top-level commas -- some real WDNR entries nest a
    second comma-separated list inside parentheses, e.g. "PIKE
    (NORTHERN, YELLOW), BASS (LG. MOUTH, ROCK)" (site ID 31, Round Lake).
    A naive split(",") would truncate that into "BASS (LG. MOUTH" and
    " ROCK)" -- broken, not just imprecise. This keeps a parenthetical
    group as one atomic phrase rather than guessing how WDNR meant it to
    decompose into individual species."""
    if not fish_species_raw:
        return []
    parts = []
    depth = 0
    current = []
    for ch in fish_species_raw:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def fetch_detail_page(site_id: str) -> str:
    """Live network call -- not exercised by unit tests (see
    parse_detail_page/parse_species_list for the tested logic)."""
    url = f"https://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID={site_id}"
    req = urllib.request.Request(url, headers={"User-Agent": v1.USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("iso-8859-1")


def init_db(conn: sqlite3.Connection):
    columns_sql = ",\n            ".join(f"{c} TEXT" for c in DETAIL_COLUMNS)
    conn.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS shore_fishing_details (
            more_info_url TEXT PRIMARY KEY,
            {columns_sql},
            fetched_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shore_fishing_species (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            more_info_url TEXT NOT NULL,
            species_text TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_shore_fishing_species_text
            ON shore_fishing_species(species_text);
        CREATE INDEX IF NOT EXISTS idx_shore_fishing_species_url
            ON shore_fishing_species(more_info_url);
        """
    )
    conn.commit()


def write_details(conn: sqlite3.Connection, more_info_url: str, fields: dict, fetched_at: str):
    conn.execute("DELETE FROM shore_fishing_details WHERE more_info_url = ?", (more_info_url,))
    values = [fields.get(c) for c in DETAIL_COLUMNS]
    placeholders = ", ".join("?" * len(DETAIL_COLUMNS))
    conn.execute(
        f"INSERT INTO shore_fishing_details (more_info_url, {', '.join(DETAIL_COLUMNS)}, fetched_at) "
        f"VALUES (?, {placeholders}, ?)",
        [more_info_url] + values + [fetched_at],
    )
    conn.execute("DELETE FROM shore_fishing_species WHERE more_info_url = ?", (more_info_url,))
    species = parse_species_list(fields.get("fish_species_raw"))
    conn.executemany(
        "INSERT INTO shore_fishing_species (more_info_url, species_text) VALUES (?, ?)",
        [(more_info_url, s) for s in species],
    )
    conn.commit()


def run(limit=None, db_path=None) -> dict:
    import datetime

    db_path = db_path or DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    rows = conn.execute(
        "SELECT DISTINCT more_info_url FROM access_points "
        "WHERE source_type = 'shore_fishing' AND more_info_url IS NOT NULL"
    ).fetchall()
    if limit:
        rows = rows[:limit]

    fetched = 0
    species_found = 0
    for row in rows:
        more_info_url = row["more_info_url"]
        site_id = extract_site_id(more_info_url)
        if not site_id:
            continue
        try:
            html = fetch_detail_page(site_id)
        except Exception as exc:  # noqa: BLE001 -- one bad fetch shouldn't kill the whole run
            print(f"  skip {more_info_url}: {exc}")
            time.sleep(FETCH_THROTTLE_SECONDS)
            continue
        fields = parse_detail_page(html)
        fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_details(conn, more_info_url, fields, fetched_at)
        fetched += 1
        if fields.get("fish_species_raw"):
            species_found += 1
        time.sleep(FETCH_THROTTLE_SECONDS)

    conn.close()
    print(f"Fetched detail pages for {fetched}/{len(rows)} shore fishing sites ({species_found} with a species list).")
    return {"fetched": fetched, "total": len(rows), "with_species": species_found}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap sites fetched (smoke test)")
    args = parser.parse_args()
    run(limit=args.limit)
