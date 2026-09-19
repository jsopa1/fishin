"""The Recommended feed and screen (V4 Phase 4).

Two promises are tested here because they are the ones that could quietly break:
  1. A recommendation card never disagrees with the spot page it links to.
  2. Nothing about the visitor (location, preferences, saved spots) reaches the
     server - the feed is one non-personal document and the ranking is local.

Run: python -m pytest webapp/tests/test_recommend_feed.py
"""

import gzip
import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import v1_review_data as data  # noqa: E402
import v4_recommend_feed as feed_module  # noqa: E402

STATIC = Path(__file__).resolve().parents[1] / "static"


class FeedContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = data.connect(data.find_db_path(start=flask_app_module.REPO_ROOT))
        cls.feed = feed_module.get_feed(cls.conn)
        cls.spots = cls.feed["spots"]

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_every_access_point_has_a_row(self):
        total = self.conn.execute("SELECT COUNT(*) FROM access_points").fetchone()[0]
        self.assertEqual(len(self.spots), total)

    def test_rows_use_only_the_documented_keys_and_values(self):
        allowed_types = {"boat_ramp", "boat_carry_in", "shore_fishing"}
        for row in self.spots[::25]:
            self.assertEqual(set(row), {"n", "w", "c", "t", "lat", "lon", "q", "v", "a", "s", "i"})
            self.assertIn(row["t"], allowed_types)
            self.assertIn(row["q"], ("real", "estimated", "proxy", None))
            for species, tier in row["a"]:
                self.assertIn(tier, ("c", "l"))
            for species, tier, distance in row["i"]:
                self.assertGreaterEqual(distance, 0)  # rounded to 0.1 F, so a hair outside a window shows 0.0

    def test_a_species_is_in_exactly_one_list_per_spot(self):
        for row in self.spots[::10]:
            names = [x[0] for x in row["a"]] + list(row["s"]) + [x[0] for x in row["i"]]
            self.assertEqual(len(names), len(set(names)), row["n"])

    def test_cards_agree_with_the_spot_page_for_a_deterministic_sample(self):
        # Every 80th spot (~41 of 3,272): the in-window species, spawning-only
        # species and quality on the card must equal what get_spot_detail
        # (the spot page's own function) computes.
        checked = 0
        for row in self.spots[::80]:
            detail = data.get_spot_detail(self.conn, row["lat"], row["lon"], row["n"])
            self.assertIsNotNone(detail, row["n"])
            activity = detail["species_activity"]
            in_window = sorted(r["species"] for r in activity["active"]
                               if r.get("activity") and r["activity"]["inside_window"])
            spawn_only = sorted(r["species"] for r in activity["active"]
                                if not (r.get("activity") and r["activity"]["inside_window"]))
            self.assertEqual(sorted(x[0] for x in row["a"]), in_window, row["n"])
            self.assertEqual(sorted(row["s"]), spawn_only, row["n"])
            self.assertEqual(sorted(x[0] for x in row["i"]), sorted(r["species"] for r in activity["inactive"]), row["n"])
            resolution = (detail["temperature"] or {}).get("resolution")
            expected_q = {"matched_waterbody_real": "real", "interpolated_nearby": "estimated",
                          "matched_waterbody_proxy": "proxy", "spot_air_proxy": "proxy"}.get(resolution)
            self.assertEqual(row["q"], expected_q, row["n"])
            checked += 1
        self.assertGreaterEqual(checked, 40)

    def test_no_spot_is_left_without_a_temperature(self):
        self.assertEqual([r["n"] for r in self.spots if r["q"] is None], [])

    def test_a_spot_without_any_windowed_species_is_only_ever_for_a_documented_reason(self):
        # Every spot has species evidence. A spot can still show no windowed species
        # when everything documented there is a species whose feeding window has not
        # been researched to the project's standard (Lake Sturgeon: only aquaculture
        # rearing studies exist; Cisco: ambiguous source table; Fathead Minnow: not a
        # target). Those spots say so on their page; this pins the list so a new
        # unexplained gap cannot appear unnoticed.
        unresearched = {"LAKE STURGEON", "CISCO", "FATHEAD MINNOW"}
        gaps = [r for r in self.spots if not (r["a"] or r["s"] or r["i"])]
        self.assertLessEqual(len(gaps), 5)
        for r in gaps:
            detail = data.get_spot_detail(self.conn, r["lat"], r["lon"], r["n"])
            cats = detail["species_categories"]
            names = {e["species"] for e in cats["confirmed_sightings"] + cats["likely_species"]}
            self.assertTrue(names, r["n"])
            self.assertTrue(names <= unresearched, (r["n"], names))

    def test_the_feed_contains_nothing_about_a_visitor(self):
        blob = json.dumps(self.feed).lower()
        for word in ("prefer", "target", "saved", "session", "cookie", "user"):
            self.assertNotIn(word, blob)


class FeedRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_route_serves_the_feed_gzipped_with_an_etag(self):
        resp = self.client.get("/recommend/feed.json", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Encoding"], "gzip")
        self.assertEqual(resp.mimetype, "application/json")
        body = json.loads(gzip.decompress(resp.data))
        self.assertGreater(len(body["spots"]), 3000)
        self.assertTrue(resp.headers["ETag"])
        self.assertIn("max-age", resp.headers["Cache-Control"])

    def test_a_matching_etag_gets_a_304_with_no_body(self):
        etag = self.client.get("/recommend/feed.json").headers["ETag"]
        resp = self.client.get("/recommend/feed.json", headers={"If-None-Match": etag})
        self.assertEqual(resp.status_code, 304)
        self.assertEqual(resp.data, b"")

    def test_plain_json_is_served_when_gzip_is_not_accepted(self):
        resp = self.client.get("/recommend/feed.json", headers={"Accept-Encoding": "identity"})
        self.assertNotIn("Content-Encoding", resp.headers)
        self.assertIn("spots", json.loads(resp.data))

    def test_the_feed_ignores_anything_a_visitor_might_send(self):
        plain = self.client.get("/recommend/feed.json").data
        with_location = self.client.get("/recommend/feed.json?lat=43.07&lon=-89.4&species=WALLEYE").data
        self.assertEqual(plain, with_location)

    def test_the_feed_is_not_counted_as_a_page_view(self):
        self.assertIn("/recommend/feed", flask_app_module.EXCLUDED_PAGEVIEW_PREFIXES)

    def test_the_feed_is_read_only(self):
        self.assertEqual(self.client.post("/recommend/feed.json").status_code, 405)


class RecommendedScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.body = flask_app_module.app.test_client().get("/").data.decode()

    def test_the_home_page_leads_with_search_and_quick_links_then_recommended(self):
        self.assertLess(self.body.index('id="quick-links"'), self.body.index('id="recommended"'))
        self.assertLess(self.body.index('role="search"'), self.body.index('id="quick-links"'))
        self.assertEqual(len(re.findall(r"<h1[ >]", self.body)), 1)

    def test_saved_spots_come_first_then_recommended_spots_as_in_the_wireframe(self):
        self.assertLess(self.body.index("Saved Spots"), self.body.index("Recommended Spots"))

    def test_the_saved_section_is_always_shown_with_an_empty_state(self):
        self.assertNotRegex(self.body, r'id="saved-section"[^>]*hidden')
        self.assertIn("No saved spots yet", self.body)

    def test_the_disclosure_is_in_the_html_not_only_added_by_script(self):
        self.assertIn("This is not a prediction of catch success.", self.body)

    def test_saved_spots_are_still_described_as_never_uploaded(self):
        self.assertIn("never uploaded anywhere", self.body)

    def test_the_screen_loads_the_ranking_and_glue_scripts(self):
        for name in ("prefs.js", "recommend.js", "recommended.js"):
            self.assertIn("/static/" + name, self.body)

    def test_the_no_javascript_case_is_explained(self):
        self.assertIn("<noscript>", self.body)


class ExploreRankedListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()
        cls.body = cls.client.get("/map").data.decode()

    def test_the_list_offers_best_match_nearest_and_a_to_z(self):
        block = self.body[self.body.index('id="sort-select"'):][:400]
        for value in ("ranked", "nearest", "az"):
            self.assertIn('value="%s"' % value, block)
        self.assertIn("disabled", block[block.index('value="nearest"'):][:40])  # until a location is shared

    def test_the_preferences_chip_is_visible_markup_with_a_clear_control(self):
        self.assertIn('id="prefs-chip"', self.body)
        self.assertIn("Using your preferences", self.body)
        self.assertIn('id="prefs-chip-clear"', self.body)

    def test_a_disclosure_line_sits_above_the_list(self):
        self.assertLess(self.body.index('id="explore-disclosure"'), self.body.index('id="access-list"'))

    def test_explore_loads_the_shared_ranking_scripts(self):
        for name in ("prefs.js", "recommend.js"):
            self.assertIn("/static/" + name, self.body)

    def test_reset_filters_appears_only_when_a_filter_is_active(self):
        self.assertNotIn('class="explore-reset"', self.body)
        self.assertIn('class="explore-reset"', self.client.get("/map?county=Dane").data.decode())

    def test_toggle_still_comes_before_filters_before_the_list(self):
        toggle = self.body.index("explore-view-toggle")
        filters = self.body.index('id="explore-filter-panel"')
        layout = self.body.index('id="explore-layout"')
        self.assertLess(toggle, filters)
        self.assertLess(filters, layout)

    def test_filters_view_and_sort_survive_the_nav_via_session_storage_only(self):
        self.assertIn("sessionStorage", self.body)
        self.assertIn("fishin.explore.v1", self.body)
        self.assertNotIn("localStorage.setItem('fishin.explore", self.body)

    def test_the_old_deep_links_still_resolve(self):
        for path in ("/map?waterbody=Devils+Lake", "/map?species=WALLEYE", "/map?source_type=boat_ramp&county=Dane"):
            self.assertEqual(self.client.get(path).status_code, 200, path)


class NothingPersonalLeavesTheDevice(unittest.TestCase):
    """Static check on the scripts that touch preferences, location and saved
    spots: the only network call allowed is the parameterless feed download."""

    def test_only_the_feed_is_ever_fetched(self):
        for name in ("recommend.js", "recommended.js", "prefs.js"):
            src = (STATIC / name).read_text(encoding="utf-8")
            for forbidden in ("XMLHttpRequest", "sendBeacon", "WebSocket", "navigator.sendBeacon", "method: \"POST\""):
                self.assertNotIn(forbidden, src, f"{name}: {forbidden}")
            fetches = re.findall(r"fetch\(([^)]*)\)", src)
            self.assertLessEqual(len(fetches), 1, name)
            for call in fetches:
                self.assertTrue(call.strip().startswith("window.FISHIN_FEED_URL"), f"{name}: {call}")

    def test_the_ranking_module_has_no_network_access_at_all(self):
        src = (STATIC / "recommend.js").read_text(encoding="utf-8")
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "localStorage", "Math.random"):
            self.assertNotIn(forbidden, src)

    def test_location_is_neither_stored_nor_put_in_a_url(self):
        src = (STATIC / "recommended.js").read_text(encoding="utf-8")
        self.assertNotIn("setItem", src)
        self.assertNotRegex(src, r"FISHIN_FEED_URL\s*\+")


if __name__ == "__main__":
    unittest.main()
