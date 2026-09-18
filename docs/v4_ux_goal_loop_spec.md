# V4 UX redesign — approved goal-loop spec

Approved by the CEO after review. Companion to [v4_ux_redesign_plan.md](v4_ux_redesign_plan.md) (the original plan); where the two differ, **this spec wins** — it resolves the open decisions the plan flagged (ranking = disclosed deterministic heuristic using Profile preferences; anonymous Profile; deep habitat/bait research; public-domain images; variable bait count; Explore screen built as its own phase).

Wireframes: [../UX/](../UX/) (all five wireframes are in that folder).

---

## Context

`docs/v4_ux_redesign_plan.md` (committed) plans a navigation redesign from
5 wireframes (`UX/`): Recommended home, redesigned Spot Detail
(Active/Inactive fish), new Fish Detail (habitat, bait), new Profile
(preferences), 3-icon bottom nav. This plan is the `/goal` directive plus
the fully specified rules the loop follows, so nothing is left to
improvisation. CEO decisions already made:

- **Ranking: Option A** — a disclosed, deterministic heuristic (never a
  "score" or prediction; DECISIONS.md #005/V0 stand). It uses the user's
  Profile preferences.
- **Profile: anonymous-first** (`localStorage`), no accounts in this loop.
- **Research: habitat and bait as deep as the species research**
  (`docs/v1_physiology_research_candidates.md` is the bar).
- **Images: public domain only**, each verified and attributed.
- Standing rule: data sources must be refreshable weekly or be excluded
  (memory: data-source-weekly-freshness-bar) — applies to any new source.

## The goal loop directive (run via `/goal`)

> continue implementing the V4 UX redesign (docs/v4_ux_redesign_plan.md and
> the approved plan's specs) phase by phase — Phase 0 research (habitat,
> bait catalog, public-domain images), then Fish Detail, Spot Detail
> redesign, the Explore (map/list + filters) screen, anonymous Profile,
> and the Recommended home screen with the fully specified deterministic
> ranking, plus the 3-icon nav — verifying each phase live in the
> browser and with the full test suite before committing; never fabricate
> research, images or citations; stop and ask only if a step would reopen
> the V0 catch-prediction question, require real user accounts, or use an
> image whose public-domain status cannot be verified — otherwise keep
> going until all phases ship

## Phase 0 — Research (blocks Fish Detail; runs first)

### Scope
All 27 species in `physiology_thresholds_v1.json`. Today bait data covers
only 11 (`bait_technique_reference_v1.json`); missing: Burbot, Channel
Catfish, Chinook, Cisco, Coho, Fathead Minnow, Freshwater Drum, Lake
Sturgeon, Lake Trout, Lake Whitefish, Pumpkinseed, Rock Bass, Sauger, White
Bass, White Crappie, White Sucker. Classify each species up front as
*angling target* vs *not an angling target* (e.g. Fathead Minnow, Cisco,
likely White Sucker): non-targets get an explicit "not an angling target"
record — never invented bait.

### Method (mirrors the species research)
1. Re-read `docs/v1_physiology_research_candidates.md`,
   `docs/v1_bait_technique_research_report.md` and the existing bait JSON
   first; carry forward what is already established.
2. Source hierarchy. Tier 1: Becker 1983 *Fishes of Wisconsin*, Scott &
   Crossman 1973, WDNR species/fisheries-management publications and lake
   survey reports, USGS/USFWS species profiles, GLFC publications, MN/MI/ON
   agency profiles, AFS journals/handbooks, diet (stomach-content) studies,
   university extension/Sea Grant. Tier 2 (angling convention only): agency
   angler-education and extension material. Excluded (logged, never used):
   tackle-maker marketing, forums, videos, unsourced blogs.
3. Habitat fields per species (season/life-stage tagged): structure and
   cover, depth ranges with units and context, substrate, flow/current
   (river species), oxygen/clarity tolerance, spawning habitat, seasonal
   movement, forage association, Wisconsin lake-class suitability. Each
   claim: value, units, ≥1 full citation (author, year, title, publisher,
   URL/DOI, page/table), evidence tier, Wisconsin-applicability flag
   (studied in WI/Great Lakes vs elsewhere), disagreements disclosed not
   collapsed.
4. Evidence tiers reuse the existing four labels (well-established =
   ≥2 independent sources agree; agency-tier; single-source-speculative;
   excluded-as-folklore) so the UI tag vocabulary does not change.
5. Bait modeling, keeping the two claim types separate as
   `v1_bait_technique.py` already enforces: **forage/diet basis** (from diet
   studies — research tier) vs **angling application** (convention tier).
   Build a shared **bait catalog** (~40-60 deduped items: id, name,
   category, description, how-to-use incl. depth/retrieve/rig, water types)
   plus a **species→bait map** with per-thermal-state applicability
   (`in_activity_window`, `below_activity_window`, `in_spawning_trigger`,
   `above_avoidance`), rationale, tier, sources. **Wisconsin bait
   regulations** (live baitfish/VHS/invasive rules, NR 19/20) recorded per
   item, or an explicit "not researched" reason — a bait card must never
   suggest something illegal on some waters without a note.
6. Variable bait count: each species gets as many or as few bait entries as
   the research supports — could be 2, could be 12; the wireframe's three
   cards are illustrative, not a limit or a target. Nothing is padded to
   reach a number and nothing is cut to fit one. Cards for the current
   thermal state are ordered deterministically by (link evidence tier,
   count of independent sources, fixed editorial `rank` stored in the data
   file) — no runtime choice. "All documented baits" lists every mapped
   item across all states. A species with only one documented bait shows
   one card.
7. Execution: batch by family (percids; centrarchids; esocids; salmonids;
   catfish/sturgeon/other) with a fixed template; one commit per batch.
   QA pass after each batch: re-open the source for every 5th claim
   (deterministic sample, not random) and confirm the number/claim; log
   retrieval failures like the CCRR-17 precedent — a claim whose source
   cannot be re-verified is downgraded or dropped, never kept on trust.
8. Honesty gate: a field that cannot reach agency-tier shows "Not yet
   documented to our standard", never a partial guess.

### Deliverables
- `docs/v4_habitat_bait_research_candidates.md` (method, tiers,
  per-species tables, disagreements, failed retrievals, exclusions,
  summary counts — same shape as the V1 species doc)
- `data/v1/habitat_reference_v1.json`, `data/v1/bait_catalog_v1.json`,
  `data/v1/species_bait_map_v1.json`
- Schema tests: every claim has ≥1 non-empty citation and an allowed tier;
  every one of the 27 species has a habitat entry or explicit "not
  documented"/"not an angling target"; every mapped bait id exists; every
  bait has a regulation note or reason; no `biological_basis` text ever
  rendered as `angling_application`.

### Public-domain images
Candidate sources: USFWS National Digital Library, USGS, state-agency
public-domain sets, Wikimedia Commons files tagged public domain. Verify
the license on the source page itself; record source URL, author, license,
retrieval date in `data/v1/image_manifest_v1.json`; store under
`webapp/static/img/species/` and `.../baits/`. No verifiable PD image →
honest no-image state, never a substitute. Test: every manifest entry has a
URL + PD license string; every shipped image file is in the manifest.

## Phase 1 — Fish Detail (`GET /fish/<species>`)
`get_species_detail()` in `ui/v1_review_data.py` composes: physiology
thresholds (Documented Activity, reusing `_short_evidence_label` /
`_activity_for_species`), habitat data, bait cards (deterministic order
above), image or no-image state. Template `fish_detail.html`. Reuse the
shared tag popover (`tags-explainer.js`, `data-explain`) for evidence
tags. Link target of every species row in later phases.

## Phase 2 — Spot Detail redesign
Extend `build_species_categories()` to bucket top-level by
`activity.inside_window` (Active green / Inactive yellow); keep the
Confirmed/Likely evidence tier as a per-row badge (not dropped). Rows link
to `/fish/<species>`. Spawning-trigger matches are shown in Active with a
"spawning range — check regulations" note. Keep the Stocking / Regulations
/ Consumption Advisory buttons.

## Phase 2b — Explore screen (map icon destination)
Built explicitly, not just reused. Starting point is `map.html` at `/map`,
which already has the Map/List toggle, the filter form
(`.explore-filters`: waterbody, county, species, source type) and
`/map/data`. Wireframe 5 differs in layout: the **Map | List toggle comes
first, then the Filters, then the content area**; today the filters sit
above the toggle. Work:
- Reorder markup: header logo → Map|List toggle → Filters → map or list
  pane. Mobile-first; filters collapsible behind a "Filters" control so the
  map/list gets the screen (keep every existing filter and its query-param
  behavior, including deep links like `/map?waterbody=...`).
- List mode is sorted by the same deterministic key as Recommended
  (Phase 4's `rank_spots_for_recommendation()` used with the active
  filters; disclosure line shown above the list whenever sorted that way;
  alphabetical remains available as an explicit "Sort: A–Z" option).
- Filters can be pre-filled from Profile preferences (spot types,
  species) but never silently — a visible "Using your preferences" chip
  the user can clear.
- Tapping a pin or list card goes to Spot Detail; the toggle state and
  filters persist when returning via the nav.
- Keep `/browse` (directory) reachable from a link inside Explore so no
  existing capability is lost when the 5-item nav collapses.
- Tests: route renders toggle before filters; every prior filter still
  works; list order equals the ranking function's order; deep links from
  the old nav still resolve. Live browser check at mobile width.

## Phase 3 — Profile (anonymous)
`profile.html`; `localStorage` keys `fishin.prefs.spotTypes.v1`
(per type: Prefer / OK / Avoid — covers both the toggle and slider
readings of the wireframe), `fishin.prefs.species.v1` (species I target),
`fishin.prefs.maxDistance.v1` (max travel distance, default 50 mi);
dark/light via `data-theme` override over existing `prefers-color-scheme`;
"Guest" state (no username/member-since); Rate us / Help / Documentation
links. Update `privacy.html` (see Privacy below) and its cross-check test.

## Phase 4 — Recommended home + ranking (fully specified)

**Endpoint:** `POST /recommend` (JSON, read-only, no state change, no
cookies; exempt from CSRF for that reason, documented). Body: optional
rounded `lat/lon` (2 decimals, ~1 km), `types` prefs, `species` targets,
`max_km`, `saved` spots (cap 20). Returns ordered `saved` and
`recommended` lists plus the disclosure string. Pure function
`rank_spots_for_recommendation()` so it is unit-testable with no network.

**Deterministic pipeline (no randomness anywhere):**
1. *Candidates (cheap, one SQL):* `access_points` joined to latest
   `waterbody_results` / `species_predictions` (`any_match`,
   `evidence_quality`, `presence_tier`, `temp_is_real`). Bounding-box then
   `_haversine_km` filter to `max_km`. `Avoid`-type spots excluded.
2. *Prelim rank* all candidates by the sort key below, keep top 25.
3. *Exact recompute* for those 25 with the same path the spot page uses
   (`get_spot_detail`), then final sort by the same key so a card never
   disagrees with its spot page (test enforces card count == spot page).
4. *Display* top 10.

**Sort key (lexicographic tuple, descending unless noted) — chosen over
numeric weights so no arbitrary weights are invented:**
1. `n_target_in_window` — count of the user's target species currently in
   their documented window at this spot (if no targets set: total
   in-window species count). Spawning-trigger matches are excluded from
   this count (shown on the card but never used to rank, since many WI
   seasons are closed then).
2. `n_confirmed_in_window` — of those, how many are in the Confirmed
   bucket (survey or citizen sighting) rather than Likely.
3. `type_preferred` — 1 if the spot type is marked Prefer.
4. `temp_quality` — real > estimated > proxy.
5. `distance_km` ascending (only when location is known).
6. `(waterbody_name, facility_name)` ascending — final stable tiebreak.

**Edge cases fixed in advance:**
- *No preferences:* all species equal, all types equal.
- *No location permission:* no radius filter, no distance key; list is the
  statewide top by keys 1-4; card says "Enable location to see distance".
- *Nothing in window anywhere (e.g. ice season):* key 1 falls back to
  smallest °C distance to a documented window (reuse `_window_distance_c` /
  `rank_species_by_proximity`); card wording changes to "closest to its
  window".
- *Too few results:* widen radius by ladder 50 → 100 → 200 km → statewide,
  and disclose the radius used. Preferences never produce an empty list:
  if target species match nothing, show spots ranked by total in-window
  count under a banner "none of your target species are in range right
  now".
- *Stale data:* reuse the existing stale banner; ranking still runs and
  says how old the data is.
- *Saved spots:* same key, no radius filter, all shown.
- *Deliberately not ranking inputs* (each stays "not used in the match"):
  wind, pressure, moon, sunrise/sunset windows, regulations. Loop must
  not add them.
- *Card content:* "likely to bite" lines are limited to the user's target
  species that are in window; if none set, the top in-window species by
  the same key (evidence tier, then alphabetical). Wording is the app's
  existing phrasing ("in documented window"), never "likely to bite"
  unless the disclosure is adjacent and the rule is stated — wireframe
  wording is adapted to "in range now" to stay inside DECISIONS.md #005.
- *Performance budget:* recompute ≤ 25 spots; measure p95 < 1.5 s locally;
  if exceeded, cache results per (run_timestamp, prefs-hash) for 15 min.

**Disclosure (always shipped, never droppable):** "Ranked by how many of
your target species are inside their documented temperature range right
now, then evidence strength, spot-type preference, reading quality and
distance. This is not a prediction of catch success." Includes the radius
used and which preferences were applied.

**Bottom nav:** collapse `base.html` from 5 items to 3 (last-spot /
Explore / Profile), fish-logo header link → `home`; last-spot uses new
`localStorage` `fishin.lastSpot.v1` written on each `/spot` visit.
Explore = Phase 2b's screen. Nav change done last, once all destinations
exist. (Phase order: 0 → 1 → 2 → 2b → 3 → 4; Phase 2b's ranked list mode
lands after Phase 4's function exists, until then it ships A–Z and is
switched over in Phase 4.)

## Privacy / honesty
Geolocation is new. Location is rounded to ~1 km client-side, sent only in
the `/recommend` request body, never stored or logged (analytics records
path only — verified in `webapp/app.py::_log_pageview`). Update
`privacy.html` and its code-cross-check test accordingly.

## Critical files (reuse, don't rebuild)
`ui/v1_review_data.py` (`_activity_for_species`, `build_species_categories`,
`_window_distance_c`, `rank_species_by_proximity`, `get_spot_detail`,
`_haversine_km`); `analysis/v1_bait_technique.py` +
`data/v1/bait_technique_reference_v1.json` (extend, keep the two-claim
separation); `webapp/templates/map.html` (Explore); `home.html`
(`fishin.saved.v1` saved spots); `webapp/static/tags-explainer.js`;
`base.html` nav; `DECISIONS.md`, `README.md` badges, `inspect_state.py`.

## Verification (every phase, before commit)
Full `python -m pytest`; live browser check of the changed page against
the running app; `DECISIONS.md` entry for each judgment call (research
sourcing, image-verification method, spawning-trigger exclusion, lexicographic
ranking choice, /recommend CSRF exemption); README badges via
`inspect_state.py`; `git fetch`/merge before push. Phase-specific tests:
ranking is deterministic (same input → identical output, run twice);
each edge case above has a test; disclosure text always present; card ==
spot-page consistency; preference changes reorder results; schema/manifest
tests from Phase 0; honest empty states for missing image/habitat.
