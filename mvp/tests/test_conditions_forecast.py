"""Deterministic unit tests for the MVP conditions-forecast narrative logic.

Focus: describe_threshold_match() and build_narrative() -- the pure logic
that turns a temperature value + physiology thresholds + stocking records
into narrative text. No network calls, no live data; all inputs are
hand-constructed. The live-data fetch functions (WDNR stocking API, NDBC
buoy, NWS observations) are exercised manually against the real APIs, not
unit-tested here, since mocking them would not verify anything about the
live services themselves.

Run: python -m unittest mvp/tests/test_conditions_forecast.py
     (or: python -m pytest mvp/tests/test_conditions_forecast.py)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conditions_forecast import (  # noqa: E402
    build_narrative,
    c_to_f,
    describe_threshold_match,
    load_thresholds,
)


class TestCToF(unittest.TestCase):
    def test_freezing(self):
        self.assertAlmostEqual(c_to_f(0), 32.0)

    def test_boiling(self):
        self.assertAlmostEqual(c_to_f(100), 212.0)

    def test_known_field_value(self):
        # Walleye WI field preference point, 20.6C, should be ~69.1F
        self.assertAlmostEqual(c_to_f(20.6), 69.08, places=1)


class TestDescribeThresholdMatch(unittest.TestCase):
    def test_range_in_bounds(self):
        threshold = {
            "type": "activity_window",
            "range_c": [12.8, 23.9],
            "range_f": [55, 75],
            "description": "test range",
        }
        result = describe_threshold_match(20.0, threshold)
        self.assertIsNotNone(result)
        self.assertIn("activity/feeding-temperature window", result)

    def test_range_out_of_bounds_below(self):
        threshold = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNone(describe_threshold_match(5.0, threshold))

    def test_range_out_of_bounds_above(self):
        threshold = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNone(describe_threshold_match(30.0, threshold))

    def test_range_boundary_inclusive(self):
        threshold = {"type": "activity_window", "range_c": [12.8, 23.9], "range_f": [55, 75], "description": "x"}
        self.assertIsNotNone(describe_threshold_match(12.8, threshold))
        self.assertIsNotNone(describe_threshold_match(23.9, threshold))

    def test_peak_sub_range_noted(self):
        threshold = {
            "type": "spawning_trigger",
            "range_c": [4.4, 11.1],
            "range_f": [40, 52],
            "peak_range_c": [6.7, 8.9],
            "peak_range_f": [44, 48],
            "description": "spawning window",
        }
        result = describe_threshold_match(7.5, threshold)
        self.assertIn("peak sub-range", result)

    def test_peak_sub_range_not_noted_outside_peak(self):
        threshold = {
            "type": "spawning_trigger",
            "range_c": [4.4, 11.1],
            "range_f": [40, 52],
            "peak_range_c": [6.7, 8.9],
            "peak_range_f": [44, 48],
            "description": "spawning window",
        }
        result = describe_threshold_match(5.0, threshold)
        self.assertIsNotNone(result)
        self.assertNotIn("peak sub-range", result)

    def test_reduced_feeding_below_triggers_under_threshold(self):
        threshold = {"type": "reduced_feeding_below", "threshold_c": 10.0, "threshold_f": 50, "description": "x"}
        self.assertIsNotNone(describe_threshold_match(9.0, threshold))

    def test_reduced_feeding_below_does_not_trigger_at_or_above(self):
        threshold = {"type": "reduced_feeding_below", "threshold_c": 10.0, "threshold_f": 50, "description": "x"}
        self.assertIsNone(describe_threshold_match(10.0, threshold))
        self.assertIsNone(describe_threshold_match(15.0, threshold))

    def test_avoidance_above_triggers_over_threshold(self):
        threshold = {"type": "avoidance_above", "threshold_c": 23.9, "threshold_f": 75, "description": "x"}
        self.assertIsNotNone(describe_threshold_match(25.0, threshold))

    def test_avoidance_above_does_not_trigger_at_or_below(self):
        threshold = {"type": "avoidance_above", "threshold_c": 23.9, "threshold_f": 75, "description": "x"}
        self.assertIsNone(describe_threshold_match(23.9, threshold))
        self.assertIsNone(describe_threshold_match(20.0, threshold))

    def test_preferred_point_within_tolerance(self):
        threshold = {"type": "activity_window", "preferred_point_c": 20.6, "preferred_point_f": 69.1, "description": "x"}
        self.assertIsNotNone(describe_threshold_match(21.5, threshold))  # 0.9C away
        self.assertIsNotNone(describe_threshold_match(19.5, threshold))  # 1.1C away

    def test_preferred_point_outside_tolerance(self):
        threshold = {"type": "activity_window", "preferred_point_c": 20.6, "preferred_point_f": 69.1, "description": "x"}
        self.assertIsNone(describe_threshold_match(25.0, threshold))
        self.assertIsNone(describe_threshold_match(15.0, threshold))


class TestLoadThresholds(unittest.TestCase):
    def test_loads_and_has_expected_species(self):
        thresholds = load_thresholds()
        self.assertIn("species", thresholds)
        for expected_species in ("WALLEYE", "YELLOW PERCH", "NORTHERN PIKE", "CHINOOK SALMON"):
            self.assertIn(expected_species, thresholds["species"])

    def test_walleye_diel_light_deliberately_excluded(self):
        # Candidate #1 (diel/light-window feeding) is the best-evidenced
        # physiology candidate in the research doc but requires a
        # time-of-day input this MVP doesn't compute -- it must not be
        # silently present as a temperature-only threshold.
        thresholds = load_thresholds()
        walleye_types = {t["type"] for t in thresholds["species"]["WALLEYE"]}
        self.assertNotIn("diel_light_window", walleye_types)
        self.assertIn("WALLEYE_DIEL_LIGHT", thresholds["_excluded"])


class TestBuildNarrative(unittest.TestCase):
    def setUp(self):
        self.thresholds = load_thresholds()

    def test_no_stocking_record_short_circuits(self):
        temp_info = {"value_c": 20.0, "is_water_measurement": False, "source": "test", "observed_at": "test"}
        narrative = build_narrative("Test Lake", "Test County", temp_info, [], self.thresholds)
        self.assertIn("No WDNR stocking record was found", narrative)
        self.assertNotIn("## Species notes", narrative)

    def test_matching_species_produces_species_section(self):
        temp_info = {"value_c": 20.6, "is_water_measurement": True, "source": "test buoy", "observed_at": "test"}
        narrative = build_narrative(
            "Test Lake", "Test County", temp_info, [("WALLEYE", 2020)], self.thresholds
        )
        self.assertIn("### Walleye", narrative)
        self.assertIn("Evidence quality", narrative)

    def test_never_claims_catch_prediction(self):
        # Decision #005/#012: this tool must never read as a catch-rate
        # prediction. Assert the required disclaimer is always present,
        # regardless of match outcome.
        temp_info = {"value_c": 20.6, "is_water_measurement": True, "source": "test", "observed_at": "test"}
        narrative = build_narrative(
            "Test Lake", "Test County", temp_info, [("WALLEYE", 2020)], self.thresholds
        )
        self.assertIn("not a catch prediction", narrative)
        self.assertNotIn("will bite", narrative)

    def test_non_matching_species_falls_through_to_no_match_message(self):
        # Chinook prefers ~11.7C; 25C should not match anything.
        temp_info = {"value_c": 25.0, "is_water_measurement": True, "source": "test", "observed_at": "test"}
        narrative = build_narrative(
            "Test Lake", "Test County", temp_info, [("CHINOOK SALMON", 2020)], self.thresholds
        )
        self.assertIn("No species confirmed present", narrative)

    def test_unknown_species_without_reference_data_is_skipped_not_error(self):
        temp_info = {"value_c": 20.0, "is_water_measurement": True, "source": "test", "observed_at": "test"}
        # Should not raise even though "CARP" has no threshold entries.
        narrative = build_narrative(
            "Test Lake", "Test County", temp_info, [("CARP", 2020)], self.thresholds
        )
        self.assertIn("No species confirmed present", narrative)

    def test_air_temperature_proxy_labeled_explicitly(self):
        temp_info = {"value_c": 20.0, "is_water_measurement": False, "source": "test", "observed_at": "test"}
        narrative = build_narrative("Test Lake", "Test County", temp_info, [], self.thresholds)
        self.assertIn("PROXY, not a direct water-temperature measurement", narrative)

    def test_real_water_measurement_labeled_explicitly(self):
        temp_info = {"value_c": 20.0, "is_water_measurement": True, "source": "test", "observed_at": "test"}
        narrative = build_narrative("Test Lake", "Test County", temp_info, [], self.thresholds)
        self.assertIn("a real, current water-temperature measurement", narrative)


if __name__ == "__main__":
    unittest.main()
