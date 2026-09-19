#!/usr/bin/env python3
"""Adds sourced bait entries for Lake Whitefish (V4 gap fill, DECISIONS #054).

The map previously held none, because the Michigan DNR page consulted first said
"special techniques" are needed but named no bait. The Minnesota DNR MinnAqua
species profile does name them, so they are added here, each with the verbatim
sentence it rests on. Verbatim-or-nothing: the script fetches the live page and
refuses to write unless every quote is present in it.

Cisco is deliberately NOT given entries: the Minnesota DNR cisco page has no
angling content at all, and nothing else retrieved names a cisco bait.

Text replacement, not json.dump: the file uses CRLF line endings and a
hand-set layout, and a re-dump would rewrite every species.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

MAP = Path(__file__).resolve().parents[1] / "data" / "v1" / "species_bait_map_v1.json"
URL = "https://www.dnr.state.mn.us/minnaqua/speciesprofile/lake_whitefish.html"
CITATION = "Minnesota DNR, MinnAqua Fishing Education. Species Profile - Lake Whitefish, 'Fishing and Handling'."
RETRIEVED = "2026-09-19"
PAGE_NOTE = " (Minnesota inland waters and Lake Superior; no Wisconsin-specific bait guidance was found)"

Q_SPRING = "In spring, try using flies, small spinners, and jigs during insect hatches."
Q_COMBO = "In the winter, a spoon and a jig combination work well."
Q_JIG = "put on a white colored jig or small minnow"
Q_MINNOW = "Crappie minnows suspended under a bobber anywhere in the water column will bring strikes."

LINKS = [
    ("minnows_crappie", 1, Q_MINNOW,
     "Minnesota DNR: crappie minnows suspended under a bobber anywhere in the water column will bring strikes.",
     "Suspend it under a bobber; fish sometimes swim by right under the ice, so any depth in the water column can produce."),
    ("jigs", 2, Q_JIG,
     "Minnesota DNR: below a flasher, put on a white colored jig or small minnow.",
     "In winter, tie a flasher about 1-2 feet below the ice, then 1-2 feet of line below it and a white jig."),
    ("spoons", 3, Q_COMBO,
     "Minnesota DNR: in the winter, a spoon and a jig combination work well.",
     "Fished together with a jig in winter."),
    ("spinners", 4, Q_SPRING,
     "Minnesota DNR: in spring, small spinners work during insect hatches.",
     "Small spinners during spring insect hatches."),
    ("artificial_flies", 5, Q_SPRING,
     "Minnesota DNR: in spring, flies work during insect hatches.",
     "Flies during spring insect hatches."),
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def page_text() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "fishin-research/1.0 (quote verification)"})
    body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
    body = re.sub(r"(?is)<(script|style).*?</\1>", "", body)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    import html
    return norm(html.unescape(body).replace("‌", "")).replace("1 - 2 feet", "1-2 feet")


def build() -> int:
    text = page_text()
    missing = [q for q in {Q_SPRING, Q_COMBO, Q_JIG, Q_MINNOW} if norm(q) not in text]
    if missing:
        print("ABORTING - nothing written; quote(s) not on the live page:", *missing, sep="\n  ")
        return 1

    links = []
    for bait_id, rank, quote, basis, how in LINKS:
        links.append({
            "bait_id": bait_id, "states": ["any"], "rank": rank, "tier": "agency-tier",
            "basis": basis, "how_to_use": how,
            "sources": [{"citation": CITATION + PAGE_NOTE, "url": URL, "quote": quote, "retrieved": RETRIEVED}],
        })
    block = {"angling_target": True, "links": links}
    body = json.dumps(block, indent=2, ensure_ascii=False)
    body = "\n".join(("    " + ln if i else ln) for i, ln in enumerate(body.split("\n")))
    new = ('"LAKE WHITEFISH": ' + body).replace("\n", "\r\n")

    with open(MAP, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    # accept the original empty block or a previous run's block
    pattern = re.compile(r'"LAKE WHITEFISH": \{\r\n(?:(?!\r\n    \},\r\n    "BURBOT").)*\r\n    \}', re.S)
    m = pattern.search(raw)
    if not m:
        print("ABORTING - Lake Whitefish block not found")
        return 1
    out = raw[:m.start()] + new + raw[m.end():]
    json.loads(out)  # must stay valid
    with open(MAP, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    print("wrote", len(links), "Lake Whitefish links")
    return 0


if __name__ == "__main__":
    sys.exit(build())
