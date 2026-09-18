"""Navigation (V4 Phase 4): fish logo -> Recommended, and a three-icon bottom nav
(My spot / Explore / Profile), as in the approved wireframes.

Run: python -m pytest webapp/tests/test_navigation.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402


def bottom_nav(body):
    start = body.index('<nav class="bottom-nav"')
    return body[start: body.index("</nav>", start)]


class BottomNavTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_every_page_has_exactly_three_bottom_icons(self):
        for path in ("/", "/map", "/browse", "/profile", "/fish/walleye", "/privacy"):
            nav = bottom_nav(self.client.get(path).data.decode())
            self.assertEqual(len(re.findall(r'class="bottom-nav-item', nav)), 3, path)
            self.assertNotIn("bottom-nav-fab", nav, path)

    def test_the_three_destinations_are_my_spot_explore_and_profile(self):
        nav = bottom_nav(self.client.get("/").data.decode())
        self.assertEqual(re.findall(r"<span>([^<]+)</span>", nav), ["My spot", "Explore", "Profile"])
        self.assertIn('href="/map"', nav)
        self.assertIn('href="/profile"', nav)

    def test_the_fish_logo_leads_to_recommended(self):
        for path in ("/", "/map", "/profile", "/fish/walleye"):
            body = self.client.get(path).data.decode()
            self.assertRegex(body, r'<a class="brand" href="/"[^>]*>', path)

    def test_the_active_tab_matches_the_page(self):
        self.assertRegex(bottom_nav(self.client.get("/profile").data.decode()),
                         r'href="/profile" class="bottom-nav-item active"')
        self.assertRegex(bottom_nav(self.client.get("/map").data.decode()),
                         r'href="/map" class="bottom-nav-item active"')

    def test_my_spot_defaults_to_recommended_and_is_pointed_at_the_last_spot_by_script(self):
        body = self.client.get("/").data.decode()
        self.assertIn('id="nav-spot"', body)
        self.assertIn("fishin.lastSpot.v1", body)

    def test_the_last_spot_script_only_trusts_numbers_and_encodes_the_name(self):
        body = self.client.get("/").data.decode()
        self.assertIn("isFinite(lat)", body)
        self.assertIn("encodeURIComponent(s.name)", body)

    def test_a_spot_page_records_itself_as_the_last_spot_on_this_device_only(self):
        conn = flask_app_module.get_conn()
        row = conn.execute("SELECT latitude, longitude, facility_name FROM access_points LIMIT 1").fetchone()
        conn.close()
        body = self.client.get("/spot?lat={}&lon={}&name={}".format(row[0], row[1], row[2])).data.decode()
        self.assertIn("localStorage.setItem('fishin.lastSpot.v1'", body)

    def test_every_old_destination_is_still_reachable(self):
        # The five-item nav is gone from the bottom bar; nothing it linked to was removed.
        for path in ("/", "/map", "/browse", "/privacy", "/profile"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        header = self.client.get("/").data.decode()
        header = header[header.index("primary-nav"): header.index("</header>")]
        for href in ("/map", "/browse", "/profile", "/#about"):
            self.assertIn('href="' + href + '"', header)


if __name__ == "__main__":
    unittest.main()
