"""Tests for the WDNR regulation and consumption-advisory lookups.

These carry legal and health consequences, so the properties under test
are about refusing to guess rather than about formatting.
"""

import os
import sqlite3
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_fishing_regulations as regs  # noqa: E402


def _feature(name, wbic, **fields):
    attrs = {"WBIC": wbic, "WATERBODY_NAME": name}
    attrs.update(fields)
    return {"attributes": attrs}


class TestRegulationShaping(unittest.TestCase):
    def test_single_water_resolves(self):
        shaped = regs._shape([_feature("Devils Lake", 980900, WALLEYE="15 inch minimum")])
        self.assertEqual(shaped["status"], "ok")
        self.assertEqual(shaped["waters"][0]["wbic"], 980900)

    def test_two_waters_in_range_refuses_to_choose(self):
        # Wisconsin has eleven waters called "Devils Lake" with different
        # rules. Picking one would be the citation-causing failure.
        shaped = regs._shape([
            _feature("Devils Lake", 139000, NORTHERN_PIKE="bag limit 2"),
            _feature("Mud Lake", 525200, NORTHERN_PIKE="bag limit 5"),
        ])
        self.assertEqual(shaped["status"], "ambiguous")
        self.assertEqual(len(shaped["waters"]), 2)

    def test_no_coverage_is_none_not_a_fabricated_default(self):
        self.assertEqual(regs._shape([])["status"], "none")

    def test_features_without_any_rule_text_are_not_reported_as_ok(self):
        shaped = regs._shape([_feature("Empty Lake", 1)])
        self.assertEqual(shaped["status"], "none")


class TestRegulationLookup(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def test_result_is_cached_rather_than_refetched(self):
        payload = [_feature("Devils Lake", 980900, WALLEYE="15 inch minimum")]
        with mock.patch.object(regs, "_query_service", return_value=payload) as q:
            first = regs.get_regulations(self.conn, 43.4263, -89.7281)
            second = regs.get_regulations(self.conn, 43.4263, -89.7281)
        self.assertEqual(q.call_count, 1)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "ok")

    def test_service_failure_with_no_cache_returns_none(self):
        with mock.patch.object(regs, "_query_service", side_effect=OSError("down")):
            self.assertIsNone(regs.get_regulations(self.conn, 44.0, -90.0))

    def test_service_failure_falls_back_to_stale_cache_and_flags_it(self):
        payload = [_feature("Devils Lake", 980900, WALLEYE="15 inch minimum")]
        with mock.patch.object(regs, "_query_service", return_value=payload):
            regs.get_regulations(self.conn, 43.4263, -89.7281)
        # Force the cached row to look old, then fail the live call.
        self.conn.execute("UPDATE regulation_cache SET fetched_at = '2020-01-01T00:00:00+00:00'")
        self.conn.commit()
        with mock.patch.object(regs, "_query_service", side_effect=OSError("down")):
            result = regs.get_regulations(self.conn, 43.4263, -89.7281)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["stale"])

    def test_missing_coordinates_return_none(self):
        self.assertIsNone(regs.get_regulations(self.conn, None, None))


class TestConsumptionAdvisory(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def test_audiences_are_kept_separate(self):
        # The limits genuinely differ: large walleye is one-meal-per-month
        # for most people and do-not-eat for women and children. Merging
        # them would be harmful.
        payload = {"features": [{"attributes": {
            "WATERBODY_NAME": "Sand Lake",
            "CONSUMPTION_JSON": (
                '[{"group_type":"O","one_meal_per_month":"Walleye"},'
                ' {"group_type":"S","do_not_eat":"Walleye"}]'
            ),
        }}]}

        class FakeResponse:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *a):
                return False
            def read(self_inner):
                import json
                return json.dumps(payload).encode()

        with mock.patch.object(regs.urllib.request, "urlopen", return_value=FakeResponse()):
            result = regs.get_consumption_advisory(self.conn, 45.29, -91.36)

        self.assertEqual(result["status"], "site_specific")
        audiences = [g["audience"] for g in result["waters"][0]["groups"]]
        self.assertIn("Most people", audiences)
        self.assertIn("Women of childbearing age and children under 15", audiences)

    def test_water_without_a_site_advisory_reports_statewide_not_nothing(self):
        class FakeResponse:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *a):
                return False
            def read(self_inner):
                return b'{"features": []}'

        with mock.patch.object(regs.urllib.request, "urlopen", return_value=FakeResponse()):
            result = regs.get_consumption_advisory(self.conn, 44.0, -90.0)
        # "No site-specific advisory" is not "no advice applies" -- the
        # statewide advisory still covers every Wisconsin water.
        self.assertEqual(result["status"], "statewide")


class TestDuplicateWatersAreMergedNotRefused(unittest.TestCase):
    """Two records for the same water (e.g. two "Lake Michigan" rows with identical rules)
    are one water, not an ambiguity. Genuinely different waters are all returned so the
    page can show each one's rules; none is picked for the visitor."""

    @staticmethod
    def feature(name, wbic, text):
        return {"attributes": {"WBIC": wbic, "WATERBODY_NAME": name, "ALL_SPECIES": text}}

    def test_identical_duplicates_collapse_to_one_water(self):
        shaped = regs._shape([self.feature("Lake Michigan", 1, "Daily bag 5"), self.feature("Lake Michigan", 2, "Daily bag 5")])
        self.assertEqual(shaped["status"], "ok")
        self.assertEqual(len(shaped["waters"]), 1)

    def test_different_rules_for_the_same_name_are_kept_apart(self):
        shaped = regs._shape([self.feature("Lake Michigan", 1, "Daily bag 5"), self.feature("Lake Michigan", 2, "Daily bag 3")])
        self.assertEqual(shaped["status"], "ambiguous")
        self.assertEqual(len(shaped["waters"]), 2)

    def test_different_waters_are_all_returned(self):
        shaped = regs._shape([self.feature("Big Lake", 1, "Daily bag 5"), self.feature("Little Creek", 2, "Daily bag 2")])
        self.assertEqual(shaped["status"], "ambiguous")
        self.assertEqual({w["waterbody_name"] for w in shaped["waters"]}, {"Big Lake", "Little Creek"})

    def test_an_old_cached_row_is_merged_on_read(self):
        old = {"status": "ambiguous", "waters": [
            {"wbic": 1, "waterbody_name": "Lake Michigan", "rules": [{"label": "All species", "text": "x"}]},
            {"wbic": 2, "waterbody_name": "Lake Michigan", "rules": [{"label": "All species", "text": "x"}]}]}
        self.assertEqual(regs._normalise(old)["status"], "ok")

    def test_nothing_matched_stays_none(self):
        self.assertEqual(regs._shape([])["status"], "none")


if __name__ == "__main__":
    unittest.main()
