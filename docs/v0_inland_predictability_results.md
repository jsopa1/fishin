# V0 Inland-Lake Pooled Predictability Report

Status: **Draft for CEO review.** Per CLAUDE.md, this document stops at the
review point — no STATE.md update, no commit beyond what documents this
analysis, and no action on any recommendation has been taken.

THE QUESTION, posed directly by the CEO: *"I would like to see if the data
you found with the inland lakes is predictable to fishing outcomes."* This
is deliberately a different, more direct question than Decision #008's
pairwise lake-to-lake transposition test (`docs/v0_transposition_results.md`,
which found no validated transfer pair). Here, nothing is transferred from
one lake to another one at a time — every real weather and lake-physical
data point gathered across all 11 inland lakes with real WDNR creel outcome
data is pooled into one dataset, and the test is: does that pooled data,
evaluated with a real held-out split, predict harvest rate at all?

Analysis script: `analysis/v0_inland_pooled_predictability.py`. Unit tests:
`analysis/tests/test_v0_inland_pooled_predictability.py` (9 tests, all
passing). Full numeric results: `analysis/v0_inland_pooled_predictability_results.csv`,
`analysis/v0_inland_pooled_predictability_lake_level_dataset.csv`,
`analysis/v0_inland_pooled_predictability_season_pairs.csv`. New weather
data retrieved this cycle (2026-09-08) for the 5 lakes that previously had
none: `data/v0/weather_biggreenlake_*.csv`, `weather_devilslake_*.csv`,
`weather_lakewissota_*.csv`, `weather_sawyerlake_*.csv`,
`weather_whitepotatolake_*.csv`.

**Honest bottom line up front: no, this data does not predict inland-lake
fishing outcomes at a real, held-out-defensible level, at either resolution
tested.** Of 10 lake-level models and 3 species-level models (16 held-out
comparisons total against one or more baselines), exactly one nominally beat
its baseline — a 5-predictor model fit on only 11 points, which shows the
textbook signature of overfitting (full-sample R²=0.93 with only 5 residual
degrees of freedom) rather than a real relationship, and was flagged as
statistically indefensible *before* it was run. Every other comparison,
including the one nominally "significant" univariate correlation
(max_depth_ft, r=+0.708, p=0.015, uncorrected), failed to beat even a naive
mean baseline once held out honestly. This result is consistent with, and
reinforces, Decision #008's transposition-test finding — this cycle asked
the more direct version of the same question and got the same answer.

---

## 1. What was tested

### 1a. Lake-level pooled model (primary test, n=11)

One row per inland lake — the most recent surveyed creel season for each of
the 11 lakes found in the Decision #008 inventory cycle. This is the
cleanest possible test of the CEO's question: every lake contributes exactly
one independent observation (no pseudo-replication), and no predictor shares
a denominator with the outcome (unlike Decision #008's effort-share
predictor, which is not used anywhere in this analysis).

- **Outcome**: an effort-weighted, lake-wide harvest rate — `sum(total_harvest
  across all species) / sum(directed_effort_hours across all species)` for
  that lake-season, computed directly from raw creel counts (not any
  pre-existing rate column, same discipline the transposition script used to
  sidestep Petenwell's unit-label bug).
- **Predictors**: real NOAA NCEI weather aggregated to the exact creel-survey
  window (mean TMAX °C, mean TMIN °C, total PRCP mm), and real lake physical
  characteristics from `data/v0/lake_characteristics.csv` (surface area,
  max depth; mean depth and trophic status tested separately on a smaller
  complete-case subset since several lakes are missing them).
- **Evaluation**: leave-one-**lake**-out cross-validation (LOO-CV) — for each
  held-out lake, a linear model is fit on the other 10 lakes only, then used
  to predict the held-out lake. Compared against a leave-one-lake-out naive
  mean baseline (predict the mean outcome of the other 10 lakes).

### 1b. Species-level pooled model (secondary test, n=118)

Every species row from every lake-season used above, pooled — 118 rows after
the same zero-effort/missing-share filtering the transposition script uses
(not the ~130 initially estimated from raw row counts, since Sand Lake,
Big Green Lake, and others have a few zero-directed-effort species rows
dropped for the same reason documented in the transposition report).

- **Outcome**: `harvest_rate_fish_per_hour`, recomputed directly per species
  as `total_harvest / directed_effort_hours`.
- **Predictors**: the *same* lake-season weather and characteristics values
  as 1a, broadcast to every species row within that lake-season. **This is
  disclosed pseudo-replication, not hidden**: the predictors only vary
  across 11 independent lake-season "treatments", not across all 118 rows,
  even though the outcome varies row by row. This resolution exists to see
  whether a much larger row count changes the answer, not because the extra
  rows represent independent weather/characteristic observations.
- **Evaluation**: LOO-**lake**-out CV (never leave-one-species-out — a
  lake's rows never leak into their own held-out prediction). Compared
  against two baselines: (a) the naive overall training-mean, and (b) a
  **species-identity baseline** (predict each held-out species row using
  that same species' mean rate from every *other* lake) — since species
  identity alone (panfish vs. gamefish, etc.) is known to explain real
  variance, any model claiming predictive value must beat that too, not
  just a flat mean.

### 1c. Why no random forest

Per Decision #002 ("simplest model that performs well") and the task's own
instruction to check row count before choosing model complexity: **n=11 at
the lake level (10 training rows per LOO fold) and n=118 pseudo-replicated
rows drawn from only 11 independent weather/characteristics contexts are
both far too small for a random forest** to do anything but memorize noise
or degenerate into a handful of near-duplicate trees. Only OLS linear
regression (via `numpy.linalg.lstsq`, no external ML dependency, consistent
with `analysis/v0_lake_michigan_eval.py` and
`analysis/v0_lake_transposition_eval.py`) is used anywhere in this analysis.

### 1d. New weather data pulled this cycle

Weather had not previously been pulled for Big Green Lake, Devils Lake, Lake
Wissota, Sawyer Lake, or White Potato Lake. All five were pulled this cycle
from NOAA NCEI GHCND daily-summaries, using the same method as the original
6 pulls: nearest station with real TMAX/TMIN/PRCP coverage (not just the
nearest station of any kind), restricted to the exact creel-survey window
stated in that lake's own PDF (grepped directly via `pdftotext -layout`, not
estimated).

| Lake-season | Station used | Distance | Survey window (from the PDF's own text) |
|---|---|---|---|
| Big Green Lake 2022-23 | Berlin WWTP, USC00470742 | 12.6 mi | "The open-water creel survey ran from May 7, 2022 through March 31, 2023, and the ice fishing creel survey ran from Dec. 5, 2022 through March 30, 2023" |
| Devils Lake Jul2023-Jun2024 | Baraboo WWTP, USC00470516 | 2.2 mi | "open-water period that ran from July 1, 2023 through Oct. 31, 2023. The ice fishing portion of the creel ran from Jan. 1 through Feb. 28, 2024. A second open-water creel period ran from May 4-June 30, 2024" |
| Lake Wissota 2019-20 | Chippewa Valley Regional Airport, USW00014991 | 11.1 mi | "An open water creel survey was conducted from opening day of gamefish season on May 4, 2019 and ran through the end of October" |
| Sawyer Lake Summer 2023 | Antigo Langlade Co Airport, USW00004864 | 15.7 mi | "2023 fishing season ran from May 6, 2023 through October 31, 2023. There was no winter clerk on Sawyer Lake" |
| White Potato Lake 2019-20 | Suring, USC00478376 | 13.7 mi | "the 2019-2020 fishing season ran from May 4, 2019 through March 1, 2020. The open-water creel survey ran from May 4 through Sept. 30, 2019 and the ice fishing creel survey ran from Jan. 4, 2020 through March 12, 2020" |

Two real data-quality findings surfaced and are disclosed rather than
papered over:

- **Lake Wissota**: the two nearest stations (Chippewa Falls 0.9NW, 5.3 mi,
  and Chippewa Falls, 5.8 mi) turned out, on inspection of the downloaded
  data, to carry `PRCP` only with no `TMAX`/`TMIN` at all. Chippewa Valley
  Regional Airport (11.1 mi) was used instead because it has complete
  TMAX/TMIN/PRCP coverage for the window.
- **Sawyer Lake**: the same problem, worse — the two nearest stations
  (Summit Lake, 6.0 mi, and Argonne, 21.8 mi) are precipitation-only.
  Antigo Langlade Co Airport (15.7 mi) was used instead, and even it has a
  real, disclosed coverage gap: TMAX/TMIN present for only 118 of the 179
  days in the survey window (66%), not the full window. This is the same
  category of gap the original transposition cycle found and disclosed for
  Pine Lake's initial station choice (Mercer Ranger Station).
- **White Potato Lake**: the single nearest station (Mountain 0.9E, 0.9 mi)
  is a CoCoRaHS citizen-network station, precipitation-only. Suring (13.7
  mi) was used instead for full TMAX/TMIN/PRCP coverage.

No station pull failed outright for these five lakes — every one produced
real, usable (if in two cases geographically more distant or partially
gapped) data. Nothing here is fabricated or estimated.

---

## 2. Results — lake-level pooled model (n=11)

### 2a. Univariate models

| Predictor | n | Pearson r | p | LOO-CV MAE | Baseline MAE | Beats baseline? |
|---|---|---|---|---|---|---|
| mean_tmax_c | 11 | +0.295 | 0.378 | 0.0930 | 0.0918 | No |
| mean_tmin_c | 11 | +0.244 | 0.469 | 0.0955 | 0.0918 | No |
| total_prcp_mm | 11 | +0.235 | 0.487 | 0.1081 | 0.0918 | No |
| surface_area_acres | 11 | +0.104 | 0.761 | 0.1115 | 0.0918 | No |
| max_depth_ft | 11 | **+0.708** | **0.015** | 0.0945 | 0.0918 | **No** |
| mean_depth_ft (reduced n) | 7 | +0.704 | 0.077 | 0.1428 | 0.1296 | No |
| trophic_index (reduced n) | 8 | -0.236 | 0.573 | 0.1251 | 0.1154 | No |

**The max_depth_ft row is the most important single result in this table,
and it is a cautionary one, not a positive one.** Its full-sample
correlation (r=+0.708) clears an uncorrected p<0.05 bar — the only predictor
in this entire analysis that does. If this analysis stopped at correlation,
it would look like a real finding. **It is not**: held out honestly with
LOO-CV, its MAE (0.0945) is *worse* than the naive baseline (0.0918). A
handful of large, deep lakes (Big Green Lake, 236 ft; Lake Wissota, 64.4 ft)
happen to also have moderately higher harvest rates in this small sample,
which is enough to produce a nominally significant correlation with only 11
points, but the relationship does not hold up when each lake is genuinely
predicted from the other 10. With 7 univariate tests run here, roughly 0.35
"significant" results would be expected by chance at p<0.05 alone — this is
within that noise band, and a Bonferroni-style correction (0.05/7 ≈ 0.007)
is not cleared either. **No univariate predictor beat its baseline.**

### 2b. Multivariate models

| Model | n | LOO-CV MAE | Baseline MAE | Beats baseline? |
|---|---|---|---|---|
| Weather combined (TMAX, TMIN, PRCP) | 11 | 0.1164 | 0.0918 | No |
| Characteristics combined (area, max depth) | 11 | 0.1140 | 0.0918 | No |
| **Weather + characteristics combined (5 predictors)** | 11 | **0.0484** | 0.0918 | **Yes** |

The 5-predictor combined model is the one result in the entire lake-level
analysis that nominally beats baseline — and it was flagged in the script's
own comments as "NOT statistically defensible at this sample size" *before*
it was run, not after seeing a favorable number. The reason: fitting 5
predictors plus an intercept (6 parameters) leaves only 4-5 residual degrees
of freedom on 10-11 points. Fit on the full 11-point sample (not held out),
this model reaches **R²=0.93** — a textbook overfitting signature, not
evidence of a real relationship. A model with that many free parameters
relative to its sample size can fit almost any smooth pattern in the
training data, including pure coincidence, and inspecting the per-lake
LOO errors confirms this is not one lake being predicted well by chance —
errors are spread fairly evenly across all 11 lakes (0.004 to 0.104), which
is exactly what an overfit model interpolating idiosyncratic small-sample
structure looks like. **This result is not reported as evidence that
weather and lake characteristics jointly predict harvest rate**, per
Decision #005 — it is reported because Decision #005 also requires
disclosing all results actually run, not only the disappointing ones.

### 2c. Lake-type groups (descriptive only)

| Lake type | n | Mean harvest rate | Std dev |
|---|---|---|---|
| Drainage | 5 | 0.246 | 0.136 |
| Impoundment | 3 | 0.198 | 0.054 |
| Seepage | 3 | 0.243 | 0.135 |

Three group means with n=3-5 each and heavily overlapping standard
deviations — not tested formally (a one-way ANOVA or similar at these group
sizes would have essentially no power), reported descriptively only. No
group differs from the others by more than about one standard deviation.

---

## 3. Results — species-level pooled model (n=118)

| Model | n | LOO-CV MAE | vs. naive-mean baseline | vs. species-identity baseline |
|---|---|---|---|---|
| Weather only | 118 | 0.2525 | 0.2403 (No) | 0.1680 (No) |
| Characteristics only (area, max depth) | 118 | 0.2512 | 0.2403 (No) | 0.1680 (No) |
| Weather + characteristics combined | 118 | 0.2641 | 0.2403 (No) | 0.1680 (No) |

None of the three models beats either baseline. The species-identity
baseline (0.168 MAE) is substantially stronger than the naive-mean baseline
(0.240 MAE) — confirming that *which species* an angler targets explains
real variance in harvest rate (an unsurprising, expected finding — panfish
naturally have very different catch dynamics than gamefish), but **weather
and lake characteristics add nothing on top of that, and in fact make
predictions worse than either baseline**, not better. This is the larger-n
version of the same question as Section 2, and it returns the same answer.

---

## 4. Within-lake, two-season descriptive comparison (n=2 per lake)

Five of the 11 lakes have two separate surveyed creel seasons: Minocqua,
Pelican, Pine, Sand (the four named in the task), plus Lake Wissota (also
has two seasons per the Decision #008 inventory, included here for
completeness though not explicitly named in the task).

| Lake | Older season | Older rate | Newer season | Newer rate | % change |
|---|---|---|---|---|---|
| Minocqua Lake | 2009-10 | 0.162 | 2024-25 | 0.305 | **+88.0%** |
| Pelican Lake | 2011-12 | 0.314 | 2024-25 | 0.211 | **-33.0%** |
| Pine Lake | 2017-18 | 0.120 | 2023-24 | 0.075 | **-37.3%** |
| Sand Lake | 2007-08 | 0.090 | 2023-24 | 0.198 | **+120.7%** |
| Lake Wissota | 2006-07 | 0.141 | 2019-20 | 0.226 | **+60.6%** |

**This is explicitly an observation, not a tested hypothesis.** With n=2 per
lake, no correlation, regression, or significance test is meaningful or
performed — the swings above (from -37% to +121%) are simply what the real
data shows, reported as fact.

**Weather-difference correlation was not attempted, and this is a real,
disclosed limitation, not an oversight.** Testing whether the season-over-
season harvest-rate change correlates with a season-over-season weather
change would require real weather data for *both* seasons of each lake.
Weather was pulled only for the more recent season of each of these five
lakes (Section 1d and the original transposition cycle); the older seasons'
source PDFs (2009-10, 2011-12, 2017-18, 2007-08, 2006-07) were not part of
this project's local PDF collection — only the most recent PDF per lake was
retained — and re-locating a 15-20-year-old WDNR report's exact stated
survey window was out of scope for this pass. Estimating an approximate
window without a real source, just to force a weather comparison, would
violate Decision #005. So: five real, wildly inconsistent-in-direction and
inconsistent-in-magnitude season-over-season harvest-rate changes are
reported as pure description, and nothing is claimed about what drove them.

---

## 5. Actual sample sizes and what they do and don't support

- **Lake-level pooled model: n=11** (one independent observation per inland
  lake with real creel outcome data). This is the entire population of
  inland lakes with usable creel data found in the Decision #008 inventory
  cycle — not a sample drawn from a larger pool, the full set. At n=11, a
  LOO-CV fold trains on 10 points; a single-predictor linear model is about
  as much complexity as this can support without overfitting risk becoming
  severe (Section 2b demonstrates exactly how severe that risk is once
  predictor count climbs past 2).
- **Species-level pooled model: n=118** rows, but only **11 independent
  weather/characteristics contexts** underneath them (Section 1b) — this
  resolution has more statistical power to characterize *species-level*
  variation (which is real and captured by the species-identity baseline)
  but no more real independent information about weather/characteristics
  than the lake-level model does.
- **Within-lake comparison: n=2 per lake**, five lakes — pure description,
  explicitly not a statistical test (Section 4).

**None of these sample sizes is large enough to rule out a real
weather/characteristics effect existing but being too small or too noisy to
detect here.** Absence of evidence at n=11 is not evidence of absence in an
absolute sense. But it is enough to say, honestly and per Decision #005,
that **no such effect was found when tested properly**, and that the one
model which nominally "found" something did so by a mechanism (severe
overfitting on 11 points) that is not credible as a real predictive
relationship.

---

## 6. Overall verdict

**No — the weather and lake-physical-characteristics data gathered so far
does not predict inland-lake fishing outcomes, tested honestly with real
held-out evaluation, at either resolution tested (lake-level, n=11;
species-level, n=118 rows / 11 independent contexts).**

- 7 univariate lake-level predictors: 0 of 7 beat baseline. One
  (max_depth_ft) showed a nominally significant full-sample correlation
  (p=0.015) that did not survive held-out testing — the clearest single
  illustration in this report of why correlation alone must never be
  reported as validation (Decision #005).
- 3 multivariate lake-level models: 1 of 3 nominally beat baseline, but by a
  model with textbook overfitting signatures (R²=0.93 on 11 points with 6
  parameters), flagged as statistically indefensible before it was run —
  not credible as a real finding.
- 3 species-level pooled models: 0 of 3 beat either the naive-mean or the
  (stronger) species-identity baseline.
- The within-lake two-season comparison (5 lakes, n=2 each) shows harvest
  rate moved in both directions, by wildly different magnitudes, with no
  weather data available for the older seasons to explore why — reported as
  description only, per Decision #005.

This result is consistent with, not contradicted by, Decision #008's
transposition-test finding (`docs/v0_transposition_results.md`), which
found no validated pairwise transfer relationship using a different
predictor (species-level effort share) and a different test design
(source-lake-only fitting). Both this cycle and that one converge on the
same honest conclusion from two different, complementary angles: **with the
real data gathered so far, no tested version of "does something about
conditions or lake character predict inland-lake harvest rate" has cleared
a real held-out bar.**

**Confidence in this verdict**: moderate-to-high that *no signal exists in
this specific dataset at this specific size* — the negative result is
consistent across two resolutions (11 lakes, 118 species-rows), multiple
predictor sets (weather alone, characteristics alone, combined), and two
different baseline types (naive mean, species-identity). It is NOT a
high-confidence claim that no such relationship could ever be found with
more data — n=11 lake-seasons is a small, complete population, not a large
sample that failed to show an effect despite ample power. As with the
transposition cycle, this is reported as a real, useful, and expected
finding in its own right (Decision #005 requires exactly this framing, not
a workaround to manufacture a positive result), not a failure of this
analysis pass.

---

## 7. Recommendations for CEO consideration

These are options for CEO consideration, not decisions made by this report.

1. **The inland-lake predictability question, tested two different ways
   now (Decision #008's pairwise transposition and this cycle's pooled
   test), has returned a consistent negative result.** Any future work
   claiming inland-lake fishing outcomes are predictable from weather or
   lake characteristics should be held to the same held-out bar used here,
   not a correlation or in-sample fit.
2. **The structural limitation is sample size, not effort.** WDNR's
   periodic (not annual) inland-lake survey cadence caps the lake-level
   pooled dataset at n=11 today — every inland lake with usable creel data
   this project has found is already in this analysis. More inland lakes
   getting third survey seasons over the 2030s (as flagged in the Decision
   #008 report) would be the most direct path to a larger, more decisive
   test.
3. **The two older-season weather gaps (Section 4) could be closed** by
   locating and downloading the original 2009-10 (Minocqua), 2011-12
   (Pelican), 2017-18 (Pine), 2007-08 (Sand), and 2006-07 (Lake Wissota)
   creel PDFs, if a real, sourced statement of their survey windows can be
   found — this would let the within-lake comparison in Section 4 test a
   real weather-difference correlation instead of remaining pure
   description, though even then each lake would still only offer n=2.
4. **Lake Michigan's own V0 result stands untouched by this cycle** — this
   report, like the Decision #008 cycle before it, is scoped entirely to
   the inland lakes and does not revisit `docs/V0_FEASIBILITY_REPORT.md`.

---

*End of report. Per CLAUDE.md's hard-stop instruction, this document stops
at the review gate — no STATE.md update and no further pipeline action has
been taken beyond writing this analysis, its code, its tests, and this
report. Awaiting CEO review.*
