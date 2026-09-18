# V4 UX Redesign Plan — Recommended / Explore / Profile

**Status: Plan only. Nothing in this document has been built.** Written
against the 5 wireframes in [`UX/`](../UX/) and the CEO's walkthrough of
the intended navigation. This is a planning document, not a decision
record — items below that require a real product/scope call are flagged
explicitly rather than decided here, and should get their own
`DECISIONS.md` entry once resolved, per this project's standing
convention of recording every real pivot with rationale.

## What the wireframes ask for

Five screens, tied together by a 3-icon bottom nav and a persistent
"fish logo" home link:

1. **Recommended** (home / the fish-logo destination) — a "Saved Spots"
   list and a "Recommended Spots" list, each spot card showing distance
   away and a short list of species with a bite likelihood, both lists
   *"ordered by how good fishing should be."*
2. **Spot Detail** (bottom-left nav icon's destination once a spot has
   been viewed) — location, water temperature (+ rain/sun icon, wind,
   moon phase), then two color-coded fish lists: green "Active Fish"
   (in their documented window) and yellow "Inactive Fish" (outside
   it), each entry with a picture and a one-line reason. Below that:
   Stocking history / Regulations / Consumption Advisory buttons.
3. **Fish Detail** (tap a fish on the Spot Detail page) — species name,
   a large image, "Documented Activity," "Documented habitat" (where
   they hang out — drop-offs, weed, depth, spawning depth, etc.), and
   3 "Recommended Bait" cards (picture, name, description, how to use),
   plus a link to "all documented baits."
4. **Profile** (bottom-right nav icon) — profile pic, username, member
   since; Rate us / Help / Documentation links; dark/light mode toggle;
   fishing-preference toggles (boat launch / carry-in / shore); a full
   species preference list. This is explicitly the data that feeds the
   recommendation ranking.
5. **Explore** (bottom-middle nav icon, the map pin) — a Map/List
   toggle, filters, and (in list mode) the same "ordered by how good
   fishing should be" sort as the Recommended screen.

Navigation, as described: the fish logo always returns to Recommended.
The map-pin icon opens Explore, where picking a spot goes to Spot
Detail. Spot Detail becomes what the bottom-left icon opens from then
on (replacing today's "home" slot). Tapping a fish from Spot Detail
opens Fish Detail, from which the bottom-left icon returns to the spot
and the map-pin icon returns to Explore. The person icon always opens
Profile.

## The one open question everything else depends on

**"Ordered by how good fishing should be" is a ranking/score, and this
project has an explicit, repeatedly-reaffirmed rule against exactly
that.** DECISIONS.md #005: *"the system must never represent an
arbitrary score as scientifically validated."* V0's entire conclusion
(DECISIONS.md #001-#009, ROADMAP.md) was that catch-rate/fishing-quality
prediction is **not demonstrated** with the data available — the app
was deliberately rebuilt in V1 around factual comparisons ("is this
species' documented window matched right now") instead of a score,
specifically to avoid implying a validated prediction that doesn't
exist.

This plan does **not** resolve that tension by picking an approach —
it needs an explicit CEO call, the same way every earlier scope
decision in this project got one, because it changes what the app is
allowed to claim. Two honest paths forward, laid out for that decision:

- **Option A — a disclosed heuristic ordering, not a "score."** Sort by
  a plain, inspectable rule stated in the UI itself — e.g. "count of
  species currently in their documented window, nearest distance as
  tiebreaker" — with a one-line disclosure next to the list ("ranked by
  how many species are in their documented range right now — not a
  prediction of catch success"), the same honesty pattern already used
  for evidence tiers and the wind/pressure display. No new statistical
  claim, no fabricated weighting, just a transparent re-sort of data
  the app already has and already trusts.
- **Option B — an actual weighted/learned ranking model.** Would need
  real validation data and real evaluation, i.e. reopening the
  V0 question this project already spent significant effort closing
  with a negative result. Not recommended without a very deliberate,
  separate decision to do that — it's a different project phase, not a
  UI change.

**This plan is written assuming Option A**, because it's the only one
consistent with existing standing discipline without a separate,
much bigger decision to reopen V0. Flagging clearly that this
assumption itself needs sign-off before Phase 4 (below) starts.

## What already exists vs. what's new

Surveyed against the current codebase before writing this, so the plan
doesn't propose rebuilding things that are already there:

| Wireframe piece | Current state |
|---|---|
| Explore (map/list toggle + filters) | **Already built** — `webapp/templates/map.html` already has a Map/List toggle (`#toggle-map-btn`/`#toggle-list-btn`) and a full filter form (waterbody, county, species, source type). Mostly a re-skin + sort-order change, not new. |
| Saved spots | **Already built** — `localStorage` key `fishin.saved.v1`, rendered on `home.html` today. Reusable as-is for the Recommended screen's "Saved Spots" section. |
| Spot Detail's confirmed/likely species dashboard | **Already built**, but on a different axis than the wireframe. Today's two categories are *evidence tier* (Confirmed Sighting vs. Likely/indirect). The wireframe's Active/Inactive split is *current-temperature match*. These need to be reconciled, not replaced — see Phase 2. |
| Bait/technique guidance | **Already built** — `analysis/v1_bait_technique.py` + `data/v1/bait_technique_reference_v1.json`, keyed by the same temperature-state logic the rest of the app uses, already separates `biological_basis` from `angling_application` per Decision #005. Currently server-side only, not exposed as its own page. Needs restructuring from per-state prose into discrete bait items for the "3 bait cards" layout, and has **no images**. |
| Species physiology data | **Already built** — `data/v1/physiology_thresholds_v1.json`, 27 species, already has `description`/`evidence` fields. Has **no "documented habitat" field** (drop-offs, weed, depth) — that's new research, not a formatting change. |
| Accounts / profile / preferences | **Does not exist.** No `/login`, `/signup`, `/account`, or `/profile` route today (confirmed live). This is new, and its scope depends on whether real accounts are in play — see Phase 3. |
| Species/bait images | **Do not exist.** No image assets anywhere in the app today. Real sourcing/licensing decision, not a build task — see Open Items. |
| Bottom nav | **Exists but different** — `base.html` currently has 5 items (Home, Explore, Search FAB, Directory, About). The wireframe's 3-icon nav is a real restructure, not additive. |
| Last-visited-spot tracking | **Does not exist.** Today's bottom-left icon goes to `home`. Needs a small new `localStorage` entry (`fishin.lastSpot.v1`) written on every `/spot` visit. |
| Geolocation / distance | **Does not exist anywhere in the app.** Needed for "x distance away" on every spot card. Real permission-prompt UX decision — see Open Items. |

## Proposed phases

Each phase is independently shippable and reversible, matching this
project's established practice of incremental, individually-verified
commits rather than one large redesign landing at once.

### Phase 1 — Fish Detail page (lowest risk, mostly existing data)

- **Backend:** new `get_species_detail(species_name)` in
  `ui/v1_review_data.py`, assembling: physiology thresholds (existing),
  `_short_evidence_label`-style plain-language activity text (existing
  pattern, reused), and bait/technique entries restructured from
  `v1_bait_technique.py`'s per-state prose into a flat list of
  `{name, description, how_to_use, state_it_applies_to}` items. This is
  a data-shape change to already-real content, not new research.
- **New route:** `GET /fish/<species>` in `webapp/app.py`.
- **New template:** `webapp/templates/fish_detail.html` — species name,
  image placeholder (see Open Items), Documented Activity (existing
  text), Documented Habitat (**blocked on new research** — see Open
  Items, ships as "not yet documented" rather than fabricated text
  until real habitat sourcing exists), Recommended Bait cards, link to
  "all documented baits" (every state's entries, not just the current
  one).
- **Tests:** route test per species, a regression test that no
  `biological_basis` text is ever presented as `angling_application`
  (mirrors the existing Decision #005 guard pattern), a test that a
  species with no bait data yet shows an honest empty state rather than
  a fabricated placeholder.

### Phase 2 — Spot Detail redesign (reconciling two real axes)

- **Design decision needed:** the Active/Inactive (temperature-match)
  split and the existing Confirmed/Likely (evidence-tier) split are
  both real and both worth keeping — proposing each fish row carry
  **both**: bucketed top-level by Active/Inactive (matching the
  wireframe), with the existing evidence-tier tag kept as a secondary
  badge on each row (small, not removed) so the evidentiary honesty
  work from `DECISIONS.md` #034-#037 isn't lost in the reshuffle.
- **Backend:** extend `build_species_categories()`
  (`ui/v1_review_data.py`) to also bucket by `activity.inside_window`
  rather than only by evidence tier — most of the underlying
  `_activity_for_species()` computation already exists and is reused
  as-is.
  Link each species row to the new `/fish/<species>` page from Phase 1.
- **Frontend:** restructure `spot_detail.html`'s species section into
  green/yellow bordered lists (styling only — this app already has an
  amber-bordered box pattern from the citizen-sightings feature to
  reuse, not a new visual language). Species images: same Open Items
  blocker as Phase 1.
- **Tests:** update the existing dashboard tests
  (`webapp/tests/test_app_routes.py`'s `SpeciesDashboardTests`) for the
  new bucketing; add a regression test that a species never
  disappears in the reshuffle (every species that had either a
  confirmed/likely tag or an activity match before still appears
  after).

### Phase 3 — Profile / preferences

- **Scope decision needed:** does this ship as an anonymous,
  `localStorage`-only preferences page (matching this project's
  existing no-account "Save this spot" pattern — fast, no backend, but
  preferences don't follow the user across devices and there's no real
  "member since" date or profile pic to show), or does it require the
  real accounts feature that was scoped in an earlier planning pass but
  never built (confirmed: no `/login`/`/signup`/`/account` route exists
  today)? The wireframe's "Username" / "Member since" / "profile pic"
  fields imply real accounts; "Fishing Preferences" and "Species" list
  do not strictly require them.
- **If anonymous (recommended for a first pass):** new
  `localStorage` keys `fishin.prefs.spotTypes.v1` and
  `fishin.prefs.species.v1`; Profile page shows a generic default
  avatar/"Guest" state instead of username/member-since until accounts
  exist; Rate us / Help / Documentation / dark-mode toggle are all
  static links + a `localStorage` theme flag, no backend needed.
- **If real accounts:** reuses the `webapp/user_data.py` /
  `webapp/accounts.py` design already scoped in the earlier product
  plan (separate SQLite DB, `FISHIN_USER_DB_PATH`, CSRF, login
  lockout) — not re-designed here, just referenced, since building
  accounts is a large enough unit of work to stay its own phase either
  way.
- **Frontend:** new `webapp/templates/profile.html`; dark/light mode
  toggle wires into a `data-theme` attribute on `<html>` (this app's
  CSS already supports `prefers-color-scheme`-based dark mode per the
  artifact-design conventions used elsewhere — extending it to a
  manual override is additive, not a rework).
- **Tests:** preference read/write round-trips (JS, manually verified
  per this project's existing "no JS test runner" accepted gap),
  route test for the page rendering with and without saved
  preferences.

### Phase 4 — Recommended home screen + ranking (gated on the open question above)

- **Blocked until Option A vs. B (above) is explicitly decided.**
  Everything else in this plan can ship without this phase; this phase
  cannot start responsibly without that decision on record.
- **Backend (assuming Option A):** new `rank_spots_for_recommendation()`
  — for a set of candidate spots (saved spots, plus nearby spots within
  some real radius of the user's geolocated position, reusing
  `_haversine_km`), compute "species currently in documented window"
  count per spot (already-existing per-spot computation, just
  aggregated across spots rather than one spot at a time), sort by that
  count with distance as a tiebreaker, and disclose the rule in the
  response payload so the template can't silently drop the disclosure
  text.
- **Frontend:** new `webapp/templates/recommended.html` as the new
  `home` route content; distance display needs the browser Geolocation
  API (permission-gated — see Open Items) with a graceful no-permission
  fallback (show spots without distance/sort by save order, don't block
  the page).
- **Nav restructure:** collapse `base.html`'s 5-item bottom nav to the
  wireframe's 3 (last-spot / Explore / Profile), with the fish-logo
  link in the header pointing at `home` (Recommended). This changes
  every page's nav, so it's the last piece to land, once the 3
  destinations it points to all exist.
- **Tests:** ranking function unit tests (deterministic given fixed
  species/temperature data — no live geolocation in tests), a
  regression test that the disclosure text is always present alongside
  any ranked list, route tests for the new nav on every existing page.

## Open items — real decisions or sourcing, not code

These block specific phases above and are listed here so they're
visible up front rather than discovered mid-build:

- **Species and bait images.** No image assets exist in this app today.
  Real photos need either licensing (cost + attribution decision) or a
  from-scratch illustration approach — not something to source from an
  ungated web search and use without checking usage rights. A real
  product decision, not a build task.
- **"Documented habitat" text per species.** Doesn't exist in
  `physiology_thresholds_v1.json` today. Real research (same standard
  this project has held every other claim to — cited, not guessed) is
  needed before this ships; Phase 1 explicitly ships with an honest
  "not yet documented" state rather than invented habitat descriptions.
- **Geolocation permission UX.** Needs a real decision on what happens
  when a user declines location access (the wireframe's "x distance
  away" simply doesn't work without it) — proposing graceful
  degradation to an un-sorted-by-distance list rather than blocking the
  page, but flagging it here as a real UX call, not an implementation
  detail.
- **The Option A/B ranking question above** — the single biggest open
  item in this whole plan.
- **Accounts scope for Profile** — anonymous-first vs. building real
  accounts now, per Phase 3.

## Verification, per this project's standing practice

Every phase: full test suite green before commit, live browser
verification against the real running app (not just unit tests) before
calling a phase done, a `DECISIONS.md` entry for any judgment call made
along the way (matching #034-#042's pattern this session), README
test/decision-count badges kept in sync, incremental commits per phase
rather than one large landing.
