# Decisions

## 001 — Validate before productizing

We will validate the fishing prediction before building a polished consumer application.

## 002 — No assumption that ML is necessary

We will use the simplest model that performs well. Potential approaches include rules, statistical models, logistic regression, random forest, gradient boosting, and other ML. An LLM is not automatically the prediction model.

## 003 — $0 initial budget

Prefer free APIs, open datasets, open-source software, and free infrastructure.

## 004 — Human approval for major decisions

Agents may research, implement, test, and document. The CEO approves major product, architecture, financial, and strategic decisions.

## 005 — Evidence over appearances

The system must never represent an arbitrary score as scientifically validated.

## 006 — GitHub/Copilot as operating model instead of autonomous agents

The company operates via GitHub as the durable source of truth, with CEO setting objectives and Copilot executing disciplined work through GitHub Issues and PRs.

**Rationale:**
- GitHub is widely understood and provides version control, audit trail, and durable memory
- Human-in-the-loop model (CEO → Issues → Copilot → PRs → Approval → Merge) reduces risk of autonomous mistakes
- PR review and CEO approval gates ensure major decisions are visible and approved
- Moving away from OpenHands SDK simplifies dependencies and reduces framework lock-in
- Copilot executes focused, evidence-based work following lightweight role definitions (RESEARCH.md, DATA_SCIENCE.md, ENGINEERING.md, QA.md, DOCUMENTATION.md)
- No separate autonomous agent orchestration framework—Copilot is the single execution engine

## 007 — V0 pilot geography: southeast Wisconsin / Lake Michigan

The V0 prediction-feasibility pilot is scoped to southeast Wisconsin, starting with:

- **Lake Michigan** (Milwaukee/Racine/Kenosha nearshore waters)
- **Lake Winnebago** (Winnebago County)
- **Pewaukee Lake** (Waukesha County)
- **Delavan Lake** (Walworth County)
- **Geneva Lake** (Walworth County)

Counties in scope: Milwaukee, Waukesha, Racine, Kenosha, Walworth, Winnebago.

**Rationale:**
- Concentrates limited $0-budget data-gathering effort on a small, well-instrumented region rather than spreading thin nationally
- Southeast Wisconsin has strong public data coverage (USGS gauges, NOAA/Great Lakes buoy and weather data, WDNR fishing/stocking records) to test the feasibility hypothesis
- Lake Michigan and inland lakes together give both a large-lake and small-lake test case within one pilot
- Out of scope for V0: any other state, region, or water body not listed above; expansion is a future-phase decision requiring CEO approval

## 008 — Expand V0 inland-lake search beyond Pewaukee/Delavan/Geneva

The V0 feasibility report found that WDNR does not creel-survey Pewaukee
Lake, Delavan Lake, or Geneva Lake — no real angler catch/harvest-rate
outcome data exists for any of the three, so prediction could not be tested
there. Rather than abandon the inland-lake question, V0's inland-lake search
is expanded to any Wisconsin inland lake with real, extractable creel survey
data, not limited to southeast Wisconsin — with the explicit goal of testing
whether a predictor-outcome relationship learned on one lake with real data
transfers to a similar lake, including lakes (like Pewaukee and Delavan)
that still have no outcome data of their own.

**Rationale:**
- The original three lakes were chosen for regional concentration (Decision
  #007), not because they were confirmed to have creel data — that
  assumption did not hold, per the V0 feasibility report
- Widening the inland-lake search statewide is the direct, evidence-driven
  fix for a data-availability gap, not a scope expansion for its own sake
- This does not change or reopen the Lake Michigan findings and conclusions
  already reported in `docs/V0_FEASIBILITY_REPORT.md` — those stand as
  reported
- Per Decision #005, any cross-lake transfer of a predictor-outcome
  relationship must be held-out tested wherever real outcome data exists on
  both lakes being compared, before it is proposed as a basis for predicting
  a lake that has no outcome data of its own; where it cannot be tested, it
  must be labeled an untested extrapolation, not a validated result

## 009 — Test established fisheries science (physiology/behavior) as a candidate-predictor class

V0's weather/lake-characteristics predictors and its cross-lake transfer
test both came back negative (Decisions #008, and the pooled inland-lake
predictability analysis). Before concluding the outcome data itself lacks a
detectable signal, V0 will test one more candidate-predictor class:
established, well-evidenced fish physiology and behavior science (e.g.
temperature-driven feeding/activity windows, diel movement, spawning
behavior, species-specific metabolic thresholds) for the species already
present in the project's real outcome data (walleye, salmonids, panfish,
etc.).

This addresses a specific hypothesis: that angler skill/effort noise in
creel data may be masking a real physiological signal that weather and lake
characteristics — being once removed from actual fish behavior — could not
capture. This is a new candidate-predictor class to evaluate, not a
replacement for the outcome data already gathered, and physiological
plausibility is not assumed to translate into a detectable catch-rate
signal without a real held-out test.

**Rationale:**
- Per Decision #005, no predictor — however well-established in the fish
  physiology literature — is treated as a validated catch-rate predictor
  until tested against the project's real outcome data with the same
  leave-one-out, baseline-comparison discipline used throughout V0
- A positive result (physiology-derived predictors beat baseline where
  weather/characteristics did not) would be a genuine new lead supporting
  the angler-skill-noise hypothesis; a negative result would suggest the
  skill/effort confound was not the actual bottleneck, and that the null
  results found so far more likely reflect a real absence of detectable
  signal or a data-availability limit than a masking effect — either
  outcome is useful and must be reported as such, not adjusted toward a
  preferred conclusion

## 010 — V1 Scope: Lake Michigan Salmon MVP

The project is pivoting from creel-based catch-rate prediction to a Lake
Michigan salmon movement-prediction MVP. **This is a deliberate scope
narrowing, not an expansion.** Inland lakes and every other track explored
under V0 (Decisions #007-#009) are explicitly out of scope for now — not to
be resumed without a future CEO decision to do so.

- **Dependent variable:** GLATOS (Great Lakes Acoustic Telemetry Observation
  System) acoustic telemetry detection data — position, and depth/
  temperature where tag sensors provide it — for Lake Michigan salmon
  (Chinook, Coho, or whichever species GLATOS coverage actually confirms).
  This replaces creel-based catch rate as the outcome measure, per the
  resolution and ground-truth problems documented across V0 (see
  `docs/V0_FEASIBILITY_REPORT.md`, `docs/v0_lake_transfer_report.md`,
  `docs/v0_inland_predictability_results.md`, and
  `docs/v0_physiology_predictors_report.md` — no single "final conclusion"
  document currently exists in the repo under that name; these four reports
  together are the documented basis for this pivot).
- **Goal:** predict salmon proximity to shore, presence in rivers/
  tributaries, and likely depth, based on historical telemetry patterns
  paired with environmental conditions (water temperature, season, etc.).
- **Real-time individual-fish location tracking is explicitly out of scope
  by default.** Tagged research fish location data can create poaching
  pressure, and data-sharing agreements commonly restrict this. Only
  historical/aggregate pattern-based prediction is assumed viable unless
  GLATOS's actual terms confirm otherwise.
- **Next required step before any modeling begins:** investigate real
  GLATOS data access (public download vs. data-use agreement) and confirm
  species/depth/temperature coverage for Lake Michigan salmon specifically.
  Do not begin modeling until this is confirmed and CEO-reviewed.
- All prior CEO-approval-gate discipline carries forward unchanged: no data
  acquisition, modeling, or claims beyond what's tested and
  held-out-validated, and no action past a draft/investigation stage
  without explicit CEO review.

**Rationale:**
- Creel-survey outcome data proved structurally limited across every V0
  track tried: too coarse in resolution (seasonal/annual, no trip-level
  timestamp) to test even well-evidenced predictors like walleye's diel
  light-driven catchability; too sparse for inland lakes (1-2 surveyed
  seasons ever per lake); and entangled with angler skill/effort in ways
  that couldn't be separated from any real environmental or physiological
  signal
- GLATOS telemetry measures the fish directly (position, and depth/
  temperature where sensors provide it) rather than what anglers reported
  catching, removing the angler-skill/effort confound entirely and giving
  a resolution (individual detections) far finer than any creel survey
  could provide
- Per Decision #005, GLATOS's real data-access terms and actual species/
  sensor coverage for Lake Michigan salmon must be confirmed before any
  acquisition or modeling — this decision authorizes investigation only,
  not data acquisition or modeling

## 011 — GLATOS Deferred to Future Upcycle

Investigation of GLATOS (Great Lakes Acoustic Telemetry Observation System)
per Decision #010 surfaced structural problems with the data that go beyond
the access/coverage questions that investigation set out to answer:

- **GLATOS acoustic telemetry data is not real-time.** Receivers are
  stationary, deployed on the lake bottom, and must be physically retrieved
  and downloaded periodically. Detection histories available for analysis
  are inherently retrospective — months to a year or more old — not a live
  feed. A movement-prediction MVP built on this data would be predicting
  from data already substantially out of date at the time it's used.
- **Coverage is inconsistent over time.** Transmitter battery life ranges
  from a few months to ten years, so which fish are trackable shifts
  continuously as tags expire and new tagging projects begin. A detection
  gap in the record can mean the tag failed, not that the fish left the
  area — a real confound that would need to be modeled or ruled out before
  any absence-of-detection could be treated as a movement signal.
- **Individual fish behavior adds further noise on top of the above.**
  Predation, food availability, and individual variation all affect a
  single tagged fish's movement, layered on top of the retrospective-data
  and coverage-inconsistency problems — a harder modeling problem than the
  creel-data confounds already documented across V0 (Decisions #007-#009).

**Decision: GLATOS/telemetry work is deferred to a future project upcycle.
Not abandoned — documented here for future reference.** No telemetry data
acquisition or modeling is in current scope. See Decision #012 for the
project's current scope in light of this deferral.

**Rationale:**
- Per Decision #005, a movement-prediction MVP cannot be honestly built on
  data that is structurally retrospective and inconsistently covered
  without first solving problems (data-lag correction, tag-failure vs.
  absence disambiguation) that are themselves substantial research
  questions, not implementation details
- Documenting the deferral (rather than silently dropping it) preserves the
  investigation's findings for whoever picks this track back up, and
  distinguishes "deferred, evidence-based" from "abandoned, unexamined"

## 012 — MVP Scope: Statewide Wisconsin Conditions & Biology Forecast

Following Decision #011's deferral of GLATOS/telemetry work, the project's
current MVP scope is a statewide Wisconsin **"conditions & biology"
forecast** — explicitly **not** a validated catch-rate prediction.

**This does not reopen or contradict the V0 finding that catch-rate
prediction is not demonstrated** (see `docs/V0_FEASIBILITY_REPORT.md`,
`docs/v0_lake_transfer_report.md`, `docs/v0_inland_predictability_results.md`,
and `docs/v0_physiology_predictors_report.md` — no single "final
conclusion" document exists in the repo under that name; these four reports
together are V0's documented conclusion). It delivers a different,
honestly-scoped kind of value instead: real-time seasonal/biological
context, not a prediction of whether an angler will catch a fish.

**Inputs — all real and live/current, not historical-lag data:**
- **(a) Current/forecast water temperature** — WDNR Citizen Lake
  Monitoring Network (CLMN) where available for a given lake, NWS/NOAA
  weather-service data otherwise (e.g. air-temperature-based estimation, or
  a nearby buoy/gauge for Lake Michigan)
- **(b) Established fish physiology thresholds** already compiled in
  `docs/v0_physiology_research_candidates.md` (spawning triggers, activity
  temperature windows, by species) — reused as reference data, not
  re-derived
- **(c) WDNR fish stocking records**, to confirm which species are actually
  present in a given lake before reporting anything about them — a lake
  with no record of a species being stocked or naturally present should not
  get a narrative about that species

**Output:** an informational narrative per lake — e.g., *"water
temperature is currently in the range associated with walleye spawning
activity"* — explicitly labeled as general, science-based seasonal
context, **not** a personalized or validated catch prediction, per
Decision #005.

**Out of scope:** GLATOS/telemetry (Decision #011) and inland pooled
catch-rate modeling (Decisions #008/#009, V0's negative results) remain
deferred/out of scope for this MVP. This tool does not predict catch rate,
does not claim a fish will bite, and does not represent any output as
scientifically validated beyond what the cited physiology sources and
live/current conditions data actually support.

**Rationale:**
- Per Decision #005, this scope is chosen specifically because it can be
  built entirely from claims already honestly sourced (V0's physiology
  research) and real, live, current data — no predictive model whose
  accuracy would need to be claimed or validated is involved
- All prior CEO-approval-gate discipline carries forward unchanged

## 013 — V1 expanded statewide: additional data sources, deeper physiology research, and ROADMAP.md as canonical phase overview

Following Decision #012's MVP scope, V1's data foundation is expanded from
a single-lake demo to real, sourced coverage across 23 Wisconsin lakes, and
[`ROADMAP.md`](ROADMAP.md) is established as the canonical, always-current
summary of project phases (V0-V4) going forward — this decisions log
remains the detailed rationale trail, but ROADMAP.md is the place to check
current phase status at a glance.

**What changed:**
- **New data sources catalogued** (`docs/v1_source_discovery_report.md`):
  WDNR fisheries-survey "Comprehensive Summary Report" PDFs (real observed
  species composition, not just stocking), a live USGS water-temperature
  gauge (Lake Monona), the GLOS Seagull API (Lake Michigan nearshore
  water quality), NTL-LTER, and several others — each verified real and
  accessible, not assumed.
- **Species-presence data expanded statewide**
  (`docs/v1_species_presence_manifest.md`): a real statewide WDNR stocking
  pull (24,683 records, 2011-2025, 2,338 waterbodies) plus a real,
  geographically-diverse 22-lake fisheries-survey sample. Per Decision
  #012's own instruction, stocking records are used as **positive-only**
  evidence of presence — never as evidence of absence — and survey data is
  treated as authoritative when it exists for a lake.
- **Physiology research expanded from 12 to 26 species**
  (`docs/v1_physiology_research_candidates.md`, superseding the V0-era
  document), re-verified against a primary Great Lakes Fishery Commission
  compilation (Wismer & Christie 1987) fetched and read in full this
  cycle. Real disagreements between sources (e.g. Muskellunge's thermal
  optimum) are disclosed, not collapsed to a single convenient number, per
  Decision #005.
- **Real current/recent water temperature pulled for all 23 lakes**
  (`docs/v1_water_temp_manifest.md`): live USGS and recent WDNR CLMN
  readings where they exist (10 of 23 lakes), an explicitly-labeled live
  NWS air-temperature proxy everywhere else — never blended or presented
  with false confidence.
- **`analysis/v1_conditions_biology_forecast.py`** supersedes
  `mvp/conditions_forecast.py` as the working implementation, with 32
  passing deterministic tests (109 project-wide) covering threshold
  matching, survey-vs-stocking presence classification, real-vs-proxy
  temperature labeling, and explicit "insufficient data" handling — no
  silent failures.

**Rationale:**
- Breadth (more lakes, more species) was pursued without lowering the
  evidentiary bar used throughout this project — every new source was
  checked for real accessibility before being relied on, and gaps are
  logged explicitly rather than papered over (Decision #005)
- Consolidating phase status in `ROADMAP.md` gives a single, always-current
  answer to "what phase is this project in and what's its status," while
  this decisions log remains the record of why each phase change happened
- This cycle does not reopen or change the V0 findings
  (`docs/V0_FEASIBILITY_REPORT.md` and its three follow-on reports) or the
  GLATOS deferral (Decision #011) — it is scoped entirely to deepening
  V1's already-approved conditions-and-biology scope (Decision #012)
