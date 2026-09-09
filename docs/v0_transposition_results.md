# V0 Cross-Lake Transposition Test (Step 3: Test Transposition Where You Can)

Prepared per DECISIONS.md #008, step 3 of the research cycle that step 1
(`docs/v0_inland_lake_inventory.md`) and step 2
(`docs/v0_lake_characteristics.md`) fed into. THE QUESTION: does a
predictor-outcome relationship learned on one lake with real data actually
hold when applied to a different, physically similar lake's real outcome
data? Per Decision #005 ("never represent an arbitrary score as
scientifically validated"), this had to be an actual held-out test, not a
qualitative similarity claim.

Analysis script: `analysis/v0_lake_transposition_eval.py`. Unit tests:
`analysis/tests/test_v0_lake_transposition_eval.py` (12 tests, all passing).
Full numeric results: `analysis/v0_lake_transposition_eval_results.csv`.
Retrieval date for all new data pulled in this step: **2026-09-08**.

**Honest bottom line up front: no validated transposition pair was found.**
Five candidate pairs were tested (ten directional fits, since each pair was
tested both A-predicts-B and B-predicts-A). In every one of the ten, the
source lake's own fitted relationship between angler effort share and
harvest rate was statistically indistinguishable from noise (all p-values
0.13-0.98, correlation signs inconsistent across pairs). Per Decision #005,
a handful of these nominally "beat" the target lake's naive baseline on raw
MAE, but that cannot be read as evidence of a working transfer, because there
was no real relationship on the source side to transfer in the first place
(see Section 4). This step therefore does **not** clear the bar Decision
#008 set for proceeding to step 4 (extrapolating to Pewaukee/Delavan) — that
step should not proceed on this evidence.

---

## 1. Which pairs were attempted, and why

From `docs/v0_lake_characteristics.md`'s descriptive groupings, five pairs
were tested, matched as closely as the real survey years allowed:

| Pair | Similarity basis (step 2) | Year match |
|---|---|---|
| Sand Lake <-> Pine Lake | Similar depth profile and trophic status (both mesotrophic drainage lakes), both have 2-season creel data | **Exact**: both surveyed 2023-24 |
| Minocqua <-> Pelican | Same county (Oneida), comparable surface area/drainage type, flagged in step 2 as "possibly" similar despite differing trophic status (meso vs. eutrophic) | **Exact**: both surveyed 2024-25 |
| Lake Wisconsin <-> Petenwell | Both Wisconsin River impoundments/flowages, comparably shallow relative to surface area | **Same general year**: Jul 2022-Jun 2023 vs. Mar-Jun 2023 |
| Lake Wisconsin <-> Lake Wissota | Both impoundments (the three-impoundment group step 2 flagged) | **Mismatch**: 2022-23 vs. 2019-20 (~3 yr gap) |
| Petenwell <-> Lake Wissota | Both impoundments | **Mismatch**: Mar-Jun 2023 vs. 2019-20 |

Pairs considered and explicitly **not** tested, per the task's instruction
not to force weak comparisons:

- **Devils Lake <-> Sawyer Lake** — step 2 found they share lake type
  (seepage) but differ materially in depth profile (mean/max depth ratio
  0.64 vs. 0.32, i.e. a steep-sided basin vs. a much shallower one relative
  to its deepest point) and neither has a second creel season. Not similar
  enough to be worth testing.
- **White Potato Lake, Big Green Lake** — step 2 explicitly flagged both as
  outliers (White Potato unusually shallow for its surface area; Big Green
  the deepest natural inland lake in the state, 4-5x deeper than anything
  else in the set). No credible match partner exists among the 11 lakes.
- **Sawyer Lake, White Potato Lake, Devils Lake, Big Green Lake** all have
  only **one** surveyed creel season each — even setting aside the pairing
  question, a single season with no second data point cannot support any
  before/after or transposition-relevant comparison on its own.
- **Lake Michigan** — step 2's own assessment (categorically different
  hydrology, orders of magnitude larger, oligotrophic vs. meso/eutrophic)
  makes it the least credible transposition candidate of the set; not paired
  with anything here, consistent with that assessment.

---

## 2. Predictor data: two separate attempts, one abandoned by design, one used

### 2a. Weather (attempted first, per the task instructions) — real data pulled, but cannot support a model

Real NOAA NCEI GHCND daily-summaries data (`data/v0/weather_*.csv`, 6 files)
was pulled via `https://www.ncei.noaa.gov/access/services/data/v1` for the
nearest identifiable long-record COOP station to each lake, restricted to
the **exact creel-survey date windows stated in each lake's own PDF**
(grepped directly from the source reports, not estimated):

| Lake-season | Station used | Survey window (from the PDF's own text) |
|---|---|---|
| Sand Lake 2023-24 | Hayward Ranger Station, USC00473511 | "The open-water creel survey ran from May 6 through Oct. 31, 2023, and the ice fishing creel survey ran from Dec. 1, 2023 through March 3[, 2024]" |
| Pine Lake 2023-24 | Hurley, USC00473800 (see note below) | Same wording as Sand Lake's PDF (shared statewide survey wave) |
| Minocqua 2024-25 | Eagle River, USC00472314 | "The 2024-25 fishing season ran from May 4, 2024, through March 2, 2025. The summer creel survey ran from May 4 through Oct. 31, 2024, and the winter creel survey ran from Dec. 1, 2024, through March 2, 2025" |
| Pelican 2024-25 | Eagle River, USC00472314 (same station) | Same wording as Minocqua's PDF |
| Lake Wisconsin 2022-23 | Sauk City WWTP, USC00477576 (on the lake itself) | Reconstructed from narrative text: September 2022 creel period, ice fishing "as early as mid-November 2022," spring creel "March 1, 2023 through May 30, 2023" — **not a single clean stated range like the others; flagged as an approximate reconstruction** |
| Petenwell Mar-Jun 2023 | Friendship, USC00472973 | "The creel survey ran from March 1 through June 30, 2023" |

One real data-quality problem was found and corrected in the process: the
initially-selected station for Pine Lake (Mercer Ranger Station,
USC00475352, the closest station to Pine Lake itself) turned out to have a
real, large coverage gap for exactly this window (no data May 2023-Oct 2023
or Nov 20, 2023-Feb 25, 2024) — discovered by inspecting the downloaded file,
not assumed. Hurley (USC00473800), a real, still-regional but more distant
COOP station with near-complete coverage for the window, was used instead
and is flagged as such in the script and results.

**Resulting seasonal weather summaries** (`data/v0/weather_*.csv`, aggregated
by `weather_season_summary()`):

| Lake-season | n days | mean TMAX (C) | mean TMIN (C) | total PRCP (mm) |
|---|---|---|---|---|
| Sand Lake 2023-24 | 273 | 16.7 | 4.9 | 458 |
| Pine Lake 2023-24 | 270 | 13.5 | 3.6 | 463 |
| Minocqua 2024-25 | 273 | 13.0 | 0.4 | 547 |
| Pelican 2024-25 | 273 | 13.0 | 0.4 | 547 |
| Lake Wisconsin 2022-23 | 227 | 9.1 | -2.5 | 496 |
| Petenwell Mar-Jun 2023 | 119 | 17.0 | 3.6 | 267 |

**This weather data is real and was genuinely pulled, but it was
deliberately NOT fit into any model, and that is the honest, load-bearing
finding of this sub-section, not a shortfall in effort.** Every inland lake
in this inventory has only 1-2 total creel-survey *seasons* (step 1's own
finding — periodic surveys every ~10-20 years, not a continuous annual
series). Aggregating weather to the outcome's own resolution therefore gives
**at most one data point per lake per candidate weather predictor** (one row
per lake-season). The original V0 Lake Michigan methodology
(`analysis/v0_lake_michigan_eval.py`) requires at least 4 overlapping years
before attempting even a leave-one-out regression, because fewer points
cannot be fit-and-held-out without the "fit" being a trivial, meaningless
line through 1-2 points. This is exactly the scenario the task's step 4
anticipated ("a lake with only one surveyed season and no monthly breakdown
cannot support a real regression, and you should say so rather than force a
1-point model") — and it applies here to every single lake in this
inventory, not just one. Forcing a weather-based lake-level regression here
would either be mathematically degenerate (n=1) or a perfect, meaningless
fit through exactly 2 points (n=2, e.g. Sand Lake's two survey seasons) --
neither is a real held-out test. So: **weather could not be tested as a
transposable predictor for any pair in this inventory**, and no model was
fit to it, per Decision #005.

### 2b. Within-season species-level effort share (the predictor actually used)

Every creel report gives real, already-extracted, per-species rows within
one lake-season: `pct_of_directed_effort` (share of total lake angling
effort spent targeting that species) and harvest counts. This gives **8-16
data points per lake-season** — an order of magnitude more than the weather
route could offer, and enough to actually run the LOO-CV discipline the
original Lake Michigan evaluation used. The outcome variable,
`harvest_rate_fish_per_hour`, was **recomputed directly** as
`total_harvest / directed_effort_hours` for every lake (including
Petenwell), rather than trusting any pre-existing rate column in the CSVs —
this was necessary because Petenwell's own source report has a documented
unit-label bug (its printed "Specific Catch/Harvest Rate" column is fish per
hour where every other lake's matching column is hours per fish; see
`docs/v0_inland_lake_inventory.md`). Recomputing from the two raw counts
directly sidesteps that bug and guarantees identical units across every lake
compared here.

**This deviates from the task's "start simple: weather" framing, and that
deviation is deliberate and disclosed, not a substitution made to manufacture
a testable result.** It is the only predictor-outcome pair in this dataset
with enough real, non-fabricated data points per lake to run an actual
held-out regression and transposition test, given the survey frequency
finding in Section 2a.

**Known caveat, flagged before any results are read:** `pct_of_directed_effort`
and `harvest_rate_fish_per_hour` both derive from the same species'
`directed_effort_hours` (`pct = effort / total lake effort`; `harvest_rate =
harvest / effort`), so any relationship found has a partial mechanical
component — structurally the same kind of concern the Lake Michigan
evaluation raised and flagged for angler effort vs. harvest rate (see
`docs/v0_evaluation_results.md`'s "Angler effort — endogeneity flag"
section). This is disclosed up front, exactly as Decision #005 requires, not
discovered after a favorable-looking result and rationalized around.

---

## 3. Method

For each pair (both directions, A-predicts-B and B-predicts-A):

1. Fit `harvest_rate_fish_per_hour ~ a + b * pct_of_directed_effort` by
   ordinary least squares on ALL of lake A's species rows for the matched
   season (no data from lake B enters this fit at any point).
2. Report lake A's own Pearson r/p and a leave-one-species-out (LOO) fit
   quality diagnostic within lake A alone (same discipline as
   `loo_linear_predictions` in the Lake Michigan script, applied across
   species instead of years; requires >=4 species, always satisfied here).
3. Apply A's fitted line, completely unmodified, to lake B's real
   `pct_of_directed_effort` values (an out-of-sample application by
   construction — lake B was never involved in fitting).
4. Compute the transposed prediction's MAE against lake B's real harvest
   rates.
5. Compare against lake B's **own** leave-one-species-out historical-mean
   baseline (predict the mean of B's *other* species, never the held-out
   species' own value) — the same "must beat a naive no-predictor baseline"
   bar the Lake Michigan evaluation used.

---

## 4. Results

| Pair | Direction | n (source) | n (target) | Source fit: r | Source fit: p | Transposed MAE | Target's own LOO baseline MAE | Beats baseline? |
|---|---|---|---|---|---|---|---|---|
| Sand <-> Pine | Sand model -> Pine | 8 | 9 | +0.011 | 0.979 | 0.1414 | 0.1333 | No |
| Sand <-> Pine | Pine model -> Sand | 9 | 8 | -0.547 | 0.127 | 0.2413 | 0.2237 | No |
| Minocqua <-> Pelican | Minocqua model -> Pelican | 11 | 10 | -0.037 | 0.914 | 0.2451 | 0.2222 | No |
| Minocqua <-> Pelican | Pelican model -> Minocqua | 10 | 11 | +0.025 | 0.945 | 0.2852 | 0.3559 | Yes (nominally) |
| Lk Wisconsin <-> Petenwell | LkWisconsin model -> Petenwell | 12 | 16 | -0.180 | 0.576 | 0.2641 | 0.2868 | Yes (nominally) |
| Lk Wisconsin <-> Petenwell | Petenwell model -> LkWisconsin | 16 | 12 | -0.008 | 0.978 | 0.2050 | 0.2034 | No |
| Lk Wisconsin <-> Wissota *(year mismatch)* | LkWisconsin model -> Wissota | 12 | 10 | -0.180 | 0.576 | 0.2141 | 0.2292 | Yes (nominally) |
| Lk Wisconsin <-> Wissota *(year mismatch)* | Wissota model -> LkWisconsin | 10 | 12 | +0.095 | 0.794 | 0.1980 | 0.2034 | Yes (nominally) |
| Petenwell <-> Wissota *(year mismatch)* | Petenwell model -> Wissota | 16 | 10 | -0.008 | 0.978 | 0.2129 | 0.2292 | Yes (nominally) |
| Petenwell <-> Wissota *(year mismatch)* | Wissota model -> Petenwell | 10 | 16 | +0.095 | 0.794 | 0.2512 | 0.2868 | Yes (nominally) |

### Interpretation — why "beats baseline" is not the same as "validated transfer" here

Look at the `r`/`p` columns before reading the "beats baseline" column: **in
every one of the ten directional tests, the source lake's own fitted
relationship is statistically indistinguishable from zero** (|r| between
0.008 and 0.547, p between 0.127 and 0.979 — none clear even the uncorrected
p<0.05 bar, let alone a multiple-comparisons-adjusted one; with 10 tests run,
roughly 0.5 "significant" results would be expected by chance at p<0.05
alone). A fitted line with r near 0 and p near 1 is, in every practical
sense, close to flat — its "prediction" for any target lake is close to a
constant near the source lake's own mean harvest rate, regardless of the
target's actual `pct_of_directed_effort` values.

That means the six "Yes (nominally)" rows above are not evidence that a real
predictor-outcome relationship transferred from one lake to another. They
show that a nearly-flat line anchored near lake A's own mean happened to
land closer to lake B's true harvest rates than lake B's own
leave-one-out-mean baseline did for that particular small sample — which can
happen by chance with n=9-16 and heavy-tailed species distributions (a
single high-effort-share species like Walleye or Bluegill can pull a
same-sized LOO-mean baseline around more than a near-constant prediction
does). This is exactly the situation Decision #005 warns against
representing as validated: **there was no real relationship on the source
side to transfer in the first place**, so a lower MAE on the target is not
attributable to that relationship being correct and useful elsewhere.

None of the four "No" rows and none of the six "Yes (nominally)" rows change
this conclusion. **No pair in this analysis produced a source-side
relationship with real, held-out-defensible statistical signal (r, p) that
could then be honestly credited with improving predictions on the paired
lake.**

---

## 5. Which pairs had enough data to even attempt a real test, and which didn't

All five pairs tested here **did** have enough real data at the
species-within-season resolution (8-16 points per lake-season, comfortably
above the minimum of 4 the LOO methodology requires) to run an actual
regression and transposition test — that is a genuine, positive finding of
this step, distinct from the outcome of the tests themselves. What could
**not** be tested, and why:

- **Weather-based transposition, for every single pair** — real weather
  data was obtained (Section 2a), but every lake in the inventory has only
  1-2 creel-survey seasons total, giving at most 1-2 outcome data points per
  lake at the resolution weather would need to be aggregated to. This is a
  hard structural limitation of how WDNR surveys inland lakes (periodic,
  not annual), not a gap in this pass's effort.
- **Devils Lake, Sawyer Lake, White Potato Lake, Big Green Lake, in any
  pairing** — each has only one surveyed season, and (per step 2) none
  forms a physically credible pair with another single-season lake in this
  set without forcing a weak comparison the task explicitly said not to
  force.
- **Lake Michigan, in any pairing** — categorically different physically
  from every inland lake per step 2's own assessment; no credible pair
  partner.

---

## 6. Overall assessment

- **No validated cross-lake transposition pair was found.** Ten directional
  tests were run across five candidate pairs, all with adequate real sample
  size (8-16 species-level data points per lake-season). In every test, the
  source-side relationship being transposed was statistically
  indistinguishable from noise (p >= 0.127, most p > 0.5).
- Six of the ten directional tests nominally beat the target lake's own
  naive baseline on MAE, but per Section 4's interpretation, this is not
  attributable to a real, transferable predictor-outcome relationship and
  must not be reported as one.
- Weather (the task's suggested starting predictor) could not be tested for
  any pair — real data was pulled for six lake-seasons, but every inland
  lake's periodic (not annual) creel-survey schedule leaves at most 1-2
  outcome points per lake, below the minimum needed for even a single
  held-out regression fit.
- **Per Decision #008, step 4 of this research cycle (proposing untested
  extrapolation of a validated relationship to Pewaukee/Delavan) cannot
  proceed on this evidence.** Decision #008 explicitly conditions step 4 on
  finding at least one validated transposition pair here; none was found.
  Any future attempt to relate Pewaukee/Delavan to another lake's
  predictor-outcome relationship must be labeled an untested extrapolation,
  not a validated result, consistent with Decision #008's own wording.
- This is a genuinely open empirical question and this result — "couldn't
  validate transfer with the data available" — is treated here as a valid,
  useful finding in its own right, not a failure to be worked around. A
  future pass could revisit this once more inland-lake creel surveys
  accumulate (WDNR's periodic ~10-20 year survey cycle means several of
  these 11 lakes are plausible candidates for a third data point sometime
  in the 2030s), or by testing predictors that don't share a denominator
  term with the outcome variable, which this dataset's structure did not
  offer a ready alternative for at adequate sample size.
