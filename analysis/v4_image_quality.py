"""Keep every photograph on the site sharp on high-density screens.

The spot, species and bait photos were first stored as 640-960 px thumbnails, which look soft
once a spot page or the home hero shows them full width. This module is the one place images
are written, so every photo gets the same two sizes:

  * ``<name>.<ext>``     the full image, up to FULL_WIDTH px wide (spot page, fish page, hero)
  * ``<name>-sm.<ext>``  a card-sized copy, CARD_WIDTH px wide (cards and thumbnails), so a
                         list of twenty cards does not download twenty full photos

It also writes webapp/static/img/framing.json: which species and bait pictures are drawings on
a white ground (framed whole on a card) rather than photographs (which fill the card).

Both come from the Commons original (never upscaled: a file smaller than a target width is
kept at its own width). Licences, authors and titles are untouched; the only manifest change
this makes is a file's extension, when an opaque PNG is stored as JPEG.

Usage:
    python analysis/v4_image_quality.py            # refresh every photo in both manifests + the hero
    python analysis/v4_image_quality.py --dry-run  # list what would be fetched
    python analysis/v4_image_quality.py --framing  # only rewrite framing.json from the files on disk
"""

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "webapp" / "static"
SPOT_MANIFEST = ROOT / "data" / "v1" / "spot_photo_manifest_v1.json"
IMAGE_MANIFEST = ROOT / "data" / "v1" / "image_manifest_v1.json"
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "fishin/0.1 (https://github.com/jsopa1/fishin; image quality refresh)"}

FULL_WIDTH = 2000
CARD_WIDTH = 720
JPEG_QUALITY = 84

# The home-page hero. Public domain (US Forest Service, Eastern Region), and it is also the
# verified photo of Richardson Lake Access, so the hero shows a real Wisconsin fishing spot.
HERO = {
    "commons_title": "File:CNNF Richardson Lake web FC092116 (2) (29654278920).jpg",
    "file": "img/hero/richardson-lake.jpg",
    "width": 3840,
}


def small_name(path: Path) -> Path:
    return path.with_name(path.stem + "-sm" + path.suffix)


def has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        return img.convert("RGBA").getextrema()[3][0] < 255
    return False


def write_sizes(data: bytes, target: Path, full_width: int = FULL_WIDTH) -> Path:
    """Write the full and card-sized copies of one image. Never enlarges. A PNG with no
    transparency is stored as JPEG (a 2000 px photograph is ~2 MB as PNG, ~0.4 MB as JPEG);
    returns the path actually written so callers can record it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(data))
    img.load()
    png = target.suffix.lower() == ".png" and has_alpha(img)
    if not png:
        target = target.with_suffix(".jpg")
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    for width, out in ((full_width, target), (CARD_WIDTH, small_name(target))):
        copy = img
        if img.width > width:
            copy = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        if png:
            copy.save(out, "PNG", optimize=True)
        else:
            copy.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return target


FRAMING = STATIC / "img" / "framing.json"


def is_on_white(path: Path) -> bool:
    """A drawing or cut-out on a white ground: at least 80% of the border pixels near-white."""
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        edge = [rgb.getpixel((x, y)) for x in range(0, w, max(1, w // 24)) for y in (1, h - 2)]
        edge += [rgb.getpixel((x, y)) for y in range(0, h, max(1, h // 16)) for x in (1, w - 2)]
    return sum(1 for p in edge if min(p) >= 235) / len(edge) >= 0.8


def write_framing(images: dict) -> None:
    """Record which species and bait pictures sit on white, so cards can frame them whole
    (read by webapp/app.py's `on_white` filter). Paths are relative to webapp/static."""
    on_white = []
    for kind in ("species", "baits"):
        for entry in images[kind].values():
            path = ROOT / entry["file"] if "file" in entry else None
            if path and path.suffix.lower() in (".jpg", ".jpeg", ".png") and path.exists() and is_on_white(path):
                on_white.append(path.relative_to(STATIC).as_posix())
    FRAMING.write_text(json.dumps({"on_white": sorted(on_white)}, indent=1) + "\n", encoding="utf-8")


def api(params: dict) -> dict:
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def source_url(title: str, width: int) -> str | None:
    """A Commons rendering at `width`, or the original when the original is narrower."""
    d = api({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size",
             "iiurlwidth": width, "format": "json"})
    page = next(iter(d.get("query", {}).get("pages", {}).values()), {})
    ii = (page.get("imageinfo") or [None])[0]
    if not ii:
        return None
    return ii["url"] if ii.get("width", 0) <= width else ii.get("thumburl")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:  # flaky connection or rate limit: back off and retry
            print("  retry", e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("download failed: " + url)


def jobs(spots: dict, images: dict) -> list:
    """(commons title, target path, width, manifest entry or None, key holding the path, path root)."""
    out = [(HERO["commons_title"], STATIC / HERO["file"], HERO["width"], None, None, None)]
    for s in spots.get("spots", []):
        out.append((s["title"], STATIC / s["file"], FULL_WIDTH, s, "file", STATIC))
    for kind in ("species", "baits"):
        for entry in images[kind].values():
            # Entries drawn for this project (entry["original"]) are SVGs, sharp at any size.
            if "file" in entry and entry.get("commons_title") and not entry.get("original"):
                out.append((entry["commons_title"], ROOT / entry["file"], FULL_WIDTH, entry, "file", ROOT))
    return out


def hero_extra(target: Path) -> None:
    """The hero also gets a 1920 px copy, for 1x desktop screens."""
    img = Image.open(target)
    img.resize((1920, round(img.height * 1920 / img.width)), Image.LANCZOS).save(
        target.with_name(target.stem + "-1920.jpg"), "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--framing", action="store_true")
    args = ap.parse_args()
    if args.framing:
        write_framing(json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8")))
        return 0
    spots = json.loads(SPOT_MANIFEST.read_text(encoding="utf-8"))
    images = json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8"))
    failed = moved = 0
    for title, target, width, entry, key, root in jobs(spots, images):
        print(target.relative_to(ROOT), "<-", title)
        if args.dry_run:
            continue
        try:
            url = source_url(title, width)
            if not url:
                raise RuntimeError("file no longer on Commons")
            written = write_sizes(fetch(url), target, width)
            if entry is None:
                hero_extra(written)
            elif written != target:  # stored under a new extension: record it, drop the old files
                entry[key] = written.relative_to(root).as_posix()
                for old in (target, small_name(target)):
                    old.unlink(missing_ok=True)
                moved += 1
        except Exception as e:  # keep the existing copy rather than leave a hole
            failed += 1
            print("  FAILED, kept the existing file:", e, file=sys.stderr)
        time.sleep(0.3)
    if moved:
        SPOT_MANIFEST.write_text(json.dumps(spots, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        IMAGE_MANIFEST.write_text(json.dumps(images, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not args.dry_run:
        write_framing(images)
    print("done,", failed, "failed,", moved, "moved to a new file type")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
