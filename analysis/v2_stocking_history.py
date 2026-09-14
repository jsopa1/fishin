#!/usr/bin/env python3
"""
Ingest the real WDNR stocking records into a queryable table.

This project has held 24,683 stocking records (2011-2025) since V1, but
has only ever used them as a yes/no presence signal: "walleye appear in
the stocking list for this water, so treat walleye as present." Every
other column was discarded.

That is a waste of the single most concrete thing WDNR publishes about a
water. "16,466 brown trout yearlings averaging 9 inches, stocked 2025"
tells an angler what is actually swimming there and roughly how big --
which is exactly the kind of thing the DNR's own Fishing Finder surfaces
and this app did not.

Nothing here re-derives or reinterprets the records. It loads them as
published, keyed for lookup by waterbody.

Usage:
    python analysis/v2_stocking_history.py
"""

import csv
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
STOCKING_CSV = REPO / "data" / "v1" / "wi_stocking_statewide_2011_2025.csv"
DB_PATH = REPO / "data" / "v1" / "v1_full_run_results.db"


def init_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS stocking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waterbody TEXT NOT NULL,
            county TEXT NOT NULL,
            stocking_year INTEGER NOT NULL,
            species TEXT NOT NULL,
            strain TEXT,
            age_class TEXT,
            number_stocked INTEGER,
            avg_length_in REAL,
            source_type TEXT NOT NULL,
            source_url TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_stocking_waterbody
            ON stocking_history(waterbody, county);
        CREATE INDEX IF NOT EXISTS idx_stocking_year
            ON stocking_history(stocking_year);
        """
    )
    conn.commit()


def _int_or_none(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ingest(conn: sqlite3.Connection) -> int:
    with open(STOCKING_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    conn.execute("DELETE FROM stocking_history")
    conn.executemany(
        """INSERT INTO stocking_history
           (waterbody, county, stocking_year, species, strain, age_class,
            number_stocked, avg_length_in, source_type, source_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                (r.get("waterbody") or "").strip(),
                (r.get("county") or "").strip(),
                _int_or_none(r.get("stocking_year")) or 0,
                (r.get("species") or "").strip(),
                (r.get("strain") or "").strip() or None,
                (r.get("age_class") or "").strip() or None,
                _int_or_none(r.get("number_stocked")),
                _float_or_none(r.get("avg_length_in")),
                (r.get("source_type") or "").strip(),
                (r.get("source_url") or "").strip() or None,
            )
            for r in rows
            if (r.get("waterbody") or "").strip()
        ],
    )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM stocking_history").fetchone()[0]


def main() -> int:
    if not STOCKING_CSV.exists():
        print(f"Stocking CSV not found: {STOCKING_CSV}", file=sys.stderr)
        return 1
    conn = sqlite3.connect(str(DB_PATH))
    init_table(conn)
    total = ingest(conn)

    years = conn.execute(
        "SELECT MIN(stocking_year), MAX(stocking_year) FROM stocking_history WHERE stocking_year > 0"
    ).fetchone()
    waters = conn.execute(
        "SELECT COUNT(DISTINCT waterbody || '|' || county) FROM stocking_history"
    ).fetchone()[0]
    conn.close()

    print(f"Ingested {total:,} stocking records")
    print(f"  {waters:,} distinct waterbodies, years {years[0]}-{years[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
