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

import sys
from pathlib import Path

from flask import Flask, render_template, request

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "ui"))
import v1_review_data as data  # noqa: E402

STALE_HOURS = 24

app = Flask(__name__)


def get_conn():
    """A fresh connection per request -- simplest safe pattern for a
    small, read-only SQLite file under Flask's threaded dev/prod server."""
    db_path = data.find_db_path(start=REPO_ROOT)
    if db_path is None:
        return None
    return data.connect(db_path)


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
    return render_template("home.html")


@app.route("/browse")
def browse():
    conn = get_conn()
    if conn is None:
        return render_template("browse.html", results=[], species_list=[], tier_choices=data.TIER_CHOICES, filters={})

    filters = {
        "name": request.args.get("name", "").strip() or None,
        "county": request.args.get("county", "").strip() or None,
        "species": request.args.get("species", "").strip() or None,
        "tier": request.args.get("tier", "all"),
    }
    results = data.search_waterbodies(
        conn, name=filters["name"], county=filters["county"], species=filters["species"], tier=filters["tier"]
    )
    species_list = data.list_distinct_species(conn)
    conn.close()
    return render_template(
        "browse.html", results=results, species_list=species_list, tier_choices=data.TIER_CHOICES, filters=filters
    )


@app.route("/waterbody")
def waterbody_detail():
    name = request.args.get("name", "")
    county = request.args.get("county", "")
    conn = get_conn()
    if conn is None:
        return render_template("waterbody_detail.html", wb=None, species_predictions=[]), 404

    detail = data.get_waterbody_detail(conn, name, county)
    conn.close()
    if detail is None:
        return render_template("waterbody_detail.html", wb=None, species_predictions=[]), 404
    return render_template("waterbody_detail.html", wb=detail["waterbody"], species_predictions=detail["species_predictions"])


@app.route("/failures")
def failures():
    conn = get_conn()
    if conn is None:
        return render_template("failures.html", results=[], failure_types=["all"], filters={})

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
    return render_template("failures.html", results=results, failure_types=failure_types, filters=filters)


@app.route("/summary")
def summary():
    conn = get_conn()
    if conn is None:
        return render_template("summary.html", counts={
            "total_waterbodies": 0, "total_species_predictions": 0, "total_failures": 0,
            "by_tier": {}, "by_type": {}, "by_temp_method": {}, "by_failure_type": {}, "species_any_match": {},
        })
    counts = data.get_summary_counts(conn)
    conn.close()
    return render_template("summary.html", counts=counts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
