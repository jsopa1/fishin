"""Tests for the moon-phase calculation.

The reference epoch (2000-01-06 18:14 UTC) is itself a documented new
moon, so the strongest tests are self-consistent: the epoch must compute
as New Moon with near-zero illumination, and half a synodic month later
must compute as Full Moon with near-100% illumination. Two real-world
almanac dates are cross-checked as an independent sanity check.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v3_moon_phase as moon  # noqa: E402


class TestPhaseFraction(unittest.TestCase):
    def test_reference_epoch_is_new_moon(self):
        fraction = moon._phase_fraction(moon.REFERENCE_NEW_MOON)
        self.assertLess(fraction, 0.01)

    def test_half_synodic_month_later_is_full_moon(self):
        halfway = moon.REFERENCE_NEW_MOON + datetime.timedelta(days=moon.SYNODIC_MONTH_DAYS / 2)
        fraction = moon._phase_fraction(halfway)
        self.assertAlmostEqual(fraction, 0.5, delta=0.01)

    def test_full_synodic_month_later_wraps_back_to_new_moon(self):
        # Floating-point modulo can land at 0.999... rather than exactly
        # 0.0 for a value that's mathematically a full wrap -- both ends
        # of the [0, 1) range are "new moon", so check distance from
        # either edge rather than just the low end.
        full_cycle_later = moon.REFERENCE_NEW_MOON + datetime.timedelta(days=moon.SYNODIC_MONTH_DAYS)
        fraction = moon._phase_fraction(full_cycle_later)
        distance_from_wrap = min(fraction, 1 - fraction)
        self.assertLess(distance_from_wrap, 0.01)

    def test_naive_datetime_is_treated_as_utc_not_rejected(self):
        naive = datetime.datetime(2000, 1, 6, 18, 14)
        fraction = moon._phase_fraction(naive)
        self.assertLess(fraction, 0.01)


class TestPhaseNameAndIllumination(unittest.TestCase):
    def test_new_moon_name_and_near_zero_illumination(self):
        name, emoji = moon._phase_name_and_emoji(0.0)
        self.assertEqual(name, "New Moon")
        self.assertEqual(emoji, "🌑")
        self.assertLess(moon._illumination_pct(0.0), 1.0)

    def test_full_moon_name_and_near_full_illumination(self):
        name, _ = moon._phase_name_and_emoji(0.5)
        self.assertEqual(name, "Full Moon")
        self.assertGreater(moon._illumination_pct(0.5), 99.0)

    def test_first_and_last_quarter_are_roughly_half_illuminated(self):
        self.assertAlmostEqual(moon._illumination_pct(0.25), 50.0, delta=1.0)
        self.assertAlmostEqual(moon._illumination_pct(0.75), 50.0, delta=1.0)

    def test_every_fraction_maps_to_exactly_one_of_the_eight_named_phases(self):
        names = {moon._phase_name_and_emoji(f / 1000)[0] for f in range(1000)}
        self.assertEqual(names, {n for _, n, _ in moon.PHASES})


class TestRealWorldCrossCheck(unittest.TestCase):
    """Independent sanity check against two publicly documented full
    moons, allowing a generous 1-day tolerance for the approximation."""

    def _assert_near_full_moon(self, when):
        fraction = moon._phase_fraction(when)
        # Within ~1 day of a synodic month's midpoint on either side.
        distance_from_full = min(abs(fraction - 0.5), 1 - abs(fraction - 0.5))
        self.assertLess(distance_from_full, 1.0 / moon.SYNODIC_MONTH_DAYS + 0.02)

    def test_january_25_2024_full_moon(self):
        self._assert_near_full_moon(datetime.datetime(2024, 1, 25, 17, 54, tzinfo=datetime.timezone.utc))

    def test_august_19_2024_full_moon(self):
        self._assert_near_full_moon(datetime.datetime(2024, 8, 19, 18, 26, tzinfo=datetime.timezone.utc))


class TestNextPhaseDates(unittest.TestCase):
    def test_next_full_moon_is_always_in_the_future(self):
        now = datetime.datetime(2026, 3, 15, tzinfo=datetime.timezone.utc)
        result = moon._next_phase_date(now, 0.5)
        self.assertGreater(result, now)
        self.assertLess(result, now + datetime.timedelta(days=moon.SYNODIC_MONTH_DAYS))

    def test_next_new_moon_is_always_in_the_future(self):
        now = datetime.datetime(2026, 3, 15, tzinfo=datetime.timezone.utc)
        result = moon._next_phase_date(now, 0.0)
        self.assertGreater(result, now)
        self.assertLess(result, now + datetime.timedelta(days=moon.SYNODIC_MONTH_DAYS))


class TestGetMoonPhase(unittest.TestCase):
    def test_returns_all_expected_fields(self):
        result = moon.get_moon_phase(datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc))
        self.assertIn("phase_name", result)
        self.assertIn("emoji", result)
        self.assertIn("illumination_pct", result)
        self.assertIn("next_full_moon", result)
        self.assertIn("next_new_moon", result)
        self.assertIn(result["phase_name"], {n for _, n, _ in moon.PHASES})

    def test_defaults_to_now_when_no_date_given(self):
        result = moon.get_moon_phase()
        self.assertIsInstance(result["illumination_pct"], float)


if __name__ == "__main__":
    unittest.main()
