#!/usr/bin/env python3
"""
Current moon phase -- requested directly by a real customer, and echoed
by other anglers, so this is real validated demand rather than a
speculative addition.

Purely astronomical: a deterministic function of the date, computed
locally with no external API and no coordinate dependency (unlike the
wind/pressure lookup, moon phase doesn't meaningfully vary by longitude
at the resolution this app needs). Same reason the dawn/dusk solar
calculation in ui/v1_review_data.py needs no live service either.

Framing matches the wind/pressure module's precedent exactly, and for
the same reason: "solunar theory" (moon phase driving fish feeding
activity) has real anecdotal following among anglers but the evidence is
mixed and inconclusive -- a 190-study review found just over half showed
any lunar-illumination effect at all, and responses were highly
species-specific, not universal. Most of the documented real mechanism
(spring tides amplifying baitfish movement) is a saltwater/tidal effect
that doesn't apply to Wisconsin's inland lakes and streams. So this
reports the real, current, verifiable moon phase and nothing more --
never a "good fishing day" score, never blended into the species-match
verdict.
"""

import datetime
import math

# A well-documented reference new moon: 2000-01-06 18:14 UTC. Any other
# reference new moon works equally well -- the calculation only depends
# on the number of synodic months elapsed since it, wrapped modulo the
# synodic month length.
REFERENCE_NEW_MOON = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)
SYNODIC_MONTH_DAYS = 29.530588853

PHASES = [
    (0.0625, "New Moon", "🌑"),
    (0.1875, "Waxing Crescent", "🌒"),
    (0.3125, "First Quarter", "🌓"),
    (0.4375, "Waxing Gibbous", "🌔"),
    (0.5625, "Full Moon", "🌕"),
    (0.6875, "Waning Gibbous", "🌖"),
    (0.8125, "Last Quarter", "🌗"),
    (0.9375, "Waning Crescent", "🌘"),
]


def _phase_fraction(when: datetime.datetime) -> float:
    """0.0 = new moon, 0.5 = full moon, wrapping back to 1.0 = next new
    moon. Standard synodic-month approximation, accurate to within a few
    hours -- more than enough for a daily display."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    days_elapsed = (when - REFERENCE_NEW_MOON).total_seconds() / 86400.0
    fraction = (days_elapsed % SYNODIC_MONTH_DAYS) / SYNODIC_MONTH_DAYS
    return fraction % 1.0


def _phase_name_and_emoji(fraction: float) -> tuple:
    for upper_bound, name, emoji in PHASES:
        if fraction < upper_bound:
            return name, emoji
    return PHASES[0][1], PHASES[0][2]  # wraps past 0.9375 back to New Moon


def _illumination_pct(fraction: float) -> float:
    """0% at new moon, 100% at full moon, symmetric on the way back down."""
    return round((1 - math.cos(2 * math.pi * fraction)) / 2 * 100, 1)


def _next_phase_date(when: datetime.datetime, target_fraction: float) -> datetime.datetime:
    """Next date (UTC midnight) at which the phase fraction crosses
    target_fraction (0.0 for new moon, 0.5 for full moon)."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    days_elapsed = (when - REFERENCE_NEW_MOON).total_seconds() / 86400.0
    current_cycle = days_elapsed / SYNODIC_MONTH_DAYS
    target_cycle = math.floor(current_cycle) + target_fraction
    if target_cycle <= current_cycle:
        target_cycle += 1.0
    target_days = target_cycle * SYNODIC_MONTH_DAYS
    return REFERENCE_NEW_MOON + datetime.timedelta(days=target_days)


def get_moon_phase(when: datetime.datetime = None) -> dict:
    """Real, current, computed moon phase -- name, emoji, % illuminated,
    and the next full/new moon dates. Informational only: never a
    predictor of fish activity, never blended into the species-match
    verdict. See module docstring for why."""
    when = when or datetime.datetime.now(datetime.timezone.utc)
    fraction = _phase_fraction(when)
    name, emoji = _phase_name_and_emoji(fraction)
    return {
        "phase_name": name,
        "emoji": emoji,
        "illumination_pct": _illumination_pct(fraction),
        "next_full_moon": _next_phase_date(when, 0.5),
        "next_new_moon": _next_phase_date(when, 0.0),
    }
