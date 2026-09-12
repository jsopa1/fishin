#!/usr/bin/env python3
"""
V2 environmental-intelligence layer: real, WDNR-verified aquatic invasive
species (AIS) sighting locations, pulled live from WDNR's own ArcGIS REST
service and persisted into the same results database V1/V2 already use.

Source (live, queried at run time):
  https://dnrmaps.wi.gov/arcgis/rest/services/WY_Lakes_AIS/
    WY_INVASIVE_AQUATIC_PLANT_LOCATIONS/MapServer
    WY_INVASIVE_FISH_LOCATIONS/MapServer
    WY_INVASIVE_INVERTEBRATES_LOCATIONS/MapServer

Each species is split across many sub-layers (verified vs. no-longer-
observed, each further split into points/lines/areas). This script pulls
only the "Verified Points" sub-layer for a curated set of the species
most commonly relevant to Wisconsin anglers/boaters -- not every species
WDNR tracks, and not the "no longer observed" or area/line geometries,
to keep this a clean, honestly-scoped point layer rather than an attempt
at a complete AIS atlas.

These sightings are NOT linked to a V1 waterbody record. Two independent
attempts to build a reliable WBIC/name-based join for a related layer
(see docs/v2_access_points_report.md and the follow-up investigation
logged in DECISIONS.md #018) both surfaced real ambiguity -- rather than
force a lower-confidence link, each sighting stands on its own real
location, exactly like an access point that doesn't match a V1
waterbody already does.

Per this project's positive-only-evidence discipline (the same rule
stocking-derived species presence follows): a sighting shown here is
real, verified, positive evidence of past detection. The ABSENCE of a
sighting for a given lake is NOT evidence the species isn't there --
WDNR's monitoring coverage is real but not exhaustive.

Usage:
    python analysis/v2_invasive_species.py                # full live pull
    python analysis/v2_invasive_species.py --limit 10      # smoke test
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

BASE = "https://dnrmaps.wi.gov/arcgis/rest/services/WY_Lakes_AIS"

# Curated, not exhaustive -- see module docstring. (service, layer id,
# common name, scientific name, taxon group).
SPECIES = [
    ("WY_INVASIVE_INVERTEBRATES_LOCATIONS", 132, "Zebra Mussel", "Dreissena polymorpha", "invertebrate"),
    ("WY_INVASIVE_INVERTEBRATES_LOCATIONS", 119, "Spiny Waterflea", "Bythotrephes cederstroemi", "invertebrate"),
    ("WY_INVASIVE_INVERTEBRATES_LOCATIONS", 106, "Rusty Crayfish", "Orconectes rusticus", "invertebrate"),
    ("WY_INVASIVE_AQUATIC_PLANT_LOCATIONS", 28, "Eurasian Water-Milfoil", "Myriophyllum spicatum", "plant"),
    ("WY_INVASIVE_AQUATIC_PLANT_LOCATIONS", 15, "Curly-Leaf Pondweed", "Potamogeton crispus", "plant"),
    ("WY_INVASIVE_FISH_LOCATIONS", 42, "Round Goby", "Neogobius melanostomus", "fish"),
]


def fetch_species_points(service: str, layer_id: int) -> list:
    """Live network call -- not exercised by unit tests (see normalize_*
    below for the tested logic), same pattern as v2_access_points.py."""
    params = {
        "where": "1=1",
        "outFields": "ROI_STATUS_DESC,ROI_START_DATE,ROI_SHORT_NAME,WBIC",
        "outSR": "4326",
        "f": "geojson",
    }
    url = f"{BASE}/{service}/MapServer/{layer_id}/query?{urllib.parse.urlencode(params)}"
    data = v1.http_get_json(url, timeout=30)
    return data.get("features", [])


def normalize_sightings(features: list, common_name: str, scientific_name: str, taxon_group: str) -> list:
    rows = []
    for feat in features:
        p = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom or geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
        detected_date = None
        raw_date = p.get("ROI_START_DATE")
        if raw_date:
            detected_date = datetime.datetime.fromtimestamp(raw_date / 1000, tz=datetime.timezone.utc).date().isoformat()
        rows.append({
            "species_common_name": common_name,
            "species_scientific_name": scientific_name,
            "taxon_group": taxon_group,
            "site_description": (p.get("ROI_SHORT_NAME") or "").strip() or None,
            "status": (p.get("ROI_STATUS_DESC") or "").strip() or None,
            "detected_date": detected_date,
            "wbic": (p.get("WBIC") or "").strip() or None,
            "latitude": lat,
            "longitude": lon,
        })
    return rows


def init_db(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS invasive_species_sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species_common_name TEXT NOT NULL,
            species_scientific_name TEXT NOT NULL,
            taxon_group TEXT NOT NULL,
            site_description TEXT,
            status TEXT,
            detected_date TEXT,
            wbic TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS invasive_species_meta (
            id INTEGER PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            total_sightings INTEGER NOT NULL,
            species_covered INTEGER NOT NULL,
            source_url TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_invasive_species_common_name
            ON invasive_species_sightings(species_common_name);
        """
    )
    conn.commit()


def write_sightings(conn: sqlite3.Connection, rows: list, fetched_at: str, source_url: str, species_covered: int):
    conn.execute("DELETE FROM invasive_species_sightings")
    conn.executemany(
        """INSERT INTO invasive_species_sightings
           (species_common_name, species_scientific_name, taxon_group, site_description,
            status, detected_date, wbic, latitude, longitude)
           VALUES (:species_common_name, :species_scientific_name, :taxon_group, :site_description,
                   :status, :detected_date, :wbic, :latitude, :longitude)""",
        rows,
    )
    conn.execute("DELETE FROM invasive_species_meta")
    conn.execute(
        """INSERT INTO invasive_species_meta (id, fetched_at, total_sightings, species_covered, source_url)
           VALUES (1, ?, ?, ?, ?)""",
        (fetched_at, len(rows), species_covered, BASE),
    )
    conn.commit()


def run(limit=None, db_path=None) -> dict:
    db_path = db_path or DB_PATH
    conn = sqlite3.connect(db_path)
    init_db(conn)

    all_rows = []
    for service, layer_id, common_name, scientific_name, taxon_group in SPECIES:
        features = fetch_species_points(service, layer_id)
        if limit:
            features = features[:limit]
        all_rows.extend(normalize_sightings(features, common_name, scientific_name, taxon_group))

    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_sightings(conn, all_rows, fetched_at, BASE, len(SPECIES))
    conn.close()

    print(f"Fetched {len(all_rows)} verified AIS sightings across {len(SPECIES)} species.")
    return {"total": len(all_rows), "species": len(SPECIES)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap features fetched per species (smoke test)")
    args = parser.parse_args()
    run(limit=args.limit)
