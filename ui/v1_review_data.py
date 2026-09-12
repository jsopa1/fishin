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
from pathlib import Path

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
    limit: int = 5000,
) -> list:
    """Real, current access-point rows for the map -- every field exactly
    as stored, including a null matched_waterbody_name/county when this
    point couldn't be confidently linked to a known V1 waterbody entry."""
    clauses = []
    params = []
    if county:
        clauses.append("county LIKE ? ESCAPE '\\'")
        params.append(_like_pattern(county))
    if source_type and source_type != "all":
        clauses.append("source_type = ?")
        params.append(source_type)
    if waterbody:
        clauses.append("(waterbody_name LIKE ? ESCAPE '\\' OR matched_waterbody_name LIKE ? ESCAPE '\\')")
        params.append(_like_pattern(waterbody))
        params.append(_like_pattern(waterbody))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM access_points {where} ORDER BY waterbody_name, county LIMIT ?"
    params.append(limit)
    try:
        return [dict(row) for row in conn.execute(query, params)]
    except sqlite3.OperationalError:
        return []


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
