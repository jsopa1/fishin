#!/usr/bin/env python3
"""
User-generated data: feedback messages and anonymous analytics events.

This is a SEPARATE SQLite database from data/v1/v1_full_run_results.db,
and that separation is deliberate, not incidental. The content database
is committed to git and gets wholesale-overwritten by
.github/workflows/refresh-temperatures.yml roughly every 4 hours, which
then triggers a fresh Render redeploy from that git checkout. Anything
written here that instead lived in the content database -- a feedback
message, an analytics event -- would be silently destroyed on that same
schedule the moment a redeploy replaced the container's local disk.

Note: this module previously also held accounts and a per-account catch
log (signup/login/session, a `users` table, a `catches` table). That was
removed -- no login is needed for this app, and the accompanying auth
surface (password storage, session handling, login-lockout tuning) was
complexity this product doesn't need right now. The anonymous "Save this
spot" feature (entirely client-side localStorage, see spot_detail.html)
remains the only "remembering" this app does.
"""

import datetime
import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def db_path() -> Path:
    raw = os.environ.get("FISHIN_USER_DB_PATH", "data/v1/user_data.db")
    p = Path(raw)
    return p if p.is_absolute() else REPO_ROOT / p


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_path TEXT,
            message TEXT NOT NULL,
            contact TEXT,
            submitted_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            page_path TEXT,
            referrer TEXT,
            session_id TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, occurred_at);
        CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, occurred_at);
        """
    )
    conn.commit()


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


def record_event(conn, *, event_type, page_path, referrer, session_id) -> int:
    """Deliberately takes no IP address or user-agent parameter -- there
    is nothing for a caller to accidentally pass through. Enough to
    compute pageviews, save rate, and return-within-7-days without
    identifying anyone."""
    cur = conn.execute(
        "INSERT INTO events (event_type, page_path, referrer, session_id, occurred_at) VALUES (?, ?, ?, ?, ?)",
        (event_type, page_path, referrer, session_id, _now()),
    )
    conn.commit()
    return cur.lastrowid


def create_feedback(conn, *, page_path, message, contact, user_id=None) -> int:
    # user_id kept as an accepted-but-ignored kwarg so callers written
    # before accounts were removed don't need touching; feedback has
    # never required an account.
    cur = conn.execute(
        "INSERT INTO feedback (page_path, message, contact, submitted_at) VALUES (?, ?, ?, ?)",
        (page_path, message, contact, _now()),
    )
    conn.commit()
    return cur.lastrowid
