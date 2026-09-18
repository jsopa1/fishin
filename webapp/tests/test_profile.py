"""Profile page (V4 Phase 3): anonymous, on-device preferences, plus the dark
theme it controls.

Run: python -m pytest webapp/tests/test_profile.py
"""

import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import v4_species_detail as sd  # noqa: E402

CSS = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text(encoding="utf-8")


class ProfilePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()
        cls.body = cls.client.get("/profile").data.decode()

    def test_page_loads_as_a_guest_with_no_account_language(self):
        self.assertEqual(self.client.get("/profile").status_code, 200)
        self.assertIn("Guest", self.body)
        self.assertIn("No account", self.body)
        self.assertNotIn("Member since", self.body)
        self.assertNotIn('type="password"', self.body)

    def test_help_links_exist_and_point_at_real_places(self):
        self.assertIn("Rate us", self.body)
        self.assertIn('href="/feedback?page=/profile"', self.body)
        self.assertIn("Help", self.body)
        self.assertIn('href="/#about"', self.body)
        self.assertIn("Documentation", self.body)
        self.assertIn("https://github.com/jsopa1/fishin", self.body)

    def test_theme_control_offers_system_light_and_dark(self):
        group = self.body[self.body.index('data-pref="theme"'):]
        for value in ("system", "light", "dark"):
            self.assertIn(f'data-value="{value}"', group[:600], value)

    def test_each_spot_type_has_prefer_ok_avoid(self):
        for t in ("boat_ramp", "boat_carry_in", "shore_fishing"):
            block = self.body[self.body.index(f'data-type="{t}"'):][:500]
            for level in ("prefer", "ok", "avoid"):
                self.assertIn(f'data-value="{level}"', block, f"{t}/{level}")
        for label in ("Boat launches", "Carry-ins", "Shore spots"):
            self.assertIn(label, self.body)

    def test_distance_options_include_any(self):
        self.assertIn('data-pref="distance"', self.body)
        self.assertIn('value="0">Any distance', self.body)

    def test_every_documented_species_can_be_ticked(self):
        boxes = re.findall(r'<input type="checkbox" value="([A-Z ]+)" data-pref="species">', self.body)
        self.assertEqual(sorted(boxes), sorted(s["name"] for s in sd.list_species()))
        self.assertEqual(len(boxes), 27)

    def test_species_thumbnails_use_the_verified_images(self):
        self.assertIn("/static/img/species/walleye.jpg", self.body)

    def test_the_page_says_nothing_is_sent_to_the_server(self):
        self.assertIn("Nothing here is sent to our servers", self.body)

    def test_the_page_makes_no_network_calls_with_preferences(self):
        js = (Path(__file__).resolve().parents[1] / "static" / "profile.js").read_text(encoding="utf-8")
        prefs = (Path(__file__).resolve().parents[1] / "static" / "prefs.js").read_text(encoding="utf-8")
        for src in (js, prefs):
            for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"):
                self.assertNotIn(forbidden, src, forbidden)


class PrivacyPageMatchesTheCode(unittest.TestCase):
    def test_privacy_page_describes_preferences_and_location_as_on_device(self):
        body = flask_app_module.app.test_client().get("/privacy").data.decode()
        self.assertIn("Preferences and location", body)
        self.assertIn("localStorage", body)
        self.assertIn("never sent anywhere", body)


class ThemeTests(unittest.TestCase):
    def test_base_template_applies_the_saved_theme_before_first_paint(self):
        body = flask_app_module.app.test_client().get("/").data.decode()
        head = body[: body.index("</head>")]
        self.assertIn('localStorage.getItem("fishin.prefs.theme.v1")', head)

    def test_dark_tokens_exist_for_both_the_explicit_choice_and_the_device_setting(self):
        self.assertIn(':root[data-theme="dark"] {', CSS)
        self.assertIn("@media (prefers-color-scheme: dark)", CSS)
        self.assertIn(':root:not([data-theme="light"])', CSS)

    def test_every_dark_rule_is_scoped_so_nothing_leaks_into_light_mode(self):
        tail = CSS[CSS.index("/* ---- Dark theme"):]
        for line in tail.splitlines():
            line = line.strip()
            if "{" in line and line.endswith("}") and not line.startswith(("/*", "--")):
                selectors = line[: line.index("{")].split(",")
                for sel in selectors:
                    self.assertTrue(sel.strip().startswith(":root"), f"unscoped dark selector: {sel.strip()}")

    def test_explicit_light_overrides_a_dark_device(self):
        # The device-driven block must exclude data-theme="light".
        media = CSS[CSS.index("@media (prefers-color-scheme: dark)"):]
        self.assertIn(':root:not([data-theme="light"])', media)

    def test_dark_and_device_blocks_define_the_same_tokens(self):
        tail = CSS[CSS.index("/* ---- Dark theme"):]
        explicit = tail[tail.index(':root[data-theme="dark"] {'):]
        explicit = explicit[: explicit.index("}")]
        device = tail[tail.index(':root:not([data-theme="light"]) {'):]
        device = device[: device.index("}")]
        tokens = lambda block: sorted(re.findall(r"(--[a-z0-9-]+):", block))
        self.assertEqual(tokens(explicit), tokens(device))


if __name__ == "__main__":
    unittest.main()
