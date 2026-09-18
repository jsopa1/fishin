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
            self.assertTrue(e["pd_templates_on_page"], f"{group}/{key}: no public-domain template recorded")
            self.assertTrue(urllib.parse.unquote(e["page_url"]).startswith("https://commons.wikimedia.org/wiki/File:"), f"{group}/{key}")
            self.assertTrue(e["artist"].strip() or e["credit"].strip(), f"{group}/{key}: no author/credit")

    def test_every_manifest_file_exists(self):
        for group, key, e in _entries(self.m):
            if "file" in e:
                self.assertTrue((ROOT / e["file"]).is_file(), f"{group}/{key}: {e['file']} missing")

    def test_no_image_ships_without_a_manifest_entry(self):
        recorded = {(ROOT / e["file"]).resolve() for _, _, e in _entries(self.m) if "file" in e}
        on_disk = {p.resolve() for p in (ROOT / "webapp" / "static" / "img").rglob("*")
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")}
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


if __name__ == "__main__":
    unittest.main()
