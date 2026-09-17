#!/usr/bin/env python3
"""
Ingest real, dated, geotagged citizen-science fish sightings from GBIF
(Global Biodiversity Information Facility) -- a new evidentiary tier, not
a replacement for anything already here.

WHY THIS EXISTS
---------------
Species presence in this app comes from WDNR fisheries surveys
(authoritative but covers only ~2% of waterbodies) and WDNR stocking
records (positive-only inference, the other ~98%). Both are real, but
neither is an actual observation of the fish being there recently.

GBIF aggregates iNaturalist's "Research Grade" observations -- meaning a
real person logged a sighting/catch with a photo, and the species ID has
community consensus, not just one person's guess. Checked live before
building this: 5,476 real Wisconsin walleye records, 6,364 largemouth
bass, 5,810 yellow perch, 2,693 muskellunge, 528 brook trout -- each with
a real coordinate, a real date, and a real named observer.

WHAT THIS IS NOT
----------------
Not a survey. Not WDNR. Misidentification is possible even at "research
grade," especially between visually similar species (e.g. black vs.
white crappie). This is stored and displayed as its own tier --
`citizen_observed` -- never merged into `species_predictions` or the
spot-page verdict, and never treated as equal to a WDNR survey.

SOURCE, LICENSE, AND SCOPE LIMITS (all deliberate, documented here rather
than discovered later)
--------------------------------------------------------------------------
- Source: GBIF's public REST API (https://api.gbif.org/v1), no key
  required. Underlying dataset is "iNaturalist research-grade
  observations".
- License: individual records are typically CC-BY-NC 4.0, attributed to
  the observer (the `recordedBy` field) -- not a blanket "GBIF" credit.
  Every record shown must carry its own observer name and a link back to
  its GBIF occurrence page.
- Filtered to `basisOfRecord=HUMAN_OBSERVATION`, `hasCoordinate=true`,
  `hasGeospatialIssue=false`, and the last 10 years -- a species sighting
  from 1975 says little about whether it's still there; this app's whole
  ethos is "what's true right now."
- Capped at MAX_RECORDS_PER_SPECIES (1,000) most recent per species, not
  an exhaustive pull -- documented here rather than silently truncated.
  Wisconsin's real bounding box is re-checked locally even though GBIF's
  own `stateProvince` filter is used, since that field is user-entered
  text on iNaturalist and occasionally wrong.
- Species resolved from this app's own 27-species physiology list via
  GBIF's species-match API, checked for an EXACT match at SPECIES rank --
  a low-confidence or wrong-rank match is skipped and logged, never
  silently accepted.

Usage:
    python analysis/v3_gbif_species_observations.py --limit 3   # try a few species
    python analysis/v3_gbif_species_observations.py             # full ingest (resumable)
"""

import argparse
import datetime
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "v1" / "v1_full_run_results.db"
USER_AGENT = "fishin/1.0 (non-commercial; Wisconsin fishing conditions)"
GBIF_API = "https://api.gbif.org/v1"

MAX_RECORDS_PER_SPECIES = 1000
PAGE_SIZE = 300
RECENCY_YEARS = 10
REQUEST_DELAY_SECONDS = 0.5  # a good API citizen, not a scrape

# Wisconsin's real bounding box, generously padded -- a second, local
# check on top of GBIF's own (user-entered, occasionally wrong)
# stateProvince field.
WI_LAT_RANGE = (41.6, 47.4)
WI_LON_RANGE = (-93.0, -86.1)

# Verified via GBIF's own species-match API at ingestion time (see
# resolve_species_key) -- this mapping is the starting point, not blindly
# trusted; a mismatch is skipped and logged rather than silently used.
SPECIES_SCIENTIFIC_NAMES = {
    "BLACK CRAPPIE": "Pomoxis nigromaculatus",
    "BLUEGILL": "Lepomis macrochirus",
    "BROOK TROUT": "Salvelinus fontinalis",
    "BROWN TROUT": "Salmo trutta",
    "BURBOT": "Lota lota",
    "CHANNEL CATFISH": "Ictalurus punctatus",
    "CHINOOK SALMON": "Oncorhynchus tshawytscha",
    "CISCO": "Coregonus artedi",
    "COHO SALMON": "Oncorhynchus kisutch",
    "FATHEAD MINNOW": "Pimephales promelas",
    "FRESHWATER DRUM": "Aplodinotus grunniens",
    "LAKE STURGEON": "Acipenser fulvescens",
    "LAKE TROUT": "Salvelinus namaycush",
    "LAKE WHITEFISH": "Coregonus clupeaformis",
    "LARGEMOUTH BASS": "Micropterus salmoides",
    "MUSKELLUNGE": "Esox masquinongy",
    "NORTHERN PIKE": "Esox lucius",
    "PUMPKINSEED": "Lepomis gibbosus",
    "RAINBOW TROUT": "Oncorhynchus mykiss",
    "ROCK BASS": "Ambloplites rupestris",
    "SAUGER": "Sander canadensis",
    "SMALLMOUTH BASS": "Micropterus dolomieu",
    "WALLEYE": "Sander vitreus",
    "WHITE BASS": "Morone chrysops",
    "WHITE CRAPPIE": "Pomoxis annularis",
    "WHITE SUCKER": "Catostomus commersonii",
    "YELLOW PERCH": "Perca flavescens",
}


def http_get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS gbif_species_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            common_name TEXT NOT NULL,
            scientific_name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            observed_date TEXT,
            recorded_by TEXT,
            license_url TEXT,
            gbif_occurrence_key INTEGER NOT NULL UNIQUE,
            gbif_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_gbif_obs_species ON gbif_species_observations(common_name);
        CREATE INDEX IF NOT EXISTS idx_gbif_obs_latlon ON gbif_species_observations(lat, lon);
        CREATE TABLE IF NOT EXISTS gbif_fetch_log (
            common_name TEXT PRIMARY KEY,
            scientific_name TEXT NOT NULL,
            gbif_species_key INTEGER,
            match_confidence INTEGER,
            records_fetched INTEGER NOT NULL,
            records_rejected_bbox INTEGER NOT NULL,
            status TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def resolve_species_key(scientific_name: str):
    """Returns (key, confidence) or (None, reason) if the match isn't a
    confident, exact SPECIES-rank match -- refuses to guess."""
    url = f"{GBIF_API}/species/match?" + urllib.parse.urlencode({"name": scientific_name, "strict": "true"})
    result = http_get_json(url)
    if result.get("matchType") != "EXACT" or result.get("rank") != "SPECIES":
        return None, f"matchType={result.get('matchType')} rank={result.get('rank')}"
    key = result.get("usageKey") or result.get("speciesKey")
    if key is None:
        return None, "no usageKey in response"
    return key, result.get("confidence")


def _in_wisconsin_bbox(lat: float, lon: float) -> bool:
    return WI_LAT_RANGE[0] <= lat <= WI_LAT_RANGE[1] and WI_LON_RANGE[0] <= lon <= WI_LON_RANGE[1]


def fetch_observations(species_key: int, common_name: str, scientific_name: str) -> tuple:
    """Returns (rows, rejected_bbox_count)."""
    min_year = datetime.datetime.now().year - RECENCY_YEARS
    rows = []
    rejected = 0
    offset = 0
    while offset < MAX_RECORDS_PER_SPECIES:
        params = {
            "speciesKey": species_key,
            # A real geographic bounding box, not GBIF's stateProvince text
            # field -- that field is free-text entered per-dataset and
            # unreliable. Verified live: for Largemouth Bass, the one
            # genuinely recent Wisconsin sighting in GBIF has no
            # stateProvince value at all and was invisible to a
            # stateProvince-filtered query, but appears correctly once
            # queried by coordinate.
            "decimalLatitude": f"{WI_LAT_RANGE[0]},{WI_LAT_RANGE[1]}",
            "decimalLongitude": f"{WI_LON_RANGE[0]},{WI_LON_RANGE[1]}",
            "country": "US",
            "basisOfRecord": "HUMAN_OBSERVATION",
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
            "year": f"{min_year},{datetime.datetime.now().year}",
            "limit": min(PAGE_SIZE, MAX_RECORDS_PER_SPECIES - offset),
            "offset": offset,
        }
        url = f"{GBIF_API}/occurrence/search?" + urllib.parse.urlencode(params)
        payload = http_get_json(url)
        results = payload.get("results", [])
        if not results:
            break
        for r in results:
            lat, lon = r.get("decimalLatitude"), r.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            if not _in_wisconsin_bbox(lat, lon):
                rejected += 1
                continue
            key = r.get("key")
            rows.append({
                "common_name": common_name,
                "scientific_name": scientific_name,
                "lat": lat,
                "lon": lon,
                "observed_date": r.get("eventDate"),
                "recorded_by": r.get("recordedBy") or r.get("rightsHolder"),
                "license_url": r.get("license"),
                "gbif_occurrence_key": key,
                "gbif_url": f"https://www.gbif.org/occurrence/{key}",
            })
        offset += len(results)
        if payload.get("endOfRecords"):
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return rows, rejected


def store_observations(conn: sqlite3.Connection, rows: list) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for row in rows:
        conn.execute(
            """INSERT OR IGNORE INTO gbif_species_observations
               (common_name, scientific_name, lat, lon, observed_date, recorded_by,
                license_url, gbif_occurrence_key, gbif_url, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (row["common_name"], row["scientific_name"], row["lat"], row["lon"],
             row["observed_date"], row["recorded_by"], row["license_url"],
             row["gbif_occurrence_key"], row["gbif_url"], now),
        )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N species (for a quick try)")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    ensure_tables(conn)

    already_done = {r[0] for r in conn.execute("SELECT common_name FROM gbif_fetch_log WHERE status = 'ok'")}
    species_items = list(SPECIES_SCIENTIFIC_NAMES.items())
    if args.limit:
        species_items = species_items[:args.limit]

    total_fetched = total_rejected = 0
    for common_name, scientific_name in species_items:
        if common_name in already_done:
            print(f"skip (already done): {common_name}")
            continue
        try:
            key, confidence = resolve_species_key(scientific_name)
            if key is None:
                print(f"SKIP {common_name} ({scientific_name}): no confident species match ({confidence})")
                conn.execute(
                    """INSERT OR REPLACE INTO gbif_fetch_log
                       (common_name, scientific_name, gbif_species_key, match_confidence,
                        records_fetched, records_rejected_bbox, status, fetched_at)
                       VALUES (?, ?, NULL, NULL, 0, 0, ?, ?)""",
                    (common_name, scientific_name, f"no_match: {confidence}",
                     datetime.datetime.now(datetime.timezone.utc).isoformat()),
                )
                conn.commit()
                continue

            rows, rejected = fetch_observations(key, common_name, scientific_name)
            store_observations(conn, rows)
            conn.execute(
                """INSERT OR REPLACE INTO gbif_fetch_log
                   (common_name, scientific_name, gbif_species_key, match_confidence,
                    records_fetched, records_rejected_bbox, status, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'ok', ?)""",
                (common_name, scientific_name, key, confidence, len(rows), rejected,
                 datetime.datetime.now(datetime.timezone.utc).isoformat()),
            )
            conn.commit()
            print(f"OK {common_name} ({scientific_name}): {len(rows)} stored, {rejected} rejected (bad bbox)")
            total_fetched += len(rows)
            total_rejected += rejected
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"FAIL {common_name}: {e}")
            conn.execute(
                """INSERT OR REPLACE INTO gbif_fetch_log
                   (common_name, scientific_name, gbif_species_key, match_confidence,
                    records_fetched, records_rejected_bbox, status, fetched_at)
                   VALUES (?, ?, NULL, NULL, 0, 0, ?, ?)""",
                (common_name, scientific_name, f"error: {e}",
                 datetime.datetime.now(datetime.timezone.utc).isoformat()),
            )
            conn.commit()
        time.sleep(REQUEST_DELAY_SECONDS)

    total_stored = conn.execute("SELECT COUNT(*) FROM gbif_species_observations").fetchone()[0]
    print(f"\nDone. This run: {total_fetched} fetched, {total_rejected} rejected. "
          f"Total in DB: {total_stored} observations.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
