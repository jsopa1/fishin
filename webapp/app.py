#!/usr/bin/env python3
"""
Hosted web version of the V1 results review tool. Same data, same
functionality, same evidentiary discipline as ui/v1_review_app.py (the
local .exe) -- this file is a thin Flask presentation layer over the
identical data-access module (ui/v1_review_data.py), reused directly
rather than reimplemented, so both surfaces stay behaviorally identical.

Reads data/v1/v1_full_run_results.db directly. Never writes to it, never
fabricates a result.
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "ui"))
import v1_review_data as data  # noqa: E402

STALE_HOURS = 24

app = Flask(__name__)


def get_conn():
    """A fresh connection per request -- simplest safe pattern for a
    small, read-only SQLite file under Flask's threaded dev/prod server.
    Returns None if the database genuinely can't be found -- callers must
    show a clear "data unavailable" message, never a silent empty page."""
    db_path = data.find_db_path(start=REPO_ROOT)
    if db_path is None:
        return None
    try:
        return data.connect(db_path)
    except Exception:  # noqa: BLE001 -- a corrupt/locked DB file is a real, if rare, possibility
        return None


def run_context():
    """Shared banner/staleness context injected into every page via the
    base template, so Part 3's freshness notice appears everywhere."""
    conn = get_conn()
    if conn is None:
        return {"run_row": None, "is_stale": True, "age_text": "unknown", "finished_at_text": "unknown", "stale_hours": STALE_HOURS}
    run_row = data.get_latest_run(conn)
    age = data.data_age(run_row)
    stale = data.is_stale(run_row, STALE_HOURS)

    if age is None:
        age_text = "unknown"
    else:
        hours = age.total_seconds() / 3600
        if hours < 1:
            age_text = f"{int(age.total_seconds() / 60)} minutes ago"
        elif hours < 48:
            age_text = f"{hours:.1f} hours ago"
        else:
            age_text = f"{hours / 24:.1f} days ago"

    finished_at_text = run_row["finished_at"] if run_row else "n/a"
    conn.close()
    return {
        "run_row": run_row,
        "is_stale": stale,
        "age_text": age_text,
        "finished_at_text": finished_at_text,
        "stale_hours": STALE_HOURS,
    }


@app.context_processor
def inject_run_context():
    return run_context()


@app.route("/")
def home():
    conn = get_conn()
    counts = data.get_summary_counts(conn) if conn is not None else None
    if conn is not None:
        conn.close()
    return render_template("home.html", counts=counts)


@app.route("/browse")
def browse():
    conn = get_conn()
    if conn is None:
        return render_template(
            "browse.html", results=[], species_list=[], tier_choices=data.TIER_CHOICES, filters={},
            data_unavailable=True,
        ), 503

    raw_tier = request.args.get("tier", "all")
    tier_note = None
    if raw_tier not in data.TIER_CHOICES:
        tier_note = f'"{raw_tier}" is not a recognized presence tier -- showing all tiers instead.'
        raw_tier = "all"

    filters = {
        "name": request.args.get("name", "").strip() or None,
        "county": request.args.get("county", "").strip() or None,
        "species": request.args.get("species", "").strip() or None,
        "tier": raw_tier,
    }
    results = data.search_waterbodies(
        conn, name=filters["name"], county=filters["county"], species=filters["species"], tier=filters["tier"]
    )
    species_list = data.list_distinct_species(conn)
    conn.close()
    return render_template(
        "browse.html", results=results, species_list=species_list, tier_choices=data.TIER_CHOICES,
        filters=filters, tier_note=tier_note, data_unavailable=False,
    )


@app.route("/waterbody")
def waterbody_detail():
    name = request.args.get("name", "")
    county = request.args.get("county", "")
    if not name or not county:
        return render_template(
            "waterbody_detail.html", wb=None, species_predictions=[],
            not_found_reason="This link is missing a waterbody name or county.",
        ), 400

    conn = get_conn()
    if conn is None:
        return render_template(
            "waterbody_detail.html", wb=None, species_predictions=[],
            not_found_reason="The results database is currently unavailable. Please try again shortly.",
        ), 503

    detail = data.get_waterbody_detail(conn, name, county)
    conn.close()
    if detail is None:
        return render_template(
            "waterbody_detail.html", wb=None, species_predictions=[],
            not_found_reason=(
                "No stored result for this waterbody/county combination. It may have been removed by a "
                "data-quality fix, or the name/county in this link doesn't exactly match a stored record."
            ),
        ), 404
    return render_template("waterbody_detail.html", wb=detail["waterbody"], species_predictions=detail["species_predictions"])


@app.route("/failures")
def failures():
    conn = get_conn()
    if conn is None:
        return render_template("failures.html", results=[], failure_types=["all"], filters={}, data_unavailable=True), 503

    filters = {
        "waterbody": request.args.get("waterbody", "").strip() or None,
        "species": request.args.get("species", "").strip() or None,
        "failure_type": request.args.get("failure_type", "all"),
    }
    results = data.search_failures(
        conn, waterbody=filters["waterbody"], species=filters["species"], failure_type=filters["failure_type"]
    )
    failure_types = ["all"] + data.list_distinct_failure_types(conn)
    conn.close()
    return render_template(
        "failures.html", results=results, failure_types=failure_types, filters=filters, data_unavailable=False
    )


@app.route("/summary")
def summary():
    conn = get_conn()
    if conn is None:
        return render_template("summary.html", counts=None, data_unavailable=True), 503
    counts = data.get_summary_counts(conn)
    conn.close()
    return render_template("summary.html", counts=counts, data_unavailable=False)


ACCESS_POINT_TYPES = (
    ("all", "All types"),
    ("boat_ramp", "Boat ramp"),
    ("boat_carry_in", "Carry-in (canoe/kayak)"),
    ("shore_fishing", "Shore fishing site"),
)


@app.route("/map")
def map_view():
    conn = get_conn()
    meta = data.get_access_points_meta(conn) if conn is not None else None
    invasive_meta = data.get_invasive_species_meta(conn) if conn is not None else None
    invasive_species_list = data.list_distinct_invasive_species(conn) if conn is not None else []
    if conn is not None:
        conn.close()
    context = dict(
        meta=meta,
        invasive_meta=invasive_meta,
        invasive_species_list=invasive_species_list,
        access_point_types=ACCESS_POINT_TYPES,
        filters={
            "county": request.args.get("county", "").strip(),
            "source_type": request.args.get("source_type", "all"),
            "waterbody": request.args.get("waterbody", "").strip(),
        },
        data_unavailable=meta is None,
    )
    if meta is None:
        return render_template("map.html", **context), 503
    return render_template("map.html", **context)


@app.route("/map/data")
def map_data():
    conn = get_conn()
    if conn is None:
        return jsonify({"points": [], "data_unavailable": True}), 503

    county = request.args.get("county", "").strip() or None
    source_type = request.args.get("source_type", "all")
    waterbody = request.args.get("waterbody", "").strip() or None

    points = data.list_access_points(conn, county=county, source_type=source_type, waterbody=waterbody)
    conn.close()
    return jsonify({
        "points": [
            {
                "source_type": p["source_type"],
                "facility_name": p["facility_name"],
                "waterbody_name": p["waterbody_name"],
                "county": p["county"],
                "municipality": p["municipality"],
                "lat": p["latitude"],
                "lon": p["longitude"],
                "ada_accessible": p["ada_accessible"],
                "ownership": p["ownership"],
                "more_info_url": p["more_info_url"],
                "matched_waterbody_name": p["matched_waterbody_name"],
                "matched_county": p["matched_county"],
            }
            for p in points
        ],
        "data_unavailable": False,
    })


@app.route("/map/invasive-species-data")
def invasive_species_data():
    conn = get_conn()
    if conn is None:
        return jsonify({"sightings": [], "data_unavailable": True}), 503

    species = request.args.get("species", "all")
    sightings = data.list_invasive_species_sightings(conn, species=species)
    conn.close()
    return jsonify({
        "sightings": [
            {
                "species_common_name": s["species_common_name"],
                "species_scientific_name": s["species_scientific_name"],
                "taxon_group": s["taxon_group"],
                "site_description": s["site_description"],
                "status": s["status"],
                "detected_date": s["detected_date"],
                "wbic": s["wbic"],
                "lat": s["latitude"],
                "lon": s["longitude"],
            }
            for s in sightings
        ],
        "data_unavailable": False,
    })


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(500)
def server_error(_error):
    # Never leak a stack trace to the user -- Flask's default non-debug
    # 500 page already avoids that, but this keeps it on-brand and gives
    # a clear, honest message instead of a bare "Internal Server Error".
    return render_template(
        "error.html", code=500,
        message="Something went wrong loading this page. This has been logged; please try again.",
    ), 500


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
