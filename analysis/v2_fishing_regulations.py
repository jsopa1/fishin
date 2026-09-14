#!/usr/bin/env python3
"""
Live fishing regulations for a specific point, from WDNR's own service.

Regulations are the most-wanted thing this app lacked and the one place
the DNR's Fishing Finder genuinely beat it on substance. They are also
the most dangerous thing to get wrong: bag and length limits are legally
binding, and showing a neighbouring lake's rules could cost someone a
citation.

Two design choices follow from that.

**Queried live and spatially, never matched by name.** Wisconsin has
eleven distinct waters called "Devils Lake" in this layer, with different
walleye rules. Name matching would silently pick one. A point-in-polygon
query against the real coordinate returns the regulation area that
actually contains the spot. If it returns more than one water, this
module refuses to choose -- it reports the ambiguity instead.

**WDNR's own words, never a paraphrase.** The text is passed through
verbatim with the time it was retrieved, so what a user reads is what
the agency published. This module composes no limits of its own.

A 100m buffer is used because access points sit on the shoreline, just
outside the water polygon -- verified: a real Devils Lake ramp returns
nothing at 0m and the correct single water (WBIC 980900) at 100m.

Source layer:
  https://dnrmaps.wi.gov/arcgis2/rest/services/FM_WFF/FM_WFF_LAKE_REGULATIONS_WTM_EXT/MapServer/2
"""

import datetime
import json
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

SERVICE_URL = (
    "https://dnrmaps.wi.gov/arcgis2/rest/services/FM_WFF/"
    "FM_WFF_LAKE_REGULATIONS_WTM_EXT/MapServer/2/query"
)
PUBLIC_LOOKUP_URL = "https://apps.dnr.wi.gov/fisheriesmanagement/Public/LakeRegulation"
USER_AGENT = "fishin/1.0 (non-commercial; Wisconsin fishing conditions)"

# Access points sit on the bank, so a small buffer is required to reach the
# water's regulation polygon. Kept tight: a large buffer starts catching
# neighbouring waters, which is exactly the failure mode to avoid.
SEARCH_BUFFER_M = 100
CACHE_TTL_HOURS = 24

# The per-species columns worth surfacing, in the order an angler reads
# them. Mapped to this app's own species vocabulary where they line up.
SPECIES_FIELDS = [
    ("ALL_SPECIES", "All species"),
    ("WALLEYE_SAUGER_AND_HYBRIDS", "Walleye, Sauger & hybrids"),
    ("LARGEMOUTH_BASS_AND_SMALLMOUTH_BASS", "Largemouth & Smallmouth Bass"),
    ("NORTHERN_PIKE", "Northern Pike"),
    ("MUSKELLUNGE_AND_HYBRIDS", "Muskellunge & hybrids"),
    ("PANFISH", "Panfish"),
    ("BLUEGILL", "Bluegill"),
    ("CRAPPIES", "Crappies"),
    ("TROUT_AND_SALMON", "Trout & Salmon"),
    ("LAKE_STURGEON", "Lake Sturgeon"),
    ("CATFISH", "Catfish"),
    ("CHANNEL_CATFISH", "Channel Catfish"),
    ("ROCK_YELLOW_AND_WHITE_BASS", "Rock, Yellow & White Bass"),
]


def ensure_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS regulation_cache (
               cache_key TEXT PRIMARY KEY,
               fetched_at TEXT NOT NULL,
               payload TEXT NOT NULL
           )"""
    )
    conn.commit()


def _cache_key(lat: float, lon: float) -> str:
    # ~11m of precision: enough that the same spot always hits the same
    # cache row, without collapsing genuinely different access points.
    return f"{lat:.4f},{lon:.4f}"


def _query_service(lat: float, lon: float, timeout: int = 12) -> list:
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": SEARCH_BUFFER_M,
        "units": "esriSRUnit_Meter",
        "outFields": ",".join(["WBIC", "WATERBODY_NAME"] + [f for f, _ in SPECIES_FIELDS]),
        "returnGeometry": "false",
        "f": "json",
    }
    request = urllib.request.Request(
        SERVICE_URL + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("features", [])


def _shape(features: list) -> dict:
    """Turn the raw service response into something a page can render, or
    into an explicit refusal to guess."""
    waters = []
    for feature in features:
        attributes = feature.get("attributes", {})
        rules = []
        for field, label in SPECIES_FIELDS:
            value = attributes.get(field)
            if value and str(value).strip():
                rules.append({"label": label, "text": str(value).strip()})
        if rules:
            waters.append({
                "wbic": attributes.get("WBIC"),
                "waterbody_name": attributes.get("WATERBODY_NAME"),
                "rules": rules,
            })

    if not waters:
        return {"status": "none", "waters": []}
    if len(waters) > 1:
        # Several regulated waters within the buffer. Picking one would be
        # exactly the mistake this module exists to avoid.
        return {"status": "ambiguous", "waters": waters}
    return {"status": "ok", "waters": waters}


def get_regulations(conn: sqlite3.Connection, lat: float, lon: float) -> dict | None:
    """Regulations covering this coordinate, cached for CACHE_TTL_HOURS.

    Returns None only when the lookup itself failed (network, service
    down). A successful lookup that found nothing returns status "none",
    which is a different and honest answer.
    """
    if lat is None or lon is None:
        return None

    ensure_cache_table(conn)
    key = _cache_key(lat, lon)
    now = datetime.datetime.now(datetime.timezone.utc)

    row = conn.execute(
        "SELECT fetched_at, payload FROM regulation_cache WHERE cache_key = ?", (key,)
    ).fetchone()
    if row:
        fetched_at = datetime.datetime.fromisoformat(row[0])
        if (now - fetched_at) < datetime.timedelta(hours=CACHE_TTL_HOURS):
            cached = json.loads(row[1])
            cached["fetched_at"] = fetched_at
            cached["source_url"] = PUBLIC_LOOKUP_URL
            return cached

    try:
        features = _query_service(lat, lon)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        # Fall back to a stale cache entry rather than showing nothing --
        # last week's regulations plus a visible date beats a blank space.
        if row:
            cached = json.loads(row[1])
            cached["fetched_at"] = datetime.datetime.fromisoformat(row[0])
            cached["source_url"] = PUBLIC_LOOKUP_URL
            cached["stale"] = True
            return cached
        return None

    shaped = _shape(features)
    conn.execute(
        "INSERT OR REPLACE INTO regulation_cache (cache_key, fetched_at, payload) VALUES (?, ?, ?)",
        (key, now.isoformat(), json.dumps(shaped)),
    )
    conn.commit()

    shaped["fetched_at"] = now
    shaped["source_url"] = PUBLIC_LOOKUP_URL
    return shaped
