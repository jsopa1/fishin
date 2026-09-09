# fishin — V1: Wisconsin Conditions & Biology Forecast

**Canonical phase overview:** [ROADMAP.md](ROADMAP.md). Check that file
first for current phase status (V0-V4); this file covers V1's working
scope and standing discipline in detail, and DECISIONS.md carries the full
rationale trail for every scope change.

## Mission
Deliver a statewide Wisconsin "conditions & biology" forecast: an
informational, per-lake narrative combining real current/recent water
temperature with established fish physiology thresholds and confirmed
species presence. **This is explicitly not a validated catch-rate
prediction** — per DECISIONS.md #012, it does not reopen or contradict
V0's finding that catch-rate prediction was not demonstrated. GLATOS/
telemetry work (DECISIONS.md #011) and inland pooled catch-rate modeling
(DECISIONS.md #008/#009) are deferred, not in scope.

## Scope (expanded statewide + rivers/streams per DECISIONS.md #013/#014)
- **Water bodies:** lakes, ponds, rivers, and streams. Two evidentiary
  tiers, both surfaced (never just the stronger one hidden behind the
  other):
  - **Survey-confirmed** (authoritative): real WDNR fisheries-survey data
    for a growing set of lakes (22 original + any found in
    `docs/v1_survey_expansion_report.md`) — see
    `docs/v1_data_coverage_report.md` for the current exact count.
  - **Stocking-only** (positive evidence, not a complete inventory): the
    ENTIRE statewide WDNR stocking pull, ~2,338 waterbodies including 690
    real stream/river waterbodies, per Decision #014 — not a hand-picked
    subset.
  - Any waterbody outside both sets returns an explicit `no_data` result,
    never a fabricated one.
- **Implementation:** `analysis/v1_conditions_biology_forecast.py`
  (supersedes `mvp/conditions_forecast.py`).
- **Inputs — all real data, never fabricated or silently estimated:**
  1. **Current/recent water temperature**, in priority order: a live USGS
     gauge (185 real WI sites: 177 streams + 8 lakes,
     `data/v1/usgs_wi_water_temp_sites.csv`, generic name-matched at
     runtime — the primary real-time source for streams specifically); a
     real recent WDNR CLMN reading for the original 22 lakes; a live NWS
     air-temperature proxy everywhere else, always explicitly labeled as
     a proxy, never blended with a real measurement; honest `no_data` if
     none of the above resolves.
  2. **Established fish physiology thresholds** — `docs/v1_physiology_research_candidates.md`
     (26 species), structured in `data/v1/physiology_thresholds_v1.json`.
     Reference data, not re-derived or re-validated here. Real
     disagreements between sources (e.g. Muskellunge's thermal optimum)
     are disclosed, not collapsed to one number. **Lake-derived
     feeding/growth thresholds are explicitly flagged as unverified when
     applied to a stream/river entry** (Decision #014) — spawning-trigger
     data is not flagged the same way, since much of it is already
     stream-relevant in the literature gathered.
  3. **Species presence** — real WDNR fisheries-survey data where it
     exists (authoritative), falling back to the full statewide WDNR
     stocking pull used as **positive-only** evidence — a species absent
     from stocking records is NOT treated as absent (self-sustaining
     populations are often stocked less, not more). See
     `docs/v1_species_presence_manifest.md`.
- **Output:** a per-waterbody informational narrative, e.g. *"water
  temperature is currently in the range associated with walleye spawning
  activity."* Every output must be explicitly labeled as general,
  science-based seasonal context — never as a personalized or validated
  catch prediction (DECISIONS.md #005).
- **Explicitly out of scope:** GLATOS/telemetry data or modeling
  (DECISIONS.md #011); any claim of predicted catch rate or catch
  probability; inland pooled catch-rate modeling (V0, negative result).

## Standing discipline (carries forward, unchanged)
- No claim beyond what real data and the cited physiology sources actually
  support (DECISIONS.md #005)
- No action past a draft/prototype stage without explicit CEO review
- Simple, interpretable logic only — this is a lookup/threshold-comparison
  tool, not a predictive model, so no model-validation claims apply, but
  the same "don't overstate" discipline applies to every narrative string
  produced
- No STATE.md update, no commit, no action on any recommendation without
  explicit CEO approval — same hard-stop gate used throughout V0 and V1
