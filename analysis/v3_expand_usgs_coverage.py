#!/usr/bin/env python3
"""
Re-checks waterbodies currently on the NWS air-temperature proxy against
data/v1/usgs_wi_water_temp_sites.csv, so a newly-added real USGS gauge
actually gets used rather than sitting in the CSV unused until the next
multi-hour full run.

WHY THIS EXISTS
----------------
The full batch (v1_full_run.py) is the only place that normally discovers
a new real-sensor match, because it's the only thing that walks every
waterbody against the site CSV -- and it takes hours. refresh_temperatures.py
(the fast, 4-hourly job) deliberately only re-checks waterbodies ALREADY
flagged temp_is_real=1, so it can't pick up a newly-added site on its own.
This script is the missing middle ground: fast, targeted at exactly the
waterbodies that could plausibly match a new site, no full re-run needed.

Checked before building: comparing USGS's live WI site inventory against
this project's 185-site CSV turned up 8 real, currently-reporting gauges
never added -- Menominee, Peshtigo, Oconto, Wolf, Kewaunee, and Root (x2)
Rivers, and Black Earth Creek. Verified live (Wolf River returned a real
17.5C reading) before adding them to the CSV. This script is what makes
that addition actually count for something instead of sitting unused.

Also covers the same middle-ground gap for Lake Michigan/Lake Superior's
NDBC-buoy path (get_current_temperature's step 1b): Lake Superior was
entirely on the NWS air-temperature proxy across its 4 WI counties until
data/v1/lake_superior_buoy_sites.csv was added this pass, mirroring the
already-shipped Lake Michigan buoy coverage. Verified live: Ashland
County's Lake Superior entry returned a real 16.3C reading from NDBC
buoy 45028 (Western Lake Superior), a few hours old at check time.

Usage:
    python analysis/v3_expand_usgs_coverage.py --dry-run   # show matches, change nothing
    python analysis/v3_expand_usgs_coverage.py             # apply real, plausible matches
"""

import argparse
import sqlite3
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v1_conditions_biology_forecast as v1  # noqa: E402
from refresh_temperatures import ensure_refresh_table, rewrite_waterbody  # noqa: E402

DB_PATH = Path(__file__).parent.parent / "data" / "v1" / "v1_full_run_results.db"
THROTTLE_SECONDS = 0.4


def proxy_waterbodies(conn: sqlite3.Connection) -> list:
    """Every waterbody currently NOT backed by a real sensor, from the
    latest run only."""
    latest = conn.execute("SELECT MAX(run_timestamp) FROM waterbody_results").fetchone()[0]
    rows = conn.execute(
        "SELECT waterbody_name, county, run_timestamp, temp_value_c, temp_method "
        "FROM waterbody_results WHERE temp_is_real = 0 AND run_timestamp = ?",
        (latest,),
    ).fetchall()
    return [dict(r) for r in rows]


def find_candidates(conn: sqlite3.Connection) -> list:
    """Proxy waterbodies whose name matches ANY real USGS site in the
    current CSV, or that are Lake Michigan/Lake Superior (routed to the
    NDBC-buoy path instead) -- not just today's specific additions, so
    this script stays useful the next time either CSV grows rather than
    needing a hardcoded site list re-edited each time."""
    candidates = []
    for row in proxy_waterbodies(conn):
        if v1.find_usgs_site_matches(row["waterbody_name"]):
            candidates.append(row)
        elif v1._norm(row["waterbody_name"]) in v1.GREAT_LAKES_WITH_BUOYS:
            candidates.append(row)
    return candidates


def refresh(dry_run: bool = False) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ensure_refresh_table(conn)

    candidates = find_candidates(conn)
    thresholds = v1.load_thresholds()
    checked = upgraded = 0

    print(f"Checking {len(candidates)} proxy waterbodies with a plausible USGS/buoy match...", file=sys.stderr)

    for row in candidates:
        name, county = row["waterbody_name"], row["county"]
        checked += 1
        try:
            temp_info = v1.get_current_temperature(name, county, live_refresh=True)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  ! {name} ({county}): {type(e).__name__}", file=sys.stderr)
            continue
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name} ({county}): {type(e).__name__}: {e}", file=sys.stderr)
            continue
        finally:
            time.sleep(THROTTLE_SECONDS)

        if not temp_info.get("is_real_water_measurement"):
            continue  # the matched site exists but isn't returning live data right now
        if not v1.is_plausible_water_temp_c(temp_info.get("value_c")):
            print(f"  ! {name} ({county}): implausible value {temp_info.get('value_c')}, skipped", file=sys.stderr)
            continue

        if dry_run:
            print(f"  would upgrade {name} ({county}): proxy -> {temp_info['value_c']:.1f}C real "
                  f"({temp_info.get('source')})", file=sys.stderr)
            upgraded += 1
            continue

        try:
            presence = v1.get_species_presence(name, county)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name} ({county}): presence lookup failed ({type(e).__name__})", file=sys.stderr)
            continue

        rewrite_waterbody(conn, row, temp_info, presence, thresholds)
        upgraded += 1
        print(f"  + {name} ({county}): proxy -> {temp_info['value_c']:.1f}C real ({temp_info.get('source')})",
              file=sys.stderr)

    if not dry_run:
        conn.commit()
    conn.close()
    print(f"\nChecked {checked} | upgraded to real {upgraded}"
          + (" (dry run, nothing written)" if dry_run else ""), file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    args = parser.parse_args()
    return refresh(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
