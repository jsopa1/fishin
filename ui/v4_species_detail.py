"""
Data assembly for the Fish Detail page (docs/v4_ux_goal_loop_spec.md, Phase 1).

Pure functions over the committed research files -- no database, no network:

  data/v1/physiology_thresholds_v1.json   documented activity windows
  data/v1/habitat_reference_v1.json       cited habitat claims per species
  data/v1/bait_catalog_v1.json            bait items + Wisconsin regulation notes
  data/v1/species_bait_map_v1.json        species -> bait links, technique notes
  data/v1/image_manifest_v1.json          verified public-domain images

Nothing here invents content: a field with no research renders as "not yet
documented", a bait with no verified picture has no picture, and a bait whose
Wisconsin rules were not reviewed says so instead of implying it is allowed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v1_review_data as data  # noqa: E402

DATA_V1 = Path(__file__).resolve().parent.parent / "data" / "v1"

TIER_RANK = {"well-established": 2, "agency-tier": 1, "single-source-speculative": 0}
TIER_LABELS = {
    "well-established": "Well established",
    "agency-tier": "Agency source",
    "single-source-speculative": "Single source",
}
FIELD_LABELS = {
    "water_type": "Water type",
    "structure": "Structure and cover",
    "depth_and_light": "Depth and light",
    "depth_and_season": "Depth and season",
    "temperature_and_depth": "Temperature and depth",
    "temperature_and_cover": "Temperature and cover",
    "temperature_behavior": "Temperature behavior",
    "temperature_preference": "Temperature preference",
    "temperature_tolerance": "Temperature tolerance",
    "seasonal_movement": "Seasonal movement",
    "seasonal_behavior": "Seasonal behavior",
    "feeding_behavior": "Feeding behavior",
    "forage": "What it eats",
    "behavior": "Behavior",
    "oxygen_tolerance": "Oxygen tolerance",
    "spawning_habitat": "Spawning",
    "spawning_timing_and_temperature": "Spawning timing and temperature",
}
FIELD_ORDER = list(FIELD_LABELS)
THRESHOLD_LABELS = {
    "activity_window": "Active range",
    "growth_optimum": "Growth range",
    "physiological_optimum": "Optimal range",
    "spawning_trigger": "Spawning range",
    "avoidance_above": "Avoidance threshold",
}

_cache: dict = {}


def _load(name: str) -> dict:
    if name not in _cache:
        with open(DATA_V1 / name, encoding="utf-8") as fh:
            _cache[name] = json.load(fh)
    return _cache[name]


def slug(species_name: str) -> str:
    return species_name.lower().replace(" ", "-")


def species_from_slug(value: str) -> str | None:
    wanted = (value or "").lower().strip()
    for name in _load("physiology_thresholds_v1.json")["species"]:
        if slug(name) == wanted:
            return name
    return None


def list_species() -> list:
    return [{"name": n, "title": n.title(), "slug": slug(n)} for n in sorted(_load("physiology_thresholds_v1.json")["species"])]


def _tier(tier: str) -> dict:
    return {"key": tier, "label": TIER_LABELS.get(tier, tier)}


def _source_view(src: dict) -> dict:
    return {"citation": src["citation"], "url": src["url"], "quote": src["quote"]}


def image_for(kind: str, key: str) -> dict | None:
    """Resolve a species/bait to a verified image, following reuse entries.
    None when no verified public-domain image exists -- the page then shows an
    explicit no-image state rather than a substitute."""
    manifest = _load("image_manifest_v1.json")
    entry = manifest[kind].get(key)
    note = None
    hops = 0
    while entry is not None and "file" not in entry and hops < 3:
        note = entry.get("note", note)
        if "reuse_species_image" in entry:
            entry = manifest["species"].get(entry["reuse_species_image"])
        elif "reuse_bait_image" in entry:
            entry = manifest["baits"].get(entry["reuse_bait_image"])
        else:
            entry = None
        hops += 1
    if not entry or "file" not in entry:
        return None
    author = entry.get("artist") or entry.get("credit") or "unknown author"
    return {
        "static_path": entry["file"].split("webapp/static/", 1)[1],
        "credit": f"{author} - {entry['license_short']}, via Wikimedia Commons",
        "page_url": entry["page_url"],
        "note": note,
    }


def describe_threshold(t: dict) -> dict:
    kind = THRESHOLD_LABELS.get(t.get("type"), "Documented range")
    parts = []
    if t.get("range_f"):
        parts.append(f"{t['range_f'][0]:g}-{t['range_f'][1]:g}°F ({t['range_c'][0]:g}-{t['range_c'][1]:g}°C)")
    if t.get("peak_range_f"):
        parts.append(f"peak {t['peak_range_f'][0]:g}-{t['peak_range_f'][1]:g}°F")
    if t.get("threshold_f") is not None:
        parts.append(f"above {t['threshold_f']:g}°F ({t['threshold_c']:g}°C)")
    if t.get("preferred_point_f") is not None:
        parts.append(f"preferred about {t['preferred_point_f']:g}°F ({t['preferred_point_c']:g}°C)")
    return {
        "label": kind,
        "value": "; ".join(parts) if parts else "no numeric range recorded",
        "evidence": data._short_evidence_label(t.get("evidence")),
        "source_note": t.get("description"),
    }


def order_baits(links: list, catalog: dict) -> list:
    """Deterministic card order: stronger evidence tier first, then more
    independent sources, then the fixed editorial rank stored in the data
    file. No runtime choice, so the same species always shows the same order."""
    def key(link):
        return (-TIER_RANK.get(link["tier"], 0), -len({s["url"] for s in link["sources"]}), link["rank"], link["bait_id"])
    return sorted((l for l in links if l["bait_id"] in catalog), key=key)


def _bait_card(link: dict, catalog: dict) -> dict:
    bait = catalog[link["bait_id"]]
    note = bait["wi_regulation_note"]
    reviewed = not note.startswith("NOT_YET_RESEARCHED")
    return {
        "id": link["bait_id"],
        "name": bait["name"],
        "category": bait["category"],
        "description": bait["description"],
        "how_to_use": link["how_to_use"],
        "basis": link["basis"],
        "tier": _tier(link["tier"]),
        "sources": [_source_view(s) for s in link["sources"]],
        "image": image_for("baits", link["bait_id"]),
        "regulation": {
            "reviewed": reviewed,
            "text": note if reviewed else "Wisconsin rules for this bait have not been reviewed here. Check the current Wisconsin fishing regulations before using it.",
            "detail": None if reviewed else note.split(":", 1)[1].strip(),
            "sources": [_source_view(s) for s in bait.get("wi_regulation_sources", [])],
        },
    }


def get_species_detail(species_name: str, temp_c: float | None = None) -> dict | None:
    name = species_name.upper()
    physiology = _load("physiology_thresholds_v1.json")["species"]
    if name not in physiology:
        return None
    habitat_entry = _load("habitat_reference_v1.json")["species"].get(name, {})
    bait_entry = _load("species_bait_map_v1.json")["species"].get(name, {})
    catalog = _load("bait_catalog_v1.json")["baits"]

    grouped: dict = {}
    for claim in habitat_entry.get("claims", []):
        grouped.setdefault(claim["field"], []).append({
            "id": claim["id"],
            "text": claim["text"],
            "stage": claim["season_or_life_stage"],
            "tier": _tier(claim["tier"]),
            "wi_applicable": claim["wi_applicable"],
            "sources": [_source_view(s) for s in claim["sources"]],
        })
    habitat = [
        {"field": f, "label": FIELD_LABELS.get(f, f.replace("_", " ").capitalize()), "claims": grouped[f]}
        for f in sorted(grouped, key=lambda f: (FIELD_ORDER.index(f) if f in FIELD_ORDER else 99, f))
    ]

    angling_target = habitat_entry.get("angling_target", bait_entry.get("angling_target", True))
    cards = [_bait_card(l, catalog) for l in order_baits(bait_entry.get("links", []), catalog)] if angling_target else []
    technique = [
        {"id": t["id"], "text": t["text"], "tier": _tier(t["tier"]), "sources": [_source_view(s) for s in t["sources"]]}
        for t in bait_entry.get("general_technique", [])
    ] if angling_target else []

    return {
        "name": name,
        "title": name.title(),
        "slug": slug(name),
        "image": image_for("species", name),
        "angling_target": angling_target,
        "not_target_reason": None if angling_target else (habitat_entry.get("not_documented_reason") or bait_entry.get("reason")),
        "diel_active": physiology[name].get("diel_active"),
        "thresholds": [describe_threshold(t) for t in physiology[name].get("thresholds", [])],
        "current": data._activity_for_species(name, temp_c) if temp_c is not None else None,
        "habitat": habitat,
        "habitat_not_documented": habitat_entry.get("not_yet_documented", []),
        "baits": cards,
        "no_baits_reason": bait_entry.get("reason_no_links"),
        "technique": technique,
    }
