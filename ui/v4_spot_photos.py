"""Verified photographs of access points (see analysis/v4_find_spot_photos.py).

Returns None when a spot has no photo that passed the finder's checks, and the caller then
falls back to the map. Reads data/v1/spot_photo_manifest_v1.json; a missing manifest simply
means no spot has a photo yet.
"""

import json
import re
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "data" / "v1" / "spot_photo_manifest_v1.json"
_cache = {"mtime": None, "index": {}}
_NO_ATTRIBUTION = re.compile(r"^(public domain|pd|cc0)", re.I)


def _index() -> dict:
    try:
        mtime = MANIFEST.stat().st_mtime
    except OSError:
        return {}
    if _cache["mtime"] != mtime:
        spots = json.loads(MANIFEST.read_text(encoding="utf-8")).get("spots", [])
        _cache["index"] = {(round(s["latitude"], 4), round(s["longitude"], 4), s["facility_name"]): s for s in spots}
        _cache["mtime"] = mtime
    return _cache["index"]


def lookup(facility_name, lat, lon):
    try:
        key = (round(float(lat), 4), round(float(lon), 4), facility_name)
    except (TypeError, ValueError):
        return None
    s = _index().get(key)
    if not s:
        return None
    return {
        "static_path": s["file"],
        "title": s["title"].replace("File:", "").rsplit(".", 1)[0],
        "author": s["author"],
        "licence": s["licence"],
        "page_url": s["page_url"],
        "distance_m": s["distance_m"],
        "credit": f"{s['author']}, {s['licence']}",
        # CC BY / CC BY-SA require naming the author and licence wherever the photo is shown;
        # public-domain and CC0 photos carry no such condition, so pages leave the credit off.
        "attribution_required": not _NO_ATTRIBUTION.match(s["licence"] or ""),
    }
