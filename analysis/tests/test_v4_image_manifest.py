"""Guards for the public-domain image set (docs/v4_ux_goal_loop_spec.md, Phase 0).

Every shipped image must have a manifest entry recording where it came from and
that it passed the two-part license check (Commons license field reads public
domain/CC0 AND a public-domain template exists on the file page). Every
manifest entry must point at a file that exists, and every file under
webapp/static/img must be in the manifest. Bait/species without an entry are
allowed - they render an honest no-image state - but nothing may ship
unrecorded.
"""

import json
import unittest
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "v1" / "image_manifest_v1.json"


def _entries(m):
    for group in ("species", "baits"):
        for key, e in m[group].items():
            yield group, key, e


class TestImageManifest(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_every_file_entry_passed_the_license_check_and_names_its_source(self):
        for group, key, e in _entries(self.m):
            if "file" not in e:
                continue
            self.assertTrue(e["license_short"].lower().startswith(("public domain", "cc0")), f"{group}/{key}")
            if e.get("original"):
                continue  # drawn for this project; checked in TestOriginalIllustrations
            self.assertTrue(e["pd_templates_on_page"], f"{group}/{key}: no public-domain template recorded")
            self.assertTrue(urllib.parse.unquote(e["page_url"]).startswith("https://commons.wikimedia.org/wiki/File:"), f"{group}/{key}")
            self.assertTrue(e["artist"].strip() or e["credit"].strip(), f"{group}/{key}: no author/credit")

    def test_every_manifest_file_exists(self):
        for group, key, e in _entries(self.m):
            if "file" in e:
                self.assertTrue((ROOT / e["file"]).is_file(), f"{group}/{key}: {e['file']} missing")

    def test_no_image_ships_without_a_manifest_entry(self):
        # img/spots/ is a separate namespace with its own manifest (data/v1/spot_photo_manifest_v1.json,
        # written by analysis/v4_find_spot_photos.py) and its own completeness test
        # (webapp/tests/test_spot_photos.py); this manifest only covers species and bait images.
        recorded = {(ROOT / e["file"]).resolve() for _, _, e in _entries(self.m) if "file" in e}
        on_disk = {p.resolve() for p in (ROOT / "webapp" / "static" / "img").rglob("*")
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
                   and "spots" not in p.relative_to(ROOT / "webapp" / "static" / "img").parts}
        self.assertEqual(on_disk - recorded, set())

    def test_reuse_entries_point_at_a_real_entry(self):
        for group, key, e in _entries(self.m):
            if "reuse_species_image" in e:
                self.assertIn("file", self.m["species"][e["reuse_species_image"]], f"{group}/{key}")
            if "reuse_bait_image" in e:
                self.assertIn("file", self.m["baits"][e["reuse_bait_image"]], f"{group}/{key}")

    def test_all_27_species_have_an_image(self):
        physiology = json.loads((ROOT / "data" / "v1" / "physiology_thresholds_v1.json").read_text(encoding="utf-8"))["species"]
        for sp in physiology:
            self.assertIn("file", self.m["species"].get(sp, {}), sp)


class TestEveryBaitHasAPicture(unittest.TestCase):
    def test_all_50_baits_resolve_to_an_image(self):
        import sys
        sys.path.insert(0, str(ROOT / "ui"))
        sys.path.insert(0, str(ROOT / "analysis"))
        import v4_species_detail as sd
        catalog = json.loads((ROOT / "data" / "v1" / "bait_catalog_v1.json").read_text(encoding="utf-8"))["baits"]
        self.assertEqual(len(catalog), 50)
        self.assertEqual([k for k in catalog if not sd.image_for("baits", k)], [])

    def test_illustrations_are_labelled_as_illustrations_not_as_commons_photos(self):
        import sys
        sys.path.insert(0, str(ROOT / "ui"))
        sys.path.insert(0, str(ROOT / "analysis"))
        import v4_species_detail as sd
        img = sd.image_for("baits", "leeches")
        self.assertTrue(img["illustration"])
        self.assertTrue(img["credit"].startswith("Illustration by"))
        self.assertNotIn("Wikimedia", img["credit"])
        photo = sd.image_for("baits", "spoons")
        self.assertFalse(photo["illustration"])
        self.assertIn("Wikimedia Commons", photo["credit"])


class TestOriginalIllustrations(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.originals = {k: e for _, k, e in _entries(self.m) if e.get("original")}

    def test_there_are_36_and_each_is_cc0_with_a_generator(self):
        self.assertEqual(len(self.originals), 36)
        for key, e in self.originals.items():
            self.assertTrue(e["license_short"].startswith("CC0"), key)
            self.assertEqual(e["license_url"], "https://creativecommons.org/publicdomain/zero/1.0/", key)
            self.assertEqual(e["generator"], "analysis/v4_draw_bait_illustrations.py", key)
            self.assertTrue(e["file"].endswith(".svg"), key)

    def test_each_file_is_well_formed_svg(self):
        import xml.dom.minidom as minidom
        for key, e in self.originals.items():
            doc = minidom.parse(str(ROOT / e["file"]))
            self.assertEqual(doc.documentElement.tagName, "svg", key)
            self.assertEqual(doc.documentElement.getAttribute("viewBox"), "0 0 320 200", key)

    def test_no_two_baits_share_the_same_drawing(self):
        import hashlib
        digests = {}
        for key, e in self.originals.items():
            digests.setdefault(hashlib.sha256((ROOT / e["file"]).read_bytes()).hexdigest(), []).append(key)
        self.assertEqual([v for v in digests.values() if len(v) > 1], [])

    def test_the_generator_reproduces_the_committed_files(self):
        import sys
        sys.path.insert(0, str(ROOT / "analysis"))
        import v4_draw_bait_illustrations as gen
        for key, fn in gen.DRAWERS.items():
            self.assertEqual(fn(), (ROOT / "webapp" / "static" / "img" / "baits" / f"{key}.svg").read_text(encoding="utf-8"), key)


if __name__ == "__main__":
    unittest.main()
