"""Navigation (V4 Phase 4): fish logo -> Recommended, and a three-icon bottom nav
(My spot / Explore / Profile), as in the approved wireframes.

Run: python -m pytest webapp/tests/test_navigation.py
"""

import os
import re
import sys
import unittest
from pathlib import Path

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
        self.assertEqual(re.findall(r'<span class="sr-only">([^<]+)</span>', nav), ["My spot", "Explore", "Profile"])
        self.assertIn('href="/map"', nav)
        self.assertIn('href="/profile"', nav)

    def test_the_bar_is_icons_only_with_a_larger_explore_icon_as_in_the_wireframe(self):
        nav = bottom_nav(self.client.get("/").data.decode())
        self.assertEqual(re.findall(r'<use href="#(icon-[a-z-]+)"', nav), ["#icon-list".lstrip("#"), "icon-explore", "icon-user"])
        self.assertEqual(len(re.findall("bottom-nav-primary", nav)), 1)
        self.assertNotRegex(re.sub(r'<span class="sr-only">[^<]*</span>', "", nav), r"<span>")

    def test_on_a_phone_the_header_is_only_the_fish(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text(encoding="utf-8")
        mobile = css[css.index("@media (max-width: 767px)"):]
        self.assertIn(".brand-sub, .brand-word { display: none; }", mobile)

    def test_the_fish_logo_leads_to_recommended(self):
        for path in ("/", "/map", "/profile", "/fish/walleye"):
            body = self.client.get(path).data.decode()
            self.assertRegex(body, r'<a class="brand" href="/"[^>]*>', path)

    def test_the_active_tab_matches_the_page(self):
        def active_hrefs(path):
            nav = bottom_nav(self.client.get(path).data.decode())
            return re.findall(r'<a href="([^"]+)"[^>]*class="bottom-nav-item[^"]* active', nav)

        self.assertEqual(active_hrefs("/profile"), ["/profile"])
        self.assertEqual(active_hrefs("/map"), ["/map"])
        self.assertEqual(active_hrefs("/browse"), ["/map"])  # the directory lives under Explore

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
