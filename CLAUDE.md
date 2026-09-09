# fishin — V1: Lake Michigan Salmon Movement-Prediction MVP

## Mission
Predict Lake Michigan salmon movement patterns — proximity to shore,
presence in rivers/tributaries, and likely depth — from historical GLATOS
acoustic telemetry data paired with environmental conditions. This is a
deliberate scope narrowing from V0's broader creel-based catch-rate work,
per DECISIONS.md #010. Inland lakes and every other V0 track (Decisions
#007-#009) are explicitly out of scope for now.

## Scope
- **Water body:** Wisconsin waters of Lake Michigan only. No inland lakes,
  no other states, no other regions, without a future CEO decision to
  resume them.
- **Dependent variable:** GLATOS (Great Lakes Acoustic Telemetry
  Observation System) detection data for Lake Michigan salmon (species per
  actual GLATOS coverage — Chinook, Coho, or whichever the data confirms) —
  position, and depth/temperature where tag sensors provide it. This
  replaces creel-based catch rate as the outcome measure.
- **Goal:** predict salmon proximity to shore, presence in rivers/
  tributaries, and likely depth, from historical telemetry patterns plus
  environmental predictors (water temperature, season, etc.).
- **Explicitly out of scope by default:** real-time individual-fish
  location tracking or prediction. Tagged research fish location data can
  create poaching pressure, and data-sharing agreements commonly restrict
  this. Only historical/aggregate pattern-based prediction is assumed
  viable unless GLATOS's actual terms confirm otherwise.

## Current phase — investigation only, no modeling yet
Per DECISIONS.md #010, the next required step is investigating real GLATOS
data access (public download vs. data-use agreement) and confirming
species/depth/temperature coverage for Lake Michigan salmon specifically.
**Do not begin modeling, and do not acquire GLATOS data, until this
investigation is complete and CEO-reviewed.**

## Standing discipline (carries forward from V0, unchanged)
- No data acquisition, modeling, or claims beyond what's tested and
  held-out-validated (DECISIONS.md #005)
- No action past a draft/investigation stage without explicit CEO review
- Simple, interpretable models only unless a CEO decision says otherwise
  (DECISIONS.md #002)
- Leakage-safe, time-aware evaluation splits; deterministic tests for all
  data-prep and evaluation logic
- No STATE.md update, no commit, no action on any recommendation past a
  report/investigation draft without explicit CEO approval — same hard-stop
  gate used throughout V0
