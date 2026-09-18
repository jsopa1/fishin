"""Deterministic unit tests for the targeted USGS-coverage expansion script.

Isolates v3_expand_usgs_coverage.DB_PATH to a throwaway SQLite file and
mocks every v1_conditions_biology_forecast call that would otherwise hit a
live network endpoint (find_usgs_site_matches, get_current_temperature,
get_species_presence, load_thresholds), so these tests never touch the
real database or the real internet.

Run: python -m pytest analysis/tests/test_v3_expand_usgs_coverage.py
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v3_expand_usgs_coverage as expand  # noqa: E402


def _init_db(path):
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
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
            diel_active INTEGER NOT NULL,
            non_match_explanation TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def _insert_waterbody(path, name, county, run_timestamp="2026-01-01T00:00:00Z", temp_is_real=0, temp_value_c=10.0):
    conn = sqlite3.connect(str(path))
    conn.execute(
        """INSERT INTO waterbody_results
           (run_timestamp, waterbody_name, county, waterbody_type, presence_tier,
            species_count, temp_value_c, temp_is_real, temp_method, temp_source,
            temp_observed_at, narrative_text)
           VALUES (?, ?, ?, 'river', 'stocking_only', 1, ?, ?, 'nws_air_proxy', 'NWS', NULL, 'placeholder')""",
        (run_timestamp, name, county, temp_value_c, temp_is_real),
    )
    conn.commit()
    conn.close()


class ExpandUsgsCoverageTestBase(unittest.TestCase):
    """Isolates expand.DB_PATH so no test ever reads or writes the real
    results database."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_db_path = expand.DB_PATH
        expand.DB_PATH = Path(self._tmpdir) / "test_results.db"
        _init_db(expand.DB_PATH)

    def tearDown(self):
        expand.DB_PATH = self._orig_db_path


class ProxyWaterbodiesTests(ExpandUsgsCoverageTestBase):
    def test_only_returns_the_latest_run_timestamp(self):
        _insert_waterbody(expand.DB_PATH, "Old River", "Dane", run_timestamp="2025-01-01T00:00:00Z")
        _insert_waterbody(expand.DB_PATH, "New River", "Dane", run_timestamp="2026-01-01T00:00:00Z")
        conn = sqlite3.connect(str(expand.DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = expand.proxy_waterbodies(conn)
        conn.close()
        names = {r["waterbody_name"] for r in rows}
        self.assertEqual(names, {"New River"})

    def test_excludes_waterbodies_already_backed_by_a_real_sensor(self):
        _insert_waterbody(expand.DB_PATH, "Proxy River", "Dane", temp_is_real=0)
        _insert_waterbody(expand.DB_PATH, "Real River", "Dane", temp_is_real=1)
        conn = sqlite3.connect(str(expand.DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = expand.proxy_waterbodies(conn)
        conn.close()
        names = {r["waterbody_name"] for r in rows}
        self.assertEqual(names, {"Proxy River"})


class FindCandidatesTests(ExpandUsgsCoverageTestBase):
    def test_only_includes_waterbodies_with_a_plausible_usgs_name_match(self):
        _insert_waterbody(expand.DB_PATH, "Matches Site River", "Dane")
        _insert_waterbody(expand.DB_PATH, "No Match Creek", "Dane")
        conn = sqlite3.connect(str(expand.DB_PATH))
        conn.row_factory = sqlite3.Row

        def fake_matches(name):
            return [{"site_no": "999"}] if name == "Matches Site River" else []

        with mock.patch.object(expand.v1, "find_usgs_site_matches", side_effect=fake_matches):
            candidates = expand.find_candidates(conn)
        conn.close()
        names = {c["waterbody_name"] for c in candidates}
        self.assertEqual(names, {"Matches Site River"})


class RefreshTests(ExpandUsgsCoverageTestBase):
    def _patch_common(self, temp_info):
        return [
            mock.patch.object(expand.v1, "find_usgs_site_matches", return_value=[{"site_no": "999"}]),
            mock.patch.object(expand.v1, "get_current_temperature", return_value=temp_info),
            mock.patch.object(expand.v1, "load_thresholds", return_value={}),
            mock.patch.object(expand.time, "sleep", return_value=None),
        ]

    def test_dry_run_reports_the_upgrade_but_writes_nothing(self):
        _insert_waterbody(expand.DB_PATH, "Wolf River", "Langlade", temp_value_c=None, temp_is_real=0)
        temp_info = {
            "value_c": 17.5, "is_real_water_measurement": True,
            "method": "usgs_live", "source": "USGS live gauge 04079000", "observed_at": "2026-01-01T00:00:00Z",
        }
        patches = self._patch_common(temp_info)
        for p in patches:
            p.start()
        try:
            result = expand.refresh(dry_run=True)
        finally:
            for p in patches:
                p.stop()
        self.assertEqual(result, 0)

        conn = sqlite3.connect(str(expand.DB_PATH))
        row = conn.execute("SELECT temp_is_real FROM waterbody_results WHERE waterbody_name='Wolf River'").fetchone()
        conn.close()
        self.assertEqual(row[0], 0, "dry run must never write to the database")

    def test_real_run_upgrades_a_matched_proxy_waterbody_to_real(self):
        _insert_waterbody(expand.DB_PATH, "Kewaunee River", "Kewaunee", temp_value_c=None, temp_is_real=0)
        temp_info = {
            "value_c": 15.4, "is_real_water_measurement": True,
            "method": "usgs_live", "source": "USGS live gauge 04085200", "observed_at": "2026-01-01T00:00:00Z",
        }
        patches = self._patch_common(temp_info)
        for p in patches:
            p.start()
        try:
            with mock.patch.object(expand.v1, "get_species_presence",
                                    return_value={"tier": "no_data", "species": [], "detail": {}, "waterbody_type": "river"}):
                result = expand.refresh(dry_run=False)
        finally:
            for p in patches:
                p.stop()
        self.assertEqual(result, 0)

        conn = sqlite3.connect(str(expand.DB_PATH))
        row = conn.execute(
            "SELECT temp_is_real, temp_value_c, temp_method FROM waterbody_results WHERE waterbody_name='Kewaunee River'"
        ).fetchone()
        conn.close()
        self.assertEqual(row[0], 1)
        self.assertAlmostEqual(row[1], 15.4)
        self.assertEqual(row[2], "usgs_live")

    def test_a_sensor_returning_a_proxy_reading_is_not_upgraded(self):
        _insert_waterbody(expand.DB_PATH, "Quiet Creek", "Dane", temp_value_c=8.0, temp_is_real=0)
        temp_info = {
            "value_c": 8.0, "is_real_water_measurement": False,
            "method": "nws_air_proxy", "source": "NWS", "observed_at": None,
        }
        patches = self._patch_common(temp_info)
        for p in patches:
            p.start()
        try:
            result = expand.refresh(dry_run=False)
        finally:
            for p in patches:
                p.stop()
        self.assertEqual(result, 0)

        conn = sqlite3.connect(str(expand.DB_PATH))
        row = conn.execute("SELECT temp_is_real FROM waterbody_results WHERE waterbody_name='Quiet Creek'").fetchone()
        conn.close()
        self.assertEqual(row[0], 0)

    def test_an_implausible_reading_is_skipped_not_written(self):
        _insert_waterbody(expand.DB_PATH, "Odd River", "Dane", temp_value_c=8.0, temp_is_real=0)
        temp_info = {
            "value_c": 999.0, "is_real_water_measurement": True,
            "method": "usgs_live", "source": "USGS live gauge 000", "observed_at": "2026-01-01T00:00:00Z",
        }
        patches = self._patch_common(temp_info)
        for p in patches:
            p.start()
        try:
            result = expand.refresh(dry_run=False)
        finally:
            for p in patches:
                p.stop()
        self.assertEqual(result, 0)

        conn = sqlite3.connect(str(expand.DB_PATH))
        row = conn.execute("SELECT temp_is_real, temp_value_c FROM waterbody_results WHERE waterbody_name='Odd River'").fetchone()
        conn.close()
        self.assertEqual(row[0], 0)
        self.assertAlmostEqual(row[1], 8.0)

    def test_a_network_error_on_one_waterbody_does_not_halt_the_run(self):
        _insert_waterbody(expand.DB_PATH, "Flaky River", "Dane", temp_is_real=0)
        _insert_waterbody(expand.DB_PATH, "Fine River", "Dane", temp_value_c=None, temp_is_real=0)

        import urllib.error

        def fake_get_current_temperature(name, county, live_refresh=True):
            if name == "Flaky River":
                raise urllib.error.URLError("boom")
            return {
                "value_c": 12.0, "is_real_water_measurement": True,
                "method": "usgs_live", "source": "USGS live gauge 111", "observed_at": "2026-01-01T00:00:00Z",
            }

        with mock.patch.object(expand.v1, "find_usgs_site_matches", return_value=[{"site_no": "999"}]), \
             mock.patch.object(expand.v1, "get_current_temperature", side_effect=fake_get_current_temperature), \
             mock.patch.object(expand.v1, "load_thresholds", return_value={}), \
             mock.patch.object(expand.v1, "get_species_presence",
                                return_value={"tier": "no_data", "species": [], "detail": {}, "waterbody_type": "river"}), \
             mock.patch.object(expand.time, "sleep", return_value=None):
            result = expand.refresh(dry_run=False)

        self.assertEqual(result, 0)
        conn = sqlite3.connect(str(expand.DB_PATH))
        rows = {r[0]: r[1] for r in conn.execute(
            "SELECT waterbody_name, temp_is_real FROM waterbody_results"
        )}
        conn.close()
        self.assertEqual(rows["Flaky River"], 0, "the failing lookup must not crash the run or write bad data")
        self.assertEqual(rows["Fine River"], 1, "a later waterbody must still be processed after an earlier failure")


if __name__ == "__main__":
    unittest.main()
