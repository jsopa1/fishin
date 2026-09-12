# V2 Access-Point Map — Report

Status: honest account of this V2 slice, including what was investigated
and deferred, not just what shipped. Every claim below is backed by a
concrete check (a live query, a test, or a measured browser result), not
an assertion.

---

## 1. Scope

Per `ROADMAP.md`, V2 ("Where Should I Fish?") covers "maps, water bodies,
access points, habitat, and environmental intelligence" — deliberately
broad. This report covers the first slice: **a statewide map of real
public boat access and shore fishing sites**, plus an honest account of a
second data layer ("habitat"/lake size) that was investigated and
deliberately not shipped this cycle, per the pattern established by
Decision #011 (GLATOS) — investigate first, and if a data source doesn't
cleanly support a claim without added risk, say so rather than force it.

## 2. Data investigation — before any code was written

Searched for what WDNR actually publishes rather than assuming. Found and
verified two live services:

- **Boat access + shore fishing sites** —
  `dnrmaps.wi.gov/arcgis2/rest/services/PR_Recreation/PR_Boat_Access_Shore_Fishing_WTM_Ext/MapServer`
  (layers 1 and 2). Queried live: 3,135 real boat access sites (ramp +
  carry-in) and 142 real shore fishing sites, each with lat/lon, waterbody
  name, county, and (boat access) ADA-accessibility/ownership fields. This
  is the same data behind DNR's own [Boat and Shore Fishing Access](https://dnr.wisconsin.gov/topic/lands/boataccess)
  page. **Shipped** — see below.
- **Lake size/depth ("habitat")** — investigated the WDNR "24K Hydro"
  waterbody polygon layer
  (`TS_AGOL_STAGING_SERVICES/EN_AGOL_STAGING_SurfaceWater_WTM/MapServer/1`)
  as a source for real, computed lake surface acreage. Found two real
  problems that made it unsafe to ship quickly and honestly:
  1. **No county field.** The layer has no county attribute, so
     disambiguating same-named lakes (the exact "Devils Lake" problem
     this project already hit once in V1 — there are multiple Wisconsin
     lakes with that name in different counties) would require either a
     separate spatial join against a county-boundary layer, or joining on
     WBIC (Wisconsin's canonical waterbody ID) — and this project's own
     `waterbody_results` table doesn't currently store WBIC. Verified the
     collision directly: querying `WATERBODY_NAME='Devils Lake'` returned
     a polygon in far-northern Wisconsin (~46.29°N), nowhere near the
     Sauk County Devils Lake this app's V1 data actually covers.
  2. **Scale mismatch.** The layer has 138,766 polygon records
     (nearly all Wisconsin's mapped water polygons down to farm ponds),
     with a 1,000-record page cap — an impractical full pull for a
     "how big is this lake" feature, and even filtered to
     `HYDROTYPE IN (706,707)` (lake/pond + reservoir) it's still 59,517
     records, the large majority unnamed and irrelevant.

  Shipping a per-lake size number without a reliable WBIC join risks
  attaching the wrong lake's size to a waterbody page — a real
  correctness/honesty failure, not a cosmetic one. **Deferred**, not
  shipped, and documented here rather than silently dropped. A safe path
  exists (add WBIC to `v1_full_run.py`'s waterbody universe, then join on
  WBIC instead of name) but is future work, not this cycle's scope.

## 3. What shipped

- **`analysis/v2_access_points.py`** — pulls both real layers live,
  drops abandoned/geometry-less/unnamed records, and links each point to
  an existing V1 waterbody only on an exact normalized-name + loose-county
  match (reusing `v1_conditions_biology_forecast.py`'s own `_norm`/
  `_norm_county`/`_county_matches` helpers, the same logic that already
  solved the "Devils Lake" collision for V1's own data — deliberately
  reused here rather than re-solved differently). Additive only: two new
  tables (`access_points`, `access_points_meta`) in the existing
  `data/v1/v1_full_run_results.db`; no V1 table or logic touched.
  - Real run result: 3,272 points stored, 1,759 (54%) linked to an
    existing V1 waterbody. The other 46% are real WDNR sites on
    waterbodies outside V1's universe (e.g., a boat launch on a pond with
    no stocking or survey record) — still shown, still real, just without
    a "view conditions" link, exactly as designed rather than hidden or
    force-matched.
- **`/map`** (Flask route) + **`/map/data`** (JSON endpoint) — filterable
  by county, waterbody name, and access type; degrades to a real 503 with
  a clear message (not a blank page) when the database is unavailable,
  matching every other route's error-handling discipline.
- **Leaflet + OpenStreetMap** front end, no API key or account required.
  Verified via a live popup click (real DOM event, not just code review):
  clicking a rendered marker for "Ada Lake Campground Boat Ramp" produced
  a popup with the correct real facility name, type, waterbody, county,
  ADA status, and manager.
- **Marker clustering** (Leaflet.markercluster) — added after confirming
  3,272 raw SVG markers is the kind of load clustering exists for.
  Verified via `document.querySelectorAll('path.leaflet-interactive').length`
  returning exactly 3,272 before clustering was added (confirming every
  real point was actually rendering, not silently dropped) and clean
  cluster badges after.
- **Search-to-zoom** — when a county/waterbody/type filter narrows the
  result set, the map calls `fitBounds` on the real returned coordinates
  instead of leaving a filtered handful of points lost on a statewide
  view. Verified live: filtering to `county=Sauk` correctly re-centered
  and zoomed the map to Sauk County with its 43 real access points
  clustered there.

## 4. Verification performed

- **Contrast**: every new color pair (match badges, cluster icons,
  legend dots against their background) computed via the same WCAG
  luminance/contrast script used in the V1 polish pass — all ≥5.19:1,
  above the 4.5:1 AA threshold for normal text; cluster-badge white text
  on brand green computed at 6.49:1 (small) and 9.15:1 (large).
- **Mobile**: `document.body.scrollWidth` vs `document.documentElement.clientWidth`
  checked at a real 375px viewport on `/map` both before and after the
  clustering change — 375/375 both times, no horizontal overflow.
- **No console errors** on page load (checked via the browser's own
  console, not assumed).
- **CI**: all 197 tests passing (20 new: 15 pure-logic/DB unit tests for
  `analysis/v2_access_points.py`, 5 Flask route tests for `/map` and
  `/map/data`, including a 503-on-unavailable-database case and a
  round-trip check that a `matched_waterbody_name` returned by
  `/map/data` actually resolves to a real 200 on `/waterbody`).

## 5. Honest gaps / not done this cycle

- Lake size/depth ("habitat") data — investigated, deferred, see §2.
  Doing it right needs a WBIC join, which needs WBIC added to the V1
  waterbody universe first.
- Aquatic invasive species presence — not investigated this cycle.
- The broader "environmental intelligence" part of V2's scope (weather
  overlays, seasonal context beyond what V1 already provides) — not
  started.
