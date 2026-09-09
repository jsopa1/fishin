"""Deterministic unit tests for the V0 lake-transposition-eval script.

Focus: the species-level lake-season preparation/filtering logic, the
leave-one-species-out baseline and fit/predict helpers, the transposition
evaluator, and the weather-window aggregation -- all on small synthetic or
hand-checkable inputs. No network calls (weather CSVs used here are tiny
synthetic fixtures, not the real downloaded files).

Run: python -m pytest analysis/tests/test_v0_lake_transposition_eval.py
"""

import os
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v0_lake_transposition_eval import (  # noqa: E402
    prepare_lake_season,
    fit_ols,
    loo_linear_predictions,
    loo_mean_baseline,
    mae,
    evaluate_transposition,
    weather_season_summary,
)


def _write_csv(rows, columns):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    )
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(tmp.name, index=False)
    tmp.close()
    return tmp.name


CREEL_COLUMNS = [
    "source_url", "source_file", "retrieval_date", "waterbody", "county",
    "creel_year", "species", "directed_effort_hours", "pct_of_directed_effort",
    "total_catch", "catch_rate_hrs_per_fish", "total_harvest",
    "harvest_rate_hrs_per_fish", "harvest_rate_fish_per_hour",
    "mean_harvest_length_in",
]


class TestPrepareLakeSeason(unittest.TestCase):
    def test_filters_to_requested_season_and_drops_zero_effort(self):
        rows = [
            ["u", "f", "d", "Test Lake", "Test", "2023-24", "Walleye", 1000, 50.0, 500, 2.0, 100, 10.0, 0.1, 15.0],
            ["u", "f", "d", "Test Lake", "Test", "2023-24", "Perch", 500, 25.0, 200, 2.5, 50, 10.0, 0.1, 8.0],
            # zero effort -> must be dropped
            ["u", "f", "d", "Test Lake", "Test", "2023-24", "Pumpkinseed", 0, 0.0, 5, None, 0, None, None, None],
            # other season -> must be excluded
            ["u", "f", "d", "Test Lake", "Test", "2009-10", "Walleye", 900, 40.0, 400, 2.0, 90, 10.0, 0.1, 15.0],
        ]
        path = _write_csv(rows, CREEL_COLUMNS)
        out = prepare_lake_season(path, "2023-24")
        os.unlink(path)
        self.assertEqual(len(out), 2)
        self.assertEqual(set(out["species"]), {"Walleye", "Perch"})

    def test_drops_missing_pct_of_effort(self):
        rows = [
            ["u", "f", "d", "Test Lake", "Test", "2022-23", "Crappie", 1000, None, 500, 2.0, 100, 10.0, 0.1, 15.0],
            ["u", "f", "d", "Test Lake", "Test", "2022-23", "Walleye", 1000, 50.0, 500, 2.0, 100, 10.0, 0.1, 15.0],
        ]
        path = _write_csv(rows, CREEL_COLUMNS)
        out = prepare_lake_season(path, "2022-23")
        os.unlink(path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["species"], "Walleye")

    def test_recomputes_harvest_rate_from_raw_counts_not_source_column(self):
        # Deliberately wrong/mislabeled source rate column (mimics the real
        # Petenwell unit-label bug) -- the recomputed column must ignore it
        # and derive fish/hour directly from total_harvest / effort_hours.
        rows = [
            ["u", "f", "d", "Test Lake", "Test", "2023", "Walleye", 100, 50.0, 50, 2.0, 10, 999.0, 999.0, 15.0],
        ]
        path = _write_csv(rows, CREEL_COLUMNS)
        out = prepare_lake_season(path, "2023")
        os.unlink(path)
        self.assertAlmostEqual(
            out.iloc[0]["harvest_rate_fish_per_hour_recomputed"], 10 / 100
        )

    def test_waterbody_filter(self):
        rows = [
            ["u", "f", "d", "Lake Wisconsin", "C", "2023", "Walleye", 1000, 50.0, 500, 2.0, 100, 10.0, 0.1, 15.0],
            ["u", "f", "d", "Wisconsin River Tailwater", "C", "2023", "Walleye", 1000, 50.0, 500, 2.0, 100, 10.0, 0.1, 15.0],
        ]
        path = _write_csv(rows, CREEL_COLUMNS)
        out = prepare_lake_season(path, "2023", waterbody="Lake Wisconsin")
        os.unlink(path)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["waterbody"], "Lake Wisconsin")


class TestFitPredictBaseline(unittest.TestCase):
    def test_fit_ols_recovers_exact_line(self):
        x = pd.Series([1.0, 2.0, 3.0, 4.0])
        y = pd.Series([3.0, 5.0, 7.0, 9.0])  # y = 1 + 2x
        a, b = fit_ols(x, y)
        self.assertAlmostEqual(a, 1.0, places=6)
        self.assertAlmostEqual(b, 2.0, places=6)

    def test_loo_mean_baseline_excludes_self(self):
        y = pd.Series({0: 10.0, 1: 20.0, 2: 30.0, 3: 40.0})
        preds = loo_mean_baseline(y)
        self.assertAlmostEqual(preds.loc[0], 30.0)  # mean of 20,30,40
        self.assertAlmostEqual(preds.loc[3], 20.0)  # mean of 10,20,30

    def test_loo_linear_too_few_points_returns_empty(self):
        x = pd.Series([1.0, 2.0, 3.0])
        y = pd.Series([1.0, 2.0, 3.0])
        preds = loo_linear_predictions(x, y)
        self.assertEqual(len(preds), 0)

    def test_loo_linear_no_leakage_on_perfect_line(self):
        x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        y = pd.Series([3.0, 5.0, 7.0, 9.0, 11.0])
        preds = loo_linear_predictions(x, y)
        for i in y.index:
            self.assertAlmostEqual(preds.loc[i], y.loc[i], places=6)

    def test_mae_known_value(self):
        y_true = pd.Series({0: 10.0, 1: 20.0})
        y_pred = pd.Series({0: 12.0, 1: 16.0})
        self.assertAlmostEqual(mae(y_true, y_pred), 3.0)


class TestEvaluateTransposition(unittest.TestCase):
    def test_perfect_transfer_beats_baseline(self):
        # Lake A and Lake B share the EXACT same underlying relationship
        # (y = 1 + 0.01*x) with different x values -- transposed model
        # should predict B almost exactly, comfortably beating B's own
        # noisy-baseline MAE.
        rng_x_a = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        lake_a = pd.DataFrame(
            {
                "pct_of_directed_effort": rng_x_a,
                "harvest_rate_fish_per_hour_recomputed": [1 + 0.01 * v for v in rng_x_a],
            }
        )
        rng_x_b = [5.0, 15.0, 25.0, 35.0, 45.0]
        lake_b = pd.DataFrame(
            {
                "pct_of_directed_effort": rng_x_b,
                "harvest_rate_fish_per_hour_recomputed": [1 + 0.01 * v for v in rng_x_b],
            }
        )
        res = evaluate_transposition(lake_a, lake_b, "test pair", "A->B")
        self.assertLess(res.transposed_mae, 1e-6)
        self.assertTrue(res.beats_test_own_baseline)

    def test_unrelated_relationship_does_not_beat_baseline(self):
        # Lake A's relationship is flat/near-random noise around a mean very
        # different from lake B's actual values -- transposed predictions
        # should be clearly worse than B's own baseline.
        lake_a = pd.DataFrame(
            {
                "pct_of_directed_effort": [10.0, 20.0, 30.0, 40.0, 50.0],
                "harvest_rate_fish_per_hour_recomputed": [0.01, 0.05, 0.02, 0.04, 0.03],
            }
        )
        lake_b = pd.DataFrame(
            {
                "pct_of_directed_effort": [10.0, 20.0, 30.0, 40.0, 50.0],
                "harvest_rate_fish_per_hour_recomputed": [5.0, 5.1, 4.9, 5.05, 4.95],
            }
        )
        res = evaluate_transposition(lake_a, lake_b, "test pair", "A->B")
        self.assertFalse(res.beats_test_own_baseline)


class TestWeatherSeasonSummary(unittest.TestCase):
    def test_restricts_to_windows_and_converts_units(self):
        rows = [
            {"STATION": "X", "DATE": "2023-05-01", "PRCP": 100, "TMAX": 200, "TMIN": 100},
            {"STATION": "X", "DATE": "2023-05-02", "PRCP": 50, "TMAX": 220, "TMIN": 110},
            # outside window -- must be excluded
            {"STATION": "X", "DATE": "2023-07-01", "PRCP": 999, "TMAX": 999, "TMIN": 999},
        ]
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
        pd.DataFrame(rows).to_csv(tmp.name, index=False)
        tmp.close()
        summary = weather_season_summary(tmp.name, [("2023-05-01", "2023-05-02")])
        os.unlink(tmp.name)
        self.assertEqual(summary["n_days"], 2)
        self.assertAlmostEqual(summary["mean_tmax_c"], 21.0)  # (20+22)/2
        self.assertAlmostEqual(summary["mean_tmin_c"], 10.5)  # (10+11)/2
        self.assertAlmostEqual(summary["total_prcp_mm"], 15.0)  # (100+50)/10


if __name__ == "__main__":
    unittest.main()
