"""Deterministic unit tests for the V0 inland pooled-predictability script.

Focus: the lake-season aggregation logic, lake-characteristics parsing, the
leave-one-lake-out CV helpers (linear model, naive baseline, species-identity
baseline), and the multivariate OLS helper -- all on small synthetic or
hand-checkable inputs. No network calls.

Run: python -m pytest analysis/tests/test_v0_inland_pooled_predictability.py
"""

import os
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v0_inland_pooled_predictability import (  # noqa: E402
    prepare_lake_season,
    lake_season_aggregate_rate,
    weather_season_summary,
    load_lake_characteristics,
    fit_ols_multi,
    predict_ols_multi,
    loo_cv_by_group,
    loo_mean_baseline_by_group,
    loo_species_mean_baseline,
    mae,
)


def _write_csv(rows, columns):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
    pd.DataFrame(rows, columns=columns).to_csv(tmp.name, index=False)
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
    def test_filters_and_recomputes(self):
        rows = [
            ["u", "f", "d", "Test Lake", "Test", "2023-24", "Walleye", 1000, 50.0, 500, 2.0, 100, 10.0, 999.0, 15.0],
            ["u", "f", "d", "Test Lake", "Test", "2023-24", "Pumpkinseed", 0, 0.0, 5, None, 0, None, None, None],
            ["u", "f", "d", "Test Lake", "Test", "2009-10", "Walleye", 900, 40.0, 400, 2.0, 90, 10.0, 0.1, 15.0],
        ]
        path = _write_csv(rows, CREEL_COLUMNS)
        out = prepare_lake_season(path, "2023-24")
        os.unlink(path)
        self.assertEqual(len(out), 1)
        # recomputed rate must ignore the (deliberately wrong) source column
        self.assertAlmostEqual(out.iloc[0]["harvest_rate_fish_per_hour_recomputed"], 100 / 1000)


class TestLakeSeasonAggregateRate(unittest.TestCase):
    def test_effort_weighted_not_simple_mean(self):
        # Species A: huge effort, low rate. Species B: tiny effort, huge rate.
        # A simple mean-of-rates would be dominated by B; the effort-weighted
        # total must be dominated by A instead.
        df = pd.DataFrame({
            "total_harvest": [100, 50],
            "directed_effort_hours": [10000, 10],
        })
        agg = lake_season_aggregate_rate(df)
        self.assertAlmostEqual(agg["aggregate_harvest_rate_fish_per_hour"], 150 / 10010)
        self.assertEqual(agg["n_species"], 2)


class TestWeatherSeasonSummary(unittest.TestCase):
    def test_window_restriction_and_units(self):
        rows = [
            {"STATION": "X", "DATE": "2023-05-01", "PRCP": 100, "TMAX": 200, "TMIN": 100},
            {"STATION": "X", "DATE": "2023-05-02", "PRCP": 50, "TMAX": 220, "TMIN": 110},
            {"STATION": "X", "DATE": "2023-07-01", "PRCP": 999, "TMAX": 999, "TMIN": 999},
        ]
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
        pd.DataFrame(rows).to_csv(tmp.name, index=False)
        tmp.close()
        summary = weather_season_summary(tmp.name, [("2023-05-01", "2023-05-02")])
        os.unlink(tmp.name)
        self.assertEqual(summary["n_days"], 2)
        self.assertAlmostEqual(summary["mean_tmax_c"], 21.0)
        self.assertAlmostEqual(summary["total_prcp_mm"], 15.0)


class TestLoadLakeCharacteristics(unittest.TestCase):
    def test_drops_reference_only_lakes_and_parses_not_found(self):
        rows = [
            {"lake_name": "Test Lake", "county": "C", "surface_area_acres": "100",
             "max_depth_ft": "20", "mean_depth_ft": "not found", "lake_type": "drainage",
             "trophic_status": "mesotrophic", "primary_species": "x", "source_url_or_file": "y", "notes": "z"},
            {"lake_name": "Lake Michigan (WI waters)", "county": "C", "surface_area_acres": "not applicable",
             "max_depth_ft": "923", "mean_depth_ft": "279", "lake_type": "Great Lake",
             "trophic_status": "oligotrophic", "primary_species": "x", "source_url_or_file": "y", "notes": "z"},
        ]
        path = _write_csv(rows, list(rows[0].keys()))
        out = load_lake_characteristics(path)
        os.unlink(path)
        self.assertNotIn("Lake Michigan (WI waters)", out.index)
        self.assertEqual(len(out), 1)
        self.assertTrue(np.isnan(out.loc["Test Lake", "mean_depth_ft"]))
        self.assertEqual(out.loc["Test Lake", "surface_area_acres"], 100.0)
        self.assertEqual(out.loc["Test Lake", "trophic_index"], 2)
        self.assertEqual(out.loc["Test Lake", "lake_type_bucket"], "drainage")


class TestOLSHelpers(unittest.TestCase):
    def test_fit_and_predict_recovers_exact_plane(self):
        X = np.array([[1.0, 2.0], [2.0, 1.0], [3.0, 4.0], [4.0, 3.0], [5.0, 5.0]])
        y = 1.0 + 2.0 * X[:, 0] + 3.0 * X[:, 1]
        coef = fit_ols_multi(X, y)
        preds = predict_ols_multi(coef, X)
        np.testing.assert_allclose(preds, y, atol=1e-8)
        np.testing.assert_allclose(coef, [1.0, 2.0, 3.0], atol=1e-8)

    def test_mae_known_value(self):
        self.assertAlmostEqual(mae([10.0, 20.0], [12.0, 16.0]), 3.0)


class TestLOOByGroup(unittest.TestCase):
    def _synthetic_df(self):
        # 3 groups (lakes), each contributing 2 rows; y is an exact linear
        # function of x with no noise so the CV predictions should be exact
        # once at least 2 OTHER groups are available to fit on.
        rows = []
        for lake, x_vals in [("A", [1.0, 2.0]), ("B", [3.0, 4.0]), ("C", [5.0, 6.0]), ("D", [7.0, 8.0])]:
            for x in x_vals:
                rows.append({"lake_name": lake, "x": x, "y": 2.0 + 3.0 * x})
        return pd.DataFrame(rows)

    def test_loo_cv_by_group_never_uses_held_out_group_to_fit(self):
        df = self._synthetic_df()
        cv = loo_cv_by_group(df, ["x"], "y", "lake_name")
        # every group appears in the results
        self.assertEqual(set(cv["group"]), {"A", "B", "C", "D"})
        # with a noiseless exact linear relationship and 3 other full groups
        # to fit on, predictions should be (near) exact
        np.testing.assert_allclose(cv["y_true"], cv["y_pred"], atol=1e-6)

    def test_loo_mean_baseline_excludes_own_group(self):
        df = self._synthetic_df()
        baseline = loo_mean_baseline_by_group(df, "y", "lake_name")
        # For group A (y = [5, 8]), baseline should be mean of B,C,D's y values
        other_mean = df[df["lake_name"] != "A"]["y"].mean()
        a_rows = baseline[baseline["group"] == "A"]
        self.assertTrue((a_rows["y_pred"] == other_mean).all())

    def test_species_mean_baseline_uses_other_lakes_same_species(self):
        rows = [
            {"lake_name": "A", "species": "Walleye", "y": 1.0},
            {"lake_name": "A", "species": "Perch", "y": 5.0},
            {"lake_name": "B", "species": "Walleye", "y": 3.0},
            {"lake_name": "B", "species": "Bass", "y": 9.0},
        ]
        df = pd.DataFrame(rows)
        baseline = loo_species_mean_baseline(df, "y", "lake_name", "species")
        # held-out lake A's Walleye row should be predicted using lake B's
        # Walleye value (3.0), not lake A's own value
        a_walleye = baseline[(baseline["group"] == "A") & (baseline["y_true"] == 1.0)]
        self.assertAlmostEqual(a_walleye.iloc[0]["y_pred"], 3.0)
        # held-out lake B's Bass row has no other-lake match -> falls back to
        # lake A's overall mean (1.0, 5.0 -> mean 3.0)
        b_bass = baseline[(baseline["group"] == "B") & (baseline["y_true"] == 9.0)]
        self.assertAlmostEqual(b_bass.iloc[0]["y_pred"], 3.0)


if __name__ == "__main__":
    unittest.main()
