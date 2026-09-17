"""Basic route tests for the Flask web app (Part 5).

Uses Flask's test client against the real, already-generated
data/v1/v1_full_run_results.db -- not mock data -- to confirm every route
responds correctly and the data flowing through matches what the .exe
review tool and docs/v1_full_run_report.md show. Not full UI/browser
testing, just route-level correctness per this cycle's scope.

Run: python -m pytest webapp/tests/test_app_routes.py
"""

import os
import re
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
        for field in ("t", "w", "c", "lat", "lon"):
            self.assertIn(field, point)

    def test_map_data_filters_by_source_type(self):
        resp = self.client.get("/map/data?source_type=shore_fishing")
        payload = resp.get_json()
        self.assertGreater(len(payload["points"]), 0)
        self.assertTrue(all(p["t"] == "shore_fishing" for p in payload["points"]))

    def test_map_data_filters_by_waterbody_name(self):
        resp = self.client.get("/map/data?waterbody=Devils+Lake")
        payload = resp.get_json()
        self.assertGreater(len(payload["points"]), 0)
        self.assertTrue(all("devils lake" in p["w"].lower()
                             or (p["mw"] and "devils lake" in p["mw"].lower())
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
            via_shore_fishing = p["sp"] is not None
            via_v1_match = p["mw"] is not None
            self.assertTrue(via_shore_fishing or via_v1_match, msg=p)

    def test_map_data_species_filter_matches_real_wdnr_typo_via_canonicalization(self):
        # Regression check: site 137 (Silver Lake Fishing Pier, Columbia
        # County) lists "WALEYE" (a real WDNR typo, missing an L) --
        # filtering for "Walleye" must still find it via the canonical
        # species table, not just a literal substring match on the raw text.
        resp = self.client.get("/map/data?species=Walleye")
        payload = resp.get_json()
        site_names = [p["n"] for p in payload["points"]]
        self.assertIn("Silver Lake Fishing Pier", site_names)

    def test_map_data_shore_fishing_species_not_truncated_by_parenthetical_comma(self):
        # Regression check for the real WDNR site (ID 109/Council Grounds
        # State Park) whose species text nests a comma inside parens --
        # a naive split would have shown "BASS (LG. MOUTH" without its
        # closing paren.
        resp = self.client.get("/map/data?source_type=shore_fishing")
        payload = resp.get_json()
        combined = " | ".join(p["sp"] or "" for p in payload["points"])
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
        linked = [p for p in payload["points"] if p["mw"]]
        self.assertGreater(len(linked), 0)
        sample = linked[0]
        wb_resp = self.client.get(
            "/waterbody?name=" + sample["mw"] + "&county=" + sample["mc"]
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
        matched = next(p for p in points if p["mw"])

        resp = self.client.get(
            "/spot?lat={}&lon={}&name={}".format(matched["lat"], matched["lon"], matched["n"] or "")
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(matched["w"].encode(), resp.data)

    def test_spot_report_loads_for_an_unmatched_real_point_honest_gaps(self):
        map_resp = self.client.get("/map/data")
        points = map_resp.get_json()["points"]
        unmatched = next(p for p in points if not p["mw"])

        resp = self.client.get(
            "/spot?lat={}&lon={}&name={}".format(unmatched["lat"], unmatched["lon"], unmatched["n"] or "")
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
        unmatched = next(p for p in points if not p["mw"])
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


class CurrentConditionsTests(unittest.TestCase):
    """Wind and pressure are shown for trip planning only. Peer-reviewed
    research (and this project's own V0 null result) found no reliable
    direct link to fish behaviour, so nothing here may let wind or
    pressure act like an evidentiary claim."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _a_spot(self):
        points = self.client.get("/map/data").get_json()["points"]
        return points[0]

    def test_wind_and_pressure_are_labeled_as_not_used_in_the_match(self):
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data
        if b"mph" in body and b"not used in the match" not in body:
            self.fail("a wind reading appeared without its informational-only disclaimer")

    def test_missing_conditions_never_break_the_page(self):
        p = self._a_spot()
        resp = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"]))
        self.assertEqual(resp.status_code, 200)


class MoonPhaseTests(unittest.TestCase):
    """Requested directly by a real customer. Shown as plain astronomical
    fact -- evidence for a fish-activity effect is mixed at best (mostly
    tidal/saltwater mechanisms that don't apply to Wisconsin's inland
    waters), so this must never read as a match input or a score."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _a_spot(self):
        points = self.client.get("/map/data").get_json()["points"]
        return points[0]

    def test_moon_phase_shown_with_illumination_and_disclaimer(self):
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn("illuminated", body)
        self.assertIn("evidence for a fish-activity effect is mixed", body)
        self.assertIn("not used in the match above", body)

    def test_moon_phase_never_breaks_the_page(self):
        p = self._a_spot()
        resp = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"]))
        self.assertEqual(resp.status_code, 200)


class CitizenObservedSpeciesTests(unittest.TestCase):
    """GBIF/iNaturalist sightings (analysis/v3_gbif_species_observations.py)
    are a real but weaker tier than a WDNR survey -- must never appear
    without its disclaimer, and must never be silently present in the
    same list as WDNR-sourced species."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_citizen_sightings_always_carry_their_disclaimer(self):
        # Merton Millpond Access (Waukesha County) is a real access point
        # verified, at test-writing time, to sit within 5km of a real
        # ingested GBIF observation -- picked directly via the database
        # rather than scanning hundreds of live spot pages hoping for a
        # hit, which was slow enough to time out.
        body = self.client.get("/spot?lat=43.14873839628315&lon=-88.30695699204537").data
        self.assertIn(b"Recently reported nearby", body)
        self.assertIn(b"not a WDNR survey", body)
        self.assertIn(b"never used to drive the temperature matching", body)
        self.assertIn(b"gbif.org", body)

    def test_every_spot_page_still_loads_regardless_of_citizen_data(self):
        p = self.client.get("/map/data").get_json()["points"][0]
        resp = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"]))
        self.assertEqual(resp.status_code, 200)


class SpeciesDashboardTests(unittest.TestCase):
    """The two-category dashboard (Confirmed Sightings / Likely species to
    find) at the top of the spot page. The property that matters: a
    species never appears in both buckets, and the honesty caveats stay
    attached."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_dashboard_renders_both_category_headings_on_a_real_spot_with_data(self):
        # Merton Millpond Access -- verified elsewhere in this suite to
        # have real WDNR and citizen-sighting data nearby.
        body = self.client.get("/spot?lat=43.14873839628315&lon=-88.30695699204537").data
        self.assertIn(b"Confirmed Sightings", body)
        self.assertIn(b"Likely species to find", body)

    def test_dashboard_never_lists_the_same_species_in_both_buckets(self):
        p = self.client.get("/map/data").get_json()["points"][0]
        conn = flask_app_module.get_conn()
        detail = flask_app_module.data.get_spot_detail(conn, p["lat"], p["lon"])
        conn.close()
        cats = detail["species_categories"]
        confirmed = {s["species"] for s in cats["confirmed_sightings"]}
        likely = {s["species"] for s in cats["likely_species"]}
        self.assertEqual(confirmed & likely, set())

    def test_dashboard_note_explains_what_confirmed_and_likely_actually_mean(self):
        body = self.client.get("/spot?lat=43.14873839628315&lon=-88.30695699204537").data
        self.assertIn(b"actually documented the species", body)
        self.assertIn(b"never a catch guarantee", body)

    def test_every_spot_page_still_loads_with_the_dashboard_wired_in(self):
        p = self.client.get("/map/data").get_json()["points"][0]
        resp = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"]))
        self.assertEqual(resp.status_code, 200)


class ProductLoopTests(unittest.TestCase):
    """The things that make this a product someone returns to, rather
    than a data reference they read once."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _a_spot(self):
        return self.client.get("/map/data").get_json()["points"][0]

    def test_spot_page_opens_with_an_answer_not_a_data_dump(self):
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn('class="verdict', body)
        # The verdict must precede the evidence tabs.
        self.assertLess(body.index('class="verdict'), body.index('id="spot-tabs"'))

    def test_every_spot_gets_a_verdict_headline(self):
        # Never a blank answer, whatever the conditions.
        points = self.client.get("/map/data").get_json()["points"]
        for p in points[:12]:
            body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
            self.assertIn("verdict-headline", body, msg=f"no verdict at {p['lat']},{p['lon']}")

    def test_spot_page_offers_save_and_directions(self):
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn('id="save-spot"', body)
        self.assertIn("google.com/maps/dir", body)

    def test_saved_spots_never_leave_the_browser(self):
        # No endpoint accepts saved spots, and the page says so. Where
        # someone fishes is exactly the data not to upload.
        p = self._a_spot()
        body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn("localStorage", body)
        home = self.client.get("/").data.decode()
        self.assertIn("never uploaded anywhere", home)

    def test_explore_offers_spots_near_me(self):
        body = self.client.get("/map").data.decode()
        self.assertIn('id="locate-btn"', body)
        self.assertIn("Spots near me", body)

    def test_map_payload_stays_lean(self):
        # Regression guard: this was 2.07MB before trimming, which is a
        # real cost on cellular at a boat ramp.
        resp = self.client.get("/map/data")
        self.assertLess(len(resp.data), 900_000)
        point = resp.get_json()["points"][0]
        for heavy in ("directions", "additional_amenities", "property_manager", "ownership"):
            self.assertNotIn(heavy, point)


class ManifestTests(unittest.TestCase):
    """Installability: a real manifest with real icon files behind it, not
    just a link tag that points at nothing."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_manifest_route_returns_expected_mimetype_and_fields(self):
        resp = self.client.get("/manifest.json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/manifest+json")
        body = resp.get_json()
        self.assertEqual(body["name"], "fishin — Wisconsin Fishing Conditions")
        self.assertEqual(body["short_name"], "fishin")
        self.assertEqual(body["start_url"], "/")
        self.assertEqual(body["display"], "standalone")
        self.assertEqual(body["theme_color"], "#2456d6")

    def test_manifest_icons_cover_192_and_512_both_any_and_maskable(self):
        body = self.client.get("/manifest.json").get_json()
        sizes_purposes = {(i["sizes"], i["purpose"]) for i in body["icons"]}
        self.assertEqual(
            sizes_purposes,
            {("192x192", "any"), ("512x512", "any"), ("192x192", "maskable"), ("512x512", "maskable")},
        )

    def test_manifest_icon_files_actually_exist_on_disk(self):
        static_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
        body = self.client.get("/manifest.json").get_json()
        for icon in body["icons"]:
            rel = icon["src"].split("/static/", 1)[-1]
            self.assertTrue(
                os.path.exists(os.path.join(static_root, rel)),
                msg=f"manifest references {icon['src']} but no such file exists",
            )

    def test_manifest_linked_and_apple_touch_icon_present_on_home_page(self):
        body = self.client.get("/").data
        self.assertIn(b'rel="manifest"', body)
        self.assertIn(b"apple-touch-icon", body)


class TagOnboardingTests(unittest.TestCase):
    """The tag popover is wired by JS against classes already in the
    markup, not by editing templates -- so what's tested server-side is
    that the script is actually loaded, and that every tag value the
    templates can render has a matching explanation, so a new tag value
    can't silently ship unexplained."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def _a_spot(self):
        points = self.client.get("/map/data").get_json()["points"]
        return points[0]

    def test_tags_explainer_script_loaded_on_pages_with_tags(self):
        p = self._a_spot()
        for path in ("/", "/browse", "/spot?lat={}&lon={}".format(p["lat"], p["lon"])):
            body = self.client.get(path).data
            self.assertIn(b"tags-explainer.js", body, msg=f"{path} did not load the tags explainer")

    def test_tag_intro_banner_present_in_base_template(self):
        body = self.client.get("/").data
        self.assertIn(b'id="tag-intro-banner"', body)
        self.assertIn(b'id="tag-intro-dismiss"', body)

    def test_tag_vocabulary_in_js_covers_every_tag_class_used_in_templates(self):
        webapp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        js_path = os.path.join(webapp_dir, "static", "tags-explainer.js")
        with open(js_path, encoding="utf-8") as f:
            js_source = f.read()
        explained = set(re.findall(r'^\s*(\w+):\s*"', js_source, re.MULTILINE))
        self.assertTrue(explained, "could not parse any explanation keys out of tags-explainer.js")

        # Literal (non-templated) tag values used across every template --
        # the templated ones (presence_tier, confidence.level) only ever
        # render values already covered by these literals or the
        # confidence- prefix, which the JS handles as a special case.
        literal_values = {
            "survey_confirmed", "stocking_only", "real", "proxy",
            "estimated", "no_data", "evidence",
        }
        missing = literal_values - explained
        self.assertFalse(missing, f"tag values with no explanation in tags-explainer.js: {missing}")

        with open(js_path, encoding="utf-8") as f:
            self.assertIn('indexOf("confidence-")', f.read(), msg="confidence-* tags must stay handled as a prefix case")


class LegalPagesTests(unittest.TestCase):
    """The privacy/terms pages are a drafted starting point, not a
    substitute for real review -- but what they claim about the app's
    own behavior must actually be true, checked here rather than trusted
    to stay in sync by hand."""

    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    def test_privacy_and_terms_pages_load(self):
        self.assertEqual(self.client.get("/privacy").status_code, 200)
        self.assertEqual(self.client.get("/terms").status_code, 200)

    def test_privacy_and_terms_linked_from_every_page(self):
        for path in ("/", "/map", "/browse"):
            body = self.client.get(path).data
            self.assertIn(b'href="/privacy"', body)
            self.assertIn(b'href="/terms"', body)

    def test_privacy_page_states_it_is_a_draft_not_a_review(self):
        body = self.client.get("/privacy").data.decode().lower()
        self.assertIn("not a substitute for review", body)

    def test_privacy_pages_localstorage_claim_matches_actual_save_spot_behavior(self):
        # The privacy page claims saved spots never leave the browser --
        # this is the same guarantee test_saved_spots_never_leave_the_browser
        # (RegulationsPointerTests-adjacent, in ProductLoopTests below)
        # already enforces server-side. Re-assert both sides here so the
        # two can't silently drift apart.
        points = self.client.get("/map/data").get_json()["points"]
        p = points[0]
        spot_body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn("localStorage", spot_body)
        privacy_body = self.client.get("/privacy").data.decode().lower()
        self.assertIn("localstorage", privacy_body)
        self.assertIn("never sent to our server", privacy_body)
