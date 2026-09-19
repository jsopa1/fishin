#!/usr/bin/env python3
"""
Live wind and barometric pressure for a specific point, from NWS.

This is deliberately informational only. Peer-reviewed research on
barometric pressure and fish behaviour finds no consistent direct causal
link in freshwater species -- atmospheric pressure swings are physically
trivial to a fish next to the pressure change it already experiences
moving a few feet up or down in the water column. Wind's effect is real
but indirect (wave-driven oxygenation, baitfish pushed onto windward
shorelines, and wind direction correlating with the front bringing it,
which is really a temperature effect). This project's own V0 research
already found weather variables carried no statistically validated
catch-rate signal in Wisconsin creel data.

So this module does exactly what the temperature proxy and regulations
modules do: report a real, live, cited number and nothing more. Wind and
pressure are never scored, never compared to a threshold, and never used
to rank or match a species -- they are shown next to the water
temperature reading as plain trip-planning context, the same way any
other fishing app shows them.

Reuses the same NWS point -> station -> latest-observation lookup as
get_nws_current_air_temp_c() in v1_conditions_biology_forecast.py -- the
single observation response already carries windSpeed, windDirection,
and barometricPressure, so no extra request is needed beyond that walk.
"""

import datetime
import json
import sqlite3
import urllib.error
import urllib.request

USER_AGENT = "fishin/1.0 (non-commercial; Wisconsin fishing conditions)"
CACHE_TTL_HOURS = 1  # wind and pressure move faster than the 24h regulation/advisory cache

COMPASS_16 = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def ensure_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS weather_conditions_cache (
               cache_key TEXT PRIMARY KEY,
               fetched_at TEXT NOT NULL,
               payload TEXT NOT NULL
           )"""
    )
    conn.commit()


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.4f},{lon:.4f}"


def _http_get_json(url: str, timeout: int = 12):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _compass(degrees) -> str:
    if degrees is None:
        return None
    idx = round(float(degrees) / 22.5) % 16
    return COMPASS_16[idx]


# Icon kind for the spot header, from the station's own text description
# ("Mostly Cloudy", "Light Rain", ...). Order matters: the most specific
# hazard wins ("Thunderstorm with rain" is a storm, not rain). Unrecognised
# text gives no icon rather than a guessed one.
_SKY_RULES = (
    ("storm", ("thunder", "t-storm", "tstorm")),
    ("rain", ("rain", "shower", "drizzle")),
    ("snow", ("snow", "sleet", "flurr", "freezing", "ice pellets", "blizzard")),
    ("fog", ("fog", "mist", "haze", "smoke")),
    ("partly", ("partly", "mostly sunny", "mostly clear", "few clouds", "scattered clouds")),
    ("cloud", ("cloud", "overcast")),
    ("sun", ("clear", "sunny", "fair")),
)


def sky_kind(description) -> str | None:
    text = (description or "").lower()
    for kind, needles in _SKY_RULES:
        if any(n in text for n in needles):
            return kind
    return None


def _query_nws(lat: float, lon: float) -> dict:
    points = _http_get_json(f"https://api.weather.gov/points/{lat},{lon}")
    stations = _http_get_json(points["properties"]["observationStations"])
    for feature in stations["features"][:5]:
        try:
            obs = _http_get_json(f"{feature['id']}/observations/latest")
        except (urllib.error.HTTPError, urllib.error.URLError):
            continue
        props = obs.get("properties", {})

        wind_speed_kmh = props.get("windSpeed", {}).get("value")
        wind_dir_deg = props.get("windDirection", {}).get("value")
        pressure_pa = props.get("barometricPressure", {}).get("value")
        air_temp_c = (props.get("temperature") or {}).get("value")
        sky = (props.get("textDescription") or "").strip() or None

        # A station can report a partial observation (e.g. wind sensor
        # down); only accept one that actually has something to show.
        if wind_speed_kmh is None and pressure_pa is None and air_temp_c is None:
            continue

        station_name = feature["id"].rsplit("/", 1)[-1]
        return {
            "status": "ok",
            "wind_speed_mph": round(wind_speed_kmh * 0.621371, 1) if wind_speed_kmh is not None else None,
            "wind_direction_deg": wind_dir_deg,
            "wind_direction_compass": _compass(wind_dir_deg),
            "pressure_inhg": round(pressure_pa / 3386.39, 2) if pressure_pa is not None else None,
            "air_temp_c": round(air_temp_c, 1) if air_temp_c is not None else None,
            "air_temp_f": round(air_temp_c * 9 / 5 + 32) if air_temp_c is not None else None,
            "sky": sky,
            "sky_kind": sky_kind(sky),
            "observed_at": props.get("timestamp"),
            "station": station_name,
        }
    return {"status": "none"}


def get_current_conditions(conn: sqlite3.Connection, lat: float, lon: float) -> dict | None:
    """Current wind and pressure at this coordinate, cached for
    CACHE_TTL_HOURS. Returns None only when the lookup itself failed
    (network, service down) and there is no cache to fall back on.

    Informational only -- see module docstring. Callers must not use
    this to rank, match, or score anything.
    """
    if lat is None or lon is None:
        return None

    ensure_cache_table(conn)
    key = _cache_key(lat, lon)
    now = datetime.datetime.now(datetime.timezone.utc)

    row = conn.execute(
        "SELECT fetched_at, payload FROM weather_conditions_cache WHERE cache_key = ?", (key,)
    ).fetchone()
    if row:
        fetched_at = datetime.datetime.fromisoformat(row[0])
        if (now - fetched_at) < datetime.timedelta(hours=CACHE_TTL_HOURS):
            cached = json.loads(row[1])
            cached["fetched_at"] = fetched_at
            return cached

    try:
        shaped = _query_nws(lat, lon)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError):
        if row:
            cached = json.loads(row[1])
            cached["fetched_at"] = datetime.datetime.fromisoformat(row[0])
            cached["stale"] = True
            return cached
        return None

    conn.execute(
        "INSERT OR REPLACE INTO weather_conditions_cache (cache_key, fetched_at, payload) VALUES (?, ?, ?)",
        (key, now.isoformat(), json.dumps(shaped)),
    )
    conn.commit()

    shaped["fetched_at"] = now
    return shaped
