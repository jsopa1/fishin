"""
Data-access layer for the V1 results review UI. No Tkinter/GUI imports
here on purpose -- this module is the unit-testable part (Part 5); the
GUI (v1_review_app.py) is a thin presentation layer on top of it.

Reads the real, already-generated data/v1/v1_full_run_results.db produced
by analysis/v1_full_run.py. Never writes to it, never fabricates a
result -- every function returns exactly what's stored, including
no_data/None values, so the UI can present them honestly.
"""

import datetime
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "analysis"))
import v1_bait_technique as bait  # noqa: E402
import v1_conditions_biology_forecast as v1  # noqa: E402

DEFAULT_STALE_HOURS = 24


def find_db_path(start: Path = None) -> Path | None:
    """
    Locates data/v1/v1_full_run_results.db by walking up from `start`
    (defaults to this file's directory, or the frozen .exe's directory
    when packaged) through parent directories. Returns None if not found
    within 6 levels -- the caller must handle that (show an error in the
    UI), never guess a path that might not exist.
    """
    import sys

    if start is None:
        if getattr(sys, "frozen", False):
            start = Path(sys.executable).parent
        else:
            start = Path(__file__).parent

    current = start
    for _ in range(6):
        candidate = current / "data" / "v1" / "v1_full_run_results.db"
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_run(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM runs ORDER BY finished_at DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def get_latest_temperature_refresh(conn: sqlite3.Connection) -> dict | None:
    """When the sensor-backed temperatures were last refreshed
    (analysis/refresh_temperatures.py), which is a different and much
    faster clock than the full run.

    These two ages are not interchangeable. Water temperature moves in
    hours -- a real reading went from 17.0C to 12.1C over one 43-hour
    window during testing, a bigger shift than the width of some spawning
    windows. Species presence and stocking records come from annual
    surveys and are not meaningfully staler at 40 hours than at 4. Judging
    both by the batch-run timestamp told users everything was stale when
    only one thing actually was."""
    try:
        row = conn.execute(
            "SELECT * FROM temperature_refreshes WHERE finished_at IS NOT NULL "
            "ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return dict(row) if row else None


def parse_iso(ts: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(ts)


def data_age(run_row: dict, now: datetime.datetime = None) -> datetime.timedelta | None:
    """Real elapsed time since the run finished, or None if there's no
    run row / no finished_at yet (a run still in progress or never run)."""
    if not run_row or not run_row.get("finished_at"):
        return None
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now - parse_iso(run_row["finished_at"])


def is_stale(run_row: dict, max_age_hours: float = DEFAULT_STALE_HOURS, now: datetime.datetime = None) -> bool:
    """True if there's no run at all, or the most recent run finished
    more than max_age_hours ago. Defaults to stale (True) on missing data
    -- never presents an absent run as fresh."""
    age = data_age(run_row, now)
    if age is None:
        return True
    return age.total_seconds() > max_age_hours * 3600


def get_summary_counts(conn: sqlite3.Connection) -> dict:
    """Live counts straight from the DB, for the Summary tab to
    sanity-check against docs/v1_full_run_report.md's own totals."""
    def _counts(query):
        return {row[0]: row[1] for row in conn.execute(query)}

    return {
        "total_waterbodies": conn.execute("SELECT COUNT(*) FROM waterbody_results").fetchone()[0],
        "total_species_predictions": conn.execute("SELECT COUNT(*) FROM species_predictions").fetchone()[0],
        "total_failures": conn.execute("SELECT COUNT(*) FROM run_failures").fetchone()[0],
        "by_tier": _counts("SELECT presence_tier, COUNT(*) FROM waterbody_results GROUP BY presence_tier"),
        "by_type": _counts("SELECT waterbody_type, COUNT(*) FROM waterbody_results GROUP BY waterbody_type"),
        "by_temp_method": _counts(
            "SELECT temp_method || CASE WHEN temp_is_real=1 THEN ' (real)' ELSE ' (proxy/none)' END, COUNT(*) "
            "FROM waterbody_results GROUP BY temp_method, temp_is_real"
        ),
        "by_failure_type": _counts("SELECT failure_type, COUNT(*) FROM run_failures GROUP BY failure_type"),
        "species_any_match": _counts("SELECT any_match, COUNT(*) FROM species_predictions GROUP BY any_match"),
    }


TIER_CHOICES = ("all", "survey_confirmed", "stocking_only")


def _like_pattern(term: str) -> str:
    """
    Builds a safe '%term%' SQL LIKE pattern, escaping SQL wildcard
    characters (% and _) in the user's own input first. Without this, a
    real waterbody/species search containing a literal "%" or "_" (rare,
    but not impossible -- e.g. a name fragment someone copy-pastes) would
    be silently reinterpreted as a wildcard instead of matched literally.
    Callers must add "ESCAPE '\\'" to the SQL LIKE clause.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_distinct_counties(conn: sqlite3.Connection) -> list:
    return [r[0] for r in conn.execute("SELECT DISTINCT county FROM waterbody_results ORDER BY county")]


def list_distinct_species(conn: sqlite3.Connection) -> list:
    return [r[0] for r in conn.execute("SELECT DISTINCT species FROM species_predictions ORDER BY species")]


def search_waterbodies(
    conn: sqlite3.Connection,
    name: str = None,
    county: str = None,
    species: str = None,
    tier: str = "all",
    limit: int = 500,
) -> list:
    """
    Real substring/exact filtering against the stored results -- never
    guesses or fuzzy-matches beyond a plain SQL LIKE on name/county, so
    what's shown is exactly what's in the database.
    """
    clauses = []
    params = []

    if name:
        clauses.append("wr.waterbody_name LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(name))
    if county:
        clauses.append("wr.county LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(county))
    if tier and tier != "all":
        clauses.append("wr.presence_tier = ?")
        params.append(tier)

    if species:
        clauses.append(
            "EXISTS (SELECT 1 FROM species_predictions sp WHERE sp.waterbody_name = wr.waterbody_name "
            "AND sp.county = wr.county AND sp.species LIKE ? ESCAPE '\\')"
        )
        params.append(_like_pattern(species.upper()))

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        f"SELECT wr.* FROM waterbody_results wr {where} "
        f"ORDER BY wr.waterbody_name, wr.county LIMIT ?"
    )
    params.append(limit)
    return [dict(row) for row in conn.execute(query, params)]


def get_waterbody_detail(conn: sqlite3.Connection, waterbody_name: str, county: str) -> dict | None:
    """
    Full detail for one waterbody: the persisted narrative text exactly
    as generated, the temperature record, and every species prediction
    row (including river/stream caveats and disputed-threshold text)
    exactly as stored -- nothing simplified or dropped for display.
    """
    wb_row = conn.execute(
        "SELECT * FROM waterbody_results WHERE waterbody_name = ? AND county = ?", (waterbody_name, county)
    ).fetchone()
    if wb_row is None:
        return None
    species_rows = conn.execute(
        "SELECT * FROM species_predictions WHERE waterbody_name = ? AND county = ? ORDER BY species",
        (waterbody_name, county),
    ).fetchall()
    waterbody = dict(wb_row)
    species_predictions = [dict(r) for r in species_rows]
    attach_bait_guidance(species_predictions, waterbody.get("temp_value_c"))
    return {
        "waterbody": waterbody,
        "species_predictions": species_predictions,
    }


def search_failures(
    conn: sqlite3.Connection,
    waterbody: str = None,
    species: str = None,
    failure_type: str = None,
    limit: int = 500,
) -> list:
    clauses = []
    params = []
    if waterbody:
        clauses.append("waterbody_name LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(waterbody))
    if species:
        clauses.append("species LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(species.upper()))
    if failure_type and failure_type != "all":
        clauses.append("failure_type = ?")
        params.append(failure_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM run_failures {where} ORDER BY waterbody_name, county LIMIT ?"
    params.append(limit)
    return [dict(row) for row in conn.execute(query, params)]


def list_distinct_failure_types(conn: sqlite3.Connection) -> list:
    return [r[0] for r in conn.execute("SELECT DISTINCT failure_type FROM run_failures ORDER BY failure_type")]


# ---------------------------------------------------------------------------
# V2: access points (real WDNR public boat access / shore fishing sites,
# see analysis/v2_access_points.py). Wrapped in try/except OperationalError
# because these tables only exist once that script has been run at least
# once against this DB file -- an older committed DB predating V2 should
# report "no data" honestly, not crash the whole page.
# ---------------------------------------------------------------------------

def get_access_points_meta(conn: sqlite3.Connection) -> dict | None:
    try:
        row = conn.execute("SELECT * FROM access_points_meta WHERE id = 1").fetchone()
    except sqlite3.OperationalError:
        return None
    return dict(row) if row else None


def list_access_points(
    conn: sqlite3.Connection,
    county: str = None,
    source_type: str = None,
    waterbody: str = None,
    species: str = None,
    limit: int = 5000,
) -> list:
    """Real, current access-point rows for the map -- every field exactly
    as stored, including a null matched_waterbody_name/county when this
    point couldn't be confidently linked to a known V1 waterbody entry.

    When shore_fishing_details exists for a row (see
    analysis/v2_shore_fishing_details.py), its real per-site fields
    (species list, directions, amenities, ADA info) are joined in --
    NULL for every other row, never fabricated.

    A `species` filter matches EITHER real source, independently: a
    shore-fishing site whose own WDNR-published species list contains
    the term, OR a point linked to a V1 waterbody where V1's own
    species_predictions has a matching record. Never merges or
    cross-fabricates between the two -- a point can match via one path,
    the other, both, or neither."""
    clauses = []
    params = []
    if county:
        clauses.append("ap.county LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(county))
    if source_type and source_type != "all":
        clauses.append("ap.source_type = ?")
        params.append(source_type)
    if waterbody:
        clauses.append("(ap.waterbody_name LIKE ? ESCAPE '\\' OR ap.matched_waterbody_name LIKE ? ESCAPE '\\')")
        params.append(_like_pattern(waterbody))
        params.append(_like_pattern(waterbody))
    if species:
        clauses.append(
            "("
            "EXISTS (SELECT 1 FROM shore_fishing_species_canonical sfc WHERE sfc.more_info_url = ap.more_info_url "
            "AND sfc.canonical_species = ?)"
            " OR "
            "EXISTS (SELECT 1 FROM species_predictions sp WHERE sp.waterbody_name = ap.matched_waterbody_name "
            "AND sp.county = ap.matched_county AND sp.species LIKE ? ESCAPE '\\')"
            ")"
        )
        params.append(species)
        params.append(_like_pattern(species.upper()))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT ap.*, sfd.directions, sfd.fishing_trail, sfd.fixed_pier, sfd.end_of_pier_depth,
               sfd.travel_route_surface, sfd.vehicle_stalls, sfd.vehicle_trailer_stalls,
               sfd.restrooms, sfd.fish_species_raw, sfd.fish_cleaning_area,
               sfd.additional_amenities, sfd.comments, sfd.ada_vehicle_stalls,
               sfd.ada_vehicle_trailer_stalls, sfd.ada_restrooms, sfd.property_manager,
               sfd.property_manager_phone
        FROM access_points ap
        LEFT JOIN shore_fishing_details sfd ON sfd.more_info_url = ap.more_info_url
        {where}
        ORDER BY ap.waterbody_name, ap.county
        LIMIT ?
    """
    params.append(limit)
    try:
        return [dict(row) for row in conn.execute(query, params)]
    except sqlite3.OperationalError:
        # shore_fishing_details/shore_fishing_species may not exist yet on
        # an older DB predating this script -- fall back to plain access
        # points rather than a hard failure.
        clauses_fallback = []
        params_fallback = []
        if county:
            clauses_fallback.append("county LIKE ? ESCAPE '\\'")
            params_fallback.append(_like_pattern(county))
        if source_type and source_type != "all":
            clauses_fallback.append("source_type = ?")
            params_fallback.append(source_type)
        if waterbody:
            clauses_fallback.append("(waterbody_name LIKE ? ESCAPE '\\' OR matched_waterbody_name LIKE ? ESCAPE '\\')")
            params_fallback.append(_like_pattern(waterbody))
            params_fallback.append(_like_pattern(waterbody))
        where_fallback = f"WHERE {' AND '.join(clauses_fallback)}" if clauses_fallback else ""
        fallback_query = f"SELECT * FROM access_points {where_fallback} ORDER BY waterbody_name, county LIMIT ?"
        params_fallback.append(limit)
        try:
            return [dict(row) for row in conn.execute(fallback_query, params_fallback)]
        except sqlite3.OperationalError:
            return []


def list_combined_species(conn: sqlite3.Connection) -> list:
    """A single, deduplicated (case-insensitive) species list spanning
    both real sources: V1's own clean species_predictions list, and the
    CANONICAL species WDNR's shore-fishing pages resolve to (see
    analysis/v2_species_canonicalization.py -- the raw text itself, e.g.
    "SM BASS" or "LAREMOUTH BASS", is preserved untouched everywhere it's
    displayed; only this filter-list/lookup path uses the canonical
    form). Without canonicalizing first, this list would offer dozens of
    near-duplicate options for a handful of real species (verified: 61
    raw WDNR phrases collapse to 30 real species here). Where the same
    species appears in both sources with different casing, V1's form is
    kept as the canonical display form since it's already normalized;
    this never changes which underlying rows a filter on either form
    matches (list_access_points checks both sources)."""
    try:
        v1_species = [r[0] for r in conn.execute("SELECT DISTINCT species FROM species_predictions")]
    except sqlite3.OperationalError:
        v1_species = []
    try:
        shore_species = [
            r[0] for r in conn.execute("SELECT DISTINCT canonical_species FROM shore_fishing_species_canonical")
        ]
    except sqlite3.OperationalError:
        shore_species = []

    seen_upper = {}
    for s in v1_species:
        seen_upper.setdefault(s.upper(), s.title())
    for s in shore_species:
        if s.upper() not in seen_upper:
            seen_upper[s.upper()] = s.title()
    return sorted(seen_upper.values())


# ---------------------------------------------------------------------------
# V2: invasive species sightings (real WDNR-verified AIS locations, see
# analysis/v2_invasive_species.py). Same "no crash on a DB predating this
# script" discipline as the access-points functions above. Per this
# project's positive-only-evidence rule: a sighting here is real, verified
# positive evidence -- absence of a sighting is never evidence a species
# isn't present, since WDNR's monitoring coverage is real but not
# exhaustive (the same rule already applied to stocking-derived presence).
# ---------------------------------------------------------------------------

def get_invasive_species_meta(conn: sqlite3.Connection) -> dict | None:
    try:
        row = conn.execute("SELECT * FROM invasive_species_meta WHERE id = 1").fetchone()
    except sqlite3.OperationalError:
        return None
    return dict(row) if row else None


def list_invasive_species_sightings(
    conn: sqlite3.Connection,
    species: str = None,
    limit: int = 2000,
) -> list:
    clauses = []
    params = []
    if species and species != "all":
        clauses.append("species_common_name = ?")
        params.append(species)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM invasive_species_sightings {where} ORDER BY species_common_name LIMIT ?"
    params.append(limit)
    try:
        return [dict(row) for row in conn.execute(query, params)]
    except sqlite3.OperationalError:
        return []


def list_distinct_invasive_species(conn: sqlite3.Connection) -> list:
    try:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT species_common_name FROM invasive_species_sightings ORDER BY species_common_name"
        )]
    except sqlite3.OperationalError:
        return []


# ---------------------------------------------------------------------------
# Spot-level temperature interpolation (V2 fish-intelligence deepening,
# Decision #021 / docs/v2_fish_intelligence_platform_plan.md Phase 1).
# Most access points aren't matched to a full V1 waterbody record, so
# they have no temperature at all today. This estimates one from nearby
# REAL (never proxy) readings only -- honestly returning nothing when no
# real reading is close enough, rather than guessing.
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Same formula as analysis/v1_conditions_biology_forecast.py's
    _haversine_km (verified there against a real Milwaukee-Chicago
    distance) -- duplicated rather than imported to keep ui/ and
    analysis/ independent of each other's internals; this one function
    is small and stable enough that the duplication is cheaper than the
    coupling."""
    import math

    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_temperature_anchors(conn: sqlite3.Connection) -> list:
    """Every REAL (non-proxy) water-temperature reading from the latest
    V1 run, paired with a real coordinate -- the anchor pool for
    spot-level interpolation. A real-temp waterbody with no available
    coordinate is left out of the pool rather than geocoded fresh here
    (this must stay fast: called per spot-detail request, not once per
    batch run, unlike the live geocoding v1_full_run.py already does).

    Three real coordinate sources, tried in order per waterbody:
      1. A matched access point's own real ArcGIS coordinate (covers
         the large majority of real-temp waterbodies with any public
         access at all).
      2. The USGS gauge site's own coordinate, for `usgs_live` readings
         not covered by (1) -- reuses v1's own find_usgs_site_matches().
      3. The NDBC buoy's own coordinate, for `ndbc_buoy_live` readings
         not covered by (1) -- parsed from the stored temp_source text
         (e.g. "NOAA NDBC buoy 45013 (...)").

    Returns [{"lat", "lon", "value_c", "waterbody_name", "county",
    "source"}, ...], one entry per distinct real-temp waterbody that
    resolved a coordinate.
    """
    try:
        row = conn.execute("SELECT run_timestamp FROM runs ORDER BY finished_at DESC LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        return []
    if row is None:
        return []
    latest = row[0]

    anchors = {}  # (name, county) -> anchor dict; first coordinate source found wins

    try:
        rows = conn.execute(
            """SELECT wr.waterbody_name, wr.county, wr.temp_value_c, wr.temp_method,
                      ap.latitude, ap.longitude
               FROM waterbody_results wr
               JOIN access_points ap ON ap.matched_waterbody_name = wr.waterbody_name
                   AND ap.matched_county = wr.county
               WHERE wr.temp_is_real = 1 AND wr.run_timestamp = ?""",
            (latest,),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    for name, county, value_c, method, lat, lon in rows:
        key = (name, county)
        if key not in anchors:
            anchors[key] = {
                "lat": lat, "lon": lon, "value_c": value_c,
                "waterbody_name": name, "county": county, "source": method,
            }

    remaining_usgs = conn.execute(
        "SELECT waterbody_name, county, temp_value_c, temp_method FROM waterbody_results "
        "WHERE temp_is_real = 1 AND run_timestamp = ? AND temp_method = 'usgs_live'", (latest,)
    ).fetchall()
    for name, county, value_c, method in remaining_usgs:
        key = (name, county)
        if key in anchors:
            continue
        matches = v1.find_usgs_site_matches(name)
        if matches:
            site = matches[0]
            anchors[key] = {
                "lat": float(site["lat"]), "lon": float(site["lon"]), "value_c": value_c,
                "waterbody_name": name, "county": county, "source": method,
            }

    buoy_sites = {s["station_id"]: s for s in v1.load_lake_michigan_buoy_sites()}
    remaining_buoy = conn.execute(
        "SELECT waterbody_name, county, temp_value_c, temp_method, temp_source FROM waterbody_results "
        "WHERE temp_is_real = 1 AND run_timestamp = ? AND temp_method = 'ndbc_buoy_live'", (latest,)
    ).fetchall()
    for name, county, value_c, method, source in remaining_buoy:
        key = (name, county)
        if key in anchors:
            continue
        for station_id, site in buoy_sites.items():
            if f"buoy {station_id} " in (source or "") or (source or "").endswith(f"buoy {station_id}"):
                anchors[key] = {
                    "lat": float(site["lat"]), "lon": float(site["lon"]), "value_c": value_c,
                    "waterbody_name": name, "county": county, "source": method,
                }
                break

    # Defence in depth, at the boundary where stored rows become inputs to
    # interpolation. A single implausible value (USGS reports missing data
    # as the sentinel -999999, not as an omitted point) doesn't just render
    # wrong on its own page -- as an anchor it silently corrupts every spot
    # within the search radius. The parse-time guard in
    # v1_conditions_biology_forecast prevents new ones; this stops any row
    # already written by an older run from reaching the estimator.
    return [a for a in anchors.values() if v1.is_plausible_water_temp_c(a["value_c"])]


# How far an estimate may reach, and how much to trust it at that range.
#
# Both numbers are measured, not chosen: every pair of the real anchors in
# this database was bucketed by separation distance and the disagreement
# between the two readings recorded (see docs/v2_ux_redesign_report.md and
# DECISIONS #026). Observed median | 90th-percentile disagreement:
#
#     0-15km   0.5C | 7.4C      40-60km   2.2C | 10.8C
#    15-25km   0.5C | 2.5C     60-100km   2.3C |  8.9C
#    25-40km   1.7C | 5.3C
#
# The cutoff is 60km because beyond it the estimate stops being useful for
# this app's actual purpose: the physiology windows it compares against are
# narrow (Brown Trout's feeding window is 7.7C wide; its spawning trigger is
# 2.2C wide), so once the error approaches the width of the window, a
# match/no-match conclusion drawn from it means nothing even though the
# number still looks plausible.
DEFAULT_MAX_ANCHOR_KM = 60.0
ESTIMATE_CONFIDENCE_BANDS = (
    # (max nearest-anchor distance, level, typical error, plain-language note)
    (15.0, "high", 0.5,
     "within 15km of a real reading, where readings typically agree to within half a degree"),
    (40.0, "moderate", 1.7,
     "the nearest real reading is far enough that a degree or two of error is typical"),
    (DEFAULT_MAX_ANCHOR_KM, "low", 2.2,
     "the nearest real reading is distant -- treat this as a regional guide, not a lake-specific value"),
)


def describe_estimate_confidence(nearest_km: float, spread_c: float | None = None) -> dict:
    """How far to trust an interpolated estimate, from measured quantities
    only: how far away the nearest real reading is, and (when more than one
    was used) how much those readings disagree with each other.

    This is deliberately not a percentage. A number like "78% confident"
    implies a validated probability this project has never measured, which
    is exactly the kind of false precision Decision #005 rules out. The
    bands below are observed typical errors at real distances."""
    level, typical_error_c, note = "low", 2.2, ESTIMATE_CONFIDENCE_BANDS[-1][3]
    for max_km, band_level, band_error, band_note in ESTIMATE_CONFIDENCE_BANDS:
        if nearest_km <= max_km:
            level, typical_error_c, note = band_level, band_error, band_note
            break

    # Anchors that disagree with each other are direct evidence that this
    # area's water isn't uniform right now, whatever the distance says.
    if spread_c is not None and spread_c > 3.0 and level != "low":
        level = "moderate" if level == "high" else "low"
        typical_error_c = max(typical_error_c, spread_c / 2)
        note = (
            f"nearby real readings disagree by {spread_c:.1f}C, so this area's water "
            "isn't uniform right now"
        )

    return {"level": level, "typical_error_c": typical_error_c, "note": note}


def estimate_temperature_from_nearby(
    conn: sqlite3.Connection, lat: float, lon: float,
    max_km: float = DEFAULT_MAX_ANCHOR_KM, max_anchors: int = 5,
):
    """Inverse-distance-weighted estimate from real anchor readings
    only (build_temperature_anchors) within max_km. Returns None when no
    real anchor is close enough -- an honest absence, never a fabricated
    guess with nothing behind it. Never uses a proxy reading as an
    anchor: a proxy is already an estimate, and re-estimating from an
    estimate would compound uncertainty invisibly.

    Returns {"value_c", "anchor_count", "nearest_km", "spread_c",
    "confidence", "anchors": [...]} on success.
    """
    anchors = build_temperature_anchors(conn)
    nearby = []
    for a in anchors:
        d = _haversine_km(lat, lon, a["lat"], a["lon"])
        if d <= max_km:
            nearby.append((d, a))
    if not nearby:
        return None
    nearby.sort(key=lambda pair: pair[0])
    nearby = nearby[:max_anchors]

    weights = [1.0 / max(d, 0.05) for d, _ in nearby]
    total_weight = sum(weights)
    value_c = sum(w * a["value_c"] for w, (_, a) in zip(weights, nearby)) / total_weight

    used_values = [a["value_c"] for _, a in nearby]
    spread_c = (max(used_values) - min(used_values)) if len(used_values) > 1 else None
    nearest_km = nearby[0][0]

    return {
        "value_c": value_c,
        "anchor_count": len(nearby),
        "nearest_km": nearest_km,
        "spread_c": spread_c,
        "confidence": describe_estimate_confidence(nearest_km, spread_c),
        "anchors": [
            {"waterbody_name": a["waterbody_name"], "county": a["county"], "distance_km": round(d, 1)}
            for d, a in nearby
        ],
    }


# ---------------------------------------------------------------------------
# Spot detail (V2 fish-intelligence deepening, Phases 1/2/4 -- Decision
# #021 / docs/v2_fish_intelligence_platform_plan.md). "Spot" means any
# access point on the map, matched to a V1 waterbody or not -- the
# one-stop-shop view the CEO described.
# ---------------------------------------------------------------------------

_COORD_MATCH_TOLERANCE = 0.0001  # ~11m at WI latitudes -- exact-float-equality-safe but not so loose it could pick up a different real point


def find_access_point_by_coords(conn: sqlite3.Connection, lat: float, lon: float, name: str = None) -> dict | None:
    """Looks up one access point by its own real coordinate -- the stable
    key for a spot-detail link, since access_points.id is only an
    AUTOINCREMENT that isn't stable across a future re-ingestion (see
    docs/v2_access_points_report.md section 8). `name` (facility_name)
    disambiguates the rare (23 of 3,272) case of two real points sharing
    a coordinate. Reuses the same shore_fishing_details join as
    list_access_points so a spot page has every field the map popup has."""
    base_query = """
        SELECT ap.*, sfd.directions, sfd.fishing_trail, sfd.fixed_pier, sfd.end_of_pier_depth,
               sfd.travel_route_surface, sfd.vehicle_stalls, sfd.vehicle_trailer_stalls,
               sfd.restrooms, sfd.fish_species_raw, sfd.fish_cleaning_area,
               sfd.additional_amenities, sfd.comments, sfd.ada_vehicle_stalls,
               sfd.ada_vehicle_trailer_stalls, sfd.ada_restrooms, sfd.property_manager,
               sfd.property_manager_phone
        FROM access_points ap
        LEFT JOIN shore_fishing_details sfd ON sfd.more_info_url = ap.more_info_url
        WHERE ABS(ap.latitude - ?) < ? AND ABS(ap.longitude - ?) < ?
    """
    params = [lat, _COORD_MATCH_TOLERANCE, lon, _COORD_MATCH_TOLERANCE]
    if name:
        base_query += " AND ap.facility_name = ?"
        params.append(name)
    try:
        row = conn.execute(base_query, params).fetchone()
    except sqlite3.OperationalError:
        fallback_query = "SELECT * FROM access_points WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ?"
        fallback_params = [lat, _COORD_MATCH_TOLERANCE, lon, _COORD_MATCH_TOLERANCE]
        if name:
            fallback_query += " AND facility_name = ?"
            fallback_params.append(name)
        row = conn.execute(fallback_query, fallback_params).fetchone()
    return dict(row) if row else None


def get_spot_temperature(
    conn: sqlite3.Connection, lat: float, lon: float, matched_waterbody: str = None, matched_county: str = None
) -> dict | None:
    """Resolves one spot's water temperature, honestly, in priority order:
      1. A real (non-proxy) V1 measurement, when this spot is matched to
         a waterbody that already has one -- the most direct real evidence.
      2. An inverse-distance-weighted estimate from real nearby readings
         (estimate_temperature_from_nearby) -- more informative than a
         generic air-temperature proxy when a real reading exists nearby.
      3. The matched waterbody's own proxy temperature, only if nothing
         better was found.
      4. None (honest no-data) if none of the above resolves.
    Every branch is labeled distinctly (`resolution`) so the UI never
    conflates a real measurement, an estimate, and a proxy."""
    matched_row = None
    if matched_waterbody and matched_county:
        matched_row = conn.execute(
            "SELECT temp_value_c, temp_is_real, temp_method, temp_source, temp_observed_at "
            "FROM waterbody_results WHERE waterbody_name = ? AND county = ?",
            (matched_waterbody, matched_county),
        ).fetchone()

    if matched_row and matched_row["temp_is_real"] and matched_row["temp_value_c"] is not None:
        return {
            "value_c": matched_row["temp_value_c"],
            "is_real": True,
            "method": matched_row["temp_method"],
            "source": matched_row["temp_source"],
            "observed_at": matched_row["temp_observed_at"],
            "resolution": "matched_waterbody_real",
        }

    estimate = estimate_temperature_from_nearby(conn, lat, lon)
    if estimate is not None:
        return {
            "value_c": estimate["value_c"],
            "is_real": False,
            "method": "interpolated_nearby",
            "resolution": "interpolated_nearby",
            "anchor_count": estimate["anchor_count"],
            "nearest_km": estimate["nearest_km"],
            "spread_c": estimate["spread_c"],
            "confidence": estimate["confidence"],
            "anchors": estimate["anchors"],
        }

    if matched_row and matched_row["temp_value_c"] is not None:
        return {
            "value_c": matched_row["temp_value_c"],
            "is_real": False,
            "method": matched_row["temp_method"],
            "source": matched_row["temp_source"],
            "observed_at": matched_row["temp_observed_at"],
            "resolution": "matched_waterbody_proxy",
        }

    return None


def attach_bait_guidance(species_predictions: list, temp_c: float | None) -> list:
    """Adds bait/technique guidance to each species prediction, resolved
    from the current temperature (see analysis/v1_bait_technique.py).

    Deliberately attached for every state, not only when a species is
    currently matching. The original plan showed it only on matches, on
    the reasoning that recommending bait for a fish that isn't biting
    undercuts trust -- but the guidance is state-aware, so in cold water
    it explains *why* the fish can't chase and what that means for the
    presentation. That is more useful than silence and just as honest.
    """
    if temp_c is None or not species_predictions:
        return species_predictions

    try:
        thresholds = v1.load_thresholds()["species"]
    except Exception:  # noqa: BLE001 -- guidance is an enhancement, never a page-breaker
        return species_predictions

    for prediction in species_predictions:
        entry = thresholds.get(prediction["species"].upper())
        if not entry:
            continue
        prediction["bait_guidance"] = bait.get_guidance(
            prediction["species"], entry.get("thresholds", []), temp_c
        )
    return species_predictions


def _window_distance_c(thresholds: list, temp_c: float):
    """How far the current temperature sits from the nearest documented
    feeding/activity window, and which way. Zero means inside it.

    Returns (distance_c, direction, window_range_c) or None when the
    species has no activity window to measure against."""
    best = None
    for threshold in thresholds:
        if threshold.get("type") not in ("activity_window", "growth_optimum", "physiological_optimum"):
            continue
        low_high = threshold.get("range_c")
        if not low_high:
            continue
        low, high = low_high
        if low <= temp_c <= high:
            return (0.0, "inside", low_high)
        distance = (low - temp_c) if temp_c < low else (temp_c - high)
        direction = "below" if temp_c < low else "above"
        if best is None or distance < best[0]:
            best = (distance, direction, low_high)
    return best


def rank_species_by_proximity(species_predictions: list, temp_c: float) -> list:
    """Order species by how close conditions are to their documented
    window, nearest first.

    This exists because 42% of waterbodies currently have no species
    inside a window at all, and answering "nothing is matching" is a dead
    end for the reader. The distance is already known -- the app computes
    it to explain *why* a species isn't matching -- so it can rank on it
    and always give a best-available answer instead of a blank.

    Ranking is not a prediction. A species 1C outside its documented
    window is not "probably biting"; it is the closest thing to it here,
    and the page says exactly that."""
    if temp_c is None or not species_predictions:
        return []
    try:
        thresholds = v1.load_thresholds()["species"]
    except Exception:  # noqa: BLE001
        return []

    ranked = []
    for prediction in species_predictions:
        entry = thresholds.get(prediction["species"].upper())
        if not entry:
            continue
        measured = _window_distance_c(entry.get("thresholds", []), temp_c)
        if measured is None:
            continue
        distance_c, direction, window = measured
        ranked.append({
            "species": prediction["species"],
            "any_match": bool(prediction.get("any_match")),
            "distance_c": distance_c,
            "distance_f": distance_c * 9 / 5,
            "direction": direction,
            "window_c": window,
            "diel_active": bool(prediction.get("diel_active")),
        })

    ranked.sort(key=lambda r: (not r["any_match"], r["distance_c"]))
    return ranked


def build_spot_verdict(species_predictions: list, temperature: dict | None, activity_window: dict | None) -> dict:
    """The one-line answer a spot page opens with: is it worth fishing
    here today, and for what.

    Everything here is derived from data already on the page. The point
    is ordering, not new information -- a reader should get the answer
    before the evidence, rather than assembling it from five sections."""
    temp_c = temperature.get("value_c") if temperature else None
    ranked = rank_species_by_proximity(species_predictions, temp_c)
    matching = [r for r in ranked if r["any_match"]]

    verdict = {
        "temp_c": temp_c,
        "temp_confidence": (temperature or {}).get("confidence"),
        "temp_is_real": bool((temperature or {}).get("is_real")),
        "matching": matching,
        "closest": ranked[0] if ranked and not matching else None,
        "next_window": None,
        "headline": None,
        "detail": None,
    }

    if activity_window and (not ranked or any(r["diel_active"] for r in ranked)):
        verdict["next_window"] = activity_window

    if temp_c is None:
        verdict["headline"] = "No temperature reading"
        verdict["detail"] = (
            "Without a water temperature there is nothing to compare against physiology, "
            "so this page can't say whether conditions favour anything here."
        )
    elif matching:
        names = ", ".join(m["species"].title() for m in matching[:3])
        more = len(matching) - 3
        verdict["headline"] = (
            f"{len(matching)} species in their documented window"
            if len(matching) > 1 else "1 species in its documented window"
        )
        verdict["detail"] = names + (f", and {more} more" if more > 0 else "")
    elif verdict["closest"]:
        closest = verdict["closest"]
        verdict["headline"] = "Nothing is inside its window right now"
        verdict["detail"] = (
            f"Closest is {closest['species'].title()}, "
            f"{closest['distance_f']:.1f}°F {closest['direction']} its documented window."
        )
    else:
        verdict["headline"] = "No species data for this spot"
        verdict["detail"] = "WDNR publishes no species record tied to this exact location."
    return verdict


def get_wdnr_lake_species(conn: sqlite3.Connection, waterbody: str, county: str) -> dict | None:
    """WDNR's own published fish list for this water, with abundance.

    This is the agency's assessment rather than this app's inference, and
    it carries an abundance rating ("Abundant"/"Common"/"Present") that
    appears nowhere else in this project's data. It also catches
    self-sustaining populations that were never stocked -- the blind spot
    of stocking-derived presence.

    It is deliberately NOT used to drive species-level physiology
    matching, because WDNR's published vocabulary is coarser than species:
    the whole list is nine categories, and "Trout" does not say brook,
    brown or rainbow -- which matters, since those have materially
    different thermal thresholds. Expanding a category into a species
    would be inventing a fact WDNR did not state.
    """
    if not waterbody:
        return None
    try:
        row = conn.execute(
            "SELECT wbic FROM wdnr_wbic_map WHERE UPPER(waterbody_name) = UPPER(?) "
            "AND UPPER(county) = UPPER(?) AND wbic IS NOT NULL",
            (waterbody, county),
        ).fetchone()
        if row is None:
            return None
        wbic = row["wbic"]
        species = conn.execute(
            "SELECT category, abundance, lake_name, acres FROM wdnr_lake_species "
            "WHERE wbic = ? ORDER BY CASE abundance WHEN 'Abundant' THEN 0 "
            "WHEN 'Common' THEN 1 WHEN 'Present' THEN 2 ELSE 3 END, category",
            (wbic,),
        ).fetchall()
    except sqlite3.OperationalError:
        return None

    if not species:
        return None
    return {
        "wbic": wbic,
        "lake_name": species[0]["lake_name"],
        "acres": species[0]["acres"],
        "species": [{"category": r["category"], "abundance": r["abundance"]} for r in species],
        "regulations_url": (
            "https://apps.dnr.wi.gov/fisheriesmanagement/Public/LakeRegulation/Details"
            f"?WBIC={wbic}"
        ),
        "lake_page_url": f"https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic={wbic}",
    }


def get_stocking_history(conn: sqlite3.Connection, waterbody: str, county: str, since_year: int = 2020) -> dict | None:
    """Real WDNR stocking records for one water, as published.

    This project has held these records since V1 but only ever used them
    as a yes/no presence signal. The detail is the most concrete thing
    WDNR publishes about a water: "16,466 brown trout yearlings averaging
    9 inches, 2025" tells an angler what is actually in there and roughly
    how big, which a species name alone does not.

    Matched on the stocking file's own waterbody/county spelling, which
    is the same source the presence data is derived from.
    """
    if not waterbody:
        return None
    try:
        rows = conn.execute(
            """SELECT stocking_year, species, strain, age_class, number_stocked,
                      avg_length_in, source_type
               FROM stocking_history
               WHERE UPPER(waterbody) = UPPER(?) AND UPPER(county) = UPPER(?)
                 AND stocking_year >= ?
               ORDER BY stocking_year DESC, number_stocked DESC""",
            (waterbody, county, since_year),
        ).fetchall()
    except sqlite3.OperationalError:
        return None
    if not rows:
        return None

    events = [dict(r) for r in rows]
    return {
        "waterbody": waterbody,
        "county": county,
        "since_year": since_year,
        "latest_year": events[0]["stocking_year"],
        "total_stocked": sum(e["number_stocked"] or 0 for e in events),
        "species_count": len({e["species"] for e in events}),
        "events": events,
    }


def get_activity_window(lat: float, lon: float, when=None) -> dict | None:
    """Today's real dawn and dusk times at this location.

    This is the part the DNR's own tool has no equivalent for. Several
    species in this app's physiology data carry a documented
    dawn/dusk/nocturnal feeding flag (`diel_active`), but "fish at dawn"
    is useless without knowing when dawn actually is at this latitude on
    this date -- and Wisconsin's sunrise moves by more than three hours
    across the year.

    Computed astronomically (NOAA's standard solar position algorithm),
    so it needs no network call and works for any coordinate. Civil
    twilight is used for the low-light window boundaries because that is
    the light level the feeding behaviour is associated with, not the
    instant of sunrise.
    """
    import datetime
    import math

    if lat is None or lon is None:
        return None
    when = when or datetime.datetime.now(datetime.timezone.utc)
    day_of_year = when.timetuple().tm_yday

    # NOAA solar position, simplified: declination and the hour angle at
    # which the sun sits at a given altitude.
    decl = 0.4093 * math.sin(2 * math.pi * (284 + day_of_year) / 365.0)
    lat_rad = math.radians(lat)

    def hour_angle(altitude_deg: float):
        alt = math.radians(altitude_deg)
        cos_h = (math.sin(alt) - math.sin(lat_rad) * math.sin(decl)) / (
            math.cos(lat_rad) * math.cos(decl)
        )
        if cos_h > 1 or cos_h < -1:
            return None  # sun never reaches this altitude here today
        return math.degrees(math.acos(cos_h)) / 15.0  # hours from solar noon

    sunrise_offset = hour_angle(-0.833)      # standard refraction-corrected sunrise
    twilight_offset = hour_angle(-6.0)       # civil twilight
    if sunrise_offset is None or twilight_offset is None:
        return None

    # Solar noon in UTC for this longitude, with the equation of time.
    b = 2 * math.pi * (day_of_year - 81) / 364.0
    eq_time = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    solar_noon_utc = 12.0 - (lon / 15.0) - (eq_time / 60.0)

    def to_time(hours_utc: float) -> datetime.datetime:
        # No modulo here: at Wisconsin's longitude solar noon sits around
        # 18:00 UTC, so sunset lands past midnight UTC. Wrapping it into
        # the same calendar day produced the right clock time on the wrong
        # date, and made sunset sort before sunrise.
        base = datetime.datetime(when.year, when.month, when.day, tzinfo=datetime.timezone.utc)
        return base + datetime.timedelta(hours=hours_utc)

    return {
        "dawn_start": to_time(solar_noon_utc - twilight_offset),
        "sunrise": to_time(solar_noon_utc - sunrise_offset),
        "sunset": to_time(solar_noon_utc + sunrise_offset),
        "dusk_end": to_time(solar_noon_utc + twilight_offset),
        "computed_for": when,
    }


def get_current_highlights(conn: sqlite3.Connection, limit: int = 3) -> list:
    """Real species/waterbody pairs where conditions match a documented
    physiology window right now, for the landing page.

    Restricted to survey-confirmed waterbodies with a real (non-proxy)
    temperature reading, so the front page shows the strongest evidence
    the database actually holds rather than its most eye-catching claim.
    One per waterbody, so it reads as a picture of the state rather than
    five facts about one lake."""
    try:
        rows = conn.execute(
            """SELECT sp.species, sp.match_description, sp.evidence_quality,
                      wr.waterbody_name, wr.county, wr.temp_value_c
               FROM species_predictions sp
               JOIN waterbody_results wr
                 ON wr.waterbody_name = sp.waterbody_name AND wr.county = sp.county
               WHERE sp.any_match = 1
                 AND wr.temp_is_real = 1
                 AND wr.presence_tier = 'survey_confirmed'
                 AND sp.match_description IS NOT NULL
               ORDER BY wr.waterbody_name, sp.species"""
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    # Distinct on both axes: three cards showing the same species, or the
    # same lake three times, reads as a bug rather than as a picture of
    # what's happening across the state.
    seen_waters, seen_species, highlights = set(), set(), []
    for r in rows:
        key = (r["waterbody_name"], r["county"])
        if key in seen_waters or r["species"] in seen_species:
            continue
        seen_waters.add(key)
        seen_species.add(r["species"])
        highlights.append({
            "species": r["species"],
            "waterbody_name": r["waterbody_name"],
            "county": r["county"],
            "temp_value_c": r["temp_value_c"],
            "match_description": r["match_description"],
            "evidence_quality": r["evidence_quality"],
        })
        if len(highlights) >= limit:
            break
    return highlights


def get_citizen_observed_species(conn: sqlite3.Connection, lat: float, lon: float,
                                  radius_km: float = 8.0, limit: int = 10) -> list:
    """Real, dated, geotagged fish sightings from GBIF (see
    analysis/v3_gbif_species_observations.py for the ingest, and why this
    is a distinct, weaker tier than a WDNR survey). Matched to a spot by
    real distance, the same nearest-neighbor approach already used for
    temperature interpolation -- there is no lake-polygon layer to join
    against for arbitrary ponds, so proximity is the honest option.

    Returns the single most recent sighting per species within
    radius_km, nearest-first is not the goal here -- most recent is,
    since "is this species still around" is the actual question. Never
    merged into species_predictions or the verdict: this is its own
    tier, `citizen_observed`, shown separately."""
    if lat is None or lon is None:
        return []
    try:
        rows = conn.execute(
            """SELECT common_name, lat, lon, observed_date, recorded_by, gbif_url
               FROM gbif_species_observations"""
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    nearby_by_species = {}
    for r in rows:
        distance = _haversine_km(lat, lon, r["lat"], r["lon"])
        if distance > radius_km:
            continue
        species = r["common_name"]
        existing = nearby_by_species.get(species)
        # Most recent wins -- "is this species still around" is the
        # question, not "which sighting happened to be closest."
        if existing is None or (r["observed_date"] or "") > (existing["observed_date"] or ""):
            nearby_by_species[species] = {
                "species": species,
                "distance_km": round(distance, 1),
                "observed_date": r["observed_date"],
                "recorded_by": r["recorded_by"],
                "gbif_url": r["gbif_url"],
            }

    results = sorted(nearby_by_species.values(), key=lambda x: x["observed_date"] or "", reverse=True)
    return results[:limit]


def get_county_species_evidence(conn: sqlite3.Connection, county: str, limit: int = 8) -> dict | None:
    """Real, county-level species evidence for a spot that has no record of
    its own -- 45% of access points are in that position, and an empty page
    is a dead end for the user.

    This is deliberately NOT presented as this waterbody's species list.
    It answers a different, weaker, still-useful question: what does WDNR
    actually document in this county's waters? An angler reading "Walleye
    in 84 Vilas County waterbodies" learns something true about where they
    are standing; inventing a species list for the specific lake would not.

    Counts are waterbodies with a documented record, so they carry the same
    positive-only-evidence rule used everywhere else: a low count means
    little documentation, never confirmed absence."""
    if not county:
        return None
    try:
        # Case-insensitive on purpose: access_points.county is raw WDNR
        # source text and mixes "WAUKESHA" and "Waukesha" for the same
        # real county, while species_predictions/waterbody_results use a
        # single consistent casing. An exact match silently returned
        # nothing for 144 real access points across 54 counties -- caught
        # by checking why spots with a real WDNR-documented county still
        # showed no county-level fallback at all.
        rows = conn.execute(
            """SELECT sp.species AS species,
                      COUNT(DISTINCT sp.waterbody_name) AS waterbody_count,
                      SUM(CASE WHEN wr.presence_tier = 'survey_confirmed' THEN 1 ELSE 0 END) AS survey_confirmed
               FROM species_predictions sp
               JOIN waterbody_results wr
                 ON wr.waterbody_name = sp.waterbody_name AND wr.county = sp.county
               WHERE UPPER(sp.county) = UPPER(?)
               GROUP BY sp.species
               ORDER BY waterbody_count DESC, sp.species
               LIMIT ?""",
            (county, limit),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(DISTINCT waterbody_name) FROM waterbody_results WHERE UPPER(county) = UPPER(?)", (county,)
        ).fetchone()[0]
    except sqlite3.OperationalError:
        return None

    if not rows:
        return None
    return {
        "county": county,
        "waterbodies_in_county": total,
        "species": [
            {
                "species": r["species"],
                "waterbody_count": r["waterbody_count"],
                "survey_confirmed": bool(r["survey_confirmed"]),
            }
            for r in rows
        ],
    }


def _activity_for_species(species_name: str, temp_c) -> dict | None:
    """The same distance-to-documented-window math the spot verdict
    already uses, reusable per-species so every evidence tier can carry
    its own honest activity read rather than duplicating this logic."""
    if temp_c is None:
        return None
    try:
        thresholds_all = v1.load_thresholds()["species"]
    except Exception:  # noqa: BLE001
        return None
    entry = thresholds_all.get(species_name.upper())
    if not entry:
        return None
    measured = _window_distance_c(entry.get("thresholds", []), temp_c)
    if measured is None:
        return None
    distance_c, direction, window_c = measured
    return {
        "inside_window": direction == "inside",
        "distance_f": round(distance_c * 9 / 5, 1),
        "direction": direction,
        "window_c": window_c,
    }


def build_species_categories(species_predictions: list, waterbody: dict | None,
                              county_species: dict | None, citizen_observed: list,
                              temp_c) -> dict:
    """Consolidates every species-level evidence source into two honest
    buckets instead of scattering them across separate boxes:

    - **Confirmed Sightings**: a WDNR fisheries survey actually documented
      this species here, OR a real person logged a community-ID-verified
      sighting of it nearby (GBIF/iNaturalist). Either way, someone or
      something actually observed the fish.
    - **Likely species to find**: positive but indirect evidence only --
      WDNR stocked it here (stocking is not proof of a current
      population), or it's documented somewhere else in this county.

    A species with real confirming evidence is never also listed as
    merely "likely" -- the stronger evidence wins and the entry is not
    duplicated.

    WDNR's own per-lake category list (Panfish, Largemouth Bass, ...) is
    deliberately NOT folded into either bucket: it is coarser than
    species, and turning "Panfish (Common)" into a specific species entry
    here would be exactly the category-to-species expansion this project
    has refused to do since the WDNR lake-species ingest (#032). It stays
    its own separate box.

    Each entry carries an `activity` read (inside its documented window,
    or how far below/above) computed against the current temperature --
    the same math the spot's headline verdict already uses -- so "is this
    species actually favoured right now" travels with it into both
    buckets, not just the confirmed one."""
    confirmed: dict = {}
    likely: dict = {}

    survey_confirmed = bool(waterbody and waterbody.get("presence_tier") == "survey_confirmed")
    for p in species_predictions:
        species = p["species"]
        bucket = confirmed if survey_confirmed else likely
        entry = bucket.setdefault(species, {
            "species": species, "sources": [], "activity": _activity_for_species(species, temp_c),
        })
        source = "WDNR fisheries survey" if survey_confirmed else "WDNR stocking record"
        if source not in entry["sources"]:
            entry["sources"].append(source)

    for o in citizen_observed:
        species = o["species"]
        likely.pop(species, None)  # a real sighting supersedes mere "likely"
        entry = confirmed.setdefault(species, {
            "species": species, "sources": [], "activity": _activity_for_species(species, temp_c),
        })
        date = (o.get("observed_date") or "")[:10]
        source = f"citizen sighting{' (' + date + ')' if date else ''}"
        entry["sources"].append(source)
        entry["citizen_detail"] = o

    if county_species:
        for s in county_species["species"]:
            species = s["species"]
            if species in confirmed:
                continue
            entry = likely.setdefault(species, {
                "species": species, "sources": [], "activity": _activity_for_species(species, temp_c),
            })
            if "regional (county) record" not in entry["sources"]:
                entry["sources"].append("regional (county) record")

    return {
        "confirmed_sightings": sorted(confirmed.values(), key=lambda x: x["species"]),
        "likely_species": sorted(likely.values(), key=lambda x: x["species"]),
    }


def _apply_categories_to_verdict(verdict: dict, species_categories: dict) -> None:
    """Mutates verdict in place -- only ever called when the original
    verdict had nothing to say (no waterbody match at all), so there is
    no existing claim here to contradict, only a blank to honestly fill
    from the WDNR-category / county / citizen-sighting evidence the
    dashboard above already shows."""
    all_entries = species_categories["confirmed_sightings"] + species_categories["likely_species"]
    with_activity = [e for e in all_entries if e.get("activity")]
    if not with_activity:
        return  # genuinely nothing to say -- leave "No species data" as-is

    inside = [e for e in with_activity if e["activity"]["inside_window"]]
    if inside:
        names = ", ".join(e["species"].title() for e in inside[:3])
        more = len(inside) - 3
        verdict["headline"] = (
            f"{len(inside)} species in their documented window"
            if len(inside) > 1 else "1 species in its documented window"
        )
        verdict["detail"] = names + (f", and {more} more" if more > 0 else "")
        verdict["matching"] = inside  # so the verdict box's own good/quiet styling matches this headline
    else:
        closest = min(with_activity, key=lambda e: e["activity"]["distance_f"])
        verdict["headline"] = "Nothing is inside its window right now"
        verdict["detail"] = (
            f"Closest is {closest['species'].title()}, "
            f"{closest['activity']['distance_f']}°F {closest['activity']['direction']} its documented window."
        )


def get_spot_detail(conn: sqlite3.Connection, lat: float, lon: float, name: str = None) -> dict | None:
    """The full one-stop-shop payload for a single spot: its own real
    access-point fields, an honestly-resolved temperature (see
    get_spot_temperature), and -- only when matched to a known V1
    waterbody -- that waterbody's full record (including the generated
    narrative_text) and species predictions (Phase 2: reused unchanged,
    never guessed for an unmatched point). A matched spot's own page
    carries everything a separate /waterbody page would have shown, so
    a user never has to leave the spot page to see the full conditions
    picture. Returns None only when the coordinate doesn't resolve to
    any real access point at all."""
    point = find_access_point_by_coords(conn, lat, lon, name=name)
    if point is None:
        return None

    temperature = get_spot_temperature(
        conn, lat, lon,
        matched_waterbody=point.get("matched_waterbody_name"),
        matched_county=point.get("matched_county"),
    )

    waterbody = None
    species_predictions = []
    if point.get("matched_waterbody_name") and point.get("matched_county"):
        wb_detail = get_waterbody_detail(conn, point["matched_waterbody_name"], point["matched_county"])
        if wb_detail:
            waterbody = wb_detail["waterbody"]
            species_predictions = wb_detail["species_predictions"]

    # Only for spots with no record of their own: real county-level evidence
    # instead of a dead end. Never merged with the above -- a spot either has
    # its own documented species or it honestly has regional context, never
    # both presented as one thing.
    if species_predictions and temperature:
        attach_bait_guidance(species_predictions, temperature.get("value_c"))

    county_species = None
    if not species_predictions:
        county_species = get_county_species_evidence(conn, point.get("county"))

    # Low-light timing only matters if something here is documented as a
    # dawn/dusk feeder, so it is attached conditionally rather than shown
    # as generic sunrise trivia.
    diel_species = [s["species"] for s in species_predictions if s.get("diel_active")]
    activity_window = get_activity_window(lat, lon) if diel_species else None

    stocking = None
    if point.get("matched_waterbody_name") and point.get("matched_county"):
        stocking = get_stocking_history(conn, point["matched_waterbody_name"], point["matched_county"])
    if stocking is None:
        stocking = get_stocking_history(conn, point.get("waterbody_name"), point.get("county"))

    wdnr_species = None
    if point.get("matched_waterbody_name") and point.get("matched_county"):
        wdnr_species = get_wdnr_lake_species(conn, point["matched_waterbody_name"], point["matched_county"])
    if wdnr_species is None:
        wdnr_species = get_wdnr_lake_species(conn, point.get("waterbody_name"), point.get("county"))

    verdict = build_spot_verdict(species_predictions, temperature, activity_window)
    citizen_observed = get_citizen_observed_species(conn, lat, lon)
    species_categories = build_species_categories(
        species_predictions, waterbody, county_species, citizen_observed,
        temperature.get("value_c") if temperature else None,
    )
    # build_spot_verdict only ever sees species_predictions -- for the
    # ~46% of spots with no waterbody match, that leaves it saying "No
    # species data" even when the dashboard above (WDNR category list,
    # county fallback, or a real citizen sighting) has real entries.
    # Recompute the headline from that fuller picture rather than let the
    # page contradict itself one section down.
    if verdict["headline"] == "No species data for this spot":
        _apply_categories_to_verdict(verdict, species_categories)

    return {
        "point": point,
        "temperature": temperature,
        "verdict": verdict,
        "waterbody": waterbody,
        "species_predictions": species_predictions,
        "county_species": county_species,
        "activity_window": activity_window,
        "diel_species": diel_species,
        "stocking": stocking,
        "wdnr_species": wdnr_species,
        "citizen_observed": citizen_observed,
        "species_categories": species_categories,
    }
