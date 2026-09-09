# V1 Data Coverage Report (Part 4)

What [`analysis/v1_conditions_biology_forecast.py`](../analysis/v1_conditions_biology_forecast.py)
actually covers today, by data-quality tier, with the source backing each
row and whether species presence is survey-confirmed or stocking-only. This
is the honest floor of the tool's current coverage — everything not listed
here is explicitly "no data," not silently assumed.

## Lakes covered (23 total: 22 real-survey lakes + 1 bonus)

| Lake | County | Species tier | Water temp: method | Water temp: real or proxy |
|---|---|---|---|---|
| Camelot Lake | Adams | survey-confirmed | CLMN recent | **real** |
| Spider Lake | Ashland | survey-confirmed | NWS proxy | proxy (CLMN station stale, 29 yrs) |
| Big Moon Lake | Barron | survey-confirmed | CLMN recent | **real** |
| Diamond Lake | Bayfield | survey-confirmed | NWS proxy | proxy |
| Upper/Lower Clam Lake | Burnett | survey-confirmed | NWS proxy | proxy |
| Lake Wisconsin | Columbia/Sauk | survey-confirmed | CLMN recent | **real** |
| Fish Lake | Dane | survey-confirmed | NWS proxy | proxy (CLMN station stale, 12 yrs) |
| Beaver Dam Lake | Dodge | survey-confirmed | CLMN recent | **real** |
| Big Green Lake | Green Lake | survey-confirmed | NWS proxy | proxy |
| Little Green Lake | Green Lake | survey-confirmed | NWS proxy | proxy |
| Blackhawk Lake | Iowa | survey-confirmed | NWS proxy | proxy |
| Rock Lake | Jefferson | survey-confirmed | CLMN recent | **real** |
| Lake DuBay | Marathon/Portage | survey-confirmed | NWS proxy | proxy |
| Bass Lake | Oconto | survey-confirmed | CLMN recent | **real** |
| Pelican Lake | Oneida | survey-confirmed | CLMN recent | **real** |
| Devils Lake | Sauk | survey-confirmed | CLMN recent | **real** |
| Shawano Lake | Shawano | survey-confirmed | NWS proxy | proxy |
| Dead Pike Lake | Vilas | survey-confirmed | NWS proxy | proxy |
| Lauderdale Lakes | Walworth | survey-confirmed | CLMN recent | **real** |
| Stone Lake | Washburn | survey-confirmed | NWS proxy | proxy |
| White Lake | Waupaca | survey-confirmed | NWS proxy | proxy |
| Fish Lake | Waushara | survey-confirmed | NWS proxy | proxy |
| Lake Monona *(bonus)* | Dane | **stocking-only** (Muskellunge, Northern Pike) | USGS live | **real, live** |

**Water temperature: 10 of 23 lakes (43%) have a real measurement** (9 real
CLMN recent readings + 1 live USGS gauge); **13 of 23 (57%) fall back to a
live NWS air-temperature proxy**, always explicitly labeled as such in the
script's output — never blended with real readings. Six of the 13 proxy
lakes actually have a CLMN station on file, but its only reading is stale
(9-29 years old) — the script's own `--no-live-refresh`-off default always
prefers a live proxy fetch over a stale cached one for those lakes; see
[`docs/v1_water_temp_manifest.md`](v1_water_temp_manifest.md) for the
per-lake detail and exact staleness.

**Species presence: 22 of 23 lakes (96%) are survey-confirmed** (real WDNR
electrofishing/netting data — the authoritative source). Lake Monona is the
sole stocking-only exception, and the script's output for it explicitly
states presence is "POSITIVE evidence only, NOT a complete species
inventory" per the presence-classification rule in
[`docs/v1_species_presence_manifest.md`](v1_species_presence_manifest.md).

## Physiology reference coverage

**26 species** have at least one usable numeric threshold in
[`data/v1/physiology_thresholds_v1.json`](../data/v1/physiology_thresholds_v1.json),
sourced from [`docs/v1_physiology_research_candidates.md`](v1_physiology_research_candidates.md).
Every species actually observed across the 22 survey lakes or confirmed via
the statewide stocking pull that has real literature coverage is in this
file — species present in the real data but explicitly out of scope for
physiology coverage (bullheads, Common Carp, Golden Shiner, hybrid
sunfish/crappie categories) are named in the research doc's own "Notes for
next steps" section as a disclosed gap, not silently dropped.

One species (Muskellunge) carries a **disclosed, unresolved disagreement**
between two real sources (22°C vs. 24-27.3°C thermal optimum) rather than a
single collapsed number — the script's threshold range spans both and its
generated narrative text says so explicitly whenever it fires.

## What's explicitly "insufficient data" (not silently omitted)

- **~2,316 of the 2,338 Wisconsin waterbodies** in the statewide stocking
  pull have stocking-only species data and no water-temperature data at
  all in this project — running the script against any of them raises a
  clear `ValueError` ("No water-temperature data... on file"), not a
  fabricated value.
- **Any Wisconsin lake outside both the stocking pull and the 22-lake
  survey sample** has zero data of any kind — `get_species_presence()`
  returns `{"tier": "no_data", ...}` and the generated narrative says so in
  plain language, never silently produces an empty-but-plausible-looking
  report.
- **Lake-name collisions** (two real "Fish Lake"s in Dane and Waushara
  counties) require `--county` to disambiguate — the script raises
  `AmbiguousLakeError` rather than silently picking one, guarding against
  a real bug this project's own data surfaced during Part 4 testing (see
  the test suite's `TestSpeciesPresence.test_ambiguous_lake_name_raises_without_county`
  and the `_lake_name_matches` docstring for the related 813-blank-row fix).
- **6 of 13 NWS-proxy lakes** have a real but stale CLMN reading on file
  (9-29 years old) — these are named individually above and in
  `docs/v1_water_temp_manifest.md`, not glossed over as simply "no CLMN
  data."

## Deterministic test coverage (Part 4 requirement)

[`analysis/tests/test_v1_conditions_biology_forecast.py`](../analysis/tests/test_v1_conditions_biology_forecast.py)
(32 tests, all passing) covers exactly the four areas Part 4 specified:
threshold-matching correctness (range/point/avoidance-above matching,
boundary inclusivity, the disputed-Muskellunge-range case), species
filtering (survey-confirmed-takes-priority, stocking-only fallback,
the real Fish-Lake-name-collision and blank-waterbody bugs this project's
own data surfaced and which are now regression-tested), water-temperature
fallback labeling (real vs. proxy, and the cache-reason wording difference
between `--no-live-refresh` and a failed live attempt), and
insufficient-data handling (missing lake raises `ValueError`, `no_data`
tier never fabricates a species section). 109 tests pass project-wide.
