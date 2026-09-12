"""Unit tests for the shore-fishing species canonicalization used by the
V2 map's species filter. Every case here uses a real raw phrase actually
present in this project's shore_fishing_species table (verified via a
direct query before writing the mapping), not a hypothetical example.

Run: python -m pytest analysis/tests/test_v2_species_canonicalization.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_species_canonicalization as canon  # noqa: E402


class CanonicalizeTests(unittest.TestCase):
    def test_exact_match_single_species(self):
        self.assertEqual(canon.canonicalize("WALLEYE"), ["Walleye"])

    def test_real_typos_map_to_correct_species(self):
        self.assertEqual(canon.canonicalize("LAREMOUTH BASS"), ["Largemouth Bass"])
        self.assertEqual(canon.canonicalize("WALEYE"), ["Walleye"])
        self.assertEqual(canon.canonicalize("NORTHEN PIKE"), ["Northern Pike"])
        self.assertEqual(canon.canonicalize("STURGON"), ["Lake Sturgeon"])
        self.assertEqual(canon.canonicalize("MUDKY"), ["Muskellunge"])

    def test_common_name_aligns_with_v1_vocabulary(self):
        # V1's own species_predictions table uses "MUSKELLUNGE", never
        # "Muskie"/"Musky" -- the two sources must converge on one name.
        self.assertEqual(canon.canonicalize("MUSKIE"), ["Muskellunge"])
        self.assertEqual(canon.canonicalize("MUSKY"), ["Muskellunge"])

    def test_compound_phrase_produces_multiple_species(self):
        self.assertEqual(
            sorted(canon.canonicalize("LM & SM BASS")), sorted(["Largemouth Bass", "Smallmouth Bass"])
        )
        self.assertEqual(
            sorted(canon.canonicalize("TROUT - BROWN & RAINBOW")), sorted(["Brown Trout", "Rainbow Trout"])
        )

    def test_parenthetical_compound_from_real_site_decomposed_correctly(self):
        # Real text from site 109 (Council Grounds State Park).
        self.assertEqual(
            sorted(canon.canonicalize("BASS (LG. MOUTH, ROCK)")), sorted(["Largemouth Bass", "Rock Bass"])
        )

    def test_ambiguous_yellow_pike_not_guessed_as_walleye(self):
        # "YELLOW" in this context is a regional nickname with real
        # historical ambiguity -- not confident enough to assert as
        # Walleye, so only "NORTHERN" is canonicalized.
        result = canon.canonicalize("PIKE (NORTHERN, YELLOW)")
        self.assertEqual(result, ["Northern Pike"])
        self.assertNotIn("Walleye", result)

    def test_generic_terms_kept_as_their_own_bucket_not_guessed(self):
        self.assertEqual(canon.canonicalize("PANFISH"), ["Panfish (unspecified)"])
        self.assertEqual(canon.canonicalize("TROUT"), ["Trout (unspecified)"])
        self.assertEqual(canon.canonicalize("CATFISH"), ["Catfish (unspecified)"])
        self.assertEqual(canon.canonicalize("SALMON"), ["Salmon (unspecified)"])

    def test_rock_bass_not_merged_into_smallmouth(self):
        # Rock Bass (Ambloplites rupestris) is a distinct species from
        # Smallmouth Bass -- must never collapse into one bucket.
        self.assertEqual(canon.canonicalize("ROCK BASS"), ["Rock Bass"])
        self.assertNotEqual(canon.canonicalize("ROCK BASS"), canon.canonicalize("SMALLMOUTH BASS"))

    def test_unknown_phrase_falls_back_to_title_case_not_dropped(self):
        result = canon.canonicalize("SOME FUTURE SPECIES WDNR ADDS")
        self.assertEqual(result, ["Some Future Species Wdnr Adds"])

    def test_empty_or_none_returns_empty_list(self):
        self.assertEqual(canon.canonicalize(""), [])
        self.assertEqual(canon.canonicalize(None), [])

    def test_whitespace_variations_normalize_to_same_key(self):
        self.assertEqual(canon.canonicalize("  WALLEYE  "), ["Walleye"])
        self.assertEqual(canon.canonicalize("walleye"), ["Walleye"])


if __name__ == "__main__":
    unittest.main()
