"""Schema and honesty guards for the V4 habitat/bait research data.

Enforces the rules in docs/v4_ux_goal_loop_spec.md Phase 0: every claim has
a real citation, verbatim quote and allowed tier; every bait link points at
a catalog item; every catalog item has a Wisconsin regulation note or an
explicit NOT_YET_RESEARCHED reason. Coverage of all 27 species is checked
separately (test_all_species_covered) and is expected to fail until the
research batches finish -- it is marked as an expected failure until then.
"""

import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "v1"
TIERS = {"well-established", "agency-tier", "single-source-speculative"}
STATES = {"in_activity_window", "below_activity_window", "in_spawning_trigger", "above_avoidance"}


def _load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


class TestHabitatReference(unittest.TestCase):
    def setUp(self):
        self.data = _load("habitat_reference_v1.json")

    def test_every_claim_is_cited_quoted_and_tiered(self):
        for species, entry in self.data["species"].items():
            for claim in entry.get("claims", []):
                cid = claim["id"]
                self.assertIn(claim["tier"], TIERS, cid)
                self.assertTrue(claim["text"].strip(), cid)
                self.assertIsInstance(claim["wi_applicable"], bool, cid)
                self.assertTrue(claim["sources"], f"{cid}: no sources")
                for src in claim["sources"]:
                    self.assertTrue(src["citation"].strip(), cid)
                    self.assertTrue(src["url"].startswith("http"), cid)
                    self.assertTrue(src["quote"].strip(), f"{cid}: no verbatim quote")
                    self.assertTrue(src["retrieved"], cid)

    def test_claim_ids_are_unique(self):
        ids = [c["id"] for e in self.data["species"].values() for c in e.get("claims", [])]
        self.assertEqual(len(ids), len(set(ids)))

    def test_well_established_needs_two_independent_sources(self):
        for entry in self.data["species"].values():
            for claim in entry.get("claims", []):
                if claim["tier"] == "well-established":
                    urls = {s["url"] for s in claim["sources"]}
                    self.assertGreaterEqual(len(urls), 2, claim["id"])

    def test_each_species_has_claims_or_an_explicit_reason(self):
        for species, entry in self.data["species"].items():
            self.assertIn("angling_target", entry, species)
            self.assertTrue(entry.get("claims") or entry.get("not_documented_reason"), species)


class TestBaitData(unittest.TestCase):
    def setUp(self):
        self.catalog = _load("bait_catalog_v1.json")["baits"]
        self.map = _load("species_bait_map_v1.json")["species"]

    def test_every_bait_has_a_regulation_note(self):
        for bid, bait in self.catalog.items():
            note = bait.get("wi_regulation_note", "")
            self.assertTrue(note.strip(), bid)
            if note.startswith("NOT_YET_RESEARCHED"):
                self.assertIn(":", note, f"{bid}: needs a reason after NOT_YET_RESEARCHED")

    def test_every_link_points_at_a_real_bait_and_is_cited(self):
        for species, entry in self.map.items():
            for link in entry.get("links", []):
                self.assertIn(link["bait_id"], self.catalog, species)
                self.assertIn(link["tier"], TIERS, species)
                self.assertTrue(set(link["states"]) <= STATES, species)
                self.assertTrue(link["sources"], f"{species}/{link['bait_id']}")
                for src in link["sources"]:
                    self.assertTrue(src["quote"].strip())
                    self.assertTrue(src["url"].startswith("http"))

    def test_ranks_are_unique_per_species(self):
        for species, entry in self.map.items():
            ranks = [l["rank"] for l in entry.get("links", [])]
            self.assertEqual(len(ranks), len(set(ranks)), species)

    def test_non_targets_have_no_invented_baits(self):
        for species, entry in self.map.items():
            if not entry.get("angling_target", True):
                self.assertEqual(entry.get("links", []), [], species)


class TestCoverage(unittest.TestCase):
    @unittest.expectedFailure
    def test_all_species_covered(self):
        physiology = set(_load("physiology_thresholds_v1.json")["species"])
        habitat = set(_load("habitat_reference_v1.json")["species"])
        baits = set(_load("species_bait_map_v1.json")["species"])
        self.assertEqual(physiology - habitat, set())
        self.assertEqual(physiology - baits, set())


if __name__ == "__main__":
    unittest.main()
