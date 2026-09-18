#!/usr/bin/env python3
"""
Re-checks every image in data/v1/image_manifest_v1.json against the live
Wikimedia Commons file page: the license field must still read Public domain
(or CC0) and a public-domain template must still be present in the page
wikitext. Needs network access; not part of the unit-test suite.

Usage:
    python analysis/verify_v4_images.py
Exit status is 1 if any image no longer passes.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "data" / "v1" / "image_manifest_v1.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = "fishin-research/1.0 (https://github.com/jsopa1/fishin; image license verification)"
PD_TEMPLATE = re.compile(r"\{\{\s*(PD-[A-Za-z0-9\-_]+|Public domain|CC0|Cc-zero)", re.I)


def api(params: dict) -> dict:
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read())


def check(title: str) -> tuple:
    d = api({"action": "query", "titles": title, "prop": "imageinfo|revisions", "iiprop": "extmetadata",
             "rvprop": "content", "rvslots": "main", "format": "json"})
    page = next(iter(d["query"]["pages"].values()))
    if "imageinfo" not in page:
        return False, "file no longer exists"
    lic = re.sub(r"<[^>]+>", "", page["imageinfo"][0]["extmetadata"].get("LicenseShortName", {}).get("value", "")).strip()
    templates = sorted({m.group(1) for m in PD_TEMPLATE.finditer(page["revisions"][0]["slots"]["main"]["*"])})
    ok = lic.lower().startswith(("public domain", "cc0")) and bool(templates)
    return ok, f"{lic} {templates}"


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = checked = 0
    for group in ("species", "baits"):
        for key, e in m[group].items():
            if "commons_title" not in e:
                continue
            checked += 1
            ok, detail = check(e["commons_title"])
            if not ok:
                bad += 1
                print(f"FAIL {group}/{key} {e['commons_title']}: {detail}", file=sys.stderr)
    print(f"Checked {checked} images | failing {bad}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
