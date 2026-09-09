# V0 Inland-Lake Transfer Report — Decision #008 Research Cycle

Status: **Draft for CEO approval.** Per CLAUDE.md, this document stops at the
approval gate. No STATE.md update, no commit, and no action on any
recommendation below has been taken — a separate step afterward will handle
documentation updates and committing.

Prepared from: `docs/v0_inland_lake_inventory.md` (step 1), `docs/v0_lake_characteristics.md`
and `data/v0/lake_characteristics.csv` (step 2), `docs/v0_transposition_results.md`
(step 3), read in full. Consistent with DECISIONS.md #005 ("the system must
never represent an arbitrary score as scientifically validated"), every claim
below is scoped exactly to what those documents' evidence supports — no
stronger, no weaker.

**This report does not revisit, change, or reopen the Lake Michigan findings
and conclusions in `docs/V0_FEASIBILITY_REPORT.md`.** Those stand exactly as
reported. This document is scoped entirely to the Decision #008 research
cycle: expanding the inland-lake search and testing cross-lake transfer.

---

## 1. Executive summary

Per Decision #008, this cycle set out to do two things: (1) widen V0's
inland-lake search beyond Pewaukee, Delavan, and Geneva to any Wisconsin
inland lake with real, extractable creel-survey data, and (2) test whether a
predictor-outcome relationship learned on one lake with real data transfers
to a physically similar lake — including, as a conditional next step, whether
that transfer could then be used to say anything about lakes like Pewaukee
and Delavan that still have no outcome data of their own.

**What this cycle found:**

- **Step 1 succeeded as an inventory exercise.** 11 additional Wisconsin
  inland lakes were found with real, extracted creel-survey data, on top of
  Lake Michigan — a large improvement over the zero inland lakes the original
  V0 report could use.
- **Step 2 succeeded as a characterization exercise.** All 11 lakes (plus
  Lake Michigan, Pewaukee, and Delavan for reference) received a real,
  sourced physical/limnological profile, with 9 of 14 lakes fully
  characterized and 5 partially characterized.
- **Step 3, the core test, came back negative.** Five candidate lake pairs
  (ten directional tests) were run through an actual held-out transposition
  test. In every one of the ten tests, the relationship being transposed was
  statistically indistinguishable from noise on the source lake itself.
  **No validated transposition pair was found anywhere in this cycle.**
- **Step 4 — proposing Pewaukee or Delavan as recipients of a transferred
  relationship — explicitly did not proceed**, per Decision #008's own
  conditional rule: step 4 only proceeds if step 3 validates at least one
  pair. It did not. There is nothing to extrapolate to Pewaukee or Delavan
  from this cycle's work.

**Bottom line: the inland-lake data foundation is now genuinely better than
it was in the original V0 report, but the specific question Decision #008
asked — can a predictor-outcome relationship be transferred between lakes —
remains unresolved, not because it was disproven, but because it could not be
tested at adequate statistical power for the reasons detailed in Section 4.**
Pewaukee and Delavan remain exactly where the original V0 report left them:
no outcome data, and now also no validated transfer path to borrow one from
elsewhere.

---

## 2. Step 1 — Inventory results

Full detail: `docs/v0_inland_lake_inventory.md`.

### 2a. Lakes found with real, extracted creel data (11)

| Rank | Lake | County | Survey season(s) | Extractability |
|---|---|---|---|---|
| 1 | Minocqua Lake | Oneida | 2024-25 and 2009-10 | Extractable (image-transcribed) |
| 2 | Pelican Lake | Oneida | 2024-25 and 2011-12 | Extractable (image-transcribed) |
| 3 | Devils Lake | Sauk | Jul 2023-Jun 2024 | Extractable directly (`pdftotext -layout`) |
| 4 | Big Green Lake | Green Lake | 2022-23 | Extractable (image-transcribed) |
| 5 | Lake Wisconsin | Columbia/Sauk | Jul 2022-Jun 2023 | Extractable (image-transcribed) |
| 6 | Petenwell Lake | Adams/Juneau/Wood | Mar-Jun 2023 | Extractable, but units differ (fish/hour, not hours/fish — flagged and corrected) |
| 7 | Pine Lake | Iron | 2023-24 and 2017-18 | Extractable (image-transcribed) |
| 8 | Sand Lake | Sawyer | 2023-24 and 2007-08 | Extractable (image-transcribed) |
| 9 | Sawyer Lake | Langlade | Summer 2023 | Extractable (image-transcribed) |
| 10 | Lake Wissota | Chippewa | 2019-20 and 2006-07 | Extractable (image-transcribed) |
| 11 | White Potato Lake | Oconto | 2019-20 | Extractable (table location differed from its own table of contents) |

Four of the eleven (Minocqua, Pelican, Pine, Sand) have two separate creel
survey seasons each, 8-17 years apart — the closest structural analogue
available for inland lakes to Lake Michigan's multi-year series, but each
pair is still only 2 point-in-time observations, not a continuous annual
series. No inland lake in this inventory has continuous annual creel
coverage comparable to Lake Michigan's 1969-2024 series.

A real, general tooling finding surfaced during extraction: plain
`pdftotext` silently misaligns species labels and numeric columns in these
WDNR multi-column creel tables. Every number above was instead verified by
rendering the table page to an image and transcribing it cell by cell, not
taken from raw `pdftotext` output.

### 2b. Found but blocked

**Lake Winnebago — 2012 Yellow Perch Creel Survey.** A genuine creel report
(not the trawl/abundance survey already correctly excluded from the original
V0 report) is listed in WDNR's index, but it is hosted only through a
JavaScript (Widen) PDF-viewer wrapper that does not expose a static,
programmatically fetchable PDF — the same failure mode as Geneva Lake's 2015
survey in the original V0 report. This is a real, materially new finding: it
means Winnebago's data-availability status is more nuanced than "no creel
data at all." It is logged as blocked, not confirmed unavailable, and is
flagged for retry with browser-automation-based fetching in a later step.

### 2c. Ruled out / explicitly not counted as creel data

- **Dozens of WDNR "Comprehensive Survey," netting, and electrofishing
  reports** found statewide — excluded for the same reason Winnebago's trawl
  data was excluded from the original V0 report: they measure fish
  population abundance, not angler catch/harvest rate.
- **Barron/Polk put-and-take trout lakes (2023)** — real WDNR data, kept as
  a source file, but reports percentage of stocked trout recaptured, a
  different metric from an angler-hours harvest rate. Not built into the
  ranked creel-data list.
- **Wisconsin River tailwater below Prairie du Sac Dam (2020-21)** — real,
  confirmed-extractable creel data with effort/catch/harvest by species, but
  excluded because it is a river tailwater reach, not a lake, which is
  outside Decision #008's "inland lake" wording. Kept as a source in case a
  later step wants to fold river creel data into the project.
- **Pewaukee, Delavan, Geneva** — status unchanged from the original V0
  report; not re-checked in this pass, since Decision #008 frames this as
  widening the search to other lakes, not re-litigating those three.

---

## 3. Step 2 — Lake characterization

Full detail: `docs/v0_lake_characteristics.md`; full table:
`data/v0/lake_characteristics.csv` (14 rows).

All 14 lakes in scope (the 11 inland lakes, Lake Michigan, and Pewaukee and
Delavan for reference only — they still lack outcome data) received at least
county, surface area, max depth, lake type, and a real creel-derived (or, for
Pewaukee/Delavan, WDNR general "fish present" list, explicitly flagged as
not creel-derived) primary-species list.

- **9 of 14 lakes fully characterized** (surface area, max depth, mean
  depth, trophic status, lake type, primary species all populated):
  Minocqua, Devils Lake, Big Green Lake, Pine Lake, Sand Lake, White Potato
  Lake, Lake Michigan, Pewaukee, Delavan Lake.
- **5 of 14 partially characterized** (missing mean depth and/or trophic
  status only — surface area, max depth, lake type, and primary species are
  populated for all 14): Pelican Lake, Lake Wisconsin, Petenwell Lake,
  Sawyer Lake, Lake Wissota.
- A data-quality finding worth carrying forward: for most inland lakes, the
  creel PDF's own stated surface area/max depth and the WDNR Find-a-Lake
  facts page's stated figures do not match exactly (e.g. Lake Wissota:
  6,300 vs. 6,148 acres; 72 vs. 64.4 ft max depth — a real, non-trivial
  discrepancy). Both figures are kept side by side rather than one being
  silently chosen.

**Notable groupings identified (descriptive only — no predictive or
transferability claim made at this step):**

- **Lake type split:** 6 of the 11 inland lakes are drainage lakes
  (Minocqua, Pelican, Big Green, Pine, Sand), 3 are seepage lakes (Devils,
  Sawyer, White Potato), and 3 are impoundments/flowages (Lake Wisconsin,
  Petenwell, Lake Wissota — all Wisconsin/Chippewa River reservoirs). Both
  Pewaukee and Delavan are drainage lakes, the majority type among the 11.
- **Sand Lake and Pine Lake** are similar in depth profile and trophic
  status (both mesotrophic drainage lakes) despite a roughly 3x surface-area
  difference, and both have 2-season creel data.
- **The three impoundments (Lake Wisconsin, Petenwell, Lake Wissota)** are
  the three largest inland lakes in the set by surface area but all
  comparatively shallow, consistent with being dammed river reaches rather
  than glacial lake basins.
- **Pewaukee Lake and Delavan Lake are themselves close to each other** on
  every physical dimension measured (surface area, max/mean depth, lake
  type, trophic status) — unsurprising since both are the original V0
  SE-Wisconsin lakes lacking outcome data, but worth noting they were
  already similar to begin with.
- **Lake Michigan is categorically different from every inland lake** in
  this set on every dimension: orders of magnitude larger, roughly 4x deeper
  than even the deepest inland lake (Big Green Lake), oligotrophic rather
  than meso/eutrophic, and a fundamentally different open-lake hydrology.
  This physical gap makes it the least credible candidate for cross-lake
  transposition of anything tested in step 3.

---

## 4. Step 3 — Transposition test results

Full detail: `docs/v0_transposition_results.md`; analysis script:
`analysis/v0_lake_transposition_eval.py`; full numeric results:
`analysis/v0_lake_transposition_eval_results.csv`.

### 4a. What could not be tested at all: weather-based transposition

The task's natural starting point — fitting a weather predictor on one lake
and applying it to a similar lake — could not be run for any pair. Real NOAA
NCEI daily-weather data was pulled and aggregated to each lake's exact
creel-survey date window (6 lake-seasons, real station data, one genuine
data-quality correction made along the way for a station with a coverage
gap). The problem is structural, not an effort shortfall: **every inland
lake in this inventory has only 1-2 total creel-survey seasons ever** — WDNR
surveys each inland lake roughly every 10-20 years, not annually. Aggregating
weather to the outcome's own resolution therefore gives at most 1-2 outcome
data points per lake per weather predictor. The original Lake Michigan
methodology requires a minimum of 4 overlapping years before even attempting
a leave-one-out regression, because fitting fewer points is either
mathematically degenerate (n=1) or a meaningless perfect fit through exactly
2 points (n=2). So weather-based transposition was correctly not forced into
a model at all, for any of the 11 lakes.

### 4b. What was tested: within-season species-level effort share vs. harvest rate

Every creel report gives 8-16 real, already-extracted per-species rows
within a single lake-season (share of angling effort directed at each
species vs. that species' harvest rate). This is the only predictor-outcome
pair in the dataset with enough real data points per lake to run an actual
held-out regression, so it was used instead of weather, with that deviation
disclosed rather than presented as the original plan. A known caveat was
flagged before results were read: effort share and harvest rate share a
common `directed_effort_hours` term, so any relationship found carries a
partial mechanical component — the same structural concern the original
Lake Michigan report raised for angler-effort-vs-harvest-rate.

Five candidate pairs, matched by step 2's physical/trophic similarity
groupings, were tested in both directions (ten directional fits total):
Sand↔Pine, Minocqua↔Pelican, Lake Wisconsin↔Petenwell, Lake
Wisconsin↔Wissota, and Petenwell↔Wissota. Four other lakes (Devils, Sawyer,
White Potato, Big Green) were correctly excluded from pairing — each has
only one surveyed season, and none forms a physically credible match with
another single-season lake without forcing a weak comparison.

**Result: in every one of the ten directional tests, the source lake's own
fitted relationship was statistically indistinguishable from noise** — |r|
between 0.008 and 0.547, p between 0.127 and 0.979, none clearing even an
uncorrected p<0.05 bar. Six of the ten transposed predictions nominally beat
the target lake's own naive baseline on raw MAE, but this cannot be read as
evidence of a working transfer. Here is why that distinction is real, not
semantic: a fitted line with r near 0 and p near 1 is, in every practical
sense, close to flat — it predicts close to a constant near the source
lake's own mean, regardless of the target lake's actual data. Landing closer
to the target's true values than the target's own leave-one-out-mean
baseline can happen by chance with small samples (n=9-16) and heavy-tailed
species distributions, where a single high-effort species can pull a
same-sized baseline around more than a near-constant prediction does. **You
cannot transfer a relationship that was never shown to exist on the source
lake in the first place** — so none of the six "nominally beats baseline"
results is attributable to a real, transferable predictor-outcome
relationship, and none is reported as one.

**No pair in this analysis produced a source-side relationship with real,
held-out-defensible statistical signal that could be honestly credited with
improving predictions on the paired lake. No validated transposition pair
was found anywhere in this cycle.**

---

## 5. Step 4 — explicitly not performed

Decision #008 conditions step 4 — proposing an untested extrapolation of a
validated cross-lake relationship to lakes lacking outcome data, such as
Pewaukee or Delavan — on step 3 first validating at least one transposition
pair. Step 3 validated none. **Per that conditional rule, step 4 was not
performed in this cycle.** No candidate lake is proposed as a transfer
source for Pewaukee, Delavan, or any other outcome-data-lacking lake.
Proposing one informally "just in case," despite step 3's negative result,
would represent an untested extrapolation as more than it is and would
violate Decision #005.

---

## 6. What this means going forward

Two distinct outcomes came out of this cycle and should not be conflated:

**(a) The inventory is a genuine, standalone success, independent of the
transposition result.** 11 additional Wisconsin inland lakes now have real,
extracted, sourced creel data where V0 previously had zero. That data exists
regardless of whether cross-lake transfer ever works, and is a real
improvement to the project's data foundation.

**(b) The open question this cycle set out to answer — can a
predictor-outcome relationship transfer between similar lakes — was not
resolved, and importantly, was not disproven either.** The negative result
in Section 4 is honest and real for what was actually tested (within-season
species-effort-share vs. harvest-rate, at the only sample size available).
But the weather-based version of this question — arguably the more directly
useful one, since weather is what would need to transfer to predict
Pewaukee or Delavan's conditions day-to-day — could not be tested at all, at
any statistical power, because WDNR's inland-lake survey cadence (1-2
seasons per lake, ever) does not produce enough outcome data points to fit
even a single held-out regression. This is a structural data-availability
limitation, the same category of problem the original V0 report identified
for Pewaukee/Delavan/Geneva's total absence of outcome data — not a finding
that transfer is impossible.

---

## 7. Recommendations for CEO consideration

These are options for CEO consideration, not decisions made by this report.

1. **The 11 newly-found lakes are themselves candidates for direct
   (non-transferred) prediction work**, independent of the transposition
   question, for any lake with enough within-lake data points to support a
   real regression — worth a scoping pass to identify which, if any, meet
   that bar on their own (most likely candidates given today's data:
   Minocqua, Pelican, Pine, and Sand, the four with two survey seasons each,
   though even those are only 2 points at the season level).
2. **Whether to invest in years of additional inland-lake creel data over
   time.** WDNR's ~10-20 year periodic survey cycle means several of these
   11 lakes are plausible candidates for a third survey sometime in the
   2030s, which would be the first real path to a same-lake time series
   comparable to what made the Lake Michigan evaluation possible.
3. **Whether cross-lake transfer is worth revisiting once more inland lakes
   accumulate multiple survey seasons**, or once a predictor is identified
   that does not share a denominator term with the outcome variable (the
   structural caveat flagged in Section 4b) — this cycle's negative result
   does not close the door on the question, it just could not clear it with
   today's data.
4. **The Winnebago 2012 Yellow Perch Creel Survey should be retried** with a
   tool capable of executing the hosting page's JavaScript viewer, before
   concluding Winnebago has no usable creel data — it is currently blocked,
   not confirmed unavailable.
5. **Pewaukee and Delavan specifically remain in the same position the
   original V0 report left them**: no outcome data of their own, and now
   also no validated cross-lake transfer path found to substitute for one.
   Any future proposal to predict conditions on either lake still needs
   either real outcome data for that lake, or a validated transposition pair
   that does not yet exist.

---

*End of report. Per CLAUDE.md's hard-stop instruction, no further pipeline
action (STATE.md update, commit, or acting on any recommendation above) has
been taken. Awaiting CEO review and explicit approval.*
