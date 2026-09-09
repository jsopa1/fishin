# fishin — MVP: Wisconsin Conditions & Biology Forecast

## Mission
Deliver a statewide Wisconsin "conditions & biology" forecast: an
informational, per-lake narrative combining live/current water temperature
with established fish physiology thresholds and confirmed species presence.
**This is explicitly not a validated catch-rate prediction** — per
DECISIONS.md #012, it does not reopen or contradict V0's finding that
catch-rate prediction was not demonstrated. GLATOS/telemetry work
(DECISIONS.md #011) and inland pooled catch-rate modeling (DECISIONS.md
#008/#009) are deferred, not in scope.

## Scope
- **Water bodies:** any Wisconsin lake, not limited to a specific region —
  the tool's inputs (live water temp, physiology thresholds, stocking
  records) are queryable per-lake on demand, not tied to a fixed pilot
  geography like V0 was.
- **Inputs — all real, live/current data, never historical-lag:**
  1. **Current/forecast water temperature** — WDNR Citizen Lake Monitoring
     Network (CLMN) where available for that lake; NWS/NOAA weather-service
     data otherwise (air temperature as a proxy, or a nearby buoy/gauge for
     Lake Michigan).
  2. **Established fish physiology thresholds** — reused from
     `docs/v0_physiology_research_candidates.md` (spawning triggers,
     activity temperature windows, by species). Reference data, not
     re-derived or re-validated here.
  3. **WDNR fish stocking records** — confirm which species are actually
     present in a given lake before generating any narrative about them. No
     stocking/presence record, no narrative for that species on that lake.
- **Output:** a per-lake informational narrative, e.g. *"water temperature
  is currently in the range associated with walleye spawning activity."*
  Every output must be explicitly labeled as general, science-based
  seasonal context — never as a personalized or validated catch
  prediction (DECISIONS.md #005).
- **Explicitly out of scope:** GLATOS/telemetry data or modeling
  (DECISIONS.md #011); any claim of predicted catch rate or catch
  probability; inland pooled catch-rate modeling (V0, negative result).

## Standing discipline (carries forward, unchanged)
- No claim beyond what live/current data and the cited physiology sources
  actually support (DECISIONS.md #005)
- No action past a draft/prototype stage without explicit CEO review
- Simple, interpretable logic only — this is a lookup/threshold-comparison
  tool, not a predictive model, so no model-validation claims apply, but
  the same "don't overstate" discipline applies to every narrative string
  produced
- No STATE.md update, no commit, no action on any recommendation without
  explicit CEO approval — same hard-stop gate used throughout V0 and V1
