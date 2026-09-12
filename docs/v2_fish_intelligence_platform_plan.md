# V2 Deepening: Fish Intelligence Platform — Plan

**A naming note, for anyone comparing this against `ROADMAP.md`**:
`ROADMAP.md` already reserves the label "V3" for a different, later
concept — fishing-trip logging and prediction-vs-outcome validation —
and "V4" for personalization from a user's own history. The CEO's vision
in this doc (spot-level temperature/species/bait intelligence, reached
by clicking a spot on the map) is a **deepening of V2's own scope**
("Where Should I Fish?"), not that later V3. Filed here as `v2_*` to
avoid confusing a future reader who cross-references the two docs.

## Context

This project has been built incrementally, session by session, without a
single forward-looking plan tying the pieces together. The CEO stepped
back to define what this app is actually *for* before more feature-by-
feature work happens: a genuine "everything you need to know to go
catch a fish" platform, not just a conditions lookup tool.

The core product loop the CEO described: **a user opens the map, finds a
spot near them, clicks it, and gets a complete, trustworthy answer** —
likely water temperature, what's likely biting and why, what signs to
look for, and what bait to use and why. Every claim carries its
evidence, the same discipline this project has used since Decision #005
("never represent an arbitrary score as scientifically validated").

Two things were confirmed before writing this plan (both read-only
checks, not assumptions):

- **No bait, lure, technique, or "signs to look for" data exists
  anywhere in this repo.** Checked the full `physiology_thresholds_v1.json`
  (26 species) and every docs file — the only near-hits are one-line
  mentions in the *superseded* V0 catch-rate research (explicitly
  rejected as untestable) and the existing `diel_active` flag. This part
  of the vision needs real, new, cited research — not an engineering
  task pulling from data that already exists.
- **The Lake Michigan buoy work from the prior session finished
  successfully**: all 10 real Lake Michigan county entries now resolve
  to `ndbc_buoy_live` (a real measurement), and the duplicate-run-rows
  bug found alongside it is fixed (`runs` table now holds exactly one
  run). This plan builds on that as a solid foundation, not something
  still in flight.

Per the CEO's own answer when asked: "niche" spots means **more real
government data sources first** (e.g. the trout-stream public-easement
layer already found and deferred in Decision #017), with **user-
submitted spots as a later, separate phase** — not in this pass.

## Vision (for the record)

**fishin becomes a spot-level fishing intelligence tool**: for any point
on the map — official or niche, matched to known data or not — a user
gets an honest, evidence-backed answer to "what's my best shot here,
right now, and why."

## What "done" looks like for this phase

Click a spot on the map → see, in one place:
1. **Water temperature** — real, or honestly labeled as estimated from
   nearby real readings, or honestly labeled as unavailable. Never a
   silent guess.
2. **Species likely present, and whether conditions currently favor
   them** — reusing the physiology-match system already built, now
   extended to spots that aren't matched to a full V1 waterbody record.
3. **Why** — the same evidence-quality/citation discipline already used
   for temperature and species matches, extended to bait/technique.
4. **What bait/technique to use, and signs to look for** — from a new,
   real research pass (this phase's biggest lift), not fabricated.

## Phased delivery

Five phases, each independently shippable and testable, matching this
project's own established discipline (V0→V1 was built the same way).

### Phase 1 — Spot-level temperature resolution

**Problem**: today, only ~54% of access points (the ones matched to a
V1 waterbody) have any temperature info. The other ~46% — plus any new
niche spots from Phase 5 — have none.

**Approach**: a new function in `analysis/v1_conditions_biology_forecast.py`
(alongside the existing `get_current_temperature`), e.g.
`estimate_temperature_from_nearby(lat, lon)`:
- Build a pool of *real* anchor readings: every waterbody in the latest
  run with `temp_is_real=1` (real USGS/CLMN/NDBC readings — never
  proxies, since a proxy is already an estimate and shouldn't be
  re-estimated from), each with a resolvable coordinate.
- Inverse-distance-weighted average of the N nearest real anchors
  within a sane radius (e.g. 15km — tunable, needs real-data tuning
  during implementation, not guessed once and left).
- If zero real anchors exist within that radius, return no estimate —
  honestly `no_data`, exactly like today's existing `NO_TEMPERATURE_DATA`
  path. This is the CEO's explicit instruction: don't fabricate when
  there's truly nothing to base it on.
- New `temp_method` value: `interpolated_nearby`, `is_real_water_
  measurement: False` (it's an estimate, not a measurement) — but with
  its own honest label distinct from the existing air-temperature-proxy
  wording, e.g. "estimated from N real readings averaging Xkm away."
  Surfaced in the UI as its own tag, not conflated with `proxy`.
- Depth-based refinement was investigated twice already (Decisions
  #017-#018) and closed out — no depth data source cleared this
  project's correctness bar. Not reopened here; distance-only IDW is
  the real, defensible starting point.

**Where it plugs in**: `ui/v1_review_data.py`'s `list_access_points()`
already returns lat/lon for every access point (matched or not). Add an
on-demand temperature resolution path for unmatched points (called from
the new spot-detail endpoint in Phase 4, not baked into the bulk
`/map/data` payload — 3,272 live interpolations per map load would be
slow and unnecessary when only one spot gets opened at a time).

**Tests**: unit tests for the IDW math (synthetic anchors, known
expected result), a real "zero anchors in range → no_data" case, and a
real "one very close real anchor" case using this project's actual
survey-confirmed lake coordinates.

### Phase 2 — Spot-level species data (reuse, don't rebuild)

For a matched access point, this already exists in full — reuse
`get_waterbody_detail()`'s species_predictions rows unchanged,
including the "why not a match right now" explanations built last
session (`non_match_explanation`).

For an **unmatched** point, there is no V1 species-presence record to
draw from, and there won't be one without guessing which waterbody it's
really on — not attempted. Shown honestly: "No species-presence data
available for this specific spot" (the same honest-gap framing already
used throughout this app), never inferred from a nearby waterbody.

No new code beyond wiring the existing detail query into the new
spot-detail endpoint (Phase 4).

### Phase 3 — Bait & technique research (the real lift)

This needs the same rigor as the original physiology research
(`docs/v1_physiology_research_candidates.md`): real citations, explicit
evidence-quality tiers (well-established / field-anchored / single-
source-speculative — the vocabulary this project already uses), and
honest "not found" gaps where the literature doesn't support a claim.

**Scope for this pass**: the species with the most real presence
records in the current database (by `species_predictions` row count) —
Largemouth Bass, Smallmouth Bass, Walleye, Northern Pike, Muskellunge,
Bluegill, Black Crappie, Yellow Perch, Channel Catfish, and Lake
Michigan's salmon/trout — rather than attempting all 26 at once. This
mirrors how V1 itself started with 22 lakes before expanding statewide
(Decision #013) — get the highest-value species right first, expand
later.

**Structure**: a new reference file, `data/v1/bait_technique_reference_v1.json`,
keyed by species, each entry tied to a **condition** (not a fixed
"use X lure") — e.g. "when water is in the documented spawning-trigger
range" or "when the activity/feeding window is active" — since bait
choice genuinely depends on the same temperature/behavior state this
app already tracks. Each entry carries: recommended bait/technique,
the biological *why* (e.g. "shad are spawning in shallows, matching
forage"), a real citation, and an evidence tier. A parallel
`docs/v1_bait_technique_research_report.md` documents the research
process itself (sources checked, what was found vs. not found per
species) — same transparency as the existing physiology report.

**This phase is a research task, not a coding task** — flagged here so
it isn't accidentally rushed alongside Phase 1/2/4's engineering work.

### Phase 4 — The spot detail view (the actual "one-stop-shop")

New Flask route, e.g. `/spot?id=<access_point_id>` (or reuse the
existing `more_info_url`/lat-lon as the key, consistent with how shore-
fishing enrichment is already keyed off `more_info_url` rather than the
volatile `access_points.id`), rendering one page combining:
- The access point's own real fields (already exist: facility name,
  directions, amenities, ADA info — `webapp/templates/map.html`'s
  existing `buildDetailHtml()` logic shows what this already looks like
  in miniature).
- Temperature (Phase 1: real, estimated, or honestly unavailable).
- Species + why/why-not (Phase 2, reusing existing species-card
  rendering from `webapp/templates/waterbody_detail.html`).
- Bait/technique + why (Phase 3's data), shown only for species that
  are actually a current match — recommending bait for a fish that
  isn't biting would undercut the whole trust goal.

Map markers and list rows both link here (replacing/extending today's
popup, which stays as a lightweight preview). This is the concrete
shape of "click a spot, get the whole picture."

### Phase 5 — More real "niche" spot sources

Per the CEO's answer: real data first. Revisit the trout-stream
easement layer found and deferred in Decision #017
(`FM_Trout/FM_TROUT_NONDNR_EASEMENTS_WTM_Ext`, polygon geometry) and
design a way to surface it as point-like spots (e.g. centroids or
access points along the easement) consistent with the existing marker
system, rather than a full polygon-overlay rebuild. Scoped as its own
investigation at the start of this phase — the right representation
won't be known until the real data's shape is checked again with this
specific goal in mind.

User-submitted spots are explicitly **not** in this plan — a
deliberately separate future phase (accounts, submission flow,
moderation) per the CEO's own phasing decision.

## Verification approach (per phase)

- Phase 1: unit tests on the IDW math with synthetic + real anchor
  coordinates; a live check that a real, currently-unmatched access
  point resolves to a sane estimated temperature.
- Phase 2: existing tests already cover species_predictions rendering;
  add one confirming an unmatched point's spot-detail honestly shows
  "no species-presence data," not a guess.
- Phase 3: no automated test for research quality itself, but every
  bait/technique entry requires a real citation before being merged —
  same bar as the physiology data.
- Phase 4: Flask route tests (200 for a matched spot, 200 with honest
  gaps for an unmatched one, 404 for a bad id) + a live browser check
  that a real spot's full card renders correctly, mirroring how the
  map/list views were verified last session.
- Phase 5: re-verify the easement data's real shape before deciding the
  final representation — don't assume the polygon-to-point approach
  sketched above until it's checked against the real geometry.

## Sequencing

Phases 1, 2, and 4 are tightly coupled (4 has nothing to show without
1+2) and should ship together as one slice. Phase 3 (research) can run
in parallel with 1/2/4's engineering, since it's a different kind of
work — but Phase 4's bait/technique section simply stays empty/omitted
for species until Phase 3 has real, cited data for them, never a
placeholder claim. Phase 5 is independent and can come before or after
the others.
