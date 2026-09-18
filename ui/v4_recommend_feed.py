"""The non-personal data behind "Recommended" (V4 Phase 4).

One row per access point saying which documented species are inside their
temperature window there right now, at what evidence tier, and how good the
temperature reading is. It contains nothing about the visitor: no location, no
preferences. The browser (static/recommend.js) does the ranking, so the
visitor's location, saved spots and Profile preferences never leave the device
(DECISIONS #047).

Each row is computed by v1_review_data.get_spot_species_picture, the same
function the spot page uses, so a recommendation card cannot disagree with the
page it links to.

Row keys (short, because there are ~3,300 of them on a phone connection):
  n name, w waterbody, c county, t source_type, lat/lon
  q  temperature quality: "real" | "estimated" | "proxy" | None
  a  species inside their documented window now: [[SPECIES, "c"|"l"], ...]
     ("c" = confirmed by survey/sighting, "l" = likely)
  s  species inside a documented *spawning* range only: [SPECIES, ...]
     (shown on a card, never used to rank - many Wisconsin seasons are closed)
  i  species with a documented window they are outside of:
     [[SPECIES, "c"|"l", distance_f], ...]  (used only when nothing is in range)
"""

import gzip
import hashlib
import json
import threading

import v1_review_data as data

_QUALITY = {
    "matched_waterbody_real": "real",
    "interpolated_nearby": "estimated",
    "matched_waterbody_proxy": "proxy",
}
_TIER = {"confirmed": "c", "likely": "l"}

_lock = threading.Lock()
_cache: dict = {}


def build_row(conn, point: dict) -> dict:
    lat, lon = point["latitude"], point["longitude"]
    picture = data.get_spot_species_picture(conn, point, lat, lon)
    temperature = picture["temperature"]
    activity = picture["species_activity"]

    in_window, spawn_only, outside = [], [], []
    for row in activity["active"]:
        act = row.get("activity")
        if act and act["inside_window"]:
            in_window.append([row["species"], _TIER[row["evidence_tier"]]])
        else:
            spawn_only.append(row["species"])
    for row in activity["inactive"]:
        outside.append([row["species"], _TIER[row["evidence_tier"]], row["activity"]["distance_f"]])

    return {
        "n": point["facility_name"],
        "w": point["waterbody_name"],
        "c": point["county"],
        "t": point["source_type"],
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "q": _QUALITY.get(temperature.get("resolution")) if temperature else None,
        "a": in_window,
        "s": spawn_only,
        "i": outside,
    }


def build_feed(conn) -> dict:
    points = conn.execute(
        "SELECT * FROM access_points ORDER BY waterbody_name, facility_name, latitude, longitude"
    ).fetchall()
    rows = [build_row(conn, dict(p)) for p in points]
    refresh = data.get_latest_temperature_refresh(conn)
    return {
        "spots": rows,
        "temperature_observed_at": (refresh or {}).get("refreshed_at") if isinstance(refresh, dict) else None,
    }


def get_feed(conn) -> dict:
    """The feed, rebuilt only when the database file changes (a data refresh),
    and built once even under concurrent first requests."""
    key = data._db_fingerprint(conn)
    if key is not None:
        cached = _cache.get(key)
        if cached is not None:
            return cached
    with _lock:
        if key is not None and key in _cache:
            return _cache[key]
        feed = build_feed(conn)
        if key is not None:
            _cache.clear()
            _cache[key] = feed
        return feed


def get_payload(conn) -> dict:
    """The feed serialised once per database version: compact JSON, its gzip
    (~85% smaller, which matters on cellular), and an ETag so a returning
    visitor re-downloads nothing until the data actually changes."""
    key = data._db_fingerprint(conn)
    if key is not None and key in _payload_cache:
        return _payload_cache[key]
    feed = get_feed(conn)
    raw = json.dumps(feed, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload = {
        "json": raw,
        "gzip": gzip.compress(raw, compresslevel=6),
        "etag": '"' + hashlib.sha256(raw).hexdigest()[:16] + '"',
        "spot_count": len(feed["spots"]),
    }
    if key is not None:
        _payload_cache.clear()
        _payload_cache[key] = payload
    return payload


_payload_cache: dict = {}
