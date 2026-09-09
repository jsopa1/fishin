#!/usr/bin/env python3
"""
Wisconsin Conditions & Biology Forecast — MVP (Decision #012).

Produces an informational, per-lake narrative from three real, live/current
data sources:
  (a) current water temperature, or a clearly-labeled air-temperature proxy
      when real water temperature isn't available for that lake right now
  (b) established fish physiology thresholds (mvp/physiology_thresholds.json,
      compiled in docs/v0_physiology_research_candidates.md)
  (c) WDNR fish stocking records, to confirm which species are actually
      present in the lake before saying anything about them

This is explicitly NOT a catch-rate prediction (Decision #005, #012). It
never says a fish will bite; it only reports whether current conditions
fall inside a documented physiological window for a species confirmed
present in that lake.

Usage:
    python conditions_forecast.py --lake "Pewaukee Lake" --county Waukesha \
        --lat 43.0189 --lon -88.2359
"""

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

THRESHOLDS_PATH = Path(__file__).parent / "physiology_thresholds.json"

WDNR_STOCKING_BASE = "https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary"
USER_AGENT = "fishin-mvp-conditions-forecast/0.1 (research prototype; contact via project repo)"

# Only used to recognize Lake Michigan and route it to a real buoy instead
# of the generic NWS-air-temperature fallback. Not a claim about any other
# lake's characteristics.
LAKE_MICHIGAN_NAMES = {"lake michigan", "lake michigan (wi waters)"}
LAKE_MICHIGAN_NDBC_STATION = "45007"  # South Michigan buoy, WI nearshore


def http_get_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, data: dict, timeout: int = 20):
    body = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items())
    req = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


import urllib.parse  # noqa: E402  (kept near its only use, above)


# ---------------------------------------------------------------------------
# (c) WDNR stocking records — confirm species actually present in this lake
# ---------------------------------------------------------------------------

def get_wdnr_county_code(county_name: str) -> str:
    """Live query against WDNR's Fish Stocking database county lookup."""
    counties = http_get_json(f"{WDNR_STOCKING_BASE}/GetCounties")
    target = county_name.strip().upper()
    for c in counties:
        if c["Text"].strip().upper() == target:
            return c["Value"]
    raise ValueError(
        f"County '{county_name}' not found in WDNR's stocking database county list. "
        f"Available: {[c['Text'] for c in counties]}"
    )


def get_stocked_species(lake_name: str, county_code: str, since_year: int = None) -> list:
    """
    Live query against WDNR's Fish Stocking database (LoadResults, the same
    DataTables endpoint the public search page uses). Returns the distinct
    species stocked in this lake, most-recent stocking year per species.

    since_year: if given, only counts stocking events in/after this year
    toward "currently present" — stocking 40 years ago with no follow-up
    is weaker evidence of present-day presence than a recent event, and
    this is disclosed in the narrative, not silently assumed.
    """
    payload = {
        "STOCKING_YEAR": "",
        "SPECIES_NAME": "",
        "COUNTY_CODE": county_code,
        "STOCKED_WB_NAME": lake_name.upper(),
        "LOCAL_WB_NAME": "",
        "draw": 1,
        "start": 0,
        "length": 2000,  # WDNR's own page paginates at 100; ask for effectively "all"
    }
    result = http_post_json(f"{WDNR_STOCKING_BASE}/LoadResults", payload)
    rows = result.get("data", [])

    by_species = {}
    for row in rows:
        species = (row.get("SPECIES_NAME") or "").strip().upper()
        year = row.get("STOCKING_YEAR")
        if not species or year is None:
            continue
        if since_year is not None and year < since_year:
            continue
        prev = by_species.get(species)
        if prev is None or year > prev:
            by_species[species] = year

    return sorted(by_species.items(), key=lambda kv: kv[0])


# ---------------------------------------------------------------------------
# (a) Current water temperature — real buoy where possible, labeled proxy
#     otherwise. Never silently substitutes one for the other.
# ---------------------------------------------------------------------------

def get_lake_michigan_buoy_water_temp_c(station: str = LAKE_MICHIGAN_NDBC_STATION):
    """
    Real-time NOAA NDBC buoy reading. Returns (temp_c, observation_time_utc)
    or (None, reason_string) if the buoy has no current data — buoys are
    seasonal and can also just be temporarily offline; this is a real,
    disclosed possibility, not an error to hide.
    """
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return None, f"NDBC buoy {station} feed returned HTTP {e.code} (buoy may be out of season or offline)"

    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if not lines:
        return None, f"NDBC buoy {station} feed returned no data rows (buoy likely offline right now)"

    # realtime2 format: YY MM DD hh mm WDIR WSPD GST WVHT DPD APD MWD PRES ATMP WTMP DEWP VIS PTDY TIDE
    header_line = next((ln for ln in text.splitlines() if ln.startswith("#")), None)
    cols = header_line.lstrip("#").split() if header_line else []
    try:
        wtmp_idx = cols.index("WTMP")
    except ValueError:
        wtmp_idx = 14  # fallback to the documented fixed column position

    fields = lines[0].split()
    if len(fields) <= wtmp_idx:
        return None, f"NDBC buoy {station} row too short to contain WTMP"
    raw = fields[wtmp_idx]
    if raw in ("MM", "99.0", "999.0"):
        return None, f"NDBC buoy {station} is reporting but WTMP is a missing-value sentinel right now"

    try:
        temp_c = float(raw)
    except ValueError:
        return None, f"NDBC buoy {station} WTMP field unparsable ({raw!r})"

    yy, mm, dd, hh, minute = fields[0:5]
    obs_time = f"20{yy}-{mm}-{dd}T{hh}:{minute}Z"
    return temp_c, obs_time


def get_nws_current_air_temp_c(lat: float, lon: float):
    """
    Real-time NWS current-conditions air temperature for the nearest
    observation station to (lat, lon). Used ONLY as a clearly-labeled
    proxy for water temperature when no real water-temperature reading is
    available — never presented as a water-temperature measurement itself.
    Returns (temp_c, station_name, observation_time_utc) or raises.
    """
    points = http_get_json(f"https://api.weather.gov/points/{lat},{lon}")
    stations_url = points["properties"]["observationStations"]
    stations = http_get_json(stations_url)
    station_urls = [f["id"] for f in stations["features"]]
    if not station_urls:
        raise RuntimeError("NWS returned no observation stations for this location")

    last_error = None
    for station_url in station_urls[:5]:
        try:
            obs = http_get_json(f"{station_url}/observations/latest")
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_error = e
            continue
        temp = obs["properties"].get("temperature", {})
        value_c = temp.get("value")
        if value_c is None:
            continue
        station_name = obs["properties"].get("stationId", station_url).rsplit("/", 1)[-1]
        obs_time = obs["properties"].get("timestamp")
        return value_c, station_name, obs_time

    raise RuntimeError(
        f"No NWS station near ({lat}, {lon}) returned a current temperature reading "
        f"(last error: {last_error})"
    )


def get_current_temperature_c(lake_name: str, lat: float, lon: float):
    """
    Returns a dict: {value_c, is_water_measurement, source, observed_at}.
    Tries a real water-temperature buoy first (Lake Michigan only, for
    now); falls back to NWS current air temperature as an explicitly
    labeled proxy everywhere else / if the buoy has no current data.
    """
    if lake_name.strip().lower() in LAKE_MICHIGAN_NAMES:
        temp_c, info = get_lake_michigan_buoy_water_temp_c()
        if temp_c is not None:
            return {
                "value_c": temp_c,
                "is_water_measurement": True,
                "source": f"NOAA NDBC buoy {LAKE_MICHIGAN_NDBC_STATION} (real-time water temperature)",
                "observed_at": info,
            }
        # Buoy has no current data right now — fall through to the proxy,
        # but say exactly why.
        buoy_failure_reason = info
    else:
        buoy_failure_reason = None

    temp_c, station_name, obs_time = get_nws_current_air_temp_c(lat, lon)
    note = "NWS current air temperature, used as a proxy — not a water-temperature measurement"
    if buoy_failure_reason:
        note += f" (buoy unavailable: {buoy_failure_reason})"
    return {
        "value_c": temp_c,
        "is_water_measurement": False,
        "source": f"{note} [station {station_name}]",
        "observed_at": obs_time,
    }


# ---------------------------------------------------------------------------
# (b) Physiology thresholds + narrative generation
# ---------------------------------------------------------------------------

def load_thresholds() -> dict:
    with open(THRESHOLDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def describe_threshold_match(current_c: float, threshold: dict) -> str | None:
    """
    Returns a narrative sentence fragment if current_c falls inside (or, for
    single-point preferences, reasonably near) the threshold's range, else
    None. "Reasonably near" for a point value is +/- 1.5C, disclosed in the
    sentence itself, not treated as an exact match.
    """
    ttype = threshold["type"]
    kind_label = {
        "activity_window": "documented activity/feeding-temperature window",
        "reduced_feeding_below": "documented reduced-feeding threshold",
        "spawning_trigger": "documented spawning-trigger range",
        "physiological_optimum": "documented physiological growth-optimum range",
        "avoidance_above": "documented warm-water avoidance threshold",
    }.get(ttype, ttype)

    if "range_c" in threshold:
        lo, hi = threshold["range_c"]
        lo_f, hi_f = threshold.get("range_f", (c_to_f(lo), c_to_f(hi)))
        in_range = lo <= current_c <= hi
        if not in_range:
            return None
        peak_note = ""
        if "peak_range_c" in threshold:
            plo, phi = threshold["peak_range_c"]
            plo_f, phi_f = threshold.get("peak_range_f", (c_to_f(plo), c_to_f(phi)))
            if plo <= current_c <= phi:
                peak_note = f" (within the peak sub-range, {plo_f:.0f}-{phi_f:.0f}°F / {plo:.1f}-{phi:.1f}°C)"
        return (
            f"currently within the {kind_label} "
            f"({lo_f:.0f}-{hi_f:.0f}°F / {lo:.1f}-{hi:.1f}°C){peak_note} — {threshold['description']}"
        )

    if "threshold_c" in threshold:
        t_c = threshold["threshold_c"]
        t_f = threshold.get("threshold_f", c_to_f(t_c))
        if ttype == "reduced_feeding_below" and current_c < t_c:
            return f"currently below the {kind_label} ({t_f:.0f}°F / {t_c:.1f}°C) — {threshold['description']}"
        if ttype == "avoidance_above" and current_c > t_c:
            return f"currently above the {kind_label} ({t_f:.0f}°F / {t_c:.1f}°C) — {threshold['description']}"
        return None

    if "preferred_point_c" in threshold:
        p_c = threshold["preferred_point_c"]
        p_f = threshold.get("preferred_point_f", c_to_f(p_c))
        if abs(current_c - p_c) <= 1.5:
            return (
                f"currently close to the field-measured preferred temperature "
                f"({p_f:.1f}°F / {p_c:.1f}°C, within 1.5°C) — {threshold['description']}"
            )
        return None

    return None


def build_narrative(lake_name: str, county: str, temp_info: dict,
                     stocked_species: list, thresholds: dict) -> str:
    lines = []
    lines.append(f"# Conditions & Biology Forecast — {lake_name}, {county} County, WI")
    lines.append(f"_Generated {datetime.datetime.now(datetime.timezone.utc).isoformat()}_")
    lines.append("")
    lines.append(
        "**This is general, science-based seasonal context — not a catch prediction.** "
        "It does not estimate catch rate or the likelihood of catching any fish (Decision #005, #012)."
    )
    lines.append("")

    value_c = temp_info["value_c"]
    value_f = c_to_f(value_c)
    measurement_note = (
        "a real, current water-temperature measurement"
        if temp_info["is_water_measurement"]
        else "an air-temperature PROXY, not a direct water-temperature measurement"
    )
    lines.append(
        f"**Current temperature reading:** {value_f:.1f}°F / {value_c:.1f}°C "
        f"({measurement_note}). Source: {temp_info['source']}. Observed: {temp_info['observed_at']}."
    )
    lines.append("")

    if not stocked_species:
        lines.append(
            "**No WDNR stocking record was found for this lake.** This does not necessarily mean no "
            "fish are present (natural reproduction and unstocked native species are common), but this "
            "tool only reports on species with a confirmed WDNR stocking record, per Decision #012 — "
            "so no species-level narrative is generated below."
        )
        return "\n".join(lines)

    lines.append(
        f"**Species with a confirmed WDNR stocking record for this lake** "
        f"({len(stocked_species)}): " + ", ".join(f"{sp.title()} (last stocked {yr})" for sp, yr in stocked_species)
    )
    lines.append("")
    lines.append("## Species notes")
    lines.append("")

    any_match = False
    for species, last_stocked_year in stocked_species:
        species_thresholds = thresholds["species"].get(species)
        if not species_thresholds:
            continue  # no physiology reference data for this species yet
        matches = []
        for t in species_thresholds:
            m = describe_threshold_match(value_c, t)
            if m:
                matches.append((m, t.get("evidence", "unspecified")))
        if not matches:
            continue
        any_match = True
        lines.append(f"### {species.title()}")
        lines.append(f"_Last stocked: {last_stocked_year}._")
        for m, evidence in matches:
            lines.append(f"- Water temperature is {m}. (Evidence quality: {evidence})")
        lines.append("")

    if not any_match:
        lines.append(
            "No species confirmed present in this lake currently has water temperature inside any "
            "of its documented physiology windows (or reference data isn't available yet for the "
            "species stocked here). No seasonal-context statement is generated for this visit — "
            "this is expected at many times of year, not an error."
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", required=True, help='Lake name, e.g. "Pewaukee Lake"')
    parser.add_argument("--county", required=True, help='WDNR county name, e.g. "Waukesha"')
    parser.add_argument("--lat", required=True, type=float, help="Latitude for nearest weather station lookup")
    parser.add_argument("--lon", required=True, type=float, help="Longitude for nearest weather station lookup")
    parser.add_argument(
        "--since-year", type=int, default=None,
        help="Only count stocking events in/after this year as evidence of present-day presence",
    )
    args = parser.parse_args()

    thresholds = load_thresholds()

    try:
        county_code = get_wdnr_county_code(args.county)
        stocked_species = get_stocked_species(args.lake, county_code, since_year=args.since_year)
    except Exception as e:
        print(f"ERROR fetching WDNR stocking data: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        temp_info = get_current_temperature_c(args.lake, args.lat, args.lon)
    except Exception as e:
        print(f"ERROR fetching current temperature: {e}", file=sys.stderr)
        sys.exit(1)

    narrative = build_narrative(args.lake, args.county, temp_info, stocked_species, thresholds)
    print(narrative)


if __name__ == "__main__":
    main()
