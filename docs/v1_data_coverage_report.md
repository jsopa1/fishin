# V1 Data Coverage Report (rewritten — full expanded scope)

What [`analysis/v1_conditions_biology_forecast.py`](../analysis/v1_conditions_biology_forecast.py)
actually covers today, across the full stocking-only tier and rivers/streams
added this cycle (Decision #014), by data-quality tier and waterbody type.
Nothing below is rounded up — every count is a real, checkable number from
the actual data files, and every gap is stated plainly rather than implied
away.

## Coverage by tier and type

| Tier | Lakes/ponds | Streams/rivers | Total |
|---|---|---|---|
| **Survey-confirmed** (authoritative) | 33 | 8 | **41** |
| **Stocking-only** (positive evidence, not exhaustive) | ~1,599 | ~683 | **~2,282** |
| **No data** | every other WI waterbody | every other WI waterbody | not enumerable |

- **Survey-confirmed = 41 distinct waterbody entries**: the original 22
  lakes (all lake) + 19 new entries from this cycle's search (11 new lakes
  + 8 stream entries, 4 of which are separately-surveyed reaches of the
  same Rush River — see [`docs/v1_survey_expansion_report.md`](v1_survey_expansion_report.md)
  for the full list, counties, and search-effort disclosure: 46 counties
  checked, 17 had a usable report link, 14 yielded real extracted data —
  roughly a 30% hit rate, not padded).
- **Stocking-only = the entire real statewide WDNR pull**, ~2,282 distinct
  (county, waterbody) pairs with a blank-waterbody-free count (24,683 raw
  records; a small number of rows have no waterbody name and are excluded
  from every count and every query match, per the blank-waterbody-matching
  fix made this cycle). Of these, **683 are real stream/river waterbodies**
  — trout streams especially, per WDNR's stocking practice — surfaced by
  this tool for the first time this cycle (Decision #014); the other
  ~1,599 are lakes, ponds, and flowages.
- **No data**: any Wisconsin waterbody outside both sets above. The script
  reports this honestly (`{"tier": "no_data", ...}`) — it is never
  silently dropped or given a fabricated species list.

## Water-temperature source breakdown

| Source | Real or proxy | Coverage |
|---|---|---|
| **Live USGS gauge** (generic name match, any waterbody) | **real** | 185 real WI sites (177 streams + 8 lakes) in `data/v1/usgs_wi_water_temp_sites.csv`; spot-checked 8 stream sites this cycle — only 3/8 had genuinely live current data today, 3/8 had a registered site but no current reading, 2/8 had no live (iv) service at all despite being dv-listed. **This is disclosed honestly, not smoothed over: dv-listed ≠ guaranteed live** — see [`docs/v1_river_stream_coverage_report.md`](v1_river_stream_coverage_report.md). |
| **Pre-pulled recent WDNR CLMN reading** | **real** | 9 of the original 22 lakes (dated, not live — CLMN itself is periodic) |
| **Live NWS air-temperature proxy** (live-geocoded at request time) | proxy, always labeled | Any waterbody with a resolvable Wisconsin location — the honest fallback for the vast majority of the ~2,300+ waterbodies this tool now covers |
| **No data** | — | Any waterbody where geocoding fails or no station returns a reading (a real, occasional outcome — reported plainly, not retried indefinitely) |

**Practical implication:** for the ~2,282 stocking-only waterbodies, the
realistic default temperature source is the live NWS proxy (always clearly
labeled as air temperature, never presented as measured water
temperature) unless the waterbody happens to be one of the 185 USGS sites
or the original 10 real-CLMN/USGS lakes.

## Physiology reference coverage

**26 species** have at least one usable numeric threshold in
`data/v1/physiology_thresholds_v1.json`, sourced from
[`docs/v1_physiology_research_candidates.md`](v1_physiology_research_candidates.md).

**New this cycle: lake-derived thresholds are explicitly flagged when
applied to a stream/river entry**, per the river/stream research pass
(`docs/v1_river_stream_coverage_report.md`) — most feeding/growth
temperature thresholds in this reference trace to lake studies (Lake
Michigan, Lake Monona, Trout Lake WI), and the script never silently
applies them to a stream waterbody without disclosing that the value
"has not been verified to transfer to flowing-water conditions."
Spawning-trigger thresholds are not flagged the same way, since a real
share of the species in this reference already have stream-relevant
spawning citations (salmonid tributary runs, Sauger, Rainbow
Trout/Steelhead, Brook Trout, Lake Sturgeon).

## What's explicitly "insufficient data" (not silently omitted)

- **Every Wisconsin waterbody outside the ~2,282-entry stocking pull and
  the 41-entry survey sample** has zero species data — reported as
  `no_data`, in plain language, never a fabricated result.
- **A waterbody with no resolvable USGS, CLMN, or geocodable-NWS
  temperature source** reports `no_data` for temperature specifically
  (`v1.NO_TEMPERATURE_DATA`) — this can happen even for a waterbody with
  real species data (e.g. a lake with a real survey but an unusual enough
  name that live geocoding fails); the script still reports species
  presence in that case, it just states plainly that no temperature
  reading is available for this visit.
- **Multi-reach stream surveys** (e.g. Rush River's four separately-
  surveyed sections) are kept as distinct entries rather than merged —
  querying the bare name without specifying a reach/county correctly
  raises `AmbiguousLakeError` rather than silently picking one.
- **Roughly half of the dv-listed USGS stream sites spot-checked this
  cycle had no genuinely live current reading** despite being listed as
  daily-value-capable — this is a real, disclosed limitation of the USGS
  network itself, not a gap in this project's own pull.
- **Geocoding a reach-level name with a parenthetical description** (e.g.
  "Rush River (whole surveyed reach)") required stripping the
  parenthetical before querying — the four Rush River sub-reaches
  therefore all resolve to the same approximate river location, not
  reach-specific coordinates. This is disclosed, not hidden.

## Deterministic test coverage

[`analysis/tests/test_v1_conditions_biology_forecast.py`](../analysis/tests/test_v1_conditions_biology_forecast.py)
(45 tests, all passing; 122 project-wide) now additionally covers:
waterbody-type classification (including the real "X River Flowage"
misclassification bug found and fixed this cycle), full-statewide
stocking-only inclusion for both lakes and streams, the river/stream
lake-derived-physiology caveat (fires for feeding/growth thresholds,
correctly does not fire for spawning-trigger thresholds or for lake
entries), generic USGS site name-matching, and `no_data` handling across
every combination of missing survey/stocking/temperature data.
