#!/usr/bin/env python3
"""
Full run of the existing V1 conditions-and-biology model
(v1_conditions_biology_forecast.py) across the entire documented
waterbody universe, persisted to a queryable SQLite database.

This does NOT change the prediction logic. It imports and calls the exact
same functions the single-waterbody CLI uses (get_species_presence,
get_current_temperature, evaluate_species_at_waterbody, build_narrative)
for every waterbody in the known universe: every survey-confirmed
waterbody, plus every distinct waterbody in the full statewide stocking
pool (lakes and streams together), per docs/v1_data_coverage_report.md.

Rate-limiting note (an honest, disclosed design choice, not a change to
the model): live geocoding for the NWS air-temperature-proxy fallback is
cached PER COUNTY rather than per exact waterbody. This is not a loss of
real precision -- the NWS proxy is already an approximate regional air
temperature standing in for water temperature (Decision #012), not a
waterbody-specific measurement, so a county-level location is an honest
match for what the number actually represents. Without this, a full run
would need 2,000+ individual live geocode calls, which both takes far
longer than useful and is inconsiderate of Nominatim's public 1-request/
second usage policy. The subsequent live NWS current-conditions lookup is
cached the same way (by rounded coordinates, which collapse to one point
per county once geocoding is cached) -- otherwise caching only the
coordinates would do nothing, since the temperature call itself would
still fire once per waterbody. A real per-waterbody USGS or CLMN reading
(when one exists) is never affected by either cache -- only the generic
fallback proxy is.

Usage:
    python analysis/v1_full_run.py                  # full run, live data
    python analysis/v1_full_run.py --limit 25        # smoke test
    python analysis/v1_full_run.py --no-live-refresh # fast, offline-safe dry run
"""

import argparse
import csv
import datetime
import sqlite3
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v1_conditions_biology_forecast as v1  # noqa: E402

DB_PATH = v1.DATA_V1 / "v1_full_run_results.db"

GEOCODE_THROTTLE_SECONDS = 1.1  # respects Nominatim's public 1 req/sec usage policy
USGS_LIVE_CHECK_THROTTLE_SECONDS = 0.3


def build_waterbody_universe() -> list:
    """
    Every distinct waterbody this project has ANY data for: the
    survey-confirmed set (authoritative) plus every distinct waterbody in
    the full statewide stocking pool, deduplicated so a waterbody already
    covered by a real survey isn't also processed under its stocking-only
    name/spelling. Returns [(name, county), ...].

    Dedup key uses v1._norm_county() (strips a trailing "COUNTY" and
    normalizes "AND"/"/" separators), not a plain string match on the raw
    county field. Real bug this fixes: the original 22-lake survey CSV
    writes counties as e.g. "Sauk County", "Oneida County", "Shawano
    County", while the statewide stocking CSV writes the same real
    counties as "Sauk", "Oneida", "Shawano" -- a plain-string dedup key
    treated these as different counties, so waterbodies present in BOTH
    files (Devils Lake, Pelican Lake, Shawano Lake, ...) were processed
    twice under two spellings of the same real place, producing visible
    duplicate entries in the results (e.g. "DEVILS LAKE, Sauk" alongside
    "Devils Lake, Sauk County").
    """
    seen = set()
    universe = []

    for row in v1._read_all_survey_rows():
        key = (v1._norm(row["lake_name"]), v1._norm_county(row["county"]))
        if key in seen:
            continue
        seen.add(key)
        universe.append((row["lake_name"], row["county"]))

    if v1.STOCKING_CSV.exists():
        with open(v1.STOCKING_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["waterbody"].strip()
                if not name:
                    continue
                key = (v1._norm(name), v1._norm_county(row["county"]))
                if key in seen:
                    continue
                seen.add(key)
                universe.append((name, row["county"]))

    return universe


def make_cached_geocoder(original_geocode_live):
    """
    Wraps the ORIGINAL v1.geocode_live (passed in explicitly, not looked
    up dynamically -- looking it up as v1.geocode_live from inside the
    wrapper would resolve to the wrapper itself once installed, causing
    infinite recursion) with a per-county cache, per this module's
    rate-limiting rationale above. Returns (cached_fn, stats_dict) so the
    caller can report cache hit/miss counts honestly in the run report.
    """
    cache = {}
    stats = {"live_geocode_calls": 0, "cache_hits": 0}

    def cached_geocode_live(waterbody_name, county):
        key = (county or "").strip().upper()
        if key in cache:
            stats["cache_hits"] += 1
            return cache[key]
        query_name = f"{county} County" if county else waterbody_name
        result = original_geocode_live(query_name, county)
        stats["live_geocode_calls"] += 1
        time.sleep(GEOCODE_THROTTLE_SECONDS)
        cache[key] = result
        return result

    return cached_geocode_live, stats


def make_cached_nws_lookup(original_get_nws_current_air_temp_c):
    """
    Wraps the ORIGINAL v1.get_nws_current_air_temp_c (passed in
    explicitly, same recursion hazard as make_cached_geocoder above) with
    a coordinate-rounded cache. Necessary companion to the geocode cache:
    caching only the coordinates doesn't help if the temperature lookup
    itself still fires once per waterbody -- since the county geocode
    cache makes every waterbody in a county resolve to the SAME
    coordinates, this cache naturally collapses to one live NWS call per
    county too, for the same disclosed reason (the proxy is a regional
    approximation, not a waterbody-specific reading).
    """
    cache = {}
    stats = {"live_nws_calls": 0, "cache_hits": 0}

    def cached_get_nws_current_air_temp_c(lat, lon):
        key = (round(lat, 2), round(lon, 2))
        if key in cache:
            stats["cache_hits"] += 1
            result = cache[key]
            if isinstance(result, Exception):
                raise result
            return result
        try:
            result = original_get_nws_current_air_temp_c(lat, lon)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as e:
            stats["live_nws_calls"] += 1
            cache[key] = e
            raise
        stats["live_nws_calls"] += 1
        cache[key] = result
        return result

    return cached_get_nws_current_air_temp_c, stats


def init_db(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_timestamp TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            total_waterbodies INTEGER,
            total_species_predictions INTEGER,
            total_failures INTEGER,
            live_refresh INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS waterbody_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            waterbody_name TEXT NOT NULL,
            county TEXT NOT NULL,
            waterbody_type TEXT NOT NULL,
            presence_tier TEXT NOT NULL,
            species_count INTEGER NOT NULL,
            temp_value_c REAL,
            temp_is_real INTEGER NOT NULL,
            temp_method TEXT,
            temp_source TEXT,
            temp_observed_at TEXT,
            narrative_text TEXT NOT NULL,
            FOREIGN KEY (run_timestamp) REFERENCES runs(run_timestamp)
        );

        CREATE TABLE IF NOT EXISTS species_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            waterbody_name TEXT NOT NULL,
            county TEXT NOT NULL,
            species TEXT NOT NULL,
            has_threshold_data INTEGER NOT NULL,
            any_match INTEGER NOT NULL,
            match_description TEXT,
            evidence_quality TEXT,
            river_caveat_applied INTEGER NOT NULL,
            diel_active INTEGER NOT NULL,
            non_match_explanation TEXT,
            FOREIGN KEY (run_timestamp) REFERENCES runs(run_timestamp)
        );

        CREATE TABLE IF NOT EXISTS run_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            waterbody_name TEXT NOT NULL,
            county TEXT NOT NULL,
            species TEXT,
            failure_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            FOREIGN KEY (run_timestamp) REFERENCES runs(run_timestamp)
        );

        CREATE INDEX IF NOT EXISTS idx_waterbody_results_name ON waterbody_results(waterbody_name, county);
        CREATE INDEX IF NOT EXISTS idx_waterbody_results_tier ON waterbody_results(presence_tier);
        CREATE INDEX IF NOT EXISTS idx_species_predictions_species ON species_predictions(species);
        CREATE INDEX IF NOT EXISTS idx_species_predictions_waterbody ON species_predictions(waterbody_name, county);
        """
    )
    # CREATE TABLE IF NOT EXISTS only applies to a genuinely new database --
    # a real DB from before non_match_explanation existed needs an actual
    # migration, not just a schema string that's silently ignored.
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(species_predictions)")}
    if "non_match_explanation" not in existing_columns:
        conn.execute("ALTER TABLE species_predictions ADD COLUMN non_match_explanation TEXT")
    conn.commit()


def run_full_batch(limit: int = None, live_refresh: bool = True, progress_every: int = 100) -> dict:
    """
    Runs the existing model across the full waterbody universe (or the
    first `limit` entries, for a smoke test) and persists every result --
    successes and failures alike -- to DB_PATH. A failure on one waterbody
    or one species never halts the run; it's logged and processing
    continues. Returns a summary dict.
    """
    run_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    started_at = run_timestamp

    universe = build_waterbody_universe()
    if limit:
        universe = universe[:limit]

    original_geocode_live = v1.geocode_live
    original_nws_lookup = v1.get_nws_current_air_temp_c
    geocode_stats = {"live_geocode_calls": 0, "cache_hits": 0}
    nws_stats = {"live_nws_calls": 0, "cache_hits": 0}
    if live_refresh:
        cached_geocode_live, geocode_stats = make_cached_geocoder(original_geocode_live)
        v1.geocode_live = cached_geocode_live
        cached_nws_lookup, nws_stats = make_cached_nws_lookup(original_nws_lookup)
        v1.get_nws_current_air_temp_c = cached_nws_lookup

    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    thresholds = v1.load_thresholds()  # loaded once, reused for every waterbody -- avoids 2,000+ redundant file reads

    total_species_predictions = 0
    total_failures = 0
    usgs_live_checks = 0

    try:
        for i, (name, county) in enumerate(universe):
            if progress_every and i % progress_every == 0:
                print(f"[{i}/{len(universe)}] {name} ({county})", file=sys.stderr)

            try:
                presence = v1.get_species_presence(name, county)
            except v1.AmbiguousLakeError as e:
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'ambiguous_presence_lookup', ?)",
                    (run_timestamp, name, county, str(e)),
                )
                total_failures += 1
                continue
            except Exception as e:  # noqa: BLE001 - a single waterbody's failure must never halt the run
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'presence_lookup_error', ?)",
                    (run_timestamp, name, county, f"{type(e).__name__}: {e}"),
                )
                total_failures += 1
                continue

            try:
                if v1.find_usgs_site_matches(name) and live_refresh:
                    usgs_live_checks += 1
                    time.sleep(USGS_LIVE_CHECK_THROTTLE_SECONDS)
                temp_info = v1.get_current_temperature(name, county, live_refresh=live_refresh)
            except v1.AmbiguousLakeError as e:
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'ambiguous_temperature_lookup', ?)",
                    (run_timestamp, name, county, str(e)),
                )
                total_failures += 1
                temp_info = dict(v1.NO_TEMPERATURE_DATA)
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'temperature_network_error', ?)",
                    (run_timestamp, name, county, f"{type(e).__name__}: {e}"),
                )
                total_failures += 1
                temp_info = dict(v1.NO_TEMPERATURE_DATA)
            except Exception as e:  # noqa: BLE001
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'temperature_lookup_error', ?)",
                    (run_timestamp, name, county, f"{type(e).__name__}: {e}"),
                )
                total_failures += 1
                temp_info = dict(v1.NO_TEMPERATURE_DATA)

            try:
                narrative = v1.build_narrative(name, temp_info, presence, thresholds)
            except Exception as e:  # noqa: BLE001
                conn.execute(
                    "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                    "VALUES (?, ?, ?, NULL, 'narrative_build_error', ?)",
                    (run_timestamp, name, county, f"{type(e).__name__}: {e}"),
                )
                total_failures += 1
                narrative = ""

            conn.execute(
                """INSERT INTO waterbody_results
                   (run_timestamp, waterbody_name, county, waterbody_type, presence_tier, species_count,
                    temp_value_c, temp_is_real, temp_method, temp_source, temp_observed_at, narrative_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_timestamp, name, county, presence["waterbody_type"], presence["tier"],
                    len(presence["species"]), temp_info.get("value_c"),
                    int(bool(temp_info.get("is_real_water_measurement"))),
                    temp_info.get("method"), temp_info.get("source"), temp_info.get("observed_at"),
                    narrative,
                ),
            )

            for species in presence["species"]:
                try:
                    evaluation = v1.evaluate_species_at_waterbody(
                        species, temp_info.get("value_c"), presence["waterbody_type"], thresholds
                    )
                except Exception as e:  # noqa: BLE001
                    conn.execute(
                        "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                        "VALUES (?, ?, ?, ?, 'species_evaluation_error', ?)",
                        (run_timestamp, name, county, species, f"{type(e).__name__}: {e}"),
                    )
                    total_failures += 1
                    continue

                if not evaluation["has_threshold_data"]:
                    conn.execute(
                        "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
                        "VALUES (?, ?, ?, ?, 'no_physiology_threshold', 'Species present but has no entry in physiology_thresholds_v1.json')",
                        (run_timestamp, name, county, species),
                    )
                    total_failures += 1
                    continue

                if evaluation["matches"]:
                    for m, evidence, river_caveat_applied in evaluation["matches"]:
                        conn.execute(
                            """INSERT INTO species_predictions
                               (run_timestamp, waterbody_name, county, species, has_threshold_data, any_match,
                                match_description, evidence_quality, river_caveat_applied, diel_active)
                               VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?, ?)""",
                            (run_timestamp, name, county, species, m, evidence,
                             int(river_caveat_applied), int(evaluation["diel_active"])),
                        )
                        total_species_predictions += 1
                else:
                    # Explains WHY this species isn't a match right now
                    # (see describe_threshold_gap()) instead of leaving
                    # any_match=0 as an unexplained dead end -- None only
                    # when there was no real temperature reading to
                    # compare against in the first place.
                    non_match_explanation = None
                    if evaluation["non_matches"]:
                        non_match_explanation = " | ".join(evaluation["non_matches"])
                    conn.execute(
                        """INSERT INTO species_predictions
                           (run_timestamp, waterbody_name, county, species, has_threshold_data, any_match,
                            match_description, evidence_quality, river_caveat_applied, diel_active,
                            non_match_explanation)
                           VALUES (?, ?, ?, ?, 1, 0, NULL, NULL, 0, ?, ?)""",
                        (run_timestamp, name, county, species, int(evaluation["diel_active"]), non_match_explanation),
                    )
                    total_species_predictions += 1

            if i % 200 == 0:
                conn.commit()

        conn.commit()
    finally:
        v1.geocode_live = original_geocode_live
        v1.get_nws_current_air_temp_c = original_nws_lookup

    finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO runs (run_timestamp, started_at, finished_at, total_waterbodies, "
        "total_species_predictions, total_failures, live_refresh) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_timestamp, started_at, finished_at, len(universe), total_species_predictions,
         total_failures, int(live_refresh)),
    )
    conn.commit()

    # Every read-side query (search_waterbodies, get_waterbody_detail,
    # summary counts, ...) queries waterbody_results/species_predictions/
    # run_failures with no run_timestamp filter -- it has always assumed
    # exactly one run's data lives here. That assumption went unverified
    # for a long time because this script was typically run once per
    # session; running it twice in the same session (as this cycle's
    # Lake Michigan buoy work did) surfaced the real bug directly: a real
    # duplicate-row regression in a live test (`browse?name=Devils+Lake`
    # returned 6 rows instead of 3). Fixed at the source, not by patching
    # every read query -- only this run's own rows survive.
    conn.execute("DELETE FROM waterbody_results WHERE run_timestamp != ?", (run_timestamp,))
    conn.execute("DELETE FROM species_predictions WHERE run_timestamp != ?", (run_timestamp,))
    conn.execute("DELETE FROM run_failures WHERE run_timestamp != ?", (run_timestamp,))
    conn.execute("DELETE FROM runs WHERE run_timestamp != ?", (run_timestamp,))
    conn.commit()
    conn.close()

    return {
        "run_timestamp": run_timestamp,
        "started_at": started_at,
        "finished_at": finished_at,
        "total_waterbodies": len(universe),
        "total_species_predictions": total_species_predictions,
        "total_failures": total_failures,
        "geocode_stats": geocode_stats,
        "nws_stats": nws_stats,
        "usgs_live_checks": usgs_live_checks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N waterbodies (smoke test)")
    parser.add_argument("--no-live-refresh", action="store_true", help="Skip all live network calls")
    parser.add_argument("--progress-every", type=int, default=100, help="Print progress every N waterbodies")
    args = parser.parse_args()

    summary = run_full_batch(
        limit=args.limit, live_refresh=not args.no_live_refresh, progress_every=args.progress_every
    )
    print(f"\nDone. {summary}")


if __name__ == "__main__":
    main()
