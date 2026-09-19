#!/usr/bin/env python3
"""
Fast, targeted refresh of the REAL water-temperature readings only.

The full batch (v1_full_run.py) recomputes all 2,296 waterbodies and takes
hours, mostly because it live-geocodes every waterbody to find an NWS
station for the air-temperature proxy. That is the wrong unit of work for
keeping temperatures current, and it is why the site has shipped data
tens of hours old.

This script refreshes only the waterbodies backed by a real sensor -- the
65 rows with temp_is_real = 1 (USGS gauges, NDBC buoys, recent CLMN
readings). Those rows matter out of all proportion to their number:

  * they are the readings shown as "real measurement", and
  * they are the entire anchor pool for spot-level interpolation, which
    now covers 79% of access points.

No geocoding, no NWS lookups, no species-presence re-derivation from CSV.
Just the sensor calls, then the local recomputation that depends on them
(narrative text and species threshold matches), so a refreshed row never
disagrees with its own narrative.

Usage:
    python analysis/refresh_temperatures.py           # refresh everything real
    python analysis/refresh_temperatures.py --dry-run # show what would change
    python analysis/refresh_temperatures.py --limit 5 # try a handful first
"""

import argparse
import datetime
import sqlite3
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "ui"))
import v1_conditions_biology_forecast as v1  # noqa: E402
import v4_spot_air_proxy as spot_air_proxy  # noqa: E402

DB_PATH = Path(__file__).parent.parent / "data" / "v1" / "v1_full_run_results.db"
THROTTLE_SECONDS = 0.4  # courtesy pause between live sensor calls


def ensure_refresh_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS temperature_refreshes (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               started_at TEXT NOT NULL,
               finished_at TEXT,
               waterbodies_checked INTEGER NOT NULL DEFAULT 0,
               waterbodies_updated INTEGER NOT NULL DEFAULT 0,
               failures INTEGER NOT NULL DEFAULT 0
           )"""
    )
    conn.commit()


def real_source_waterbodies(conn: sqlite3.Connection, limit: int | None = None) -> list:
    """Rows backed by an actual sensor. Ordered so buoy and gauge readings
    (which drive interpolation statewide) refresh before anything else."""
    query = """
        SELECT waterbody_name, county, run_timestamp, temp_value_c, temp_method
        FROM waterbody_results
        WHERE temp_is_real = 1
        ORDER BY CASE temp_method
                   WHEN 'ndbc_buoy_live' THEN 0
                   WHEN 'usgs_live' THEN 1
                   ELSE 2
                 END, waterbody_name
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    return [dict(r) for r in conn.execute(query)]


def rewrite_waterbody(conn, row, temp_info, presence, thresholds) -> None:
    """Replace one waterbody's temperature, narrative and species matches
    together, so the stored record stays internally consistent."""
    name, county = row["waterbody_name"], row["county"]
    narrative = v1.build_narrative(name, temp_info, presence, thresholds)

    conn.execute(
        """UPDATE waterbody_results
           SET temp_value_c=?, temp_is_real=?, temp_method=?, temp_source=?,
               temp_observed_at=?, narrative_text=?
           WHERE waterbody_name=? AND county=?""",
        (
            temp_info.get("value_c"),
            int(bool(temp_info.get("is_real_water_measurement"))),
            temp_info.get("method"),
            temp_info.get("source"),
            temp_info.get("observed_at"),
            narrative,
            name,
            county,
        ),
    )

    conn.execute(
        "DELETE FROM species_predictions WHERE waterbody_name=? AND county=?", (name, county)
    )
    for species in presence["species"]:
        evaluation = v1.evaluate_species_at_waterbody(
            species, temp_info.get("value_c"), presence["waterbody_type"], thresholds
        )
        if not evaluation["has_threshold_data"]:
            continue
        if evaluation["matches"]:
            for description, evidence, river_caveat in evaluation["matches"]:
                conn.execute(
                    """INSERT INTO species_predictions
                       (run_timestamp, waterbody_name, county, species, has_threshold_data,
                        any_match, match_description, evidence_quality, river_caveat_applied, diel_active)
                       VALUES (?, ?, ?, ?, 1, 1, ?, ?, ?, ?)""",
                    (row["run_timestamp"], name, county, species, description, evidence,
                     int(river_caveat), int(evaluation["diel_active"])),
                )
        else:
            explanation = " | ".join(evaluation["non_matches"]) if evaluation["non_matches"] else None
            conn.execute(
                """INSERT INTO species_predictions
                   (run_timestamp, waterbody_name, county, species, has_threshold_data,
                    any_match, match_description, evidence_quality, river_caveat_applied,
                    diel_active, non_match_explanation)
                   VALUES (?, ?, ?, ?, 1, 0, NULL, NULL, 0, ?, ?)""",
                (row["run_timestamp"], name, county, species,
                 int(evaluation["diel_active"]), explanation),
            )


def refresh(dry_run: bool = False, limit: int | None = None) -> int:
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ensure_refresh_table(conn)

    targets = real_source_waterbodies(conn, limit)
    thresholds = v1.load_thresholds()
    checked = updated = failures = 0

    print(f"Refreshing {len(targets)} sensor-backed waterbodies...", file=sys.stderr)

    for row in targets:
        name, county = row["waterbody_name"], row["county"]
        checked += 1
        try:
            temp_info = v1.get_current_temperature(name, county, live_refresh=True)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  ! {name} ({county}): {type(e).__name__} -- keeping previous value", file=sys.stderr)
            failures += 1
            continue
        except Exception as e:  # noqa: BLE001 -- one waterbody must never halt the refresh
            print(f"  ! {name} ({county}): {type(e).__name__}: {e}", file=sys.stderr)
            failures += 1
            continue
        finally:
            time.sleep(THROTTLE_SECONDS)

        new_value = temp_info.get("value_c")
        # A refresh must never downgrade a real reading into a proxy: if the
        # sensor is momentarily unavailable, the previous real value is more
        # useful than an air-temperature stand-in, and get_current_temperature
        # will happily fall through to one.
        if not temp_info.get("is_real_water_measurement"):
            print(f"  - {name} ({county}): sensor returned nothing, keeping previous reading", file=sys.stderr)
            continue
        if not v1.is_plausible_water_temp_c(new_value):
            print(f"  ! {name} ({county}): implausible value {new_value}, skipped", file=sys.stderr)
            failures += 1
            continue

        old = row["temp_value_c"]
        delta = f"{old:.1f} -> {new_value:.1f}C" if old is not None else f"-> {new_value:.1f}C"
        if dry_run:
            print(f"  would update {name} ({county}): {delta}", file=sys.stderr)
            updated += 1
            continue

        try:
            presence = v1.get_species_presence(name, county)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name} ({county}): presence lookup failed ({type(e).__name__})", file=sys.stderr)
            failures += 1
            continue

        rewrite_waterbody(conn, row, temp_info, presence, thresholds)
        updated += 1
        print(f"  + {name} ({county}): {delta}", file=sys.stderr)

    # Spots with no water reading of any kind get a current air-temperature proxy
    # (ui/v4_spot_air_proxy.py). Best effort: a failure here must never fail or
    # delay the sensor refresh above, and old proxy rows age out on their own.
    if not dry_run and limit is None:
        try:
            proxy = spot_air_proxy.refresh(conn)
            print(f"Spot air proxy: {proxy['updated']}/{proxy['cells']} cells refreshed, {proxy['failed']} failed", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"Spot air proxy skipped: {type(e).__name__}: {e}", file=sys.stderr)

    finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not dry_run:
        conn.execute(
            """INSERT INTO temperature_refreshes
               (started_at, finished_at, waterbodies_checked, waterbodies_updated, failures)
               VALUES (?, ?, ?, ?, ?)""",
            (started_at, finished_at, checked, updated, failures),
        )
        conn.commit()

    conn.close()
    print(
        f"\nChecked {checked} | updated {updated} | failures {failures}"
        + (" (dry run, nothing written)" if dry_run else ""),
        file=sys.stderr,
    )
    return 0 if failures < checked else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    parser.add_argument("--limit", type=int, default=None, help="only refresh the first N waterbodies")
    args = parser.parse_args()
    return refresh(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
