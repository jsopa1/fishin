"""Tests for the WDNR lake-page species ingest.

The property that matters most: WDNR's published categories are coarser
than species, and nothing here may quietly turn a category into one.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_wdnr_lake_species as wls  # noqa: E402


REAL_PAGE_FRAGMENT = """
<h1>Devils Lake</h1>
<p>Devils Lake is a 374 acre lake located in Sauk County.</p>
<h3>Fish</h3><ul class='fishBullets'><li>Panfish (Abundant)</li>
<li>Largemouth Bass (Common)</li><li>Smallmouth Bass (Present)</li>
<li>Trout (Present)</li></ul> <!--end fish section-->
<h3>Before You Go </h3>
"""


class TestLakePageParsing(unittest.TestCase):
    def test_extracts_species_with_abundance(self):
        parsed = wls.parse_lake_page(REAL_PAGE_FRAGMENT)
        categories = {s["category"]: s["abundance"] for s in parsed["species"]}
        self.assertEqual(categories["Panfish"], "Abundant")
        self.assertEqual(categories["Largemouth Bass"], "Common")
        self.assertEqual(categories["Trout"], "Present")

    def test_extracts_lake_name_and_acreage(self):
        parsed = wls.parse_lake_page(REAL_PAGE_FRAGMENT)
        self.assertEqual(parsed["lake_name"], "Devils Lake")
        self.assertEqual(parsed["acres"], 374.0)

    def test_categories_are_kept_verbatim_not_expanded_into_species(self):
        # "Trout" must stay "Trout". Turning it into brook/brown/rainbow
        # would invent a fact WDNR did not state -- and those three have
        # materially different thermal thresholds.
        parsed = wls.parse_lake_page(REAL_PAGE_FRAGMENT)
        names = {s["category"] for s in parsed["species"]}
        self.assertIn("Trout", names)
        for invented in ("Brook Trout", "Brown Trout", "Rainbow Trout",
                         "Bluegill", "Black Crappie", "Yellow Perch"):
            self.assertNotIn(invented, names)

    def test_page_without_a_fish_section_yields_no_species(self):
        parsed = wls.parse_lake_page("<h1>Some Lake</h1><p>No fish block here.</p>")
        self.assertEqual(parsed["species"], [])
        self.assertEqual(parsed["lake_name"], "Some Lake")

    def test_species_without_an_abundance_qualifier_is_still_captured(self):
        parsed = wls.parse_lake_page(
            "<h1>X</h1><h3>Fish</h3><ul class='fishBullets'><li>Walleye</li></ul>"
        )
        self.assertEqual(parsed["species"][0]["category"], "Walleye")
        self.assertIsNone(parsed["species"][0]["abundance"])

    def test_documented_vocabulary_is_recorded_for_future_readers(self):
        # If WDNR ever publishes something outside this set, the ingest
        # reports it rather than silently absorbing it.
        self.assertIn("Panfish", wls.KNOWN_CATEGORIES)
        self.assertIn("Trout", wls.KNOWN_CATEGORIES)
        self.assertEqual(len(wls.KNOWN_CATEGORIES), 9)


if __name__ == "__main__":
    unittest.main()
