#!/usr/bin/env python3
"""
Wisconsin Conditions & Biology Forecast — V1, expanded to the full
stocking-only tier plus rivers/streams (this cycle's Parts 1-5).

Supersedes mvp/conditions_forecast.py's single-lake demo, and the prior
survey-lakes-only version of this script, with:
  - data/v1/wi_fisheries_survey_species_sample.csv (+ _batch2 if present)
    -- real, survey-confirmed lakes/streams, authoritative when present
  - data/v1/wi_stocking_statewide_2011_2025.csv (24,683 real statewide
    stocking records, 2,338 waterbodies INCLUDING 690 real stream/river
    waterbodies -- POSITIVE evidence only, never used to conclude a
    species is absent) -- now surfaced for EVERY waterbody, not just the
    22 original survey lakes
  - data/v1/usgs_wi_water_temp_sites.csv (185 real USGS WI sites with
    daily-value water-temperature coverage: 177 streams/rivers, 8 lakes)
    -- queried live at runtime for any matching waterbody
  - data/v1/wi_lake_water_temp_current.csv (real current/recent water
    temperature pre-pulled for the original 22 survey lakes + Lake Monona)
  - data/v1/physiology_thresholds_v1.json (26-species physiology reference,
    docs/v1_physiology_research_candidates.md) -- lake-derived thresholds
    are flagged, not silently applied, when used against a stream entry

Still explicitly NOT a catch-rate prediction (Decision #005, #012). Every
output states this plainly. A waterbody with neither survey nor stocking
data, or neither a real nor proxy temperature source, reports "no_data"
explicitly -- it is never silently dropped or given a fabricated value.

Usage:
    python analysis/v1_conditions_biology_forecast.py --lake "Devils Lake"
    python analysis/v1_conditions_biology_forecast.py --lake "Fox River" --county Green Lake
    python analysis/v1_conditions_biology_forecast.py --list-lakes
"""

import argparse
import csv
import datetime
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_V1 = REPO_ROOT / "data" / "v1"
SURVEY_CSV = DATA_V1 / "wi_fisheries_survey_species_sample.csv"
SURVEY_CSV_BATCH2 = DATA_V1 / "wi_fisheries_survey_species_sample_batch2.csv"
STOCKING_CSV = DATA_V1 / "wi_stocking_statewide_2011_2025.csv"
WATER_TEMP_CSV = DATA_V1 / "wi_lake_water_temp_current.csv"
USGS_SITES_CSV = DATA_V1 / "usgs_wi_water_temp_sites.csv"
LAKE_MICHIGAN_BUOY_CSV = DATA_V1 / "lake_michigan_buoy_sites.csv"
THRESHOLDS_JSON = DATA_V1 / "physiology_thresholds_v1.json"

USER_AGENT = "fishin-v1-conditions-forecast/0.1 (research prototype; contact via project repo)"

STOCKING_MIN_YEAR_FOR_PRESENCE = 2011  # matches the statewide pull's own window

# Name-keyword heuristic for classifying a waterbody as a river/stream vs.
# a lake/pond/flowage -- used only to decide whether to flag lake-derived
# physiology thresholds as unverified for this entry (Part 3). FLOWAGE is
# deliberately excluded: it's a dammed, lake-like impoundment, not
# flowing-water stream habitat, despite being river-adjacent by name.
STREAM_KEYWORDS = ("CREEK", "RIVER", "BROOK", "STREAM", "BRANCH")


# ---------------------------------------------------------------------------
# Data loading (local files -- real, pre-pulled per Parts 2-3 of this cycle)
# ---------------------------------------------------------------------------

def load_thresholds() -> dict:
    with open(THRESHOLDS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm(name: str) -> str:
    return " ".join(name.strip().upper().split())


def _norm_county(county: str) -> str:
    c = _norm(county).replace(" COUNTY", "")
    c = c.replace(" AND ", "/")
    c = "/".join(p.strip() for p in c.split("/"))
    return c


def _county_matches(a: str, b: str) -> bool:
    """Loose match: the two county strings across data/v1's source files
    use inconsistent formatting ("Sauk County" vs "Sauk", "Columbia and
    Sauk" vs "Columbia/Sauk") -- treat as a match if either normalized
    string is a substring of the other, or they share any "/"-token."""
    na, nb = _norm_county(a), _norm_county(b)
    if na == nb or na in nb or nb in na:
        return True
    return bool(set(na.split("/")) & set(nb.split("/")))


def _lake_name_matches(target_norm: str, candidate_raw: str) -> bool:
    """Exact match first; falls back to substring match (either direction)
    to handle real naming inconsistencies across source files, e.g.
    "Lauderdale Lakes" vs "Lauderdale Lakes (Green Lake/Middle Lake/Mill
    Lake chain)" -- both refer to the same real survey.

    Guards against a real data issue: 813 stocking rows have a blank
    waterbody field (private-pond stocking with no named public
    waterbody), and an empty string is a substring of everything -- without
    this guard, every such row would spuriously "match" every lake query.
    """
    candidate_norm = _norm(candidate_raw)
    if not candidate_norm or not target_norm:
        return False
    if candidate_norm == target_norm:
        return True
    if len(target_norm) < 4 or len(candidate_norm) < 4:
        return False  # too short for substring matching to be meaningful
    return target_norm in candidate_norm or candidate_norm in target_norm


class AmbiguousLakeError(ValueError):
    pass


def _group_rows_by_distinct_lake(rows: list, name_key: str, county_key: str) -> dict:
    """Groups matching rows by their (lake_name, county) pair as it
    actually appears in the source file, so two different real lakes that
    happen to share a name (e.g. two "Fish Lake"s) are never silently
    merged."""
    groups = {}
    for row in rows:
        key = (row[name_key], row[county_key])
        groups.setdefault(key, []).append(row)
    return groups


def _resolve_distinct_waterbody(
    all_rows: list, name_key: str, county_key: str, query_name: str, query_county: str | None, source_label: str
) -> list | None:
    """
    Shared resolution used by every loader (survey, stocking, water-temp):
    fuzzy-matches query_name against name_key across all_rows, groups by
    the real distinct (name, county) pairs found, and returns the one
    group of rows to use -- or None if nothing matched.

    Real bug this fixes: `_lake_name_matches`'s bidirectional substring
    check means an EXACT query for e.g. "Apple River" also fuzzy-matches
    "Apple River Flowage" (and vice versa) -- without this function, an
    exact, unambiguous query would spuriously raise AmbiguousLakeError
    just because another real waterbody's name happens to contain it as a
    substring. Fix: if any candidate's real name is an EXACT match (after
    normalization) to the query, prefer it and ignore the fuzzy matches --
    only raise ambiguity when the query itself doesn't exactly identify a
    single real waterbody.
    """
    target = _norm(query_name)
    matched = [row for row in all_rows if _lake_name_matches(target, row[name_key])]
    if not matched:
        return None
    groups = _group_rows_by_distinct_lake(matched, name_key, county_key)
    if query_county:
        groups = {k: v for k, v in groups.items() if _county_matches(query_county, k[1])}
    if not groups:
        return None
    exact_groups = {k: v for k, v in groups.items() if _norm(k[0]) == target}
    if exact_groups:
        groups = exact_groups
    if len(groups) > 1:
        options = ", ".join(f"{n} ({c})" for n, c in sorted(groups))
        raise AmbiguousLakeError(
            f"'{query_name}' matches more than one distinct waterbody in the {source_label}: {options}. "
            f"Pass --county to disambiguate."
        )
    return next(iter(groups.values()))


def classify_waterbody_type(name: str) -> str:
    """
    "stream" if the name contains a flowing-water keyword (CREEK, RIVER,
    BROOK, STREAM, BRANCH), else "lake" (covers lakes, ponds, and
    flowages -- a flowage is a dammed, lake-like impoundment, not
    flowing-water stream habitat, despite the river-adjacent name).
    Used only to decide whether to flag lake-derived physiology
    thresholds as unverified for a given entry (Part 3) -- never to
    exclude a waterbody from coverage.
    """
    upper = name.upper()
    if "FLOWAGE" in upper:
        return "lake"  # dammed impoundment, lake-like, even when named "X River Flowage"
    return "stream" if any(kw in upper for kw in STREAM_KEYWORDS) else "lake"


_csv_read_cache: dict = {}  # {(resolved_path, mtime): [row dicts]} -- see _read_csv_cached


def _read_csv_cached(path) -> list:
    """
    Reads a CSV once per (path, mtime) and reuses the parsed rows on
    every subsequent call in this process. Pure I/O memoization, not a
    change to any matching/decision logic -- added because a full batch
    run calls these loaders once per waterbody (thousands of times), and
    without this, each call re-parses the entire 24,683-row statewide
    stocking CSV from scratch, which is the dominant cost of a full run.
    Safe for this project's read-only, locally-pre-pulled data files.
    """
    if not path.exists():
        return []
    key = (str(path), path.stat().st_mtime)
    cached = _csv_read_cache.get(key)
    if cached is not None:
        return cached
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    _csv_read_cache[key] = rows
    return rows


def _read_all_survey_rows() -> list:
    """Reads the original 22-lake survey sample plus batch2 (Part 4's
    additional survey-report pull), if present. Never errors if batch2
    doesn't exist yet -- it's an optional, later-arriving file."""
    return _read_csv_cached(SURVEY_CSV) + _read_csv_cached(SURVEY_CSV_BATCH2)


def load_survey_species(lake_name: str, county: str | None = None) -> list | None:
    """
    Returns a sorted list of (species, cpue_metric, cpue_value) for a
    survey-confirmed waterbody, or None if it isn't in the real survey
    sample. This is the authoritative source when present. Raises
    AmbiguousLakeError if the name matches more than one distinct real
    waterbody and no county was given to disambiguate (e.g. "Fish Lake"
    exists in both Dane and Waushara counties).
    """
    all_rows = _read_all_survey_rows()
    if not all_rows:
        return None
    rows = _resolve_distinct_waterbody(all_rows, "lake_name", "county", lake_name, county, "survey data")
    if rows is None:
        return None
    by_species = {}
    for row in rows:
        # Uppercase to match load_stocking_species's convention and the
        # physiology_thresholds_v1.json key casing -- the survey CSVs store
        # species in Title Case ("Walleye"), so without this every
        # survey-confirmed waterbody's species silently failed to match any
        # threshold (a real bug this full-run exercise surfaced: matching
        # only ever worked via the stocking-only path before this fix).
        species = row["species"].strip().upper()
        by_species.setdefault(species, []).append(
            (row.get("cpue_or_abundance_metric", ""), row.get("cpue_value", ""))
        )
    return sorted(by_species.items())


def survey_water_type(lake_name: str, county: str | None = None) -> str | None:
    """
    Real water_type from the survey data itself (batch2's PDFs are tagged
    lake/stream at extraction time -- ground truth, not a name guess), if
    this waterbody is survey-confirmed and its rows carry that column.
    Returns None if not survey-confirmed or the column isn't present
    (the original 22-lake sample predates this column; falls back to
    classify_waterbody_type's name heuristic in that case).
    """
    all_rows = _read_all_survey_rows()
    if not all_rows:
        return None
    target = _norm(lake_name)
    matched = [row for row in all_rows if _lake_name_matches(target, row["lake_name"])]
    if county:
        matched = [row for row in matched if _county_matches(county, row["county"])]
    for row in matched:
        wt = row.get("water_type", "").strip().lower()
        if wt in ("lake", "stream"):
            return wt
    return None


def load_stocking_species(
    lake_name: str, county: str | None = None, since_year: int = STOCKING_MIN_YEAR_FOR_PRESENCE
) -> list | None:
    """
    Returns [(species, last_stocked_year), ...] from the statewide stocking
    pull, or None if this lake has no stocking record at all in the pull.
    POSITIVE evidence only -- caller must label this "stocking-only,
    unconfirmed complete list", never treat as a full species inventory.
    Same ambiguity handling as load_survey_species.
    """
    all_rows = _read_csv_cached(STOCKING_CSV)
    if not all_rows:
        return None
    rows = _resolve_distinct_waterbody(all_rows, "waterbody", "county", lake_name, county, "stocking data")
    if rows is None:
        return None
    by_species = {}
    for row in rows:
        try:
            year = int(row["stocking_year"])
        except (ValueError, KeyError):
            continue
        if year < since_year:
            continue
        species = row["species"].strip().upper()
        prev = by_species.get(species)
        if prev is None or year > prev:
            by_species[species] = year
    if not by_species:
        return None
    return sorted(by_species.items())


def get_species_presence(lake_name: str, county: str | None = None) -> dict:
    """
    Returns {"tier": "survey_confirmed"|"stocking_only"|"no_data",
             "species": [...], "waterbody_type": "lake"|"stream",
             "detail": {...}} applying the presence-classification rule
    from docs/v1_species_presence_manifest.md: survey data is authoritative
    when present; stocking data is positive-only evidence, never proof of
    absence (per this cycle's Part 1, EVERY waterbody in the statewide
    stocking pull -- lake or stream, not just the original 22 survey lakes
    -- surfaces this way, not just a hand-picked subset); no data means no
    claim is made either way.
    """
    survey = load_survey_species(lake_name, county)
    if survey is not None:
        # Prefer the real, extraction-time water_type tag (batch2's PDFs
        # are tagged lake/stream from the source report itself) over the
        # name heuristic, when available.
        waterbody_type = survey_water_type(lake_name, county) or classify_waterbody_type(lake_name)
        return {
            "tier": "survey_confirmed",
            "species": [sp for sp, _ in survey],
            "detail": dict(survey),
            "waterbody_type": waterbody_type,
        }
    waterbody_type = classify_waterbody_type(lake_name)
    stocking = load_stocking_species(lake_name, county)
    if stocking is not None:
        return {
            "tier": "stocking_only",
            "species": [sp for sp, _ in stocking],
            "detail": dict(stocking),
            "waterbody_type": waterbody_type,
        }
    return {"tier": "no_data", "species": [], "detail": {}, "waterbody_type": waterbody_type}


def load_prepulled_water_temp(lake_name: str, county: str | None = None) -> dict | None:
    all_rows = _read_csv_cached(WATER_TEMP_CSV)
    if not all_rows:
        return None
    rows = _resolve_distinct_waterbody(all_rows, "lake_name", "county", lake_name, county, "water-temperature data")
    return rows[0] if rows else None


def list_known_lakes() -> list:
    """Every (lake, county) pair with SURVEY-CONFIRMED or pre-pulled
    real/proxy temperature data -- the small, high-confidence subset.
    Deduped by exact name, shown with county so name collisions (e.g. two
    "Fish Lake"s) are visible up front rather than discovered via an error."""
    pairs = set()
    for row in _read_all_survey_rows():
        pairs.add((row["lake_name"], row["county"]))
    for row in _read_csv_cached(WATER_TEMP_CSV):
        pairs.add((row["lake_name"], row["county"]))
    return sorted(pairs)


def list_stocking_only_waterbodies() -> list:
    """Every (waterbody, county, type) triple in the full statewide
    stocking pull -- ~2,338 entries, lakes AND streams. This is the full
    Part 1 coverage universe: every one of these gets a stocking-only
    presence result when queried, even though most have no survey or
    temperature data. Not printed by default (too large for a plain
    --list-lakes) -- use --list-stocking-only."""
    pairs = set()
    for row in _read_csv_cached(STOCKING_CSV):
        name = row["waterbody"].strip()
        if not name:
            continue
        pairs.add((name, row["county"], classify_waterbody_type(name)))
    return sorted(pairs)


# ---------------------------------------------------------------------------
# Live temperature refresh -- upgrades a stale pre-pulled proxy to a
# genuinely current one at run time. Never silently blends real vs. proxy.
# ---------------------------------------------------------------------------

def http_get_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_usgs_live_water_temp_c(site_id: str):
    url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={site_id}&parameterCd=00010&period=P1D"
    data = http_get_json(url)
    try:
        series = data["value"]["timeSeries"][0]["values"][0]["value"]
    except (KeyError, IndexError):
        return None, None
    if not series:
        return None, None
    latest = series[-1]
    return float(latest["value"]), latest["dateTime"]


def get_nws_current_air_temp_c(lat: float, lon: float):
    points = http_get_json(f"https://api.weather.gov/points/{lat},{lon}")
    stations = http_get_json(points["properties"]["observationStations"])
    for feature in stations["features"][:5]:
        try:
            obs = http_get_json(f"{feature['id']}/observations/latest")
        except (urllib.error.HTTPError, urllib.error.URLError):
            continue
        value_c = obs["properties"].get("temperature", {}).get("value")
        if value_c is None:
            continue
        station_name = feature["id"].rsplit("/", 1)[-1]
        return value_c, station_name, obs["properties"].get("timestamp")
    raise RuntimeError(f"No NWS station near ({lat},{lon}) returned a current reading")


def _parse_coords_from_notes(notes: str):
    """The Part 3b pull embedded 'lake coords LAT,LON' in the notes field
    for every NWS-proxy row -- reuse it rather than re-geocoding."""
    marker = "lake coords "
    idx = notes.find(marker)
    if idx == -1:
        return None
    rest = notes[idx + len(marker):]
    coord_str = rest.split(" ")[0].rstrip(",;")
    try:
        lat_s, lon_s = coord_str.split(",")
        return float(lat_s), float(lon_s)
    except ValueError:
        return None


def load_usgs_sites() -> list:
    return _read_csv_cached(USGS_SITES_CSV)


def find_usgs_site_matches(waterbody_name: str) -> list:
    """Real, generic name match against the 185-site USGS WI water-
    temperature reference table (Part 2/3: 177 streams + 8 lakes). USGS
    station names are formatted like "FOX RIVER AT BERLIN, WI" -- matches
    if the waterbody name is a substring of the station name. Returns
    every match (there can be several sites on the same named river);
    the caller tries them in order until one yields real live data."""
    target = _norm(waterbody_name.split("(")[0].strip())
    if len(target) < 4:
        return []
    matches = []
    for site in load_usgs_sites():
        if target in _norm(site["station_nm"]):
            matches.append(site)
    return matches


def load_lake_michigan_buoy_sites() -> list:
    return _read_csv_cached(LAKE_MICHIGAN_BUOY_CSV)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km -- used only to pick the nearest real
    NDBC buoy to a real, geocoded Lake Michigan coordinate, never to
    estimate or interpolate a temperature value itself."""
    import math

    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def find_nearest_buoys(lat: float, lon: float) -> list:
    """Every real NDBC/Lake Michigan buoy in the reference table
    (see data/v1/lake_michigan_buoy_sites.csv), nearest first. Returns
    all of them so the caller can try each in turn until one has a
    real, fresh reading -- some real buoys go stale or offline
    seasonally (verified: station 45014 was reporting nothing newer
    than a week old during this project's own live testing)."""
    sites = load_lake_michigan_buoy_sites()
    return sorted(sites, key=lambda s: _haversine_km(lat, lon, float(s["lat"]), float(s["lon"])))


NDBC_BUOY_MAX_AGE_HOURS = 48  # a real reading older than this isn't "live" in any useful sense


def parse_ndbc_realtime2(text: str, now: "datetime.datetime | None" = None):
    """Pure, testable: raw NDBC realtime2.txt content -> (value_c,
    observed_at_iso), or (None, None) if the most recent row has no real
    WTMP value or is older than NDBC_BUOY_MAX_AGE_HOURS. Real format:
    whitespace-columned, two comment header lines starting with '#',
    most-recent-first, 'MM' marks a missing field. Column order: YY MM
    DD hh mm WDIR WSPD GST WVHT DPD APD MWD PRES ATMP WTMP DEWP VIS PTDY
    TIDE (WTMP is column index 14)."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    if not lines:
        return None, None
    cols = lines[0].split()
    if len(cols) < 15:
        return None, None
    try:
        year, month, day, hour, minute = (int(c) for c in cols[:5])
        wtmp_raw = cols[14]
    except (ValueError, IndexError):
        return None, None
    if wtmp_raw == "MM":
        return None, None
    observed_at = datetime.datetime(year, month, day, hour, minute, tzinfo=datetime.timezone.utc)
    age_hours = (now - observed_at).total_seconds() / 3600
    if age_hours > NDBC_BUOY_MAX_AGE_HOURS:
        return None, None
    try:
        return float(wtmp_raw), observed_at.isoformat()
    except ValueError:
        return None, None


def get_ndbc_buoy_water_temp_c(station_id: str):
    """Live real-time water temperature from a real NOAA NDBC buoy --
    https://www.ndbc.noaa.gov/data/realtime2/<station_id>.txt, the
    standard public NDBC realtime2 text format. No API key, freely
    public. Returns (value_c, observed_at_iso), or (None, None) if the
    station has no recent reading (real buoys do go stale/offline,
    especially in winter) -- never a stale value silently presented as
    current. See parse_ndbc_realtime2() for the tested parsing logic;
    this wrapper only does the live fetch."""
    url = f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return parse_ndbc_realtime2(text)


def geocode_live(waterbody_name: str, county: str | None) -> tuple | None:
    """Live OpenStreetMap/Nominatim geocode, same real method used for the
    original 13 NWS-proxy lakes in Part 3b -- extended here to work for
    ANY waterbody name at request time, not just the ones pre-geocoded.
    Returns (lat, lon) or None if geocoding fails; never fabricates a
    location.

    Real, disclosed limitation: reach-level survey names carry a
    parenthetical description (e.g. "Rush River (whole surveyed reach)")
    that breaks the geocoder, so it's stripped before querying -- this
    means a multi-reach river's several entries all geocode to the same
    approximate point (the river's general location in that county), not
    the specific surveyed reach.
    """
    clean_name = waterbody_name.split("(")[0].strip()
    query = f"{clean_name}, {county} County, Wisconsin" if county else f"{clean_name}, Wisconsin"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "us"}
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None
    if not results:
        return None
    try:
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (KeyError, ValueError):
        return None


NO_TEMPERATURE_DATA = {
    "value_c": None,
    "is_real_water_measurement": False,
    "method": "no_data",
    "source": None,
    "observed_at": None,
}


def get_current_temperature(lake_name: str, county: str | None = None, live_refresh: bool = True) -> dict:
    """
    Resolution order, real sources only, honest no_data if all fail
    (Part 2/3: this now applies to ANY Wisconsin waterbody, lake or
    stream, not just the original 22 survey lakes):
      1. Live USGS gauge -- generic match against the 185-site real
         reference table (177 streams + 8 lakes), tried in order until one
         returns real current data. This is the PRIMARY real source for
         streams, which have far richer live USGS coverage than lakes do.
      1b. For Lake Michigan specifically: a live NOAA NDBC buoy water-
          temperature reading (real water measurement, not an air proxy)
          from the nearest of 15 real Lake Michigan buoys, tried in
          distance order until one has a fresh reading. USGS stream
          gauges don't cover the open lake, so this is Lake Michigan's
          own equivalent of step 1 -- inserted here, before falling back
          to an air-temperature proxy, specifically because a huge,
          thermally-buffered lake makes air temperature a poor stand-in
          for water temperature (verified: every Lake Michigan entry was
          using the air proxy before this was added).
      2. Pre-pulled real CLMN/USGS reading from the original 22-lake pull
         -- used AS-IS with its true observed date (real, dated data, not
         stale-and-hidden; CLMN itself is periodic, not a live feed).
      3. Live NWS air-temperature proxy, explicitly labeled as such --
         live geocode (Nominatim) + live current-conditions fetch for any
         waterbody not covered by 1, 1b, or 2.
      4. Honest no_data -- returned, never raised and never silently
         dropped; the narrative builder reports this plainly.
    """
    if live_refresh:
        for site in find_usgs_site_matches(lake_name):
            try:
                value_c, obs_time = get_usgs_live_water_temp_c(site["site_no"])
            except (urllib.error.HTTPError, urllib.error.URLError):
                continue
            if value_c is not None:
                return {
                    "value_c": value_c,
                    "is_real_water_measurement": True,
                    "method": "usgs_live",
                    "source": f"USGS live gauge {site['site_no']} ({site['station_nm']})",
                    "observed_at": obs_time,
                }

    if live_refresh and _norm(lake_name) == "LAKE MICHIGAN":
        coords = geocode_live(lake_name, county) or (geocode_live(county, None) if county else None)
        if coords:
            for buoy in find_nearest_buoys(*coords):
                try:
                    value_c, obs_time = get_ndbc_buoy_water_temp_c(buoy["station_id"])
                except (urllib.error.HTTPError, urllib.error.URLError):
                    continue
                if value_c is not None:
                    return {
                        "value_c": value_c,
                        "is_real_water_measurement": True,
                        "method": "ndbc_buoy_live",
                        "source": f"NOAA NDBC buoy {buoy['station_id']} ({buoy['station_name']})",
                        "observed_at": obs_time,
                    }

    row = load_prepulled_water_temp(lake_name, county)
    if row is not None:
        is_real = row["is_real_water_measurement"].strip().lower() == "true"
        if is_real:
            return {
                "value_c": float(row["value_c"]),
                "is_real_water_measurement": True,
                "method": row["method"],
                "source": row["source_url_or_station"],
                "observed_at": row["retrieved_at"],
                "note": row.get("notes", ""),
            }

        # Proxy row: try a live refresh; fall back to the pre-pulled proxy
        # value if that fails, but still label it a proxy either way.
        if live_refresh:
            coords = _parse_coords_from_notes(row.get("notes", ""))
            if coords:
                try:
                    value_c, station, obs_time = get_nws_current_air_temp_c(*coords)
                    return {
                        "value_c": value_c,
                        "is_real_water_measurement": False,
                        "method": "nws_air_proxy_live",
                        "source": f"NWS current air temperature (live refresh) [station {station}]",
                        "observed_at": obs_time,
                    }
                except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError):
                    pass  # fall back to the pre-pulled proxy value below

        cache_reason = "live refresh disabled (--no-live-refresh)" if not live_refresh else "live refresh attempted and failed"
        return {
            "value_c": float(row["value_c"]),
            "is_real_water_measurement": False,
            "method": row["method"] + "_cached",
            "source": row["source_url_or_station"] + f" (cached from prior pull, {cache_reason})",
            "observed_at": row["retrieved_at"],
            "note": row.get("notes", ""),
        }

    # Not in the pre-pulled snapshot at all (the common case for the
    # ~2,315 stocking-only waterbodies added this cycle) -- try a live
    # NWS proxy via live geocoding before giving up.
    if live_refresh:
        coords = geocode_live(lake_name, county)
        if coords:
            try:
                value_c, station, obs_time = get_nws_current_air_temp_c(*coords)
                return {
                    "value_c": value_c,
                    "is_real_water_measurement": False,
                    "method": "nws_air_proxy_live",
                    "source": f"NWS current air temperature (live refresh, live-geocoded) [station {station}]",
                    "observed_at": obs_time,
                }
            except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError):
                pass  # fall through to no_data below

    return dict(NO_TEMPERATURE_DATA)


# ---------------------------------------------------------------------------
# Narrative generation (same matching logic as mvp/conditions_forecast.py,
# extended for growth_optimum and the richer V1 threshold set)
# ---------------------------------------------------------------------------

def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def describe_threshold_match(current_c: float, threshold: dict) -> str | None:
    ttype = threshold["type"]
    kind_label = {
        "activity_window": "documented activity/feeding-temperature window",
        "spawning_trigger": "documented spawning-trigger range",
        "physiological_optimum": "documented physiological growth-optimum range",
        "growth_optimum": "documented growth-optimum range",
        "avoidance_above": "documented warm-water avoidance threshold",
    }.get(ttype, ttype)

    if "range_c" in threshold:
        lo, hi = threshold["range_c"]
        lo_f, hi_f = threshold.get("range_f", (c_to_f(lo), c_to_f(hi)))
        if not (lo <= current_c <= hi):
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


def describe_threshold_gap(current_c: float, threshold: dict) -> str | None:
    """The counterpart to describe_threshold_match(): when a threshold
    does NOT match the current temperature, this describes how far off
    and in which direction, instead of a silent, unexplained "no match."
    Returns None when the threshold DID match (nothing to explain) or
    when the gap genuinely can't be computed.

    For an avoidance_above threshold specifically, "not matching" means
    the water is NOT yet warm enough to trigger avoidance -- worded as
    neutral/reassuring information (water within a safe range for this
    species), not as a problem, since a non-match here is not a bad
    thing for the fish."""
    ttype = threshold["type"]
    kind_label = {
        "activity_window": "documented activity/feeding-temperature window",
        "spawning_trigger": "documented spawning-trigger range",
        "physiological_optimum": "documented physiological growth-optimum range",
        "growth_optimum": "documented growth-optimum range",
        "avoidance_above": "documented warm-water avoidance threshold",
    }.get(ttype, ttype)

    if "range_c" in threshold:
        lo, hi = threshold["range_c"]
        lo_f, hi_f = threshold.get("range_f", (c_to_f(lo), c_to_f(hi)))
        if lo <= current_c <= hi:
            return None
        if current_c < lo:
            gap_c, direction = lo - current_c, "below"
        else:
            gap_c, direction = current_c - hi, "above"
        gap_f = gap_c * 9 / 5
        return (
            f"currently {gap_f:.1f}°F / {gap_c:.1f}°C {direction} the {kind_label} "
            f"({lo_f:.0f}-{hi_f:.0f}°F / {lo:.1f}-{hi:.1f}°C) — {threshold['description']}"
        )

    if "threshold_c" in threshold:
        t_c = threshold["threshold_c"]
        t_f = threshold.get("threshold_f", c_to_f(t_c))
        if ttype == "avoidance_above":
            if current_c > t_c:
                return None
            gap_c = t_c - current_c
            gap_f = gap_c * 9 / 5
            return (
                f"currently {gap_f:.1f}°F / {gap_c:.1f}°C below the {kind_label} "
                f"({t_f:.0f}°F / {t_c:.1f}°C) — not yet warm enough to trigger avoidance behavior "
                f"for this species — {threshold['description']}"
            )
        return None

    if "preferred_point_c" in threshold:
        p_c = threshold["preferred_point_c"]
        p_f = threshold.get("preferred_point_f", c_to_f(p_c))
        if abs(current_c - p_c) <= 1.5:
            return None
        gap_c = abs(current_c - p_c)
        gap_f = gap_c * 9 / 5
        direction = "below" if current_c < p_c else "above"
        return (
            f"currently {gap_f:.1f}°F / {gap_c:.1f}°C {direction} the field-measured preferred temperature "
            f"({p_f:.1f}°F / {p_c:.1f}°C, outside the ±1.5°C window) — {threshold['description']}"
        )

    return None


RIVER_STREAM_CAVEAT = (
    "River/stream caveat: this value is derived from lake-based studies "
    "(see docs/v1_physiology_research_candidates.md and "
    "docs/v1_river_stream_coverage_report.md) and has not been verified to transfer to "
    "flowing-water conditions — reported with this caveat, not excluded."
)
DIEL_NOTE = (
    "This species also has documented low-light/dawn-dusk-or-nocturnal feeding activity "
    "(see docs/v1_physiology_research_candidates.md) — not evaluated against the clock here, "
    "logged for reference."
)


def evaluate_species_at_waterbody(species: str, value_c: float | None, waterbody_type: str, thresholds: dict) -> dict:
    """
    The core per-species prediction step, shared by build_narrative() (the
    single-waterbody CLI) and v1_full_run.py (the batch runner) so both
    exercise EXACTLY the same matching logic -- no drift between the two.

    Returns {"has_threshold_data": bool, "matches": [(description,
    evidence, river_caveat_applied: bool), ...], "non_matches": [str, ...],
    "diel_active": bool}. matches is empty (but has_threshold_data True)
    when the species has reference data but none of it matches the
    current temperature -- a real, expected outcome, distinct from "no
    reference data at all". non_matches is only populated in that no-match
    case (a real temperature reading exists, but nothing matched): one
    entry per threshold explaining how far off and in which direction,
    via describe_threshold_gap(), so "no match" is never an unexplained
    dead end -- this never changes which species count as matching,
    only adds explanatory text for the ones that don't.
    """
    species_entry = thresholds["species"].get(species)
    if not species_entry:
        return {"has_threshold_data": False, "matches": [], "non_matches": [], "diel_active": False}
    matches = []
    non_matches = []
    if value_c is not None:
        for t in species_entry["thresholds"]:
            m = describe_threshold_match(value_c, t)
            if m:
                river_caveat_applied = (
                    waterbody_type == "stream"
                    and t["type"] in ("activity_window", "physiological_optimum", "growth_optimum")
                )
                matches.append((m, t.get("evidence", "unspecified"), river_caveat_applied))
        if not matches:
            for t in species_entry["thresholds"]:
                gap = describe_threshold_gap(value_c, t)
                if gap:
                    non_matches.append(gap)
    return {
        "has_threshold_data": True,
        "matches": matches,
        "non_matches": non_matches,
        "diel_active": bool(species_entry.get("diel_active")),
    }


def build_narrative(lake_name: str, temp_info: dict, presence: dict, thresholds: dict) -> str:
    lines = []
    lines.append(f"# Conditions & Biology Forecast — {lake_name}")
    lines.append(f"_Generated {datetime.datetime.now(datetime.timezone.utc).isoformat()}_")
    lines.append("")
    lines.append(
        "**This is general, science-based seasonal context — not a catch prediction.** "
        "It does not estimate catch rate or the likelihood of catching any fish (Decision #005, #012)."
    )
    lines.append("")

    value_c = temp_info["value_c"]
    waterbody_type = presence.get("waterbody_type", "lake")

    if value_c is None:
        lines.append(
            "**No real or proxy water-temperature data is available for this waterbody.** "
            "Neither a live USGS gauge, a pre-pulled real reading, nor a live NWS proxy could be "
            "resolved. This is reported honestly as no_data, not a fabricated value."
        )
    else:
        value_f = c_to_f(value_c)
        measurement_note = (
            "a real water-temperature measurement"
            if temp_info["is_real_water_measurement"]
            else "an air-temperature PROXY, not a direct water-temperature measurement"
        )
        lines.append(
            f"**Current temperature reading:** {value_f:.1f}°F / {value_c:.1f}°C ({measurement_note}). "
            f"Source: {temp_info['source']}. Observed: {temp_info['observed_at']}."
        )
        if temp_info.get("note"):
            lines.append(f"_Note: {temp_info['note']}_")
    lines.append("")

    tier = presence["tier"]
    if tier == "no_data":
        lines.append(
            "**No species-presence data (survey or stocking) is on file for this waterbody in this "
            "project.** No species-level narrative can be generated. Run --list-lakes or "
            "--list-stocking-only to see waterbodies this tool has data for."
        )
        return "\n".join(lines)

    type_label = "stream/river" if waterbody_type == "stream" else "lake"
    if tier == "survey_confirmed":
        lines.append(
            f"**Species with real WDNR fisheries-survey-confirmed presence** "
            f"({len(presence['species'])}, {type_label}): "
            + ", ".join(sp.title() for sp in presence["species"])
        )
        lines.append(
            "_This is a real, DNR-observed species list from an electrofishing/netting survey — "
            "the authoritative source for this waterbody (see docs/v1_species_presence_manifest.md)._"
        )
    else:
        lines.append(
            f"**Species confirmed present via WDNR stocking records, 2011-present** "
            f"({len(presence['species'])}, {type_label}): "
            + ", ".join(sp.title() for sp in presence["species"])
        )
        lines.append(
            "_Stocking-only confirmation: this list is POSITIVE evidence these species were introduced here, "
            "NOT a complete species inventory — a species absent from this list may still be present "
            "(self-sustaining populations are often stocked less, not more). No real fisheries survey "
            "was pulled for this waterbody in this project._"
        )
    lines.append("")

    if value_c is None:
        lines.append(
            "_No species-vs-temperature narrative below, since no water-temperature data is available "
            "for this visit — species presence is still reported honestly above._"
        )
        return "\n".join(lines)

    lines.append("## Species notes")
    lines.append("")

    any_match = False
    for species in presence["species"]:
        evaluation = evaluate_species_at_waterbody(species, value_c, waterbody_type, thresholds)
        if not evaluation["has_threshold_data"]:
            continue
        matches = evaluation["matches"]
        non_matches = evaluation["non_matches"]
        diel_note = f" {DIEL_NOTE}" if evaluation["diel_active"] else ""
        if not matches and not non_matches and not diel_note:
            continue
        lines.append(f"### {species.title()}")
        if matches:
            any_match = True
            for m, evidence, river_caveat_applied in matches:
                caveat_text = f" **{RIVER_STREAM_CAVEAT}**" if river_caveat_applied else ""
                lines.append(f"- Water temperature is {m}. (Evidence quality: {evidence}){caveat_text}")
        elif non_matches:
            # Explains WHY this species isn't a match right now, instead
            # of a silent "no match" -- see describe_threshold_gap().
            lines.append("- No documented physiology window matches the current temperature. Why not:")
            for gap in non_matches:
                lines.append(f"  - Water temperature is {gap}.")
        if diel_note:
            lines.append(f"- {diel_note.strip()}")
        lines.append("")

    if not any_match:
        lines.append(
            "No species confirmed present in this waterbody currently has water temperature inside any "
            "of its documented physiology windows (or reference data isn't available for the species "
            "present here). No seasonal-context statement is generated for this visit — this is "
            "expected at many times of year, not an error. See each species above for why, when a real "
            "temperature reading was available to compare against."
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lake", help='Lake name, e.g. "Devils Lake"')
    parser.add_argument(
        "--county", default=None,
        help='Disambiguates lakes that share a name across counties, e.g. "Fish Lake" (Dane vs. Waushara)',
    )
    parser.add_argument(
        "--list-lakes", action="store_true",
        help="List waterbodies with survey-confirmed or pre-pulled temperature data (the high-confidence subset)",
    )
    parser.add_argument(
        "--list-stocking-only", action="store_true",
        help="List every waterbody (lake or stream) in the full statewide stocking pull (~2,338 entries)",
    )
    parser.add_argument(
        "--no-live-refresh", action="store_true",
        help="Use only the pre-pulled data/v1 snapshot, skip live USGS/NWS refetch (faster, offline-safe)",
    )
    args = parser.parse_args()

    if args.list_lakes:
        for name, county in list_known_lakes():
            print(f"{name} ({county})")
        return

    if args.list_stocking_only:
        for name, county, wtype in list_stocking_only_waterbodies():
            print(f"{name} ({county}) [{wtype}]")
        return

    if not args.lake:
        parser.error("--lake is required (or use --list-lakes / --list-stocking-only)")

    thresholds = load_thresholds()

    try:
        presence = get_species_presence(args.lake, args.county)
        temp_info = get_current_temperature(args.lake, args.county, live_refresh=not args.no_live_refresh)
    except AmbiguousLakeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(build_narrative(args.lake, temp_info, presence, thresholds))


if __name__ == "__main__":
    main()
