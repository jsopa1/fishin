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

import json
import os
import secrets
import sys
import zoneinfo
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, session, url_for

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "ui"))
sys.path.insert(0, str(REPO_ROOT / "analysis"))
import v1_review_data as data  # noqa: E402
import v2_fishing_regulations as fishing_regulations  # noqa: E402
import v3_current_conditions as current_conditions  # noqa: E402
import v3_moon_phase as moon_phase  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import user_data as udata  # noqa: E402
from security import csrf_protect, get_csrf_token  # noqa: E402

# Water temperature is the only thing here that ages in hours. Six hours
# is roughly how long a real reading stays representative in open water --
# and it is reachable, since refresh_temperatures.py takes minutes.
TEMPERATURE_STALE_HOURS = 6

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # templates are cheap to re-check per request; keeps local dev iteration fast without needing debug mode

app.secret_key = os.environ.get("FISHIN_SECRET_KEY", "dev-only-insecure-secret-key-change-me")
if app.secret_key == "dev-only-insecure-secret-key-change-me" and not app.testing:
    print(
        "WARNING: FISHIN_SECRET_KEY not set -- using an insecure development "
        "fallback. Set FISHIN_SECRET_KEY before any real user data exists.",
        file=sys.stderr,
    )
app.context_processor(lambda: {"csrf_token": get_csrf_token})

# ---------------------------------------------------------------------------
# Minimal, self-hosted analytics. No third-party service (none is signed
# up for on anyone's behalf), no tracking cookie beyond the same signed
# session cookie already used for CSRF, and never an IP address or
# user-agent string -- see user_data.record_event()'s own guard. Enough
# to compute the three numbers that actually matter for retention: spot
# pages per visit, save rate, and return within 7 days.
# ---------------------------------------------------------------------------
EXCLUDED_PAGEVIEW_PATHS = {"/healthz", "/manifest.json", "/robots.txt", "/sitemap.xml", "/events/save"}
EXCLUDED_PAGEVIEW_PREFIXES = ("/static", "/map/data", "/map/invasive-species-data")


def _analytics_session_id() -> str:
    sid = session.get("asid")
    if not sid:
        sid = secrets.token_urlsafe(16)
        session["asid"] = sid
    return sid


@app.after_request
def _log_pageview(response):
    try:
        path = request.path
        if (
            request.method == "GET" and response.status_code < 400
            and path not in EXCLUDED_PAGEVIEW_PATHS
            and not path.startswith(EXCLUDED_PAGEVIEW_PREFIXES)
        ):
            conn = udata.connect()
            udata.record_event(
                conn, event_type="pageview", page_path=path,
                referrer=request.referrer, session_id=_analytics_session_id(),
            )
            conn.close()
    except Exception:  # noqa: BLE001 -- analytics must never break a page
        pass
    return response


@app.route("/events/save", methods=["POST"])
def log_save_event():
    # A fire-and-forget navigator.sendBeacon ping, not a form post -- kept
    # outside CSRF protection since it changes nothing about the user's
    # own data (the actual save stays localStorage-only, see spot_detail.html),
    # it only increments an anonymous counter.
    try:
        conn = udata.connect()
        udata.record_event(
            conn, event_type="save", page_path=(request.form.get("page") or request.path)[:200],
            referrer=None, session_id=_analytics_session_id(),
        )
        conn.close()
    except Exception:  # noqa: BLE001
        pass
    return ("", 204)


# Wisconsin is entirely Central. Solar times are computed in UTC, and an
# angler reading "sunrise 11:37" would rightly stop trusting the page.
CENTRAL = zoneinfo.ZoneInfo("America/Chicago")


@app.template_filter("central")
def central_time(value, fmt: str = "%-I:%M %p"):
    if value is None:
        return ""
    local = value.astimezone(CENTRAL)
    try:
        return local.strftime(fmt)
    except ValueError:
        # %-I is glibc-only; Windows needs %#I.
        return local.strftime(fmt.replace("%-", "%#"))


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


def _humanise_age(age) -> str:
    if age is None:
        return "unknown"
    hours = age.total_seconds() / 3600
    if hours < 1:
        return f"{int(age.total_seconds() / 60)} minutes ago"
    if hours < 48:
        return f"{hours:.0f} hours ago"
    return f"{hours / 24:.0f} days ago"


def run_context():
    """Freshness context injected into every page.

    Temperature and species data age at completely different rates, so
    they get separate clocks. Water temperature moves in hours and is
    refreshed on its own fast schedule (analysis/refresh_temperatures.py);
    species presence and stocking records come from annual WDNR surveys
    and are not meaningfully staler at 40 hours than at 4. The old single
    banner judged both by the batch-run timestamp, so it shouted that
    everything was stale whenever the slow clock ticked over -- alarming
    on every page, and wrong about most of the data."""
    conn = get_conn()
    if conn is None:
        return {
            "run_row": None, "temp_is_stale": True, "temp_age_text": "unknown",
            "survey_age_text": "unknown", "stale_hours": TEMPERATURE_STALE_HOURS,
        }

    run_row = data.get_latest_run(conn)
    refresh_row = data.get_latest_temperature_refresh(conn)

    # Temperature freshness: the refresh clock if one has ever run,
    # otherwise fall back to the full run that last wrote temperatures.
    temp_source_row = refresh_row or run_row
    temp_age = data.data_age(temp_source_row)
    temp_is_stale = data.is_stale(temp_source_row, TEMPERATURE_STALE_HOURS)

    conn.close()
    return {
        "run_row": run_row,
        "temp_is_stale": temp_is_stale,
        "temp_age_text": _humanise_age(temp_age),
        "survey_age_text": _humanise_age(data.data_age(run_row)),
        "stale_hours": TEMPERATURE_STALE_HOURS,
    }


@app.context_processor
def inject_run_context():
    return run_context()


@app.route("/")
def home():
    conn = get_conn()
    counts = data.get_summary_counts(conn) if conn is not None else None
    meta = data.get_access_points_meta(conn) if conn is not None else None
    highlights = data.get_current_highlights(conn) if conn is not None else []
    if conn is not None:
        conn.close()
    return render_template("home.html", counts=counts, meta=meta, highlights=highlights)


@app.route("/browse")
def browse():
    conn = get_conn()
    if conn is None:
        return render_template(
            "browse.html", results=[], species_list=[], tier_choices=data.TIER_CHOICES, filters={},
            data_unavailable=True, counts=None,
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
    counts = data.get_summary_counts(conn)
    conn.close()
    return render_template(
        "browse.html", results=results, species_list=species_list, tier_choices=data.TIER_CHOICES, counts=counts,
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
    combined_species_list = data.list_combined_species(conn) if conn is not None else []
    if conn is not None:
        conn.close()
    context = dict(
        meta=meta,
        invasive_meta=invasive_meta,
        invasive_species_list=invasive_species_list,
        combined_species_list=combined_species_list,
        access_point_types=ACCESS_POINT_TYPES,
        filters={
            "county": request.args.get("county", "").strip(),
            "source_type": request.args.get("source_type", "all"),
            "waterbody": request.args.get("waterbody", "").strip(),
            "species": request.args.get("species", "").strip(),
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
    species = request.args.get("species", "").strip() or None

    points = data.list_access_points(
        conn, county=county, source_type=source_type, waterbody=waterbody, species=species
    )
    conn.close()

    # Only what the map pins and the list cards actually render. The full
    # per-site detail (directions, stalls, amenities, ADA, manager) lives
    # on the spot page, which is the real destination now -- shipping all
    # of it to every visitor made this response 2.07MB, and the bulk of
    # that was field names repeated 3,272 times for data nobody had asked
    # to see yet. That matters on cellular at a boat ramp.
    return jsonify({
        "points": [
            {
                "t": p["source_type"],
                "n": p["facility_name"],
                "w": p["waterbody_name"],
                "c": p["county"],
                "lat": p["latitude"],
                "lon": p["longitude"],
                "mw": p["matched_waterbody_name"],
                "mc": p["matched_county"],
                "sp": p.get("fish_species_raw"),
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


@app.route("/spot")
def spot_detail():
    """Phase 4 of docs/v2_fish_intelligence_platform_plan.md: the
    one-stop-shop spot view. Keyed by lat/lon (+ optional facility name
    to disambiguate the rare shared-coordinate case) rather than
    access_points.id, since that id isn't stable across a future
    re-ingestion (see docs/v2_access_points_report.md section 8) -- the
    map/list views already have the exact lat/lon for every marker they
    render, so they can link here directly with no extra lookup."""
    lat_raw = request.args.get("lat", "")
    lon_raw = request.args.get("lon", "")
    name = request.args.get("name", "").strip() or None
    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except ValueError:
        return render_template(
            "spot_detail.html", spot=None,
            not_found_reason="This link is missing a valid spot location.",
        ), 400

    conn = get_conn()
    if conn is None:
        return render_template(
            "spot_detail.html", spot=None,
            not_found_reason="The results database is currently unavailable. Please try again shortly.",
        ), 503

    detail = data.get_spot_detail(conn, lat, lon, name=name)
    # Live, cached 24h, and allowed to fail: regulations are valuable but
    # never worth a blank page if WDNR's service is slow or down.
    regulations = advisory = conditions = moon = None
    if detail is not None:
        try:
            regulations = fishing_regulations.get_regulations(conn, lat, lon)
        except Exception:  # noqa: BLE001 -- an enhancement must not break the page
            regulations = None
        try:
            advisory = fishing_regulations.get_consumption_advisory(conn, lat, lon)
        except Exception:  # noqa: BLE001
            advisory = None
        try:
            conditions = current_conditions.get_current_conditions(conn, lat, lon)
        except Exception:  # noqa: BLE001
            conditions = None
        try:
            moon = moon_phase.get_moon_phase()
        except Exception:  # noqa: BLE001
            moon = None
    conn.close()
    if detail is None:
        return render_template(
            "spot_detail.html", spot=None,
            not_found_reason="No stored access point at this location. It may have been removed by a data refresh.",
        ), 404
    return render_template(
        "spot_detail.html", spot=detail["point"], temperature=detail["temperature"],
        waterbody=detail["waterbody"], species_predictions=detail["species_predictions"],
        county_species=detail["county_species"], activity_window=detail["activity_window"],
        diel_species=detail["diel_species"], stocking=detail["stocking"],
        wdnr_species=detail["wdnr_species"], verdict=detail["verdict"],
        citizen_observed=detail["citizen_observed"],
        regulations=regulations, advisory=advisory, conditions=conditions, moon=moon,
    )


@app.route("/healthz")
def healthz():
    """Liveness plus a real readiness check. A 200 here means the process
    is up AND the database actually answers -- a process that boots but
    can't read its data is not healthy, and on a free tier that spins down
    between requests, the difference matters."""
    conn = get_conn()
    if conn is None:
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
    try:
        waterbodies = conn.execute("SELECT COUNT(*) FROM waterbody_results").fetchone()[0]
        refresh_row = data.get_latest_temperature_refresh(conn)
    except Exception:  # noqa: BLE001 -- a health check must never raise
        return jsonify({"status": "degraded", "database": "unreadable"}), 503
    finally:
        conn.close()

    return jsonify({
        "status": "ok",
        "waterbodies": waterbodies,
        "temperatures_refreshed_at": refresh_row["finished_at"] if refresh_row else None,
    })


@app.route("/robots.txt")
def robots():
    # The diagnostic pages are real and public, but they are not what
    # should surface in a search for Wisconsin fishing conditions.
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /failures\n"
        "Disallow: /summary\n"
        "Disallow: /map/data\n"
        "Disallow: /map/invasive-species-data\n"
        f"Sitemap: {url_for('sitemap', _external=True)}\n"
    )
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    """Only the pages worth indexing. Spot pages are deliberately excluded:
    there are 3,272 of them, they are keyed by coordinate, and their value
    is current conditions rather than durable content."""
    pages = [url_for(e, _external=True) for e in ("home", "map_view", "browse")]
    urls = "".join(f"<url><loc>{p}</loc><changefreq>daily</changefreq></url>" for p in pages)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, mimetype="application/xml")


@app.route("/feedback", methods=["GET", "POST"])
@csrf_protect
def feedback():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        page = request.form.get("page", "").strip()[:500] or None
        if not message:
            return render_template("feedback.html", error="Please enter a message.", page=page or ""), 400
        conn = udata.connect()
        udata.create_feedback(
            conn, page_path=page, message=message[:5000],
            contact=request.form.get("contact", "").strip()[:200] or None,
            user_id=None,
        )
        conn.close()
        return render_template("feedback.html", submitted=True)
    return render_template("feedback.html", page=request.args.get("page", ""))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/manifest.json")
def manifest():
    """At the root, not under /static, so the PWA's default scope covers
    the whole site rather than just /static/."""
    body = {
        "name": "fishin — Wisconsin Fishing Conditions",
        "short_name": "fishin",
        "description": "Live Wisconsin water temperatures checked against published fish-physiology research.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7f8fa",
        "theme_color": "#2456d6",
        "icons": [
            {"src": url_for("static", filename="icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": url_for("static", filename="icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": url_for("static", filename="icons/icon-192-maskable.png"), "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": url_for("static", filename="icons/icon-512-maskable.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return Response(json.dumps(body), mimetype="application/manifest+json")


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
