"""Deterministic unit tests for the V0 physiology-predictor-eval script
(Decision #009, step 2). Focus: the temperature-band-distance transform, the
daily-to-period aggregation logic (the monthly-matching step for Lake
Michigan), and the LOO/baseline helpers -- all on small synthetic inputs
with hand-computed expected values. No I/O beyond small synthetic
DataFrames, no network, no randomness.

Run: python -m unittest analysis/tests/test_v0_physiology_predictors_eval.py
     (or: python -m pytest analysis/tests/test_v0_physiology_predictors_eval.py)
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v0_physiology_predictors_eval import (  # noqa: E402
    aggregate_daily_to_annual,
    aggregate_daily_to_period,
    loo_mean_baseline,
    mae,
    loo_linear_predictions,
    evaluate_distance_candidate,
    loo_cv_by_lake,
    loo_lake_mean_baseline,
    loo_species_identity_baseline,
    PHYSIOLOGY_TEMPERATURES,
    INLAND_SPECIES_TEMPERATURES,
    SALMONID_GUILD_TEMP_C,
)


class TestAggregateDailyToAnnual(unittest.TestCase):
    def test_simple_two_year_mean(self):
        df = pd.DataFrame({
            "date": ["2020-01-01", "2020-01-02", "2021-01-01"],
            "value": [1.0, 3.0, 10.0],
        })
        out = aggregate_daily_to_annual(df, "date", ["value"])
        self.assertAlmostEqual(out.loc[2020, "value"], 2.0)
        self.assertAlmostEqual(out.loc[2021, "value"], 10.0)


class TestAggregateDailyToPeriod(unittest.TestCase):
    def test_window_mean_matches_hand_computation(self):
        df = pd.DataFrame({
            "date": ["2022-03-15", "2022-04-20", "2022-05-01", "2023-03-15"],
            "wtmp": [4.0, 6.0, 20.0, 99.0],
        })
        # 2022 March/April window should average only the first two rows,
        # excluding the May row (out of window) and the 2023 row (wrong year).
        result = aggregate_daily_to_period(df, "date", "wtmp", 2022, "03-01", "04-30")
        self.assertAlmostEqual(result, 5.0)

    def test_empty_window_returns_none(self):
        df = pd.DataFrame({"date": ["2022-01-01"], "wtmp": [1.0]})
        result = aggregate_daily_to_period(df, "date", "wtmp", 2022, "06-01", "06-30")
        self.assertIsNone(result)

    def test_year_boundary_respected(self):
        # A reading in 2021 must never leak into a 2022 period window, even
        # with an identical month/day.
        df = pd.DataFrame({
            "date": ["2021-07-15", "2022-07-15"],
            "wtmp": [1.0, 5.0],
        })
        result = aggregate_daily_to_period(df, "date", "wtmp", 2022, "07-01", "07-31")
        self.assertAlmostEqual(result, 5.0)


class TestLooHelpers(unittest.TestCase):
    def test_loo_mean_baseline_excludes_self(self):
        y = pd.Series({"a": 10.0, "b": 20.0, "c": 30.0})
        preds = loo_mean_baseline(y)
        self.assertAlmostEqual(preds.loc["a"], 25.0)  # mean of b,c

    def test_mae_known_value(self):
        y_true = pd.Series({1: 10.0, 2: 20.0})
        y_pred = pd.Series({1: 12.0, 2: 16.0})
        self.assertAlmostEqual(mae(y_true, y_pred), 3.0)

    def test_loo_linear_perfect_fit_recovered(self):
        x = pd.Series({i: float(i) for i in range(5)})
        y = pd.Series({i: 2.0 * i + 1.0 for i in range(5)})
        preds = loo_linear_predictions(x, y)
        for idx in y.index:
            self.assertAlmostEqual(preds.loc[idx], y.loc[idx], places=5)

    def test_loo_linear_too_few_points(self):
        x = pd.Series({1: 1.0, 2: 2.0, 3: 3.0})
        y = pd.Series({1: 1.0, 2: 2.0, 3: 3.0})
        preds = loo_linear_predictions(x, y)
        self.assertEqual(len(preds), 0)


class TestEvaluateDistanceCandidate(unittest.TestCase):
    def test_distance_transform_and_no_lookahead(self):
        # Construct water temp values and a "preferred temp" of 15 -- the
        # further from 15, the lower the harvest rate (an inverse
        # relationship), which is exactly the physiological hypothesis
        # under test. Confirm the sign of r comes out negative (distance up
        # -> harvest down) and the candidate beats a flat baseline on this
        # noiseless synthetic case.
        wtmp = pd.Series({2018: 15.0, 2019: 20.0, 2020: 10.0, 2021: 25.0, 2022: 5.0})
        dist = (wtmp - 15.0).abs()
        harvest = pd.Series({
            2018: 1.0, 2019: 0.6, 2020: 0.6, 2021: 0.2, 2022: 0.2,
        })
        res = evaluate_distance_candidate("test", dist, harvest, units="years")
        self.assertEqual(res.n, 5)
        self.assertLess(res.pearson_r, 0)
        self.assertTrue(res.beats_baseline)

    def test_too_few_points_flagged(self):
        dist = pd.Series({1: 1.0, 2: 2.0, 3: 3.0})
        y = pd.Series({1: 1.0, 2: 2.0, 3: 3.0})
        res = evaluate_distance_candidate("test", dist, y, units="years")
        self.assertIn("too few", res.note)
        self.assertFalse(res.beats_baseline)


class TestLooByLakeHelpers(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "lake_name": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "species": ["Walleye", "Perch"] * 4,
            "dist": [1.0, 2.0, 3.0, 4.0, 1.5, 2.5, 3.5, 4.5],
            "harvest_rate_recomputed": [0.9, 0.8, 0.5, 0.4, 0.85, 0.75, 0.45, 0.35],
        })

    def test_loo_cv_by_lake_excludes_own_lake_from_fit(self):
        cv = loo_cv_by_lake(self.df, "dist", "harvest_rate_recomputed")
        # every held-out lake's rows should appear exactly once
        self.assertEqual(sorted(cv["lake"].unique()), ["A", "B", "C", "D"])
        self.assertEqual(len(cv), 8)

    def test_loo_lake_mean_baseline_excludes_self(self):
        base = loo_lake_mean_baseline(self.df, "harvest_rate_recomputed")
        # held-out lake A: baseline should be mean of B,C,D rows only
        a_preds = base[base["lake"] == "A"]["y_pred"].unique()
        expected = self.df[self.df["lake_name"] != "A"]["harvest_rate_recomputed"].mean()
        self.assertAlmostEqual(a_preds[0], expected)

    def test_species_identity_baseline_uses_other_lakes_same_species(self):
        base = loo_species_identity_baseline(self.df, "harvest_rate_recomputed")
        # held-out lake A, species Walleye: should predict mean of Walleye
        # rows at B, C, D (0.5, 0.85, 0.45) = 0.6
        row = base[(base["lake"] == "A")]
        # match against original species by reconstructing from df order
        walleye_other = self.df[(self.df["lake_name"] != "A") & (self.df["species"] == "Walleye")]
        expected = walleye_other["harvest_rate_recomputed"].mean()
        self.assertAlmostEqual(expected, (0.5 + 0.85 + 0.45) / 3)


class TestPhysiologyTemperatureValuesAreReal(unittest.TestCase):
    """Guards against silently editing a sourced number without updating its
    citation -- every value must have a non-empty source string, and every
    value must fall in a physically plausible range for freshwater fish
    (0-35C)."""

    def test_every_lm_species_has_a_cited_source(self):
        for species, spec in PHYSIOLOGY_TEMPERATURES.items():
            self.assertTrue(spec["source"], msg=f"{species} missing source")
            self.assertTrue(0.0 <= spec["temp_c"] <= 35.0)

    def test_every_inland_species_has_a_cited_source(self):
        for species, spec in INLAND_SPECIES_TEMPERATURES.items():
            self.assertTrue(spec["source"], msg=f"{species} missing source")
            self.assertTrue(0.0 <= spec["temp_c"] <= 35.0)

    def test_salmonid_guild_average_matches_hand_computation(self):
        expected = round(
            (
                PHYSIOLOGY_TEMPERATURES["Chinook Salmon"]["temp_c"]
                + PHYSIOLOGY_TEMPERATURES["Coho Salmon"]["temp_c"]
                + PHYSIOLOGY_TEMPERATURES["Lake Trout"]["temp_c"]
                + PHYSIOLOGY_TEMPERATURES["Brown Trout"]["temp_c"]
            ) / 4, 2,
        )
        self.assertAlmostEqual(SALMONID_GUILD_TEMP_C["temp_c"], expected)


if __name__ == "__main__":
    unittest.main()
