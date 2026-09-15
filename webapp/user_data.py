#!/usr/bin/env python3
"""
User-generated data: accounts, catches, feedback, login attempts.

This is a SEPARATE SQLite database from data/v1/v1_full_run_results.db,
and that separation is deliberate, not incidental. The content database
is committed to git and gets wholesale-overwritten by
.github/workflows/refresh-temperatures.yml roughly every 4 hours, which
then triggers a fresh Render redeploy from that git checkout. Anything
written here that instead lived in the content database -- an account, a
logged catch, a feedback message -- would be silently destroyed on that
same schedule the moment a redeploy replaced the container's local disk.

IMPORTANT -- this problem is not solved by using a separate file alone.
Render's free tier (this project's current deploy target -- see
render.yaml, DEPLOY.md) has no persistent disk by default. Until one is
attached and FISHIN_USER_DB_PATH points at its mount path, this database
still lives only on the current container's local disk and is destroyed
on every redeploy. Do not treat real signups as durable in production
until that disk exists. See DEPLOY.md's "Before enabling real user
accounts" section.
"""

import datetime
import os
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

REPO_ROOT = Path(__file__).parent.parent


class EmailAlreadyRegistered(ValueError):
    pass


def db_path() -> Path:
    raw = os.environ.get("FISHIN_USER_DB_PATH", "data/v1/user_data.db")
    p = Path(raw)
    return p if p.is_absolute() else REPO_ROOT / p


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            species TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            spot_name TEXT,
            caught_at TEXT NOT NULL,
            notes TEXT,
            kept_or_released TEXT NOT NULL CHECK (kept_or_released IN ('kept', 'released', 'unknown')),
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_catches_user ON catches(user_id);
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            attempted_at TEXT NOT NULL,
            success INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, attempted_at);
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_path TEXT,
            message TEXT NOT NULL,
            contact TEXT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            submitted_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

def create_feedback(conn, *, page_path, message, contact, user_id) -> int:
    cur = conn.execute(
        "INSERT INTO feedback (page_path, message, contact, user_id, submitted_at) VALUES (?, ?, ?, ?, ?)",
        (page_path, message, contact, user_id, _now()),
    )
    conn.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def create_user(conn, *, email: str, password: str) -> int:
    email = email.strip().lower()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise EmailAlreadyRegistered(email)
    cur = conn.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, generate_password_hash(password), _now()),
    )
    conn.commit()
    return cur.lastrowid


def get_user_by_email(conn, email: str):
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None


def get_user_by_id(conn, user_id: int):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def verify_password(user: dict, password: str) -> bool:
    return check_password_hash(user["password_hash"], password)


def record_login_attempt(conn, *, email: str, success: bool) -> None:
    conn.execute(
        "INSERT INTO login_attempts (email, attempted_at, success) VALUES (?, ?, ?)",
        (email.strip().lower(), _now(), int(success)),
    )
    conn.commit()


def recent_failed_login_count(conn, *, email: str, window_minutes: int) -> int:
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE email = ? AND success = 0 AND attempted_at >= ?",
        (email.strip().lower(), cutoff),
    ).fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Catches
# ---------------------------------------------------------------------------

def create_catch(conn, *, user_id, species, lat, lon, spot_name, caught_at, notes, kept_or_released) -> int:
    cur = conn.execute(
        """INSERT INTO catches (user_id, species, lat, lon, spot_name, caught_at, notes,
               kept_or_released, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, species, lat, lon, spot_name, caught_at, notes, kept_or_released, _now()),
    )
    conn.commit()
    return cur.lastrowid


def list_catches_for_user(conn, user_id):
    rows = conn.execute(
        "SELECT * FROM catches WHERE user_id = ? ORDER BY caught_at DESC, id DESC", (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def delete_catch(conn, *, catch_id, user_id) -> bool:
    """Returns False (no-op) if the catch doesn't exist or isn't owned by
    this user -- never lets one user delete another's row."""
    cur = conn.execute("DELETE FROM catches WHERE id = ? AND user_id = ?", (catch_id, user_id))
    conn.commit()
    return cur.rowcount > 0
