# Current State

## Current Objective

Predict Lake Michigan salmon movement (proximity to shore, presence in rivers/tributaries, likely depth) from historical GLATOS acoustic telemetry data paired with environmental conditions.

## Phase

V1 — Lake Michigan Salmon MVP, investigation stage. Per DECISIONS.md #010, this is a deliberate scope narrowing from V0's broader creel-based catch-rate work — inland lakes and every other V0 track are deferred, not abandoned, pending a future CEO decision to resume them.

## Scope (V1)

Wisconsin waters of Lake Michigan only. Outcome measure is GLATOS telemetry detection data (position, depth/temperature where sensors provide it) for Lake Michigan salmon — replacing creel-based catch rate. Real-time individual-fish location tracking is out of scope by default (poaching-pressure risk; data-sharing agreements commonly restrict it) unless GLATOS's actual terms confirm otherwise. See CLAUDE.md and DECISIONS.md #010 for full scope.

**Next required step before any modeling begins:** investigate real GLATOS data access (public download vs. data-use agreement) and confirm species/depth/temperature coverage for Lake Michigan salmon specifically. No data acquisition or modeling until this is confirmed and CEO-reviewed.

## Repository Status

✅ Refactored from OpenHands-centric to GitHub/Copilot-centric operating model
✅ V0 (creel-based catch-rate prediction) run to completion across four research cycles — concluded, findings documented, scope now deferred per Decision #010
🔲 V1 (Lake Michigan salmon MVP via GLATOS) — investigation stage, not yet started

**V0 work completed (deferred, not deleted — reports remain the evidentiary basis for the V1 pivot):**
- Refactor: operating manual (COPILOT.md), lightweight role definitions (agent-roles/), removed OpenHands SDK, cleaned up agent_system/
- Added CLAUDE.md pipeline definition and `.claude/agents/` role subagents (now superseded by the V1 CLAUDE.md scope)
- **V0 pilot (Decision #007):** research (19 candidates) → dataset build → baseline → evaluation → report. Only Lake Michigan had real matched outcome+predictor data; no candidate showed real signal for salmonid harvest rate; one statistically notable but causally uncertain result for yellow perch vs. wave height (r=0.865, p=0.001, n=10). Pewaukee/Delavan/Geneva had no creel data at all. — [docs/V0_FEASIBILITY_REPORT.md](docs/V0_FEASIBILITY_REPORT.md)
- **Decision #008 cycle:** statewide inland-lake search found 11 additional WI lakes with real creel data; cross-lake predictor transposition tested across 5 pairs/10 directional fits — no validated transfer pair found. — [docs/v0_lake_transfer_report.md](docs/v0_lake_transfer_report.md)
- **Pooled inland predictability cycle:** tested whether weather + lake-characteristics data (pooled across all 11 inland lakes, leave-one-lake-out CV) predicts harvest rate at all — no, 0 of 10 lake-level and 0 of 3 species-level models beat baseline. — [docs/v0_inland_predictability_results.md](docs/v0_inland_predictability_results.md)
- **Decision #009 physiology cycle:** tested established fish physiology/behavior science (17 candidates researched) against real outcome data — a cleaner null than the weather test (0 of 12 tests reached even uncorrected p<0.05); argues against, not for, the angler-skill-noise-masking hypothesis. The best-evidenced candidate (walleye diel/light-window feeding) was untestable — no trip-level timestamps exist in any creel data used. — [docs/v0_physiology_predictors_report.md](docs/v0_physiology_predictors_report.md)
- **Decision #010:** pivot to V1 Lake Michigan salmon MVP via GLATOS telemetry, replacing creel-based catch rate as the outcome measure — see DECISIONS.md #010 and CLAUDE.md.

## Active Work

None — V1 investigation (GLATOS data access and coverage) has not yet started. Awaiting CEO direction to begin it.

## Blocked

None.

## Decisions Needed

- CEO to authorize the V1 investigation step: confirming real GLATOS data access terms (public download vs. data-use agreement) and species/depth/temperature coverage for Lake Michigan salmon
- Longer-term (not urgent): what, if anything, to do with the deferred V0 inland-lake track and its four reports/datasets — no action needed now per Decision #010

## Recent Findings

V0's creel-based catch-rate track is closed out (not deleted) as of Decision #010. Across every predictor class and every water body tested — Lake Michigan weather/wave/pressure, statewide inland-lake weather/characteristics, cross-lake transfer, and established fish physiology/behavior science — no candidate produced a real, held-out-validated signal beyond one causally-uncertain Lake Michigan result (wave height vs. yellow perch, r=0.865, p=0.001, n=10, unreplicated). The recurring structural bottleneck across all four cycles was the outcome data itself: WDNR creel surveys are seasonal/annual aggregates with no trip-level timestamp, which made even the single best-evidenced physiological mechanism found (walleye's diel light-driven catchability) impossible to test. This is the direct evidentiary basis for Decision #010's pivot to GLATOS telemetry, which measures the fish's position and depth directly rather than relying on angler-reported, coarsely-aggregated catch data.

## Next Recommended Action

1. CEO: Authorize the V1 GLATOS investigation step (see Decisions Needed above)
2. Copilot: Investigate real GLATOS data access and Lake Michigan salmon coverage; report back before any modeling begins — no data acquisition or modeling without CEO review of that investigation

**V1 has not started modeling or data acquisition — investigation only, pending CEO authorization.**

## Human Attention Required

CEO should authorize the next step (GLATOS access/coverage investigation) when ready. No report review is currently pending — the four V0 reports above are informational background for the pivot, already reflected in Decision #010.

---

*Note: This file is maintained collaboratively by CEO and Copilot. Each completed work item or decision updates this file. Copilot updates STATE.md in the final PR of each work item.*
