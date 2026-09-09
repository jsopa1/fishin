# V0 Feasibility Report — Fishing-Condition Prediction

Status: **Draft for CEO approval.** Per CLAUDE.md, this is the final step of the V0
pipeline. No STATE.md update, no commit, and no action on any recommendation
below has been taken — this document stops at the approval gate and awaits
explicit CEO decision.

Prepared from: `docs/v0_research_candidates.md` (step 1), `docs/v0_dataset_manifest.md`
(step 2), `docs/v0_evaluation_results.md` (steps 3-4), read in full. Consistent
with DECISIONS.md #005 ("the system must never represent an arbitrary score as
scientifically validated"), every claim below is scoped exactly to what those
documents' held-out evidence supports — no stronger, no weaker.

---

## 1. Executive summary

**Is fishing-condition prediction feasible from public data, for this V0 scope
(SE Wisconsin inland lakes + WI waters of Lake Michigan)? Honest answer: not
demonstrated — for two different reasons that must not be conflated.**

- For the three named SE Wisconsin inland lakes actually checked for outcome
  data in this pass — **Pewaukee, Delavan, and Geneva** — no creel or
  angler-catch-rate outcome data exists in WDNR's public records at all. There
  was nothing to predict, so feasibility could not be tested one way or the
  other. This is a **data-availability failure**, not evidence that prediction
  is infeasible there.
- For **Lake Michigan (WI waters)**, the only waterbody with real, matching
  outcome and predictor data, seven candidate predictors were evaluated
  against a historical-mean baseline across two outcomes (14 statistical
  tests total). For the primary outcome — **salmonid harvest rate** — none of
  the seven candidates showed a statistically distinguishable relationship,
  and none meaningfully beat the naive baseline. For the secondary outcome —
  **yellow perch harvest rate** — one result stood out (wave height, r=0.865,
  p=0.001, surviving a conservative Bonferroni correction), but it ran counter
  to the a-priori hypothesized direction, rests on only 10 annual data points,
  and is flagged as a lead worth investigating, not a validated finding.

**Bottom line: V0 did not establish that fishing conditions can be predicted
from the public data assembled so far, for either part of the scope.** The
inland-lake question remains genuinely untested. The Lake Michigan question
was tested and came back mostly negative, with one statistically notable but
causally uncertain exception that should not be oversold.

---

## 2. Scope recap

Per DECISIONS.md #007, the V0 pilot geography is:

- **Lake Michigan** (Milwaukee/Racine/Kenosha nearshore waters)
- **Lake Winnebago** (Winnebago County)
- **Pewaukee Lake** (Waukesha County)
- **Delavan Lake** (Walworth County)
- **Geneva Lake** (Walworth County)

Counties in scope: Milwaukee, Waukesha, Racine, Kenosha, Walworth, Winnebago.
Any other water body or region is out of scope for V0 without CEO approval.

---

## 3. Full research candidate list (step 1) — all 19, with final disposition

Step 1 identified 19 candidate predictors and, independently, labeled each
with a confidence rating on the *predictor claim's* evidentiary basis. The
table below adds what actually happened to each candidate across steps 2-4.
Every candidate from the research document appears exactly once below;
none were dropped.

| # | Candidate | Claimed effect (brief) | Step-1 confidence label | Final disposition |
|---|---|---|---|---|
| 1 | Water temperature | Strong — governs metabolism/activity, species-specific optimal ranges | Well-established | **Tested (Lake Michigan).** r=+0.487/salmonids (p=0.153, no), r=+0.558/perch (p=0.094, suggestive but not significant). Inland lakes: no data obtained (USGS confirmed no temperature parameter at the sites found; no USGS site for Pewaukee at all). |
| 2 | Ice-out date | Season-start/phenology signal, correlated with spring catchability | Well-established | **Not tested.** No real SE-WI-specific data source confirmed in step 1 (rigorous records exist only for Madison-area lakes); not pursued in step 2. |
| 3 | Season / spawning window | Strong — catchability spikes during spawning windows | Well-established | **Tested/buildable (Lake Michigan only)**, derivable from existing date fields; moot for inland lakes since no outcome data exists there. |
| 4 | Time of day (crepuscular feeding) | Moderate-strong, dawn/dusk feeding peaks | Well-established (qualitative) | **Not usable in V0.** The Lake Michigan creel data obtained is monthly/annual aggregate, not per-interview, so time-of-day could not be derived from what was extracted. |
| 5 | Wind speed | Mixed but generally positive at moderate levels | Single-source speculative | **Tested (Lake Michigan).** No significant relationship with either outcome (salmonids p=0.224; perch p=0.141). Inland lakes: not obtained (time-boxed). |
| 6 | Wind direction | Claimed strong directional effect; "which shoreline" heuristic | Single-source speculative | **Partially tested.** Raw direction was obtained for Lake Michigan but not separately regressed as reported here beyond wind-speed candidate #5; the specific shoreline-accumulation mechanism was flagged in step 1 as not testable (no lake-specific shoreline geometry data) and remained untested. Inland lakes: not obtained. |
| 7 | Cloud cover / sky condition | Contradictory claims across sources | Single-source speculative | **Not tested.** Data was not queried in step 2 (no NWS/NCEI pull attempted, time-boxed) for either Lake Michigan or inland lakes. |
| 8 | Precipitation / rain | Mixed, intensity-dependent | Single-source speculative | **Not tested.** Not queried in step 2 for any waterbody (time-boxed). |
| 9 | Barometric pressure (absolute) | Popular belief, but well-established *negative* finding (no proven direct effect) | Well-established (as a negative finding) | **Tested (Lake Michigan).** No relationship with either outcome (salmonids r=+0.003, p=0.994; perch r=+0.317, p=0.372) — consistent with the step-1 expectation of a null result. Inland lakes: not obtained. |
| 10 | Barometric pressure trend | Rate-of-change hypothesis; one saltwater tuna study found an effect, freshwater transferability unverified | Single-source speculative | **Tested (Lake Michigan).** No significant relationship with salmonids (p=0.474); suggestive but not significant with perch (r=+0.631, p=0.069, does not clear even an uncorrected 0.05 bar). Inland lakes: not obtained. |
| 11 | Moon phase / solunar tables | Highly contested; peer-reviewed bass research found no effect | Single-source speculative / actively contested | **Not tested.** Deterministic and cheap to compute, but deferred since it requires exact daily outcome dates, which do not exist for the inland lakes and were not built out for Lake Michigan in this pass. |
| 12 | Water clarity / turbidity | Well-supported negative relationship for sight-feeding predators | Well-established | **Not tested.** WDNR/CLMN Secchi data exists in principle for inland lakes but was not queried in step 2 (time-boxed); per-lake coverage was never verified. |
| 13 | Dissolved oxygen (DO) | Well-documented physiological threshold effect | Well-established (physiology); inferential leap to catch rate not evidenced | **Not testable** from the start — no continuous/reliable DO time series identified for the SE WI inland lakes in either step 1 or step 2 (only sparse volunteer CLMN snapshots at best). |
| 14 | Great Lakes wave height | Plausible by analogy to wind-speed findings; not independently verified | Single-source speculative / inferred | **Tested (Lake Michigan).** No relationship with salmonids (p=0.501, essentially tied with baseline). **The one notable result of the entire evaluation:** strong, held-out-validated relationship with yellow perch harvest rate (r=0.865, p=0.001) — see Section 5 for full caveats. Not applicable to inland lakes (no Great Lakes wave data there). |
| 15 | Great Lakes water level | Plausible effect on nearshore habitat/access; no direct catch-rate study found | Single-source speculative / inferred | **Tested (Lake Michigan).** No significant relationship with either outcome (salmonids p=0.276; perch p=0.550). Not applicable to inland lakes. |
| 16 | Fishing pressure / angler effort | Plausible negative/confounding relationship; also a methodological endogeneity concern | Well-established as a methodological consideration | **Tested (Lake Michigan), with an endogeneity flag.** Effort is the denominator of harvest rate by construction. Showed no significant correlation with either outcome (salmonids p=0.614; perch p=0.121) and did not beat baseline. Confirmed as unsuitable for use as an independent predictor in this form. Inland lakes: moot (no outcome data). |
| 17 | Fish stocking history | Plausible positive effect in stocked species/year-classes following a stocking event | Well-established as fisheries-management logic | **Not statistically tested** in step 4 (not included among the seven regressed candidates). Data was extracted for Pewaukee Lake (65 records, 1987-2025) as a proof of concept and confirmed accessible for Delavan, Geneva, and Winnebago, but full extraction for those three was not completed, and it is moot for Delavan/Geneva since neither has outcome data to test against. |
| 18 | Lake-specific bathymetry / structure | Strong angler consensus that fish concentrate near structure | Single-source speculative (from a data standpoint); ecological logic standard | **Not testable** — static spatial data exists (WDNR lake maps) but WDNR creel survey outcome data is whole-lake aggregate, not location-resolved, so structure cannot be linked to catch-rate variation in V0. |
| 19 | Air temperature / cold-front passage | Widely believed "post-frontal lockjaw" effect; conceptually overlaps pressure/wind | Single-source speculative | **Not separately tested.** Air temperature was obtained for Lake Michigan (buoy ATMP) but the composite "front passage" feature was not built or regressed in step 4. Inland lakes: not obtained. |

**Count check:** 19 candidates total. Of these: 7 were statistically evaluated
against baseline for Lake Michigan in step 4 (#1, #5, #9, #10, #14, #15, #16);
3 more were obtained/buildable but not run through the step-4 regression
(#3, #6 partially, #17 partially, #19); 8 were never obtained/tested for any
waterbody in this pass (#2, #4 unusable at this resolution, #7, #8, #11
deferred, #12, #13 not testable, #18 not testable). Every one of the 19 is
accounted for above.

---

## 4. Dataset reality check (step 2)

The single most consequential finding of the entire V0 pipeline came from the
dataset-build step, not the modeling step: **WDNR does not creel-survey
Pewaukee Lake, Delavan Lake, or Geneva Lake at all.** WDNR's own fisheries
survey reports index (checked directly, by county) lists no creel survey of
any kind for Pewaukee or Delavan, and only a 2015 electrofishing comprehensive
survey (not a creel survey) for Geneva — which, separately, could not even be
extracted from its hosting format (a JavaScript PDF viewer that blocked
programmatic text extraction; a genuine tooling limitation, not evidence the
data doesn't exist, but the practical result in V0 is the same: no usable
data).

This means: **there is no outcome variable — no measure of angler catch or
harvest rate — to predict for any of these three lakes in V0.** No amount of
predictor data (weather, water temperature, stocking history, etc.) can be
evaluated against an outcome that doesn't exist. This is why these three
lakes could not be carried into steps 3-4 at all, regardless of how good the
predictor-side data collection was.

**Lake Winnebago** is a different, more nuanced case. It has real,
long-running WDNR data (1986-2023 bottom-trawl assessment, 38 years) — but
this is a **standardized fisheries research survey measuring fish abundance
per trawl tow**, not an angler creel survey measuring catch rate. It answers
a different scientific question ("how abundant are fish in the lake, per a
standardized research method") than the one this pipeline set out to answer
("how does catch rate vary with conditions, for anglers"). Using it as a
stand-in outcome would misrepresent what the data measures, so it was
correctly excluded from evaluation rather than substituted in as a proxy.

**Only Lake Michigan** had real, matching outcome data (annual harvest rate,
1969-2024, with the extracted years being 2013-2024) and multiple real
predictor series covering overlapping years. That is why steps 3-4
(baseline and evaluation) were only possible for Lake Michigan.

**What this means for the original pilot scope:** the pipeline's premise —
that four named waterbodies would each yield a predictor-evaluation result —
did not hold. Three-quarters of the named inland-lake scope (Pewaukee,
Delavan, Geneva) produced no testable result whatsoever, not because
prediction failed there, but because there was no target to predict against.
Only the Lake Michigan portion of the scope produced a real test.

---

## 5. Evaluation results (Lake Michigan only)

### Baseline

Two no-predictor-data baselines were defined against 2013-2024 annual harvest
rate data (12 years):

1. **Primary: leave-one-year-out (LOO) historical-mean baseline** — for each
   held-out year, predict the mean of all *other* years.
2. **Secondary: persistence baseline** — predict last year's actual value.

| Outcome | LOO mean-baseline MAE | LOO mean-baseline RMSE | Persistence MAE | Persistence RMSE |
|---|---|---|---|---|
| All salmonids combined | 0.0200 | 0.0320 | 0.0246 | 0.0336 |
| Yellow perch (total) | 0.0266 | 0.0316 | 0.0283 | 0.0372 |

The historical-mean baseline outperformed persistence for both outcomes, so
it was used as the bar every candidate had to clear.

### Candidate results

Seven candidates were evaluated with single-variable linear regression under
leave-one-year-out cross-validation, against two outcomes — 14 tests total.
With only 9-12 annual data points, no model beyond simple linear
regression/correlation was used; anything requiring a larger sample would
have overfit and produced meaningless results.

**Primary outcome — all salmonids combined:** none of the seven candidates
showed a statistically distinguishable relationship (all p > 0.15), and six
of seven failed to beat the historical-mean baseline on held-out MAE (the
seventh, wave height, was essentially tied with baseline, not a real edge).
**No candidate tested shows real signal for salmonid harvest rate;** the
historical average remains the best available predictor in V0 for this
outcome.

**Secondary outcome — yellow perch:**

| Candidate | n (years) | r | p | Beats baseline (LOO MAE)? |
|---|---|---|---|---|
| Water temperature | 10 | +0.558 | 0.094 | Yes, but not statistically significant |
| Wind speed | 10 | +0.500 | 0.141 | No |
| **Wave height** | 10 | **+0.865** | **0.001** | **Yes, clearly (47% MAE reduction)** |
| Water level | 12 | +0.192 | 0.550 | No |
| Pressure (absolute) | 10 | +0.317 | 0.372 | No |
| Pressure trend | 9 | +0.631 | 0.069 | Yes, but not statistically significant |
| Angler effort | 12 | -0.473 | 0.121 | No (also structurally endogenous) |

**The one notable result: wave height vs. yellow perch harvest rate.**
r=0.865, p=0.001, which survives even a conservative Bonferroni correction
applied across all 14 tests (~0.0036 threshold). The LOO-CV model cut MAE by
about 47% versus baseline. This is a genuine, held-out-validated statistical
signal — not a fitting artifact of an in-sample-only correlation. However, it
must be read with real caution, not treated as a confirmed finding:

- **n=10.** Ten annual data points is a very small sample for any regression,
  and small-sample correlations are unstable — a single unusual year can
  drive the whole result.
- **The direction is counter to the a-priori hypothesis.** The research phase
  (step 1) inferred, by analogy to wind-speed literature, that *rougher*
  water would suppress catchability or angler access. The actual result is
  the opposite: higher mean wave height is associated with *higher* perch
  harvest rate. A result that contradicts its own prior hypothesis and is
  only explainable after the fact is inherently more likely to reflect
  confounding (e.g., both wave height and perch harvest trending with some
  unmeasured year-level factor, or a specific unusual year) than a result
  predicted in advance and then confirmed.
- **Correcting for multiple comparisons reduces but does not eliminate the
  risk of a false positive at this sample size.** Bonferroni is a
  conservative correction for the number of *tests*, but it does not protect
  against the deeper problem of small-n instability — a real relationship
  and a coincidental strong correlation can look statistically identical with
  only 10 points.

**On the negative results generally:** with only 9-12 annual observations,
statistical power is low. A true, real-world effect of moderate size could
easily fail to reach p<0.05 at this sample size. **The correct reading of the
six-of-seven "no relationship" results for salmonids (and most of the perch
results) is "inconclusive due to low statistical power," not "proven no
effect."** This report does not claim these predictors have been ruled out —
only that they showed no detectable signal in the data available, at the
sample sizes available.

---

## 6. What this means for feasibility

Two different questions were actually asked by this pipeline, and they got
two different kinds of non-answer. Conflating them would misrepresent the
work, so they are kept separate here per DECISIONS.md #005:

**Question A — "Is there outcome data to even test prediction against, for
the inland lakes?"** Answer: **no, not for Pewaukee, Delavan, or Geneva.**
This is a data-availability failure. It says nothing about whether fishing
conditions on those lakes are in fact predictable — that question was never
put to the data, because there was no data to put it to.

**Question B — "Given real outcome and predictor data (Lake Michigan), is
there a detectable predictive signal?"** Answer: **mostly no, with one
statistically notable but causally uncertain exception.** This is an actual
predictive-signal question that was tested and came back negative for the
primary outcome (salmonid harvest rate) and mixed-to-negative for the
secondary outcome (yellow perch), aside from the wave-height result discussed
above.

**Neither question supports a claim that fishing-condition prediction is
"feasible" as currently scoped and evidenced.** Equally, neither result
supports a claim that it is conclusively "infeasible" — Question A was never
tested, and Question B was tested under real statistical-power constraints
(9-12 data points) that leave most negative results open rather than closed.
The honest, evidence-bound conclusion is: **V0 did not establish feasibility,
and identified specific, fixable reasons why it could not**, laid out below.

---

## 7. Recommendations for what would need to change to continue past V0

These are options for CEO consideration, not decisions made by this report.

1. **Inland lakes need an alternative outcome-data source, or should be
   dropped/replaced in scope.** WDNR does not creel-survey Pewaukee or
   Delavan at all; Geneva has one 2015 survey that is not creel data and was
   also not technically extractable in this pass. Before continuing to invest
   in predictor data for these lakes, the project needs either (a) a
   different, real angler-outcome data source for them (state license/app
   survey data, volunteer angler-diary programs, etc., if any exist), or (b)
   a CEO decision to drop them from V0 scope or substitute other WDNR-surveyed
   waterbodies that do have creel data.
2. **Lake Winnebago needs either a matching angler-creel data source or an
   explicit reframing of the research question.** Its trawl-abundance data is
   real and rich but answers "how many fish are there," not "how well do
   anglers catch them." If Winnebago stays in scope, the project should either
   find real Winnebago creel data or explicitly redefine the Winnebago
   sub-question as an abundance-prediction problem, not a catch-rate
   prediction problem, and say so plainly wherever results are reported.
3. **Lake Michigan needs more statistical power before its negative results
   can be trusted, and before its one positive result can be either promoted
   or discarded.** 9-12 annual points is not enough to distinguish "no
   effect" from "effect too small to detect." Two concrete paths: (a) more
   years of history (older Lake Michigan creel reports exist back to 1969 and
   were not fully transcribed — only 2013-2024 was pulled), and (b)
   higher-resolution outcome data (monthly, not just annual, harvest rates —
   the manifest notes monthly data exists in the source PDFs for 2022 and
   2024 and could be extracted for more years), which would multiply the
   effective sample size substantially.
4. **The predictors that were never actually pulled should be pulled before
   being treated as ruled out.** Cloud cover, precipitation, and all inland
   NWS/NCEI weather station data were not queried in step 2 due to time
   constraints, not because they were found unavailable. They remain open
   questions, not tested-and-rejected candidates, and should not be described
   as such in any future summary of this work.
5. **The wave-height / yellow-perch finding needs replication before being
   treated as real.** It should not be used as a basis for any
   user-facing prediction claim until at least one of: (a) it holds up
   against a genuine holdout — i.e., new years of data collected after this
   report, not re-splits of the same 10 points; (b) a plausible causal or
   mechanistic explanation is found for why *higher* waves would correlate
   with *higher* perch harvest (the opposite of the a-priori hypothesis); or
   (c) it is at minimum flagged, if surfaced to any user, as an unconfirmed,
   statistically-derived lead rather than a validated driver of fishing
   success — consistent with DECISIONS.md #005.

---

*End of report. Per CLAUDE.md's hard-stop instruction, no further pipeline
action (STATE.md update, commit, or acting on any recommendation above) has
been taken. Awaiting CEO review and explicit approval.*
