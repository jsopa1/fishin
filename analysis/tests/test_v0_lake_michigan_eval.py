"""Deterministic unit tests for the V0 Lake Michigan predictor-eval script.

Focus: the daily-to-annual aggregation logic (the step that makes the raw
NDBC/water-level predictor data comparable to the annual outcome data) and the
baseline/LOO-CV helpers, all on small synthetic inputs with hand-computed
expected values. No I/O, no network, no randomness -- safe and fast to run
repeatedly.

Run: python -m unittest analysis/tests/test_v0_lake_michigan_eval.py
     (or: python -m pytest analysis/tests/test_v0_lake_michigan_eval.py)
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v0_lake_michigan_eval import (  # noqa: E402
    aggregate_daily_to_annual,
    year_over_year_trend,
    loo_mean_baseline,
    persistence_baseline,
    mae,
    rmse,
    loo_linear_predictions,
    evaluate_candidate,
)


class TestAggregateDailyToAnnual(unittest.TestCase):
    def test_simple_two_year_mean(self):
        df = pd.DataFrame(
            {
                "date": [
                    "2020-01-01", "2020-01-02", "2020-01-03",
                    "2021-01-01", "2021-01-02",
                ],
                "value": [1.0, 2.0, 3.0, 10.0, 20.0],
            }
        )
        out = aggregate_daily_to_annual(df, "date", ["value"], how="mean")
        self.assertEqual(list(out.index), [2020, 2021])
        self.assertAlmostEqual(out.loc[2020, "value"], 2.0)
        self.assertAlmostEqual(out.loc[2021, "value"], 15.0)
        self.assertEqual(out.loc[2020, "n_days"], 3)
        self.assertEqual(out.loc[2021, "n_days"], 2)

    def test_max_aggregation(self):
        df = pd.DataFrame(
            {
                "date": ["2020-06-01", "2020-06-02", "2020-06-03"],
                "value": [1.0, 5.0, 3.0],
            }
        )
        out = aggregate_daily_to_annual(df, "date", ["value"], how="max")
        self.assertAlmostEqual(out.loc[2020, "value"], 5.0)

    def test_ignores_nan_like_pandas_default(self):
        df = pd.DataFrame(
            {
                "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "value": [1.0, np.nan, 3.0],
            }
        )
        out = aggregate_daily_to_annual(df, "date", ["value"], how="mean")
        # mean of [1.0, 3.0] ignoring NaN == 2.0, not affected by the missing day
        self.assertAlmostEqual(out.loc[2020, "value"], 2.0)

    def test_multi_column(self):
        df = pd.DataFrame(
            {
                "date": ["2020-01-01", "2020-01-02"],
                "a": [1.0, 3.0],
                "b": [10.0, 20.0],
            }
        )
        out = aggregate_daily_to_annual(df, "date", ["a", "b"], how="mean")
        self.assertAlmostEqual(out.loc[2020, "a"], 2.0)
        self.assertAlmostEqual(out.loc[2020, "b"], 15.0)

    def test_unsupported_how_raises(self):
        df = pd.DataFrame({"date": ["2020-01-01"], "value": [1.0]})
        with self.assertRaises(ValueError):
            aggregate_daily_to_annual(df, "date", ["value"], how="median")


class TestYearOverYearTrend(unittest.TestCase):
    def test_first_year_dropped(self):
        s = pd.Series({2020: 10.0, 2021: 12.0, 2022: 9.0})
        trend = year_over_year_trend(s)
        self.assertNotIn(2020, trend.index)
        self.assertAlmostEqual(trend.loc[2021], 2.0)
        self.assertAlmostEqual(trend.loc[2022], -3.0)


class TestBaselines(unittest.TestCase):
    def setUp(self):
        # simple constant-ish series so LOO mean is hand-verifiable
        self.y = pd.Series({2020: 10.0, 2021: 20.0, 2022: 30.0, 2023: 40.0})

    def test_loo_mean_baseline_excludes_self(self):
        preds = loo_mean_baseline(self.y)
        # held-out 2020: mean of [20,30,40] = 30
        self.assertAlmostEqual(preds.loc[2020], 30.0)
        # held-out 2023: mean of [10,20,30] = 20
        self.assertAlmostEqual(preds.loc[2023], 20.0)

    def test_persistence_baseline_shifts_and_drops_first(self):
        preds = persistence_baseline(self.y)
        self.assertNotIn(2020, preds.index)
        self.assertAlmostEqual(preds.loc[2021], 10.0)
        self.assertAlmostEqual(preds.loc[2022], 20.0)
        self.assertAlmostEqual(preds.loc[2023], 30.0)

    def test_mae_rmse_known_values(self):
        y_true = pd.Series({1: 10.0, 2: 20.0})
        y_pred = pd.Series({1: 12.0, 2: 16.0})
        # errors: 2, 4 -> MAE=3
        self.assertAlmostEqual(mae(y_true, y_pred), 3.0)
        # RMSE = sqrt((4+16)/2) = sqrt(10)
        self.assertAlmostEqual(rmse(y_true, y_pred), np.sqrt(10.0))


class TestLooLinear(unittest.TestCase):
    def test_perfect_linear_relationship_recovered(self):
        # y = 2x + 1 exactly -> LOO predictions should reproduce y exactly
        x = pd.Series({2020: 1.0, 2021: 2.0, 2022: 3.0, 2023: 4.0, 2024: 5.0})
        y = pd.Series({2020: 3.0, 2021: 5.0, 2022: 7.0, 2023: 9.0, 2024: 11.0})
        preds = loo_linear_predictions(x, y)
        for yr in y.index:
            self.assertAlmostEqual(preds.loc[yr], y.loc[yr], places=6)

    def test_too_few_points_returns_empty(self):
        x = pd.Series({2020: 1.0, 2021: 2.0, 2022: 3.0})
        y = pd.Series({2020: 1.0, 2021: 2.0, 2022: 3.0})
        preds = loo_linear_predictions(x, y)
        self.assertEqual(len(preds), 0)

    def test_no_lookahead_leakage(self):
        # Construct x,y where a naive "fit on all data including target year"
        # would perfectly overfit a noisy single point, but LOO (excluding
        # that year) must not. Verify LOO prediction for a held-out year does
        # not equal the exact-fit-on-all-data value when that year is an
        # outlier the fit-on-all-data would specifically bend to reach.
        x = pd.Series({2020: 1.0, 2021: 2.0, 2022: 3.0, 2023: 4.0, 2024: 100.0})
        y = pd.Series({2020: 1.0, 2021: 2.0, 2022: 3.0, 2023: 4.0, 2024: -500.0})
        preds = loo_linear_predictions(x, y)
        # fit-on-all-data (with leakage) would pass exactly through 2024's
        # extreme point; LOO fit (trained only on the clean linear 2020-2023
        # points) should predict something close to the linear trend (~5),
        # nowhere near -500, proving 2024's own value was not used to
        # predict 2024.
        self.assertGreater(preds.loc[2024], -50.0)


class TestEvaluateCandidateNoLeakage(unittest.TestCase):
    def test_years_outside_overlap_excluded(self):
        # y (outcome) has 2013-2016; x (candidate) only has 2015-2016 data
        # (mimics NDBC buoy only starting in 2015) -- evaluation must use
        # only the 2-year... actually needs >=4, use 5 overlapping years.
        y = pd.Series({y_: float(y_) for y_ in range(2010, 2020)})
        x = pd.Series({y_: float(y_) * 2 for y_ in range(2015, 2020)})
        res = evaluate_candidate("test_cand", x, y)
        self.assertEqual(res.n_years, 5)
        self.assertEqual(res.years, "2015-2019")


if __name__ == "__main__":
    unittest.main()
