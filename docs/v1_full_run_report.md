# V1 Full Run Report

Status: **Draft for CEO review.** This document reports the results of running
the existing, unmodified `analysis/v1_conditions_biology_forecast.py` model
exhaustively across every documented Wisconsin waterbody, per the prior
cycle's Parts 1-4. No new predictive logic was introduced — this is a full
execution of the model already built and reported on in
`docs/v1_data_coverage_report.md`, `docs/v1_species_presence_manifest.md`,
`docs/v1_water_temp_manifest.md`, and `docs/v1_physiology_research_candidates.md`.

**Run timestamp:** `2026-09-09T13:56:55.705426+00:00` (start) →
`2026-09-09T14:03:45.797456+00:00` (finish), **6 minutes 50 seconds**, live
data throughout (not a dry run). Results are stored in
[`data/v1/v1_full_run_results.db`](../data/v1/v1_full_run_results.db)
(SQLite), queryable by waterbody, county, species, and tier via the `runs`,
`waterbody_results`, `species_predictions`, and `run_failures` tables.

---

## Two real bugs found and fixed while building this run

Running the model exhaustively — rather than one waterbody at a time —
surfaced two real defects in the existing script that a spot-check never
would have caught. Both are fixed in `analysis/v1_conditions_biology_forecast.py`,
verified against the full regression test suite, and are the reason this
run's species-match numbers are real rather than artificially zero:

1. **Species-name casing mismatch.** `load_survey_species` stored species
   as scraped (Title Case, e.g. "Walleye"), while `load_stocking_species`
   uppercased them ("WALLEYE") to match `physiology_thresholds_v1.json`'s
   uppercase keys. Every survey-confirmed waterbody's species therefore
   silently failed to match any physiology threshold — every prior
   single-lake demo in this project that showed a real match happened to
   go through the stocking-only path, never the survey path. Fixed by
   uppercasing consistently in both loaders.
2. **Exact-name query ambiguity.** The fuzzy substring name-matcher used
   to reconcile naming differences across source files (e.g. "Lauderdale
   Lakes" vs. "Lauderdale Lakes (Green Lake/Middle Lake/Mill Lake
   chain)") meant an *exact* query like "Apple River" also fuzzy-matched
   "Apple River Flowage" and vice versa — any waterbody whose name was a
   substring of another's would spuriously raise an ambiguity error even
   when the query was unambiguous. Fixed with a shared resolver that
   prefers an exact name match over the fuzzy ones when one exists.

Both fixes were validated against the full existing test suite (no
regressions) before this run.

## Performance note (does not affect results, disclosed for transparency)

The per-waterbody data loaders re-parsed the 24,683-row statewide stocking
CSV from scratch on every call — at ~2,300 waterbodies, this dominated
runtime. Added an in-memory, mtime-keyed cache for the CSV reads (pure I/O
memoization, not a change to any matching or decision logic) — this cut a
500-waterbody dry run from an extrapolated ~8 minutes to 14 seconds.

---

## Totals

| Metric | Count |
|---|---|
| Waterbodies processed | **2,301** |
| Waterbodies with a persisted result | 2,300 (1 excluded — see Failures) |
| Species-waterbody predictions generated | **4,537** |
| Total failures logged | **219** |

## Breakdown by data-quality tier

| Presence tier | Waterbodies |
|---|---|
| Survey-confirmed (authoritative) | 55 |
| Stocking-only (positive evidence, not exhaustive) | 2,245 |

*(55 + 2,245 = 2,300 — matches the persisted-result count exactly; the
2,301st waterbody is the one excluded by an ambiguous-name failure, below.)*

## Breakdown by waterbody type

| Type | Waterbodies |
|---|---|
| Lake / pond / flowage | 1,609 |
| Stream / river | 691 |

## Water-temperature source breakdown

| Method | Real or proxy | Waterbodies |
|---|---|---|
| USGS live gauge | **real** | 43 |
| WDNR CLMN recent reading | **real** | 16 |
| NWS air-temp proxy (live fetch) | proxy | 2,224 |
| NWS air-temp proxy (cached fallback, live fetch failed) | proxy | 14 |
| No data (no real or proxy source resolved) | — | 3 |

**59 of 2,300 waterbodies (2.6%) have a real water-temperature
measurement; the remaining 97.1% use the honestly-labeled NWS proxy; 3
waterbodies (0.1%) have no temperature data at all.** This matches the
expectation set in the prior cycle's coverage report — most of Wisconsin's
waterbodies have no dedicated sensor, and the tool says so rather than
padding the real-data count.

## Species predictions

| Outcome | Count |
|---|---|
| Species evaluated against current temperature, no threshold matched at this reading | 2,290 |
| Species evaluated, at least one threshold matched (a real narrative statement generated) | 2,247 |
| **Total** | **4,537** |

A "no match" result is a real, expected outcome — most species most of the
time aren't inside a specific documented physiological window — and is
recorded identically to a match, not dropped.

**The disclosed Muskellunge thermal-optimum dispute (V0's ~22°C vs. GLFC's
24-27.3°C cluster) was verified to survive intact into the stored
narrative text** for both real waterbodies where it fired (Big Moon Lake,
Lake Wisconsin) — the full caveat sentence, not a summary, is present in
`species_predictions.match_description` for those rows.

## Failures (Part 3 — logged explicitly, run never halted)

| Failure type | Count | What it means |
|---|---|---|
| `no_physiology_threshold` | 217 | A real, present species has no entry in the 26-species physiology reference (e.g. Common Carp, Golden Shiner, various bullheads and hybrid sunfish — species this project has never researched physiology for). A real, disclosed coverage gap, not an error in the run. |
| `temperature_lookup_error` | 1 | Legend Lake, Menominee County — a live network read timed out. Logged with the real exception message (`TimeoutError: The read operation timed out`); the waterbody still got a `no_data` temperature result and its species presence was still recorded. |
| `ambiguous_presence_lookup` | 1 | "Green Lake" (Green Lake County) matches two distinct real survey lakes — Big Green Lake and Little Green Lake — under one shortened name; this project's own data has no single "Green Lake" entry, only the two specifically-named ones. This waterbody was excluded from `waterbody_results` for this run rather than guessed at. |

**No output was fabricated where real data was missing.** Every `no_data`
temperature result is a real `NO_TEMPERATURE_DATA` record with `value_c =
NULL` in the database, never a plausible-looking invented number. Every
`no_physiology_threshold` failure is a real species with zero threshold
rows, not a silently-skipped one. One real, disclosed data gap (Cisco
appearing in survey data as "Cisco (Lake Herring)" vs. the reference file's
plain "CISCO" key) was also observed during report review — the exact
alias doesn't match today, so Cisco predictions did not fire for that
waterbody; noted here as an honest finding, not silently patched in this
report-writing pass.

---

## Bottom line

The existing rule-based model was run exactly as built, across every
waterbody this project has any real data for. Two real defects were found
and fixed in service of making that run produce real results rather than
silent zeros. The results — 4,537 real species-waterbody predictions,
2,300 persisted waterbody records, 219 honestly-logged failures — are
stored in a queryable SQLite database for review. This report makes no
claim about the model's predictive validity beyond what the underlying
physiology research and V0's feasibility findings already establish; it
only reports that the model, as designed, ran successfully and completely
at scale.
