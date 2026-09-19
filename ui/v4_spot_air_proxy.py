"""Air-temperature proxy for spots that have no water-temperature reading of any kind.

Why this exists. A spot gets a real reading if its waterbody has a sensor, an
estimate if a real reading lies within 60 km (the cut-off is measured, see
DECISIONS #026), and otherwise the waterbody's own air proxy. About 290 access
points (mostly the far north) are matched to no waterbody and sit 60-120 km from
the nearest real reading, so they had nothing. Estimating from a gauge that far
away is worse than useless for windows only a few degrees wide, so instead these
spots get the same thing every other proxy spot gets: the current NWS
air temperature, labelled "air-temperature proxy" everywhere it appears, never
blended with or presented as a water measurement.

Freshness (standing rule: nothing that cannot be refreshed weekly stays). One
NWS reading is stored per quarter-degree cell (about 27 km, ~60 cells cover
every gap spot), refreshed by the same scheduled job as the sensor readings
(analysis/refresh_temperatures.py, every four hours), and ignored at lookup once
it is older than MAX_AGE_HOURS - an old air temperature is dropped, not shown.
"""

import datetime
import sqlite3
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import v1_conditions_biology_forecast as v1  # noqa: E402

PLAUSIBLE_AIR_C = (-60.0, 50.0)  # any real Wisconsin air reading; rejects sentinels and garbage
CELL_DEG = 0.25
MAX_AGE_HOURS = 36.0
THROTTLE_SECONDS = 0.4


def _plausible_air(value) -> bool:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False
    return value == value and PLAUSIBLE_AIR_C[0] <= value <= PLAUSIBLE_AIR_C[1]


def cell_key(lat: float, lon: float) -> str:
    return "{:.2f},{:.2f}".format(round(lat / CELL_DEG) * CELL_DEG, round(lon / CELL_DEG) * CELL_DEG)


def cell_center(key: str) -> tuple:
    lat, lon = key.split(",")
    return float(lat), float(lon)


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS spot_air_proxy (
               cell TEXT PRIMARY KEY,
               temp_c REAL NOT NULL,
               station TEXT,
               observed_at TEXT,
               fetched_at TEXT NOT NULL
           )"""
    )
    conn.commit()


def _parse(ts):
    try:
        parsed = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed


def lookup(conn: sqlite3.Connection, lat: float, lon: float, now: datetime.datetime = None) -> dict | None:
    """The stored proxy for this coordinate's cell, or None if there is none or
    it is older than MAX_AGE_HOURS. Never raises: a missing table just means the
    refresh has not run yet."""
    try:
        row = conn.execute(
            "SELECT temp_c, station, observed_at, fetched_at FROM spot_air_proxy WHERE cell = ?",
            (cell_key(lat, lon),),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None or not _plausible_air(row[0]):
        return None
    now = now or datetime.datetime.now(datetime.timezone.utc)
    observed = _parse(row[2]) or _parse(row[3])
    if observed is None or (now - observed) > datetime.timedelta(hours=MAX_AGE_HOURS):
        return None
    return {"value_c": row[0], "station": row[1], "observed_at": row[2] or row[3]}


def gap_cells(conn: sqlite3.Connection) -> list:
    """Cells that contain at least one spot with no temperature from any other
    source. Uses the same resolver as the spot page with the proxy step
    excluded, so the definition of "gap" cannot drift from what visitors see."""
    import v1_review_data as data

    cells = {}
    for r in conn.execute("SELECT latitude, longitude, matched_waterbody_name, matched_county FROM access_points"):
        if data.get_spot_temperature(conn, r[0], r[1], r[2], r[3], use_spot_proxy=False) is None:
            cells[cell_key(r[0], r[1])] = True
    return sorted(cells)


def refresh(conn: sqlite3.Connection, fetch=None, sleep=time.sleep, limit: int | None = None) -> dict:
    """Fetches one current NWS air temperature per gap cell. `fetch(lat, lon)`
    returns (temp_c, station, observed_at) and is injectable for tests. A cell
    whose fetch fails keeps its previous row, which ages out on its own."""
    fetch = fetch or v1.get_nws_current_air_temp_c
    ensure_table(conn)
    cells = gap_cells(conn)
    if limit:
        cells = cells[:limit]
    ok = failed = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for key in cells:
        lat, lon = cell_center(key)
        try:
            temp_c, station, observed_at = fetch(lat, lon)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, KeyError, OSError, ValueError):
            failed += 1
            sleep(THROTTLE_SECONDS)
            continue
        if not _plausible_air(temp_c):
            failed += 1
            continue
        conn.execute(
            "INSERT OR REPLACE INTO spot_air_proxy (cell, temp_c, station, observed_at, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (key, float(temp_c), station, observed_at, now),
        )
        ok += 1
        sleep(THROTTLE_SECONDS)
    # Cells no longer in any gap (a gauge came online nearby) are dropped.
    if not limit:
        keep = set(cells)
        for (key,) in conn.execute("SELECT cell FROM spot_air_proxy").fetchall():
            if key not in keep:
                conn.execute("DELETE FROM spot_air_proxy WHERE cell = ?", (key,))
    conn.commit()
    return {"cells": len(cells), "updated": ok, "failed": failed}
