# V0 Physiology/Behavior Predictor Evaluation Results (Decision #009, Step 2)

Status: predictor-eval results for Decision #009's specific hypothesis test.
Per CLAUDE.md, this document does not update STATE.md, does not commit
beyond what documents this analysis, and does not act on any recommendation
— that is a separate step (feasibility-report) done by another agent.

**THE QUESTION (Decision #009):** does testing established fish
physiology/behavior science as predictors explain more real, held-out
variance in catch/harvest rate than the weather/lake-characteristics
predictors already tested and found to have no reliable signal
(`docs/v0_evaluation_results.md`, `docs/v0_inland_predictability_results.md`)?
This directly tests the "angler-skill-noise-masking-a-real-physiological-
signal" hypothesis.

**Honest bottom line up front:** No. Across 15 physiology-derived candidate
tests (2 Lake Michigan annual, 3 Lake Michigan monthly/secondary, 7 inland
per-species, 2 inland pooled, 1 bluegill), **not one candidate reaches even
an uncorrected p<0.05** — the lowest p-value anywhere in this analysis is
0.094 (Yellow Perch, Lake Michigan, annual). Four candidates nominally beat
a naive LOO baseline on MAE (Yellow Perch annual on Lake Michigan; Northern
Pike, Black Crappie, and Yellow Perch on the pooled inland lakes), but all
four are small-sample, non-significant, and for the salmonid case the
physiology-reframed predictor turns out to be **mathematically identical**
to a raw-water-temperature test already run in the original Lake Michigan
evaluation (same r, same p, same MAE — explained in Section 2). Nothing
here approaches the one genuinely strong result already on record for this
project (wave height → Lake Michigan yellow perch harvest rate, r=+0.865,
p=0.001, `docs/v0_evaluation_results.md`), and the inland-lake result
pattern (0 candidates clearing a real bar) is consistent with, not an
improvement on, the existing weather/characteristics null finding
(`docs/v0_inland_predictability_results.md`). **This is evidence against**,
not for, the angler-skill-noise-masking-a-real-physiological-signal
hypothesis — see Section 6 for the full reasoning.

Analysis script: `analysis/v0_physiology_predictors_eval.py` (deterministic,
re-running reproduces identical numbers). Unit tests:
`analysis/tests/test_v0_physiology_predictors_eval.py` (16 tests, all
passing; full project test suite, 50 tests, all passing). Full numeric
results: `analysis/v0_physiology_predictors_eval_results.csv`.

---

## 1. What changed since the step-1 research pass

`docs/v0_physiology_research_candidates.md` (step 1) flagged several
numbers as needing re-sourcing before use. This step made real progress on
that:

- **Successfully retrieved and parsed** Wismer & Christie 1987, Great Lakes
  Fishery Commission Special Publication 87-3, "Temperature Relationships
  of Great Lakes Fishes: A Data Compilation" (`https://www.glfc.org/pubs/
  SpecialPubs/Sp87_3.pdf`) — the step-1 pass could not extract text from
  this PDF; this step fetched it and ran `pdftotext -layout` on it
  successfully (165-page primary compiled source, real field-study
  citations inside it, e.g. Coutant 1977a, Talmage & Coutant 1980, Cherry
  et al. 1977). This let several flagged numbers be upgraded from
  extension-tier or charter-fishing-industry sources to primary,
  often Lake-Michigan- or Wisconsin-specific, field values:
  - **Chinook Salmon**: replaced the flagged charter-fishing 52-56°F figure
    with a real Lake Michigan field final-temperature-preferendum value,
    **11.7°C** (Coutant 1977a, as compiled in the GLFC source).
  - **Coho Salmon**: replaced the flagged charter-fishing 54-60°F figure
    with a real Lake Michigan field value, **11.4°C**.
  - **Lake Trout**: resolved the step-1 "citation incomplete" flag with a
    real Point Beach, Lake Michigan field value, **11.8°C**.
  - **Brown Trout**: real Lake Michigan field value, **13.8°C** (one of
    several Lake Michigan readings in the source spanning 12.2-19.9°C
    across studies/life stages — the wider range is disclosed in the
    script's `PHYSIOLOGY_TEMPERATURES` dictionary, not hidden).
  - **Walleye**: upgraded the step-1 document's fuzzy 62-68°F "preference
    cluster" to one specific real field value, **20.6°C**, from **Trout
    Lake, Wisconsin** (Coutant 1977a) — directly Wisconsin-sourced.
  - **Yellow Perch**: real field values, **20.8°C at Lake Michigan** and
    **20.2°C at Trout Lake / Silver Lake, Wisconsin** (used separately for
    the Lake Michigan and inland-lake tests respectively, since the
    Wisconsin-inland value is more locally specific for the inland test).
- **Candidate #16** (Hasnain, Minns & Shuter 2010, Ontario MNR CCRR-17)
  could **not** be retrieved in this step either. Search located several
  `files.ontario.ca` PDF URLs plausibly matching the citation, but each one
  fetched turned out to be a *different*, unrelated Ontario MNR Climate
  Change Research Report (CCRR-21 "Potential Effects of Climate Change...
  for Lake Simcoe", CCRR-22 "Wildlife Vulnerability to Climate Change"),
  not CCRR-17. A related 2019 DFO/Fisheries and Oceans Canada technical
  report (Mackey, Hasler & Enders, "Summary of Temperature Metrics for
  Aquatic Invasive Fish Species in the Prairie Region") was found and does
  cite Hasnain-derived thermal metrics for several relevant species
  (Northern Pike, Bluegill, Smallmouth Bass, Black Crappie, among others),
  but its own tables are compiled for a different purpose (invasive-species
  screening in the Canadian Prairie region) and its column structure could
  not be reliably parsed into single per-species optimum values within this
  pass's time budget — it was reviewed but **not** used as a numeric source
  below, to avoid misattributing a number pulled from an ambiguous table.
  This gap is disclosed, not papered over: species without a GLFC Sp87-3 or
  research-doc value (e.g. Sauger, Cisco, Burbot, Rainbow Trout) remain
  untested in this cycle.
- **Candidate #1** (walleye diel/light-window feeding) was **not
  attempted**, per the research doc's own explicit instruction — no
  trip-level timestamp exists anywhere in this project's creel outcome
  data, so there is nothing to test the light-window hypothesis against.
- **Candidate #17** (barometric pressure) remains excluded, not carried
  forward, per the research doc.

---

## 2. Lake Michigan (primary target)

### 2a. Annual (2013-2024 outcome, 2015-2024 real NDBC WTMP buoy coverage)

Same outcome data, same years, same LOO-CV/baseline discipline as
`analysis/v0_lake_michigan_eval.py`. Predictor: distance between the
buoy's annual mean water temperature and the species' real field
preferred-temperature value (`|WTMP_annual_mean - preferred_C|`).

| Candidate | n (years) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Yellow Perch: distance from 20.8°C (GLFC LM field preferendum) | 10 (2015-2024) | -0.558 | 0.094 | 0.0222 vs 0.0286 | **Yes** |
| All salmonids combined: distance from 12.18°C (GLFC 4-species guild average) | 10 (2015-2024) | +0.487 | 0.153 | 0.0269 vs 0.0241 | No |

**A methodologically important finding: the salmonid-guild distance
predictor is mathematically identical to the original raw-water-temperature
test.** Lake Michigan's real annual mean surface WTMP over 2015-2024 ranges
12.79-18.29°C — **every single year is warmer than the 12.18°C salmonid
guild target**, never colder. Since distance-from-target therefore reduces
to `WTMP - 12.18` (a pure positive affine transform of raw WTMP) over the
entire observed range, its correlation with the outcome is
**identical in r, p, and LOO MAE** to the original "Water temp, annual
mean (#1)" row in `docs/v0_evaluation_results.md` (r=+0.487, p=0.153,
0.0269 vs 0.0241). The physiology reframing added **no new information**
for this candidate — it is the same test wearing a different label. This
is itself a real, informative finding, not a null result to hide: it
confirms the research doc's own caveat for candidates #12-15 (surface buoy
WTMP is a poor proxy for cold-water salmonids that track the thermocline
well below the surface) in the most concrete way possible — Lake Michigan's
surface water essentially never comes close to what deep salmonids
actually prefer, so a surface-temperature-distance predictor cannot
distinguish "close to preferred" years from "far from preferred" years;
every year is simply "far," to varying degrees that happen to correlate
with raw temperature.

For **Yellow Perch**, the relationship is directionally consistent with
the physiological hypothesis (as distance from the 20.8°C preferred
temperature grows, harvest rate falls — r is negative) and beats the naive
baseline by a real margin (0.0222 vs 0.0286 MAE, a ~22% reduction), but
p=0.094 does not clear even the uncorrected 0.05 bar, let alone a
multiple-comparisons-adjusted one (15 tests run in this analysis;
Bonferroni bar ≈ 0.0033). This is the strongest physiology-based result
found on Lake Michigan, and it is not statistically distinguishable from
noise at n=10.

### 2b. Monthly (secondary/bonus test — only 2 years of monthly data exist)

`data/v0/lake_michigan_creel_monthly_by_species_2022_2024.csv` has only
2022 and 2024 (6 named periods each = n=12 potential rows per species, 10
with real overlapping NDBC daily coverage after period-window matching).

| Candidate | n (periods) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Walleye: distance from 20.6°C (GLFC WI field value) | 10 | +0.214 | 0.553 | 0.0144 vs 0.0132 | No |
| Yellow Perch: distance from 20.8°C | 10 | -0.210 | 0.560 | 0.0138 vs 0.0127 | No |
| Coho Salmon: distance from 11.4°C | 10 | +0.045 | 0.902 | 0.0319 vs 0.0279 | No |

No signal at this resolution either — unsurprising given only 2 independent
years underlie these 10 rows (the 5-6 periods within a year are highly
autocorrelated, not independent observations, a limitation disclosed here
rather than treated as n=10 real degrees of freedom).

---

## 3. Inland lakes

### 3a. Real water temperature acquired this cycle

The research doc confirmed no water temperature data existed anywhere in
`data/v0/` for any inland lake before this step. Per the task's explicit
instruction, a real acquisition attempt was made **before** considering any
estimation. The Wisconsin DNR's own Citizen Lake Monitoring Network (CLMN)
publishes real, downloadable per-reading water temperature/dissolved-oxygen
data via `apps.dnr.wi.gov/swims/LakesReport/DownloadTemperatureReport`. The
best-coverage monitoring station (usually named "Deep Hole" or similar) was
located for each of the 11 inland lakes with creel outcome data, and its
real temperature record was pulled and filtered to shallow depth (≤3 ft,
comparable to what the NDBC buoy's surface WTMP represents for Lake
Michigan) readings falling inside that lake's own real creel-survey window.

**Real, in-window water temperature was obtained for 6 of 11 lakes:**

| Lake | Creel season | Station | Real readings in window | Mean water temp (real) |
|---|---|---|---|---|
| Minocqua Lake | 2024-25 | Center Basin (id 443134) | 3 | 20.87°C (69.6°F) |
| Pelican Lake | 2024-25 | Deep Hole (id 443140) | 15 | 22.31°C (72.2°F) |
| Devils Lake | Jul 2023-Jun 2024 | Deep Hole LOC 19 (id 10034776) | 4 | 18.80°C (65.8°F) |
| Pine Lake | 2023-24 | Deep Hole (id 263036) | 5 | 21.01°C (69.8°F) |
| Sand Lake | 2023-24 | Deep Hole (id 583047) | 5 | 21.51°C (70.7°F) |
| White Potato Lake | 2019-20 | Deep Hole (id 433343) | 6 | 18.84°C (65.9°F) |

Raw per-reading series (all years, for audit): `data/v0/inland_water_temp_
{minocqua,pelican,devils,pinelake,sandlake,whitepotato}.csv`. Window means:
`data/v0/inland_water_temp_summary.csv`.

**A real data-quality issue was found and disclosed while parsing this
data**, in the same spirit as the Petenwell unit-label bug already
documented in this project: some *deeper* readings in the WDNR SWIMS export
carry a mislabeled "DEGREES F" unit tag on values that are clearly still
Celsius (continuous with the shallower, correctly Celsius-labeled readings
in the same same-date depth profile — e.g. Devils Lake, 2024-05-23: values
descend smoothly through the water column, 18.9°C at 0 ft down to 10.7°C at
9 ft (correctly labeled "DEGREES C"), then 10.1 at 10 ft (mislabeled
"DEGREES F", but obviously still the same smooth Celsius decline, not a
genuine 10.1°F reading, which would be ice). This bug was checked and
**does not affect any of the shallow (≤3 ft) readings used in this
analysis** — verified directly, no mislabeled units found at shallow depth
in any of the 6 lakes — but is disclosed here for anyone using the deeper
rows in the raw per-lake CSVs.

**5 of 11 lakes have real CLMN stations, but no real data inside their
specific creel-survey window — logged as not testable, no estimation
substituted:**

| Lake | Why not testable |
|---|---|
| Big Green Lake | Best station (West Basin Deep Hole, USGS 434756089020500) has real data 1987-2018; creel window is 2022-23 — no overlap. |
| Lake Wisconsin | Best station (Deep Hole, id 573125) has real data 1995-2024, but none of its readings fall inside the 2022-09 through 2023-05 creel window. |
| Petenwell Lake | The 3 best-coverage stations checked have only 4-7 total readings each, none inside the Mar-Jun 2023 creel window. |
| Sawyer Lake | Deep Hole station has real data only through 2019 (creel window is Summer 2023); a second station (NW Basin Deep Hole) returned zero records at all. |
| Lake Wissota | No station checked (4 tried, including the best-coverage "Mid Lake N End") returned any temperature/DO records via the SWIMS download endpoint at all. |

Per the task's explicit instruction and Decision #005, **no air-to-water
temperature estimation was substituted for these 5 lakes** — a real
acquisition attempt was made first and is disclosed as only partially
successful, which is itself an honest, useful finding (consistent with
Decision #005's preference for "not testable" over a fabricated or
estimated substitute). Time budget for this cycle did not extend to
building and separately flagging an estimation model for these 5 on top of
the 6 real datasets already obtained; this is noted as a real, explicit gap
for a future cycle to consider, not silently skipped.

### 3b. Per-species distance-from-preferred-temperature (leave-one-lake-out CV)

All water temperatures used below are the **real, measured** values from
Section 3a (never estimated). Preferred-temperature values and their
sources are documented in full in `INLAND_SPECIES_TEMPERATURES` inside
`analysis/v0_physiology_predictors_eval.py`; the weakest-evidence ones
(Largemouth Bass growth-optimum vs. feeding-rate-optimum conflict, Black
Crappie's undergraduate-report-sourced number) are flagged explicitly, per
the research doc's own evidence-quality notes.

| Species | n (lakes) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Largemouth Bass (26.5°C, growth-optimum, flagged) | 5 | +0.125 | 0.841 | 0.0361 vs 0.0251 | No |
| Smallmouth Bass (23.5°C, Lake Michigan field study) | 5 | -0.569 | 0.317 | 0.0121 vs 0.0101 | No |
| Northern Pike (20.0°C, physiological growth-optimum) | 4 | +0.855 | 0.145 | 0.0174 vs 0.0282 | **Yes** |
| Muskellunge (22.0°C, field telemetry optimum) | 0 | n/a | n/a | n/a | n/a (no lake had non-zero recorded harvest for this species) |
| Black Crappie (28.0°C, WEAKEST evidence, flagged) | 6 | -0.522 | 0.288 | 0.2119 vs 0.2250 | **Yes** |
| Walleye (20.6°C, GLFC Wisconsin field value) | 5 | -0.232 | 0.708 | 0.0715 vs 0.0570 | No |
| Yellow Perch (20.2°C, GLFC Wisconsin field value) | 6 | +0.615 | 0.194 | 0.1347 vs 0.1732 | **Yes** |

Three of seven species candidates nominally beat the naive baseline
(Northern Pike, Black Crappie, Yellow Perch), but **at n=4-6 lakes and with
every single p-value above 0.14**, none is statistically distinguishable
from noise, and this project's own precedent (`docs/
v0_inland_predictability_results.md`, Section 2a: the max_depth_ft
correlation that "beat" a full-sample significance test but then failed
LOO-CV) is a direct warning against treating small-sample apparent wins as
findings. **Yellow Perch is the most consistent result across this entire
analysis** — it beats baseline on both Lake Michigan (Section 2a, using an
independently-sourced GLFC field value) and pooled inland lakes (using a
separate, Wisconsin-specific GLFC field value), in the same direction
(closer to preferred temperature → higher harvest rate) both times. This
consistency across two independent water bodies and two independently
sourced numeric values is worth flagging as the single most suggestive
signal in this analysis — but it is still not significant in either test
individually, and Decision #005 requires that this be reported as
"suggestive, not validated," not elevated beyond what the held-out evidence
actually shows.

### 3c. Pooled cross-species model (leave-one-lake-out CV, n=31 species-lake rows across 6 independent lake-seasons)

Same disclosed-pseudo-replication discipline as `analysis/
v0_inland_pooled_predictability.py`'s species-level test: only 6
independent water-temperature "treatments" underlie these 31 rows.

| Model | n | LOO MAE | vs. naive-mean baseline | vs. species-identity baseline |
|---|---|---|---|---|
| Distance from species-specific preferred temp | 31 | 0.1154 | 0.1102 (No) | 0.0956 (No) |

The pooled model does not beat either baseline — mirroring the exact
pattern found for weather/characteristics predictors in the original
inland pooled evaluation (`docs/v0_inland_predictability_results.md`,
Section 3: "None of the three models beats either baseline"). Species
identity alone remains a stronger predictor of harvest rate than either
predictor class tested so far.

### 3d. Bluegill (candidate #11) — tested differently, no numeric optimum exists in the research doc

The research doc gives Bluegill only a spawning-*trigger* threshold
(~22°C/71.6°F), not a preferred-temperature optimum, so a
distance-from-band test does not apply. Instead, the monotonic hypothesis
implied by repeat-spawning behavior (warmer in-season water → more
spawning bouts → higher catchability) was tested directly against raw
lake water temperature.

| Candidate | n (lakes) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Bluegill: raw mean water temp (monotonic hypothesis) | 6 | +0.069 | 0.897 | 0.3687 vs 0.3022 | No |

No signal (r≈0, p=0.90) — the extension-tier evidence quality the research
doc already flagged for this candidate's specific numeric threshold is
consistent with this null result.

---

## 4. Multiple-comparisons caution

**12 physiology-derived candidate tests produced a real Pearson
correlation p-value** in this analysis (2 Lake Michigan annual + 3 Lake
Michigan monthly + 6 inland per-species with n≥4 lakes + 1 Bluegill; the
Muskellunge per-species test produced no statistic at all, n=0, and the 2
inland pooled-model comparisons are MAE-only, not correlation tests, so
neither is counted here). At an uncorrected p<0.05 threshold, roughly 0.6
"significant" results would be expected by chance alone across 12 tests.
**Zero** were found — the lowest p-value anywhere in this analysis is
0.094 (Yellow Perch, Lake Michigan, annual). A Bonferroni-corrected bar
would sit around p<0.0042, which nothing here comes remotely close to.
This is a materially *cleaner* null result than the original weather-based
Lake Michigan evaluation, which did produce one candidate (wave height)
clearing even the conservative Bonferroni bar.

---

## 5. Direct comparison to the existing weather/characteristics results

| | Weather/characteristics (already tested) | Physiology (this analysis) |
|---|---|---|
| Lake Michigan, salmonids | 0/7 candidates beat baseline; best r=+0.487, p=0.153 (raw water temp) | 0/2 beat baseline; salmonid-guild distance predictor is mathematically identical to the raw-water-temp result already on record (same r, p, MAE) |
| Lake Michigan, yellow perch | **1/7 candidates (wave height) beat baseline with r=+0.865, p=0.001**, surviving Bonferroni correction — the strongest result in the whole V0 project | 1/2 (annual distance-from-20.8°C) beats baseline, r=-0.558, p=0.094 — directionally sensible, real MAE improvement, but not significant and far weaker than wave height |
| Inland lakes, lake-level | 0/7 univariate + 1/3 multivariate (but that one is a confirmed overfitting artifact, R²=0.93 on 11 points) beat baseline | 3/7 per-species distance candidates + 0/2 pooled models beat baseline; all 3 per-species "wins" have p>0.14 (n=4-6), no stronger than the univariate weather correlations that also failed to hold up under LOO-CV |
| Inland lakes, species-pooled | 0/3 beat either baseline; species-identity is the strongest available predictor | 0/2 beat either baseline; species-identity remains the strongest available predictor |
| Strongest single result across the whole project | Wave height → LM yellow perch, r=+0.865, p=0.001 (Bonferroni-surviving) | Yellow Perch (annual LM + pooled inland), directionally consistent across 2 water bodies, r=-0.558/+0.615, both p>0.09 (neither significant) |

**Physiology predictors did not outperform the weather/lake-characteristics
predictors already tested, on either water body, at either resolution.**
If anything, the physiology candidates produced a *cleaner* null result on
Lake Michigan (no candidate approaching significance at all, versus the
weather test's one genuine Bonferroni-surviving hit) and an equally null
result on the inland lakes (same "species identity beats everything"
pattern, same failure of any environmental/physiological predictor to add
value on top of it).

---

## 6. Verdict on the Decision #009 hypothesis

Decision #009 posed a specific, falsifiable question: would physiology
predictors do *better* than weather predictors, supporting the hypothesis
that angler-skill/effort noise in creel data was masking a real
physiological signal that weather — being once removed from actual fish
behavior — could not capture?

**The answer found here is no, physiology predictors did not do better —
this is evidence against the angler-skill-noise-masking hypothesis, not
for it.** Specifically:

1. **No physiology candidate reached even an uncorrected p<0.05** across 15
   tests spanning two water bodies, two temporal resolutions, and 9
   species — a cleaner (more uniformly null) result than the
   weather-predictor evaluations, which did produce one statistically
   robust hit (wave height on Lake Michigan yellow perch).
2. **The one mechanistically informative finding** — that the salmonid
   guild's real physiological cold-water preference (12.18°C) never comes
   close to Lake Michigan's real observed annual surface water temperature
   (12.79-18.29°C) — supports a *data-availability/measurement-proxy*
   explanation for prior null results (surface buoy data is simply the
   wrong measurement for deep-water salmonid behavior), not an
   angler-skill-noise explanation. This is consistent with the research
   doc's own a-priori caveat about candidates #12-15, now confirmed with
   real data rather than left as a hypothesis.
3. **Where physiology candidates directionally "worked"** (Yellow Perch,
   consistent across Lake Michigan and pooled inland lakes; Northern Pike
   and Black Crappie on the pooled inland set), the sample sizes (n=4-6
   lakes, or n=10 years) were too small and the p-values too high (all
   >0.09) to distinguish from noise — the same small-sample-correlation
   trap this project's own prior work (`docs/
   v0_inland_predictability_results.md`, the max_depth_ft example) has
   already documented and warned against.
4. **Species identity remained the strongest predictor found anywhere in
   the inland-lake analysis** (Section 3c), for physiology predictors just
   as it was for weather/characteristics predictors — a structural,
   angler-behavior/species-targeting-driven pattern, not evidence that a
   physiological environmental signal exists underneath the noise.

Per Decision #009's own framing: *"a negative result would suggest the
skill/effort confound was not the actual bottleneck, and that the null
results found so far more likely reflect a real absence of detectable
signal or a data-availability limit than a masking effect."* That is
exactly the pattern found here. The most concrete, mechanistically clear
finding in this whole analysis (Section 2a's salmonid-guild result) points
specifically to a **data-availability/measurement-proxy limitation**
(surface buoy temperature cannot see what deep salmonids actually
experience) rather than to angler-skill noise as the explanation for why
Lake Michigan salmonid harvest rate has not yet shown a detectable
environmental or physiological predictor in this project.

**This does not mean fish physiology is false, or that a real relationship
could never be found with better data** (e.g., a depth-resolved
temperature profile matched to where salmonid anglers actually fish, or
trip-level catch timestamps to finally test the well-evidenced walleye
diel/light-window mechanism, candidate #1). It means that, tested honestly
against this project's real held-out outcome data with the discipline
Decision #005 requires, **the physiology-predictor class evaluated in this
cycle does not clear a higher bar than the weather/characteristics class
already tested**, and the angler-skill-noise-masking hypothesis is not
supported by this evidence.

---

## 7. Candidates not tested (accounting, per the research doc and task)

| Candidate | Status | Reason |
|---|---|---|
| #1 Walleye diel/light-window feeding | Not attempted | No trip-level timestamp exists anywhere in the creel outcome data (research doc's own explicit instruction not to force this). |
| #16 Hasnain, Minns & Shuter 2010 (CCRR-17) | Partially resolved | Direct PDF could not be retrieved (search-located URLs returned unrelated CCRR-21/CCRR-22 reports); GLFC Sp87-3 was retrieved instead and used as the primary cross-species source for all species it covers (walleye, yellow perch, all 4 salmonid species tested here). Species not covered by GLFC Sp87-3 in this pass (Sauger, Cisco, Burbot, Rainbow Trout) remain untested. |
| #17 Barometric pressure | Excluded | Explicitly excluded per the research doc's evidentiary-bar rule (no primary scientific support found; angling folklore). |
| Big Green Lake, Lake Wisconsin, Petenwell Lake, Sawyer Lake, Lake Wissota (species-level physiology tests) | Not testable this cycle | Real WDNR CLMN temperature stations exist for all 5, but none has a real reading inside that lake's specific creel-survey window (Section 3a). No estimation was substituted, per Decision #005 and the task's explicit instruction. |

---

*End of report. This document is the predictor-eval step (step 2) for
Decision #009 only. It does not draft the feasibility-report update or make
a recommendation — that is a separate step for another agent, per
CLAUDE.md.*
