#!/usr/bin/env python3
"""
Signup, login, and the catch/trip log. A Blueprint (no URL prefix, so
routes stay flat -- /signup, /login, /account -- consistent with the
rest of this site's URLs) rather than more routes pasted into app.py,
since this is a genuinely different concern (authenticated user data)
from every other route in this app (public, read-only).

Fully separate from the existing anonymous "Save this spot" localStorage
feature, which is untouched by this file -- see spot_detail.html and
test_saved_spots_never_leave_the_browser. An account is opt-in, and the
no-account experience stays exactly as it was.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for

import user_data as udata
from security import csrf_protect, login_required

accounts_bp = Blueprint("accounts", __name__)

FAILED_LOGIN_WINDOW_MINUTES = 15
FAILED_LOGIN_MAX_ATTEMPTS = 8


@accounts_bp.route("/signup", methods=["GET", "POST"])
@csrf_protect
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        errors = []
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if errors:
            return render_template("signup.html", errors=errors, email=email), 400

        conn = udata.connect()
        try:
            user_id = udata.create_user(conn, email=email, password=password)
        except udata.EmailAlreadyRegistered:
            conn.close()
            return render_template(
                "signup.html", errors=["An account with that email already exists."], email=email
            ), 400
        conn.close()
        session.clear()
        session["user_id"] = user_id
        return redirect(url_for("accounts.account"))
    return render_template("signup.html", errors=[], email="")


@accounts_bp.route("/login", methods=["GET", "POST"])
@csrf_protect
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        conn = udata.connect()
        if udata.recent_failed_login_count(
            conn, email=email, window_minutes=FAILED_LOGIN_WINDOW_MINUTES
        ) >= FAILED_LOGIN_MAX_ATTEMPTS:
            conn.close()
            return render_template(
                "login.html", error="Too many failed attempts. Try again in a few minutes.", email=email
            ), 429

        user = udata.get_user_by_email(conn, email)
        ok = user is not None and udata.verify_password(user, password)
        udata.record_login_attempt(conn, email=email, success=ok)
        if not ok:
            conn.close()
            return render_template("login.html", error="Incorrect email or password.", email=email), 400
        conn.close()
        session.clear()
        session["user_id"] = user["id"]
        next_url = request.args.get("next") or url_for("accounts.account")
        return redirect(next_url)
    return render_template("login.html", error=None, email="")


@accounts_bp.route("/logout", methods=["POST"])
@csrf_protect
def logout():
    session.clear()
    return redirect(url_for("home"))


@accounts_bp.route("/account", methods=["GET"])
@login_required
def account():
    conn = udata.connect()
    catches = udata.list_catches_for_user(conn, session["user_id"])
    conn.close()
    return render_template(
        "account.html", catches=catches,
        prefill_lat=request.args.get("lat", ""), prefill_lon=request.args.get("lon", ""),
        prefill_name=request.args.get("name", ""),
    )


@accounts_bp.route("/account/catches", methods=["POST"])
@login_required
@csrf_protect
def log_catch():
    form = request.form
    try:
        lat = float(form.get("lat"))
        lon = float(form.get("lon"))
    except (TypeError, ValueError):
        return render_template("error.html", code=400, message="A catch needs a valid spot location."), 400
    species = form.get("species", "").strip()
    caught_at = form.get("caught_at", "").strip()
    if not species or not caught_at:
        conn = udata.connect()
        catches = udata.list_catches_for_user(conn, session["user_id"])
        conn.close()
        return render_template(
            "account.html", catches=catches, error="Species and date are both required.",
            prefill_lat=form.get("lat", ""), prefill_lon=form.get("lon", ""),
            prefill_name=form.get("spot_name", ""),
        ), 400

    conn = udata.connect()
    udata.create_catch(
        conn, user_id=session["user_id"],
        species=species[:100],
        lat=lat, lon=lon,
        spot_name=form.get("spot_name", "").strip()[:200] or None,
        caught_at=caught_at,
        notes=form.get("notes", "").strip()[:1000] or None,
        kept_or_released=form.get("kept_or_released", "unknown"),
    )
    conn.close()
    return redirect(url_for("accounts.account"))


@accounts_bp.route("/account/catches/<int:catch_id>/delete", methods=["POST"])
@login_required
@csrf_protect
def delete_catch_route(catch_id):
    conn = udata.connect()
    udata.delete_catch(conn, catch_id=catch_id, user_id=session["user_id"])
    conn.close()
    return redirect(url_for("accounts.account"))
