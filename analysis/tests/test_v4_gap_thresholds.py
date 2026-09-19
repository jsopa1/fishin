"""The V4 gap-fill temperature windows (Pumpkinseed, Channel Catfish, Burbot).

The point of these tests is the standing rule that no window rests on a number
that is not in its source: every quote is re-checked against the source text on
every test run, and the numbers in each window are re-derived from the quotes.

Run: python -m pytest analysis/tests/test_v4_gap_thresholds.py
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[2] / "ui"))

import v4_add_gap_thresholds as builder  # noqa: E402
import v1_review_data as data  # noqa: E402

THRESHOLDS = json.loads(builder.THRESHOLDS.read_text(encoding="utf-8"))["species"]
SOURCE_LINES = builder.SOURCE.read_text(encoding="utf-8", errors="replace").split(chr(10))
SPECIES = ("PUMPKINSEED", "CHANNEL CATFISH", "BURBOT")


def added(species):
    return [t for t in THRESHOLDS[species]["thresholds"] if t.get("added_by") == builder.TAG]


class VerbatimTests(unittest.TestCase):
    def test_every_species_has_exactly_one_added_window(self):
        for s in SPECIES:
            self.assertEqual(len(added(s)), 1, s)

    def test_every_quote_is_found_in_its_stated_lines_of_the_source(self):
        for s in SPECIES:
            for src in added(s)[0]["sources"]:
                first, last = src["lines"]
                haystack = builder.normalise(" ".join(SOURCE_LINES[first - 1:last]))
                self.assertIn(builder.normalise(src["quote"]), haystack, f"{s}: {src['quote']}")

    def test_the_data_file_matches_what_the_builder_would_write(self):
        for s in SPECIES:
            entry = builder.ENTRIES[s]
            got = added(s)[0]
            self.assertEqual(got["range_c"], entry["range_c"], s)
            self.assertEqual(got["type"], entry["type"], s)
            self.assertEqual(got["evidence"], entry["evidence"], s)

    def test_the_window_numbers_are_the_numbers_in_the_quotes(self):
        # Pumpkinseed 27-32: the quotes carry 28.5-32, 27.7 and 27-29.
        quotes = " ".join(s["quote"] for s in added("PUMPKINSEED")[0]["sources"])
        self.assertIn("28.5-32", quotes)
        self.assertIn("27.7", quotes)
        self.assertIn("27-29", quotes)
        # Catfish 28-30 and Burbot 15.6-18.3 appear verbatim.
        self.assertIn("28-30", " ".join(s["quote"] for s in added("CHANNEL CATFISH")[0]["sources"]))
        self.assertIn("15.6-18.3", " ".join(s["quote"] for s in added("BURBOT")[0]["sources"]))

    def test_the_stated_range_is_the_envelope_of_the_quoted_values_and_nothing_wider(self):
        nums = [float(x) for x in re.findall(r"\d+\.?\d*", " ".join(s["quote"] for s in added("PUMPKINSEED")[0]["sources"]))
                if 20 < float(x) < 40]
        low, high = added("PUMPKINSEED")[0]["range_c"]
        self.assertLessEqual(low, min(nums))
        self.assertGreaterEqual(high, max(nums))
        self.assertLessEqual(low, 27.0 + 1e-9)
        self.assertLessEqual(high - max(nums), 1e-9)

    def test_fahrenheit_is_consistent_with_celsius(self):
        for s in SPECIES:
            t = added(s)[0]
            for c, f in zip(t["range_c"], t["range_f"]):
                self.assertAlmostEqual(c * 9 / 5 + 32, f, delta=0.06)

    def test_evidence_labels_are_from_the_existing_vocabulary(self):
        for s in SPECIES:
            self.assertRegex(added(s)[0]["evidence"], r"^(well-established|agency-tier)")

    def test_the_descriptions_disclose_what_the_source_does_not_cover(self):
        self.assertIn("not measured in Wisconsin", added("CHANNEL CATFISH")[0]["description"])
        self.assertIn("empty in the compilation", added("BURBOT")[0]["description"])
        self.assertIn("not used", added("PUMPKINSEED")[0]["description"])

    def test_the_builder_aborts_rather_than_write_an_unverifiable_quote(self):
        bad = {"PUMPKINSEED": dict(builder.ENTRIES["PUMPKINSEED"], sources=[{"lines": [8339, 8397], "quote": "large D 99.9-100 Nowhere"}])}
        self.assertTrue(builder.verify(bad, SOURCE_LINES))

    def test_the_species_deliberately_left_out_stay_out(self):
        for s in ("CISCO", "FATHEAD MINNOW", "LAKE STURGEON"):
            self.assertEqual(added(s), [], s)


class EffectTests(unittest.TestCase):
    def test_spawning_ranges_are_untouched(self):
        for s in SPECIES:
            self.assertTrue([t for t in THRESHOLDS[s]["thresholds"] if t["type"] == "spawning_trigger"], s)

    def test_each_species_now_has_a_window_that_the_spot_math_uses(self):
        for s, inside_c in (("PUMPKINSEED", 29.0), ("CHANNEL CATFISH", 29.0), ("BURBOT", 17.0)):
            act = data._activity_for_species(s, inside_c)
            self.assertIsNotNone(act, s)
            self.assertTrue(act["inside_window"], s)
            self.assertIn("Currently", act["short_text"])

    def test_outside_the_window_the_distance_is_reported(self):
        act = data._activity_for_species("PUMPKINSEED", 20.0)
        self.assertFalse(act["inside_window"])
        self.assertEqual(act["direction"], "below")
        self.assertAlmostEqual(act["distance_f"], 12.6, delta=0.1)

    def test_a_window_no_longer_leaves_these_species_in_the_no_window_bucket(self):
        cats = {"confirmed_sightings": [{"species": "PUMPKINSEED", "sources": ["x"], "activity": data._activity_for_species("PUMPKINSEED", 15.0)}],
                "likely_species": []}
        out = data.bucket_species_by_activity(cats, 15.0)
        self.assertEqual(out["no_window"], [])
        self.assertEqual([r["species"] for r in out["inactive"]], ["PUMPKINSEED"])


if __name__ == "__main__":
    unittest.main()
