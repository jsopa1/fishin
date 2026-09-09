# Current State

## Current Objective

Validate whether fishing conditions can be predicted using public data.

## Pilot Geography (V0)

Southeast Wisconsin, starting with: Lake Michigan (Milwaukee/Racine/Kenosha nearshore), Lake Winnebago, Pewaukee Lake, Delavan Lake, and Geneva Lake. Counties: Milwaukee, Waukesha, Racine, Kenosha, Walworth, Winnebago. See DECISIONS.md #007. Any water body or region outside this list is out of scope for V0 without CEO approval.

## Phase

V0 — Prediction Feasibility

## Repository Status

✅ Refactored from OpenHands-centric to GitHub/Copilot-centric operating model
✅ V0 prediction-feasibility pipeline run end-to-end for the pilot geography (research → dataset build → baseline → evaluation → report)
✅ Inland-lake search expanded statewide (Decision #008) and cross-lake predictor transfer tested

**Completed:**
- Created comprehensive operating manual (COPILOT.md)
- Created lightweight role definitions (agent-roles/)
- Removed OpenHands SDK dependencies and infrastructure
- Cleaned up agent_system/ (kept only context utility)
- Updated README.md, pyproject.toml, DECISIONS.md
- Updated .env.example (removed deprecated credentials)
- All remaining tests pass
- Added CLAUDE.md pipeline definition and `.claude/agents/` role subagents (predictor-research, pdf-extraction, predictor-eval, feasibility-report)
- Step 1 (research): 19 candidate predictors identified — [docs/v0_research_candidates.md](docs/v0_research_candidates.md)
- Step 2 (dataset build): real outcome + predictor data assembled for Lake Michigan (2013–2024); confirmed no creel/catch-rate outcome data exists for Pewaukee, Delavan, or Geneva — [docs/v0_dataset_manifest.md](docs/v0_dataset_manifest.md), data under `data/v0/`
- Steps 3–4 (baseline + evaluation, Lake Michigan only): 7 candidates tested against a historical-mean baseline across 2 outcomes; analysis code + tests under `analysis/` — [docs/v0_evaluation_results.md](docs/v0_evaluation_results.md)
- Step 5 (report): full V0 feasibility report — [docs/V0_FEASIBILITY_REPORT.md](docs/V0_FEASIBILITY_REPORT.md)
- Decision #008 research cycle: statewide inland-lake inventory found 11 additional WI lakes with real, extracted creel data — [docs/v0_inland_lake_inventory.md](docs/v0_inland_lake_inventory.md); all 14 relevant lakes physically/limnologically characterized — [docs/v0_lake_characteristics.md](docs/v0_lake_characteristics.md); cross-lake predictor transposition tested across 5 pairs/10 directional fits, no validated transfer pair found — [docs/v0_transposition_results.md](docs/v0_transposition_results.md); full write-up — [docs/v0_lake_transfer_report.md](docs/v0_lake_transfer_report.md)

## Active Work

None — both the original V0 pipeline and the Decision #008 inland-lake transfer cycle are complete for this pass, awaiting CEO review of both reports and a decision on next step.

## Blocked

None.

## Decisions Needed

CEO review of `docs/V0_FEASIBILITY_REPORT.md` and `docs/v0_lake_transfer_report.md`, and a decision on how to proceed, specifically:
- Whether to find an alternative outcome-data source for Pewaukee/Delavan/Geneva (no WDNR creel data exists for them, and no validated cross-lake transfer path was found to substitute for one either), drop them from V0 scope, or substitute other WDNR-creel-surveyed waterbodies (11 new candidates now inventoried — see below)
- Whether to pursue more Lake Michigan history/higher-resolution (monthly) outcome data to get real statistical power
- Whether to pull the not-yet-obtained predictors (cloud cover, precipitation, inland weather station data) before treating them as ruled out
- How to treat the one statistically notable but causally uncertain Lake Michigan finding (yellow perch harvest rate vs. wave height, r=0.865, p=0.001, n=10) — it needs replication before being used for anything user-facing
- Whether to pursue direct (non-transferred) prediction work on any of the 11 newly-found inland lakes, invest in years of additional inland-lake creel data over time, or retry the blocked Lake Winnebago 2012 Yellow Perch Creel Survey (JS-viewer-blocked, not confirmed unavailable) — see `docs/v0_lake_transfer_report.md` §7

## Recent Findings

- **No creel/catch-rate outcome data exists for Pewaukee, Delavan, or Geneva lakes** — WDNR does not creel-survey these waterbodies. This is a data-availability gap, not a negative predictive-signal finding.
- **Lake Winnebago** has real WDNR trawl-abundance data (1986–2023) but that measures fish abundance, not angler catch rate — a different question than V0 set out to answer, so it was not substituted in as an outcome. A genuine 2012 Winnebago *creel* survey was later found to exist but is blocked behind a JS PDF viewer (not yet extracted).
- **Lake Michigan** (WI waters), the only waterbody with real matched outcome + predictor data: of 7 candidates tested against a historical-mean baseline (2013–2024, 9–12 annual data points), none showed real signal for the primary outcome (salmonid harvest rate). One candidate — wave height vs. yellow perch harvest rate — showed a statistically strong but causally uncertain result (r=0.865, p=0.001, counter to the a-priori hypothesized direction, small n) flagged as a lead requiring replication, not a validated finding.
- **Decision #008 cycle:** widening the inland-lake search statewide found 11 additional Wisconsin lakes with real, extracted creel data (Minocqua, Pelican, Devils, Big Green, Lake Wisconsin, Petenwell, Pine, Sand, Sawyer, Wissota, White Potato) — a genuine improvement to the project's data foundation. However, the core question — does a predictor-outcome relationship transfer between similar lakes — came back negative: across 5 candidate pairs (10 directional held-out tests), no validated transposition pair was found; weather-based transfer could not even be tested due to inland lakes having only 1-2 creel-survey seasons ever (WDNR surveys them every ~10-20 years, not annually). As a result, extrapolating a transferred relationship to Pewaukee or Delavan was explicitly not attempted, per the cycle's own conditional rule and Decision #005.
- Full detail, caveats, and recommendations are in `docs/V0_FEASIBILITY_REPORT.md` and `docs/v0_lake_transfer_report.md`.

## Next Recommended Action

1. CEO: Review `docs/V0_FEASIBILITY_REPORT.md` and `docs/v0_lake_transfer_report.md` and decide next step (see Decisions Needed above)
2. Copilot: Await CEO direction before pursuing any of the recommendations in either report

**Pipeline paused at the CEO approval gate — do not act on any report recommendation until CEO decides.**

## Human Attention Required

CEO should review both the V0 feasibility report (`docs/V0_FEASIBILITY_REPORT.md`) and the inland-lake transfer report (`docs/v0_lake_transfer_report.md`) and decide how to proceed, per the options above.

---

*Note: This file is maintained collaboratively by CEO and Copilot. Each completed work item or decision updates this file. Copilot updates STATE.md in the final PR of each work item.*

