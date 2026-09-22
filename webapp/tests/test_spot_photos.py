"""Spot photos: shown only when a verified photo exists, credited, with the map as the fallback.

The manifest is written by analysis/v4_find_spot_photos.py. These tests pin the lookup, the spot
page markup, the card fallback in recommend.js, and the finder's matching rules, using a temporary
manifest so they do not depend on what the last scan found.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ui"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "webapp"))

import v4_spot_photos as spot_photos  # noqa: E402
import v4_find_spot_photos as finder  # noqa: E402
import app as flask_app_module  # noqa: E402

RECOMMEND_JS = ROOT / "webapp" / "static" / "recommend.js"


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manifest = Path(self.tmp.name) / "m.json"
        self.manifest.write_text(json.dumps({"spots": [{
            "facility_name": "Middle Genesee Lake", "waterbody_name": "Middle Genesee Lake", "county": "Waukesha",
            "latitude": 43.0123, "longitude": -88.4567, "title": "File:Middle Genesee Lake.jpg", "distance_m": 4,
            "licence": "CC BY-SA 3.0", "author": "Awkwafaba", "page_url": "https://commons.wikimedia.org/wiki/File:X.jpg",
            "file": "img/spots/abc.jpg"}]}), encoding="utf-8")
        self.saved = spot_photos.MANIFEST
        spot_photos.MANIFEST = self.manifest
        spot_photos._cache.update(mtime=None, index={})

    def tearDown(self):
        spot_photos.MANIFEST = self.saved
        spot_photos._cache.update(mtime=None, index={})
        self.tmp.cleanup()

    def test_a_listed_spot_gets_its_photo_and_credit(self):
        p = spot_photos.lookup("Middle Genesee Lake", 43.0123, -88.4567)
        self.assertEqual(p["static_path"], "img/spots/abc.jpg")
        self.assertEqual(p["title"], "Middle Genesee Lake")
        self.assertEqual(p["credit"], "Awkwafaba, CC BY-SA 3.0")

    def test_an_unlisted_spot_or_bad_coordinates_gets_nothing(self):
        self.assertIsNone(spot_photos.lookup("Somewhere Else", 43.0123, -88.4567))
        self.assertIsNone(spot_photos.lookup("Middle Genesee Lake", None, "x"))

    def test_a_missing_manifest_means_no_photos_not_an_error(self):
        spot_photos.MANIFEST = Path(self.tmp.name) / "absent.json"
        spot_photos._cache.update(mtime=None, index={})
        self.assertIsNone(spot_photos.lookup("Middle Genesee Lake", 43.0123, -88.4567))


class SpotPageTests(unittest.TestCase):
    def test_the_photo_figure_is_credited_and_absent_without_a_photo(self):
        client = flask_app_module.app.test_client()
        point = client.get("/map/data").get_json()["points"][0]
        url = "/spot?lat={}&lon={}&name={}".format(point["lat"], point["lon"], point["n"])
        body = client.get(url).data.decode()
        original = flask_app_module.spot_photos.lookup
        try:
            flask_app_module.spot_photos.lookup = lambda *a: None
            self.assertNotIn('class="spot-photo"', client.get(url).data.decode())
            flask_app_module.spot_photos.lookup = lambda *a: {
                "static_path": "img/spots/abc.jpg", "title": "A lake", "distance_m": 12,
                "credit": "Someone, CC BY 4.0", "page_url": "https://commons.wikimedia.org/wiki/File:A.jpg"}
            with_photo = client.get(url).data.decode()
        finally:
            flask_app_module.spot_photos.lookup = original
        self.assertIn('class="spot-photo"', with_photo)
        self.assertIn("Someone, CC BY 4.0", with_photo)
        self.assertIn("12 m from this spot", with_photo)
        self.assertIn('alt="A lake"', with_photo)
        self.assertTrue(body)


@unittest.skipUnless(shutil.which("node"), "Node is not installed")
class CardTests(unittest.TestCase):
    def test_cards_prefer_a_photo_then_the_map_and_credit_the_photo(self):
        script = (
            "const R=require(process.argv[1]);"
            "const base={name:'X',water:'W',county:'C',type:'boat_ramp',quality:'real',tempC:20,count:0,confirmed:0,inRange:[],spawning:[],nearest:null,distanceKm:null,url:'/s',lat:43.07,lon:-89.4};"
            "const a=R.cardHtml(base);"
            "const b=R.cardHtml(Object.assign({},base,{photo:'img/spots/abc.jpg',photoCredit:'Ann, CC BY 4.0'}));"
            "console.log(JSON.stringify({mapOnly:/openstreetmap/.test(a)&&!/card-photo/.test(a),"
            "photo:/card-photo/.test(b)&&/img\\/spots\\/abc\\.jpg/.test(b)&&!/openstreetmap/.test(b),credit:/Photo: Ann, CC BY 4\\.0/.test(b)&&!/Photo:/.test(a)}));"
        )
        out = json.loads(subprocess.run(["node", "-e", script, str(RECOMMEND_JS)], capture_output=True, text=True, check=True).stdout)
        for key, value in out.items():
            self.assertTrue(value, key)


class CandidateSelectionTests(unittest.TestCase):
    """End-to-end through candidates_for() with the network call stubbed, so the interaction between
    the facility/water match paths and BARE_PLACE_PHOTO is verified, not just the regexes alone."""

    def _run(self, point, titles_and_distances):
        def fake_api(params, retries=3):
            return {"query": {"geosearch": [{"title": t, "dist": d} for t, d in titles_and_distances]}}

        original = finder.api
        finder.api = fake_api
        try:
            return finder.candidates_for(point)
        finally:
            finder.api = original

    def test_a_bare_town_photo_is_dropped_when_only_the_facility_name_matches(self):
        point = {"facility_name": "Lynxville Landing", "waterbody_name": "Mississippi River", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Lynxville, Wisconsin-1.jpg", 50)])
        self.assertEqual(out, [])

    def test_a_bare_town_photo_is_kept_when_it_also_names_the_waterbody_with_a_water_word(self):
        point = {"facility_name": "Rice Lake Access", "waterbody_name": "Rice Lake", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Rice Lake, Wisconsin.jpg", 20)])
        self.assertEqual([c["title"] for c in out], ["File:Rice Lake, Wisconsin.jpg"])

    def test_an_excluded_building_is_dropped_even_when_very_close(self):
        point = {"facility_name": "Mendota County Park Boat Launch", "waterbody_name": "Lake Mendota", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Parking lot in Mendota County Park.jpg", 5)])
        self.assertEqual(out, [])

    def test_a_facility_match_with_no_water_word_in_the_title_is_dropped(self):
        # Regression: "Bukolt Park Sign.jpg" shares "bukolt" with the facility name and is close by,
        # but a signpost is not a photo of the water, and its title says nothing about water either.
        point = {"facility_name": "Bukolt Park Boat Launch", "waterbody_name": "Wisconsin River", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Bukolt Park Sign.jpg", 174)])
        self.assertEqual(out, [])

    def test_a_genuine_facility_photo_within_range_is_kept(self):
        point = {"facility_name": "Petenwell Powerhouse and Landing", "waterbody_name": "Wisconsin River", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Petenwell Lake and dam.jpg", 144)])
        self.assertEqual([c["title"] for c in out], ["File:Petenwell Lake and dam.jpg"])

    def test_a_facility_match_past_the_tightened_distance_is_dropped(self):
        point = {"facility_name": "Petenwell Powerhouse and Landing", "waterbody_name": "Wisconsin River", "latitude": 0, "longitude": 0}
        out = self._run(point, [("File:Petenwell Lake and dam.jpg", 250)])  # 250 m > FACILITY_MAX_M (200 m)
        self.assertEqual(out, [])


class FinderRuleTests(unittest.TestCase):
    def test_licences_never_include_noncommercial_or_noderivatives(self):
        for ok in ("Public domain", "CC0", "CC BY 4.0", "CC BY-SA 3.0", "CC BY 2.0"):
            self.assertTrue(finder.ALLOWED_LICENCES.match(ok), ok)
        for bad in ("CC BY-NC 4.0", "CC BY-ND 2.0", "CC BY-NC-SA 3.0", "All rights reserved", ""):
            self.assertFalse(finder.ALLOWED_LICENCES.match(bad), bad)

    def test_other_places_and_non_photos_are_rejected(self):
        for title in ("File:Spring Harbor Middle School.jpg", "File:Middleton Shores Apartments.jpg", "File:Olbrich Botanical Gardens.jpg"):
            self.assertTrue(finder.OTHER_PLACES.search(title), title)
        for title in ("File:ISS048-E-57295 - View of Earth.jpg", "File:Plat map.jpg", "File:Aerial view.tif"):
            self.assertTrue(finder.REJECT_TITLE.search(title), title)
        self.assertFalse(finder.OTHER_PLACES.search("File:Middle Genesee Lake.jpg"))

    def test_a_batch_of_real_wrong_matches_found_in_review_are_all_rejected(self):
        # Regression: a first full scan matched these to spots by a shared place-name word even
        # though none of them show water -- a courthouse, a grocery-store sign, a parking lot, a
        # water tower, a wastewater plant, a burial mound, a train, and a memorial plaza. Each must
        # be excluded on title alone, independent of distance or which spot it was found near.
        wrong = (
            "File:Water tower, Star Prairie, Wisconsin.jpg",
            "File:Green Lake County Courthouse.jpg",
            "File:Wauzeka schools.jpg",
            "File:Columbia Energy Center - panoramio - Corey Coyle.jpg",
            "File:Parking lot in Mendota County Park (53906842264).jpg",
            "File:Spring Harbor Mound Group.JPG",
            "File:La Crosse wastewater treatment facility-2.jpg",
            "File:Tower Hill State Park shelter.JPG",
            "File:19971011 15a BNSF Genoa, Wisconsin (6108912626).jpg",
            "File:Sign for Belle's Argyle Grocery (53911184426).jpg",
            "File:Traxler Park June 2024 7 (Veterans Memorial Plaza).jpg",
        )
        for title in wrong:
            self.assertTrue(finder.OTHER_PLACES.search(title), title)

    def test_a_bare_town_name_photo_is_trusted_only_when_it_also_carries_a_water_word(self):
        # "Town, Wisconsin.jpg" is a known Commons series (welcome signs, main streets) that says
        # nothing about water on its own; several were wrongly matched via a shared facility-name
        # word. It is accepted only through the water-name path, which requires a water word too.
        self.assertTrue(finder.BARE_PLACE_PHOTO.match("Lynxville, Wisconsin-1.jpg"))
        self.assertTrue(finder.BARE_PLACE_PHOTO.match("Strum, Wisconsin.jpg"))
        self.assertTrue(finder.BARE_PLACE_PHOTO.match("Rice Lake, Wisconsin.jpg"))
        self.assertFalse(finder.BARE_PLACE_PHOTO.match("Rice Lake Whitewater Wisconsin - panoramio (5).jpg"))

    def test_the_title_must_name_the_place(self):
        self.assertEqual(finder.tokens("Bukolt Park Boat Launch"), {"bukolt"})
        self.assertIn("genesee", finder.tokens("Middle Genesee Lake"))
        self.assertTrue(finder.WATER_WORDS.search("Middle Genesee Lake"))
        self.assertFalse(finder.WATER_WORDS.search("Baywood Drive"))


if __name__ == "__main__":
    unittest.main()
