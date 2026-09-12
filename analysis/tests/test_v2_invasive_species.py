"""Deterministic unit tests for the V2 invasive-species ingestion script.

Covers the pure, testable logic: normalizing raw ArcGIS GeoJSON features
into flat rows (date conversion, geometry/field handling), and the
SQLite read/write path. No network calls -- fetch_species_points() itself
is not exercised here, consistent with how this project tests other
live-fetch call sites (analysis/tests/test_v2_access_points.py). Uses a
throwaway SQLite file; the real data/v1/v1_full_run_results.db is never
touched.

Run: python -m pytest analysis/tests/test_v2_invasive_species.py
"""

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_invasive_species as inv  # noqa: E402


def _feature(lon, lat, **props):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


class NormalizeSightingsTests(unittest.TestCase):
    def test_basic_row_with_all_fields(self):
        features = [_feature(-89.0, 43.0, ROI_STATUS_DESC="Verified and Vouchered",
                              ROI_START_DATE=1252990800000, ROI_SHORT_NAME="Test Site", WBIC="123456")]
        rows = inv.normalize_sightings(features, "Zebra Mussel", "Dreissena polymorpha", "invertebrate")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["species_common_name"], "Zebra Mussel")
        self.assertEqual(row["species_scientific_name"], "Dreissena polymorpha")
        self.assertEqual(row["taxon_group"], "invertebrate")
        self.assertEqual(row["site_description"], "Test Site")
        self.assertEqual(row["status"], "Verified and Vouchered")
        self.assertEqual(row["wbic"], "123456")
        self.assertAlmostEqual(row["longitude"], -89.0)
        self.assertAlmostEqual(row["latitude"], 43.0)

    def test_epoch_millis_converted_to_iso_date(self):
        # 1252990800000 ms -> 2009-09-15T05:00:00Z
        features = [_feature(-89.0, 43.0, ROI_START_DATE=1252990800000)]
        row = inv.normalize_sightings(features, "X", "Y", "plant")[0]
        self.assertEqual(row["detected_date"], "2009-09-15")

    def test_missing_date_is_none_not_crash(self):
        features = [_feature(-89.0, 43.0, ROI_START_DATE=None)]
        row = inv.normalize_sightings(features, "X", "Y", "plant")[0]
        self.assertIsNone(row["detected_date"])

    def test_missing_geometry_excluded(self):
        feat = _feature(-89.0, 43.0)
        feat["geometry"] = None
        self.assertEqual(inv.normalize_sightings([feat], "X", "Y", "fish"), [])

    def test_empty_site_description_becomes_none(self):
        features = [_feature(-89.0, 43.0, ROI_SHORT_NAME="")]
        row = inv.normalize_sightings(features, "X", "Y", "fish")[0]
        self.assertIsNone(row["site_description"])


class DbRoundTripTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        os.remove(self.db_path)

    def test_write_then_read_back(self):
        conn = sqlite3.connect(self.db_path)
        inv.init_db(conn)
        rows = [
            {"species_common_name": "Zebra Mussel", "species_scientific_name": "Dreissena polymorpha",
             "taxon_group": "invertebrate", "site_description": "Site A", "status": "Verified and Vouchered",
             "detected_date": "2020-01-01", "wbic": "111", "latitude": 43.0, "longitude": -89.0},
            {"species_common_name": "Rusty Crayfish", "species_scientific_name": "Orconectes rusticus",
             "taxon_group": "invertebrate", "site_description": None, "status": "Verified (Not Vouchered)",
             "detected_date": None, "wbic": None, "latitude": 44.0, "longitude": -90.0},
        ]
        inv.write_sightings(conn, rows, "2026-01-01T00:00:00+00:00", "https://example.org", 6)

        stored = conn.execute("SELECT * FROM invasive_species_sightings ORDER BY id").fetchall()
        self.assertEqual(len(stored), 2)

        meta = conn.execute("SELECT * FROM invasive_species_meta").fetchone()
        self.assertEqual(meta[1], "2026-01-01T00:00:00+00:00")  # fetched_at
        self.assertEqual(meta[2], 2)  # total_sightings
        self.assertEqual(meta[3], 6)  # species_covered
        conn.close()

    def test_rerun_replaces_rather_than_accumulates(self):
        conn = sqlite3.connect(self.db_path)
        inv.init_db(conn)
        row = {"species_common_name": "X", "species_scientific_name": "Y", "taxon_group": "fish",
               "site_description": None, "status": None, "detected_date": None, "wbic": None,
               "latitude": 1.0, "longitude": -1.0}
        inv.write_sightings(conn, [row], "t1", "u1", 6)
        inv.write_sightings(conn, [row, dict(row)], "t2", "u2", 6)
        count = conn.execute("SELECT COUNT(*) FROM invasive_species_sightings").fetchone()[0]
        self.assertEqual(count, 2)
        meta_count = conn.execute("SELECT COUNT(*) FROM invasive_species_meta").fetchone()[0]
        self.assertEqual(meta_count, 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
