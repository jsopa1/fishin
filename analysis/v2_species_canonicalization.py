#!/usr/bin/env python3
"""
Canonical species names for the V2 map's species filter.

WDNR's shore-fishing "Available Fish Species" text (see
v2_shore_fishing_details.py) is free-typed per site, not drawn from a
controlled vocabulary -- the real result, verified against every one of
the 61 distinct phrases actually present in this project's database, is
things like "LM BASS", "SM. MOUTH BASS", "LAREMOUTH BASS" (a real typo),
"BASS (LG. MOUTH, ROCK)", and "MUSKY" all meaning what V1's own,
already-clean species_predictions table calls "LARGEMOUTH BASS",
"SMALLMOUTH BASS", and "MUSKELLUNGE" respectively. Left as raw text, the
map's species filter would show dozens of near-duplicate entries for a
handful of real species -- exactly what was reported as undermining
trust in the system.

This module maps each raw phrase to the canonical species name(s) it
represents, for FILTERING only. It never replaces or deletes the raw
text: every site's detail view (map popup, list row) still shows WDNR's
text exactly as published, typos included, per this project's standing
no-fabrication discipline (Decision #019 already established this for
species text specifically). Canonicalization only changes what the
filter dropdown offers and what a filter query matches against.

A raw phrase can canonicalize to MORE than one species (e.g. "LM & SM
BASS" -> both Largemouth and Smallmouth Bass) or to exactly one. Where a
phrase is genuinely ambiguous about which specific species it means
(e.g. "PANFISH", "TROUT", "CATFISH", "SALMON" with no further
qualifier), it is kept as its own generic canonical bucket rather than
guessed into a specific species -- the same judgment call already
documented for "PIKE (NORTHERN, YELLOW)" not being decomposed into a
guessed species for "YELLOW" (see the mapping below).

Every mapping decision here is a spelling/abbreviation normalization of
a name WDNR itself used (e.g. "MUSKY" -> "Muskellunge" is the same
species under its common vs. proper name, not a reinterpretation of
which species was meant) -- never a guess at which of several distinct
possible species an ambiguous term could refer to.
"""

import re

# Canonical display names match V1's own species_predictions vocabulary
# (see analysis/v1_conditions_biology_forecast.py / physiology_thresholds_v1.json)
# wherever V1 already covers that species, so the combined filter
# dropdown (ui/v1_review_data.py: list_combined_species) doesn't show
# "Muskellunge" and "Musky" as two separate options for the same fish.
CANONICAL_MAP = {
    # Bass
    "BASS": ["Bass (unspecified)"],
    "LARGEMOUTH": ["Largemouth Bass"],
    "LARGEMOUTH BASS": ["Largemouth Bass"],
    "LAREMOUTH BASS": ["Largemouth Bass"],  # real WDNR typo
    "LARGEMOIUHT BASS": ["Largemouth Bass"],  # real WDNR typo
    "LG. MOUTH BASS": ["Largemouth Bass"],
    "LM BASS": ["Largemouth Bass"],
    "SMALLMOUTH BASS": ["Smallmouth Bass"],
    "SMALL MOUTH BASS": ["Smallmouth Bass"],
    "SM. MOUTH BASS": ["Smallmouth Bass"],
    "SM BASS": ["Smallmouth Bass"],
    "ROCK BASS": ["Rock Bass"],
    "ROCKBASS": ["Rock Bass"],
    "WHITE BASS": ["White Bass"],
    "LM & SM BASS": ["Largemouth Bass", "Smallmouth Bass"],
    "SM & LG MOUTH BASS": ["Largemouth Bass", "Smallmouth Bass"],
    "LG. & SM. MOUTH BASS": ["Largemouth Bass", "Smallmouth Bass"],
    "SM. & LG. MOUTH BASS": ["Largemouth Bass", "Smallmouth Bass"],
    "LARGEMOUTH BASS & PANFISH": ["Largemouth Bass", "Panfish (unspecified)"],
    "BASS (LG. MOUTH, ROCK)": ["Largemouth Bass", "Rock Bass"],
    "BASS (SMALLMOUTH, ROCK)": ["Smallmouth Bass", "Rock Bass"],
    # Pike / Muskellunge
    "NORTHERN": ["Northern Pike"],
    "NORHTERN": ["Northern Pike"],  # real WDNR typo
    "NORTHERN PIKE": ["Northern Pike"],
    "NORTHEN PIKE": ["Northern Pike"],  # real WDNR typo
    "NOURTHERN PIKE": ["Northern Pike"],  # real WDNR typo
    "N. PIKE": ["Northern Pike"],
    # "YELLOW" here is left undecoded -- historically a regional nickname
    # for walleye in the Great Lakes area, but not certain enough in this
    # context to assert as fact; only the unambiguous "NORTHERN" half is
    # canonicalized.
    "PIKE (NORTHERN, YELLOW)": ["Northern Pike"],
    "MUSKIE": ["Muskellunge"],
    "MUSKY": ["Muskellunge"],
    "MUDKY": ["Muskellunge"],  # real WDNR typo
    # Panfish family
    "PANFISH": ["Panfish (unspecified)"],
    "BLUEGILL": ["Bluegill"],
    "PUMPKINSEED": ["Pumpkinseed"],
    "SUNFISH": ["Sunfish (unspecified)"],
    "CRAPPIE": ["Crappie (unspecified)"],
    "BLACK CRAPPIE": ["Black Crappie"],
    "PERCH": ["Perch (unspecified)"],
    "YELLOW PERCH": ["Yellow Perch"],
    # Walleye / Sauger
    "WALLEYE": ["Walleye"],
    "WALEYE": ["Walleye"],  # real WDNR typo
    # Trout / Salmon
    "TROUT": ["Trout (unspecified)"],
    "BROOK TROUT": ["Brook Trout"],
    "BROWN TROUT": ["Brown Trout"],
    "RAINBOW TROUT": ["Rainbow Trout"],
    "TROUT - BROWN & RAINBOW": ["Brown Trout", "Rainbow Trout"],
    "SALMON": ["Salmon (unspecified)"],
    # Catfish / Bullhead
    "CATFISH": ["Catfish (unspecified)"],
    "CHANNEL CATFISH": ["Channel Catfish"],
    "BULLHEAD": ["Bullhead"],
    # Sturgeon
    "STURGEON": ["Lake Sturgeon"],
    "STURGON": ["Lake Sturgeon"],  # real WDNR typo
    # Suckers
    "SUCKER": ["Sucker (unspecified)"],
    "SUCKERS": ["Sucker (unspecified)"],
    "WHITE SUCKER": ["White Sucker"],
    "WHITE SUCKERS": ["White Sucker"],
    "REDHORSE": ["Redhorse"],
    "REDHORSE - SUCKERS": ["Redhorse", "Sucker (unspecified)"],
    # Other
    "CARP": ["Carp"],
    "WARMWATER SPECIES": ["Warmwater species (unspecified)"],
}


def canonicalize(raw_phrase: str) -> list:
    """Real WDNR text -> canonical species name(s), for filtering only.
    Falls back to a title-cased version of the raw phrase itself when no
    mapping exists (so a future, not-yet-seen WDNR phrase still shows up
    in the filter rather than silently disappearing) -- never dropped,
    never guessed into an unrelated species."""
    if not raw_phrase:
        return []
    key = re.sub(r"\s+", " ", raw_phrase.strip().upper())
    if key in CANONICAL_MAP:
        return list(CANONICAL_MAP[key])
    return [raw_phrase.strip().title()]
