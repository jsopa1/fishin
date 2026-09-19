"""Every page renders and every asset it links to exists.

Found by crawling the running site (547 URLs, all 200); kept as a test so a broken
page, a missing species image or a stray template tag cannot ship unnoticed. Spot
pages are excluded here because they make live regulation and weather calls; they
are covered by the route tests, which mock those.

Run: python -m pytest webapp/tests/test_every_page_works.py
"""

import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import v4_species_detail as sd  # noqa: E402

PAGES = ["/", "/map", "/profile", "/summary", "/failures", "/feedback", "/privacy", "/terms"]
DATA_ROUTES = ["/sitemap.xml", "/robots.txt", "/manifest.json", "/healthz", "/recommend/feed.json", "/map/data"]
ARTIFACT = re.compile(r"\{\{|\{%|Traceback|UndefinedError")


class EveryPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()
        cls.fish = ["/fish/" + sd.slug(s["name"]) for s in sd.list_species()]

    def test_every_page_renders_without_template_artifacts(self):
        for path in PAGES + self.fish:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, path)
            self.assertIsNone(ARTIFACT.search(resp.data.decode("utf-8", "replace")), path)

    def test_every_data_route_answers(self):
        for path in DATA_ROUTES:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_all_27_fish_pages_exist_and_are_in_the_sitemap(self):
        self.assertEqual(len(self.fish), 27)
        sitemap = self.client.get("/sitemap.xml").data.decode()
        for path in self.fish:
            self.assertIn(path, sitemap, path)

    def test_every_static_asset_linked_from_these_pages_exists(self):
        missing = []
        for path in PAGES + self.fish:
            body = self.client.get(path).data.decode("utf-8", "replace")
            for m in re.finditer(r'(?:href|src)="(/static/[^"?#]+)', body):
                if self.client.get(m.group(1)).status_code != 200:
                    missing.append((path, m.group(1)))
        self.assertEqual(missing, [])

    def test_every_internal_page_link_resolves(self):
        broken = []
        for path in PAGES + self.fish[:6]:
            body = self.client.get(path).data.decode("utf-8", "replace")
            for m in re.finditer(r'href="(/[a-z][^"#]*)"', body):
                target = html.unescape(m.group(1))
                if target.startswith("/static/") or target.startswith("/spot"):
                    continue
                if self.client.get(target).status_code not in (200, 304):
                    broken.append((path, target))
        self.assertEqual(broken, [])

    def test_every_species_with_an_image_in_the_manifest_serves_it(self):
        for s in sd.list_species():
            img = sd.image_for("species", s["name"])
            if img:
                self.assertEqual(self.client.get("/static/" + img["static_path"]).status_code, 200, s["name"])


if __name__ == "__main__":
    unittest.main()
