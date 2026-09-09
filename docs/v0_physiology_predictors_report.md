# V0 Physiology/Behavior Predictors Report (Decision #009)

Status: **Draft for CEO approval.** Per CLAUDE.md, this document stops at the
review gate — no STATE.md update, no commit beyond what documents this
analysis, and no action on any recommendation below has been taken.

Prepared from `docs/v0_physiology_research_candidates.md` (step 1),
`docs/v0_physiology_eval_results.md` (step 2), and — for comparison —
`docs/V0_FEASIBILITY_REPORT.md` and `docs/v0_inland_predictability_results.md`
(the prior weather/lake-characteristics results this cycle is measured
against), all read in full. Consistent with DECISIONS.md #005 ("the system
must never represent an arbitrary score as scientifically validated"), every
claim below is scoped exactly to what those documents' held-out evidence
supports — no stronger, no weaker.

---

## 1. Executive summary

Decision #009 posed a specific hypothesis: V0's weather/lake-characteristics
predictors, and the inland cross-lake transfer test, had all come back
negative. Before concluding the project's real outcome data simply lacks a
detectable signal, this cycle tested one more candidate-predictor class —
established, well-evidenced fish physiology and behavior science
(temperature-driven feeding/activity windows, diel movement, spawning
behavior, species-specific metabolic thresholds) — for the species already
present in the project's real outcome data. The specific question: does
angler skill/effort noise in creel data mask a real physiological signal
that weather and lake characteristics, being once removed from actual fish
behavior, could not capture?

**Direct answer: no.** Physiology-derived predictors were tested against
real Lake Michigan and inland-lake outcome data with the same leave-one-out
cross-validation discipline used throughout V0. Across 12 physiology-derived
tests that produced a real correlation statistic, **not one reached even an
uncorrected p<0.05** — the lowest p-value anywhere in this analysis is 0.094
(Yellow Perch, Lake Michigan, annual). This is a *cleaner* (more uniformly
null) result than the weather-based Lake Michigan evaluation, which produced
one predictor — wave height vs. yellow perch harvest rate, r=+0.865, p=0.001
— that survived Bonferroni correction.

Per Decision #009's own framing, this result argues **against** the
angler-skill-noise-masking hypothesis, not for it. If a well-evidenced,
species-specific physiological signal existed and angler skill/effort noise
were merely obscuring it, a reasonably strong, mechanistically-targeted
predictor set should have shown at least a hint of a *stronger* relationship
to catch rate than arbitrary weather variables. Instead it showed a
*weaker* one. This is reported plainly, per Decision #005, as a negative
result and not adjusted toward a preferred conclusion.

---

## 2. Step 1 — Research candidates (all 17, nothing dropped)

`docs/v0_physiology_research_candidates.md` searched peer-reviewed fisheries
journals, agency technical reports (Ontario MNR, Great Lakes Fishery
Commission, WDNR), and university extension material for quantifiable
physiology/behavior relationships in the species actually present in the
project's outcome data. It recorded **17 candidates**: 16 real
physiology/behavior claims plus one folklore claim (barometric pressure)
explicitly checked and excluded per this cycle's evidentiary bar.

Evidentiary discipline applied in step 1, carried through this report:
barometric pressure was checked against primary literature and found to
have no controlled-study support, so it was excluded outright rather than
tested; several numeric claims sourced to charter-fishing-industry websites
(Chinook and Coho Lake Michigan temperature windows) were flagged as **not
meeting the evidentiary bar as stated** and held pending re-sourcing from a
primary study, rather than used as-is.

| # | Species | Claim (brief) | Evidence strength | Computable? |
|---|---|---|---|---|
| 1 | Walleye | Feeding peaks near dusk/dawn low-light (~300 lux); scotopic vision advantage | Strong — field study (Ryder 1977) + supporting lab/physiological studies | **No** — no trip-level timestamp exists in the creel outcome data |
| 2 | Walleye | Reduced feeding below ~50°F; activity range ~55-75°F; preference cluster ~62-68°F | Solid field telemetry study + agency/extension synthesis for the precise band | Lake Michigan: yes (NDBC WTMP exists). Inland: only with water-temp acquisition/estimation |
| 3 | Walleye | Spawning triggered ~40-52°F, peak ~44-48°F | Agency/extension-tier for the precise window; underlying trigger mechanism well established | Yes, at seasonal resolution; same water-temp-availability constraints as #2 |
| 4 | Yellow Perch | Optimal temperature ~23-24°C | Peer-reviewed aquaculture/growth-performance literature; growth-optimum, not catchability-optimum | LM: yes (NDBC WTMP). Inland: only with water-temp acquisition/estimation |
| 5 | Largemouth Bass | Thermal optimum for growth ~25-29°C; one study found higher feeding at 18°C | Mixed/conflicting within the primary literature itself | Inland only, requires water-temp acquisition/estimation |
| 6 | Smallmouth Bass | Thermal preference ~22-25°C; avoids warmer/colder water in a Lake Michigan harbor study | Field telemetry directly in Lake Michigan — comparatively strong | Inland only (species not confirmed in LM data), requires water-temp acquisition/estimation |
| 7 | Northern Pike | Activity optimum ~55-65°F; physiological optimum 19-21°C; avoidance above ~75°F | Solid field telemetry (MN lakes) + lab physiology for lethal limit; activity-optimum band more agency-tier | Inland only, requires water-temp acquisition/estimation |
| 8 | Northern Pike | Spawning trigger ~40-48°F, earliest gamefish to spawn | Extension-tier for the precise figure; consistent with supporting cold-temperature early-life-stage physiology | Inland only, requires water-temp acquisition/estimation |
| 9 | Muskellunge | Thermal optimum ~22°C; activity declines above 25°C; thermal refuging in summer | Solid field telemetry/radio-tracking studies | Inland only, requires water-temp acquisition/estimation |
| 10 | Black Crappie | Preferred temp ~27-29°C; feeding events +22% with 2°C rise in one study | Mixed — direct feeding-behavior experiment is undergraduate research, not journal-reviewed; preferred-temp figure lacks a clear primary citation | Inland only, requires water-temp acquisition/estimation |
| 11 | Bluegill | Spawning trigger ~65-80°F (peak initiation ~71.6°F), repeat spawning ~30-day intervals | Extension/angling-media-tier for the precise numbers; underlying mechanism well established | Inland only, requires water-temp acquisition/estimation; seasonal resolution only |
| 12 | Chinook Salmon | Feeds most actively 50-58°F; tracks thermocline in summer | Thermocline-tracking mechanism real; **specific °F figures traced to charter-fishing sources — flagged, does not meet evidentiary bar as stated** | LM: computable once re-sourced; surface buoy WTMP a poor proxy for depth-following behavior even then |
| 13 | Coho Salmon | Prefers slightly warmer water than Chinook (~54-60°F) | Same evidentiary issue as #12 — **charter-fishing sourced, flagged** | Same as #12 |
| 14 | Brown Trout | Annual modal selected temp ~12°C; upper preferred ~16°C in Lake Michigan | Field study specifically in Lake Michigan — reasonably strong | Inland (Devils Lake) requires water-temp acquisition/estimation; LM species-level presence unconfirmed in step 1 |
| 15 | Lake Trout | Cold-water preference ~40-52°F | General secondary/extension-tier synthesis; primary source (Wismer & Christie 1987) not retrievable in step 1 | LM computable via NDBC WTMP once sourced; inland requires water-temp acquisition/estimation |
| 16 | Cross-species | Ontario MNR (Hasnain, Minns & Shuter 2010, CCRR-17) compiled thermal metrics — a source pointer, not a standalone candidate | Peer-reviewed agency compilation; full text not retrieved in step 1 | N/A directly — logged for step 2 follow-up |
| 17 | Cross-species | Barometric pressure affects fish activity/catch rate | **No primary scientific support found — excluded per this cycle's folklore rule** | Excluded, not carried into step 2 |

---

## 3. Step 2 — Validation results (the actual tests run)

### 3a. Mid-cycle sourcing improvement

Step 1 had flagged several numbers (Chinook/Coho/Lake Trout/Brown Trout
Lake Michigan temperatures; walleye/yellow perch preference bands) as
needing re-sourcing before use. Step 2 made real progress on this: it
successfully retrieved and parsed **Wismer & Christie 1987, Great Lakes
Fishery Commission Special Publication 87-3**, "Temperature Relationships of
Great Lakes Fishes: A Data Compilation" — a 165-page primary compiled
source that step 1 could not text-extract — and used it to replace flagged
numbers with real field values:

- Chinook Salmon: charter-fishing 52-56°F figure replaced with the real
  Lake Michigan field final-temperature-preferendum value, **11.7°C**
  (Coutant 1977a, via GLFC Sp87-3).
- Coho Salmon: charter-fishing 54-60°F figure replaced with a real Lake
  Michigan field value, **11.4°C**.
- Lake Trout: the step-1 "citation incomplete" flag resolved with a real
  Point Beach, Lake Michigan field value, **11.8°C**.
- Brown Trout: real Lake Michigan field value, **13.8°C** (one of several
  readings in the source spanning 12.2-19.9°C across studies/life stages,
  disclosed rather than hidden).
- Walleye: the fuzzy 62-68°F "preference cluster" upgraded to one specific
  real field value, **20.6°C**, from Trout Lake, Wisconsin (Coutant 1977a) —
  directly Wisconsin-sourced.
- Yellow Perch: real field values, **20.8°C at Lake Michigan** and **20.2°C
  at Trout Lake/Silver Lake, Wisconsin**, used separately for the Lake
  Michigan and inland tests respectively.

Candidate #16 (Hasnain, Minns & Shuter 2010, Ontario MNR CCRR-17) could
**not** be retrieved in step 2 either — search-located URLs returned
unrelated CCRR-21/CCRR-22 reports. A related DFO/Fisheries and Oceans
Canada report was found but its tables could not be reliably parsed within
the pass's time budget and was not used as a numeric source, to avoid
misattributing a number pulled from an ambiguous table. Species without a
GLFC Sp87-3 or research-doc value (Sauger, Cisco, Burbot, Rainbow Trout)
remain untested this cycle. Candidate #1 (walleye diel/light-window
feeding) was **not attempted**, per the research doc's own instruction — no
trip-level timestamp exists anywhere in the creel outcome data. Candidate
#17 (barometric pressure) remains excluded.

### 3b. Lake Michigan results

**Annual (2015-2024, real NDBC WTMP buoy coverage):**

| Candidate | n (years) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Yellow Perch: distance from 20.8°C (GLFC LM field preferendum) | 10 | -0.558 | 0.094 | 0.0222 vs 0.0286 | Yes |
| All salmonids combined: distance from 12.18°C (GLFC 4-species guild average) | 10 | +0.487 | 0.153 | 0.0269 vs 0.0241 | No |

A methodologically important finding: the salmonid-guild distance predictor
is **mathematically identical** to the original raw-water-temperature test
already run in `docs/v0_evaluation_results.md`. Lake Michigan's real annual
mean surface WTMP over 2015-2024 ranges 12.79-18.29°C — every year is
warmer than the 12.18°C salmonid guild target, never colder — so
distance-from-target reduces to a pure positive affine transform of raw
WTMP over the observed range, producing identical r, p, and LOO MAE
(r=+0.487, p=0.153, 0.0269 vs 0.0241) to the prior test. The physiology
reframing added no new information for this candidate. This confirms, with
real data, the research doc's own a-priori caveat for candidates #12-15:
surface buoy data is a poor proxy for the depth-following behavior of
cold-water salmonids, which track the thermocline well below the surface —
Lake Michigan's surface water essentially never comes close to what deep
salmonids actually prefer.

For Yellow Perch, the relationship is directionally consistent with the
physiological hypothesis (harvest rate falls as distance from the 20.8°C
preferred temperature grows) and beats the naive baseline by a real margin
(a ~22% MAE reduction), but p=0.094 does not clear even the uncorrected
0.05 bar, let alone a multiple-comparisons-adjusted one (Bonferroni bar
across this analysis's 15 tests ≈ 0.0033). This is the strongest
physiology-based result found on Lake Michigan, and it is not statistically
distinguishable from noise at n=10.

**Monthly (secondary/bonus test — only 2 years of monthly data exist):**

| Candidate | n (periods) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Walleye: distance from 20.6°C (GLFC WI field value) | 10 | +0.214 | 0.553 | 0.0144 vs 0.0132 | No |
| Yellow Perch: distance from 20.8°C | 10 | -0.210 | 0.560 | 0.0138 vs 0.0127 | No |
| Coho Salmon: distance from 11.4°C | 10 | +0.045 | 0.902 | 0.0319 vs 0.0279 | No |

No signal at this resolution either, disclosed as unsurprising given only 2
independent years underlie these 10 rows (the periods within a year are
highly autocorrelated, not independent observations).

### 3c. Inland lake results

**Real WDNR CLMN water temperature was obtained for 6 of 11 lakes** — a
methodological strength worth naming explicitly. Rather than falling back
to estimating water temperature from air temperature, step 2 first
attempted real acquisition via WDNR's Citizen Lake Monitoring Network
(CLMN), located the best-coverage monitoring station for each of the 11
inland lakes with creel outcome data, and pulled real shallow-depth (≤3 ft)
readings falling inside each lake's own creel-survey window:

| Lake | Creel season | Real readings in window | Mean water temp (real) |
|---|---|---|---|
| Minocqua Lake | 2024-25 | 3 | 20.87°C (69.6°F) |
| Pelican Lake | 2024-25 | 15 | 22.31°C (72.2°F) |
| Devils Lake | Jul 2023-Jun 2024 | 4 | 18.80°C (65.8°F) |
| Pine Lake | 2023-24 | 5 | 21.01°C (69.8°F) |
| Sand Lake | 2023-24 | 5 | 21.51°C (70.7°F) |
| White Potato Lake | 2019-20 | 6 | 18.84°C (65.9°F) |

The other **5 of 11 lakes had real CLMN stations but no real reading inside
that lake's own creel-survey window** — Big Green Lake, Lake Wisconsin,
Petenwell Lake, Sawyer Lake, and Lake Wissota — and were correctly logged
as **not testable**, with no estimation substituted, per Decision #005 and
the task's explicit instruction. This is itself a methodological strength:
step 2 disclosed a partially-successful acquisition attempt rather than
papering over the gap with a modeled estimate.

**A real data-quality finding was disclosed while parsing this data**: a
unit-mislabeling bug in the source WDNR SWIMS export — some deeper readings
carry a "DEGREES F" tag on values that are clearly still Celsius, continuous
with the shallower, correctly-Celsius-labeled readings in the same
same-date depth profile (e.g., Devils Lake, 2024-05-23: a smooth Celsius
decline through the water column, with a value at 10 ft mislabeled
"DEGREES F" that would otherwise imply an impossible ice-cold 10.1°F
reading). This bug was checked and verified to **not** affect any of the
shallow (≤3 ft) readings used in this analysis, but is disclosed for anyone
using the deeper rows in the raw per-lake CSVs.

**Per-species distance-from-preferred-temperature (leave-one-lake-out CV):**

| Species | n (lakes) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Largemouth Bass (26.5°C, growth-optimum, flagged) | 5 | +0.125 | 0.841 | 0.0361 vs 0.0251 | No |
| Smallmouth Bass (23.5°C, Lake Michigan field study) | 5 | -0.569 | 0.317 | 0.0121 vs 0.0101 | No |
| Northern Pike (20.0°C, physiological growth-optimum) | 4 | +0.855 | 0.145 | 0.0174 vs 0.0282 | Yes |
| Muskellunge (22.0°C, field telemetry optimum) | 0 | n/a | n/a | n/a | n/a — no lake had non-zero recorded harvest for this species |
| Black Crappie (28.0°C, WEAKEST evidence, flagged) | 6 | -0.522 | 0.288 | 0.2119 vs 0.2250 | Yes |
| Walleye (20.6°C, GLFC Wisconsin field value) | 5 | -0.232 | 0.708 | 0.0715 vs 0.0570 | No |
| Yellow Perch (20.2°C, GLFC Wisconsin field value) | 6 | +0.615 | 0.194 | 0.1347 vs 0.1732 | Yes |

Three of seven species candidates nominally beat baseline (Northern Pike,
Black Crappie, Yellow Perch), but at n=4-6 lakes with every p-value above
0.14, none is statistically distinguishable from noise — this project's own
precedent (the `max_depth_ft` correlation in
`docs/v0_inland_predictability_results.md` that beat a full-sample
significance test but then failed LOO-CV) is a direct warning against
treating small-sample apparent wins as findings. Yellow Perch is the most
consistent result across the whole analysis — it beats baseline on both
Lake Michigan and pooled inland lakes, in the same direction, using two
independently-sourced GLFC field values — but it remains not significant in
either test individually and must be reported as "suggestive, not
validated," per Decision #005.

**Pooled cross-species model (leave-one-lake-out CV, n=31 species-lake rows
across 6 independent lake-seasons):**

| Model | n | LOO MAE | vs. naive-mean baseline | vs. species-identity baseline |
|---|---|---|---|---|
| Distance from species-specific preferred temp | 31 | 0.1154 | 0.1102 (No) | 0.0956 (No) |

The pooled model does not beat either baseline, mirroring the exact pattern
found for weather/characteristics predictors in the original inland pooled
evaluation. Species identity alone remains a stronger predictor of harvest
rate than either predictor class tested so far.

**Bluegill (candidate #11)** was tested differently, since the research doc
gives it only a spawning-trigger threshold, not a preferred-temperature
optimum — the monotonic hypothesis (warmer water → more spawning bouts →
higher catchability) was tested directly against raw lake water
temperature:

| Candidate | n (lakes) | r | p | LOO MAE: model vs baseline | Beats baseline? |
|---|---|---|---|---|---|
| Bluegill: raw mean water temp (monotonic hypothesis) | 6 | +0.069 | 0.897 | 0.3687 vs 0.3022 | No |

No signal (r≈0, p=0.90), consistent with the extension-tier evidence
quality already flagged for this candidate's specific numeric threshold.

### 3d. The untestable diel/light-window candidate

Candidate #1, walleye's dusk/dawn low-light feeding-activity window — the
single most rigorously evidenced physiological mechanism identified in
step 1 (field study plus supporting lab/physiological literature on
walleye scotopic vision) — was **correctly not forced into a test**. No
trip-level timestamp exists anywhere in this project's creel outcome data
(both inland-lake and Lake Michigan monthly records are seasonal/period
aggregates), so there is no sub-daily catch record to attach a
light-condition value to. This is logged as "considered, not testable in
V0," per the pipeline's dataset-build step, not as a test that ran and
failed.

### 3e. Multiple-comparisons caution

Twelve physiology-derived candidate tests produced a real Pearson
correlation p-value (2 Lake Michigan annual + 3 Lake Michigan monthly + 6
inland per-species with n≥4 lakes + 1 Bluegill). At an uncorrected p<0.05
threshold, roughly 0.6 "significant" results would be expected by chance
alone across 12 tests. **Zero** were found — the lowest p-value anywhere is
0.094. A Bonferroni-corrected bar would sit around p<0.0042, which nothing
here comes close to. This is a materially cleaner null result than the
original weather-based Lake Michigan evaluation, which did produce one
candidate (wave height) clearing even the conservative Bonferroni bar.

---

## 4. Comparison to prior V0 evaluations

| | Weather/characteristics (already tested) | Physiology (this cycle) |
|---|---|---|
| Lake Michigan, salmonids | 0/7 candidates beat baseline; best r=+0.487, p=0.153 (raw water temp) | 0/2 beat baseline; salmonid-guild distance predictor mathematically identical to the raw-water-temp result already on record |
| Lake Michigan, yellow perch | **1/7 candidates (wave height) beat baseline, r=+0.865, p=0.001**, surviving Bonferroni correction — the strongest result in the whole V0 project, though causally uncertain per the original report | 1/2 beats baseline (annual distance-from-20.8°C), r=-0.558, p=0.094 — directionally sensible, real MAE improvement, but not significant and far weaker than wave height |
| Inland lakes, lake-level | 0/7 univariate + 1/3 multivariate (confirmed overfitting artifact, R²=0.93 on 11 points) beat baseline | 3/7 per-species distance candidates + 0/2 pooled models beat baseline; all 3 per-species "wins" have p>0.14 (n=4-6) |
| Inland lakes, species-pooled | 0/3 beat either baseline; species identity is the strongest available predictor | 0/2 beat either baseline; species identity remains the strongest available predictor |
| Strongest single result across the whole project | Wave height → LM yellow perch, r=+0.865, p=0.001 (Bonferroni-surviving) | Yellow Perch (annual LM + pooled inland), directionally consistent across 2 water bodies, r=-0.558/+0.615, both p>0.09 |

**Physiology predictors did not outperform weather/lake-characteristics
predictors on either water body.** On Lake Michigan, physiology produced a
cleaner null (no candidate approaching significance at all) versus
weather's one genuine Bonferroni-surviving hit. On the inland lakes, both
predictor classes converge on the same "species identity beats everything"
pattern, with no environmental or physiological predictor adding value on
top of it.

---

## 5. What this means for Decision #009's hypothesis

Decision #009's angler-skill-noise-masking hypothesis predicted that a
well-evidenced, species-specific, mechanistically-grounded predictor class
would show a *stronger* relationship to catch rate than arbitrary weather
variables, once skill/effort noise was accounted for by using
better-targeted predictors. **That did not happen — if anything, the
physiology predictors performed slightly worse.**

This is more consistent with either:

1. **A genuine absence of a detectable catch-rate signal** in the available
   outcome data at this sample size — the same "no signal, not enough power
   to rule effects out entirely" framing used in every prior V0 report; or
2. **The physiology predictors used, despite being well-evidenced for the
   fish's own thermal/behavioral state, still being several steps removed
   from what actually determines whether an angler catches a fish on a
   given trip** — gear, technique, exact location, timing within a season —
   not necessarily that no physiological signal exists at all.

The one mechanistically informative finding in this cycle (Section 3b: the
salmonid guild's real physiological cold-water preference, 12.18°C, never
comes close to Lake Michigan's real observed annual surface water
temperature, 12.79-18.29°C) supports a **data-availability/measurement-proxy**
explanation, not an angler-skill-noise explanation — surface buoy data is
simply the wrong measurement for deep-water salmonid behavior.

This report does **not** claim the skill/effort-noise hypothesis is
disproven outright. It states precisely what was and was not tested: the
single most rigorously-evidenced physiological mechanism found in this
cycle — walleye's diel, light-driven catchability (candidate #1) — was
**never possible to test**, because the outcome data's temporal resolution
has no trip-level timestamp to attach a light-condition value to. That
means the strongest candidate for the skill-noise-masking hypothesis was
**untestable, not tested-and-failed** — an important, honest distinction.
Every candidate that *was* tested came back negative, but the best-evidenced
one never got a real chance.

---

## 6. Recommendations for CEO consideration

These are options for CEO consideration, not decisions made by this report.

1. **Whether it is worth acquiring trip-level or daily creel data** (rather
   than seasonal aggregates) specifically to test the diel/light-window
   walleye hypothesis — this is the one candidate this cycle could not test
   at all, and it is also the best-evidenced physiological mechanism found
   across both research passes. Without it, the skill-noise hypothesis
   remains only partially examined.
2. **Whether this is sufficient evidence to deprioritize the "better
   predictors will fix it" line of investigation**, in favor of directly
   investigating outcome-data resolution/quality. Two full predictor
   classes (weather/characteristics, and now physiology/behavior) have both
   returned null or near-null results against the same outcome data; the
   diel/light-window gap suggests the bottleneck may be the outcome data's
   temporal granularity rather than the predictor class chosen.
3. **Whether the real Wismer & Christie 1987 (GLFC Sp87-3) source and the
   real WDNR CLMN inland water-temperature data obtained this cycle are
   reusable assets** for any future predictor work, independent of this
   cycle's null result — both represent real, primary/agency-sourced data
   that took genuine acquisition effort and remain valid regardless of
   whether physiology predictors clear a bar in this cycle.
4. **Whether the Ontario MNR CCRR-17 (Hasnain, Minns & Shuter 2010) source —
   never successfully retrieved across two research passes — is worth a
   dedicated retrieval attempt**, or should be abandoned as a lead. It would
   let several extension-tier numeric flags (bluegill, black crappie,
   pike spawning trigger) be upgraded to a genuine peer-reviewed
   cross-species source, and would fill in species this cycle left
   untested (Sauger, Cisco, Burbot, Rainbow Trout), but two passes have now
   failed to locate the actual document.

---

*End of report. Per CLAUDE.md's hard-stop instruction, this document stops
at the review gate — no STATE.md update and no further pipeline action has
been taken beyond writing this analysis's underlying scripts, tests, and
this report. Awaiting CEO review.*
