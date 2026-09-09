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

## Scope (expanded statewide per DECISIONS.md #013)
- **Water bodies:** 23 real Wisconsin lakes with actual pulled data today
  (22 real, geographically-diverse survey lakes + Lake Monona) — see
  `docs/v1_data_coverage_report.md` for the exact per-lake breakdown.
  Species-presence data (stocking-only, positive-evidence-only) additionally
  covers 2,338 Wisconsin waterbodies statewide via the real WDNR stocking
  pull; any lake outside these sets returns an explicit "no data" result,
  never a fabricated one.
- **Implementation:** `analysis/v1_conditions_biology_forecast.py`
  (supersedes `mvp/conditions_forecast.py`).
- **Inputs — all real data, never fabricated or silently estimated:**
  1. **Current/recent water temperature** — a live USGS gauge or a real
     recent WDNR CLMN reading where one exists (10 of 23 lakes); a live
     NWS air-temperature proxy everywhere else, always explicitly labeled
     as a proxy, never blended with a real measurement.
  2. **Established fish physiology thresholds** — `docs/v1_physiology_research_candidates.md`
     (26 species, supersedes the V0-era 12-species document), structured
     for the script in `data/v1/physiology_thresholds_v1.json`. Reference
     data, not re-derived or re-validated here. Real disagreements between
     sources (e.g. Muskellunge's thermal optimum) are disclosed, not
     collapsed to one number.
  3. **Species presence** — real WDNR fisheries-survey data
     (`data/v1/wi_fisheries_survey_species_sample.csv`) where it exists for
     a lake (authoritative), falling back to real WDNR stocking records
     (`data/v1/wi_stocking_statewide_2011_2025.csv`) used as
     **positive-only** evidence — a species absent from stocking records is
     NOT treated as absent from the lake (self-sustaining populations are
     often stocked less, not more). See `docs/v1_species_presence_manifest.md`.
- **Output:** a per-lake informational narrative, e.g. *"water temperature
  is currently in the range associated with walleye spawning activity."*
  Every output must be explicitly labeled as general, science-based
  seasonal context — never as a personalized or validated catch
  prediction (DECISIONS.md #005).
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
