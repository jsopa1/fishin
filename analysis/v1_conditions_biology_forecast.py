#!/usr/bin/env python3
"""
Wisconsin Conditions & Biology Forecast — V1, expanded statewide (Part 4).

Supersedes mvp/conditions_forecast.py's single-lake demo with the real,
expanded V1 data foundation built in Parts 2-3 of this cycle:
  - data/v1/wi_fisheries_survey_species_sample.csv (22 real, survey-
    confirmed lakes -- actual observed species composition)
  - data/v1/wi_stocking_statewide_2011_2025.csv (24,683 real statewide
    stocking records, 2,338 waterbodies -- POSITIVE evidence only, never
    used to conclude a species is absent)
  - data/v1/wi_lake_water_temp_current.csv (real current/recent water
    temperature for the 22 survey lakes + Lake Monona, via USGS live /
    WDNR CLMN recent readings / NWS air-temp proxy, each honestly labeled)
  - data/v1/physiology_thresholds_v1.json (26-species physiology reference,
    docs/v1_physiology_research_candidates.md)

Still explicitly NOT a catch-rate prediction (Decision #005, #012). Every
output states this plainly.

Usage:
    python analysis/v1_conditions_biology_forecast.py --lake "Devils Lake"
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
STOCKING_CSV = DATA_V1 / "wi_stocking_statewide_2011_2025.csv"
WATER_TEMP_CSV = DATA_V1 / "wi_lake_water_temp_current.csv"
THRESHOLDS_JSON = DATA_V1 / "physiology_thresholds_v1.json"

USER_AGENT = "fishin-v1-conditions-forecast/0.1 (research prototype; contact via project repo)"

# The one lake in wi_lake_water_temp_current.csv with a genuinely LIVE
# (not just recent) real water-temperature source, confirmed in Part 3b.
USGS_LIVE_SITES = {
    "lake monona": "05429000",
}

STOCKING_MIN_YEAR_FOR_PRESENCE = 2011  # matches the statewide pull's own window


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


def load_survey_species(lake_name: str, county: str | None = None) -> list | None:
    """
    Returns a sorted list of (species, cpue_metric, cpue_value) for a
    survey-confirmed lake, or None if this lake isn't in the real survey
    sample (22 lakes). This is the authoritative source when present.
    Raises AmbiguousLakeError if the name matches more than one distinct
    real lake and no county was given to disambiguate (e.g. "Fish Lake"
    exists in both Dane and Waushara counties).
    """
    if not SURVEY_CSV.exists():
        return None
    target = _norm(lake_name)
    with open(SURVEY_CSV, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    matched = [row for row in all_rows if _lake_name_matches(target, row["lake_name"])]
    if not matched:
        return None
    groups = _group_rows_by_distinct_lake(matched, "lake_name", "county")
    if county:
        groups = {k: v for k, v in groups.items() if _county_matches(county, k[1])}
    if len(groups) > 1:
        options = ", ".join(f"{n} ({c})" for n, c in sorted(groups))
        raise AmbiguousLakeError(
            f"'{lake_name}' matches more than one distinct lake in the survey data: {options}. "
            f"Pass --county to disambiguate."
        )
    if not groups:
        return None
    rows = next(iter(groups.values()))
    by_species = {}
    for row in rows:
        by_species.setdefault(row["species"], []).append(
            (row.get("cpue_or_abundance_metric", ""), row.get("cpue_value", ""))
        )
    return sorted(by_species.items())


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
    if not STOCKING_CSV.exists():
        return None
    target = _norm(lake_name)
    with open(STOCKING_CSV, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    matched = [row for row in all_rows if _lake_name_matches(target, row["waterbody"])]
    if not matched:
        return None
    groups = _group_rows_by_distinct_lake(matched, "waterbody", "county")
    if county:
        groups = {k: v for k, v in groups.items() if _county_matches(county, k[1])}
    if len(groups) > 1:
        options = ", ".join(f"{n} ({c})" for n, c in sorted(groups))
        raise AmbiguousLakeError(
            f"'{lake_name}' matches more than one distinct lake in the stocking data: {options}. "
            f"Pass --county to disambiguate."
        )
    if not groups:
        return None
    rows = next(iter(groups.values()))
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
             "species": [...]} applying the presence-classification rule
    from docs/v1_species_presence_manifest.md: survey data is authoritative
    when present; stocking data is positive-only evidence, never proof of
    absence; no data means no claim is made either way.
    """
    survey = load_survey_species(lake_name, county)
    if survey is not None:
        return {
            "tier": "survey_confirmed",
            "species": [sp for sp, _ in survey],
            "detail": dict(survey),
        }
    stocking = load_stocking_species(lake_name, county)
    if stocking is not None:
        return {
            "tier": "stocking_only",
            "species": [sp for sp, _ in stocking],
            "detail": dict(stocking),
        }
    return {"tier": "no_data", "species": [], "detail": {}}


def load_prepulled_water_temp(lake_name: str, county: str | None = None) -> dict | None:
    if not WATER_TEMP_CSV.exists():
        return None
    target = _norm(lake_name)
    with open(WATER_TEMP_CSV, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    matched = [row for row in all_rows if _lake_name_matches(target, row["lake_name"])]
    if not matched:
        return None
    groups = _group_rows_by_distinct_lake(matched, "lake_name", "county")
    if county:
        groups = {k: v for k, v in groups.items() if _county_matches(county, k[1])}
    if len(groups) > 1:
        options = ", ".join(f"{n} ({c})" for n, c in sorted(groups))
        raise AmbiguousLakeError(
            f"'{lake_name}' matches more than one distinct lake in the water-temperature data: "
            f"{options}. Pass --county to disambiguate."
        )
    if not groups:
        return None
    return next(iter(groups.values()))[0]


def list_known_lakes() -> list:
    """Every (lake, county) pair this script has SOME real data for, deduped
    by exact name -- shown with county so name collisions (e.g. two "Fish
    Lake"s) are visible up front rather than discovered via an error."""
    pairs = set()
    if SURVEY_CSV.exists():
        with open(SURVEY_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pairs.add((row["lake_name"], row["county"]))
    if WATER_TEMP_CSV.exists():
        with open(WATER_TEMP_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pairs.add((row["lake_name"], row["county"]))
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


def get_current_temperature(lake_name: str, county: str | None = None, live_refresh: bool = True) -> dict:
    """
    Resolution order (Part 3b's real findings):
      1. USGS live gauge, if this lake is one of the confirmed live sites
         (currently just Lake Monona) -- refetched live every run.
      2. Pre-pulled real CLMN/USGS reading from Part 3b's data pull --
         used AS-IS with its true observed date (this is real, dated data,
         not stale-and-hidden; CLMN itself is periodic, not a live feed).
      3. Live NWS air-temperature proxy, explicitly labeled as such --
         refetched live every run using coordinates recovered from the
         pre-pull's notes, since a live proxy is more honest than a
         cached one that grows staler by the day.
    """
    key = _norm(lake_name).lower()
    if key in USGS_LIVE_SITES and live_refresh:
        site_id = USGS_LIVE_SITES[key]
        try:
            value_c, obs_time = get_usgs_live_water_temp_c(site_id)
            if value_c is not None:
                return {
                    "value_c": value_c,
                    "is_real_water_measurement": True,
                    "method": "usgs_live",
                    "source": f"USGS live gauge {site_id}",
                    "observed_at": obs_time,
                }
        except (urllib.error.HTTPError, urllib.error.URLError):
            pass  # fall through to the pre-pulled row / proxy below

    row = load_prepulled_water_temp(lake_name, county)
    if row is None:
        raise ValueError(
            f"No water-temperature data (real or proxy) on file for '{lake_name}'. "
            f"Run --list-lakes to see lakes with data."
        )

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
            "**No species-presence data (survey or stocking) is on file for this lake in this project.** "
            "No species-level narrative can be generated. Run --list-lakes to see lakes this tool has data for."
        )
        return "\n".join(lines)

    if tier == "survey_confirmed":
        lines.append(
            f"**Species with real WDNR fisheries-survey-confirmed presence** "
            f"({len(presence['species'])}): " + ", ".join(sp.title() for sp in presence["species"])
        )
        lines.append(
            "_This is a real, DNR-observed species list from an electrofishing/netting survey — "
            "the authoritative source for this lake (see docs/v1_species_presence_manifest.md)._"
        )
    else:
        lines.append(
            f"**Species confirmed present via WDNR stocking records, 2011-present** "
            f"({len(presence['species'])}): " + ", ".join(sp.title() for sp in presence["species"])
        )
        lines.append(
            "_Stocking-only confirmation: this list is POSITIVE evidence these species were introduced here, "
            "NOT a complete species inventory — a species absent from this list may still be present "
            "(self-sustaining populations are often stocked less, not more). No real fisheries survey "
            "was pulled for this lake in this project._"
        )
    lines.append("")
    lines.append("## Species notes")
    lines.append("")

    any_match = False
    for species in presence["species"]:
        species_entry = thresholds["species"].get(species)
        if not species_entry:
            continue
        matches = []
        for t in species_entry["thresholds"]:
            m = describe_threshold_match(value_c, t)
            if m:
                matches.append((m, t.get("evidence", "unspecified")))
        diel_note = ""
        if species_entry.get("diel_active"):
            diel_note = (
                " This species also has documented low-light/dawn-dusk-or-nocturnal feeding activity "
                "(see docs/v1_physiology_research_candidates.md) — not evaluated against the clock here, "
                "logged for reference."
            )
        if not matches and not diel_note:
            continue
        any_match = True
        lines.append(f"### {species.title()}")
        for m, evidence in matches:
            lines.append(f"- Water temperature is {m}. (Evidence quality: {evidence})")
        if diel_note:
            lines.append(f"- {diel_note.strip()}")
        lines.append("")

    if not any_match:
        lines.append(
            "No species confirmed present in this lake currently has water temperature inside any "
            "of its documented physiology windows (or reference data isn't available for the species "
            "present here). No seasonal-context statement is generated for this visit — this is "
            "expected at many times of year, not an error."
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
    parser.add_argument("--list-lakes", action="store_true", help="List every lake this tool has real data for")
    parser.add_argument(
        "--no-live-refresh", action="store_true",
        help="Use only the pre-pulled data/v1 snapshot, skip live USGS/NWS refetch (faster, offline-safe)",
    )
    args = parser.parse_args()

    if args.list_lakes:
        for name, county in list_known_lakes():
            print(f"{name} ({county})")
        return

    if not args.lake:
        parser.error("--lake is required (or use --list-lakes)")

    thresholds = load_thresholds()

    try:
        presence = get_species_presence(args.lake, args.county)
        temp_info = get_current_temperature(args.lake, args.county, live_refresh=not args.no_live_refresh)
    except AmbiguousLakeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(build_narrative(args.lake, temp_info, presence, thresholds))


if __name__ == "__main__":
    main()
