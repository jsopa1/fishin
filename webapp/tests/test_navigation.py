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

    def test_every_page_has_exactly_four_labelled_tabs(self):
        for path in ("/", "/map", "/profile", "/fish", "/fish/walleye", "/privacy"):
            nav = bottom_nav(self.client.get(path).data.decode())
            self.assertEqual(len(re.findall(r'class="bottom-nav-item', nav)), 4, path)

    def test_the_four_destinations_are_home_explore_fish_and_profile_with_visible_labels(self):
        nav = bottom_nav(self.client.get("/").data.decode())
        self.assertEqual(re.findall(r'<span class="bottom-nav-label">([^<]+)</span>', nav), ["Home", "Explore", "Fish", "Profile"])
        for href in ("/", "/map", "/fish", "/profile"):
            self.assertIn('href="' + href + '"', nav)

    def test_detail_pages_light_up_their_parent_tab(self):
        def current(path):
            nav = bottom_nav(self.client.get(path).data.decode())
            return re.findall(r'<a href="([^"]+)"[^>]*aria-current="page"', nav)

        self.assertEqual(current("/"), ["/"])
        self.assertEqual(current("/map"), ["/map"])
        self.assertEqual(current("/fish"), ["/fish"])
        self.assertEqual(current("/fish/walleye"), ["/fish"])
        self.assertEqual(current("/profile"), ["/profile"])
        self.assertEqual(current("/privacy"), [])

    def test_the_header_names_the_current_section(self):
        for path, label in (("/", "Home"), ("/map", "Explore"), ("/fish", "Fish"), ("/profile", "Profile"), ("/privacy", "Privacy")):
            self.assertRegex(self.client.get(path).data.decode(), r'class="header-here"[^>]*>' + label + "<", path)

    def test_on_a_phone_the_header_is_the_fish_and_the_section_name(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text(encoding="utf-8")
        mobile = css[css.index("@media (max-width: 767px)"):]
        self.assertIn(".brand-sub, .brand-word { display: none; }", mobile)

    def test_the_fish_logo_leads_home(self):
        for path in ("/", "/map", "/profile", "/fish/walleye"):
            body = self.client.get(path).data.decode()
            self.assertRegex(body, r'<a class="brand" href="/"[^>]*>', path)

    def test_a_spot_page_records_itself_as_the_last_spot_on_this_device_only(self):
        conn = flask_app_module.get_conn()
        row = conn.execute("SELECT latitude, longitude, facility_name FROM access_points LIMIT 1").fetchone()
        conn.close()
        body = self.client.get("/spot?lat={}&lon={}&name={}".format(row[0], row[1], row[2])).data.decode()
        self.assertIn("localStorage.setItem('fishin.lastSpot.v1'", body)

    def test_every_old_destination_is_still_reachable(self):
        # The five-item nav is gone from the bottom bar; nothing it linked to was removed.
        for path in ("/", "/map", "/privacy", "/profile"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        header = self.client.get("/").data.decode()
        header = header[header.index("primary-nav"): header.index("</header>")]
        for href in ("/map", "/fish", "/profile"):
            self.assertIn('href="' + href + '"', header)


if __name__ == "__main__":
    unittest.main()


class DirectoryRetiredTests(unittest.TestCase):
    """The waterbody directory was outdated once Explore replaced it. No page links to it and the
    old URL still lands somewhere useful instead of a 404."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_the_old_url_redirects_permanently_to_explore(self):
        for path in ("/browse", "/browse?name=Devils+Lake"):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 301, path)
            self.assertTrue(resp.headers["Location"].endswith("/map"), path)

    def test_no_page_links_to_the_directory(self):
        for path in ("/", "/map", "/profile", "/fish/walleye", "/privacy", "/terms"):
            body = self.client.get(path).data.decode()
            self.assertNotIn("Waterbody Directory", body, path)
            self.assertNotIn('href="/browse"', body, path)

    def test_the_sitemap_no_longer_lists_it(self):
        self.assertNotIn("/browse", self.client.get("/sitemap.xml").data.decode())

    def test_the_template_is_gone(self):
        self.assertFalse((Path(__file__).resolve().parents[1] / "templates" / "browse.html").exists())


class ResponsiveLayouts(unittest.TestCase):
    """Phones and tablets get one centred column with the labelled bottom bar; from 1024px up the
    app uses the full width with the top nav and multi-column grids."""

    CSS = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text(encoding="utf-8")

    def tablet(self):
        i = self.CSS.index("/* ---- Tablet: the phone column")
        return self.CSS[i:self.CSS.index("/* ---- Wayfinding", i)]

    def desktop(self):
        i = self.CSS.index("/* ---- Desktop (1024px+)")
        return self.CSS[i:self.CSS.index("/* ---- Dark theme", i)]

    def test_the_tablet_block_reuses_the_mobile_pieces_and_stops_before_desktop(self):
        block = self.tablet()
        self.assertIn("@media (min-width: 768px) and (max-width: 1023px)", block)
        for piece in (".wrap { max-width: 560px; }", ".primary-nav { display: none !important; }", ".bottom-nav {",
                      "display: flex;", ".explore-view-toggle { display: inline-flex; }", ".explore-layout { display: block; }"):
            self.assertIn(piece, block)
        self.assertIn("width: 560px", block)

    def test_desktop_uses_the_top_nav_and_multi_column_grids_and_no_bottom_bar(self):
        block = self.desktop()
        self.assertIn("@media (min-width: 1024px)", block)
        self.assertIn(".quick-links { grid-template-columns: repeat(4, 1fr); }", block)
        self.assertIn("#rec-list, #saved-list { display: grid; grid-template-columns: repeat(2, 1fr)", block)
        self.assertNotIn(".primary-nav { display: none", block)
        self.assertNotIn(".bottom-nav {", block)
        # the base rule that hides the bottom bar outside phone/tablet widths is still there
        self.assertIn(".bottom-nav { display: none; }", self.CSS)

    def test_the_top_nav_has_the_same_four_destinations_as_the_bottom_bar(self):
        body = self.client_body()
        header = body[body.index('id="primary-nav"'): body.index("</header>")]
        for href in ("/", "/map", "/fish", "/profile"):
            self.assertIn('href="' + href + '"', header)

    def client_body(self):
        flask_app_module.app.testing = True
        return flask_app_module.app.test_client().get("/").data.decode()

    def test_explore_starts_collapsed_like_on_a_phone(self):
        html = (Path(__file__).resolve().parents[1] / "templates" / "map.html").read_text(encoding="utf-8")
        self.assertNotIn("matchMedia('(min-width: 768px)')", html)



class HowItWorksExplainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.body = flask_app_module.app.test_client().get("/about").data.decode()

    def test_the_about_page_leads_with_the_three_step_picture_and_the_worked_example(self):
        self.assertLess(self.body.index('id="how"'), self.body.index('id="what"'))
        self.assertEqual(self.body.count('class="how-step"'), 3)
        self.assertIn('class="how-chart"', self.body)

    def test_the_example_marks_who_is_in_range_from_the_real_windows(self):
        # 68F sits inside walleye 55-75F and brook trout 66-68F, outside pike 55-65F and bass 80-86F.
        rows = re.findall(r'<span class="how-fish">([^<]+)</span>\s*<span class="how-status (in|out)"', self.body)
        self.assertEqual(rows, [("Walleye", "in"), ("Northern pike", "out"), ("Brook trout", "in"), ("Largemouth bass", "out")])

    def test_the_explainer_says_in_range_is_not_biting(self):
        self.assertIn("is not", self.body[self.body.index('class="how-caveat"'):])
        self.assertRegex(self.body, r"can&rsquo;t tell you whether you&rsquo;ll catch one")

    def test_the_chart_has_a_text_alternative(self):
        self.assertRegex(self.body, r'class="how-plot" role="img"\s+aria-label="Example at 68')
