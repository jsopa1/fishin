# V0 Evaluation Results — Steps 3-4 (Baseline + Predictor Evaluation)

Scope: **Lake Michigan (Wisconsin waters), 2013-2024 only.** Per the step-2
dataset manifest (`docs/v0_dataset_manifest.md`), this is the only waterbody
with real, matching outcome (angler harvest rate) and predictor data in V0.
Pewaukee, Delavan, and Geneva have no creel/catch-rate outcome data at all and
are not evaluated here. Lake Winnebago has fisheries-abundance trawl data (a
different metric than angler catch rate) with no matching daily predictor
series pulled, and is likewise not evaluated. No data was fabricated or
estimated to work around these gaps.

Analysis script: `analysis/v0_lake_michigan_eval.py` (deterministic,
re-running reproduces identical numbers). Unit tests for the daily-to-annual
aggregation logic and the LOO/baseline helpers:
`analysis/tests/test_v0_lake_michigan_eval.py` (13 tests, all passing). Full
numeric results table: `analysis/v0_lake_michigan_eval_results.csv`.

## Outcome variable

Annual harvest rate (fish harvested per angler-hour), from
`data/v0/lake_michigan_creel_harvest_rate_annual_by_species.csv`, 2013-2024
(12 annual observations):

- **All salmonids combined** (primary outcome): mean 0.1208, std 0.0307
  fish/angler-hour.
- **Yellow perch (total)** (secondary outcome): mean 0.0622, std 0.0302
  fish/angler-hour.

This is a *harvest* rate (fish kept), not a total-catch-and-release rate — the
best real proxy WDNR publishes, per the manifest.

## Predictor aggregation (daily → annual)

The outcome is annual; the raw predictor sources are daily. All predictors
below were aggregated from daily records up to annual means (or year-over-year
differences) with `aggregate_daily_to_annual()` in the analysis script, unit
tested on synthetic data. Two source-coverage caveats apply and are carried
through to every result below:

- **NDBC buoy 45007** (water temp, wind speed, wave height, pressure) only
  reports during the open-water season (removed each winter), and its record
  starts in 2015 — so these four candidates cover **2015-2024 (10 years)**
  and their "annual mean" is really an **in-season mean**, not a full
  Jan-Dec average.
- **NOAA CO-OPS water level** (Milwaukee, station 9087057) has full daily
  coverage **2013-2024 (12 years)**, matching the outcome's full range.
- **Pressure trend** (year-over-year difference) loses its first year to
  differencing, leaving **2016-2024 (9 years)**.
- **Angler effort** (angler-hours) is available for all **2013-2024 (12
  years)**, since it is already embedded in the outcome CSV as the harvest
  rate's own denominator.

## Baseline (step 3)

Two baselines were defined, both requiring no predictor data — a real
predictive candidate must beat these to be worth anything:

1. **Primary: leave-one-year-out (LOO) historical-mean baseline.** For each
   held-out year, predict the mean of harvest rate across all *other* years
   (never the held-out year's own value). This is evaluated on exactly the
   same held-out years as every candidate model, so baseline-vs-candidate
   comparisons below are apples-to-apples.
2. **Secondary: persistence baseline.** Predict last year's actual value
   (undefined for the first year, which is dropped).

| Outcome | LOO mean-baseline MAE | LOO mean-baseline RMSE | Persistence MAE | Persistence RMSE |
|---|---|---|---|---|
| All salmonids combined | 0.0200 | 0.0320 | 0.0246 | 0.0336 |
| Yellow perch (total) | 0.0266 | 0.0316 | 0.0283 | 0.0372 |

The historical-mean baseline outperforms persistence for both outcomes (year
to year harvest rate is noisy enough that "last year's value" is a worse
guess than "the long-run average"), so the **LOO historical-mean baseline is
used as the bar every candidate must clear** below.

## Candidate evaluation (step 4)

Method: single-variable linear regression (`harvest_rate ~ a + b * predictor`),
evaluated with leave-one-year-out cross-validation — for each held-out year,
the model is fit only on the *other* years, then used to predict the held-out
year (never fit and scored on the same year, never using a future year to
predict a past one). Pearson correlation (r, two-sided p-value) is reported
over the same overlapping years. **No model beyond simple linear regression /
correlation was used** — with 9-12 annual data points, anything requiring a
larger sample (random forest, gradient boosting, multiple regression with
several terms) would overfit and produce meaningless results; this is a hard
methodological limitation of the available data, not a shortcut.

**Multiple-comparisons caution:** 7 candidates × 2 outcomes = 14 statistical
tests were run. At an uncorrected p<0.05 threshold, roughly 0.7 "significant"
results would be expected by chance alone; a conservative Bonferroni
correction would put the real significance bar around p<0.0036. This is kept
in mind when reading every "p<0.05" flag below.

### All salmonids combined (primary outcome)

| Candidate | n (years) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Water temp, annual mean (#1) | 10 (2015-2024) | +0.487 | 0.153 | 0.0269 vs 0.0241 | No |
| Wind speed, annual mean (#5) | 10 (2015-2024) | -0.422 | 0.224 | 0.0250 vs 0.0241 | No |
| Wave height, annual mean (#14) | 10 (2015-2024) | -0.242 | 0.501 | 0.0240 vs 0.0241 | Marginally (essentially a tie) |
| Water level, annual mean (#15) | 12 (2013-2024) | -0.342 | 0.276 | 0.0235 vs 0.0200 | No |
| Pressure, annual mean (#9) | 10 (2015-2024) | +0.003 | 0.994 | 0.0268 vs 0.0241 | No |
| Pressure, year-over-year trend (#10) | 9 (2016-2024) | +0.275 | 0.474 | 0.0331 vs 0.0257 | No |
| Angler effort, hours (#16) | 12 (2013-2024) | -0.162 | 0.614 | 0.0247 vs 0.0200 | No |

**Assessment:** none of the seven candidates shows a statistically
distinguishable relationship with the primary outcome (all p > 0.15, all well
above even the uncorrected 0.05 bar), and six of seven fail to beat the naive
historical-mean baseline on held-out MAE. Wave height's LOO MAE (0.0240) is
essentially tied with the baseline (0.0241) — not a real edge, well within
noise for n=10. For salmonid harvest rate specifically, **no candidate tested
here shows real signal**; the historical average remains the best available
predictor in V0.

### Yellow perch (total) (secondary outcome)

| Candidate | n (years) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Water temp, annual mean (#1) | 10 (2015-2024) | +0.558 | 0.094 | 0.0222 vs 0.0286 | Yes |
| Wind speed, annual mean (#5) | 10 (2015-2024) | +0.500 | 0.141 | 0.0293 vs 0.0286 | No |
| Wave height, annual mean (#14) | 10 (2015-2024) | **+0.865** | **0.001** | **0.0152 vs 0.0286** | **Yes, clearly** |
| Water level, annual mean (#15) | 12 (2013-2024) | +0.192 | 0.550 | 0.0323 vs 0.0266 | No |
| Pressure, annual mean (#9) | 10 (2015-2024) | +0.317 | 0.372 | 0.0298 vs 0.0286 | No |
| Pressure, year-over-year trend (#10) | 9 (2016-2024) | +0.631 | 0.069 | 0.0240 vs 0.0298 | Yes |
| Angler effort, hours (#16) | 12 (2013-2024) | -0.473 | 0.121 | 0.0287 vs 0.0266 | No |

**Assessment, candidate by candidate:**

- **Wave height (#14) is the one genuinely noteworthy result in this
  evaluation.** r=0.865, p=0.001 survives even the conservative
  Bonferroni-corrected threshold (~0.0036), and the LOO-CV model cuts MAE
  from 0.0286 to 0.0152 (a ~47% reduction) versus the naive baseline — a
  real, not marginal, improvement even leaving one year out each time. That
  said: n=10, the relationship is positive (higher mean wave height →
  higher perch harvest rate), which runs counter to the research doc's
  a-priori inferred hypothesis (#14) that *rougher* water would suppress
  catchability/access, not raise it. With only 10 points this could reflect
  a real oceanographic/behavioral mechanism, a shared confound (e.g. both
  wave height and perch harvest rate trending with some other year-level
  factor, such as lake productivity or a specific stormy-but-good-perch-year
  like 2024), or simple small-sample coincidence that happens to be strong.
  This should be treated as a **flagged, worth-investigating-further signal**,
  not a confirmed causal predictor — it was not hypothesized in advance with
  this direction, and 10 data points cannot rule out confounding.
- **Water temperature (#1)** and **pressure trend (#10)** both beat the
  baseline on LOO MAE and have p-values in the 0.07-0.09 range — suggestive,
  but neither clears even the uncorrected p<0.05 bar, let alone a
  multiple-comparisons-adjusted one. Read these as "not distinguishable from
  noise at n=9-10," not as findings.
- Wind speed, water level, and pressure (absolute) show no meaningful
  relationship (p > 0.1, at or worse than baseline on LOO MAE).

### Angler effort (#16) — endogeneity flag

Angler-hours is the denominator of harvest rate by construction
(`harvest_rate = harvest / angler_hours`), so any correlation observed here is
not a clean independent-predictor effect — it can arise mechanically (e.g. if
harvest doesn't scale linearly with effort) even with no real behavioral
relationship. As it happens, effort showed **no significant correlation with
either outcome** (salmonids r=-0.162, p=0.614; perch r=-0.473, p=0.121) and
did not beat baseline for either outcome. Given both the endogeneity concern
and the null result, **effort should not be used as a predictor in this
form** — this is a caution flag confirmed rather than a predictor recommended
for use.

## Overall assessment

- For the **primary outcome (salmonid harvest rate)**, none of the seven
  tested candidates showed real signal. The historical-mean baseline was not
  meaningfully beaten by any candidate. Prediction does not currently beat a
  trivial baseline for Lake Michigan salmonid harvest rate using these
  predictors.
- For the **secondary outcome (yellow perch harvest rate)**, one candidate —
  **annual mean wave height** — shows a statistically strong and
  practically large LOO-CV improvement over baseline, robust to a
  conservative multiple-comparisons correction. Two others (water
  temperature, pressure trend) show weaker, suggestive-but-not-significant
  improvements. These perch results should be read cautiously: n=10-12 years
  is small, three separate "hits" out of fourteen tests is within the range
  multiple comparisons alone would predict for weaker candidates, and the
  wave-height direction was not the one hypothesized in the research phase —
  more years of data (or a held-out future season) would be needed before
  treating this as a validated predictor rather than a lead worth
  investigating further.
- **No candidate should be described as a validated, ready-to-use predictor
  of Lake Michigan catch rate on this evidence.** The one strong result
  (wave height → perch harvest rate) is a real, held-out-validated
  statistical signal worth flagging for the feasibility report and possible
  follow-up with more years of data — not a confirmed causal or
  production-ready finding.
- This evaluation could not be extended to any inland lake (Pewaukee,
  Delavan, Geneva, Winnebago) because no matching outcome variable exists for
  them in V0, per the step-2 manifest; that limitation is inherited here
  unchanged, not re-litigated.
