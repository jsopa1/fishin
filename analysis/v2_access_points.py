#!/usr/bin/env python3
"""
V2 access-point layer: real Wisconsin DNR public boat access and shore
fishing site locations, pulled live from WDNR's own ArcGIS REST service
and persisted into the same results database V1 already uses, so the
web app's map can show them alongside the existing waterbody data.

Source (live, queried at run time -- not scraped, not estimated):
  https://dnrmaps.wi.gov/arcgis2/rest/services/PR_Recreation/PR_Boat_Access_Shore_Fishing_WTM_Ext/MapServer
    layer 1: Shore Fishing Site   (~142 real DNR-maintained sites)
    layer 2: Boat Access Sites    (~3,135 real sites: ramp + carry-in)

This is the same public WDNR service documented at
https://dnr.wisconsin.gov/topic/lands/boataccess -- "over 2,000 identified
public boat access sites and over 100 developed shore fishing sites".

Each record is linked to an existing data/v1 waterbody_results entry only
when its (normalized name, county) matches one exactly -- reusing the
same _norm/_norm_county/_county_matches helpers v1_full_run.py's own
dedup logic uses. Per Decision #005's no-fabrication discipline, an
access point that doesn't match a known waterbody is still stored (it's
still a real, useful map point) but its matched_waterbody_name/
matched_county stay NULL rather than guessed.

Usage:
    python analysis/v2_access_points.py                # full live pull
    python analysis/v2_access_points.py --limit 50      # smoke test
"""

import argparse
import datetime
import sqlite3
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v1_conditions_biology_forecast as v1  # noqa: E402

DB_PATH = v1.DATA_V1 / "v1_full_run_results.db"

MAPSERVER_BASE = (
    "https://dnrmaps.wi.gov/arcgis2/rest/services/PR_Recreation/"
    "PR_Boat_Access_Shore_Fishing_WTM_Ext/MapServer"
)
SHORE_FISHING_LAYER = 1
BOAT_ACCESS_LAYER = 2
PAGE_SIZE = 2000  # this MapServer's own maxRecordCount, confirmed via .../MapServer/2?f=json


# ---------------------------------------------------------------------------
# Live fetch -- not exercised by unit tests (see normalize_* below, which
# is where the actually-testable logic lives).
# ---------------------------------------------------------------------------

def fetch_layer(layer_id: int, base_url: str = MAPSERVER_BASE, page_size: int = PAGE_SIZE) -> list:
    """Pages through an ArcGIS REST feature layer and returns every raw
    GeoJSON feature (WGS84 lon/lat, real ArcGIS attribute names)."""
    features = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "outSR": "4326",
            "f": "geojson",
            "resultRecordCount": str(page_size),
            "resultOffset": str(offset),
        }
        url = f"{base_url}/{layer_id}/query?{urllib.parse.urlencode(params)}"
        data = v1.http_get_json(url, timeout=30)
        page = data.get("features", [])
        features.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return features


# ---------------------------------------------------------------------------
# Pure normalization -- unit tested, no network.
# ---------------------------------------------------------------------------

def normalize_boat_access(features: list) -> list:
    rows = []
    for feat in features:
        p = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom or geom.get("type") != "Point":
            continue
        if (p.get("ABANDON_FLAG") or "").strip().lower() == "yes":
            continue
        waterbody = (p.get("WATERBODY_NAME_TEXT") or "").strip()
        county = (p.get("COUNTY_NAME_TEXT") or "").strip()
        if not waterbody or not county:
            continue
        landing_type = (p.get("LANDING_TYPE_CODE") or "").strip().upper()
        source_type = "boat_carry_in" if landing_type == "CARRY-IN" else "boat_ramp"
        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
        rows.append({
            "source_type": source_type,
            "facility_name": (p.get("LMS_BOAT_LANDING_NAME") or "").strip() or None,
            "waterbody_name": waterbody,
            "county": county,
            "municipality": (p.get("MUNICIPALITY_NAME_TEXT") or "").strip() or None,
            "latitude": lat,
            "longitude": lon,
            "ada_accessible": (p.get("ADA_ACCESSIBLE_FEATURE_CODE") or "").strip() or None,
            "ownership": (p.get("OWNERSHIP_MANAGER_NAME_TEXT") or p.get("OWNERSHIP_NAME_TEXT") or "").strip() or None,
            "more_info_url": None,
        })
    return rows


def normalize_shore_fishing(features: list) -> list:
    rows = []
    for feat in features:
        p = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom or geom.get("type") != "Point":
            continue
        waterbody = (p.get("WATERBODY_NAME_TEXT") or "").strip()
        county = (p.get("COUNTY_NAME_TEXT") or "").strip()
        if not waterbody or not county:
            continue
        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
        rows.append({
            "source_type": "shore_fishing",
            "facility_name": (p.get("FACILITY_NAME_TEXT") or "").strip() or None,
            "waterbody_name": waterbody,
            "county": county,
            "municipality": (p.get("MUNICIPALITY_NAME_TEXT") or "").strip() or None,
            "latitude": lat,
            "longitude": lon,
            "ada_accessible": None,
            "ownership": None,
            "more_info_url": (p.get("MORE_INFO_URL") or "").strip() or None,
        })
    return rows


def build_waterbody_index(conn: sqlite3.Connection) -> dict:
    """normalized waterbody name -> [(real waterbody_name, real county), ...]
    from V1's most recent run, for linking access points to a real
    waterbody detail page. Grouped by name so link_to_waterbody only has
    to loose-match county among same-name candidates, not the whole set."""
    index: dict = {}
    row = conn.execute("SELECT run_timestamp FROM runs ORDER BY finished_at DESC LIMIT 1").fetchone()
    if row is None:
        return index
    latest_run = row[0]
    cur = conn.execute(
        "SELECT DISTINCT waterbody_name, county FROM waterbody_results WHERE run_timestamp = ?",
        (latest_run,),
    )
    for name, county in cur.fetchall():
        index.setdefault(v1._norm(name), []).append((name, county))
    return index


def link_to_waterbody(row: dict, index: dict):
    """Exact normalized-name match, with the same loose county match
    v1_full_run.py's own dedup uses -- never a fuzzy name guess. Returns
    (matched_name, matched_county) or (None, None)."""
    candidates = index.get(v1._norm(row["waterbody_name"]))
    if not candidates:
        return None, None
    for real_name, real_county in candidates:
        if v1._county_matches(row["county"], real_county):
            return real_name, real_county
    return None, None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def init_db(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS access_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            facility_name TEXT,
            waterbody_name TEXT NOT NULL,
            county TEXT NOT NULL,
            municipality TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            ada_accessible TEXT,
            ownership TEXT,
            more_info_url TEXT,
            matched_waterbody_name TEXT,
            matched_county TEXT
        );

        CREATE TABLE IF NOT EXISTS access_points_meta (
            id INTEGER PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            total_boat_ramp INTEGER NOT NULL,
            total_boat_carry_in INTEGER NOT NULL,
            total_shore_fishing INTEGER NOT NULL,
            source_url TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_access_points_matched
            ON access_points(matched_waterbody_name, matched_county);
        CREATE INDEX IF NOT EXISTS idx_access_points_source_type
            ON access_points(source_type);
        """
    )
    conn.commit()


def write_access_points(conn: sqlite3.Connection, rows: list, fetched_at: str, source_url: str):
    conn.execute("DELETE FROM access_points")
    conn.executemany(
        """INSERT INTO access_points
           (source_type, facility_name, waterbody_name, county, municipality,
            latitude, longitude, ada_accessible, ownership, more_info_url,
            matched_waterbody_name, matched_county)
           VALUES (:source_type, :facility_name, :waterbody_name, :county, :municipality,
                   :latitude, :longitude, :ada_accessible, :ownership, :more_info_url,
                   :matched_waterbody_name, :matched_county)""",
        rows,
    )
    counts = {"boat_ramp": 0, "boat_carry_in": 0, "shore_fishing": 0}
    for r in rows:
        counts[r["source_type"]] = counts.get(r["source_type"], 0) + 1
    conn.execute("DELETE FROM access_points_meta")
    conn.execute(
        """INSERT INTO access_points_meta
           (id, fetched_at, total_boat_ramp, total_boat_carry_in, total_shore_fishing, source_url)
           VALUES (1, ?, ?, ?, ?, ?)""",
        (fetched_at, counts["boat_ramp"], counts["boat_carry_in"], counts["shore_fishing"], source_url),
    )
    conn.commit()


def run(limit=None, db_path=None) -> dict:
    db_path = db_path or DB_PATH
    conn = sqlite3.connect(db_path)
    init_db(conn)
    index = build_waterbody_index(conn)

    boat_features = fetch_layer(BOAT_ACCESS_LAYER)
    shore_features = fetch_layer(SHORE_FISHING_LAYER)
    if limit:
        boat_features = boat_features[:limit]
        shore_features = shore_features[:limit]

    rows = normalize_boat_access(boat_features) + normalize_shore_fishing(shore_features)
    for row in rows:
        matched_name, matched_county = link_to_waterbody(row, index)
        row["matched_waterbody_name"] = matched_name
        row["matched_county"] = matched_county

    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_access_points(conn, rows, fetched_at, MAPSERVER_BASE)
    conn.close()

    matched = sum(1 for r in rows if r["matched_waterbody_name"])
    print(
        f"Fetched {len(boat_features)} boat access + {len(shore_features)} shore fishing "
        f"features -> {len(rows)} stored ({matched} linked to an existing V1 waterbody)."
    )
    return {"total": len(rows), "matched": matched}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap features fetched per layer (smoke test)")
    args = parser.parse_args()
    run(limit=args.limit)
