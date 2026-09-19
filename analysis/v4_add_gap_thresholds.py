#!/usr/bin/env python3
"""Adds documented feeding/growth temperature windows for species that had only
a spawning range (V4 gap fill, DECISIONS #053).

Verbatim-or-nothing: every entry below carries the exact text it rests on, and
this script refuses to write anything unless each quote is found (whitespace
collapsed, nothing else altered) inside the stated line range of the local copy
of the source, so a window can never rest on a number that is not in the source.
Idempotent: re-running replaces the entries it owns, identified by `added_by`.

Source: Wismer & Christie 1987, GLFC Special Publication 87-3, extracted text at
data/v1/raw/glfc_sp87_3_wismer_christie_1987_fulltext.txt.

Deliberately NOT added, with the reason (so the gap is honest, not forgotten):
  * Cisco: the preferred-temperature columns of the extracted table are ambiguous
    (a value could be an avoidance limit or a preferendum) and the growth optimum
    is a single point (18.1 C), which is not a window.
  * Fathead Minnow: a forage / bait fish, not an angling target.
  * Lake Sturgeon: absent from this source; needs a different, separately
    verified source.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "v1" / "raw" / "glfc_sp87_3_wismer_christie_1987_fulltext.txt"
THRESHOLDS = ROOT / "data" / "v1" / "physiology_thresholds_v1.json"
SOURCE_REL = "data/v1/raw/glfc_sp87_3_wismer_christie_1987_fulltext.txt"
TAG = "v4-gap-fill"

CITATION = ("Wismer, D.A. and A.E. Christie. 1987. Temperature relationships of Great Lakes fishes: "
            "a data compilation. Great Lakes Fishery Commission Special Publication 87-3.")

ENTRIES = {
    "PUMPKINSEED": {
        "type": "activity_window",
        "range_c": [27.0, 32.0],
        "description": (
            "final-preferendum values for large adults, 27-32 C: 28.5-32 C by day in Lake Monona, Wisconsin "
            "(Coutant 1977a), 27.7 C in summer in Lake Monona (Brown 1974) and 27-29 C at night in the "
            "laboratory (Coutant 1977a). A spring adult value of 24.2 C is in the same table but its "
            "location is not legible in the extracted text, so it is not used"
        ),
        "evidence": "agency-tier, WI-specific",
        "sources": [
            {"lines": [8339, 8397], "quote": "large D 28.5-32 L. Monona, Wis. Coutant 1977a"},
            {"lines": [8339, 8397], "quote": "adult su 27.7 L. Monona, Wis. Brown 1974"},
            {"lines": [8339, 8397], "quote": "large N 27-29 Lab Coutant 1977a"},
        ],
    },
    "CHANNEL CATFISH": {
        "type": "growth_optimum",
        "range_c": [28.0, 30.0],
        "description": (
            "growth optimum 28-30 C; the compilation lists 29 C and 30 C (Jobling 1981) and 28-30 C "
            "(Brown 1974) for the same quantity. Laboratory and aquaculture-context values, not measured in "
            "Wisconsin waters; adults prefer somewhat cooler water (final preferendum 25.2 C in summer, "
            "Coutant 1977a), so a fish just below this range is not necessarily inactive"
        ),
        "evidence": "well-established",
        "sources": [
            {"lines": [7279, 7305], "quote": "29 Jobling 1981"},
            {"lines": [7279, 7305], "quote": "30 Jobling 1981"},
            {"lines": [7279, 7305], "quote": "28-30 Brown 1974"},
        ],
    },
    "BURBOT": {
        "type": "growth_optimum",
        "range_c": [15.6, 18.3],
        "description": (
            "growth optimum 15.6-18.3 C (Scott and Crossman 1973, single source in the compilation). The "
            "preferred-temperature table for this species is empty in the compilation itself, so this is the "
            "only feeding-side number available. A cold-water fish, much cooler than its under-ice spawning range"
        ),
        "evidence": "agency-tier",
        "sources": [
            {"lines": [7542, 7555], "quote": "GROWTH TEMPERATURES"},
            {"lines": [7542, 7555], "quote": "15.6-18.3"},
            {"lines": [7542, 7555], "quote": "Scott and Crossman 1973"},
        ],
    },
}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify(entries: dict, source_lines: list) -> list:
    problems = []
    for species, entry in entries.items():
        for src in entry["sources"]:
            first, last = src["lines"]
            haystack = normalise(" ".join(source_lines[first - 1:last]))
            if normalise(src["quote"]) not in haystack:
                problems.append(f"{species}: quote not found in lines {first}-{last}: {src['quote']!r}")
    return problems


def to_f(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def build() -> int:
    # Split on the newline character only: str.splitlines() also breaks on the
    # form-feed characters in the extracted PDF text, which would shift every line
    # number away from what grep -n and editors show.
    source_lines = SOURCE.read_text(encoding="utf-8", errors="replace").split(chr(10))
    problems = verify(ENTRIES, source_lines)
    if problems:
        print("ABORTING - nothing written:", *problems, sep="\n  ")
        return 1

    # Text insertion, not json.dump: the file is hand-formatted (one threshold per
    # line) and re-serialising it would bury this change in a rewrite of every entry.
    text = THRESHOLDS.read_text(encoding="utf-8")
    for species, entry in ENTRIES.items():
        low, high = entry["range_c"]
        obj = {
            "type": entry["type"],
            "range_c": [low, high],
            "range_f": [to_f(low), to_f(high)],
            "description": entry["description"],
            "evidence": entry["evidence"],
            "added_by": TAG,
            "sources": [
                {"citation": CITATION, "file": SOURCE_REL, "lines": s["lines"], "quote": s["quote"]}
                for s in entry["sources"]
            ],
        }
        line = "        " + json.dumps(obj, ensure_ascii=False) + ","
        block = re.search(r'    "%s": \{\n(?:.*\n)*?      "thresholds": \[\n' % re.escape(species), text)
        if not block:
            print("ABORTING - species block not found:", species)
            return 1
        # drop a previous run's entry for this species, then insert at the top
        start, end = block.end(), text.index("      ]", block.end())
        kept = [ln for ln in text[start:end].split(chr(10)) if ln and '"added_by": "%s"' % TAG not in ln]
        kept_text = chr(10).join(kept) + chr(10) if kept else ""
        # the entry we insert ends with a comma only when something follows it
        insert = line if kept else line.rstrip(",")
        text = text[:start] + insert + chr(10) + kept_text + text[end:]
    json.loads(text)  # must still be valid JSON before anything is written
    THRESHOLDS.write_text(text, encoding="utf-8")
    print("wrote", ", ".join(ENTRIES))
    return 0


if __name__ == "__main__":
    sys.exit(build())
