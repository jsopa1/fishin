"""Find real, openly licensed photographs of access points on Wikimedia Commons.

There are no photographs of individual spots in our own data, so a spot page and card
can only show one when a verifiable photo exists. This script looks, and writes what it
finds to data/v1/spot_photo_manifest_v1.json. Nothing is guessed:

  * The file must be geotagged within MAX_DISTANCE_M of the access point.
  * It must be a raster photograph (jpg/png), not a satellite frame, map, scan or aerial.
  * Its title must name the place. Either a distinctive word from the facility name
    (so "Bukolt Park Sign.jpg" matches Bukolt Park Boat Launch) within 300 m, or every
    distinctive word of the waterbody name plus a water word (lake, river, creek...) within
    250 m ("Middle Genesee Lake.jpg" for Middle Genesee Lake). "Dog Fighting.jpg" that merely
    happens to be nearby, or a photo of a different lake that shares a word, does not.
  * Its licence must be public domain, CC0, CC BY or CC BY-SA (never NC/ND or unknown),
    read from the file's own Commons metadata.

Everything the page needs to credit the photo is recorded: title, author, licence, source
page, distance. Re-running the script refreshes the manifest, so it meets the weekly
freshness bar (data-source-weekly-freshness-bar). Images are downloaded once and stored under
webapp/static/img/spots/ in two sizes (full and card), by analysis/v4_image_quality.py.

Usage:
    python analysis/v4_find_spot_photos.py            # full run, writes manifest and images
    python analysis/v4_find_spot_photos.py --limit 200 --dry-run
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_image_quality as image_quality  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "v1" / "v1_full_run_results.db"
MANIFEST = ROOT / "data" / "v1" / "spot_photo_manifest_v1.json"
IMG_DIR = ROOT / "webapp" / "static" / "img" / "spots"

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "fishin/0.1 (https://github.com/jsopa1/fishin; spot photo finder)"}
MAX_DISTANCE_M = 500
FACILITY_MAX_M = 200
WATERBODY_MAX_M = 250
WATER_WORDS = re.compile(r"\b(lake|river|creek|pond|flowage|reservoir|millpond|bay|harbor|harbour|dam|rapids|falls|slough|marsh)\b", re.I)
# Other things that happen to share a park or lake name: a photo of these is not a photo of the spot.
OTHER_PLACES = re.compile(
    r"\b(schools?|apartments?|hall|church|houses?|hotel|motel|hospital|library|libraries|museum|gardens?|cemetery|"
    r"colleges?|universit\w*|courts?|courthouses?|malls?|stores?|grocery|groceries|restaurant|office|factor\w*|"
    r"mills?|stations?|depots?|stadiums?|arenas?|theaters?|theatres?|inns?|lodges?|"
    r"water\s?tower|parking(\s+lot)?|mounds?|wastewater|treatment|sewage|"
    r"power\s?plant|energy\s?center|plants?|shelters?|"
    r"railroad|railway|\btrain\b|bnsf|amtrak|"
    r"plaza|memorial\s+plaza|welcome\s+center)\b",
    re.I,
)
# A photographer on Commons has systematically documented Wisconsin small towns with photos titled
# just "Town, Wisconsin.jpg" or "Town, Wisconsin-2.jpg" -- welcome signs, main streets, buildings.
# The name alone tells us nothing about whether the photo shows water, so this pattern is trusted
# only when the title also carries a water word (the by_water path); a bare facility-name match on
# it is not accepted.
BARE_PLACE_PHOTO = re.compile(r"^(file:)?[\w .'-]+,\s*wisconsin(\s*-\s*\d+)?\.(jpe?g|png)$", re.I)

ALLOWED_LICENCES = re.compile(r"^(public domain|pd\b|cc0|cc[ -]by(?![- ](nc|nd))(?:[- ]sa)?\b)", re.I)
REJECT_TITLE = re.compile(r"(ISS\d|view of earth|\.tiff?$|\.svg$|\.pdf$|\.gif$|satellite|aerial|orthophoto|map\b|plat\b|topo|lidar)", re.I)
GENERIC = {
    "access", "boat", "ramp", "launch", "landing", "public", "county", "park", "lake", "river", "creek", "the", "of", "and",
    "state", "canoe", "carry", "shore", "fishing", "pier", "dock", "wisconsin", "town", "village", "city", "trail", "area",
    "wildlife", "forest", "recreation", "flowage", "pond", "reservoir", "road", "highway", "hwy", "north", "south", "east",
    "west", "big", "little", "upper", "lower", "wdnr", "dnr", "site", "bridge", "with", "for",
}


def tokens(text):
    return {w for w in re.findall(r"[a-z]{4,}", (text or "").lower()) if w not in GENERIC}


def api(params, retries=3):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def strip_html(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def candidates_for(point):
    fac_tokens, water_tokens = tokens(point["facility_name"]), tokens(point["waterbody_name"])
    if not fac_tokens and not water_tokens:
        return []
    d = api({"action": "query", "list": "geosearch", "gscoord": f"{point['latitude']}|{point['longitude']}",
             "gsradius": MAX_DISTANCE_M, "gsnamespace": 6, "gslimit": 20, "format": "json"})
    out = []
    for g in d.get("query", {}).get("geosearch", []):
        title = g["title"]
        if REJECT_TITLE.search(title) or OTHER_PLACES.search(title):
            continue
        if not re.search(r"\.(jpe?g|png)$", title, re.I):
            continue
        words = tokens(title.rsplit(".", 1)[0])
        dist = round(g["dist"])
        # A facility-name word alone is not enough -- "Bukolt Park Sign.jpg" and "Sauk City Welcome
        # Sign- Monument.jpg" both share a facility word with their spot but show a sign, not water.
        # The title must also carry an explicit water word (checked on the untokenized title, since
        # "Wisconsin River" and "Mississippi River" are themselves stripped as generic and could
        # never satisfy the stricter by_water rule below).
        by_facility = bool(words & fac_tokens) and dist <= FACILITY_MAX_M and bool(WATER_WORDS.search(title))
        by_water = bool(water_tokens) and water_tokens <= words and bool(WATER_WORDS.search(title)) and dist <= WATERBODY_MAX_M
        if by_facility and not by_water and BARE_PLACE_PHOTO.match(title):
            continue
        if by_facility or by_water:
            out.append({"title": title, "distance_m": dist})
    return out


def file_info(titles):
    """Licence, author and a full-width rendering for each candidate title."""
    info = {}
    for i in range(0, len(titles), 40):
        batch = titles[i:i + 40]
        d = api({"action": "query", "titles": "|".join(batch), "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
                 "iiurlwidth": image_quality.FULL_WIDTH, "format": "json"})
        for page in d.get("query", {}).get("pages", {}).values():
            ii = (page.get("imageinfo") or [None])[0]
            if not ii:
                continue
            meta = ii.get("extmetadata", {})
            info[page["title"]] = {
                "licence": strip_html(meta.get("LicenseShortName", {}).get("value")),
                "author": strip_html(meta.get("Artist", {}).get("value")) or "unknown author",
                "page_url": ii.get("descriptionurl"),
                "thumb_url": ii.get("thumburl"),
                "mime": ii.get("mime"),
            }
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    points = [dict(r) for r in conn.execute(
        "SELECT facility_name, waterbody_name, county, latitude, longitude FROM access_points ORDER BY id")]
    if args.limit:
        points = points[:args.limit]

    found = {}
    done = 0

    def search(p):
        try:
            return p, candidates_for(p)
        except Exception as e:  # network trouble: skip this point, the next run retries it
            print("skip", p["facility_name"], e, file=sys.stderr)
            return p, []

    with ThreadPoolExecutor(max_workers=3) as pool:
        for p, cands in pool.map(search, points):
            done += 1
            if cands:
                found[(p["facility_name"], p["latitude"], p["longitude"])] = (p, cands)
            if done % 100 == 0:
                print(f"  {done}/{len(points)} searched, {len(found)} with candidates", flush=True)

    titles = sorted({c["title"] for _, cs in found.values() for c in cs})
    info = file_info(titles) if titles else {}

    spots = []
    for (name, lat, lon), (p, cands) in found.items():
        ok = [c for c in cands if info.get(c["title"]) and ALLOWED_LICENCES.match(info[c["title"]]["licence"])
              and info[c["title"]]["thumb_url"] and (info[c["title"]]["mime"] or "").startswith("image/")]
        if not ok:
            continue
        best = min(ok, key=lambda c: c["distance_m"])
        meta = info[best["title"]]
        spots.append({"facility_name": p["facility_name"], "waterbody_name": p["waterbody_name"], "county": p["county"],
                      "latitude": round(lat, 5), "longitude": round(lon, 5), "title": best["title"],
                      "distance_m": best["distance_m"], **{k: meta[k] for k in ("licence", "author", "page_url", "thumb_url")}})

    print(f"{len(spots)} of {len(points)} access points have a verified photo")
    if args.dry_run:
        for s in spots[:25]:
            print(f"  {s['facility_name']} / {s['waterbody_name']}: {s['title']} ({s['distance_m']} m, {s['licence']})")
        return

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    kept = []
    for s in spots:
        fname = hashlib.sha1(s["title"].encode()).hexdigest()[:12] + ".jpg"
        target = IMG_DIR / fname
        if not target.exists():
            req = urllib.request.Request(s["thumb_url"], headers=UA)
            ok = False
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        image_quality.write_sizes(r.read(), target)
                    ok = True
                    break
                except Exception as e:  # flaky connection: retry, then drop this one spot, never crash the run
                    print("download retry", s["facility_name"], e, file=sys.stderr)
                    time.sleep(2 * (attempt + 1))
            if not ok:
                print("skip (download failed)", s["facility_name"], file=sys.stderr)
                continue
            time.sleep(0.2)
        s["file"] = "img/spots/" + fname
        del s["thumb_url"]
        kept.append(s)
    spots = kept
    keep = {n for s in spots for n in (Path(s["file"]).name, image_quality.small_name(Path(s["file"])).name)}
    for old in IMG_DIR.glob("*.jpg"):
        if old.name not in keep:
            old.unlink()
    MANIFEST.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Wikimedia Commons geosearch + imageinfo",
        "max_distance_m": MAX_DISTANCE_M,
        "spots": sorted(spots, key=lambda s: (s["waterbody_name"], s["facility_name"])),
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", MANIFEST)


if __name__ == "__main__":
    main()
