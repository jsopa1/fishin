"""Deterministic unit tests for the V1 conditions & biology forecast script.

Focus (per Part 4's explicit test requirements): threshold-matching
correctness, species filtering (survey-confirmed vs. stocking-only,
including the real name-collision bug this project's own data surfaced --
two "Fish Lake"s, and 813 blank-waterbody stocking rows that were
spuriously matching every query before a fix), correct fallback labeling
when a real water-temp source is unavailable, and "insufficient data"
handling -- no silent failures anywhere. All fixtures are small, synthetic,
temp-file CSVs; the real data/v1/*.csv files are never touched by these
tests, and no network calls are made.

Run: python -m pytest analysis/tests/test_v1_conditions_biology_forecast.py
"""

import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v1_conditions_biology_forecast as v1  # noqa: E402


def _write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


class TempDataMixin:
    """Points the module's global CSV/JSON path constants at isolated temp
    fixtures for the duration of a test, restoring the originals after."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_paths = {
            "SURVEY_CSV": v1.SURVEY_CSV,
            "SURVEY_CSV_BATCH2": v1.SURVEY_CSV_BATCH2,
            "STOCKING_CSV": v1.STOCKING_CSV,
            "WATER_TEMP_CSV": v1.WATER_TEMP_CSV,
            "USGS_SITES_CSV": v1.USGS_SITES_CSV,
            "THRESHOLDS_JSON": v1.THRESHOLDS_JSON,
        }
        # Point batch2 and the USGS sites table at nonexistent temp paths by
        # default so tests never pick up this project's real, larger data
        # files -- each test that needs one calls the matching _set_* helper.
        v1.SURVEY_CSV_BATCH2 = Path(self._tmpdir) / "no_batch2.csv"
        v1.USGS_SITES_CSV = Path(self._tmpdir) / "no_usgs_sites.csv"

    def tearDown(self):
        for name, path in self._orig_paths.items():
            setattr(v1, name, path)

    def _set_usgs_sites(self, rows):
        path = os.path.join(self._tmpdir, "usgs_sites.csv")
        _write_csv(path, rows, ["site_no", "station_nm", "site_type", "lat", "lon"])
        v1.USGS_SITES_CSV = Path(path)

    def _set_survey(self, rows):
        path = os.path.join(self._tmpdir, "survey.csv")
        _write_csv(
            path, rows,
            ["lake_name", "county", "survey_year", "species", "cpue_or_abundance_metric", "cpue_value", "notes", "source_pdf_url"],
        )
        v1.SURVEY_CSV = Path(path)

    def _set_stocking(self, rows):
        path = os.path.join(self._tmpdir, "stocking.csv")
        _write_csv(
            path, rows,
            ["source_url", "retrieval_date", "stocking_year", "source_type", "county", "waterbody", "local_wb_name", "species", "strain", "age_class", "number_stocked", "avg_length_in"],
        )
        v1.STOCKING_CSV = Path(path)

    def _set_water_temp(self, rows):
        path = os.path.join(self._tmpdir, "watertemp.csv")
        _write_csv(
            path, rows,
            ["lake_name", "county", "method", "value_c", "value_f", "is_real_water_measurement", "retrieved_at", "source_url_or_station", "notes"],
        )
        v1.WATER_TEMP_CSV = Path(path)

    def _set_thresholds(self, species_dict):
        path = os.path.join(self._tmpdir, "thresholds.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"species": species_dict}, f)
        v1.THRESHOLDS_JSON = Path(path)


class TestThresholdMatching(unittest.TestCase):
    def test_range_in_bounds(self):
        t = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNotNone(v1.describe_threshold_match(20.0, t))

    def test_range_out_of_bounds(self):
        t = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNone(v1.describe_threshold_match(30.0, t))

    def test_range_boundary_inclusive(self):
        t = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNotNone(v1.describe_threshold_match(12.8, t))
        self.assertIsNotNone(v1.describe_threshold_match(23.9, t))

    def test_peak_sub_range_noted(self):
        t = {
            "type": "spawning_trigger", "range_c": [4.4, 11.1], "range_f": [40, 52],
            "peak_range_c": [6.7, 8.9], "peak_range_f": [44, 48], "description": "x",
        }
        self.assertIn("peak sub-range", v1.describe_threshold_match(7.5, t))

    def test_avoidance_above_triggers_over_threshold(self):
        t = {"type": "avoidance_above", "threshold_c": 23.9, "threshold_f": 75, "description": "x"}
        self.assertIsNotNone(v1.describe_threshold_match(25.0, t))

    def test_avoidance_above_does_not_trigger_at_boundary(self):
        t = {"type": "avoidance_above", "threshold_c": 23.9, "threshold_f": 75, "description": "x"}
        self.assertIsNone(v1.describe_threshold_match(23.9, t))

    def test_preferred_point_within_tolerance(self):
        t = {"type": "activity_window", "preferred_point_c": 11.7, "preferred_point_f": 53.1, "description": "x"}
        self.assertIsNotNone(v1.describe_threshold_match(12.5, t))

    def test_preferred_point_outside_tolerance(self):
        t = {"type": "activity_window", "preferred_point_c": 11.7, "preferred_point_f": 53.1, "description": "x"}
        self.assertIsNone(v1.describe_threshold_match(20.0, t))

    def test_disputed_muskellunge_range_matches_both_ends(self):
        # Real disputed range from docs/v1_physiology_research_candidates.md:
        # V0's 22C and GLFC's 24-27.3C cluster are both inside [22.0, 27.3].
        t = {"type": "activity_window", "range_c": [22.0, 27.3], "range_f": [71.6, 81.1], "description": "disputed"}
        self.assertIsNotNone(v1.describe_threshold_match(22.0, t))
        self.assertIsNotNone(v1.describe_threshold_match(26.0, t))


class TestLakeNameMatching(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(v1._lake_name_matches("DEVILS LAKE", "Devils Lake"))

    def test_substring_match_handles_real_naming_inconsistency(self):
        # Real case: survey CSV says "Lauderdale Lakes (Green Lake/Middle
        # Lake/Mill Lake chain)", water-temp CSV says "Lauderdale Lakes".
        self.assertTrue(v1._lake_name_matches(
            "LAUDERDALE LAKES", "Lauderdale Lakes (Green Lake/Middle Lake/Mill Lake chain)"
        ))

    def test_empty_candidate_never_matches(self):
        # Real bug this project's own data surfaced: 813 stocking rows have
        # a blank waterbody field. An empty string is a substring of
        # everything, so without an explicit guard, every blank row would
        # spuriously match every lake query.
        self.assertFalse(v1._lake_name_matches("LAKE MONONA", ""))
        self.assertFalse(v1._lake_name_matches("LAKE MONONA", "   "))

    def test_short_strings_do_not_substring_match(self):
        self.assertFalse(v1._lake_name_matches("FOX", "Fox River Flowage"))

    def test_unrelated_names_do_not_match(self):
        self.assertFalse(v1._lake_name_matches("DEVILS LAKE", "Pelican Lake"))


class TestCountyMatching(unittest.TestCase):
    def test_exact_county_match(self):
        self.assertTrue(v1._county_matches("Dane", "Dane"))

    def test_county_suffix_ignored(self):
        self.assertTrue(v1._county_matches("Sauk", "Sauk County"))

    def test_multi_county_slash_notation(self):
        self.assertTrue(v1._county_matches("Columbia/Sauk", "Columbia and Sauk"))
        self.assertTrue(v1._county_matches("Sauk", "Columbia and Sauk"))

    def test_different_counties_do_not_match(self):
        self.assertFalse(v1._county_matches("Dane", "Waushara"))


class TestSpeciesPresence(TempDataMixin, unittest.TestCase):
    def test_survey_confirmed_takes_priority_over_stocking(self):
        self._set_survey([
            {"lake_name": "Test Lake", "county": "Test County", "survey_year": "2024",
             "species": "Walleye", "cpue_or_abundance_metric": "fish/net night", "cpue_value": "5.0",
             "notes": "", "source_pdf_url": ""},
        ])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "2020", "source_type": "DNR",
             "county": "Test County", "waterbody": "TEST LAKE", "local_wb_name": "", "species": "MUSKELLUNGE",
             "strain": "", "age_class": "", "number_stocked": "100", "avg_length_in": ""},
        ])
        presence = v1.get_species_presence("Test Lake")
        self.assertEqual(presence["tier"], "survey_confirmed")
        self.assertEqual(presence["species"], ["WALLEYE"])

    def test_falls_back_to_stocking_only_when_no_survey(self):
        self._set_survey([])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "2020", "source_type": "DNR",
             "county": "Test County", "waterbody": "TEST LAKE", "local_wb_name": "", "species": "WALLEYE",
             "strain": "", "age_class": "", "number_stocked": "100", "avg_length_in": ""},
        ])
        presence = v1.get_species_presence("Test Lake")
        self.assertEqual(presence["tier"], "stocking_only")
        self.assertEqual(presence["species"], ["WALLEYE"])

    def test_no_data_when_neither_source_has_the_lake(self):
        self._set_survey([])
        self._set_stocking([])
        presence = v1.get_species_presence("Nowhere Lake")
        self.assertEqual(presence["tier"], "no_data")
        self.assertEqual(presence["species"], [])

    def test_stocking_before_min_year_excluded(self):
        self._set_survey([])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "1995", "source_type": "DNR",
             "county": "Test County", "waterbody": "TEST LAKE", "local_wb_name": "", "species": "WALLEYE",
             "strain": "", "age_class": "", "number_stocked": "100", "avg_length_in": ""},
        ])
        presence = v1.get_species_presence("Test Lake")
        # 1995 is before STOCKING_MIN_YEAR_FOR_PRESENCE (2011) -> no usable record
        self.assertEqual(presence["tier"], "no_data")

    def test_ambiguous_lake_name_raises_without_county(self):
        # Real case: two distinct "Fish Lake"s exist in this project's
        # actual data (Dane County and Waushara County).
        self._set_survey([
            {"lake_name": "Fish Lake", "county": "Dane", "survey_year": "2021",
             "species": "Bluegill", "cpue_or_abundance_metric": "x", "cpue_value": "1",
             "notes": "", "source_pdf_url": ""},
            {"lake_name": "Fish Lake", "county": "Waushara", "survey_year": "2023",
             "species": "Walleye", "cpue_or_abundance_metric": "x", "cpue_value": "1",
             "notes": "", "source_pdf_url": ""},
        ])
        self._set_stocking([])
        with self.assertRaises(v1.AmbiguousLakeError):
            v1.get_species_presence("Fish Lake")

    def test_ambiguous_lake_name_resolved_with_county(self):
        self._set_survey([
            {"lake_name": "Fish Lake", "county": "Dane", "survey_year": "2021",
             "species": "Bluegill", "cpue_or_abundance_metric": "x", "cpue_value": "1",
             "notes": "", "source_pdf_url": ""},
            {"lake_name": "Fish Lake", "county": "Waushara", "survey_year": "2023",
             "species": "Walleye", "cpue_or_abundance_metric": "x", "cpue_value": "1",
             "notes": "", "source_pdf_url": ""},
        ])
        self._set_stocking([])
        presence = v1.get_species_presence("Fish Lake", county="Dane")
        self.assertEqual(presence["species"], ["BLUEGILL"])

    def test_blank_waterbody_stocking_rows_never_match(self):
        # Real bug: 813 real stocking rows have an empty waterbody field
        # (private-pond stocking). Before the fix, these matched every query.
        self._set_survey([])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "2020", "source_type": "PRIVATE STOCKING",
             "county": "Some County", "waterbody": "", "local_wb_name": "", "species": "FATHEAD MINNOW",
             "strain": "", "age_class": "", "number_stocked": "500", "avg_length_in": ""},
        ])
        presence = v1.get_species_presence("Lake Monona")
        self.assertEqual(presence["tier"], "no_data")


class TestWaterTemperatureLabeling(TempDataMixin, unittest.TestCase):
    def test_real_measurement_labeled_true(self):
        self._set_water_temp([
            {"lake_name": "Test Lake", "county": "Test County", "method": "clmn_recent",
             "value_c": "20.0", "value_f": "68.0", "is_real_water_measurement": "true",
             "retrieved_at": "2026-01-01", "source_url_or_station": "test station", "notes": ""},
        ])
        result = v1.get_current_temperature("Test Lake", live_refresh=False)
        self.assertTrue(result["is_real_water_measurement"])
        self.assertEqual(result["value_c"], 20.0)

    def test_proxy_measurement_labeled_false_and_cache_reason_explicit(self):
        self._set_water_temp([
            {"lake_name": "Test Lake", "county": "Test County", "method": "nws_air_proxy",
             "value_c": "18.0", "value_f": "64.4", "is_real_water_measurement": "false",
             "retrieved_at": "2026-01-01T00:00:00Z", "source_url_or_station": "test station",
             "notes": "lake coords 43.0,-89.0"},
        ])
        result = v1.get_current_temperature("Test Lake", live_refresh=False)
        self.assertFalse(result["is_real_water_measurement"])
        self.assertIn("--no-live-refresh", result["source"])

    def test_missing_lake_reports_no_data_not_silent_or_fabricated(self):
        # Part 2's explicit requirement: a waterbody with no real/proxy
        # source reports no_data honestly -- it must never raise past the
        # caller (which would abort the whole run) and must never invent
        # a plausible-looking value.
        self._set_water_temp([])
        result = v1.get_current_temperature("Nonexistent Lake", live_refresh=False)
        self.assertIsNone(result["value_c"])
        self.assertEqual(result["method"], "no_data")
        self.assertFalse(result["is_real_water_measurement"])


class TestNarrativeHonesty(TempDataMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._set_thresholds({
            "WALLEYE": {"diel_active": True, "thresholds": [
                {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75],
                 "description": "test range", "evidence": "test-tier"},
            ]},
        })

    def test_never_claims_catch_prediction(self):
        temp_info = {"value_c": 20.0, "is_real_water_measurement": True, "source": "x", "observed_at": "x"}
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        self.assertIn("not a catch prediction", narrative)
        self.assertNotIn("will bite", narrative)

    def test_stocking_only_carries_explicit_non_exhaustive_caveat(self):
        temp_info = {"value_c": 20.0, "is_real_water_measurement": False, "source": "x", "observed_at": "x"}
        presence = {"tier": "stocking_only", "species": ["WALLEYE"], "detail": {}}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        self.assertIn("NOT a complete species inventory", narrative)

    def test_no_data_tier_generates_no_species_section(self):
        temp_info = {"value_c": 20.0, "is_real_water_measurement": False, "source": "x", "observed_at": "x"}
        presence = {"tier": "no_data", "species": [], "detail": {}}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        self.assertIn("No species-presence data", narrative)
        self.assertNotIn("## Species notes", narrative)

    def test_diel_note_appears_for_diel_active_species(self):
        temp_info = {"value_c": 999.0, "is_real_water_measurement": True, "source": "x", "observed_at": "x"}
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        # Temp is far outside the activity window, but the diel note should
        # still appear since diel_active is independent of temperature.
        self.assertIn("low-light", narrative)

    def test_no_temperature_data_section_never_crashes_and_states_no_data(self):
        # Part 2: a waterbody with real species data but no temperature
        # source of any kind must still produce a valid narrative -- never
        # crash on a None value_c, never silently omit the gap.
        temp_info = dict(v1.NO_TEMPERATURE_DATA)
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}, "waterbody_type": "lake"}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        self.assertIn("No real or proxy water-temperature data is available", narrative)
        self.assertNotIn("## Species notes", narrative)  # can't compare temp to thresholds with no reading


class TestWaterbodyTypeClassification(unittest.TestCase):
    def test_river_and_creek_classified_as_stream(self):
        self.assertEqual(v1.classify_waterbody_type("Fox River"), "stream")
        self.assertEqual(v1.classify_waterbody_type("Prairie Brook"), "stream")
        self.assertEqual(v1.classify_waterbody_type("Adams Creek"), "stream")

    def test_lake_and_pond_classified_as_lake(self):
        self.assertEqual(v1.classify_waterbody_type("Devils Lake"), "lake")
        self.assertEqual(v1.classify_waterbody_type("Round Pond"), "lake")

    def test_flowage_overrides_river_keyword(self):
        # Real bug found this cycle: "Apple River Flowage" is a dammed,
        # lake-like impoundment despite containing "River" in its name --
        # without this override it was misclassified as a stream.
        self.assertEqual(v1.classify_waterbody_type("Apple River Flowage"), "lake")
        self.assertEqual(v1.classify_waterbody_type("Petenwell Flowage"), "lake")


class TestStockingOnlyFullStatewideCoverage(TempDataMixin, unittest.TestCase):
    """Part 1: stocking-only presence must be surfaced for ANY waterbody in
    the statewide pull, lake or stream -- not a hand-picked subset."""

    def test_stream_waterbody_gets_stocking_only_presence(self):
        self._set_survey([])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "2022", "source_type": "DNR",
             "county": "Waukesha", "waterbody": "OCONOMOWOC RIVER", "local_wb_name": "", "species": "BROWN TROUT",
             "strain": "", "age_class": "", "number_stocked": "500", "avg_length_in": ""},
        ])
        presence = v1.get_species_presence("Oconomowoc River", county="Waukesha")
        self.assertEqual(presence["tier"], "stocking_only")
        self.assertEqual(presence["waterbody_type"], "stream")
        self.assertEqual(presence["species"], ["BROWN TROUT"])

    def test_lake_and_stream_with_same_species_both_included_independently(self):
        self._set_survey([])
        self._set_stocking([
            {"source_url": "", "retrieval_date": "", "stocking_year": "2022", "source_type": "DNR",
             "county": "Test", "waterbody": "SOME LAKE", "local_wb_name": "", "species": "WALLEYE",
             "strain": "", "age_class": "", "number_stocked": "500", "avg_length_in": ""},
            {"source_url": "", "retrieval_date": "", "stocking_year": "2022", "source_type": "DNR",
             "county": "Test", "waterbody": "SOME CREEK", "local_wb_name": "", "species": "WALLEYE",
             "strain": "", "age_class": "", "number_stocked": "200", "avg_length_in": ""},
        ])
        lake_presence = v1.get_species_presence("Some Lake", county="Test")
        stream_presence = v1.get_species_presence("Some Creek", county="Test")
        self.assertEqual(lake_presence["waterbody_type"], "lake")
        self.assertEqual(stream_presence["waterbody_type"], "stream")


class TestRiverStreamPhysiologyCaveat(TempDataMixin, unittest.TestCase):
    """Part 5: lake-derived physiology thresholds must be explicitly
    flagged, not silently applied, when matched against a stream entry."""

    def setUp(self):
        super().setUp()
        self._set_thresholds({
            "WALLEYE": {"diel_active": False, "thresholds": [
                {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75],
                 "description": "lake preferendum study", "evidence": "test-tier"},
                {"type": "spawning_trigger", "range_c": [4.4, 11.1], "range_f": [40, 52],
                 "description": "spawning trigger", "evidence": "test-tier"},
            ]},
        })

    def test_activity_window_flagged_as_unverified_for_stream(self):
        temp_info = {"value_c": 20.0, "is_real_water_measurement": True, "source": "x", "observed_at": "x"}
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}, "waterbody_type": "stream"}
        narrative = v1.build_narrative("Test River", temp_info, presence, v1.load_thresholds())
        self.assertIn("River/stream caveat", narrative)
        self.assertIn("has not been verified to transfer", narrative)

    def test_activity_window_not_flagged_for_lake(self):
        temp_info = {"value_c": 20.0, "is_real_water_measurement": True, "source": "x", "observed_at": "x"}
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}, "waterbody_type": "lake"}
        narrative = v1.build_narrative("Test Lake", temp_info, presence, v1.load_thresholds())
        self.assertNotIn("River/stream caveat", narrative)

    def test_spawning_trigger_not_flagged_even_for_stream(self):
        # Spawning-trigger data is not assumed lake-specific in the same way
        # feeding/activity preferenda are (many species spawn in flowing
        # water) -- only feeding/growth-type thresholds get the caveat.
        temp_info = {"value_c": 7.0, "is_real_water_measurement": True, "source": "x", "observed_at": "x"}
        presence = {"tier": "survey_confirmed", "species": ["WALLEYE"], "detail": {}, "waterbody_type": "stream"}
        narrative = v1.build_narrative("Test River", temp_info, presence, v1.load_thresholds())
        self.assertIn("spawning-trigger range", narrative)
        self.assertNotIn("River/stream caveat", narrative)


class TestUsgsGenericSiteMatching(TempDataMixin, unittest.TestCase):
    def test_matches_stream_site_by_name(self):
        self._set_usgs_sites([
            {"site_no": "04073500", "station_nm": "FOX RIVER AT BERLIN, WI", "site_type": "ST",
             "lat": "43.96875", "lon": "-88.950306"},
            {"site_no": "05429000", "station_nm": "LAKE MONONA AT MADISON, WI", "site_type": "LK",
             "lat": "43.06", "lon": "-89.38"},
        ])
        matches = v1.find_usgs_site_matches("Fox River")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["site_no"], "04073500")

    def test_no_match_returns_empty_list_not_error(self):
        self._set_usgs_sites([])
        self.assertEqual(v1.find_usgs_site_matches("Nonexistent River"), [])

    def test_short_query_does_not_match_everything(self):
        self._set_usgs_sites([
            {"site_no": "1", "station_nm": "FOX RIVER AT BERLIN, WI", "site_type": "ST", "lat": "1", "lon": "1"},
        ])
        self.assertEqual(v1.find_usgs_site_matches("Fox"), [])  # too short to substring-match safely


class TestNoDataAcrossAllSources(TempDataMixin, unittest.TestCase):
    """Part 5: a waterbody with neither survey, nor stocking, nor any
    temperature source reports no_data cleanly on every axis -- no crash,
    no fabricated value, no silent omission."""

    def test_completely_unknown_waterbody(self):
        self._set_survey([])
        self._set_stocking([])
        self._set_water_temp([])
        self._set_usgs_sites([])
        presence = v1.get_species_presence("Nowhere Creek", county="Nowhere")
        temp_info = v1.get_current_temperature("Nowhere Creek", county="Nowhere", live_refresh=False)
        self.assertEqual(presence["tier"], "no_data")
        self.assertEqual(presence["waterbody_type"], "stream")
        self.assertIsNone(temp_info["value_c"])
        self.assertEqual(temp_info["method"], "no_data")
        # Must still render a coherent narrative, not raise.
        narrative = v1.build_narrative("Nowhere Creek", temp_info, presence, v1.load_thresholds())
        self.assertIn("No real or proxy water-temperature data", narrative)
        self.assertIn("No species-presence data", narrative)


if __name__ == "__main__":
    unittest.main()
