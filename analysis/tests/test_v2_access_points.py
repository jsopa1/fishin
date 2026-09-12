"""Deterministic unit tests for the V2 access-point ingestion script.

Covers the pure, testable logic: normalizing raw ArcGIS GeoJSON features
into flat rows (dropping abandoned/geometry-less/unnamed records), the
exact-name/loose-county waterbody linking logic (reusing v1's own dedup
helpers), and the SQLite read/write path. No network calls -- fetch_layer()
itself is not exercised here, only its output shape (a list of raw GeoJSON
features), consistent with how this project tests other live-fetch call
sites (analysis/tests/test_v1_full_run.py). Uses a throwaway SQLite file;
the real data/v1/v1_full_run_results.db is never touched.

Run: python -m pytest analysis/tests/test_v2_access_points.py
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_access_points as v2  # noqa: E402


def _feature(lon, lat, **props):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


class NormalizeBoatAccessTests(unittest.TestCase):
    def test_ramp_and_carry_in_classified_correctly(self):
        features = [
            _feature(-89.0, 43.0, WATERBODY_NAME_TEXT="Devils Lake", COUNTY_NAME_TEXT="Sauk",
                     LANDING_TYPE_CODE="RAMP", ABANDON_FLAG="No"),
            _feature(-89.1, 43.1, WATERBODY_NAME_TEXT="Devils Lake", COUNTY_NAME_TEXT="Sauk",
                     LANDING_TYPE_CODE="CARRY-IN", ABANDON_FLAG="No"),
        ]
        rows = v2.normalize_boat_access(features)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["source_type"], "boat_ramp")
        self.assertEqual(rows[1]["source_type"], "boat_carry_in")

    def test_abandoned_site_excluded(self):
        features = [_feature(-89.0, 43.0, WATERBODY_NAME_TEXT="Old Lake", COUNTY_NAME_TEXT="Dane",
                              LANDING_TYPE_CODE="RAMP", ABANDON_FLAG="Yes")]
        self.assertEqual(v2.normalize_boat_access(features), [])

    def test_missing_waterbody_name_excluded(self):
        features = [_feature(-89.0, 43.0, WATERBODY_NAME_TEXT="", COUNTY_NAME_TEXT="Dane",
                              LANDING_TYPE_CODE="RAMP", ABANDON_FLAG="No")]
        self.assertEqual(v2.normalize_boat_access(features), [])

    def test_missing_geometry_excluded(self):
        feat = _feature(-89.0, 43.0, WATERBODY_NAME_TEXT="X", COUNTY_NAME_TEXT="Dane", LANDING_TYPE_CODE="RAMP")
        feat["geometry"] = None
        self.assertEqual(v2.normalize_boat_access([feat]), [])

    def test_lat_lon_preserved_from_geojson_coordinates(self):
        features = [_feature(-88.5, 44.5, WATERBODY_NAME_TEXT="X", COUNTY_NAME_TEXT="Dane",
                              LANDING_TYPE_CODE="RAMP", ABANDON_FLAG="No")]
        row = v2.normalize_boat_access(features)[0]
        self.assertAlmostEqual(row["longitude"], -88.5)
        self.assertAlmostEqual(row["latitude"], 44.5)


class NormalizeShoreFishingTests(unittest.TestCase):
    def test_basic_row(self):
        features = [_feature(-88.0, 44.0, FACILITY_NAME_TEXT="Pier A", WATERBODY_NAME_TEXT="Mauthe Lake",
                              COUNTY_NAME_TEXT="Fond du Lac", MORE_INFO_URL="http://example.org/1")]
        rows = v2.normalize_shore_fishing(features)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_type"], "shore_fishing")
        self.assertEqual(rows[0]["facility_name"], "Pier A")
        self.assertEqual(rows[0]["more_info_url"], "http://example.org/1")

    def test_missing_county_excluded(self):
        features = [_feature(-88.0, 44.0, FACILITY_NAME_TEXT="Pier A", WATERBODY_NAME_TEXT="Mauthe Lake",
                              COUNTY_NAME_TEXT="")]
        self.assertEqual(v2.normalize_shore_fishing(features), [])


class LinkToWaterbodyTests(unittest.TestCase):
    def test_exact_name_and_county_match(self):
        index = {"DEVILS LAKE": [("DEVILS LAKE", "Sauk")]}
        row = {"waterbody_name": "Devils Lake", "county": "Sauk"}
        self.assertEqual(v2.link_to_waterbody(row, index), ("DEVILS LAKE", "Sauk"))

    def test_no_match_when_name_absent(self):
        index = {"DEVILS LAKE": [("DEVILS LAKE", "Sauk")]}
        row = {"waterbody_name": "Some Other Lake", "county": "Sauk"}
        self.assertEqual(v2.link_to_waterbody(row, index), (None, None))

    def test_no_match_when_same_name_different_county(self):
        index = {"MILL POND": [("MILL POND", "Waukesha")]}
        row = {"waterbody_name": "Mill Pond", "county": "Dane"}
        self.assertEqual(v2.link_to_waterbody(row, index), (None, None))

    def test_picks_correct_candidate_among_same_named_waterbodies(self):
        index = {"ADAMS CREEK": [("ADAMS CREEK", "Eau Claire"), ("ADAMS CREEK", "Trempealeau")]}
        row = {"waterbody_name": "Adams Creek", "county": "Trempealeau"}
        self.assertEqual(v2.link_to_waterbody(row, index), ("ADAMS CREEK", "Trempealeau"))


class DbRoundTripTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        os.remove(self.db_path)

    def test_write_then_read_back(self):
        conn = sqlite3.connect(self.db_path)
        v2.init_db(conn)
        rows = [
            {"source_type": "boat_ramp", "facility_name": "F1", "waterbody_name": "Devils Lake",
             "county": "Sauk", "municipality": "Town X", "latitude": 43.4, "longitude": -89.7,
             "ada_accessible": "Yes", "ownership": "State", "more_info_url": None,
             "matched_waterbody_name": "DEVILS LAKE", "matched_county": "Sauk"},
            {"source_type": "shore_fishing", "facility_name": "Pier", "waterbody_name": "Mauthe Lake",
             "county": "Fond du Lac", "municipality": None, "latitude": 43.6, "longitude": -88.18,
             "ada_accessible": None, "ownership": None, "more_info_url": "http://x",
             "matched_waterbody_name": None, "matched_county": None},
        ]
        v2.write_access_points(conn, rows, "2026-01-01T00:00:00+00:00", "https://example.org")

        stored = conn.execute("SELECT * FROM access_points ORDER BY id").fetchall()
        self.assertEqual(len(stored), 2)

        meta = conn.execute("SELECT * FROM access_points_meta").fetchone()
        self.assertEqual(meta[1], "2026-01-01T00:00:00+00:00")  # fetched_at
        self.assertEqual(meta[2], 1)  # total_boat_ramp
        self.assertEqual(meta[4], 1)  # total_shore_fishing
        conn.close()

    def test_rerun_replaces_rather_than_accumulates(self):
        conn = sqlite3.connect(self.db_path)
        v2.init_db(conn)
        row = {"source_type": "boat_ramp", "facility_name": "F1", "waterbody_name": "X", "county": "Y",
               "municipality": None, "latitude": 1.0, "longitude": -1.0, "ada_accessible": None,
               "ownership": None, "more_info_url": None, "matched_waterbody_name": None, "matched_county": None}
        v2.write_access_points(conn, [row], "t1", "u1")
        v2.write_access_points(conn, [row, dict(row)], "t2", "u2")
        count = conn.execute("SELECT COUNT(*) FROM access_points").fetchone()[0]
        self.assertEqual(count, 2)
        meta_count = conn.execute("SELECT COUNT(*) FROM access_points_meta").fetchone()[0]
        self.assertEqual(meta_count, 1)
        conn.close()


class BuildWaterbodyIndexTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(
            """
            CREATE TABLE runs (run_timestamp TEXT PRIMARY KEY, finished_at TEXT);
            CREATE TABLE waterbody_results (
                run_timestamp TEXT, waterbody_name TEXT, county TEXT
            );
            """
        )

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    def test_uses_only_latest_run(self):
        self.conn.executemany(
            "INSERT INTO runs VALUES (?, ?)",
            [("run1", "2026-01-01T00:00:00+00:00"), ("run2", "2026-01-02T00:00:00+00:00")],
        )
        self.conn.executemany(
            "INSERT INTO waterbody_results VALUES (?, ?, ?)",
            [("run1", "OLD LAKE", "Dane"), ("run2", "DEVILS LAKE", "Sauk")],
        )
        self.conn.commit()
        index = v2.build_waterbody_index(self.conn)
        self.assertIn("DEVILS LAKE", index)
        self.assertNotIn("OLD LAKE", index)

    def test_empty_runs_table_returns_empty_index(self):
        self.assertEqual(v2.build_waterbody_index(self.conn), {})


if __name__ == "__main__":
    unittest.main()
