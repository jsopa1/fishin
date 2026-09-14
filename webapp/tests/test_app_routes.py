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
from unittest import mock

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
        self.assertEqual(resp.data.count(b'class="list-card"'), 3)

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

    def test_data_freshness_visible_on_every_page(self):
        # Freshness must always be disclosed, but it no longer shouts from a
        # full-width banner when nothing is actually stale -- the two clocks
        # (fast-moving temperature, annual survey data) are reported
        # separately in the footer instead.
        for path in ("/", "/browse", "/failures", "/summary", "/map"):
            resp = self.client.get(path)
            self.assertIn(b"Water temperatures updated", resp.data, msg=f"freshness missing on {path}")
            self.assertIn(b"species &amp; stocking records", resp.data, msg=f"survey age missing on {path}")

    def test_scope_statement_present_on_every_page(self):
        # The honest framing moved out of the full-width bar, but it must
        # still appear on every page -- quieter, not gone.
        for path in ("/", "/browse", "/map"):
            resp = self.client.get(path)
            self.assertIn(b"does not predict whether you", resp.data, msg=f"scope note missing on {path}")

    def test_stale_temperature_still_raises_a_visible_banner(self):
        # The banner isn't deleted, it's conditional: when temperatures
        # genuinely age out, users are still told plainly.
        with mock.patch.object(flask_app_module.data, "is_stale", return_value=True):
            resp = self.client.get("/")
        self.assertIn(b'class="banner', resp.data)
        self.assertIn(b"Water temperatures last updated", resp.data)

    def test_attribution_footer_present(self):
        resp = self.client.get("/")
        self.assertIn(b"Wisconsin Department of Natural Resources", resp.data)
        self.assertIn(b"U.S. Geological Survey", resp.data)
        self.assertIn(b"National Weather Service", resp.data)

    def test_map_page_loads_and_shows_real_counts(self):
        import v1_review_data as data

        conn = flask_app_module.get_conn()
        meta = data.get_access_points_meta(conn)
        conn.close()

        resp = self.client.get("/map")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("{:,}".format(meta["total_boat_ramp"]).encode(), resp.data)
        self.assertIn("{:,}".format(meta["total_shore_fishing"]).encode(), resp.data)

    def test_map_data_endpoint_returns_real_points(self):
        resp = self.client.get("/map/data")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertFalse(payload["data_unavailable"])
        self.assertGreater(len(payload["points"]), 0)
        point = payload["points"][0]
        for field in ("source_type", "waterbody_name", "county", "lat", "lon"):
            self.assertIn(field, point)

    def test_map_data_filters_by_source_type(self):
        resp = self.client.get("/map/data?source_type=shore_fishing")
        payload = resp.get_json()
        self.assertGreater(len(payload["points"]), 0)
        self.assertTrue(all(p["source_type"] == "shore_fishing" for p in payload["points"]))

    def test_map_data_filters_by_waterbody_name(self):
        resp = self.client.get("/map/data?waterbody=Devils+Lake")
        payload = resp.get_json()
        self.assertGreater(len(payload["points"]), 0)
        self.assertTrue(all("devils lake" in p["waterbody_name"].lower()
                             or (p["matched_waterbody_name"] and "devils lake" in p["matched_waterbody_name"].lower())
                             for p in payload["points"]))

    def test_map_data_filters_by_species_matches_shore_fishing_and_v1_sources(self):
        resp = self.client.get("/map/data?species=Walleye")
        payload = resp.get_json()
        self.assertGreater(len(payload["points"]), 0)
        # Every point matched via one real source or the other -- either
        # WDNR's own shore-fishing species text (matched through the
        # canonical-species table, so a real WDNR typo like "WALEYE"
        # still counts -- not just a literal "WALLEYE" substring), or a
        # V1 species_predictions record for its matched waterbody.
        for p in payload["points"]:
            via_shore_fishing = p["fish_species_raw"] is not None
            via_v1_match = p["matched_waterbody_name"] is not None
            self.assertTrue(via_shore_fishing or via_v1_match, msg=p)

    def test_map_data_species_filter_matches_real_wdnr_typo_via_canonicalization(self):
        # Regression check: site 137 (Silver Lake Fishing Pier, Columbia
        # County) lists "WALEYE" (a real WDNR typo, missing an L) --
        # filtering for "Walleye" must still find it via the canonical
        # species table, not just a literal substring match on the raw text.
        resp = self.client.get("/map/data?species=Walleye")
        payload = resp.get_json()
        site_names = [p["facility_name"] for p in payload["points"]]
        self.assertIn("Silver Lake Fishing Pier", site_names)

    def test_map_data_shore_fishing_species_not_truncated_by_parenthetical_comma(self):
        # Regression check for the real WDNR site (ID 109/Council Grounds
        # State Park) whose species text nests a comma inside parens --
        # a naive split would have shown "BASS (LG. MOUTH" without its
        # closing paren.
        resp = self.client.get("/map/data?source_type=shore_fishing")
        payload = resp.get_json()
        combined = " | ".join(p["fish_species_raw"] or "" for p in payload["points"])
        self.assertNotIn("BASS (LG. MOUTH |", combined)
        self.assertNotIn("BASS (SMALLMOUTH |", combined)

    def test_map_page_shows_species_filter_dropdown(self):
        resp = self.client.get("/map")
        self.assertIn(b'name="species"', resp.data)
        self.assertIn(b"Walleye", resp.data)

    def test_map_page_shows_view_toggle(self):
        resp = self.client.get("/map")
        self.assertIn(b"toggle-map-btn", resp.data)
        self.assertIn(b"toggle-list-btn", resp.data)

    def test_map_points_linked_to_real_waterbody_have_valid_link_target(self):
        resp = self.client.get("/map/data")
        payload = resp.get_json()
        linked = [p for p in payload["points"] if p["matched_waterbody_name"]]
        self.assertGreater(len(linked), 0)
        sample = linked[0]
        wb_resp = self.client.get(
            "/waterbody?name=" + sample["matched_waterbody_name"] + "&county=" + sample["matched_county"]
        )
        self.assertEqual(wb_resp.status_code, 200)

    def test_map_page_shows_invasive_species_count(self):
        import v1_review_data as data

        conn = flask_app_module.get_conn()
        invasive_meta = data.get_invasive_species_meta(conn)
        conn.close()

        resp = self.client.get("/map")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("{:,}".format(invasive_meta["total_sightings"]).encode(), resp.data)

    def test_invasive_species_data_endpoint_returns_real_sightings(self):
        resp = self.client.get("/map/invasive-species-data")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertFalse(payload["data_unavailable"])
        self.assertGreater(len(payload["sightings"]), 0)
        sighting = payload["sightings"][0]
        for field in ("species_common_name", "species_scientific_name", "taxon_group", "lat", "lon"):
            self.assertIn(field, sighting)

    def test_invasive_species_data_filters_by_species(self):
        resp = self.client.get("/map/invasive-species-data?species=Zebra+Mussel")
        payload = resp.get_json()
        self.assertGreater(len(payload["sightings"]), 0)
        self.assertTrue(all(s["species_common_name"] == "Zebra Mussel" for s in payload["sightings"]))

    def test_invasive_species_sightings_not_linked_to_waterbody_fields(self):
        # Deliberate design: these are a standalone real layer, not joined
        # to V1 waterbody records (see docs/v2_access_points_report.md).
        resp = self.client.get("/map/invasive-species-data")
        payload = resp.get_json()
        sighting = payload["sightings"][0]
        self.assertNotIn("matched_waterbody_name", sighting)

    def test_spot_report_loads_for_a_matched_real_point(self):
        map_resp = self.client.get("/map/data")
        points = map_resp.get_json()["points"]
        matched = next(p for p in points if p["matched_waterbody_name"])

        resp = self.client.get(
            "/spot?lat={}&lon={}&name={}".format(matched["lat"], matched["lon"], matched["facility_name"] or "")
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(matched["waterbody_name"].encode(), resp.data)

    def test_spot_report_loads_for_an_unmatched_real_point_honest_gaps(self):
        map_resp = self.client.get("/map/data")
        points = map_resp.get_json()["points"]
        unmatched = next(p for p in points if not p["matched_waterbody_name"])

        resp = self.client.get(
            "/spot?lat={}&lon={}&name={}".format(unmatched["lat"], unmatched["lon"], unmatched["facility_name"] or "")
        )
        self.assertEqual(resp.status_code, 200)
        # A spot with no record of its own now shows real county-level
        # evidence instead of a dead end -- but it must say plainly that
        # this is regional context, not this water's species list.
        self.assertIn(b"Regional guide", resp.data)
        self.assertIn(b"not a species list for this water", resp.data)
        self.assertIn(b"no fisheries-survey or stocking record tied to this specific spot", resp.data)

    def test_regional_evidence_never_claims_species_are_in_this_water(self):
        # The honesty property that makes the county fallback defensible:
        # counts are always attributed to county waterbodies, and the page
        # never asserts presence at the spot itself.
        map_resp = self.client.get("/map/data")
        points = map_resp.get_json()["points"]
        unmatched = next(p for p in points if not p["matched_waterbody_name"])
        resp = self.client.get("/spot?lat={}&lon={}".format(unmatched["lat"], unmatched["lon"]))
        body = resp.data.decode()

        self.assertIn("documented in", body)
        self.assertIn("waterbod", body)
        self.assertIn("isn't evidence", body)  # absence-is-not-proof caveat

    def test_interpolated_temperature_carries_a_measured_confidence_signal(self):
        map_resp = self.client.get("/map/data")
        points = map_resp.get_json()["points"]
        # Find a spot whose temperature actually resolves by interpolation.
        for p in points[:60]:
            resp = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"]))
            if b"estimated from nearby real readings" in resp.data:
                body = resp.data.decode()
                self.assertIn("confidence", body)
                self.assertIn("Typically accurate to about", body)
                # Never a fabricated probability (Decision #005).
                self.assertNotIn("% confident", body)
                return
        self.skipTest("no interpolated spot found in the sampled points")

    def test_spot_report_404_for_coordinates_matching_no_real_point(self):
        resp = self.client.get("/spot?lat=0.0&lon=0.0")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"Not found", resp.data)

    def test_spot_report_400_for_missing_coordinates(self):
        resp = self.client.get("/spot")
        self.assertEqual(resp.status_code, 400)

    def test_map_popup_links_to_spot_report(self):
        resp = self.client.get("/map")
        self.assertIn(b"Full spot report", resp.data)
        self.assertIn(b"spotUrl", resp.data)


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
        self.assertGreater(resp.data.count(b'class="list-card"'), 0)

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

            resp = self.client.get("/map")
            self.assertEqual(resp.status_code, 503)
            self.assertIn(b"currently unavailable", resp.data)

            resp = self.client.get("/map/data")
            self.assertEqual(resp.status_code, 503)
            self.assertTrue(resp.get_json()["data_unavailable"])

            resp = self.client.get("/map/invasive-species-data")
            self.assertEqual(resp.status_code, 503)
            self.assertTrue(resp.get_json()["data_unavailable"])
        finally:
            rd.find_db_path = original


if __name__ == "__main__":
    unittest.main()


class ProductionReadinessTests(unittest.TestCase):
    """Things a publicly-launched site needs that a review tool doesn't."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_healthz_reports_ok_and_a_real_row_count(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertGreater(payload["waterbodies"], 0)

    def test_healthz_degrades_to_503_when_the_database_is_gone(self):
        # A process that boots but can't read its data is not healthy.
        with mock.patch.object(flask_app_module, "get_conn", return_value=None):
            resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.get_json()["status"], "degraded")

    def test_robots_allows_the_product_and_hides_the_diagnostics(self):
        body = self.client.get("/robots.txt").data.decode()
        self.assertIn("Disallow: /failures", body)
        self.assertIn("Disallow: /summary", body)
        self.assertIn("Sitemap:", body)

    def test_sitemap_lists_the_real_pages(self):
        body = self.client.get("/sitemap.xml").data.decode()
        self.assertIn("/map", body)
        self.assertIn("/browse", body)

    def test_share_preview_tags_present_so_shared_links_render_a_card(self):
        body = self.client.get("/").data.decode()
        self.assertIn('property="og:title"', body)
        self.assertIn('property="og:image"', body)
        self.assertIn('name="twitter:card"', body)

    def test_share_card_image_is_served(self):
        resp = self.client.get("/static/share-card.png")
        self.assertEqual(resp.status_code, 200)

    def test_feedback_route_is_reachable_from_every_page(self):
        for path in ("/", "/map", "/browse"):
            self.assertIn(b"Report a problem", self.client.get(path).data)


class RegulationsPointerTests(unittest.TestCase):
    """Anglers are legally required to check bag and length limits. The app
    must point at the authoritative source without restating rules that
    change between seasons -- a stale copy here could cost someone a
    citation."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _a_spot(self):
        points = self.client.get("/map/data").get_json()["points"]
        return points[0]

    def test_spot_page_always_routes_the_reader_to_official_regulations(self):
        # Whether the live lookup resolved a water, found several, or found
        # none, the page must always end up pointing at WDNR.
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data
        self.assertIn(b"apps.dnr.wi.gov/fisheriesmanagement/Public/LakeRegulation", body)
        self.assertTrue(
            b"Check the regulations before you keep anything" in body
            or b"Regulations for this water" in body,
            msg="spot page showed neither resolved regulations nor the fallback pointer",
        )

    def test_any_displayed_limits_are_wdnrs_own_dated_and_verifiable(self):
        # Regulations may now be shown, but only because they come verbatim
        # from WDNR's live service. If limits ever appear, three things must
        # appear with them: whose words they are, when they were retrieved,
        # and a link to verify. Hand-written limits would fail this.
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        lowered = body.lower()
        shows_limits = any(c in lowered for c in ("daily bag limit", "minimum length"))
        if shows_limits:
            self.assertIn("WDNR's own wording", body)
            self.assertIn("retrieved", lowered)
            self.assertIn("verify with WDNR", body)
            self.assertIn("apps.dnr.wi.gov/fisheriesmanagement", body)

    def test_regulations_are_never_matched_by_name_alone(self):
        # Wisconsin has eleven unrelated waters called "Devils Lake" with
        # different walleye rules. The page must say it matched on
        # coordinates, so a reader knows it isn't a name guess.
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        if "Regulations for this water" in body:
            self.assertIn("coordinates rather than by", body)
