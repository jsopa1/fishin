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
# The layer carries both combined and split columns for several species
# (WALLEYE alongside WALLEYE_SAUGER_AND_HYBRIDS, LARGEMOUTH_BASS alongside
# LARGEMOUTH_BASS_AND_SMALLMOUTH_BASS), and different waters populate
# different ones. Listing only the combined columns silently dropped real
# rules on any water that used the split form, so every rule-bearing
# column is read and only the populated ones are shown.
SPECIES_FIELDS = [
    ("ALL_SPECIES", "All species"),
    ("WALLEYE_SAUGER_AND_HYBRIDS", "Walleye, Sauger & hybrids"),
    ("WALLEYE", "Walleye"),
    ("SAUGER_AND_HYBRIDS", "Sauger & hybrids"),
    ("LARGEMOUTH_BASS_AND_SMALLMOUTH_BASS", "Largemouth & Smallmouth Bass"),
    ("LARGEMOUTH_BASS", "Largemouth Bass"),
    ("SMALLMOUTH_BASS", "Smallmouth Bass"),
    ("NORTHERN_PIKE", "Northern Pike"),
    ("MUSKELLUNGE_AND_HYBRIDS", "Muskellunge & hybrids"),
    ("PANFISH", "Panfish"),
    ("BLUEGILL", "Bluegill"),
    ("CRAPPIES", "Crappies"),
    ("TROUT_AND_SALMON", "Trout & Salmon"),
    ("LAKE_STURGEON", "Lake Sturgeon"),
    ("SHOVELNOSE_STURGEON", "Shovelnose Sturgeon"),
    ("CATFISH", "Catfish"),
    ("CHANNEL_CATFISH", "Channel Catfish"),
    ("FLATHEAD_CATFISH", "Flathead Catfish"),
    ("ROCK_YELLOW_AND_WHITE_BASS", "Rock, Yellow & White Bass"),
    ("HYBRID_STRIPED_YELLOW_AND_WHITE_BASS", "Hybrid Striped, Yellow & White Bass"),
    ("CISCO_AND_WHITEFISH", "Cisco & Whitefish"),
    ("BULLHEADS", "Bullheads"),
    ("BOWFIN", "Bowfin"),
    ("PADDLEFISH", "Paddlefish"),
    ("ROUGH_FISH", "Rough fish"),
    ("URBAN_WATERS_GAMEFISH", "Urban waters gamefish"),
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


# ---------------------------------------------------------------------------
# Fish consumption advisories -- the same agency, the same spatial approach,
# and the other half of "is it legal and safe to keep this fish".
#
# 154 Wisconsin waters carry a site-specific advisory; everywhere else the
# statewide advisory applies. WDNR publishes two audiences separately, and
# that distinction is the whole point of the data: the limits for women of
# childbearing age and children under 15 are stricter than for everyone
# else, so collapsing them into one list would be actively harmful.
# ---------------------------------------------------------------------------

ADVISORY_SERVICE_URL = (
    "https://dnrmaps.wi.gov/arcgis2/rest/services/FM_WFF/"
    "FM_FISH_CONSUMPTION_ADVISORIES_WTM_EXT/MapServer/0/query"
)
ADVISORY_PUBLIC_URL = "https://dnr.wisconsin.gov/topic/fishing/consumption"

ADVISORY_GROUPS = {
    "O": "Most people",
    "S": "Women of childbearing age and children under 15",
}
ADVISORY_LEVELS = [
    ("unrestricted", "Unrestricted"),
    ("one_meal_per_week", "One meal per week"),
    ("one_meal_per_month", "One meal per month"),
    ("six_meals_per_year", "Six meals per year"),
    ("do_not_eat", "Do not eat"),
]


def get_consumption_advisory(conn: sqlite3.Connection, lat: float, lon: float) -> dict | None:
    """Site-specific fish consumption advice covering this coordinate.

    Returns status "site_specific" with the advice, or "statewide" when no
    site-specific advisory applies -- which is the common case and is not
    the same as "no advice exists", since Wisconsin's statewide advisory
    still applies to every water.
    """
    if lat is None or lon is None:
        return None

    ensure_cache_table(conn)
    key = "advisory:" + _cache_key(lat, lon)
    now = datetime.datetime.now(datetime.timezone.utc)

    row = conn.execute(
        "SELECT fetched_at, payload FROM regulation_cache WHERE cache_key = ?", (key,)
    ).fetchone()
    if row:
        fetched_at = datetime.datetime.fromisoformat(row[0])
        if (now - fetched_at) < datetime.timedelta(hours=CACHE_TTL_HOURS):
            cached = json.loads(row[1])
            cached["fetched_at"] = fetched_at
            cached["source_url"] = ADVISORY_PUBLIC_URL
            return cached

    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": SEARCH_BUFFER_M,
        "units": "esriSRUnit_Meter",
        "outFields": "WATERBODY_NAME,CONSUMPTION_JSON",
        "returnGeometry": "false",
        "f": "json",
    }
    try:
        request = urllib.request.Request(
            ADVISORY_SERVICE_URL + "?" + urllib.parse.urlencode(params),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            features = json.loads(response.read().decode("utf-8")).get("features", [])
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    shaped = {"status": "statewide", "waters": []}
    for feature in features:
        attributes = feature.get("attributes", {})
        try:
            entries = json.loads(attributes.get("CONSUMPTION_JSON") or "[]")
        except json.JSONDecodeError:
            continue

        groups = []
        for entry in entries:
            advice = [
                {"level": label, "species": str(entry[field]).strip()}
                for field, label in ADVISORY_LEVELS
                if entry.get(field)
            ]
            if advice:
                groups.append({
                    "audience": ADVISORY_GROUPS.get(entry.get("group_type"), "See WDNR"),
                    "advice": advice,
                })
        if groups:
            shaped["waters"].append({
                "waterbody_name": attributes.get("WATERBODY_NAME"),
                "groups": groups,
            })

    if shaped["waters"]:
        shaped["status"] = "site_specific"

    conn.execute(
        "INSERT OR REPLACE INTO regulation_cache (cache_key, fetched_at, payload) VALUES (?, ?, ?)",
        (key, now.isoformat(), json.dumps(shaped)),
    )
    conn.commit()

    shaped["fetched_at"] = now
    shaped["source_url"] = ADVISORY_PUBLIC_URL
    return shaped
