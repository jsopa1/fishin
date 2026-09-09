"""
V0 predictor-eval (Decision #009, step 2) -- fish physiology/behavior as a
candidate-predictor class, tested against the project's real held-out catch/
harvest-rate outcome data, with the same LOO-CV / baseline-comparison
discipline used throughout V0 (analysis/v0_lake_michigan_eval.py,
analysis/v0_inland_pooled_predictability.py).

THE QUESTION (Decision #009): does testing established fish physiology
science as predictors explain more real, held-out variance in catch/harvest
rate than the weather/lake-characteristics predictors already tested and
found to have no reliable signal? This directly tests the
"angler-skill-noise-masking-a-real-signal" hypothesis.

Candidate source: docs/v0_physiology_research_candidates.md (step 1, this
cycle). Every numeric temperature value used below traces to a specific
citation in that document OR to a primary source retrieved directly in this
step (Wismer & Christie 1987, Great Lakes Fishery Commission Special
Publication 87-3, "Temperature Relationships of Great Lakes Fishes: A Data
Compilation" -- successfully fetched and parsed in this step; the research
doc could not parse it and flagged several numbers as needing re-sourcing).
Every such re-sourced number is documented in PHYSIOLOGY_TEMPERATURES below
with its citation. Candidate #16 (Hasnain, Minns & Shuter 2010, Ontario MNR
CCRR-17) could NOT be retrieved in this step either (the ontario.ca URL
pattern found by search returned different, unrelated CCRR reports --
CCRR-21, CCRR-22 -- not CCRR-17); this is disclosed, not papered over.
Candidate #1 (walleye diel/light-window) is not computable against this
project's outcome data (no trip-level timestamp exists anywhere in the creel
data) and is not attempted here, per the research doc's own explicit
instruction.

PART 1 -- Lake Michigan (primary target). Real daily water temperature
(NDBC buoy 45007 WTMP) aggregated to the SAME temporal resolution as the
outcome data:
  1a. ANNUAL: distance-from-preferred-temperature-band predictors for
      Yellow Perch and "All salmonids combined" against the annual harvest
      rate CSV (2013-2024 outcome, 2015-2024 buoy coverage) -- directly
      mirrors the resolution and years used in v0_lake_michigan_eval.py, so
      results are directly comparable to that script's weather/wave/
      pressure findings.
  1b. MONTHLY (bonus/secondary): the same distance-from-preferred-temp
      predictors for Walleye, Yellow Perch, and Coho Salmon against the
      monthly-by-species harvest rate data (2022 and 2024 only, 6 named
      periods/year -- real but limited to 2 years, n=12 per species).

PART 2 -- Inland lakes. The research doc found NO water temperature data
existed anywhere in data/v0/ for any inland lake (only air temperature).
Before falling back to any estimation, this step went and pulled REAL water
temperature data from the Wisconsin DNR's own Citizen Lake Monitoring
Network (CLMN) SWIMS database (apps.dnr.wi.gov/swims/LakesReport/
DownloadTemperatureReport) for the deep-hole/best-coverage monitoring
station at each of the 11 inland lakes with creel outcome data, restricted
to shallow-depth (<=3 ft, i.e. near-surface, comparable to what the NDBC
buoy's WTMP reading represents for Lake Michigan) readings that fall inside
each lake's own real creel-survey window (data/v0/lake_characteristics.csv,
same windows already established in v0_inland_pooled_predictability.py).
Real, in-window water temperature readings were found for 6 of the 11
lakes: Minocqua, Pelican, Devils, Pine, Sand, White Potato. The other 5
(Big Green, Lake Wisconsin, Petenwell, Sawyer, Lake Wissota) have CLMN
temperature/DO records at their best-coverage station, but NONE of those
records fall inside that lake's specific creel-survey window -- so those 5
are logged as NOT TESTABLE this cycle for lack of real water temperature
data in the relevant window (per Decision #005 and the task's own explicit
instruction, no estimation was substituted here; this is disclosed as a
real, honest data gap, not implied to be missing entirely).
Real raw per-reading water-temperature series pulled this cycle:
data/v0/inland_water_temp_{minocqua,pelican,devils,pinelake,sandlake,
whitepotato}.csv; the in-creel-window mean per lake is in
data/v0/inland_water_temp_summary.csv. A data-quality issue was found and
disclosed while parsing this data: some deep readings in the WDNR SWIMS
export carry a mislabeled "DEGREES F" unit tag on values that are clearly
still Celsius (continuous with the shallower, correctly-labeled Celsius
readings in the same depth profile -- e.g. Devils Lake 2024-05-23, values
descend smoothly 18.9, 18.8, ..., 10.7 (depth 9ft, labeled C), then 10.1
(depth 10ft, mislabeled F) continuing the same smooth decline). This does
not affect the shallow (<=3ft) readings used here (checked: no mislabeled
units were found at shallow depth in any of the 6 lakes' data), but is
disclosed for anyone using the deeper rows in the raw per-lake CSVs.

For the 6 lakes with real water temperature, species-level physiology
predictors (distance from each species' own preferred-temperature value,
per PHYSIOLOGY_TEMPERATURES below) are tested against real recomputed
species harvest rates (same total_harvest/directed_effort_hours recompute
discipline as v0_inland_pooled_predictability.py), both per-species and
pooled across species with leave-one-LAKE-out cross-validation (same
discipline as that script, including its disclosed pseudo-replication
caveat: only 6 independent water-temperature "treatments" underlie the
pooled species-level rows, even though more rows are used to fit).

Method: single-variable linear regression / Pearson correlation only, LOO-CV
(by year for Lake Michigan, by lake for inland), always compared against a
naive LOO historical/lake mean baseline computed on the exact same held-out
units. No model beyond this is used anywhere, per Decision #002 and the
precedent set by every other V0 evaluation script -- sample sizes here (n=6
to n=36, mostly under 15) are far too small for anything else.

Run: python analysis/v0_physiology_predictors_eval.py
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

LM_HARVEST_ANNUAL_CSV = os.path.join(
    DATA_DIR, "lake_michigan_creel_harvest_rate_annual_by_species.csv"
)
LM_HARVEST_MONTHLY_CSV = os.path.join(
    DATA_DIR, "lake_michigan_creel_monthly_by_species_2022_2024.csv"
)
LM_NDBC_DAILY_CSV = os.path.join(DATA_DIR, "lake_michigan_ndbc_45007_daily.csv")
INLAND_WATERTEMP_SUMMARY_CSV = os.path.join(DATA_DIR, "inland_water_temp_summary.csv")

# ---------------------------------------------------------------------------
# Physiology-derived preferred/optimal temperatures, one number (or averaged
# set of numbers) per species, EVERY one traceable to a specific citation.
# distance-from-this-value is the predictor tested for each species below.
# Values in degrees Celsius (converted from source units where the source
# reported degF).
# ---------------------------------------------------------------------------

PHYSIOLOGY_TEMPERATURES = {
    "Walleye": dict(
        temp_c=20.6,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, LARGE walleye, Trout Lake, Wisconsin field study "
        "(orig. cited as Coutant 1977a). Directly Wisconsin-sourced field "
        "data, the strongest single number available for this species in "
        "this pass -- upgrades the research doc's fuzzier 62-68F "
        "(16.7-20C) 'preference cluster' framing to one specific "
        "real-field, Wisconsin-specific value.",
    ),
    "Yellow Perch": dict(
        temp_c=20.8,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, Lake Michigan field study (orig. cited as Coutant "
        "1977a). Used for the Lake Michigan test. A closely comparable "
        "Wisconsin-inland-lake field value (20.2C, Trout Lake / Silver "
        "Lake, WI, same source) is used for the inland-lake test below "
        "(YELLOW_PERCH_INLAND_TEMP_C) since it is more locally specific "
        "than the Lake Michigan number.",
    ),
    "Coho Salmon": dict(
        temp_c=11.4,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, adult, Lake Michigan field study (orig. cited as "
        "Coutant 1977a). This REPLACES the research doc's flagged, "
        "charter-fishing-sourced 54-60F figure with a primary-sourced, "
        "Lake-Michigan-specific field value, resolving the research doc's "
        "note 4 flag for this candidate.",
    ),
    "Chinook Salmon": dict(
        temp_c=11.7,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, adult, Lake Michigan field study (orig. cited as "
        "Coutant 1977a). Replaces the research doc's flagged, "
        "charter-fishing-sourced 52-56F figure with a primary-sourced, "
        "Lake-Michigan-specific field value.",
    ),
    "Lake Trout": dict(
        temp_c=11.8,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, Point Beach, Lake Michigan field study (orig. cited "
        "as Talmage & Coutant 1980). Resolves the research doc's note that "
        "this candidate's citation was incomplete pending direct GLFC "
        "retrieval.",
    ),
    "Brown Trout": dict(
        temp_c=13.8,
        source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
        "preferendum, adult, Lake Michigan (rising water temps) field "
        "study (orig. cited as Cherry et al. 1977) -- one of several "
        "Lake-Michigan field readings in the source (12.2-19.9C range "
        "across studies/life stages); this single adult field value is "
        "used as the representative point estimate, with the wider range "
        "disclosed here rather than hidden.",
    ),
}

# Wisconsin-inland-lake-specific yellow perch value (see note above).
YELLOW_PERCH_INLAND_TEMP_C = dict(
    temp_c=20.2,
    source="Wismer & Christie 1987 (GLFC Sp87-3), final temperature "
    "preferendum, large yellow perch, Trout Lake / Silver Lake, Wisconsin "
    "field studies (orig. cited as Coutant 1977a).",
)

# Combined "Great Lakes coldwater salmonid guild" preference, used for the
# LM outcome category "All salmonids combined" (which spans Chinook, Coho,
# Lake Trout, Brown Trout, Rainbow Trout per the outcome CSV's own category
# description) -- per the research doc's own note 4 fallback instruction
# ("use the general distance-from-typical-Great-Lakes-coldwater-salmonid-
# preference framing"), now made concrete with primary GLFC field numbers
# for the four salmonid species actually retrievable from the source in
# this pass (Chinook, Coho, Lake Trout, Brown Trout -- Rainbow Trout was
# not confirmed in the LM species-level data and is not included in the
# average).
SALMONID_GUILD_TEMP_C = dict(
    temp_c=round(
        (
            PHYSIOLOGY_TEMPERATURES["Chinook Salmon"]["temp_c"]
            + PHYSIOLOGY_TEMPERATURES["Coho Salmon"]["temp_c"]
            + PHYSIOLOGY_TEMPERATURES["Lake Trout"]["temp_c"]
            + PHYSIOLOGY_TEMPERATURES["Brown Trout"]["temp_c"]
        )
        / 4,
        2,
    ),
    source="Simple average of the 4 GLFC Sp87-3 Lake-Michigan-field final "
    "temperature preferenda above (Chinook 11.7C, Coho 11.4C, Lake Trout "
    "11.8C, Brown Trout 13.8C) = 12.18C. A simple average across species "
    "with very different life histories is a real methodological "
    "approximation (disclosed, not hidden) -- the true 'combined salmonid "
    "guild optimum' is not itself a physiological quantity that exists in "
    "the literature; this is this analysis's own construction for testing "
    "the 'All salmonids combined' outcome category, not a claim from the "
    "source.",
)

# Inland-lake species temperature values (research doc candidates #5-#10;
# candidate #11 bluegill has no numeric OPTIMUM in the research doc, only a
# spawning-trigger THRESHOLD, so it is tested differently -- see
# evaluate_bluegill_threshold()).
INLAND_SPECIES_TEMPERATURES = {
    "Largemouth Bass": dict(
        temp_c=26.5,
        source="Research doc candidate #5: midpoint of the 25-28C growth-"
        "optimum range reported across several aquaculture/growth studies. "
        "FLAGGED: this is a growth-optimum, not a catchability-optimum, "
        "and the research doc notes conflicting evidence (one study found "
        "higher feeding rates at 18C) -- treated here as the primary "
        "hypothesis per the research doc's own priority ranking, with the "
        "conflict disclosed, not resolved.",
    ),
    "Smallmouth Bass": dict(
        temp_c=23.5,
        source="Research doc candidate #6: midpoint of 22-25C, from a "
        "field telemetry study specifically IN Lake Michigan (directly "
        "relevant water body, comparatively strong evidence per the "
        "research doc).",
    ),
    "Northern Pike": dict(
        temp_c=20.0,
        source="Research doc candidate #7: midpoint of the 19-21C "
        "physiological growth-optimum range (laboratory/experimental "
        "physiology studies, per the research doc).",
    ),
    "Muskellunge": dict(
        temp_c=22.0,
        source="Research doc candidate #9: thermal optimum from field "
        "telemetry/radio-tracking studies (Bieber et al. 2024 and others, "
        "per the research doc).",
    ),
    "Black Crappie": dict(
        temp_c=28.0,
        source="Research doc candidate #10: midpoint of 27-29C preferred "
        "temperature. FLAGGED as the WEAKEST-evidence candidate carried "
        "into this step -- the research doc notes the source for this "
        "specific number is an undergraduate research report, not a "
        "primary journal article.",
    ),
    "Walleye": dict(
        temp_c=20.6,
        source="Same GLFC Sp87-3 Wisconsin field value used for the Lake "
        "Michigan walleye test above (Trout Lake, WI).",
    ),
    "Yellow Perch": YELLOW_PERCH_INLAND_TEMP_C,
}


# ---------------------------------------------------------------------------
# Shared daily/period aggregation + LOO/baseline helpers (deliberately
# reimplemented here rather than imported from v0_lake_michigan_eval.py or
# v0_inland_pooled_predictability.py, matching this project's existing
# precedent of keeping each evaluation script import-independent -- see the
# module docstring of v0_inland_pooled_predictability.py for the same
# rationale). Logic is intentionally identical/equivalent to those scripts
# and covered by its own tests in analysis/tests/.
# ---------------------------------------------------------------------------

def aggregate_daily_to_annual(df: pd.DataFrame, date_col: str, value_cols: list[str]) -> pd.DataFrame:
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    work["year"] = work[date_col].dt.year
    agg = work.groupby("year")[value_cols].mean()
    counts = work.groupby("year")[value_cols[0]].count().rename("n_days")
    return agg.join(counts)


def aggregate_daily_to_period(
    df: pd.DataFrame, date_col: str, value_col: str, year: int, start_md: str, end_md: str
) -> float | None:
    """Mean of value_col over [year-start_md, year-end_md] inclusive. Used to
    match Lake Michigan's monthly-by-species outcome periods (e.g.
    'March/April' -> start_md='03-01', end_md='04-30') to the same-window
    daily NDBC mean. Returns None if no daily observations fall in the
    window (never silently substitutes a different window)."""
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    start = pd.Timestamp(f"{year}-{start_md}")
    end = pd.Timestamp(f"{year}-{end_md}")
    mask = (work[date_col] >= start) & (work[date_col] <= end)
    sub = work.loc[mask, value_col].dropna()
    if len(sub) == 0:
        return None
    return float(sub.mean())


PERIOD_WINDOWS = {
    "March/April": ("03-01", "04-30"),
    "May": ("05-01", "05-31"),
    "June": ("06-01", "06-30"),
    "July": ("07-01", "07-31"),
    "August": ("08-01", "08-31"),
    "Sept/Oct": ("09-01", "10-31"),
}


def loo_mean_baseline(y: pd.Series) -> pd.Series:
    preds = {}
    for idx in y.index:
        other = y.drop(index=idx)
        preds[idx] = other.mean()
    return pd.Series(preds)


def mae(y_true, y_pred) -> float:
    yt = pd.Series(y_true)
    yp = pd.Series(y_pred)
    common = yt.index.intersection(yp.index)
    return float(np.mean(np.abs(yt.loc[common] - yp.loc[common])))


def loo_linear_predictions(x: pd.Series, y: pd.Series) -> pd.Series:
    """LOO-CV for y ~ a + b*x over the overlapping index. Requires >=4
    overlapping points (see v0_lake_michigan_eval.py for the same rule and
    rationale: a 3-point fit-then-hold-out-1 is a degenerate 2-point fit)."""
    common = x.index.intersection(y.index)
    x = x.loc[common].sort_index()
    y = y.loc[common].sort_index()
    if len(common) < 4:
        return pd.Series(dtype=float)
    preds = {}
    for idx in x.index:
        train_idx = x.index.difference([idx])
        xt = x.loc[train_idx].values
        yt = y.loc[train_idx].values
        b, a = np.polyfit(xt, yt, 1)
        preds[idx] = a + b * x.loc[idx]
    return pd.Series(preds)


@dataclass
class CandidateResult:
    candidate: str
    outcome: str
    n: int
    units: str  # "years" or "lake-seasons" or "monthly periods"
    pearson_r: float
    pearson_p: float
    loo_model_mae: float
    loo_baseline_mae: float
    beats_baseline: bool
    note: str = ""


def evaluate_distance_candidate(
    candidate_name: str, x_distance: pd.Series, y: pd.Series, units: str, note: str = ""
) -> CandidateResult:
    common = x_distance.index.intersection(y.index)
    x_c = x_distance.loc[common].sort_index()
    y_c = y.loc[common].sort_index()
    if len(common) < 4:
        return CandidateResult(
            candidate=candidate_name, outcome="", n=len(common), units=units,
            pearson_r=float("nan"), pearson_p=float("nan"),
            loo_model_mae=float("nan"), loo_baseline_mae=float("nan"),
            beats_baseline=False,
            note=(note + " | too few overlapping points (<4) for LOO CV").strip(" |"),
        )
    r, p = stats.pearsonr(x_c.values, y_c.values)
    model_preds = loo_linear_predictions(x_c, y_c)
    baseline_preds = loo_mean_baseline(y_c)
    m_mae = mae(y_c, model_preds)
    b_mae = mae(y_c, baseline_preds)
    return CandidateResult(
        candidate=candidate_name, outcome="", n=len(common), units=units,
        pearson_r=r, pearson_p=p, loo_model_mae=m_mae, loo_baseline_mae=b_mae,
        beats_baseline=m_mae < b_mae, note=note,
    )


# ---------------------------------------------------------------------------
# Part 1: Lake Michigan
# ---------------------------------------------------------------------------

def load_lm_annual_outcomes() -> dict[str, pd.Series]:
    df = pd.read_csv(LM_HARVEST_ANNUAL_CSV)
    out = {}
    for species, group in df.groupby("species"):
        out[species] = group.set_index("year")["harvest_rate_fish_per_hour"].sort_index()
    return out


def load_lm_annual_wtmp() -> pd.Series:
    df = pd.read_csv(LM_NDBC_DAILY_CSV)
    annual = aggregate_daily_to_annual(df, "date", ["WTMP_mean"])
    return annual["WTMP_mean"]


def load_lm_monthly_outcomes() -> pd.DataFrame:
    df = pd.read_csv(LM_HARVEST_MONTHLY_CSV)
    df["year"] = df["year"].astype(int)
    return df


def build_lm_monthly_wtmp(ndbc_df: pd.DataFrame) -> dict[tuple[str, int], float | None]:
    out = {}
    for year in (2022, 2024):
        for period, (start_md, end_md) in PERIOD_WINDOWS.items():
            out[(period, year)] = aggregate_daily_to_period(
                ndbc_df, "date", "WTMP_mean", year, start_md, end_md
            )
    return out


def run_lake_michigan(results: list[CandidateResult]) -> None:
    print("=" * 100)
    print("PART 1: LAKE MICHIGAN -- physiology-derived (distance-from-preferred-temperature) predictors")
    print("=" * 100)

    outcomes = load_lm_annual_outcomes()
    salmonids = outcomes["All salmonids combined"]
    perch = outcomes["Yellow perch (total)"]
    wtmp_annual = load_lm_annual_wtmp()

    perch_dist = (wtmp_annual - PHYSIOLOGY_TEMPERATURES["Yellow Perch"]["temp_c"]).abs()
    perch_dist.name = "yellow_perch_dist_from_20.8C"
    salmonid_dist = (wtmp_annual - SALMONID_GUILD_TEMP_C["temp_c"]).abs()
    salmonid_dist.name = "salmonid_guild_dist_from_12.18C"

    print("\n--- 1a. Annual (2013-2024 outcome, 2015-2024 real NDBC WTMP coverage) ---")
    r1 = evaluate_distance_candidate(
        "Yellow Perch: |annual mean WTMP - 20.8C GLFC LM field preferendum|",
        perch_dist, perch, units="years",
        note="GLFC Sp87-3 primary-sourced value (candidate #4, upgraded from the "
        "research doc's aquaculture-growth-optimum number)",
    )
    r1.outcome = "Yellow perch (total)"
    results.append(r1)
    r2 = evaluate_distance_candidate(
        "All salmonids combined: |annual mean WTMP - 12.18C combined-guild GLFC field value|",
        salmonid_dist, salmonids, units="years",
        note="Combines GLFC Sp87-3 primary field values for Chinook/Coho/Lake Trout/"
        "Brown Trout per research doc note 4's fallback instruction (candidates #12-15)",
    )
    r2.outcome = "All salmonids combined"
    results.append(r2)
    for res in (r1, r2):
        _print_result(res)

    print("\n--- 1b. Monthly (2022 & 2024 only, 6 periods/year, n=12 per species; SECONDARY/bonus) ---")
    monthly_df = load_lm_monthly_outcomes()
    ndbc_df = pd.read_csv(LM_NDBC_DAILY_CSV)
    period_wtmp = build_lm_monthly_wtmp(ndbc_df)

    monthly_specs = [
        ("Walleye", PHYSIOLOGY_TEMPERATURES["Walleye"]["temp_c"], "#2/#3 (GLFC WI field value)"),
        ("Yellow Perch", PHYSIOLOGY_TEMPERATURES["Yellow Perch"]["temp_c"], "#4 (GLFC LM field value)"),
        ("Coho Salmon", PHYSIOLOGY_TEMPERATURES["Coho Salmon"]["temp_c"], "#13 (GLFC LM field value, replaces charter-sourced number)"),
    ]
    for species, temp_c, tag in monthly_specs:
        sub = monthly_df[monthly_df["species"] == species].copy()
        sub["wtmp"] = sub.apply(lambda row: period_wtmp.get((row["period"], row["year"])), axis=1)
        sub = sub.dropna(subset=["wtmp"])
        sub["dist"] = (sub["wtmp"] - temp_c).abs()
        sub["key"] = sub["period"] + "_" + sub["year"].astype(str)
        x = sub.set_index("key")["dist"]
        y = sub.set_index("key")["season_harvest_rate_fish_per_hour"]
        res = evaluate_distance_candidate(
            f"{species} (monthly): |period mean WTMP - {temp_c}C| {tag}",
            x, y, units="monthly periods (2022+2024)",
            note="secondary/bonus test -- only 2 years of monthly LM data exist",
        )
        res.outcome = f"{species} (monthly)"
        results.append(res)
        _print_result(res)


def _print_result(res: CandidateResult) -> None:
    sig = "p<0.05" if (res.pearson_p == res.pearson_p and res.pearson_p < 0.05) else "n.s."
    print(
        f"  [{res.outcome}] {res.candidate}\n"
        f"    n={res.n} {res.units}  r={res.pearson_r:+.3f} ({sig}, p={res.pearson_p:.3f})  "
        f"LOO_MAE model={res.loo_model_mae:.4f} vs baseline={res.loo_baseline_mae:.4f} "
        f"[{'BEATS' if res.beats_baseline else 'does not beat'} baseline]"
    )
    if res.note:
        print(f"      note: {res.note}")


# ---------------------------------------------------------------------------
# Part 2: Inland lakes
# ---------------------------------------------------------------------------

INLAND_LAKE_SEASONS = {
    "Minocqua Lake": dict(creel_csv="minocqualake_creel_2009_10_2024_25.csv", creel_year="2024-25"),
    "Pelican Lake": dict(creel_csv="pelicanlake_creel_2011_12_2024_25.csv", creel_year="2024-25"),
    "Devils Lake": dict(creel_csv="devilslake_creel_2023_24.csv", creel_year="Jul 2023-Jun 2024"),
    "Pine Lake": dict(creel_csv="pinelake_creel_2017_18_2023_24.csv", creel_year="2023-24"),
    "Sand Lake": dict(creel_csv="sandlake_creel_2007_08_2023_24.csv", creel_year="2023-24"),
    "White Potato Lake": dict(creel_csv="whitepotatolake_creel_2019_20.csv", creel_year="2019-20"),
}

# 5 lakes with real CLMN temperature data at the best-coverage station, but
# NO readings inside the exact creel-survey window -- logged as untestable,
# not silently dropped.
INLAND_LAKES_NOT_TESTABLE = {
    "Big Green Lake": "CLMN West Basin Deep Hole station (USGS 434756089020500, "
        "id 243049) has real temperature/DO data 1987-2018, but the lake's "
        "creel-survey window is 2022-23 -- no overlap.",
    "Lake Wisconsin": "CLMN Deep Hole station (id 573125) has real data "
        "1995-2024, but none of the readings fall inside the 2022-23 "
        "creel-survey window checked (2022-09 through 2023-05).",
    "Petenwell Lake": "Best-coverage CLMN stations found (Deep Hole id "
        "013134, and two other 2023-max-year stations) have only 4-7 total "
        "readings each, none inside the Mar-Jun 2023 creel-survey window.",
    "Sawyer Lake": "CLMN Deep Hole stations (ids 343132, 343150) have real "
        "data only through 2019/2025 respectively with no readings inside "
        "the Summer 2023 creel-survey window at the 343132 station "
        "(343150 returned zero records at all).",
    "Lake Wissota": "No CLMN station checked (Mid Lake N End id 093105, "
        "plus 3 additional stations tried) returned any temperature/DO "
        "records at all via the SWIMS download endpoint.",
}


def prepare_lake_species(csv_path: str, creel_year: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, csv_path))
    df = df[df["creel_year"].astype(str).str.strip() == creel_year].copy()
    df = df[df["directed_effort_hours"].notna() & (df["directed_effort_hours"] > 0)]
    df["harvest_rate_recomputed"] = df["total_harvest"].fillna(0) / df["directed_effort_hours"]
    return df[["waterbody", "species", "directed_effort_hours", "total_harvest", "harvest_rate_recomputed"]]


def load_inland_watertemp_summary() -> pd.Series:
    df = pd.read_csv(INLAND_WATERTEMP_SUMMARY_CSV)
    return df.set_index("lake")["mean_temp_c_in_window"]


def loo_cv_by_lake(df: pd.DataFrame, feature_col: str, target_col: str) -> pd.DataFrame:
    results = []
    for held_out in df["lake_name"].unique():
        train = df[df["lake_name"] != held_out]
        test = df[df["lake_name"] == held_out]
        if len(train) < 3 or len(test) == 0:
            continue
        b, a = np.polyfit(train[feature_col].values, train[target_col].values, 1)
        for _, row in test.iterrows():
            results.append(dict(lake=held_out, y_true=row[target_col], y_pred=a + b * row[feature_col]))
    return pd.DataFrame(results)


def loo_lake_mean_baseline(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    results = []
    for held_out in df["lake_name"].unique():
        train = df[df["lake_name"] != held_out]
        test = df[df["lake_name"] == held_out]
        pred = train[target_col].mean()
        for _, row in test.iterrows():
            results.append(dict(lake=held_out, y_true=row[target_col], y_pred=pred))
    return pd.DataFrame(results)


def loo_species_identity_baseline(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    results = []
    for held_out in df["lake_name"].unique():
        train = df[df["lake_name"] != held_out]
        test = df[df["lake_name"] == held_out]
        species_means = train.groupby("species")[target_col].mean()
        overall = train[target_col].mean()
        for _, row in test.iterrows():
            pred = species_means.get(row["species"], overall)
            results.append(dict(lake=held_out, y_true=row[target_col], y_pred=pred))
    return pd.DataFrame(results)


def build_inland_species_dataset() -> pd.DataFrame:
    watertemp = load_inland_watertemp_summary()
    frames = []
    for lake, spec in INLAND_LAKE_SEASONS.items():
        if lake not in watertemp.index or pd.isna(watertemp.loc[lake]):
            continue
        sp_df = prepare_lake_species(spec["creel_csv"], spec["creel_year"])
        sp_df = sp_df.copy()
        sp_df["lake_name"] = lake
        sp_df["water_temp_c"] = watertemp.loc[lake]
        frames.append(sp_df)
    return pd.concat(frames, ignore_index=True)


def run_inland(results: list[CandidateResult]) -> None:
    print("\n" + "=" * 100)
    print("PART 2: INLAND LAKES -- physiology-derived predictors using REAL WDNR CLMN water temperature")
    print("=" * 100)
    print("\nLakes with NO real water-temperature data inside their creel-survey window "
          "(logged untestable, not estimated):")
    for lake, reason in INLAND_LAKES_NOT_TESTABLE.items():
        print(f"  - {lake}: {reason}")

    all_species = build_inland_species_dataset()
    watertemp = load_inland_watertemp_summary()
    print(f"\nLakes WITH real in-window water temperature (n={watertemp.dropna().shape[0]}): "
          f"{dict(watertemp.dropna().round(2))}")

    print("\n--- 2a. Per-species distance-from-preferred-temperature (leave-one-lake-out CV) ---")
    for species, spec in INLAND_SPECIES_TEMPERATURES.items():
        sub = all_species[all_species["species"] == species].copy()
        sub = sub[sub["harvest_rate_recomputed"].notna() & (sub["total_harvest"].fillna(0) > 0)]
        sub["dist"] = (sub["water_temp_c"] - spec["temp_c"]).abs()
        n = sub["lake_name"].nunique()
        if n < 4:
            res = CandidateResult(
                candidate=f"{species}: |lake real mean water temp - {spec['temp_c']}C|",
                outcome=species, n=n, units="lake-seasons",
                pearson_r=float("nan"), pearson_p=float("nan"),
                loo_model_mae=float("nan"), loo_baseline_mae=float("nan"),
                beats_baseline=False,
                note=f"too few lakes with real, non-zero-harvest data for this species (<4) | {spec['source']}",
            )
        else:
            r, p = stats.pearsonr(sub["dist"].values, sub["harvest_rate_recomputed"].values)
            cv = loo_cv_by_lake(sub, "dist", "harvest_rate_recomputed")
            base = loo_lake_mean_baseline(sub, "harvest_rate_recomputed")
            m_mae = mae(cv["y_true"], cv["y_pred"]) if len(cv) else float("nan")
            b_mae = mae(base["y_true"], base["y_pred"]) if len(base) else float("nan")
            res = CandidateResult(
                candidate=f"{species}: |lake real mean water temp - {spec['temp_c']}C|",
                outcome=species, n=n, units="lake-seasons",
                pearson_r=r, pearson_p=p, loo_model_mae=m_mae, loo_baseline_mae=b_mae,
                beats_baseline=(m_mae < b_mae) if m_mae == m_mae else False,
                note=spec["source"],
            )
        results.append(res)
        _print_result(res)

    print("\n--- 2b. Pooled cross-species model (all species combined, leave-one-lake-out CV) ---")
    pooled = all_species.copy()
    pooled = pooled[pooled["species"].isin(INLAND_SPECIES_TEMPERATURES.keys())]
    pooled = pooled[pooled["harvest_rate_recomputed"].notna() & (pooled["total_harvest"].fillna(0) > 0)]
    pooled["dist"] = pooled.apply(
        lambda row: abs(row["water_temp_c"] - INLAND_SPECIES_TEMPERATURES[row["species"]]["temp_c"]), axis=1
    )
    cv = loo_cv_by_lake(pooled, "dist", "harvest_rate_recomputed")
    naive_base = loo_lake_mean_baseline(pooled, "harvest_rate_recomputed")
    species_base = loo_species_identity_baseline(pooled, "harvest_rate_recomputed")
    m_mae = mae(cv["y_true"], cv["y_pred"])
    naive_mae = mae(naive_base["y_true"], naive_base["y_pred"])
    species_mae = mae(species_base["y_true"], species_base["y_pred"])
    res_pooled = CandidateResult(
        candidate="Pooled cross-species: |lake real mean water temp - species preferred temp|",
        outcome="pooled (7 species x 6 lakes)", n=len(pooled), units="species-lake rows (6 independent lake-seasons)",
        pearson_r=float("nan"), pearson_p=float("nan"),
        loo_model_mae=m_mae, loo_baseline_mae=naive_mae, beats_baseline=m_mae < naive_mae,
        note="disclosed pseudo-replication: only 6 independent water-temperature contexts "
        "underlie these rows, same discipline as v0_inland_pooled_predictability.py",
    )
    results.append(res_pooled)
    print(f"  {res_pooled.candidate}\n    n={res_pooled.n} {res_pooled.units}\n"
          f"    LOO_MAE model={m_mae:.4f} vs naive-mean baseline={naive_mae:.4f} "
          f"[{'BEATS' if m_mae < naive_mae else 'does not beat'}]\n"
          f"    LOO_MAE model={m_mae:.4f} vs species-identity baseline={species_mae:.4f} "
          f"[{'BEATS' if m_mae < species_mae else 'does not beat'}]")
    res_species_cmp = CandidateResult(
        candidate="Pooled cross-species vs species-identity baseline",
        outcome="pooled (7 species x 6 lakes)", n=len(pooled), units="species-lake rows",
        pearson_r=float("nan"), pearson_p=float("nan"),
        loo_model_mae=m_mae, loo_baseline_mae=species_mae, beats_baseline=m_mae < species_mae,
        note="species identity alone is known to explain real harvest-rate variance "
        "(panfish vs. gamefish); the physiology model must beat this, not just a flat mean",
    )
    results.append(res_species_cmp)

    print("\n--- 2c. Bluegill (candidate #11): raw in-window mean water temp vs harvest rate "
          "(no numeric OPTIMUM in the research doc for this species, only a ~22C spawning-"
          "activity THRESHOLD -- tested as a monotonic, not distance-from-band, hypothesis) ---")
    bg = all_species[all_species["species"] == "Bluegill"].copy()
    bg = bg[bg["harvest_rate_recomputed"].notna() & (bg["total_harvest"].fillna(0) > 0)]
    n = bg["lake_name"].nunique()
    if n >= 4:
        r, p = stats.pearsonr(bg["water_temp_c"].values, bg["harvest_rate_recomputed"].values)
        cv = loo_cv_by_lake(bg, "water_temp_c", "harvest_rate_recomputed")
        base = loo_lake_mean_baseline(bg, "harvest_rate_recomputed")
        m_mae = mae(cv["y_true"], cv["y_pred"])
        b_mae = mae(base["y_true"], base["y_pred"])
        res_bg = CandidateResult(
            candidate="Bluegill: raw lake real mean water temp (monotonic hypothesis, ~22C spawn-activity threshold)",
            outcome="Bluegill", n=n, units="lake-seasons",
            pearson_r=r, pearson_p=p, loo_model_mae=m_mae, loo_baseline_mae=b_mae,
            beats_baseline=m_mae < b_mae,
            note="research doc candidate #11 -- extension-tier evidence for the specific threshold, per research doc",
        )
    else:
        res_bg = CandidateResult(
            candidate="Bluegill: raw lake real mean water temp", outcome="Bluegill", n=n,
            units="lake-seasons", pearson_r=float("nan"), pearson_p=float("nan"),
            loo_model_mae=float("nan"), loo_baseline_mae=float("nan"), beats_baseline=False,
            note="too few lakes with data (<4)",
        )
    results.append(res_bg)
    _print_result(res_bg)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    results: list[CandidateResult] = []
    run_lake_michigan(results)
    run_inland(results)

    out_csv = os.path.join(os.path.dirname(__file__), "v0_physiology_predictors_eval_results.csv")
    pd.DataFrame([r.__dict__ for r in results]).to_csv(out_csv, index=False)
    print(f"\nFull results table written to: {out_csv}")

    print("\nCandidate #1 (walleye diel/light-window feeding) -- NOT ATTEMPTED, per research doc: "
          "no trip-level timestamp exists anywhere in the creel outcome data.")
    print("Candidate #16 (Hasnain, Minns & Shuter 2010, Ontario MNR CCRR-17) -- could NOT be "
          "retrieved in this step either (search-located ontario.ca URLs returned unrelated "
          "CCRR-21/CCRR-22 reports); GLFC Sp87-3 was retrieved successfully and used instead.")
    print("Candidate #17 (barometric pressure) -- excluded per the research doc, not carried forward.")


if __name__ == "__main__":
    main()
