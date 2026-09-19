"""Route tests for the Fish Detail page (/fish/<species>).

Run: python -m pytest webapp/tests/test_fish_detail.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import v4_species_detail as sd  # noqa: E402


class FishDetailRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _page(self, slug, query=""):
        resp = self.client.get(f"/fish/{slug}{query}")
        self.assertEqual(resp.status_code, 200, slug)
        return resp.data.decode()

    def test_every_species_page_renders(self):
        for s in sd.list_species():
            body = self._page(s["slug"])
            self.assertIn(s["title"], body)
            self.assertIn("Documented activity", body)
            self.assertIn("Documented habitat", body)

    def test_unknown_species_is_a_404(self):
        self.assertEqual(self.client.get("/fish/dragon").status_code, 404)

    def test_species_image_is_shown_with_its_credit_and_license(self):
        body = self._page("walleye")
        self.assertIn("/static/img/species/walleye.jpg", body)
        self.assertIn("Public domain", body)
        self.assertIn("Wikimedia Commons", body)

    def test_a_cited_habitat_claim_shows_its_verbatim_source_quote(self):
        body = self._page("walleye")
        self.assertIn("Walleyes live near or on the lake bottom", body)
        self.assertIn("Species_walleye.pdf", body)

    def test_bait_cards_render_for_a_target_species(self):
        body = self._page("walleye")
        self.assertIn("Recommended bait", body)
        self.assertIn("Live minnows", body)
        self.assertIn("angling practice, not tested research", body)

    def test_a_stated_wisconsin_rule_is_shown_with_its_source(self):
        body = self._page("smallmouth-bass")
        self.assertIn("Wisconsin rule stated", body)
        self.assertIn("live crayfish", body)

    def test_an_unreviewed_bait_is_flagged_not_cleared(self):
        body = self._page("channel-catfish")
        self.assertIn("Rules not reviewed", body)
        self.assertIn("have not been reviewed", body)
        self.assertNotIn("legal to use everywhere", body)

    def test_a_bait_without_a_picture_says_so_instead_of_a_placeholder_image(self):
        body = self._page("walleye")
        self.assertIn("No picture yet", body)

    def test_non_targets_show_no_bait_section(self):
        for slug in ("white-sucker", "fathead-minnow"):
            body = self._page(slug)
            self.assertIn("Not an angling target", body)
            self.assertNotIn("Recommended bait", body)

    def test_species_with_no_documented_bait_say_why(self):
        body = self._page("cisco")
        self.assertIn("no bait is listed rather than guessed", body)

    def test_lake_whitefish_now_lists_its_sourced_baits(self):
        body = self._page("lake-whitefish")
        self.assertIn("Recommended bait", body)
        self.assertNotIn("no bait is listed rather than guessed", body)

    def test_page_states_it_is_not_a_prediction_and_never_promises_a_bite(self):
        for slug in ("walleye", "yellow-perch", "muskellunge"):
            body = self._page(slug).lower()
            self.assertNotIn("guarantee", body)
            self.assertIn("not a promise of a bite", body)

    def test_spot_context_adds_a_back_link(self):
        conn = flask_app_module.get_conn()
        row = conn.execute(
            "SELECT latitude, longitude, facility_name FROM access_points WHERE matched_waterbody_name IS NOT NULL LIMIT 1"
        ).fetchone()
        conn.close()
        body = self._page("walleye", f"?lat={row['latitude']}&lon={row['longitude']}&name={row['facility_name']}")
        self.assertIn("/spot?", body)
        self.assertIn("Back to", body)

    def test_a_bad_spot_context_does_not_break_the_page(self):
        body = self._page("walleye", "?lat=abc&lon=def")
        self.assertIn("Walleye", body)

    def test_sitemap_lists_every_species_page(self):
        body = self.client.get("/sitemap.xml").data.decode()
        for s in sd.list_species():
            self.assertIn(f"/fish/{s['slug']}", body)


if __name__ == "__main__":
    unittest.main()
