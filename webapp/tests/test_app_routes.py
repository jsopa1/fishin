"""Basic route tests for the Flask web app (Part 5).

Uses Flask's test client against the real, already-generated
data/v1/v1_full_run_results.db -- not mock data -- to confirm every route
responds correctly and the data flowing through matches what the .exe
review tool and docs/v1_full_run_report.md show. Not full UI/browser
testing, just route-level correctness per this cycle's scope.

Run: python -m pytest webapp/tests/test_app_routes.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402


class WebAppRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_home_page_loads(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_home_page_states_not_a_prediction(self):
        resp = self.client.get("/")
        self.assertIn(b"NOT a validated catch-rate prediction", resp.data)

    def test_browse_page_loads_with_no_filters(self):
        resp = self.client.get("/browse")
        self.assertEqual(resp.status_code, 200)

    def test_browse_filters_by_name(self):
        resp = self.client.get("/browse?name=Devils+Lake")
        self.assertEqual(resp.status_code, 200)
        # Real dedup fix verification: exactly the distinct real waterbodies,
        # not a duplicate "Devils Lake" entry under two county spellings.
        self.assertEqual(resp.data.count(b"<tr>"), 4)  # 1 header + 3 real distinct entries

    def test_browse_filters_by_tier(self):
        resp = self.client.get("/browse?tier=survey_confirmed")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"survey_confirmed", resp.data)

    def test_waterbody_detail_shows_full_narrative(self):
        resp = self.client.get("/waterbody?name=Big+Moon+Lake&county=Barron")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"FULL NARRATIVE", resp.data.upper())

    def test_waterbody_detail_disputed_threshold_shown_in_full(self):
        # The Muskellunge two-source thermal-optimum disagreement must
        # render verbatim, not summarized or dropped, on the web version
        # exactly as it does in the .exe.
        resp = self.client.get("/waterbody?name=Big+Moon+Lake&county=Barron")
        self.assertIn(b"DISPUTED", resp.data)
        self.assertIn(b"treat any single value drawn from here as one source", resp.data)

    def test_waterbody_detail_404_for_unknown_waterbody(self):
        resp = self.client.get("/waterbody?name=Nonexistent+Lake+XYZ&county=Nowhere")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"Not found", resp.data)

    def test_failures_page_loads(self):
        resp = self.client.get("/failures")
        self.assertEqual(resp.status_code, 200)

    def test_failures_filter_by_type(self):
        resp = self.client.get("/failures?failure_type=no_physiology_threshold")
        self.assertEqual(resp.status_code, 200)

    def test_summary_page_loads_and_shows_real_counts(self):
        resp = self.client.get("/summary")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Total waterbody results", resp.data)

    def test_summary_counts_match_review_data_module_directly(self):
        # Cross-check the page's rendered totals against a direct query,
        # the same way the report's own totals were verified.
        import v1_review_data as data

        conn = flask_app_module.get_conn()
        counts = data.get_summary_counts(conn)
        conn.close()

        resp = self.client.get("/summary")
        self.assertIn(str(counts["total_waterbodies"]).encode(), resp.data)
        self.assertIn(str(counts["total_species_predictions"]).encode(), resp.data)

    def test_staleness_banner_present_on_every_page(self):
        for path in ("/", "/browse", "/failures", "/summary"):
            resp = self.client.get(path)
            self.assertIn(b'class="banner', resp.data, msg=f"banner missing on {path}")

    def test_attribution_footer_present(self):
        resp = self.client.get("/")
        self.assertIn(b"Wisconsin Department of Natural Resources", resp.data)
        self.assertIn(b"U.S. Geological Survey", resp.data)
        self.assertIn(b"National Weather Service", resp.data)


class WebAppErrorHandlingTests(unittest.TestCase):
    """Part 3 of the polish pass: malformed input, missing params, and
    unmatched routes must degrade gracefully -- never a raw error page or
    stack trace, always a clear, honest message."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_invalid_tier_falls_back_to_all_with_a_visible_note(self):
        resp = self.client.get("/browse?tier=not_a_real_tier")
        self.assertEqual(resp.status_code, 200)  # degrades gracefully, doesn't error
        self.assertIn(b"not a recognized presence tier", resp.data)
        # Falling back to "all" means real results still show, not zero.
        self.assertGreater(resp.data.count(b"<tr>"), 1)

    def test_waterbody_detail_missing_params_returns_400_not_crash(self):
        resp = self.client.get("/waterbody")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"missing a waterbody name or county", resp.data)

    def test_unmatched_route_returns_styled_404_no_traceback(self):
        resp = self.client.get("/this-route-does-not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"Page not found", resp.data)
        self.assertNotIn(b"Traceback", resp.data)
        self.assertNotIn(b"werkzeug", resp.data.lower())

    def test_percent_and_underscore_in_search_do_not_crash_or_wildcard_match(self):
        # Regression check at the route level for the LIKE-escaping fix.
        resp = self.client.get("/browse?name=" + "%25%25%25")  # literal "%%%"
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"0 results shown", resp.data)

    def test_data_unavailable_state_never_shows_bare_empty_page(self):
        # Simulates a failed data load (Criterion 3) without touching the
        # real database file -- patches find_db_path to return a path
        # that doesn't exist.
        import v1_review_data as rd
        from pathlib import Path

        original = rd.find_db_path
        rd.find_db_path = lambda start=None: Path("/nonexistent/does-not-exist.db")
        try:
            resp = self.client.get("/browse")
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"currently unavailable", resp.data)

            resp = self.client.get("/summary")
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"currently unavailable", resp.data)

            resp = self.client.get("/failures")
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"currently unavailable", resp.data)

            resp = self.client.get("/waterbody?name=X&county=Y")
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"currently unavailable", resp.data)
        finally:
            rd.find_db_path = original


if __name__ == "__main__":
    unittest.main()
