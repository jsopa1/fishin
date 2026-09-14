#!/usr/bin/env python3
"""
Bait and technique guidance, resolved from the SAME temperature states the
rest of this app already derives.

The point of keying on state rather than season or species alone is that
the recommendation changes for the reason the fish's behaviour changes. A
walleye in 6C water is not "a walleye that likes jigs" -- it is a fish
whose aerobic scope will not support chasing anything, which is why the
presentation slows down.

Every entry separates two kinds of claim and this module keeps them
separate all the way to the page:

  biological_basis   -- established physiology (ectotherm metabolic and
                        swimming performance scale with temperature; Q10
                        for fish metabolic rate is typically around 2)
  angling_application -- the technique anglers infer from that, which is
                        widely practised convention and NOT a tested
                        research finding

Per Decision #005 the second is never presented as the first. See
data/v1/bait_technique_reference_v1.json for sources.
"""

import json
from pathlib import Path

REFERENCE_PATH = Path(__file__).parent.parent / "data" / "v1" / "bait_technique_reference_v1.json"

# Order matters: spawning behaviour and active heat avoidance both override
# the plain "is it in the feeding window" reading, because both relocate the
# fish and change what it is doing.
STATE_PRIORITY = ("above_avoidance", "in_spawning_trigger", "in_activity_window", "below_activity_window")

_reference_cache = None


def load_reference() -> dict:
    global _reference_cache
    if _reference_cache is None:
        with open(REFERENCE_PATH, encoding="utf-8") as fh:
            _reference_cache = json.load(fh)
    return _reference_cache


def resolve_state(species_thresholds: list, temp_c: float) -> str | None:
    """Which documented thermal state the species is in at this temperature.

    Returns None when the species has no threshold that speaks to this
    temperature at all -- an honest "we don't know", not a default.
    """
    if temp_c is None or not species_thresholds:
        return None

    states = set()
    has_activity_window = False

    for threshold in species_thresholds:
        ttype = threshold.get("type")
        low_high = threshold.get("range_c")

        if ttype == "avoidance_above":
            limit = threshold.get("value_c")
            if limit is None and low_high:
                limit = low_high[0]
            if limit is not None and temp_c >= limit:
                states.add("above_avoidance")

        elif ttype == "spawning_trigger" and low_high:
            if low_high[0] <= temp_c <= low_high[1]:
                states.add("in_spawning_trigger")

        elif ttype in ("activity_window", "growth_optimum", "physiological_optimum"):
            if ttype == "activity_window":
                has_activity_window = True
            if low_high and low_high[0] <= temp_c <= low_high[1]:
                states.add("in_activity_window")

    if not states and has_activity_window:
        # Only claim "too cold to be active" when there is a real activity
        # window to be below, and the temperature is actually below it.
        for threshold in species_thresholds:
            if threshold.get("type") == "activity_window" and threshold.get("range_c"):
                if temp_c < threshold["range_c"][0]:
                    states.add("below_activity_window")
                break

    for state in STATE_PRIORITY:
        if state in states:
            return state
    return None


def get_guidance(species: str, species_thresholds: list, temp_c: float) -> dict | None:
    """Guidance for one species at the current temperature, or None when
    the state can't be determined.

    The general (cross-species) physiology always carries the biological
    reasoning; a species entry, where one exists, supplies the specific
    technique. Species without their own entry still get the general
    guidance rather than nothing, because the physiology is what it is
    regardless of which fish it is.
    """
    state = resolve_state(species_thresholds, temp_c)
    if state is None:
        return None

    reference = load_reference()
    general = reference.get("general", {}).get(state)
    if general is None:
        return None

    specific = reference.get("species", {}).get(species.upper(), {}).get(state, {})

    return {
        "state": state,
        "state_description": reference.get("_states", {}).get(state),
        "biological_basis": general["biological_basis"],
        "basis_evidence_tier": general.get("basis_evidence_tier", "well-established"),
        # A species-specific technique where we have one, the general
        # fallback otherwise -- never an invented specific.
        "angling_application": specific.get("angling_application") or general["angling_application"],
        "application_evidence_tier": specific.get(
            "application_evidence_tier", general.get("application_evidence_tier", "angling-convention")
        ),
        "species_note": specific.get("species_note"),
        "is_species_specific": bool(specific.get("angling_application")),
    }
