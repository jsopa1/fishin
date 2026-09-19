"""Unit tests for the Fish Detail data assembly (ui/v4_species_detail.py).

Runs against the committed research files (no database, no network).

Run: python -m pytest ui/tests/test_v4_species_detail.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "analysis"))

import v4_species_detail as sd  # noqa: E402


class TestSlugs(unittest.TestCase):
    def test_slug_round_trips_for_every_species(self):
        for s in sd.list_species():
            self.assertEqual(sd.species_from_slug(s["slug"]), s["name"])

    def test_unknown_or_empty_slug_is_none(self):
        self.assertIsNone(sd.species_from_slug("dragon"))
        self.assertIsNone(sd.species_from_slug(""))
        self.assertIsNone(sd.species_from_slug(None))

    def test_there_are_27_species(self):
        self.assertEqual(len(sd.list_species()), 27)


class TestBaitOrdering(unittest.TestCase):
    CATALOG = {"a": {}, "b": {}, "c": {}}

    def _link(self, bait_id, tier, rank, urls):
        return {"bait_id": bait_id, "tier": tier, "rank": rank, "sources": [{"url": u} for u in urls]}

    def test_stronger_tier_first_then_more_sources_then_rank(self):
        links = [
            self._link("a", "agency-tier", 1, ["u1"]),
            self._link("b", "well-established", 9, ["u1", "u2"]),
            self._link("c", "agency-tier", 2, ["u1", "u2"]),
        ]
        self.assertEqual([l["bait_id"] for l in sd.order_baits(links, self.CATALOG)], ["b", "c", "a"])

    def test_order_is_deterministic_regardless_of_input_order(self):
        links = [self._link("a", "agency-tier", 1, ["u"]), self._link("b", "agency-tier", 2, ["u"]), self._link("c", "agency-tier", 3, ["u"])]
        forward = [l["bait_id"] for l in sd.order_baits(links, self.CATALOG)]
        backward = [l["bait_id"] for l in sd.order_baits(list(reversed(links)), self.CATALOG)]
        self.assertEqual(forward, backward)

    def test_links_to_unknown_baits_are_dropped_not_crashed_on(self):
        links = [self._link("zzz", "agency-tier", 1, ["u"])]
        self.assertEqual(sd.order_baits(links, self.CATALOG), [])


class TestSpeciesDetail(unittest.TestCase):
    def test_unknown_species_is_none(self):
        self.assertIsNone(sd.get_species_detail("Unicorn"))

    def test_every_species_assembles(self):
        for s in sd.list_species():
            d = sd.get_species_detail(s["name"])
            self.assertIsNotNone(d, s["name"])
            self.assertTrue(d["thresholds"], s["name"])

    def test_angling_targets_with_baits_have_cards_in_a_stable_order(self):
        first = [b["id"] for b in sd.get_species_detail("WALLEYE")["baits"]]
        second = [b["id"] for b in sd.get_species_detail("WALLEYE")["baits"]]
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first), 5)

    def test_non_targets_get_no_baits_or_technique(self):
        for name in ("WHITE SUCKER", "FATHEAD MINNOW"):
            d = sd.get_species_detail(name)
            self.assertFalse(d["angling_target"], name)
            self.assertEqual(d["baits"], [], name)
            self.assertEqual(d["technique"], [], name)
            self.assertTrue(d["not_target_reason"], name)

    def test_species_whose_source_names_no_bait_says_why(self):
        # Cisco: the agency page consulted has no angling content at all.
        d = sd.get_species_detail("CISCO")
        self.assertEqual(d["baits"], [])
        self.assertTrue(d["no_baits_reason"])

    def test_lake_whitefish_baits_come_from_the_minnesota_dna_profile_and_say_where(self):
        d = sd.get_species_detail("LAKE WHITEFISH")
        self.assertGreaterEqual(len(d["baits"]), 4)
        self.assertEqual(d["baits"][0]["id"], "minnows_crappie")
        for b in d["baits"]:
            self.assertEqual(b["tier"]["key"], "agency-tier")
            self.assertTrue(any("minnesota" in s["citation"].lower() for s in b["sources"]), b["id"])
            self.assertTrue(any("no Wisconsin-specific" in s["citation"] for s in b["sources"]), b["id"])

    def test_unreviewed_regulation_is_never_presented_as_cleared(self):
        frogs = next(b for b in sd.get_species_detail("CHANNEL CATFISH")["baits"] if b["id"] == "frogs")
        self.assertFalse(frogs["regulation"]["reviewed"])
        self.assertIn("have not been reviewed", frogs["regulation"]["text"])

    def test_a_reviewed_regulation_carries_its_sources(self):
        leech = next(b for b in sd.get_species_detail("WALLEYE")["baits"] if b["id"] == "leeches")
        self.assertTrue(leech["regulation"]["reviewed"])
        self.assertTrue(leech["regulation"]["sources"])

    def test_every_bait_card_carries_a_source_and_a_regulation_status(self):
        for s in sd.list_species():
            for b in sd.get_species_detail(s["name"])["baits"]:
                self.assertTrue(b["sources"], f"{s['name']}/{b['id']}")
                self.assertIn("reviewed", b["regulation"])
                self.assertTrue(b["how_to_use"].strip())

    def test_spawning_range_is_reported_when_the_temperature_is_inside_it(self):
        # Bluegill at 20C (68F): feeding window is 85-88F, spawning range is 65-80F.
        d = sd.get_species_detail("BLUEGILL", temp_c=20.0)
        self.assertFalse(d["current"]["inside_window"])
        self.assertEqual(d["spawning_now"], [65, 80])
        self.assertIsNone(sd.get_species_detail("BLUEGILL", temp_c=5.0)["spawning_now"])
        self.assertIsNone(sd.get_species_detail("BLUEGILL")["spawning_now"])

    def test_current_state_is_only_computed_when_a_temperature_is_given(self):
        self.assertIsNone(sd.get_species_detail("WALLEYE")["current"])
        self.assertIsNotNone(sd.get_species_detail("WALLEYE", temp_c=20.0)["current"])


class TestImages(unittest.TestCase):
    def test_a_species_image_carries_credit_license_and_source_page(self):
        img = sd.get_species_detail("WALLEYE")["image"]
        self.assertIn("Public domain", img["credit"])
        self.assertTrue(img["page_url"].startswith("https://commons.wikimedia.org/"))

    def test_a_bait_with_no_verified_image_has_none(self):
        self.assertIsNone(sd.image_for("baits", "leeches"))

    def test_bait_fish_reuse_the_species_image_and_say_so(self):
        img = sd.image_for("baits", "minnows_live")
        self.assertIsNotNone(img)
        self.assertIn("not a picture of a packaged bait", img["note"])

    def test_fly_baits_share_one_generic_photo(self):
        a = sd.image_for("baits", "wet_dry_flies")
        b = sd.image_for("baits", "streamer_flies_poppers")
        self.assertEqual(a["static_path"], b["static_path"])


class TestThresholdDescription(unittest.TestCase):
    def test_range_and_peak_render_in_both_units(self):
        d = sd.describe_threshold({"type": "spawning_trigger", "range_c": [4.4, 11.1], "range_f": [40, 52], "peak_range_f": [44, 48], "evidence": "agency-tier"})
        self.assertIn("40-52°F", d["value"])
        self.assertIn("peak 44-48", d["value"])
        self.assertEqual(d["label"], "Spawning range")

    def test_avoidance_threshold_reads_as_above(self):
        d = sd.describe_threshold({"type": "avoidance_above", "threshold_c": 25.0, "threshold_f": 77, "evidence": "agency-tier"})
        self.assertIn("above 77", d["value"])


if __name__ == "__main__":
    unittest.main()
