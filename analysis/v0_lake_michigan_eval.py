"""
V0 predictor-eval (steps 3-4) for Lake Michigan (WI waters) angler harvest rate.

Scope and why: step 2 (dataset build, see docs/v0_dataset_manifest.md) found real,
matching outcome + predictor data ONLY for Lake Michigan, 2013-2024. Pewaukee,
Delavan, and Geneva have no creel/catch-rate outcome data at all. Winnebago has
fisheries-abundance trawl data (a different metric than angler catch rate) with
no matching daily predictor series pulled. So this script evaluates Lake Michigan
only, per the manifest's explicit instruction not to fabricate or extend to the
inland lakes.

Outcome variable: annual harvest rate (fish harvested per angler-hour), for
"All salmonids combined" (primary) and "Yellow perch (total)" (secondary),
2013-2024 (12 annual observations), from
data/v0/lake_michigan_creel_harvest_rate_annual_by_species.csv.

Predictor candidates tested (all aggregated from DAILY source data up to ANNUAL
means/extremes to match the outcome's actual temporal resolution -- the raw
daily files do NOT share the outcome's granularity, so this aggregation step is
mandatory and is implemented once, generically, in aggregate_daily_to_annual()):
  1. Annual mean water temperature (WTMP)               -- candidate #1
  5. Annual mean wind speed (WSPD)                       -- candidate #5
  14. Annual mean wave height (WVHT)                     -- candidate #14
  15. Annual mean water level                            -- candidate #15
  9. Annual mean barometric pressure (PRES)              -- candidate #9
  10. Year-over-year barometric pressure trend           -- candidate #10
  16. Angler effort (angler-hours)                       -- candidate #16
      (explicitly flagged for endogeneity -- effort is the denominator of the
      harvest-rate outcome itself, so any observed relationship is partly-to-
      wholly mechanical, not a clean independent predictor effect. See the
      writeup in docs/v0_evaluation_results.md.)

Predictor data coverage caveat: NDBC buoy 45007 (water temp, wind, wave height,
pressure) only has open-water-season records 2015-2024 (buoy is pulled every
winter) -- so annual aggregates for those four candidates are SEASONAL means
over the buoy's in-season days, not true Jan-Dec means, and only span
2015-2024 (10 years; 9 for the pressure-trend candidate, which loses its first
year to differencing). Water level (NOAA CO-OPS 9087057) has full daily
coverage 2013-2024 (12 years) and effort is available for all 12 outcome years
too.

Method (deliberately simple/interpretable -- ~9-12 annual data points is far
too small for anything requiring a large sample, e.g. random forest or
gradient boosting; only a naive/persistence baseline, Pearson correlation, and
single-variable linear regression are used):
  - Baseline (step 3): (a) leave-one-year-out (LOO) historical-mean baseline
    (predict the mean of all OTHER years' outcome values) is the primary
    baseline; (b) a persistence baseline (predict last year's value) is
    reported alongside for comparison. Both are pure "no predictor" baselines.
  - Evaluation (step 4): for each candidate x each outcome, report the Pearson
    correlation (r, p-value) over the overlapping years, and a LOO
    cross-validated single-variable linear regression, comparing its LOO
    MAE/RMSE against the LOO baseline MAE/RMSE computed over the exact same
    held-out years (so the comparison is apples-to-apples, never using a
    future year to predict a past year, and never fitting and evaluating on
    the same year).

Run: python analysis/v0_lake_michigan_eval.py
Deterministic: no randomness anywhere (plain least-squares LOO on a fixed,
static CSV input), so re-running gives identical numbers every time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data", "v0")

HARVEST_RATE_CSV = os.path.join(
    DATA_DIR, "lake_michigan_creel_harvest_rate_annual_by_species.csv"
)
NDBC_DAILY_CSV = os.path.join(DATA_DIR, "lake_michigan_ndbc_45007_daily.csv")
WATER_LEVEL_DAILY_CSV = os.path.join(
    DATA_DIR, "lake_michigan_coops_9087057_water_level_daily.csv"
)


# ---------------------------------------------------------------------------
# Core aggregation logic (daily -> annual). Unit-tested in
# analysis/tests/test_v0_lake_michigan_eval.py on a small synthetic input.
# ---------------------------------------------------------------------------

def aggregate_daily_to_annual(
    df: pd.DataFrame, date_col: str, value_cols: list[str], how: str = "mean"
) -> pd.DataFrame:
    """Aggregate a daily time series to one row per calendar year.

    This is the generic aggregation step required because the outcome data
    (harvest rate) is annual, while the raw predictor sources (NDBC buoy,
    NOAA water level) are daily. Missing values (NaN) are ignored per pandas
    default groupby-mean/max behavior, not treated as zero.

    Parameters
    ----------
    df : DataFrame with a date column (parseable to datetime) and one or more
        numeric value columns.
    date_col : name of the date column.
    value_cols : numeric columns to aggregate.
    how : "mean" or "max".

    Returns
    -------
    DataFrame indexed by integer `year`, one column per input value column,
    plus `n_days` = number of daily observations that went into that year
    (so thin years, e.g. a partial buoy season, are visible/auditable).
    """
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    work["year"] = work[date_col].dt.year
    if how == "mean":
        agg = work.groupby("year")[value_cols].mean()
    elif how == "max":
        agg = work.groupby("year")[value_cols].max()
    else:
        raise ValueError(f"Unsupported how={how!r}")
    counts = work.groupby("year")[value_cols[0]].count().rename("n_days")
    return agg.join(counts)


def year_over_year_trend(annual_series: pd.Series) -> pd.Series:
    """Simple year-over-year difference (this year minus last year).

    The first available year has no prior year and is dropped (NaN), which is
    correct: a trend cannot be computed for a year with no preceding
    observation, and we must never use a future year to "fill in" a past
    trend value.
    """
    s = annual_series.sort_index()
    return s.diff().dropna()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_outcomes() -> dict[str, pd.Series]:
    """Return {species_label: Series indexed by year of harvest_rate_fish_per_hour}."""
    df = pd.read_csv(HARVEST_RATE_CSV)
    out = {}
    for species, group in df.groupby("species"):
        s = group.set_index("year")["harvest_rate_fish_per_hour"].sort_index()
        out[species] = s
    return out


def load_effort() -> pd.Series:
    """Angler-hours by year -- embedded in the harvest-rate CSV itself as the
    denominator (total_angler_hours), identical across species rows for a
    given year, so it is read directly rather than re-derived from the
    separate effort-by-location CSV (which stores the same total under
    location == 'Total (all locations incl. Green Bay)')."""
    df = pd.read_csv(HARVEST_RATE_CSV)
    s = df.drop_duplicates("year").set_index("year")["total_angler_hours"].sort_index()
    return s


def load_ndbc_annual() -> pd.DataFrame:
    df = pd.read_csv(NDBC_DAILY_CSV)
    value_cols = ["WTMP_mean", "WSPD_mean", "WVHT_mean", "PRES_mean"]
    annual = aggregate_daily_to_annual(df, "date", value_cols, how="mean")
    return annual


def load_water_level_annual() -> pd.Series:
    df = pd.read_csv(WATER_LEVEL_DAILY_CSV)
    annual = aggregate_daily_to_annual(
        df, "date", ["water_level_ft_IGLD"], how="mean"
    )
    return annual["water_level_ft_IGLD"]


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def loo_mean_baseline(y: pd.Series) -> pd.Series:
    """Leave-one-year-out historical-mean baseline: predict the mean of all
    OTHER years for each held-out year (never includes the held-out year's
    own value, so it is a fair held-out prediction, not a fitted-and-scored-
    on-the-same-data number)."""
    preds = {}
    for yr in y.index:
        other = y.drop(index=yr)
        preds[yr] = other.mean()
    return pd.Series(preds).sort_index()


def persistence_baseline(y: pd.Series) -> pd.Series:
    """Predict last year's actual value. Undefined for the first year (no
    prior year exists), which is dropped -- never filled from a future
    year."""
    s = y.sort_index()
    preds = s.shift(1).dropna()
    return preds


def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    common = y_true.index.intersection(y_pred.index)
    return float(np.mean(np.abs(y_true.loc[common] - y_pred.loc[common])))


def rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
    common = y_true.index.intersection(y_pred.index)
    return float(np.sqrt(np.mean((y_true.loc[common] - y_pred.loc[common]) ** 2)))


# ---------------------------------------------------------------------------
# Single-variable LOO linear regression
# ---------------------------------------------------------------------------

def loo_linear_predictions(x: pd.Series, y: pd.Series) -> pd.Series:
    """Leave-one-year-out CV for y ~ a + b*x, restricted to years present in
    both x and y. For each held-out year, fit ordinary least squares on the
    remaining years only, then predict the held-out year. Requires at least
    4 overlapping years (3 to fit + 1 held out) to produce anything; with
    exactly 3 total points a single-point fit would be a perfect but
    meaningless line, so we require >=4 to attempt LOO at all, and note when
    a candidate has too few overlapping years to evaluate this way."""
    common = x.index.intersection(y.index)
    x = x.loc[common].sort_index()
    y = y.loc[common].sort_index()
    preds = {}
    if len(common) < 4:
        return pd.Series(dtype=float)
    for yr in x.index:
        train_idx = x.index.difference([yr])
        xt = x.loc[train_idx].values
        yt = y.loc[train_idx].values
        # ordinary least squares, y = a + b*x
        b, a = np.polyfit(xt, yt, 1)
        preds[yr] = a + b * x.loc[yr]
    return pd.Series(preds).sort_index()


@dataclass
class CandidateResult:
    candidate: str
    outcome: str
    n_years: int
    years: str
    pearson_r: float
    pearson_p: float
    slope: float
    loo_model_mae: float
    loo_model_rmse: float
    loo_baseline_mae: float
    loo_baseline_rmse: float
    beats_baseline_mae: bool
    beats_baseline_rmse: bool
    note: str = ""


def evaluate_candidate(
    candidate_name: str,
    x: pd.Series,
    y: pd.Series,
    note: str = "",
) -> CandidateResult:
    common = x.index.intersection(y.index)
    x_c = x.loc[common].sort_index()
    y_c = y.loc[common].sort_index()

    if len(common) < 4:
        return CandidateResult(
            candidate=candidate_name,
            outcome="",
            n_years=len(common),
            years=",".join(str(v) for v in sorted(common)),
            pearson_r=float("nan"),
            pearson_p=float("nan"),
            slope=float("nan"),
            loo_model_mae=float("nan"),
            loo_model_rmse=float("nan"),
            loo_baseline_mae=float("nan"),
            loo_baseline_rmse=float("nan"),
            beats_baseline_mae=False,
            beats_baseline_rmse=False,
            note=(note + " | too few overlapping years (<4) for LOO CV").strip(" |"),
        )

    r, p = stats.pearsonr(x_c.values, y_c.values)
    slope = np.polyfit(x_c.values, y_c.values, 1)[0]

    model_preds = loo_linear_predictions(x_c, y_c)
    # baseline computed on the SAME held-out years as the model, so the
    # comparison is apples-to-apples (baseline is not allowed to see more
    # or fewer years than the model it's being compared to).
    baseline_preds = loo_mean_baseline(y_c)

    m_mae = mae(y_c, model_preds)
    m_rmse = rmse(y_c, model_preds)
    b_mae = mae(y_c, baseline_preds)
    b_rmse = rmse(y_c, baseline_preds)

    return CandidateResult(
        candidate=candidate_name,
        outcome="",
        n_years=len(common),
        years=f"{min(common)}-{max(common)}",
        pearson_r=r,
        pearson_p=p,
        slope=slope,
        loo_model_mae=m_mae,
        loo_model_rmse=m_rmse,
        loo_baseline_mae=b_mae,
        loo_baseline_rmse=b_rmse,
        beats_baseline_mae=m_mae < b_mae,
        beats_baseline_rmse=m_rmse < b_rmse,
        note=note,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    outcomes = load_outcomes()
    salmonids = outcomes["All salmonids combined"]
    perch = outcomes["Yellow perch (total)"]

    effort = load_effort()
    ndbc_annual = load_ndbc_annual()
    water_level_annual = load_water_level_annual()
    pressure_trend = year_over_year_trend(ndbc_annual["PRES_mean"])

    candidates = {
        "water_temp_mean_C (#1)": ndbc_annual["WTMP_mean"],
        "wind_speed_mean_ms (#5)": ndbc_annual["WSPD_mean"],
        "wave_height_mean_m (#14)": ndbc_annual["WVHT_mean"],
        "water_level_mean_ft (#15)": water_level_annual,
        "pressure_mean_hPa (#9)": ndbc_annual["PRES_mean"],
        "pressure_yoy_trend_hPa (#10)": pressure_trend,
        "angler_effort_hours (#16, ENDOGENEITY FLAG)": effort,
    }

    print("=" * 100)
    print("BASELINES (leave-one-year-out)")
    print("=" * 100)
    baseline_rows = []
    for outcome_name, y in [("All salmonids combined", salmonids), ("Yellow perch (total)", perch)]:
        loo_mean_preds = loo_mean_baseline(y)
        loo_mean_mae = mae(y, loo_mean_preds)
        loo_mean_rmse = rmse(y, loo_mean_preds)
        pers_preds = persistence_baseline(y)
        pers_mae = mae(y, pers_preds)
        pers_rmse = rmse(y, pers_preds)
        print(f"\nOutcome: {outcome_name}  (n={len(y)} years, {y.index.min()}-{y.index.max()})")
        print(f"  Sample values (fish/angler-hour): mean={y.mean():.4f}, std={y.std():.4f}")
        print(f"  LOO historical-mean baseline : MAE={loo_mean_mae:.4f}  RMSE={loo_mean_rmse:.4f}")
        print(f"  Persistence baseline (n={len(pers_preds)}): MAE={pers_mae:.4f}  RMSE={pers_rmse:.4f}")
        baseline_rows.append(
            dict(outcome=outcome_name, loo_mean_mae=loo_mean_mae, loo_mean_rmse=loo_mean_rmse,
                 persistence_mae=pers_mae, persistence_rmse=pers_rmse)
        )

    print("\n" + "=" * 100)
    print("CANDIDATE EVALUATION (LOO-CV linear regression vs LOO historical-mean baseline)")
    print("=" * 100)

    all_results = []
    for outcome_name, y in [("All salmonids combined", salmonids), ("Yellow perch (total)", perch)]:
        print(f"\n--- Outcome: {outcome_name} ---")
        for cand_name, x in candidates.items():
            note = ""
            if "ENDOGENEITY" in cand_name:
                note = ("effort is the denominator of harvest_rate by construction; "
                         "any relationship is confounded/partly mechanical, not a clean "
                         "independent predictor effect")
            res = evaluate_candidate(cand_name, x, y, note=note)
            res.outcome = outcome_name
            all_results.append(res)
            sig = "p<0.05" if (res.pearson_p == res.pearson_p and res.pearson_p < 0.05) else "n.s."
            print(
                f"  {cand_name:42s} n={res.n_years:2d} yrs={res.years:11s} "
                f"r={res.pearson_r:+.3f} ({sig}, p={res.pearson_p:.3f})  "
                f"slope={res.slope:+.6g}  "
                f"LOO_MAE model={res.loo_model_mae:.4f} vs baseline={res.loo_baseline_mae:.4f} "
                f"[{'BEATS' if res.beats_baseline_mae else 'does not beat'} baseline on MAE]"
            )
            if res.note:
                print(f"      NOTE: {res.note}")

    results_df = pd.DataFrame([r.__dict__ for r in all_results])
    out_csv = os.path.join(os.path.dirname(__file__), "v0_lake_michigan_eval_results.csv")
    results_df.to_csv(out_csv, index=False)
    print(f"\nFull results table written to: {out_csv}")


if __name__ == "__main__":
    main()
