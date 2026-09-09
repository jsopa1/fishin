"""
V0 cross-lake transposition test (Decision #008, step 3 of the research cycle).

THE QUESTION: does a predictor-outcome relationship learned on one lake with
real creel data actually hold when applied to a *different*, physically
similar lake's real outcome data? This script runs actual held-out tests,
not qualitative similarity claims, wherever real matching data exists -- and
says plainly where it does not, per Decision #005 ("never represent an
arbitrary score as scientifically validated").

Two, clearly separated, lines of evidence are produced here:

1. WEATHER CONTEXT (descriptive only, NOT modeled). Step 2's characterization
   flagged candidate similar-lake pairs; this step tried to pull real NOAA
   NCEI daily weather (station data, not fabricated/estimated) for the exact
   creel-survey windows named in each lake's own PDF ("the open-water creel
   survey ran from May 6 through Oct. 31, 2023..." etc., grepped directly out
   of the source PDFs, see docs/v0_transposition_results.md for the exact
   quotes). This succeeded (data/v0/weather_*.csv, six files, sourced from
   NOAA NCEI GHCND daily-summaries via
   https://www.ncei.noaa.gov/access/services/data/v1). But every inland lake
   in this inventory has only 1-2 creel-survey SEASONS total (not a
   continuous annual series like Lake Michigan) -- so aggregating weather to
   the outcome's own resolution (one row per lake-season) gives at most 1-2
   data points per lake. The original V0 Lake Michigan methodology
   (analysis/v0_lake_michigan_eval.py) requires >=4 overlapping years before
   even attempting a LOO-CV regression, for exactly this reason: fewer points
   cannot be fit-and-held-out at all without being a meaningless degenerate
   fit. So weather is reported here for descriptive context only and is
   explicitly NOT used to fit or transpose any model -- doing so would
   violate Decision #005.

2. WITHIN-SEASON SPECIES-LEVEL TRANSPOSITION (the actual held-out test that
   IS possible with adequate sample size). Every creel survey report gives
   one row per species within a single lake-season: real, already-extracted
   `pct_of_directed_effort` (share of total lake angling effort spent
   targeting that species) and harvest counts -- 8 to 16 species per
   lake-season, an order of magnitude more data points than the weather
   route can offer. This lets us actually fit
   `harvest_rate_fish_per_hour ~ a + b * pct_of_directed_effort` on lake A's
   real species data and test it, unmodified, against lake B's real species
   data for a matching (or nearest available) season -- a genuine held-out
   transposition test, evaluated against lake B's own leave-one-species-out
   historical-mean baseline, the same discipline the Lake Michigan
   evaluation used for years.

   Caveat carried through every result below: `pct_of_directed_effort` and
   `harvest_rate_fish_per_hour` both derive from the same species' own
   `directed_effort_hours` (effort is the shared term: pct = effort / total
   lake effort; harvest_rate = harvest / effort), so any relationship found
   has a partial mechanical component, structurally the same
   endogeneity flag the original Lake Michigan evaluation raised for angler
   effort vs. harvest rate. This is disclosed, not hidden, and is why this
   analysis is not described as revealing a "clean" independent predictor.

Harvest rate units: recomputed directly as
`total_harvest / directed_effort_hours` for every lake (including Petenwell,
whose own report mislabels this column -- see
docs/v0_inland_lake_inventory.md's unit-inconsistency flag), rather than
trusting any pre-existing rate column, so units are guaranteed consistent
across every lake compared here.

Run: python analysis/v0_lake_transposition_eval.py
Deterministic: static CSV inputs, no randomness.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data", "v0")


# ---------------------------------------------------------------------------
# Species-level lake-season preparation
# ---------------------------------------------------------------------------

def prepare_lake_season(
    csv_path: str, creel_year: str, waterbody: str | None = None
) -> pd.DataFrame:
    """Load one lake's creel CSV and return the usable species-level rows for
    a single surveyed season.

    Filters out:
      - rows for other creel_year values in the same file (several of these
        lakes have two survey seasons in one CSV),
      - rows for other waterbody values (Lake Wisconsin's CSV also carries
        the separate Kilbourn tailwater reach in some pulls; harmless no-op
        for single-waterbody files),
      - rows with zero or missing directed_effort_hours (harvest rate is
        undefined/not meaningful with no directed effort -- e.g. Sand Lake's
        Pumpkinseed and Rock Bass rows in 2023-24, which show 0 directed
        hours because no angler specifically targeted them that year),
      - rows with missing pct_of_directed_effort (e.g. Lake Wisconsin's two
        crappie rows, which the source report left blank for this field).

    harvest_rate_fish_per_hour is RECOMPUTED here as
    total_harvest / directed_effort_hours for every row, rather than trusting
    the CSV's own precomputed column, specifically because Petenwell Lake's
    source report has a documented unit-label bug (see module docstring) --
    recomputing directly from the two raw counts sidesteps it and keeps units
    identical across every lake.
    """
    df = pd.read_csv(csv_path)
    df = df[df["creel_year"].astype(str).str.strip() == creel_year].copy()
    if waterbody is not None:
        df = df[df["waterbody"].astype(str).str.strip() == waterbody].copy()

    df = df[df["directed_effort_hours"].notna() & (df["directed_effort_hours"] > 0)]
    df = df[df["pct_of_directed_effort"].notna()]

    df["harvest_rate_fish_per_hour_recomputed"] = (
        df["total_harvest"].fillna(0) / df["directed_effort_hours"]
    )
    return df[
        [
            "waterbody",
            "creel_year",
            "species",
            "directed_effort_hours",
            "pct_of_directed_effort",
            "total_harvest",
            "harvest_rate_fish_per_hour_recomputed",
        ]
    ].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fit / predict / baseline (species-level, mirrors the LOO discipline used
# in analysis/v0_lake_michigan_eval.py, applied here across species within a
# lake-season instead of across years within one lake)
# ---------------------------------------------------------------------------

def fit_ols(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    """Ordinary least squares y = a + b*x over ALL points in x/y (no
    held-out split) -- used only to fit lake A's model in full before
    transposing it, unmodified, to lake B, which is already a fully
    out-of-sample test by construction (lake B's data is never seen by the
    fit)."""
    b, a = np.polyfit(x.values, y.values, 1)
    return a, b


def loo_linear_predictions(x: pd.Series, y: pd.Series) -> pd.Series:
    """Leave-one-species-out CV within a single lake-season: for each held
    out species, fit on the other species only, then predict the held-out
    one. Requires >=4 species (3 to fit + 1 held out); returns empty
    otherwise."""
    if len(x) < 4:
        return pd.Series(dtype=float)
    preds = {}
    for idx in x.index:
        train_idx = x.index.difference([idx])
        a, b = fit_ols(x.loc[train_idx], y.loc[train_idx])
        preds[idx] = a + b * x.loc[idx]
    return pd.Series(preds).sort_index()


def loo_mean_baseline(y: pd.Series) -> pd.Series:
    """Leave-one-species-out historical-mean baseline: predict the mean
    harvest rate of the OTHER species in the same lake-season (never the
    held-out species' own value)."""
    preds = {}
    for idx in y.index:
        preds[idx] = y.drop(index=idx).mean()
    return pd.Series(preds).sort_index()


def mae(y_true: pd.Series, y_pred: pd.Series) -> float:
    common = y_true.index.intersection(y_pred.index)
    return float(np.mean(np.abs(y_true.loc[common] - y_pred.loc[common])))


@dataclass
class TranspositionResult:
    pair: str
    direction: str  # "A predicts B" style label
    n_train: int
    n_test: int
    train_r: float
    train_p: float
    train_loo_mae: float
    train_loo_baseline_mae: float
    transposed_mae: float
    test_own_loo_baseline_mae: float
    beats_test_own_baseline: bool
    note: str = ""


def evaluate_transposition(
    lake_a: pd.DataFrame, lake_b: pd.DataFrame, pair_label: str, direction_label: str
) -> TranspositionResult:
    """Fit harvest_rate ~ a + b*pct_of_directed_effort on ALL of lake A's
    species (in-lake LOO diagnostics reported alongside for context), then
    apply that exact fitted line, unmodified, to lake B's real species data.
    Compare the transposed prediction's MAE on lake B against lake B's own
    leave-one-species-out historical-mean baseline -- this is the actual
    "does A's relationship help predict B" test."""
    xa = lake_a["pct_of_directed_effort"]
    ya = lake_a["harvest_rate_fish_per_hour_recomputed"]
    xb = lake_b["pct_of_directed_effort"]
    yb = lake_b["harvest_rate_fish_per_hour_recomputed"]

    r, p = stats.pearsonr(xa.values, ya.values)
    a, b = fit_ols(xa, ya)

    # in-lake-A diagnostic (fit quality on its own data, LOO within A)
    loo_preds_a = loo_linear_predictions(xa, ya)
    train_loo_mae = mae(ya, loo_preds_a) if len(loo_preds_a) else float("nan")
    train_loo_baseline_mae = (
        mae(ya, loo_mean_baseline(ya)) if len(loo_preds_a) else float("nan")
    )

    # the actual transposition test: A's fitted line applied to B's real x
    transposed_preds = a + b * xb
    transposed_mae = mae(yb, transposed_preds)

    # B's own naive baseline, same discipline as the LM eval: leave-one-out
    # historical mean, never using the held-out species' own value
    b_baseline_preds = loo_mean_baseline(yb)
    b_baseline_mae = mae(yb, b_baseline_preds)

    return TranspositionResult(
        pair=pair_label,
        direction=direction_label,
        n_train=len(xa),
        n_test=len(xb),
        train_r=r,
        train_p=p,
        train_loo_mae=train_loo_mae,
        train_loo_baseline_mae=train_loo_baseline_mae,
        transposed_mae=transposed_mae,
        test_own_loo_baseline_mae=b_baseline_mae,
        beats_test_own_baseline=transposed_mae < b_baseline_mae,
    )


# ---------------------------------------------------------------------------
# Weather context (descriptive only -- see module docstring for why this is
# never fit into a model)
# ---------------------------------------------------------------------------

def weather_season_summary(
    csv_path: str, windows: list[tuple[str, str]]
) -> dict:
    """Real NOAA NCEI GHCND daily-summaries data (already downloaded to
    data/v0/weather_*.csv), restricted to the real survey-window date ranges
    named in each lake's own creel PDF, aggregated to one descriptive summary
    per lake-season. Units converted from GHCND tenths (TMAX/TMIN in tenths
    of deg C, PRCP in tenths of mm) to whole degrees C / mm. NOT used as a
    model input anywhere in this script -- one row per lake-season is too
    few points to fit or hold out (see module docstring)."""
    df = pd.read_csv(csv_path)
    df["DATE"] = pd.to_datetime(df["DATE"])
    mask = pd.Series(False, index=df.index)
    for start, end in windows:
        mask |= (df["DATE"] >= start) & (df["DATE"] <= end)
    sub = df[mask]
    return {
        "n_days": int(sub["TMAX"].notna().sum()),
        "mean_tmax_c": float(sub["TMAX"].dropna().mean()) / 10.0,
        "mean_tmin_c": float(sub["TMIN"].dropna().mean()) / 10.0,
        "total_prcp_mm": float(sub["PRCP"].dropna().sum()) / 10.0,
    }


WEATHER_WINDOWS = {
    "sand_2023_24": (
        os.path.join(DATA_DIR, "weather_sandlake_USC00473511_2023_24.csv"),
        [("2023-05-06", "2023-10-31"), ("2023-12-01", "2024-03-03")],
        "Hayward Ranger Station, USC00473511 (Sawyer Co., nearest long-record "
        "COOP station to Sand Lake)",
    ),
    "pine_2023_24": (
        os.path.join(DATA_DIR, "weather_pinelake_USC00473800_2023_24.csv"),
        [("2023-05-06", "2023-10-31"), ("2023-12-01", "2024-03-03")],
        "Hurley, USC00473800 (Iron Co.; the closer Mercer Ranger Station "
        "USC00475352 had a large real coverage gap May 2023-Feb 2024 for "
        "this window and was dropped in favor of this station)",
    ),
    "minocqua_2024_25": (
        os.path.join(DATA_DIR, "weather_minocqua_USC00472314_2024_25.csv"),
        [("2024-05-04", "2024-10-31"), ("2024-12-01", "2025-03-02")],
        "Eagle River, USC00472314 (Vilas Co.; nearest long-record COOP "
        "station shared by Minocqua and Pelican Lakes, both Oneida Co.)",
    ),
    "pelican_2024_25": (
        os.path.join(DATA_DIR, "weather_pelican_USC00472314_2024_25.csv"),
        [("2024-05-04", "2024-10-31"), ("2024-12-01", "2025-03-02")],
        "Eagle River, USC00472314 (same station as Minocqua above)",
    ),
    "lakewisconsin_2022_23": (
        os.path.join(DATA_DIR, "weather_lakewisconsin_USC00477576_2022_23.csv"),
        [("2022-09-01", "2022-09-30"), ("2022-11-15", "2023-05-30")],
        "Sauk City WWTP, USC00477576 (on Lake Wisconsin itself); window is "
        "an approximate reconstruction from the report's own narrative text "
        "(September 2022 creel, ice fishing 'as early as mid-November 2022', "
        "spring creel March 1-May 30, 2023) -- not a single stated range like "
        "the other lakes, flagged as such",
    ),
    "petenwell_2023": (
        os.path.join(DATA_DIR, "weather_petenwell_USC00472973_2023.csv"),
        [("2023-03-01", "2023-06-30")],
        "Friendship, USC00472973 (Adams Co.); report states survey ran "
        "March 1-June 30, 2023 exactly",
    ),
}


def all_weather_summaries() -> dict[str, dict]:
    out = {}
    for key, (path, windows, source_note) in WEATHER_WINDOWS.items():
        summary = weather_season_summary(path, windows)
        summary["source"] = source_note
        out[key] = summary
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    sand_2324 = prepare_lake_season(
        os.path.join(DATA_DIR, "sandlake_creel_2007_08_2023_24.csv"), "2023-24"
    )
    pine_2324 = prepare_lake_season(
        os.path.join(DATA_DIR, "pinelake_creel_2017_18_2023_24.csv"), "2023-24"
    )
    minocqua_2425 = prepare_lake_season(
        os.path.join(DATA_DIR, "minocqualake_creel_2009_10_2024_25.csv"), "2024-25"
    )
    pelican_2425 = prepare_lake_season(
        os.path.join(DATA_DIR, "pelicanlake_creel_2011_12_2024_25.csv"), "2024-25"
    )
    lakewisconsin = prepare_lake_season(
        os.path.join(DATA_DIR, "lakewisconsin_creel_2022_23.csv"),
        "Jul 2022-Jun 2023",
        waterbody="Lake Wisconsin",
    )
    petenwell = prepare_lake_season(
        os.path.join(DATA_DIR, "petenwelllake_creel_2023.csv"), "Mar-Jun 2023"
    )
    wissota_1920 = prepare_lake_season(
        os.path.join(DATA_DIR, "lakewissota_creel_2006_07_2019_20.csv"), "2019-20"
    )

    pairs = [
        ("Sand Lake <-> Pine Lake (2023-24, exact-year match)", sand_2324, "Sand Lake", pine_2324, "Pine Lake"),
        ("Minocqua <-> Pelican (2024-25, exact-year match)", minocqua_2425, "Minocqua", pelican_2425, "Pelican"),
        ("Lake Wisconsin <-> Petenwell (2022-23 vs Mar-Jun 2023, same year)", lakewisconsin, "Lake Wisconsin", petenwell, "Petenwell"),
        ("Lake Wisconsin <-> Lake Wissota (2022-23 vs 2019-20, YEAR MISMATCH)", lakewisconsin, "Lake Wisconsin", wissota_1920, "Lake Wissota"),
        ("Petenwell <-> Lake Wissota (Mar-Jun 2023 vs 2019-20, YEAR MISMATCH)", petenwell, "Petenwell", wissota_1920, "Lake Wissota"),
    ]

    print("=" * 100)
    print("WEATHER CONTEXT (descriptive only, NOT modeled -- see docstring)")
    print("=" * 100)
    for key, summary in all_weather_summaries().items():
        print(f"\n{key}: n_days={summary['n_days']} "
              f"mean_TMAX={summary['mean_tmax_c']:.1f}C "
              f"mean_TMIN={summary['mean_tmin_c']:.1f}C "
              f"total_PRCP={summary['total_prcp_mm']:.0f}mm")
        print(f"    source: {summary['source']}")

    print("\n" + "=" * 100)
    print("SPECIES-LEVEL WITHIN-SEASON TRANSPOSITION TESTS")
    print("=" * 100)
    all_results: list[TranspositionResult] = []
    for pair_label, df_a, name_a, df_b, name_b in pairs:
        print(f"\n--- {pair_label} ---")
        print(f"    {name_a}: n={len(df_a)} species | {name_b}: n={len(df_b)} species")
        res_ab = evaluate_transposition(df_a, df_b, pair_label, f"{name_a} model -> {name_b} data")
        res_ba = evaluate_transposition(df_b, df_a, pair_label, f"{name_b} model -> {name_a} data")
        for res in (res_ab, res_ba):
            all_results.append(res)
            print(
                f"    [{res.direction}] fit-on-source: r={res.train_r:+.3f} p={res.train_p:.3f} "
                f"(n={res.n_train}) | transposed MAE={res.transposed_mae:.4f} vs "
                f"target's own LOO baseline MAE={res.test_own_loo_baseline_mae:.4f} "
                f"[{'BEATS baseline' if res.beats_test_own_baseline else 'does not beat baseline'}]"
            )

    results_df = pd.DataFrame([r.__dict__ for r in all_results])
    out_csv = os.path.join(os.path.dirname(__file__), "v0_lake_transposition_eval_results.csv")
    results_df.to_csv(out_csv, index=False)
    print(f"\nFull results table written to: {out_csv}")


if __name__ == "__main__":
    main()
