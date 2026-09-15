#!/usr/bin/env python3
"""
Minimal CSRF protection and a login-required decorator.

No Flask-WTF dependency added -- this project's webapp/requirements.txt
is deliberately two lines (flask, gunicorn), and a one-token-per-session
scheme is enough for this app's threat model (same-site forms, nothing
embedded cross-origin). Rotating the token per-submission would need
extra plumbing for multi-tab use and isn't justified here.
"""

import secrets
from functools import wraps

from flask import redirect, render_template, request, session, url_for


def get_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_protect(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method == "POST":
            submitted = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not secrets.compare_digest(submitted, expected):
                return render_template(
                    "error.html", code=400,
                    message="Your form session expired. Please reload the page and try again.",
                ), 400
        return view(*args, **kwargs)
    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("accounts.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
