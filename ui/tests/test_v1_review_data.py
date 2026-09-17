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
CREATE TABLE access_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    facility_name TEXT,
    waterbody_name TEXT NOT NULL,
    county TEXT NOT NULL,
    municipality TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    ada_accessible TEXT,
    ownership TEXT,
    more_info_url TEXT,
    matched_waterbody_name TEXT,
    matched_county TEXT
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

    def _insert_access_point(
        self, name, county, lat, lon, matched_name=None, matched_county=None,
        source_type="boat_ramp", facility_name="Test Ramp",
    ):
        self.conn.execute(
            """INSERT INTO access_points
               (source_type, facility_name, waterbody_name, county, latitude, longitude,
                matched_waterbody_name, matched_county)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_type, facility_name, name, county, lat, lon,
             matched_name if matched_name is not None else name,
             matched_county if matched_county is not None else county),
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


class TestHaversineDistance(unittest.TestCase):
    def test_real_milwaukee_chicago_distance(self):
        # Real coordinates; real straight-line distance is ~146km.
        milwaukee = (43.0389, -87.9065)
        chicago = (41.8781, -87.6298)
        d = rd._haversine_km(milwaukee[0], milwaukee[1], chicago[0], chicago[1])
        self.assertAlmostEqual(d, 146, delta=15)

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(rd._haversine_km(43.0, -89.0, 43.0, -89.0), 0.0, delta=0.001)


class TestBuildTemperatureAnchors(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def test_source1_matched_access_point_used_as_anchor(self):
        self._insert_waterbody("Devils Lake", "Sauk", temp_value_c=18.5, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301)

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(len(anchors), 1)
        self.assertAlmostEqual(anchors[0]["lat"], 43.4286)
        self.assertAlmostEqual(anchors[0]["lon"], -89.7301)
        self.assertAlmostEqual(anchors[0]["value_c"], 18.5)
        self.assertEqual(anchors[0]["source"], "clmn_recent")

    def test_proxy_temperature_excluded_from_anchor_pool(self):
        self._insert_waterbody("Nowhere Lake", "Vilas", temp_value_c=22.0, temp_is_real=0, temp_method="nws_air_proxy_live")
        self._insert_access_point("Nowhere Lake", "Vilas", lat=46.0, lon=-89.5)

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(anchors, [])

    def test_unmatched_real_temp_with_no_coordinate_source_excluded(self):
        # temp_method isn't usgs_live or ndbc_buoy_live, and no matching
        # access point exists -- no coordinate source resolves, so this
        # waterbody must be left out rather than guessed.
        self._insert_waterbody("Mystery Lake", "Oneida", temp_value_c=19.0, temp_is_real=1, temp_method="clmn_recent")

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(anchors, [])

    def test_source2_usgs_gauge_coordinate_used_when_no_matched_access_point(self):
        # Real USGS station "BOIS BRULE RIVER NEAR LAKE SUPERIOR, WI" is in
        # data/v1/usgs_wi_water_temp_sites.csv; find_usgs_site_matches()
        # substring-matches on the waterbody name.
        self._insert_waterbody("Bois Brule River", "Douglas", temp_value_c=14.2, temp_is_real=1, temp_method="usgs_live")

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(len(anchors), 1)
        self.assertAlmostEqual(anchors[0]["lat"], 46.7055374, delta=0.01)
        self.assertAlmostEqual(anchors[0]["lon"], -91.6021071, delta=0.01)
        self.assertAlmostEqual(anchors[0]["value_c"], 14.2)

    def test_source3_ndbc_buoy_coordinate_used_for_lake_michigan(self):
        # Real buoy 45013 (Atwater Park, Milwaukee) is in
        # data/v1/lake_michigan_buoy_sites.csv.
        self._insert_waterbody(
            "Lake Michigan", "Milwaukee", temp_value_c=16.8, temp_is_real=1, temp_method="ndbc_buoy_live",
        )
        self.conn.execute(
            "UPDATE waterbody_results SET temp_source = ? WHERE waterbody_name = 'Lake Michigan'",
            ("NOAA NDBC buoy 45013 (ATW20 - Atwater Park WI (Milwaukee))",),
        )
        self.conn.commit()

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(len(anchors), 1)
        self.assertAlmostEqual(anchors[0]["lat"], 43.098, delta=0.01)
        self.assertAlmostEqual(anchors[0]["lon"], -87.85, delta=0.01)

    def test_matched_access_point_takes_priority_over_usgs_lookup(self):
        # Even though temp_method is 'usgs_live', a directly matched
        # access point's own coordinate should win -- it's a more precise
        # real coordinate than a generic name-matched USGS site.
        self._insert_waterbody("Bois Brule River", "Douglas", temp_value_c=14.2, temp_is_real=1, temp_method="usgs_live")
        self._insert_access_point("Bois Brule River", "Douglas", lat=1.0, lon=2.0)

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(len(anchors), 1)
        self.assertEqual(anchors[0]["lat"], 1.0)
        self.assertEqual(anchors[0]["lon"], 2.0)

    def test_implausible_stored_value_never_becomes_an_anchor(self):
        # Real bug: BREWERY CREEK (Iowa County) stored USGS's -999999
        # "no data" sentinel as a real measurement. As an anchor it
        # dragged Salmo Pond's estimate to -476,254C and sat inside the
        # radius of four Lake Mendota ramps. A row written by an older
        # run must never reach the estimator.
        self._insert_waterbody(
            "Brewery Creek", "Iowa", temp_value_c=-999999.0, temp_is_real=1, temp_method="clmn_recent",
        )
        self._insert_access_point("Brewery Creek", "Iowa", lat=43.125, lon=-89.635)

        anchors = rd.build_temperature_anchors(self.conn)
        self.assertEqual(anchors, [])

    def test_implausible_anchor_does_not_poison_a_nearby_estimate(self):
        self._insert_waterbody(
            "Brewery Creek", "Iowa", temp_value_c=-999999.0, temp_is_real=1, temp_method="clmn_recent",
        )
        self._insert_access_point("Brewery Creek", "Iowa", lat=43.125, lon=-89.635)
        self._insert_waterbody("Good Lake", "Dane", temp_value_c=19.0, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Good Lake", "Dane", lat=43.130, lon=-89.640)

        result = rd.estimate_temperature_from_nearby(self.conn, lat=43.127, lon=-89.637, max_km=15.0)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["value_c"], 19.0, delta=0.01)
        self.assertEqual(result["anchor_count"], 1)

    def test_no_runs_returns_empty_list(self):
        conn2 = sqlite3.connect(":memory:")
        conn2.row_factory = sqlite3.Row
        conn2.executescript(SCHEMA)
        self.assertEqual(rd.build_temperature_anchors(conn2), [])


class TestEstimateTemperatureFromNearby(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def test_no_real_anchor_in_range_returns_none(self):
        # Real anchor far away (Devils Lake, Sauk) from a query point in
        # a different part of the state (Ashland, far north).
        self._insert_waterbody("Devils Lake", "Sauk", temp_value_c=18.0, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301)

        result = rd.estimate_temperature_from_nearby(self.conn, lat=46.5927, lon=-90.8823, max_km=15.0)
        self.assertIsNone(result)

    def test_single_close_real_anchor_returns_its_value(self):
        # Real Devils Lake, Sauk coordinate; query point ~1km away.
        self._insert_waterbody("Devils Lake", "Sauk", temp_value_c=18.0, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301)

        result = rd.estimate_temperature_from_nearby(self.conn, lat=43.4370, lon=-89.7301, max_km=15.0)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["value_c"], 18.0, delta=0.01)
        self.assertEqual(result["anchor_count"], 1)
        self.assertLess(result["nearest_km"], 2.0)
        self.assertEqual(result["anchors"][0]["waterbody_name"], "Devils Lake")

    def test_idw_weights_nearer_anchor_more_heavily(self):
        # Two synthetic anchors on either side of the query point, one
        # much closer than the other -- the estimate must land closer to
        # the near anchor's value than a plain average would.
        self._insert_waterbody("Near Lake", "TestCounty", temp_value_c=10.0, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Near Lake", "TestCounty", lat=43.001, lon=-89.0)
        self._insert_waterbody("Far Lake", "TestCounty", temp_value_c=20.0, temp_is_real=1, temp_method="clmn_recent",
                                run_timestamp="2026-09-09T12:00:00+00:00")
        self._insert_access_point("Far Lake", "TestCounty", lat=43.1, lon=-89.0)

        result = rd.estimate_temperature_from_nearby(self.conn, lat=43.0, lon=-89.0, max_km=15.0)
        self.assertIsNotNone(result)
        self.assertEqual(result["anchor_count"], 2)
        plain_average = (10.0 + 20.0) / 2
        self.assertLess(result["value_c"], plain_average)
        self.assertGreater(result["value_c"], 10.0)

    def test_max_anchors_caps_how_many_are_used(self):
        for i in range(8):
            name = f"Lake{i}"
            self._insert_waterbody(name, "TestCounty", temp_value_c=float(i), temp_is_real=1, temp_method="clmn_recent")
            self._insert_access_point(name, "TestCounty", lat=43.0 + i * 0.001, lon=-89.0)

        result = rd.estimate_temperature_from_nearby(self.conn, lat=43.0, lon=-89.0, max_km=15.0, max_anchors=3)
        self.assertEqual(result["anchor_count"], 3)


class TestEstimateConfidence(unittest.TestCase):
    """The confidence signal is derived from measured quantities (distance
    to the nearest real reading, and how much nearby readings disagree),
    never from an invented probability."""

    def test_close_anchor_is_high_confidence(self):
        c = rd.describe_estimate_confidence(8.0)
        self.assertEqual(c["level"], "high")

    def test_mid_range_is_moderate(self):
        self.assertEqual(rd.describe_estimate_confidence(30.0)["level"], "moderate")

    def test_far_anchor_is_low(self):
        self.assertEqual(rd.describe_estimate_confidence(55.0)["level"], "low")

    def test_disagreeing_anchors_downgrade_confidence(self):
        # Distance alone would say "high"; readings that disagree by 6C are
        # direct evidence the water isn't uniform, whatever the distance.
        close = rd.describe_estimate_confidence(5.0)
        disagreeing = rd.describe_estimate_confidence(5.0, spread_c=6.0)
        self.assertEqual(close["level"], "high")
        self.assertEqual(disagreeing["level"], "moderate")
        self.assertIn("disagree", disagreeing["note"])

    def test_confidence_is_never_expressed_as_a_percentage(self):
        # Decision #005: no false precision. A percentage implies a
        # validated probability this project has never measured.
        for km in (1.0, 20.0, 50.0):
            c = rd.describe_estimate_confidence(km)
            self.assertNotIn("%", c["note"])
            self.assertIn(c["level"], ("high", "moderate", "low"))


class TestCountySpeciesEvidence(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def test_returns_real_county_records_ranked_by_waterbody_count(self):
        self._insert_waterbody("Lake A", "Vilas")
        self._insert_waterbody("Lake B", "Vilas")
        self._insert_species_prediction("Lake A", "Vilas", "WALLEYE")
        self._insert_species_prediction("Lake B", "Vilas", "WALLEYE")
        self._insert_species_prediction("Lake A", "Vilas", "MUSKELLUNGE")

        ev = rd.get_county_species_evidence(self.conn, "Vilas")
        self.assertEqual(ev["county"], "Vilas")
        self.assertEqual(ev["waterbodies_in_county"], 2)
        self.assertEqual(ev["species"][0]["species"], "WALLEYE")
        self.assertEqual(ev["species"][0]["waterbody_count"], 2)

    def test_matches_regardless_of_case_difference_from_access_points(self):
        # access_points.county is raw WDNR source text and mixes
        # "WAUKESHA" / "Waukesha" for the same real county, while
        # species_predictions/waterbody_results use one consistent
        # casing. This silently returned nothing for 144 real access
        # points across 54 counties before the UPPER() fix -- caught by
        # checking why spots with a real WDNR-documented county still
        # showed no county-level fallback at all.
        self._insert_waterbody("Pewaukee Lake", "Waukesha")
        self._insert_species_prediction("Pewaukee Lake", "Waukesha", "WALLEYE")

        ev = rd.get_county_species_evidence(self.conn, "WAUKESHA")
        self.assertIsNotNone(ev)
        self.assertEqual(ev["species"][0]["species"], "WALLEYE")
        self.assertEqual(ev["waterbodies_in_county"], 1)

    def test_county_with_no_records_returns_none_not_an_empty_shell(self):
        self.assertIsNone(rd.get_county_species_evidence(self.conn, "Nowhere"))

    def test_missing_county_returns_none(self):
        self.assertIsNone(rd.get_county_species_evidence(self.conn, None))

    def test_spot_with_own_species_does_not_get_county_fallback(self):
        # A spot that has real records of its own must never have them
        # diluted with weaker regional context.
        self._insert_waterbody("Devils Lake", "Sauk")
        self._insert_species_prediction("Devils Lake", "Sauk", "WALLEYE")
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301)

        detail = rd.get_spot_detail(self.conn, 43.4286, -89.7301)
        self.assertEqual(len(detail["species_predictions"]), 1)
        self.assertIsNone(detail["county_species"])

    def test_unmatched_spot_gets_county_evidence_instead_of_a_dead_end(self):
        self._insert_waterbody("Big Vilas Lake", "Vilas")
        self._insert_species_prediction("Big Vilas Lake", "Vilas", "MUSKELLUNGE")
        self.conn.execute(
            """INSERT INTO access_points
               (source_type, facility_name, waterbody_name, county, latitude, longitude,
                matched_waterbody_name, matched_county)
               VALUES ('boat_carry_in', 'Bittersweet Carry-In', 'Bittersweet Lake', 'Vilas',
                       46.02, -89.51, NULL, NULL)"""
        )
        self.conn.commit()

        detail = rd.get_spot_detail(self.conn, 46.02, -89.51)
        self.assertEqual(detail["species_predictions"], [])
        self.assertIsNotNone(detail["county_species"])
        self.assertEqual(detail["county_species"]["species"][0]["species"], "MUSKELLUNGE")


class TestCurrentHighlights(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def _matching_waterbody(self, name, county, species, temp=21.0):
        self._insert_waterbody(name, county, tier="survey_confirmed", temp_value_c=temp, temp_is_real=1)
        self._insert_species_prediction(name, county, species, any_match=1, match_description="within range")

    def test_highlights_are_distinct_by_species_and_waterbody(self):
        # Three cards of the same species, or the same lake three times,
        # reads as a bug rather than a picture of the state.
        self._matching_waterbody("Lake One", "A", "BLUEGILL")
        self._insert_species_prediction("Lake One", "A", "WALLEYE", any_match=1, match_description="within range")
        self._matching_waterbody("Lake Two", "B", "BLUEGILL")
        self._matching_waterbody("Lake Three", "C", "WALLEYE")
        self._matching_waterbody("Lake Four", "D", "MUSKELLUNGE")

        highlights = rd.get_current_highlights(self.conn, limit=3)
        self.assertEqual(len(highlights), 3)
        self.assertEqual(len({h["species"] for h in highlights}), 3)
        self.assertEqual(len({h["waterbody_name"] for h in highlights}), 3)

    def test_only_survey_confirmed_with_real_temperature_is_showcased(self):
        # The front page shows the strongest evidence the database holds,
        # never a proxy reading or a stocking-only record.
        self._insert_waterbody("Proxy Lake", "P", tier="survey_confirmed", temp_value_c=21.0, temp_is_real=0)
        self._insert_species_prediction("Proxy Lake", "P", "WALLEYE", any_match=1, match_description="within range")
        self._insert_waterbody("Stocked Lake", "S", tier="stocking_only", temp_value_c=21.0, temp_is_real=1)
        self._insert_species_prediction("Stocked Lake", "S", "PERCH", any_match=1, match_description="within range")

        self.assertEqual(rd.get_current_highlights(self.conn), [])

    def test_no_matches_returns_empty_list(self):
        self._insert_waterbody("Cold Lake", "Z", tier="survey_confirmed", temp_value_c=2.0, temp_is_real=1)
        self._insert_species_prediction("Cold Lake", "Z", "WALLEYE", any_match=0, match_description=None)
        self.assertEqual(rd.get_current_highlights(self.conn), [])


class TestFindAccessPointByCoords(DataTestBase):
    def test_finds_by_exact_coordinate(self):
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301, facility_name="Devils Lake Ramp")
        point = rd.find_access_point_by_coords(self.conn, 43.4286, -89.7301)
        self.assertIsNotNone(point)
        self.assertEqual(point["facility_name"], "Devils Lake Ramp")

    def test_finds_within_small_float_tolerance(self):
        # Real-world coordinates round-trip through JSON/JS -- a spot
        # link must still resolve even with tiny float drift.
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286001, lon=-89.7301, facility_name="Devils Lake Ramp")
        point = rd.find_access_point_by_coords(self.conn, 43.4286, -89.7301)
        self.assertIsNotNone(point)

    def test_returns_none_when_no_point_at_coordinate(self):
        point = rd.find_access_point_by_coords(self.conn, 0.0, 0.0)
        self.assertIsNone(point)

    def test_name_disambiguates_duplicate_coordinates(self):
        # Real data has 23 duplicate lat/lon pairs (two real points at the
        # same physical location) -- facility_name must pick the right one.
        self._insert_access_point("Shared Spot A", "TestCounty", lat=44.0, lon=-90.0, facility_name="Ramp A")
        self._insert_access_point("Shared Spot B", "TestCounty", lat=44.0, lon=-90.0, facility_name="Ramp B")
        point = rd.find_access_point_by_coords(self.conn, 44.0, -90.0, name="Ramp B")
        self.assertEqual(point["facility_name"], "Ramp B")


class TestGetSpotTemperature(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def test_real_matched_waterbody_temperature_used_first(self):
        self._insert_waterbody("Devils Lake", "Sauk", temp_value_c=18.0, temp_is_real=1, temp_method="clmn_recent")
        result = rd.get_spot_temperature(self.conn, 43.4286, -89.7301, matched_waterbody="Devils Lake", matched_county="Sauk")
        self.assertEqual(result["resolution"], "matched_waterbody_real")
        self.assertTrue(result["is_real"])
        self.assertAlmostEqual(result["value_c"], 18.0)

    def test_falls_back_to_interpolation_when_matched_temp_is_proxy(self):
        self._insert_waterbody("Nowhere Lake", "Vilas", temp_value_c=22.0, temp_is_real=0, temp_method="nws_air_proxy_live")
        self._insert_waterbody("Nearby Real Lake", "Vilas", temp_value_c=17.5, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Nearby Real Lake", "Vilas", lat=46.001, lon=-89.5)

        result = rd.get_spot_temperature(self.conn, 46.0, -89.5, matched_waterbody="Nowhere Lake", matched_county="Vilas")
        self.assertEqual(result["resolution"], "interpolated_nearby")
        self.assertFalse(result["is_real"])

    def test_falls_back_to_proxy_when_no_real_anchor_nearby(self):
        self._insert_waterbody("Nowhere Lake", "Vilas", temp_value_c=22.0, temp_is_real=0, temp_method="nws_air_proxy_live")
        result = rd.get_spot_temperature(self.conn, 46.0, -89.5, matched_waterbody="Nowhere Lake", matched_county="Vilas")
        self.assertEqual(result["resolution"], "matched_waterbody_proxy")
        self.assertFalse(result["is_real"])
        self.assertAlmostEqual(result["value_c"], 22.0)

    def test_none_when_unmatched_and_no_nearby_anchor(self):
        result = rd.get_spot_temperature(self.conn, 46.0, -89.5)
        self.assertIsNone(result)

    def test_unmatched_point_still_gets_interpolated_estimate(self):
        self._insert_waterbody("Nearby Real Lake", "Vilas", temp_value_c=17.5, temp_is_real=1, temp_method="clmn_recent")
        self._insert_access_point("Nearby Real Lake", "Vilas", lat=46.001, lon=-89.5)

        result = rd.get_spot_temperature(self.conn, 46.0, -89.5)
        self.assertEqual(result["resolution"], "interpolated_nearby")


class TestGetSpotDetail(DataTestBase):
    def setUp(self):
        super().setUp()
        self._insert_run()

    def test_unknown_coordinate_returns_none(self):
        self.assertIsNone(rd.get_spot_detail(self.conn, 0.0, 0.0))

    def test_matched_spot_includes_species_predictions(self):
        self._insert_waterbody("Devils Lake", "Sauk", temp_value_c=18.0, temp_is_real=1, temp_method="clmn_recent")
        self._insert_species_prediction("Devils Lake", "Sauk", "WALLEYE", any_match=1)
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301, facility_name="Devils Lake Ramp")

        detail = rd.get_spot_detail(self.conn, 43.4286, -89.7301)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["point"]["facility_name"], "Devils Lake Ramp")
        self.assertEqual(detail["temperature"]["resolution"], "matched_waterbody_real")
        self.assertEqual(len(detail["species_predictions"]), 1)
        self.assertEqual(detail["species_predictions"][0]["species"], "WALLEYE")

    def test_matched_spot_includes_full_waterbody_record_not_just_species(self):
        # A matched spot's page must carry the waterbody's own narrative
        # text and fields -- so viewing a spot never requires clicking
        # through to a separate /waterbody page for the full picture.
        self._insert_waterbody(
            "Devils Lake", "Sauk", temp_value_c=18.0, temp_is_real=1, temp_method="clmn_recent",
            narrative="=== full generated narrative text ===",
        )
        self._insert_access_point("Devils Lake", "Sauk", lat=43.4286, lon=-89.7301, facility_name="Devils Lake Ramp")

        detail = rd.get_spot_detail(self.conn, 43.4286, -89.7301)
        self.assertIsNotNone(detail["waterbody"])
        self.assertIn("full generated narrative text", detail["waterbody"]["narrative_text"])
        self.assertEqual(detail["waterbody"]["waterbody_name"], "Devils Lake")

    def test_unmatched_spot_has_no_species_predictions_never_guessed(self):
        self.conn.execute(
            """INSERT INTO access_points
               (source_type, facility_name, waterbody_name, county, latitude, longitude,
                matched_waterbody_name, matched_county)
               VALUES ('boat_ramp', 'Lone Ramp', 'Unknown Pond', 'Vilas', 46.0, -89.5, NULL, NULL)"""
        )
        self.conn.commit()

        detail = rd.get_spot_detail(self.conn, 46.0, -89.5)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["species_predictions"], [])
        self.assertIsNone(detail["waterbody"])


if __name__ == "__main__":
    unittest.main()


class TestActivityWindow(unittest.TestCase):
    """Real dawn/dusk times at a real coordinate. Verified against
    published Madison, WI times: the algorithm lands within a couple of
    minutes across both solstices."""

    MADISON = (43.0731, -89.4012)

    def _ct(self, dt):
        import zoneinfo
        return dt.astimezone(zoneinfo.ZoneInfo("America/Chicago"))

    def test_summer_solstice_matches_published_madison_times(self):
        when = datetime.datetime(2026, 6, 21, 12, tzinfo=datetime.timezone.utc)
        w = rd.get_activity_window(*self.MADISON, when=when)
        sunrise = self._ct(w["sunrise"])
        sunset = self._ct(w["sunset"])
        # Published: sunrise ~5:18, sunset ~20:38 CDT
        self.assertEqual(sunrise.hour, 5)
        self.assertLess(abs(sunrise.minute - 18), 8)
        self.assertEqual(sunset.hour, 20)
        self.assertLess(abs(sunset.minute - 38), 8)

    def test_winter_solstice_is_dramatically_shorter(self):
        summer = rd.get_activity_window(*self.MADISON, when=datetime.datetime(2026, 6, 21, 12, tzinfo=datetime.timezone.utc))
        winter = rd.get_activity_window(*self.MADISON, when=datetime.datetime(2026, 12, 21, 12, tzinfo=datetime.timezone.utc))
        summer_len = (summer["sunset"] - summer["sunrise"]).total_seconds() / 3600
        winter_len = (winter["sunset"] - winter["sunrise"]).total_seconds() / 3600
        self.assertGreater(summer_len, 15)
        self.assertLess(winter_len, 10)

    def test_dawn_window_precedes_sunrise_and_dusk_follows_sunset(self):
        w = rd.get_activity_window(*self.MADISON)
        self.assertLess(w["dawn_start"], w["sunrise"])
        self.assertLess(w["sunrise"], w["sunset"])
        self.assertLess(w["sunset"], w["dusk_end"])

    def test_missing_coordinates_return_none(self):
        self.assertIsNone(rd.get_activity_window(None, None))


class TestStockingHistory(DataTestBase):
    def setUp(self):
        super().setUp()
        self.conn.executescript(
            """CREATE TABLE stocking_history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   waterbody TEXT NOT NULL, county TEXT NOT NULL,
                   stocking_year INTEGER NOT NULL, species TEXT NOT NULL,
                   strain TEXT, age_class TEXT, number_stocked INTEGER,
                   avg_length_in REAL, source_type TEXT NOT NULL, source_url TEXT);"""
        )
        self.conn.commit()

    def _stock(self, waterbody, county, year, species, n, age="YEARLING"):
        self.conn.execute(
            "INSERT INTO stocking_history (waterbody, county, stocking_year, species, age_class, "
            "number_stocked, avg_length_in, source_type) VALUES (?,?,?,?,?,?,?, 'DNR')",
            (waterbody, county, year, species, age, n, 9.0),
        )
        self.conn.commit()

    def test_returns_records_newest_first_with_totals(self):
        self._stock("DEVILS LAKE", "Sauk", 2023, "BROWN TROUT", 16110)
        self._stock("DEVILS LAKE", "Sauk", 2025, "BROWN TROUT", 16466)
        h = rd.get_stocking_history(self.conn, "DEVILS LAKE", "Sauk")
        self.assertEqual(h["latest_year"], 2025)
        self.assertEqual(h["total_stocked"], 32576)
        self.assertEqual(h["events"][0]["stocking_year"], 2025)

    def test_case_insensitive_match(self):
        self._stock("DEVILS LAKE", "Sauk", 2025, "WALLEYE", 100)
        self.assertIsNotNone(rd.get_stocking_history(self.conn, "devils lake", "sauk"))

    def test_respects_the_since_year_cutoff(self):
        self._stock("OLD LAKE", "Iron", 2012, "WALLEYE", 500)
        self.assertIsNone(rd.get_stocking_history(self.conn, "OLD LAKE", "Iron", since_year=2020))

    def test_unstocked_water_returns_none_not_an_empty_shell(self):
        self.assertIsNone(rd.get_stocking_history(self.conn, "NOWHERE LAKE", "Vilas"))


class TestSpotVerdict(unittest.TestCase):
    """The page must always give an answer. 42% of waterbodies have
    nothing inside a window, and 'no match' is a dead end for a reader
    trying to decide whether to drive somewhere."""

    WALLEYE = [{"type": "activity_window", "range_c": [12.8, 23.9]}]

    def test_inside_window_measures_zero_distance(self):
        d, direction, _ = rd._window_distance_c(self.WALLEYE, 18.0)
        self.assertEqual(d, 0.0)
        self.assertEqual(direction, "inside")

    def test_below_window_measures_real_distance(self):
        d, direction, _ = rd._window_distance_c(self.WALLEYE, 10.8)
        self.assertAlmostEqual(d, 2.0)
        self.assertEqual(direction, "below")

    def test_above_window_measures_real_distance(self):
        d, direction, _ = rd._window_distance_c(self.WALLEYE, 25.9)
        self.assertAlmostEqual(d, 2.0)
        self.assertEqual(direction, "above")

    def test_matching_species_rank_ahead_of_near_misses(self):
        preds = [
            {"species": "WALLEYE", "any_match": 0, "diel_active": 1},
            {"species": "BLUEGILL", "any_match": 1, "diel_active": 0},
        ]
        ranked = rd.rank_species_by_proximity(preds, 21.0)
        self.assertTrue(ranked[0]["any_match"])

    def test_verdict_names_what_is_matching(self):
        preds = [{"species": "WALLEYE", "any_match": 1, "diel_active": 1}]
        v = rd.build_spot_verdict(preds, {"value_c": 18.0, "is_real": True}, None)
        self.assertIn("window", v["headline"])
        self.assertIn("Walleye", v["detail"])

    def test_verdict_offers_the_closest_species_when_nothing_matches(self):
        # The whole point: never answer with a blank.
        preds = [{"species": "WALLEYE", "any_match": 0, "diel_active": 1}]
        v = rd.build_spot_verdict(preds, {"value_c": 10.8, "is_real": True}, None)
        self.assertIsNotNone(v["closest"])
        self.assertIn("Closest is Walleye", v["detail"])
        self.assertIn("below", v["detail"])

    def test_verdict_is_honest_when_there_is_no_temperature(self):
        preds = [{"species": "WALLEYE", "any_match": 0, "diel_active": 0}]
        v = rd.build_spot_verdict(preds, None, None)
        self.assertIn("No temperature", v["headline"])
        self.assertEqual(v["matching"], [])

    def test_ranking_never_claims_a_near_miss_is_biting(self):
        # A species outside its window is "closest", never "matching".
        preds = [{"species": "WALLEYE", "any_match": 0, "diel_active": 0}]
        v = rd.build_spot_verdict(preds, {"value_c": 10.8, "is_real": True}, None)
        self.assertEqual(v["matching"], [])
        self.assertNotIn("biting", (v["detail"] or "").lower())


class TestCitizenObservedSpecies(unittest.TestCase):
    """GBIF/iNaturalist sightings are a real but distinct evidence tier --
    the tests that matter most are about distance filtering and never
    silently blending this into anything WDNR-sourced."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE gbif_species_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                common_name TEXT NOT NULL,
                scientific_name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                observed_date TEXT,
                recorded_by TEXT,
                license_url TEXT,
                gbif_occurrence_key INTEGER NOT NULL UNIQUE,
                gbif_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            """
        )

    def _insert(self, common_name, lat, lon, observed_date, key, recorded_by="tester"):
        self.conn.execute(
            """INSERT INTO gbif_species_observations
               (common_name, scientific_name, lat, lon, observed_date, recorded_by,
                license_url, gbif_occurrence_key, gbif_url, fetched_at)
               VALUES (?, 'Testus fishus', ?, ?, ?, ?, NULL, ?, 'https://gbif.org/x', '2026-01-01')""",
            (common_name, lat, lon, observed_date, recorded_by, key),
        )
        self.conn.commit()

    def test_returns_empty_list_with_no_coordinates(self):
        self.assertEqual(rd.get_citizen_observed_species(self.conn, None, None), [])

    def test_returns_empty_list_when_table_does_not_exist(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        self.assertEqual(rd.get_citizen_observed_species(conn, 45.0, -89.0), [])

    def test_a_nearby_observation_is_included(self):
        self._insert("WALLEYE", 45.001, -89.001, "2024-06-01", 1)
        result = rd.get_citizen_observed_species(self.conn, 45.0, -89.0, radius_km=8.0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["species"], "WALLEYE")
        self.assertLess(result[0]["distance_km"], 1.0)

    def test_a_far_away_observation_is_excluded(self):
        self._insert("WALLEYE", 46.5, -90.5, "2024-06-01", 2)  # well over 8km away
        result = rd.get_citizen_observed_species(self.conn, 45.0, -89.0, radius_km=8.0)
        self.assertEqual(result, [])

    def test_only_the_most_recent_sighting_per_species_is_kept(self):
        self._insert("WALLEYE", 45.001, -89.001, "2020-01-01", 3)
        self._insert("WALLEYE", 45.002, -89.002, "2024-06-01", 4)
        result = rd.get_citizen_observed_species(self.conn, 45.0, -89.0, radius_km=8.0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["observed_date"], "2024-06-01")

    def test_different_species_are_both_kept(self):
        self._insert("WALLEYE", 45.001, -89.001, "2024-06-01", 5)
        self._insert("MUSKELLUNGE", 45.001, -89.001, "2024-06-01", 6)
        result = rd.get_citizen_observed_species(self.conn, 45.0, -89.0, radius_km=8.0)
        self.assertEqual({r["species"] for r in result}, {"WALLEYE", "MUSKELLUNGE"})

    def test_result_carries_attribution_fields_for_license_compliance(self):
        self._insert("WALLEYE", 45.001, -89.001, "2024-06-01", 7, recorded_by="realangler42")
        result = rd.get_citizen_observed_species(self.conn, 45.0, -89.0, radius_km=8.0)
        self.assertEqual(result[0]["recorded_by"], "realangler42")
        self.assertTrue(result[0]["gbif_url"].startswith("https://"))


class TestBuildSpeciesCategories(unittest.TestCase):
    """The property that matters most: a species with real confirming
    evidence (survey or citizen sighting) is never also listed as merely
    "likely" -- the stronger evidence wins and it appears exactly once."""

    def test_survey_confirmed_waterbody_puts_species_in_confirmed_bucket(self):
        preds = [{"species": "WALLEYE"}]
        waterbody = {"presence_tier": "survey_confirmed"}
        result = rd.build_species_categories(preds, waterbody, None, [], None)
        self.assertEqual([s["species"] for s in result["confirmed_sightings"]], ["WALLEYE"])
        self.assertEqual(result["likely_species"], [])
        self.assertIn("WDNR fisheries survey", result["confirmed_sightings"][0]["sources"])

    def test_stocking_only_waterbody_puts_species_in_likely_bucket(self):
        preds = [{"species": "NORTHERN PIKE"}]
        waterbody = {"presence_tier": "stocking_only"}
        result = rd.build_species_categories(preds, waterbody, None, [], None)
        self.assertEqual(result["confirmed_sightings"], [])
        self.assertEqual([s["species"] for s in result["likely_species"]], ["NORTHERN PIKE"])
        self.assertIn("WDNR stocking record", result["likely_species"][0]["sources"])

    def test_citizen_sighting_alone_lands_in_confirmed(self):
        citizen = [{"species": "MUSKELLUNGE", "observed_date": "2024-06-01", "recorded_by": "x", "gbif_url": "https://gbif.org/1"}]
        result = rd.build_species_categories([], None, None, citizen, None)
        self.assertEqual([s["species"] for s in result["confirmed_sightings"]], ["MUSKELLUNGE"])
        self.assertTrue(any("citizen sighting" in s for s in result["confirmed_sightings"][0]["sources"]))

    def test_citizen_sighting_promotes_a_stocking_only_species_out_of_likely(self):
        # The same species is both stocked (weak) and really sighted
        # (strong) -- it must end up ONLY in confirmed, never duplicated.
        preds = [{"species": "WALLEYE"}]
        waterbody = {"presence_tier": "stocking_only"}
        citizen = [{"species": "WALLEYE", "observed_date": "2024-06-01", "recorded_by": "x", "gbif_url": "https://gbif.org/1"}]
        result = rd.build_species_categories(preds, waterbody, None, citizen, None)
        confirmed_species = [s["species"] for s in result["confirmed_sightings"]]
        likely_species = [s["species"] for s in result["likely_species"]]
        self.assertEqual(confirmed_species, ["WALLEYE"])
        self.assertNotIn("WALLEYE", likely_species)

    def test_county_species_never_overrides_an_already_confirmed_species(self):
        preds = [{"species": "WALLEYE"}]
        waterbody = {"presence_tier": "survey_confirmed"}
        county = {"county": "Vilas", "waterbodies_in_county": 10,
                  "species": [{"species": "WALLEYE", "waterbody_count": 5, "survey_confirmed": False}]}
        result = rd.build_species_categories(preds, waterbody, county, [], None)
        self.assertEqual([s["species"] for s in result["confirmed_sightings"]], ["WALLEYE"])
        self.assertEqual(result["likely_species"], [])

    def test_county_species_lands_in_likely_when_nothing_stronger_exists(self):
        county = {"county": "Vilas", "waterbodies_in_county": 10,
                  "species": [{"species": "YELLOW PERCH", "waterbody_count": 5, "survey_confirmed": False}]}
        result = rd.build_species_categories([], None, county, [], None)
        self.assertEqual([s["species"] for s in result["likely_species"]], ["YELLOW PERCH"])

    def test_activity_is_attached_when_temperature_is_inside_the_documented_window(self):
        preds = [{"species": "WALLEYE"}]
        waterbody = {"presence_tier": "survey_confirmed"}
        # Walleye's documented activity window comfortably includes 18C.
        result = rd.build_species_categories(preds, waterbody, None, [], 18.0)
        activity = result["confirmed_sightings"][0]["activity"]
        self.assertIsNotNone(activity)
        self.assertIn("inside_window", activity)

    def test_no_temperature_means_no_activity_claim_at_all(self):
        preds = [{"species": "WALLEYE"}]
        waterbody = {"presence_tier": "survey_confirmed"}
        result = rd.build_species_categories(preds, waterbody, None, [], None)
        self.assertIsNone(result["confirmed_sightings"][0]["activity"])

    def test_empty_everything_returns_empty_buckets_not_an_error(self):
        result = rd.build_species_categories([], None, None, [], None)
        self.assertEqual(result, {"confirmed_sightings": [], "likely_species": []})


class TestApplyCategoriesToVerdict(unittest.TestCase):
    """The verdict headline must never say "No species data" one section
    above a dashboard that's showing real species -- this is what fixes
    that specific contradiction."""

    def test_upgrades_no_species_data_headline_when_categories_have_a_match(self):
        verdict = {"headline": "No species data for this spot", "detail": "x", "matching": []}
        categories = {
            "confirmed_sightings": [],
            "likely_species": [{"species": "WALLEYE", "sources": ["regional (county) record"],
                                 "activity": {"inside_window": True, "distance_f": 0.0, "direction": "inside"}}],
        }
        rd._apply_categories_to_verdict(verdict, categories)
        self.assertIn("1 species in its documented window", verdict["headline"])
        self.assertIn("Walleye", verdict["detail"])
        self.assertTrue(verdict["matching"])

    def test_upgrades_to_closest_when_nothing_is_inside_its_window(self):
        verdict = {"headline": "No species data for this spot", "detail": "x", "matching": []}
        categories = {
            "confirmed_sightings": [],
            "likely_species": [{"species": "WALLEYE", "sources": ["regional (county) record"],
                                 "activity": {"inside_window": False, "distance_f": 5.0, "direction": "below"}}],
        }
        rd._apply_categories_to_verdict(verdict, categories)
        self.assertEqual(verdict["headline"], "Nothing is inside its window right now")
        self.assertIn("Closest is Walleye", verdict["detail"])
        self.assertIn("5.0", verdict["detail"])

    def test_leaves_no_species_data_alone_when_categories_are_genuinely_empty(self):
        verdict = {"headline": "No species data for this spot", "detail": "x", "matching": []}
        categories = {"confirmed_sightings": [], "likely_species": []}
        rd._apply_categories_to_verdict(verdict, categories)
        self.assertEqual(verdict["headline"], "No species data for this spot")

    def test_leaves_no_species_data_alone_when_entries_exist_but_have_no_activity(self):
        # e.g. temperature was unavailable, so activity couldn't be computed --
        # nothing honest to upgrade the headline to.
        verdict = {"headline": "No species data for this spot", "detail": "x", "matching": []}
        categories = {
            "confirmed_sightings": [],
            "likely_species": [{"species": "WALLEYE", "sources": ["regional (county) record"], "activity": None}],
        }
        rd._apply_categories_to_verdict(verdict, categories)
        self.assertEqual(verdict["headline"], "No species data for this spot")
