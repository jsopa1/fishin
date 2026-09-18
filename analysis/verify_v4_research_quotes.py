#!/usr/bin/env python3
"""
QA pass for the V4 habitat/bait research (docs/v4_habitat_bait_research_candidates.md).

Re-fetches every source URL cited in data/v1/habitat_reference_v1.json,
data/v1/species_bait_map_v1.json and data/v1/bait_catalog_v1.json and confirms
each stored verbatim quote is actually present in the live document text.
A quote is split on ' ... ' into fragments; every fragment must be found.
Whitespace, curly quotes and dashes are normalised; the PDF degree-sign
placeholder is mapped to a degree sign.

Needs network access, and `pdftotext` on PATH for PDF sources. Not part of the
unit-test suite (tests must not depend on the network); run it before
committing new research and record the result in the research doc.

Usage:
    python analysis/verify_v4_research_quotes.py
    python analysis/verify_v4_research_quotes.py --only walleye   # substring match on URL
Exit status is 1 if any quote could not be found or any source could not be read.
"""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "v1"
UA = "fishin-research/1.0 (quote verification)"


def norm(s: str) -> str:
    s = s.replace("�", "°").replace("­", "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
        ctype = resp.headers.get("Content-Type", "")
    if url.lower().endswith(".pdf") or "pdf" in ctype:
        if not shutil.which("pdftotext"):
            raise RuntimeError("pdftotext not found on PATH (needed for PDF sources)")
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "s.pdf"
            pdf.write_bytes(body)
            out = Path(td) / "s.txt"
            subprocess.run(["pdftotext", str(pdf), str(out)], check=False, capture_output=True)
            return out.read_text(encoding="utf-8", errors="replace")
    text = body.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?</\1>", "", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return html.unescape(text)


def collect() -> list:
    """(where, url, quote) for every cited quote."""
    out = []
    hab = json.loads((DATA / "habitat_reference_v1.json").read_text(encoding="utf-8"))
    for sp, entry in hab["species"].items():
        for c in entry.get("claims", []):
            for s in c["sources"]:
                out.append((f"{sp}/{c['id']}", s["url"], s["quote"]))
    mp = json.loads((DATA / "species_bait_map_v1.json").read_text(encoding="utf-8"))
    for sp, entry in mp["species"].items():
        for l in entry.get("links", []):
            for s in l["sources"]:
                out.append((f"{sp}/{l['bait_id']}", s["url"], s["quote"]))
        for t in entry.get("general_technique", []):
            for s in t["sources"]:
                out.append((f"{sp}/{t['id']}", s["url"], s["quote"]))
    cat = json.loads((DATA / "bait_catalog_v1.json").read_text(encoding="utf-8"))
    for bid, b in cat["baits"].items():
        for s in b.get("wi_regulation_sources", []):
            out.append((f"bait/{bid}", s["url"], s["quote"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default=None, help="only verify sources whose URL contains this text")
    args = ap.parse_args()

    items = [i for i in collect() if not args.only or args.only in i[1]]
    by_url = {}
    for where, url, quote in items:
        by_url.setdefault(url, []).append((where, quote))

    bad = unread = checked = 0
    for url, quotes in sorted(by_url.items()):
        try:
            text = norm(fetch_text(url))
        except Exception as e:  # noqa: BLE001
            unread += 1
            print(f"UNREADABLE {url}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for where, quote in quotes:
            checked += 1
            missing = [p for p in (norm(x) for x in quote.split(" ... ")) if p and p not in text]
            if missing:
                bad += 1
                print(f"NOT FOUND  {where}  {url}\n    {missing[0][:110]}", file=sys.stderr)
    print(f"\nChecked {checked} quotes across {len(by_url)} sources | not found {bad} | unreadable sources {unread}", file=sys.stderr)
    return 1 if (bad or unread) else 0


if __name__ == "__main__":
    sys.exit(main())
