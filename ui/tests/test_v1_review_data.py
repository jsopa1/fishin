"""Deterministic unit tests for the V1 review UI's data-access layer
(ui/v1_review_data.py). Confirms the data-loading and filtering logic
reads and filters correctly against a real-schema SQLite fixture -- not
the real database, and not the GUI (per this cycle's Part 5, UI widgets
are not unit-tested here, only the underlying data logic).

Run: python -m pytest ui/tests/test_v1_review_data.py
"""

import datetime
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "analysis"))

import v1_review_data as rd  # noqa: E402

# Mirrors the real schema created by analysis/v1_full_run.py's init_db(),
# kept in sync manually since this module intentionally has no dependency
# on the batch script (the UI must be able to read a DB produced by any
# past run, not just today's).
SCHEMA = """
CREATE TABLE runs (
    run_timestamp TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total_waterbodies INTEGER,
    total_species_predictions INTEGER,
    total_failures INTEGER,
    live_refresh INTEGER NOT NULL
);
CREATE TABLE waterbody_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    waterbody_name TEXT NOT NULL,
    county TEXT NOT NULL,
    waterbody_type TEXT NOT NULL,
    presence_tier TEXT NOT NULL,
    species_count INTEGER NOT NULL,
    temp_value_c REAL,
    temp_is_real INTEGER NOT NULL,
    temp_method TEXT,
    temp_source TEXT,
    temp_observed_at TEXT,
    narrative_text TEXT NOT NULL
);
CREATE TABLE species_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    waterbody_name TEXT NOT NULL,
    county TEXT NOT NULL,
    species TEXT NOT NULL,
    has_threshold_data INTEGER NOT NULL,
    any_match INTEGER NOT NULL,
    match_description TEXT,
    evidence_quality TEXT,
    river_caveat_applied INTEGER NOT NULL,
    diel_active INTEGER NOT NULL
);
CREATE TABLE run_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    waterbody_name TEXT NOT NULL,
    county TEXT NOT NULL,
    species TEXT,
    failure_type TEXT NOT NULL,
    error_message TEXT NOT NULL
);
"""


class DataTestBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.db_path = Path(self._tmpdir) / "test.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _insert_run(self, run_timestamp="2026-09-09T12:00:00+00:00", finished_at="2026-09-09T12:05:00+00:00"):
        self.conn.execute(
            "INSERT INTO runs (run_timestamp, started_at, finished_at, total_waterbodies, "
            "total_species_predictions, total_failures, live_refresh) VALUES (?, ?, ?, 1, 1, 0, 1)",
            (run_timestamp, run_timestamp, finished_at),
        )
        self.conn.commit()

    def _insert_waterbody(
        self, name, county, wtype="lake", tier="survey_confirmed", species_count=1,
        temp_value_c=20.0, temp_is_real=1, temp_method="clmn_recent", narrative="test narrative",
        run_timestamp="2026-09-09T12:00:00+00:00",
    ):
        self.conn.execute(
            """INSERT INTO waterbody_results
               (run_timestamp, waterbody_name, county, waterbody_type, presence_tier, species_count,
                temp_value_c, temp_is_real, temp_method, temp_source, temp_observed_at, narrative_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'test source', 'test observed', ?)""",
            (run_timestamp, name, county, wtype, tier, species_count, temp_value_c, temp_is_real, temp_method, narrative),
        )
        self.conn.commit()

    def _insert_species_prediction(
        self, name, county, species, any_match=1, match_description="test match",
        river_caveat_applied=0, run_timestamp="2026-09-09T12:00:00+00:00",
    ):
        self.conn.execute(
            """INSERT INTO species_predictions
               (run_timestamp, waterbody_name, county, species, has_threshold_data, any_match,
                match_description, evidence_quality, river_caveat_applied, diel_active)
               VALUES (?, ?, ?, ?, 1, ?, ?, 'test-tier', ?, 0)""",
            (run_timestamp, name, county, species, any_match, match_description, river_caveat_applied),
        )
        self.conn.commit()

    def _insert_failure(self, name, county, species, failure_type, message, run_timestamp="2026-09-09T12:00:00+00:00"):
        self.conn.execute(
            "INSERT INTO run_failures (run_timestamp, waterbody_name, county, species, failure_type, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_timestamp, name, county, species, failure_type, message),
        )
        self.conn.commit()


class TestFindDbPath(unittest.TestCase):
    def test_finds_db_in_ancestor_directory(self):
        tmpdir = tempfile.mkdtemp()
        root = Path(tmpdir)
        (root / "data" / "v1").mkdir(parents=True)
        (root / "data" / "v1" / "v1_full_run_results.db").write_text("fake db")
        nested = root / "some" / "nested" / "dir"
        nested.mkdir(parents=True)
        found = rd.find_db_path(start=nested)
        self.assertEqual(found, root / "data" / "v1" / "v1_full_run_results.db")

    def test_returns_none_when_not_found(self):
        tmpdir = tempfile.mkdtemp()
        found = rd.find_db_path(start=Path(tmpdir))
        self.assertIsNone(found)


class TestStaleness(unittest.TestCase):
    def test_no_run_is_stale(self):
        self.assertTrue(rd.is_stale(None))

    def test_run_with_no_finished_at_is_stale(self):
        self.assertTrue(rd.is_stale({"finished_at": None}))

    def test_recent_run_is_not_stale(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        finished = (now - datetime.timedelta(hours=1)).isoformat()
        self.assertFalse(rd.is_stale({"finished_at": finished}, max_age_hours=24, now=now))

    def test_old_run_is_stale(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        finished = (now - datetime.timedelta(hours=25)).isoformat()
        self.assertTrue(rd.is_stale({"finished_at": finished}, max_age_hours=24, now=now))

    def test_exactly_at_boundary_is_not_stale(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        finished = (now - datetime.timedelta(hours=24)).isoformat()
        self.assertFalse(rd.is_stale({"finished_at": finished}, max_age_hours=24, now=now))

    def test_data_age_none_when_no_run(self):
        self.assertIsNone(rd.data_age(None))

    def test_data_age_real_timedelta(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        finished = (now - datetime.timedelta(hours=3)).isoformat()
        age = rd.data_age({"finished_at": finished}, now=now)
        self.assertAlmostEqual(age.total_seconds(), 3 * 3600, delta=1)


class TestSummaryCounts(DataTestBase):
    def test_counts_match_inserted_rows(self):
        self._insert_run()
        self._insert_waterbody("Lake A", "County1", wtype="lake", tier="survey_confirmed")
        self._insert_waterbody("Creek B", "County1", wtype="stream", tier="stocking_only")
        self._insert_species_prediction("Lake A", "County1", "WALLEYE", any_match=1)
        self._insert_species_prediction("Creek B", "County1", "MUSKELLUNGE", any_match=0)
        self._insert_failure("Lake A", "County1", "CARP", "no_physiology_threshold", "no data")

        counts = rd.get_summary_counts(self.conn)
        self.assertEqual(counts["total_waterbodies"], 2)
        self.assertEqual(counts["total_species_predictions"], 2)
        self.assertEqual(counts["total_failures"], 1)
        self.assertEqual(counts["by_tier"], {"survey_confirmed": 1, "stocking_only": 1})
        self.assertEqual(counts["by_type"], {"lake": 1, "stream": 1})
        self.assertEqual(counts["species_any_match"], {0: 1, 1: 1})


class TestSearchWaterbodies(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()
        self._insert_waterbody("Devils Lake", "Sauk", wtype="lake", tier="survey_confirmed")
        self._insert_waterbody("Devils Lake", "Burnett", wtype="lake", tier="stocking_only")
        self._insert_waterbody("Fox River", "Winnebago", wtype="stream", tier="stocking_only")
        self._insert_species_prediction("Devils Lake", "Sauk", "WALLEYE")
        self._insert_species_prediction("Fox River", "Winnebago", "MUSKELLUNGE")

    def test_filter_by_name_substring(self):
        results = rd.search_waterbodies(self.conn, name="Devils")
        names = {(r["waterbody_name"], r["county"]) for r in results}
        self.assertEqual(names, {("Devils Lake", "Sauk"), ("Devils Lake", "Burnett")})

    def test_filter_by_county(self):
        results = rd.search_waterbodies(self.conn, county="Sauk")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["waterbody_name"], "Devils Lake")

    def test_filter_by_tier(self):
        results = rd.search_waterbodies(self.conn, tier="survey_confirmed")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["county"], "Sauk")

    def test_filter_by_species(self):
        results = rd.search_waterbodies(self.conn, species="MUSKELLUNGE")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["waterbody_name"], "Fox River")

    def test_no_filters_returns_all(self):
        results = rd.search_waterbodies(self.conn)
        self.assertEqual(len(results), 3)

    def test_combined_filters(self):
        results = rd.search_waterbodies(self.conn, name="Devils", tier="stocking_only")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["county"], "Burnett")

    def test_no_match_returns_empty_list_not_error(self):
        results = rd.search_waterbodies(self.conn, name="Nonexistent Lake XYZ")
        self.assertEqual(results, [])

    def test_percent_sign_in_query_treated_as_literal_not_wildcard(self):
        # Real bug found during polish testing: an unescaped "%" in user
        # input is a SQL LIKE wildcard, so a real waterbody named e.g.
        # "50% Slough" would match against ANY name once naively wrapped
        # in %...% -- and, worse, searching for a literal "%" that isn't
        # actually in any name should find nothing, not everything.
        self._insert_waterbody("50% Slough", "TestCounty")
        results = rd.search_waterbodies(self.conn, name="50%")
        self.assertEqual([r["waterbody_name"] for r in results], ["50% Slough"])
        # A literal percent sign with no real match must return nothing,
        # not silently match every row via wildcard reinterpretation.
        no_match = rd.search_waterbodies(self.conn, name="99%")
        self.assertEqual(no_match, [])

    def test_underscore_in_query_treated_as_literal_not_single_char_wildcard(self):
        self._insert_waterbody("Big_Lake", "TestCounty")
        self._insert_waterbody("BigXLake", "TestCounty")  # would match "Big_Lake" if _ were a wildcard
        results = rd.search_waterbodies(self.conn, name="Big_Lake")
        self.assertEqual([r["waterbody_name"] for r in results], ["Big_Lake"])


class TestWaterbodyDetail(DataTestBase):
    def test_detail_includes_full_narrative_and_species(self):
        self._insert_run()
        self._insert_waterbody(
            "Big Moon Lake", "Barron", narrative="=== full text with DISPUTED caveat intact ==="
        )
        self._insert_species_prediction(
            "Big Moon Lake", "Barron", "MUSKELLUNGE",
            match_description="DISPUTED: two sources disagree, range spans both",
            river_caveat_applied=0,
        )
        detail = rd.get_waterbody_detail(self.conn, "Big Moon Lake", "Barron")
        self.assertIsNotNone(detail)
        self.assertIn("DISPUTED", detail["waterbody"]["narrative_text"])
        self.assertEqual(len(detail["species_predictions"]), 1)
        self.assertIn("DISPUTED", detail["species_predictions"][0]["match_description"])

    def test_detail_none_for_unknown_waterbody(self):
        self._insert_run()
        detail = rd.get_waterbody_detail(self.conn, "Nowhere", "Nowhere")
        self.assertIsNone(detail)

    def test_detail_requires_exact_name_and_county(self):
        self._insert_run()
        self._insert_waterbody("Devils Lake", "Sauk County")
        # A fuzzy/partial county ("Sauk" vs "Sauk County") does NOT match --
        # get_waterbody_detail is meant to be called with the exact values
        # from a selected search-result row, not a free-text query.
        self.assertIsNone(rd.get_waterbody_detail(self.conn, "Devils Lake", "Sauk"))
        self.assertIsNotNone(rd.get_waterbody_detail(self.conn, "Devils Lake", "Sauk County"))


class TestSearchFailures(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()
        self._insert_failure("Lake A", "County1", "CARP", "no_physiology_threshold", "no threshold data")
        self._insert_failure("Lake B", "County2", None, "temperature_lookup_error", "timeout")

    def test_filter_by_failure_type(self):
        results = rd.search_failures(self.conn, failure_type="temperature_lookup_error")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["waterbody_name"], "Lake B")

    def test_filter_by_waterbody(self):
        results = rd.search_failures(self.conn, waterbody="Lake A")
        self.assertEqual(len(results), 1)

    def test_all_returns_everything(self):
        results = rd.search_failures(self.conn, failure_type="all")
        self.assertEqual(len(results), 2)

    def test_species_none_preserved_not_fabricated(self):
        results = rd.search_failures(self.conn, waterbody="Lake B")
        self.assertIsNone(results[0]["species"])


if __name__ == "__main__":
    unittest.main()
