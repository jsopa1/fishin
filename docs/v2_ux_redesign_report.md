# Full UX Redesign — Report

Full plan (approved before this work started): the plan-mode session that
preceded this build. Full detail of what was actually shipped, phase by
phase, is below. Decision record: `DECISIONS.md` #023.

## Why

The app worked and was data-honest, but looked and behaved like an
internal review tool — plain HTML tables, four-field `<select>` filter
forms, emoji-as-icons, a Map and a Browse page that duplicated each
other's job, and diagnostic pages (Failures, Summary) sitting in the
main nav next to angler-facing pages. The CEO asked for a full redesign
modeled on popular outdoor/fishing apps (AllTrails, OnX Fish/Hunt,
Fishbrain) — a full UX rework, not a skin: navigation, information
architecture, and page structure were all explicitly open to change,
across the entire app.

## What changed

### Design system foundation

`webapp/static/style.css` was rebuilt around the existing pine-green
brand color (`--accent`, kept deliberately — it already reads as
"outdoors/water" and the CEO didn't ask for a new palette) with a real
token system added on top: a full neutral scale (`--gray-0`…`--gray-900`),
a spacing scale (`--space-1`…`--space-8`), and a type scale
(`--text-xs`…`--text-2xl`). Every component below is built from these
tokens rather than hardcoded values, so future pages stay consistent by
construction.

A new component library replaces the old ad hoc classes: real buttons
(`.btn`, `.btn-primary/.btn-secondary/.btn-ghost`), a pill-shaped search
bar (`.search-bar`), filter chips (`.chip`, toggle-style with an
`.active` state), list-item cards (`.list-card`), a stat-chip badge
(`.stat-chip`), a detail-page hero block (`.detail-hero`), and section
tabs (`.section-tabs`/`.section-tab`/`.section-panel`). Existing
semantics that already worked (`.tag`, `.species-card`, `.match-badge`,
`.flag`, `.why-not-box`, `.detail-box`) were kept and re-themed, not
replaced, per the plan's explicit instruction not to touch things that
weren't broken.

`webapp/templates/base.html` gained a single inline SVG `<symbol>`
sprite (20 icons: fish, map-pin, search, filter, thermometer, ruler,
accessibility, route, menu, chevron-right, alert-triangle,
external-link, x, check-circle, moon, anchor, waves, list, map, info),
referenced everywhere the app previously used an emoji or nothing —
zero new dependency, no build step, consistent with the project's
existing CDN-only/no-bundler setup.

The responsive system became properly mobile-first: base rules target
narrow viewports, with `min-width: 768px` (tablet) and `min-width: 1024px`
(desktop) layering on top — replacing the old single `max-width: 640px`
breakpoint.

### Information architecture

- **`/map` became "Explore"**, the app's primary discovery surface and
  the nav's first item. Rebuilt from a map-with-a-toggle-to-a-separate-
  list into a real AllTrails/Zillow-style split view: map and a
  synchronized scrollable card list, side by side on desktop
  (`.explore-layout` in a row), a Map/List toggle on mobile
  (`data-mobile-view` attribute on the layout, driven by the existing
  `#toggle-map-btn`/`#toggle-list-btn` buttons). The old four-field
  `<select>` filter form became a search bar plus a filter-chip bar —
  radio-button chips for access type, a text-input styled as a chip for
  county, a native `<select>` styled as a chip for species — still a
  real GET form with the same query-param names, so every existing
  bookmark, direct link, and Flask-level test keeps working.
- **`/` became a map-first landing**: a hero with a prominent search bar
  that submits into Explore, real stat pills (now including total real
  access-point count, previously not shown on this page), and a
  decorative live Leaflet tile preview (non-interactive, no markers —
  fetching all 3,272 points just for a homepage decoration would be
  slow and wasteful) that links through to Explore on click. The
  trust-building "what this is/isn't" section — this project's
  load-bearing framing since Decision #005 — was kept in full, not cut
  for the sake of matching a reference app's brevity.
- **`/browse` became the "Waterbody Directory"**: restyled with the same
  search-bar-plus-chips pattern and a card list instead of a table.
  Kept as a secondary surface (linked from Explore's intro copy and the
  nav, not the primary item) — it remains the only way to reach the
  waterbodies with no physical access point at all (pure streams/
  creeks with stocking-only records), which Explore's access-point data
  can't cover.
- **`/failures` and `/summary` moved out of primary nav** into a
  "Data Health" section of the footer. Both pages were restyled
  (a small kicker label, inherited component styling) but not
  restructured — a dense table is still the right pattern for a
  diagnostic page, unlike the angler-facing pages.
- **`/waterbody` and `/spot`** both got a hero block (name, location,
  key stat badges — temperature and match/species count) plus section
  tabs instead of one long scroll. `/waterbody` has two tabs
  (Conditions, Species); `/spot` has three (Conditions, Species, Site
  info — the access-point fields that used to be one long `<dl>`).
  Tabs are progressive enhancement: every panel renders unhidden in the
  server response, and a small inline script hides all but the first
  on load and wires the click handlers — so nothing depends on
  JavaScript for content to exist in the page, only for the tabbed
  presentation.
- **No routes were removed, renamed, or given new required parameters.**
  Every URL that worked before this redesign still works identically.

### Real bugs found and fixed during this pass

- **A CSS specificity bug collapsed the Explore map to 2px tall on first
  build.** `#access-map, .map-pane > div { height: 100% }` was carried
  over from an earlier draft and, because ID selectors outrank class
  selectors, overrode the `.map-pane` class's own explicit height
  (`460px` / `62vh` depending on viewport) on the very element that
  needed it — and `height: 100%` against a parent with no explicit
  height resolves to nothing. Caught by checking `getComputedStyle()`
  height directly rather than trusting a screenshot that happened to
  crop the empty space out of view; fixed by removing `#access-map`
  from that selector so it only sizes Leaflet's own internal child
  divs, not the container itself.
- **A real, pre-existing data inconsistency in the `county` column
  surfaced through a new card layout.** Some real WDNR-sourced records
  store just the county name (`"Sauk"`); at least one (`"Sauk County"`,
  used deliberately in this project's own test fixtures) already
  includes the word "County." The redesign's new detail-hero and card
  templates initially appended `" County"` unconditionally for a nicer
  label, producing "Sauk County County" for that record. Caught by
  reading the live rendered page text for a real filtered search, not
  just a screenshot glance. Fixed by dropping the appended suffix
  everywhere and displaying the stored field exactly as-is, matching
  how the rest of the app (the map popups) already handled this same
  known inconsistency.

## What did not change

- No backend or data-layer code (`ui/v1_review_data.py`,
  `analysis/*.py`) was touched — this was templates, CSS, and the
  Explore page's inline JS only.
- No new species/temperature/physiology logic — every real-data field
  shown is exactly what the existing routes already returned.
- The evidentiary-honesty framing (real vs. estimated vs. proxy vs.
  no-data; survey-confirmed vs. stocking-only; disputed-threshold
  disclosure; "why not a match" explanations) is unchanged in
  substance everywhere it appears — only its visual presentation
  changed.

## Verification

- Full test suite: 296 passing (unchanged count from before this pass
  started — no tests were added or removed, only two assertions in
  `webapp/tests/test_app_routes.py` updated to check for the new real
  markup, `class="list-card"` counts, in place of the old `<tr>` counts,
  since the Waterbody Directory intentionally moved from a table to a
  card list).
- Live browser verification at mobile (375px), and desktop (1280px)
  widths for every rebuilt page: Explore's split view, filter chips,
  and mobile Map/List toggle; both detail pages' hero and tab
  switching against real matched and unmatched records (a real
  previously-unmatched point, a real disputed-threshold waterbody);
  the new landing page's search bar and map preview; the restyled
  secondary pages and the 404 error page.
- No changes to `analysis/`, `ui/v1_review_data.py`, or the database —
  the full non-webapp test suite ran unmodified and unaffected.
