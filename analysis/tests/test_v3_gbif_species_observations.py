"""Tests for the GBIF citizen-observation ingest.

The property that matters most: this never trusts GBIF's data blindly.
A low-confidence species match is refused, an out-of-Wisconsin
coordinate is rejected even if GBIF's own stateProvince tag disagrees,
and the module never claims a record is more certain than it is.
"""

import os
import sqlite3
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v3_gbif_species_observations as gbif  # noqa: E402


class TestSpeciesResolution(unittest.TestCase):
    def test_exact_species_match_returns_key_and_confidence(self):
        with mock.patch.object(gbif, "http_get_json", return_value={
            "matchType": "EXACT", "rank": "SPECIES", "usageKey": 2382172, "confidence": 99,
        }):
            key, confidence = gbif.resolve_species_key("Sander vitreus")
        self.assertEqual(key, 2382172)
        self.assertEqual(confidence, 99)

    def test_fuzzy_match_is_refused_not_silently_accepted(self):
        with mock.patch.object(gbif, "http_get_json", return_value={
            "matchType": "FUZZY", "rank": "SPECIES", "usageKey": 123, "confidence": 40,
        }):
            key, reason = gbif.resolve_species_key("Some Unclear Name")
        self.assertIsNone(key)

    def test_genus_or_higher_rank_match_is_refused(self):
        with mock.patch.object(gbif, "http_get_json", return_value={
            "matchType": "EXACT", "rank": "GENUS", "usageKey": 456, "confidence": 99,
        }):
            key, reason = gbif.resolve_species_key("Sander")
        self.assertIsNone(key)


class TestBoundingBox(unittest.TestCase):
    def test_a_real_wisconsin_coordinate_is_accepted(self):
        self.assertTrue(gbif._in_wisconsin_bbox(43.0731, -89.4012))  # Madison

    def test_a_florida_coordinate_is_rejected(self):
        self.assertFalse(gbif._in_wisconsin_bbox(28.5, -81.3))

    def test_a_coordinate_just_outside_the_box_is_rejected(self):
        self.assertFalse(gbif._in_wisconsin_bbox(41.0, -89.0))


class TestFetchObservations(unittest.TestCase):
    def _fake_page(self, results, end_of_records=True):
        return {"results": results, "endOfRecords": end_of_records}

    def test_a_real_looking_record_is_stored_with_all_fields(self):
        record = {
            "decimalLatitude": 45.0, "decimalLongitude": -89.5,
            "eventDate": "2024-06-01", "recordedBy": "someangler",
            "license": "http://creativecommons.org/licenses/by-nc/4.0/legalcode",
            "key": 123456789,
        }
        with mock.patch.object(gbif, "http_get_json", return_value=self._fake_page([record])):
            rows, rejected = gbif.fetch_observations(999, "WALLEYE", "Sander vitreus")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rejected, 0)
        row = rows[0]
        self.assertEqual(row["common_name"], "WALLEYE")
        self.assertEqual(row["recorded_by"], "someangler")
        self.assertEqual(row["gbif_url"], "https://www.gbif.org/occurrence/123456789")

    def test_a_record_outside_wisconsin_is_rejected_even_if_gbif_returned_it(self):
        # Defensive: even though the query itself filters by bbox, a
        # record that slips through (e.g. a bad GBIF geocode) must still
        # be caught locally.
        record = {
            "decimalLatitude": 25.7, "decimalLongitude": -80.2,  # Miami
            "eventDate": "2024-01-01", "recordedBy": "x", "license": None, "key": 1,
        }
        with mock.patch.object(gbif, "http_get_json", return_value=self._fake_page([record])):
            rows, rejected = gbif.fetch_observations(999, "WALLEYE", "Sander vitreus")
        self.assertEqual(len(rows), 0)
        self.assertEqual(rejected, 1)

    def test_a_record_with_no_coordinate_is_silently_skipped_not_counted_as_rejected(self):
        record = {"decimalLatitude": None, "decimalLongitude": None, "key": 2}
        with mock.patch.object(gbif, "http_get_json", return_value=self._fake_page([record])):
            rows, rejected = gbif.fetch_observations(999, "WALLEYE", "Sander vitreus")
        self.assertEqual(len(rows), 0)
        self.assertEqual(rejected, 0)

    def test_falls_back_to_rights_holder_when_recorded_by_is_missing(self):
        record = {
            "decimalLatitude": 45.0, "decimalLongitude": -89.5, "key": 3,
            "eventDate": "2024-01-01", "rightsHolder": "someone_else",
        }
        with mock.patch.object(gbif, "http_get_json", return_value=self._fake_page([record])):
            rows, _ = gbif.fetch_observations(999, "WALLEYE", "Sander vitreus")
        self.assertEqual(rows[0]["recorded_by"], "someone_else")


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        gbif.ensure_tables(self.conn)

    def test_ensure_tables_creates_both_tables(self):
        tables = {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        self.assertIn("gbif_species_observations", tables)
        self.assertIn("gbif_fetch_log", tables)

    def test_storing_the_same_occurrence_key_twice_does_not_duplicate(self):
        row = {
            "common_name": "WALLEYE", "scientific_name": "Sander vitreus",
            "lat": 45.0, "lon": -89.5, "observed_date": "2024-01-01",
            "recorded_by": "x", "license_url": None,
            "gbif_occurrence_key": 42, "gbif_url": "https://www.gbif.org/occurrence/42",
        }
        gbif.store_observations(self.conn, [row])
        gbif.store_observations(self.conn, [row])
        count = self.conn.execute("SELECT COUNT(*) FROM gbif_species_observations").fetchone()[0]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
