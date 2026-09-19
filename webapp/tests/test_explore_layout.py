"""Explore screen layout (V4 Phase 2b): Map | List toggle first, then the
collapsible Filters, then the map or list. Every filter and query-param deep
link that worked before must still work.

Run: python -m pytest webapp/tests/test_explore_layout.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402


class ExploreLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _body(self, query=""):
        resp = self.client.get("/map" + query)
        self.assertEqual(resp.status_code, 200)
        return resp.data.decode()

    def test_map_list_toggle_comes_before_the_filters_which_come_before_the_content(self):
        body = self._body()
        toggle = body.index('id="toggle-map-btn"')
        filters = body.index('id="explore-filter-panel"')
        content = body.index('id="explore-layout"')
        self.assertLess(toggle, filters)
        self.assertLess(filters, content)

    def test_every_prior_filter_control_is_still_in_the_form(self):
        body = self._body()
        for needle in ('name="waterbody"', 'name="county"', 'name="source_type"', 'name="species"', 'id="locate-btn"'):
            self.assertIn(needle, body, needle)

    def test_filters_are_collapsed_by_default(self):
        body = self._body()
        tag = body[body.index('<details class="explore-filter-panel"'):]
        tag = tag[:tag.index(">") + 1]
        self.assertNotIn(" open", tag)

    def test_filters_open_and_are_flagged_when_a_filter_is_active(self):
        body = self._body("?species=WALLEYE")
        tag = body[body.index('<details class="explore-filter-panel"'):]
        tag = tag[:tag.index(">") + 1]
        self.assertIn(" open", tag)
        self.assertIn(">active<", body)

    def test_query_param_deep_links_still_drive_the_map_data_request(self):
        body = self._body("?waterbody=Lake+Monona&county=Dane&species=WALLEYE&source_type=boat_ramp")
        self.assertIn('data-waterbody="Lake Monona"', body)
        self.assertIn('data-county="Dane"', body)
        self.assertIn('data-species="WALLEYE"', body)
        self.assertIn('data-source-type="boat_ramp"', body)

    def test_the_directory_is_still_reachable_from_explore(self):
        self.assertNotIn("/browse", self._body())
        self.assertNotIn("Waterbody Directory", self._body())

    def test_the_bottom_nav_search_shortcut_still_has_something_to_focus(self):
        body = self._body()
        self.assertIn('id="explore-search"', body)
        self.assertIn("explore-filter-panel", body)


if __name__ == "__main__":
    unittest.main()
