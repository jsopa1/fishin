"""Tests for bait/technique guidance resolution.

The property that matters most here is the separation of claim types: the
biological basis is cited physiology, the angling application is
convention, and the module must never let the second be presented as the
first (Decision #005).
"""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v1_bait_technique as bt  # noqa: E402
import v1_conditions_biology_forecast as v1  # noqa: E402


WALLEYE_THRESHOLDS = [
    {"type": "activity_window", "range_c": [12.8, 23.9]},
    {"type": "spawning_trigger", "range_c": [4.4, 11.1]},
]


class TestStateResolution(unittest.TestCase):
    def test_inside_activity_window(self):
        self.assertEqual(bt.resolve_state(WALLEYE_THRESHOLDS, 18.0), "in_activity_window")

    def test_inside_spawning_trigger(self):
        self.assertEqual(bt.resolve_state(WALLEYE_THRESHOLDS, 7.0), "in_spawning_trigger")

    def test_below_everything_is_below_activity_window(self):
        self.assertEqual(bt.resolve_state(WALLEYE_THRESHOLDS, 1.0), "below_activity_window")

    def test_avoidance_outranks_activity_window(self):
        # A fish actively leaving water this warm is not "feeding normally"
        # just because the number also falls inside its activity range.
        thresholds = [
            {"type": "activity_window", "range_c": [10.0, 30.0]},
            {"type": "avoidance_above", "value_c": 25.0},
        ]
        self.assertEqual(bt.resolve_state(thresholds, 27.0), "above_avoidance")

    def test_spawning_outranks_activity_window(self):
        thresholds = [
            {"type": "activity_window", "range_c": [5.0, 25.0]},
            {"type": "spawning_trigger", "range_c": [6.0, 9.0]},
        ]
        self.assertEqual(bt.resolve_state(thresholds, 7.0), "in_spawning_trigger")

    def test_no_temperature_gives_no_state(self):
        self.assertIsNone(bt.resolve_state(WALLEYE_THRESHOLDS, None))

    def test_no_thresholds_gives_no_state(self):
        self.assertIsNone(bt.resolve_state([], 15.0))

    def test_species_with_only_a_spawning_trigger_is_not_called_cold(self):
        # Without a documented activity window there is nothing to be
        # "below", so the honest answer is no state rather than a guess.
        thresholds = [{"type": "spawning_trigger", "range_c": [10.0, 14.0]}]
        self.assertIsNone(bt.resolve_state(thresholds, 2.0))


class TestGuidance(unittest.TestCase):
    def test_species_specific_guidance_is_used_when_present(self):
        g = bt.get_guidance("WALLEYE", WALLEYE_THRESHOLDS, 18.0)
        self.assertTrue(g["is_species_specific"])
        self.assertIn("jig", g["angling_application"].lower())

    def test_unknown_species_still_gets_the_general_physiology(self):
        # The physiology holds regardless of which fish it is, so a species
        # without its own entry gets the general guidance, not nothing.
        g = bt.get_guidance("BURBOT", WALLEYE_THRESHOLDS, 2.0)
        self.assertIsNotNone(g)
        self.assertFalse(g["is_species_specific"])
        self.assertIn("metabolic", g["biological_basis"].lower())

    def test_cold_water_guidance_explains_the_mechanism_not_just_the_lure(self):
        g = bt.get_guidance("WALLEYE", WALLEYE_THRESHOLDS, 3.0)
        self.assertEqual(g["state"], "below_activity_window")
        self.assertTrue(len(g["biological_basis"]) > 60)

    def test_application_is_never_labelled_as_research(self):
        # The whole point of the split: technique is convention, and must
        # never inherit the evidence tier of the physiology behind it.
        for temp in (3.0, 18.0, 7.0):
            g = bt.get_guidance("WALLEYE", WALLEYE_THRESHOLDS, temp)
            self.assertEqual(g["application_evidence_tier"], "angling-convention")
            self.assertIn(g["basis_evidence_tier"], ("well-established", "agency-tier"))

    def test_no_guidance_without_a_resolvable_state(self):
        self.assertIsNone(bt.get_guidance("WALLEYE", WALLEYE_THRESHOLDS, None))


class TestReferenceFileIntegrity(unittest.TestCase):
    def test_every_general_state_has_both_claim_types(self):
        ref = bt.load_reference()
        for state, entry in ref["general"].items():
            self.assertIn("biological_basis", entry, msg=state)
            self.assertIn("angling_application", entry, msg=state)

    def test_every_species_entry_keys_a_real_state(self):
        ref = bt.load_reference()
        valid = set(ref["_states"])
        for species, states in ref["species"].items():
            for state in states:
                self.assertIn(state, valid, msg=f"{species}/{state}")

    def test_every_species_in_the_reference_exists_in_the_physiology_data(self):
        # Guidance for a species this app has no thresholds for could never
        # be reached, and would mean the two files had drifted apart.
        ref = bt.load_reference()
        thresholds = v1.load_thresholds()
        known = {k.upper() for k in thresholds["species"]}
        for species in ref["species"]:
            self.assertIn(species, known, msg=f"{species} has guidance but no physiology thresholds")

    def test_reference_declares_its_sources(self):
        ref = bt.load_reference()
        self.assertGreaterEqual(len(ref["_sources"]), 3)
        self.assertIn("honesty_note", json.dumps(ref))


if __name__ == "__main__":
    unittest.main()
