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
    return {
        "waterbody": dict(wb_row),
        "species_predictions": [dict(r) for r in species_rows],
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


def estimate_temperature_from_nearby(
    conn: sqlite3.Connection, lat: float, lon: float, max_km: float = 15.0, max_anchors: int = 5
):
    """Inverse-distance-weighted estimate from real anchor readings
    only (build_temperature_anchors) within max_km. Returns None when no
    real anchor is close enough -- an honest absence, never a fabricated
    guess with nothing behind it. Never uses a proxy reading as an
    anchor: a proxy is already an estimate, and re-estimating from an
    estimate would compound uncertainty invisibly.

    Returns {"value_c", "anchor_count", "nearest_km", "anchors":
    [{"waterbody_name", "county", "distance_km"}, ...]} on success.
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

    return {
        "value_c": value_c,
        "anchor_count": len(nearby),
        "nearest_km": nearby[0][0],
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

    return {
        "point": point,
        "temperature": temperature,
        "waterbody": waterbody,
        "species_predictions": species_predictions,
    }
