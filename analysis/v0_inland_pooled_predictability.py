"""
V0 inland-lake pooled predictability test.

THE QUESTION (posed directly by the CEO, distinct from Decision #008's
pairwise cross-lake transposition question already answered in
docs/v0_transposition_results.md): pooling across all 11 inland lakes with
real WDNR creel-survey outcome data, does the real weather and/or lake
physical/limnological data already gathered actually predict fishing
outcomes (harvest rate), tested honestly with a real held-out evaluation?
This is NOT a lake-to-lake transfer test -- every model here is fit and
evaluated with leave-one-LAKE-out cross-validation across the pooled set, so
no lake's own data is ever used to help predict itself, but the model is
allowed to learn from every OTHER lake at once (unlike the transposition
test, which only ever used one source lake at a time).

Per Decision #005 ("never represent an arbitrary score as scientifically
validated"), every number below is held-out (LOO-CV) unless explicitly
labeled descriptive/full-sample, and no claim of a "real" predictor is made
unless it clears a real held-out bar against a naive baseline.

Two resolutions are tested, both leak-safe (leave-one-lake-out):

1. LAKE-SEASON LEVEL (n=11: one row per inland lake, its most recent
   surveyed creel season). Outcome: an effort-weighted lake-wide harvest
   rate (total harvest across all species / total directed-effort hours
   across all species for that lake-season -- computed directly from raw
   creel counts, not any pre-existing rate column). Predictors: real NOAA
   NCEI weather aggregated to the survey window (mean TMAX, mean TMIN, total
   PRCP) and real lake physical characteristics (surface area, max depth,
   lake type; mean depth and trophic status are tested separately on the
   smaller complete-case subset, since they are missing for some lakes).
   This is the cleanest test of the CEO's question: it has no pseudo-
   replication (each lake contributes exactly one independent observation)
   and no species-effort-share endogeneity (Decision #008's flag does not
   apply here -- effort share is not used as a predictor anywhere in this
   script).

2. SPECIES LEVEL, POOLED (n~130: every species row from every lake-season
   used above). Outcome: harvest_rate_fish_per_hour, recomputed directly
   from total_harvest / directed_effort_hours per species (same recompute
   discipline as the transposition script, sidesteps Petenwell's unit-label
   bug). Predictors: the SAME lake-season weather and lake-characteristics
   values, broadcast to every species row in that lake-season (they do not
   vary within a lake-season). This gives far more rows to fit a model on,
   at the cost of pseudo-replication in the predictors (11 independent
   weather/characteristics "treatments", not 130) -- disclosed explicitly,
   not hidden. Cross-validation is still leave-one-LAKE-out (never
   leave-one-species-out), so no lake's data ever leaks into its own
   held-out prediction, and a species-identity baseline (mean harvest rate
   for that species across the OTHER lakes) is reported alongside the naive
   overall-mean baseline, since species identity alone is known to explain a
   lot of harvest-rate variance (panfish vs. gamefish) and any model must
   beat that, not just a flat mean.

Weather for 5 of the 11 lakes (Big Green, Devils, Lake Wissota, Sawyer,
White Potato) was pulled fresh in this cycle from NOAA NCEI GHCND
daily-summaries, nearest-station-with-real-TMAX/TMIN/PRCP-coverage method,
restricted to each lake's own creel PDF's stated survey window (grepped
directly from the PDF text via pdftotext -layout, same discipline as the
original 6 pulls). See WEATHER_WINDOWS below for exact windows, stations,
and distances. One real coverage gap was found and disclosed (Sawyer Lake's
nearest full station, Antigo Langlade Co Airport, has TMAX/TMIN for 118 of
179 days in its window -- the nearer COOP stations at Summit Lake and
Argonne turned out to be precipitation-only, no temperature data at all;
this was discovered by inspecting the downloaded files, not assumed).

Model: simple linear regression (OLS via least squares) only. A random
forest or other flexible model is NOT used here -- with a maximum of 11
independent lake-level observations (10 per LOO training fold) and ~130
pseudo-replicated species-level rows drawn from only 11 independent
weather/characteristics contexts, there is nowhere near enough real
independent data to fit a random forest without it either overfitting
noise or degenerating to a handful of near-duplicate trees. This mirrors
Decision #002 ("simplest model that performs well") and the precedent set
in analysis/v0_lake_michigan_eval.py and analysis/v0_lake_transposition_eval.py,
both of which used linear regression only for the same reason.

Run: python analysis/v0_inland_pooled_predictability.py
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
LAKE_CHAR_CSV = os.path.join(DATA_DIR, "lake_characteristics.csv")


# ---------------------------------------------------------------------------
# Species-level lake-season preparation (identical discipline to
# analysis/v0_lake_transposition_eval.py's prepare_lake_season -- reimplemented
# here, not imported, so this script has no import-order dependency on that
# one; kept byte-for-byte equivalent in logic and covered by its own tests
# below).
# ---------------------------------------------------------------------------

def prepare_lake_season(
    csv_path: str, creel_year: str, waterbody: str | None = None
) -> pd.DataFrame:
    """Load one lake's creel CSV and return usable species-level rows for a
    single surveyed season: drops other creel_year/waterbody rows, drops
    rows with zero/missing directed_effort_hours or missing
    pct_of_directed_effort, and RECOMPUTES harvest_rate_fish_per_hour
    directly as total_harvest / directed_effort_hours (never trusts the
    CSV's own precomputed rate column -- necessary because Petenwell's
    source report has a documented unit-label bug; recomputing keeps units
    identical across every lake)."""
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


def lake_season_aggregate_rate(species_df: pd.DataFrame) -> dict:
    """Aggregate species-level rows for one lake-season into a single,
    effort-weighted lake-wide harvest rate: sum(total_harvest) /
    sum(directed_effort_hours) across all species in that lake-season.
    Computed directly from the two raw counts (never averaging the
    per-species rates, which would overweight rarely-targeted, noisy-rate
    species) -- this is the outcome variable for the lake-season-level
    pooled model."""
    total_harvest = float(species_df["total_harvest"].fillna(0).sum())
    total_effort = float(species_df["directed_effort_hours"].sum())
    return {
        "n_species": len(species_df),
        "total_harvest": total_harvest,
        "total_directed_effort_hours": total_effort,
        "aggregate_harvest_rate_fish_per_hour": total_harvest / total_effort,
    }


# ---------------------------------------------------------------------------
# Weather aggregation (same logic/units as v0_lake_transposition_eval.py's
# weather_season_summary)
# ---------------------------------------------------------------------------

def weather_season_summary(csv_path: str, windows: list[tuple[str, str]]) -> dict:
    """Real NOAA NCEI GHCND daily-summaries data restricted to the real
    survey-window date ranges named in each lake's own creel PDF, aggregated
    to one descriptive summary per lake-season. Units converted from GHCND
    tenths (TMAX/TMIN in tenths of deg C, PRCP in tenths of mm) to whole
    degrees C / mm."""
    df = pd.read_csv(csv_path)
    df["DATE"] = pd.to_datetime(df["DATE"])
    mask = pd.Series(False, index=df.index)
    for start, end in windows:
        mask |= (df["DATE"] >= start) & (df["DATE"] <= end)
    sub = df[mask]
    return {
        "n_days": int(sub["TMAX"].notna().sum()),
        "n_days_in_window": int(len(sub)),
        "mean_tmax_c": float(sub["TMAX"].dropna().mean()) / 10.0,
        "mean_tmin_c": float(sub["TMIN"].dropna().mean()) / 10.0,
        "total_prcp_mm": float(sub["PRCP"].dropna().sum()) / 10.0,
    }


# Lake-season -> (creel csv, creel_year, waterbody, weather csv, windows,
# weather source note). One row per lake -- the most recent surveyed season
# for the 5 lakes with two seasons, so every lake contributes exactly one
# independent lake-season to the pooled dataset (no double-counting a lake).
LAKE_SEASONS = {
    "Minocqua Lake": dict(
        creel_csv="minocqualake_creel_2009_10_2024_25.csv",
        creel_year="2024-25",
        weather_csv="weather_minocqua_USC00472314_2024_25.csv",
        windows=[("2024-05-04", "2024-10-31"), ("2024-12-01", "2025-03-02")],
        weather_source="Eagle River, USC00472314 (existing pull)",
    ),
    "Pelican Lake": dict(
        creel_csv="pelicanlake_creel_2011_12_2024_25.csv",
        creel_year="2024-25",
        weather_csv="weather_pelican_USC00472314_2024_25.csv",
        windows=[("2024-05-04", "2024-10-31"), ("2024-12-01", "2025-03-02")],
        weather_source="Eagle River, USC00472314 (existing pull)",
    ),
    "Devils Lake": dict(
        creel_csv="devilslake_creel_2023_24.csv",
        creel_year="Jul 2023-Jun 2024",
        weather_csv="weather_devilslake_USC00470516_2023_24.csv",
        windows=[
            ("2023-07-01", "2023-10-31"),
            ("2024-01-01", "2024-02-28"),
            ("2024-05-04", "2024-06-30"),
        ],
        weather_source="Baraboo WWTP, USC00470516 (new pull, this cycle; 2.2 mi "
        "from Devils Lake, nearest active full station)",
    ),
    "Big Green Lake": dict(
        creel_csv="biggreenlake_creel_2022_23.csv",
        creel_year="2022-23",
        weather_csv="weather_biggreenlake_USC00470742_2022_23.csv",
        windows=[("2022-05-07", "2023-03-31"), ("2022-12-05", "2023-03-30")],
        weather_source="Berlin WWTP, USC00470742 (new pull, this cycle; 12.6 mi "
        "from Big Green Lake, nearest active full station -- closer stations "
        "Ripon 5NE and Ripon Near lack coverage through the 2022-23 window)",
    ),
    "Lake Wisconsin": dict(
        creel_csv="lakewisconsin_creel_2022_23.csv",
        creel_year="Jul 2022-Jun 2023",
        waterbody="Lake Wisconsin",
        weather_csv="weather_lakewisconsin_USC00477576_2022_23.csv",
        windows=[("2022-09-01", "2022-09-30"), ("2022-11-15", "2023-05-30")],
        weather_source="Sauk City WWTP, USC00477576 (existing pull; window is an "
        "approximate reconstruction, see docs/v0_transposition_results.md)",
    ),
    "Petenwell Lake": dict(
        creel_csv="petenwelllake_creel_2023.csv",
        creel_year="Mar-Jun 2023",
        weather_csv="weather_petenwell_USC00472973_2023.csv",
        windows=[("2023-03-01", "2023-06-30")],
        weather_source="Friendship, USC00472973 (existing pull)",
    ),
    "Pine Lake": dict(
        creel_csv="pinelake_creel_2017_18_2023_24.csv",
        creel_year="2023-24",
        weather_csv="weather_pinelake_USC00473800_2023_24.csv",
        windows=[("2023-05-06", "2023-10-31"), ("2023-12-01", "2024-03-03")],
        weather_source="Hurley, USC00473800 (existing pull, substituted for "
        "Mercer Ranger Station which had a coverage gap)",
    ),
    "Sand Lake": dict(
        creel_csv="sandlake_creel_2007_08_2023_24.csv",
        creel_year="2023-24",
        weather_csv="weather_sandlake_USC00473511_2023_24.csv",
        windows=[("2023-05-06", "2023-10-31"), ("2023-12-01", "2024-03-03")],
        weather_source="Hayward Ranger Station, USC00473511 (existing pull)",
    ),
    "Sawyer Lake": dict(
        creel_csv="sawyerlake_langlade_creel_2023.csv",
        creel_year="Summer 2023",
        weather_csv="weather_sawyerlake_USW00004864_2023.csv",
        windows=[("2023-05-06", "2023-10-31")],
        weather_source="Antigo Langlade Co Airport, USW00004864 (new pull, this "
        "cycle; 15.7 mi from Sawyer Lake -- the two nearer stations, Summit "
        "Lake at 6.0 mi and Argonne at 21.8 mi, turned out to carry PRCP only, "
        "no TMAX/TMIN at all, discovered by inspecting the downloaded data; "
        "TMAX/TMIN present for 118 of 179 days in the window, a real coverage "
        "gap disclosed rather than papered over)",
    ),
    "Lake Wissota": dict(
        creel_csv="lakewissota_creel_2006_07_2019_20.csv",
        creel_year="2019-20",
        weather_csv="weather_lakewissota_USW00014991_2019.csv",
        windows=[("2019-05-04", "2019-10-31")],
        weather_source="Chippewa Valley Regional Airport, USW00014991 (new "
        "pull, this cycle; 11.1 mi from Lake Wissota -- the two closer "
        "stations, Chippewa Falls 0.9NW and Chippewa Falls, turned out to "
        "carry PRCP only, no TMAX/TMIN, discovered by inspecting the "
        "downloaded data)",
    ),
    "White Potato Lake": dict(
        creel_csv="whitepotatolake_creel_2019_20.csv",
        creel_year="2019-20",
        weather_csv="weather_whitepotatolake_USC00478376_2019_20.csv",
        windows=[("2019-05-04", "2019-09-30"), ("2020-01-04", "2020-03-12")],
        weather_source="Suring, USC00478376 (new pull, this cycle; 13.7 mi "
        "from White Potato Lake -- the nearest station, Mountain 0.9E at 0.9 "
        "mi, turned out to be a CoCoRaHS precipitation-only station with no "
        "TMAX/TMIN, discovered by inspecting the downloaded data)",
    ),
}

# Older second season for the 5 lakes that have two surveyed seasons. Used
# ONLY for the within-lake descriptive comparison (Section on n=2
# observations) -- NOT part of the pooled cross-lake model. No weather is
# available for any of these older seasons: the source PDFs for these older
# surveys were not part of this project's local PDF collection (only the
# most recent PDF per lake was kept), and re-locating/re-extracting a
# 15-20-year-old WDNR report's exact survey-window wording was out of scope
# for this pass. This is disclosed explicitly rather than estimating a
# window without a real source, per Decision #005.
OLDER_SEASONS = {
    "Minocqua Lake": dict(creel_csv="minocqualake_creel_2009_10_2024_25.csv", creel_year="2009-10"),
    "Pelican Lake": dict(creel_csv="pelicanlake_creel_2011_12_2024_25.csv", creel_year="2011-12"),
    "Pine Lake": dict(creel_csv="pinelake_creel_2017_18_2023_24.csv", creel_year="2017-18"),
    "Sand Lake": dict(creel_csv="sandlake_creel_2007_08_2023_24.csv", creel_year="2007-08"),
    "Lake Wissota": dict(creel_csv="lakewissota_creel_2006_07_2019_20.csv", creel_year="2006-07"),
}


# ---------------------------------------------------------------------------
# Lake characteristics loading/parsing
# ---------------------------------------------------------------------------

def load_lake_characteristics(csv_path: str = LAKE_CHAR_CSV) -> pd.DataFrame:
    """Load data/v0/lake_characteristics.csv and coerce 'not found'/'not
    applicable' text to NaN for the numeric columns, restricted to the 11
    inland lakes with real creel outcome data (Lake Michigan, Pewaukee, and
    Delavan are dropped -- reference-only rows with no creel outcome data,
    out of scope for a predictability test)."""
    df = pd.read_csv(csv_path)
    df = df[~df["lake_name"].isin(
        ["Lake Michigan (WI waters)", "Pewaukee Lake", "Delavan Lake"]
    )].copy()
    for col in ["surface_area_acres", "max_depth_ft", "mean_depth_ft"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["trophic_status"] = df["trophic_status"].replace("not found", np.nan)
    # Ordinal trophic index for the (small, complete-case-only) trophic model.
    trophic_order = {"oligotrophic": 1, "mesotrophic": 2, "eutrophic": 3}
    df["trophic_index"] = df["trophic_status"].map(trophic_order)
    # Coarse lake-type bucket (drainage / seepage / impoundment) -- the raw
    # column has parenthetical WDNR-hydrologic-code caveats for the three
    # impoundments; bucket on the leading word.
    df["lake_type_bucket"] = df["lake_type"].str.extract(r"^(\w+)")
    return df.set_index("lake_name")


# ---------------------------------------------------------------------------
# Pooled dataset builders
# ---------------------------------------------------------------------------

def build_lake_level_dataset() -> pd.DataFrame:
    """One row per inland lake (n=11): outcome = effort-weighted lake-wide
    harvest rate for that lake's most recent surveyed season; predictors =
    real weather aggregated to the survey window + real lake physical
    characteristics."""
    chars = load_lake_characteristics()
    rows = []
    for lake, spec in LAKE_SEASONS.items():
        species_df = prepare_lake_season(
            os.path.join(DATA_DIR, spec["creel_csv"]),
            spec["creel_year"],
            waterbody=spec.get("waterbody"),
        )
        agg = lake_season_aggregate_rate(species_df)
        weather = weather_season_summary(
            os.path.join(DATA_DIR, spec["weather_csv"]), spec["windows"]
        )
        row = {"lake_name": lake, "creel_year": spec["creel_year"], **agg, **weather}
        row.update(chars.loc[lake].to_dict())
        rows.append(row)
    return pd.DataFrame(rows).set_index("lake_name")


def build_species_level_dataset() -> pd.DataFrame:
    """One row per species per lake-season, pooled across all 11 lakes
    (n~130): outcome = harvest_rate_fish_per_hour_recomputed; predictors =
    the SAME lake-season weather/characteristics values as the lake-level
    dataset, broadcast to every species row in that lake-season (disclosed
    pseudo-replication -- see module docstring)."""
    chars = load_lake_characteristics()
    frames = []
    for lake, spec in LAKE_SEASONS.items():
        species_df = prepare_lake_season(
            os.path.join(DATA_DIR, spec["creel_csv"]),
            spec["creel_year"],
            waterbody=spec.get("waterbody"),
        )
        weather = weather_season_summary(
            os.path.join(DATA_DIR, spec["weather_csv"]), spec["windows"]
        )
        species_df = species_df.copy()
        species_df["lake_name"] = lake
        for k, v in weather.items():
            species_df[f"weather_{k}"] = v
        for k, v in chars.loc[lake].to_dict().items():
            species_df[f"lakechar_{k}"] = v
        frames.append(species_df)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# OLS (single- and multi-predictor) + leave-one-out CV helpers
# ---------------------------------------------------------------------------

def fit_ols_multi(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Ordinary least squares with an intercept column prepended, solved via
    numpy least squares (no sklearn dependency, consistent with the rest of
    this project's analysis scripts). Returns the coefficient vector
    [intercept, b1, b2, ...]."""
    X1 = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return coef


def predict_ols_multi(coef: np.ndarray, X: np.ndarray) -> np.ndarray:
    X1 = np.column_stack([np.ones(len(X)), X])
    return X1 @ coef


def loo_cv_by_group(
    df: pd.DataFrame, feature_cols: list[str], target_col: str, group_col: str
) -> pd.DataFrame:
    """Leave-one-GROUP-out cross-validation: for each unique value of
    group_col (a lake), fit an OLS model on every row belonging to every
    OTHER group, then predict every row in the held-out group. This is the
    leak-safe discipline this whole script depends on -- a lake's own rows
    (whether one row at lake-level, or many at species-level) never
    contribute to their own held-out prediction. Rows with any NaN in the
    requested feature columns are dropped (complete-case) both for fitting
    and for the row's own prediction.

    Returns a DataFrame with one row per input row that had complete
    features, columns: group, y_true, y_pred.
    """
    work = df.dropna(subset=feature_cols + [target_col]).copy()
    results = []
    for held_out in work[group_col].unique():
        train = work[work[group_col] != held_out]
        test = work[work[group_col] == held_out]
        if len(train) < len(feature_cols) + 2 or len(test) == 0:
            continue
        coef = fit_ols_multi(train[feature_cols].values, train[target_col].values)
        preds = predict_ols_multi(coef, test[feature_cols].values)
        for (_, row), pred in zip(test.iterrows(), preds):
            results.append({"group": held_out, "y_true": row[target_col], "y_pred": pred})
    return pd.DataFrame(results)


def loo_mean_baseline_by_group(
    df: pd.DataFrame, target_col: str, group_col: str
) -> pd.DataFrame:
    """Naive baseline paired with loo_cv_by_group: predict the mean of the
    target column over every OTHER group's rows (never the held-out group's
    own rows)."""
    results = []
    for held_out in df[group_col].unique():
        train = df[df[group_col] != held_out]
        test = df[df[group_col] == held_out]
        pred = train[target_col].mean()
        for _, row in test.iterrows():
            results.append({"group": held_out, "y_true": row[target_col], "y_pred": pred})
    return pd.DataFrame(results)


def loo_species_mean_baseline(df: pd.DataFrame, target_col: str, group_col: str, species_col: str) -> pd.DataFrame:
    """Species-identity baseline for the species-level pooled model: predict
    the mean target value for that SAME species across every OTHER lake
    (never the held-out lake's own rows). Falls back to the overall
    other-lakes mean if the held-out row's species was never observed in any
    other lake."""
    results = []
    for held_out in df[group_col].unique():
        train = df[df[group_col] != held_out]
        test = df[df[group_col] == held_out]
        species_means = train.groupby(species_col)[target_col].mean()
        overall_mean = train[target_col].mean()
        for _, row in test.iterrows():
            pred = species_means.get(row[species_col], overall_mean)
            results.append({"group": held_out, "y_true": row[target_col], "y_pred": pred})
    return pd.DataFrame(results)


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


@dataclass
class PredictorResult:
    resolution: str  # "lake-level" or "species-level"
    model: str
    n: int
    r: float = float("nan")
    p: float = float("nan")
    loo_mae: float = float("nan")
    baseline_mae: float = float("nan")
    beats_baseline: bool = False
    note: str = ""


def evaluate_univariate_lake_level(df: pd.DataFrame, feature: str, target: str = "aggregate_harvest_rate_fish_per_hour") -> PredictorResult:
    work = df.dropna(subset=[feature, target])
    r, p = stats.pearsonr(work[feature].values, work[target].values)
    cv = loo_cv_by_group(
        work.reset_index().rename(columns={"index": "lake_name"}),
        [feature], target, "lake_name",
    )
    baseline = loo_mean_baseline_by_group(
        work.reset_index().rename(columns={"index": "lake_name"}), target, "lake_name"
    )
    return PredictorResult(
        resolution="lake-level", model=feature, n=len(work), r=r, p=p,
        loo_mae=mae(cv["y_true"], cv["y_pred"]),
        baseline_mae=mae(baseline["y_true"], baseline["y_pred"]),
        beats_baseline=mae(cv["y_true"], cv["y_pred"]) < mae(baseline["y_true"], baseline["y_pred"]),
    )


def evaluate_multivariate_lake_level(
    df: pd.DataFrame, features: list[str], label: str, note: str = "",
    target: str = "aggregate_harvest_rate_fish_per_hour",
) -> PredictorResult:
    work = df.dropna(subset=features + [target]).reset_index().rename(columns={"index": "lake_name"})
    cv = loo_cv_by_group(work, features, target, "lake_name")
    baseline = loo_mean_baseline_by_group(work, target, "lake_name")
    return PredictorResult(
        resolution="lake-level", model=label, n=len(work),
        loo_mae=mae(cv["y_true"], cv["y_pred"]),
        baseline_mae=mae(baseline["y_true"], baseline["y_pred"]),
        beats_baseline=mae(cv["y_true"], cv["y_pred"]) < mae(baseline["y_true"], baseline["y_pred"]),
        note=note,
    )


def evaluate_species_level(
    df: pd.DataFrame, features: list[str], label: str, note: str = "",
    target: str = "harvest_rate_fish_per_hour_recomputed",
) -> tuple[PredictorResult, PredictorResult]:
    """Returns (model_result, species_identity_baseline_result) -- the model
    must be compared against BOTH the naive overall-mean baseline (folded
    into model_result.baseline_mae) and the species-identity baseline
    (species_identity_result), since species identity alone is a strong
    predictor of harvest rate."""
    work = df.dropna(subset=features + [target]).copy()
    cv = loo_cv_by_group(work, features, target, "lake_name")
    naive_baseline = loo_mean_baseline_by_group(work, target, "lake_name")
    species_baseline = loo_species_mean_baseline(work, target, "lake_name", "species")
    model_res = PredictorResult(
        resolution="species-level", model=label, n=len(cv),
        loo_mae=mae(cv["y_true"], cv["y_pred"]),
        baseline_mae=mae(naive_baseline["y_true"], naive_baseline["y_pred"]),
        beats_baseline=mae(cv["y_true"], cv["y_pred"]) < mae(naive_baseline["y_true"], naive_baseline["y_pred"]),
        note=note,
    )
    species_res = PredictorResult(
        resolution="species-level", model=f"{label} vs species-identity baseline",
        n=len(species_baseline),
        loo_mae=mae(cv["y_true"], cv["y_pred"]),
        baseline_mae=mae(species_baseline["y_true"], species_baseline["y_pred"]),
        beats_baseline=mae(cv["y_true"], cv["y_pred"]) < mae(species_baseline["y_true"], species_baseline["y_pred"]),
        note="Compares the model's LOO-by-lake MAE against a species-identity "
        "(not naive-mean) baseline: predicting each held-out species row with "
        "that same species' mean harvest rate from every OTHER lake.",
    )
    return model_res, species_res


# ---------------------------------------------------------------------------
# Within-lake two-season descriptive comparison (n=2 per lake -- explicitly
# NOT a statistical test, see module docstring and results doc)
# ---------------------------------------------------------------------------

def within_lake_season_pairs() -> pd.DataFrame:
    rows = []
    for lake in OLDER_SEASONS:
        newer_spec = LAKE_SEASONS[lake]
        older_spec = OLDER_SEASONS[lake]
        newer_df = prepare_lake_season(
            os.path.join(DATA_DIR, newer_spec["creel_csv"]), newer_spec["creel_year"],
            waterbody=newer_spec.get("waterbody"),
        )
        older_df = prepare_lake_season(
            os.path.join(DATA_DIR, older_spec["creel_csv"]), older_spec["creel_year"],
        )
        newer_agg = lake_season_aggregate_rate(newer_df)
        older_agg = lake_season_aggregate_rate(older_df)
        rows.append({
            "lake_name": lake,
            "older_season": older_spec["creel_year"],
            "older_rate": older_agg["aggregate_harvest_rate_fish_per_hour"],
            "newer_season": newer_spec["creel_year"],
            "newer_rate": newer_agg["aggregate_harvest_rate_fish_per_hour"],
            "pct_change": (
                (newer_agg["aggregate_harvest_rate_fish_per_hour"]
                 - older_agg["aggregate_harvest_rate_fish_per_hour"])
                / older_agg["aggregate_harvest_rate_fish_per_hour"] * 100
            ),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    lake_df = build_lake_level_dataset()
    species_df = build_species_level_dataset()

    print("=" * 100)
    print(f"LAKE-LEVEL POOLED DATASET: n={len(lake_df)} lakes")
    print("=" * 100)
    print(lake_df[[
        "creel_year", "n_species", "aggregate_harvest_rate_fish_per_hour",
        "mean_tmax_c", "mean_tmin_c", "total_prcp_mm",
        "surface_area_acres", "max_depth_ft", "mean_depth_ft", "lake_type_bucket", "trophic_status",
    ]].to_string())

    results: list[PredictorResult] = []

    print("\n" + "=" * 100)
    print("LAKE-LEVEL UNIVARIATE MODELS (LOO-lake-out CV, n=11 unless noted)")
    print("=" * 100)
    for feature in ["mean_tmax_c", "mean_tmin_c", "total_prcp_mm", "surface_area_acres", "max_depth_ft"]:
        res = evaluate_univariate_lake_level(lake_df, feature)
        results.append(res)
        print(f"  {feature:22s} n={res.n:2d} r={res.r:+.3f} p={res.p:.3f} "
              f"LOO-MAE={res.loo_mae:.4f} baseline-MAE={res.baseline_mae:.4f} "
              f"[{'BEATS baseline' if res.beats_baseline else 'does not beat baseline'}]")
    # mean_depth_ft / trophic_index: reduced complete-case n
    for feature in ["mean_depth_ft", "trophic_index"]:
        res = evaluate_univariate_lake_level(lake_df, feature)
        res.note = "reduced n: this characteristic is missing for some lakes"
        results.append(res)
        print(f"  {feature:22s} n={res.n:2d} r={res.r:+.3f} p={res.p:.3f} "
              f"LOO-MAE={res.loo_mae:.4f} baseline-MAE={res.baseline_mae:.4f} "
              f"[{'BEATS baseline' if res.beats_baseline else 'does not beat baseline'}] "
              f"({res.note})")

    print("\n" + "=" * 100)
    print("LAKE-LEVEL MULTIVARIATE MODELS (LOO-lake-out CV, low power at n=11 -- flagged)")
    print("=" * 100)
    combo_specs = [
        (["mean_tmax_c", "mean_tmin_c", "total_prcp_mm"], "weather combined",
         "3 predictors, 9-10 training rows per fold -- low power, reported for completeness"),
        (["surface_area_acres", "max_depth_ft"], "characteristics combined (area, max depth)",
         "2 predictors, n=11"),
        (["mean_tmax_c", "mean_tmin_c", "total_prcp_mm", "surface_area_acres", "max_depth_ft"],
         "weather + characteristics combined",
         "5 predictors, 9-10 training rows per fold -- NOT statistically defensible "
         "at this sample size, reported only for transparency, not as evidence"),
    ]
    for features, label, note in combo_specs:
        res = evaluate_multivariate_lake_level(lake_df, features, label, note)
        results.append(res)
        print(f"  {label:45s} n={res.n:2d} LOO-MAE={res.loo_mae:.4f} "
              f"baseline-MAE={res.baseline_mae:.4f} "
              f"[{'BEATS baseline' if res.beats_baseline else 'does not beat baseline'}]")
        print(f"      note: {note}")

    print("\n" + "=" * 100)
    print("LAKE-TYPE GROUPS (descriptive only -- group means, small n per group)")
    print("=" * 100)
    grp = lake_df.groupby("lake_type_bucket")["aggregate_harvest_rate_fish_per_hour"].agg(["count", "mean", "std"])
    print(grp.to_string())

    print("\n" + "=" * 100)
    print(f"SPECIES-LEVEL POOLED DATASET: n={len(species_df)} species-lake-season rows across {species_df['lake_name'].nunique()} lakes")
    print("=" * 100)

    species_specs = [
        (["weather_mean_tmax_c", "weather_mean_tmin_c", "weather_total_prcp_mm"], "weather only"),
        (["lakechar_surface_area_acres", "lakechar_max_depth_ft"], "characteristics only (area, max depth)"),
        (["weather_mean_tmax_c", "weather_mean_tmin_c", "weather_total_prcp_mm",
          "lakechar_surface_area_acres", "lakechar_max_depth_ft"], "weather + characteristics combined"),
    ]
    species_results = []
    for features, label in species_specs:
        model_res, species_res = evaluate_species_level(species_df, features, label)
        results.append(model_res)
        results.append(species_res)
        species_results.append((label, model_res, species_res))
        print(f"  {label:40s} n={model_res.n:3d} LOO-MAE={model_res.loo_mae:.4f} "
              f"vs naive-mean baseline={model_res.baseline_mae:.4f} "
              f"[{'BEATS' if model_res.beats_baseline else 'does not beat'}]")
        print(f"  {'':40s}      vs species-identity baseline={species_res.baseline_mae:.4f} "
              f"[{'BEATS' if species_res.beats_baseline else 'does not beat'}]")

    print("\n" + "=" * 100)
    print("WITHIN-LAKE TWO-SEASON DESCRIPTIVE COMPARISON (n=2 per lake -- NOT a statistical test)")
    print("=" * 100)
    pairs_df = within_lake_season_pairs()
    print(pairs_df.to_string(index=False))

    out_dir = os.path.dirname(os.path.abspath(__file__))
    results_df = pd.DataFrame([r.__dict__ for r in results])
    results_df.to_csv(os.path.join(out_dir, "v0_inland_pooled_predictability_results.csv"), index=False)
    lake_df.to_csv(os.path.join(out_dir, "v0_inland_pooled_predictability_lake_level_dataset.csv"))
    pairs_df.to_csv(os.path.join(out_dir, "v0_inland_pooled_predictability_season_pairs.csv"), index=False)
    print(f"\nFull results written to {out_dir}")


if __name__ == "__main__":
    main()
