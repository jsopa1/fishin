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

## 6. Follow-up: a second attempt at lake-size data, and a pivot to AIS

Before closing this slice out, a second, smarter attempt was made at the
lake-size problem from §2, and a real "environmental intelligence" layer
(aquatic invasive species) was shipped instead once that attempt also
came back negative. Full rationale: DECISIONS.md #018.

- **Second attempt: spatial join instead of name matching.** Rather than
  match lake polygons by name (the approach that failed in §2), this
  tried a point-in-polygon spatial query: take a real, already-trusted
  coordinate from a confidently-linked access point (e.g. the real "North
  Shore Landing" boat ramp at 43.4263°N, -89.7281°W, linked to Sauk
  County's Devils Lake), and ask WDNR's 24K Hydro layer which polygon
  contains that exact point — no name ambiguity possible. Live-tested
  against that real coordinate. Result: the point landed on a polygon
  named `"Unnamed"` (`HYDROTYPE` 710, "Unspecified Open Water"), not the
  named Devils Lake polygon — because this hydrography layer breaks
  complex shorelines (docks, channels, marina inlets) into many small
  fragment polygons near the shore, not one polygon per named lake.
  Getting the "right" fragment reliably would need a nearest-largest-
  named-polygon heuristic — real added complexity and a second source of
  possible error, not a clean fix. **Confirmed deferred**, with stronger
  evidence than §2 alone (two independent techniques, two independent
  failure modes) — see DECISIONS.md #018 for the full rationale on why
  this closes out the investigation rather than prompting a third
  attempt.
- **Shipped instead: real, verified aquatic invasive species sightings**
  (`analysis/v2_invasive_species.py`), pulled live from WDNR's AIS
  monitoring service (`WY_Lakes_AIS` ArcGIS services) — 557 real,
  WDNR-verified sightings across 6 commonly-tracked species (Zebra
  Mussel, Spiny Waterflea, Rusty Crayfish, Eurasian Water-Milfoil,
  Curly-Leaf Pondweed, Round Goby), each with a real detection date,
  site description, and verification status. Deliberately **not** joined
  to V1 waterbody records, for the same reason the lake-size join was
  deferred — these records carry a `WBIC` field but no county, and this
  project doesn't yet have a safe way to resolve that to one of its own
  waterbodies. Instead, each sighting stands on its own real location, an
  optional (off-by-default) map layer toggled via a Leaflet layer
  control, exactly like an unmatched access point already does.
  Positive-only framing applied explicitly in the UI copy: a sighting is
  real evidence a species was found there; its absence from this layer
  is not evidence the species isn't present, since WDNR's monitoring
  coverage is real but not exhaustive — the same rule already governing
  stocking-derived species presence in V1.
- Verified live: toggling the layer control on renders exactly 557 real
  markers (`document.querySelectorAll('path...[stroke="#b3261e"]').length`);
  clicking one produced a real, correct popup (Curly-Leaf Pondweed,
  *Potamogeton crispus*, "Pine River Apache Rd", "Verified (Not
  Vouchered)", detected 2018-08-15).
- 11 new tests (7 pure-logic/DB unit tests for
  `analysis/v2_invasive_species.py`, 4 new Flask route tests) — 208
  passing total.

## 8. Shore-fishing species enrichment, species filter, and list view

Following a CEO request to "fill in gaps" for sites without species
info and make the map "a one-stop shop... clearly labeled," this pass
adds a real per-site data source specifically for shore-fishing sites,
a species filter spanning both real sources, and a list-view alternative
to the map. Full rationale: DECISIONS.md #019.

- **New source, investigated and verified before writing an ingestion
  script**: every shore-fishing access point's `more_info_url` already
  pointed at a real WDNR detail page
  (`dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=<n>`) that this
  project was only ever linking to, never reading. That page publishes,
  per site: available fish species, directions, vehicle/ADA stall
  counts, restrooms, fish-cleaning area, amenities, comments, and
  property-manager contact — real fields no ArcGIS layer this project
  uses carries. Confirmed the page's HTML structure is stable (fixed
  `<td><b>LABEL</b></td><td><span>VALUE</span>` rows) across three real
  site IDs (21, 5, 116) before writing a parser against it.
- **Deliberately does not trust this page's own Latitude/Longitude
  fields.** Site ID 5 (Namekagon Lake) has them backwards in WDNR's own
  data ("Latitude: -91.08", "Longitude: 46.21" — swapped for a Wisconsin
  site). This project already has a real, trustworthy coordinate for
  every shore-fishing point from the ArcGIS layer
  (`analysis/v2_access_points.py`); the new scraper
  (`analysis/v2_shore_fishing_details.py`) only adds the text fields
  that layer doesn't carry, never touching the coordinate.
- **`analysis/v2_shore_fishing_details.py`** fetched all 138 real
  shore-fishing detail pages live (109 had a species list — the other
  29 are real WDNR records that simply don't list species, an honest
  gap in WDNR's own data, not something to paper over). Keyed by
  `more_info_url` rather than `access_points.id`, so this enrichment
  survives a future `access_points` re-ingestion (that table's
  AUTOINCREMENT ids aren't stable across reruns) without silently
  attaching to the wrong site.
- **Two real bugs found and fixed while verifying the real scraped
  data, not assumed correct from a first pass:**
  1. Naive `split(",")` truncated species text that nests a second
     comma-separated list inside parentheses — real WDNR text at site
     109 (Council Grounds State Park) reads `"PIKE (NORTHERN, YELLOW),
     ... BASS (SMALLMOUTH, ROCK), ..."`; a plain split produced the
     broken fragment `"BASS (SMALLMOUTH"` with no closing paren.
     Fixed with a paren-depth-aware splitter and a regression test
     using this exact real string.
  2. WDNR's own "unknown" placeholder is spelled three different ways
     across real records — `UNKNOWN`, `UKNOWN` (site 109), and `UNKOWN`
     (2 other sites). Only recognizing the first meant "UKNOWN" was
     rendering in the UI as if it were real content. All three are now
     recognized as the same "no info" marker; this only affects
     placeholder detection, never species text, which is still shown
     with every real WDNR typo intact (e.g. "NORTHEN PIKE") per this
     project's no-"fixing" discipline.
- **Species filter** (`list_combined_species`, `list_access_points`'
  new `species` param) checks both real sources independently for a
  given access point: its own WDNR shore-fishing species text, OR (if
  linked to a V1 waterbody) V1's `species_predictions` table for that
  waterbody. A point can match via either path, both, or neither —
  never merged or cross-fabricated between sources. Verified live:
  filtering to "Walleye" returns 987 points, each matching via one real
  path or the other (`test_map_data_filters_by_species_matches_shore_fishing_and_v1_sources`).
- **Map/List toggle** — the same fetched data renders either as
  clustered map markers or as a sortable table with an expandable
  detail row per site, sharing one `buildDetailHtml()` function so the
  map popup and the list's detail panel show identical, complete
  information — every real field WDNR publishes, clearly labeled, nulls
  simply omitted rather than shown as blank or "N/A." Verified live on
  a real record (Council Grounds State Park Fishing Pier): species,
  directions, stall counts, amenities, ADA info, and manager
  contact all rendered correctly in the list's detail panel.
- 18 new tests (14 for the scraper, 5 new Flask route tests including
  a regression test for the parenthetical-truncation bug) — 226 passing
  total.

## 9. Species canonicalization

Reported directly: "we also need to deduplicate the db becuase species
are occuring more than once look at how many variations of the same
bass type we have." Checked, and confirmed real — `shore_fishing_species`
had 61 distinct raw phrases, 7 of them bass-related alone (`BASS`, `LM
BASS`, `SM BASS`, `ROCK BASS`, `WHITE BASS`, `LM & SM BASS`, `BASS (LG.
MOUTH, ROCK)`).

`analysis/v2_species_canonicalization.py` maps every one of those 61
real phrases (verified against the live database, not a guessed list)
to 30 canonical species names, stored in a new
`shore_fishing_species_canonical` table used only by the map's species
filter and dropdown — the raw WDNR text is never altered anywhere it's
actually displayed (map popups, list view), only the filter layer is
deduplicated. Rules applied, in order of confidence:

- **Real spelling typos** corrected to the right species name:
  `LAREMOUTH BASS` / `LARGEMOIUHT BASS` → Largemouth Bass, `WALEYE` →
  Walleye, `MUDKY` → Muskellunge, `STURGON` → Lake Sturgeon,
  `NORTHEN`/`NORHTERN`/`NOURTHERN PIKE` → Northern Pike.
- **Common name aligned to V1's own vocabulary**: `MUSKY`/`MUSKIE` →
  `Muskellunge` (matching `species_predictions`' own spelling), so the
  combined filter doesn't offer both as separate options for one fish.
- **Compound phrases decomposed into every species they name**, not one
  guessed choice: `LM & SM BASS` → Largemouth Bass + Smallmouth Bass;
  `BASS (LG. MOUTH, ROCK)` → Largemouth Bass + Rock Bass (a real phrase
  from site 109, Council Grounds State Park); `TROUT - BROWN & RAINBOW`
  → Brown Trout + Rainbow Trout.
- **Genuinely ambiguous terms kept undecomposed**, not guessed: `PANFISH`,
  `TROUT`, `CATFISH`, `SALMON` each become their own "(unspecified)"
  bucket. Notably, `PIKE (NORTHERN, YELLOW)` only canonicalizes to
  Northern Pike — "yellow pike" is a real historical Great Lakes
  nickname for walleye, but not confident enough in this specific
  context to assert as fact, so it's left alone rather than guessed.

Result, verified directly: the "Bass" filter went from 7 confusing
near-duplicate raw entries to 5 real distinct species (Largemouth,
Smallmouth, Rock, White, and an explicit "Bass (unspecified)" bucket
for generic mentions); the combined species dropdown (V1 + shore-fishing)
went from 73 mostly-redundant entries to 39 real distinct species.
11 new unit tests, each keyed to a real phrase actually in the database.

## 10. "Why not a match right now" explanations

Reported directly: "if its no match right now I don't exactly know why
which leads to lower trust of the system." Checked the existing
species-card UI (the one redesigned earlier this project) and confirmed
this was real — a "No match right now" badge carried zero explanation,
because the underlying model only ever generated descriptive text for
matches, never for misses.

`describe_threshold_gap()` (`analysis/v1_conditions_biology_forecast.py`),
the direct counterpart to the existing `describe_threshold_match()`,
computes how far off the current temperature is from each threshold a
species did NOT match, and in which direction — e.g. *"currently 8.2°F
/ 4.5°C below the documented activity/feeding-temperature window
(70-78°F / 21.1-25.6°C)."* For the one threshold type where "not
matching" is actually good news for the fish (`avoidance_above` — the
water simply isn't warm enough yet to trigger heat-avoidance), the
wording says so explicitly rather than framing it as a problem.

This is purely additive: `evaluate_species_at_waterbody()` computes
`non_matches` only when a species has real threshold data, a real
temperature reading exists, and nothing matched — it never changes
which species count as a match, only explains the ones that don't.
Stored in a new `species_predictions.non_match_explanation` column and
rendered in its own labeled box on the waterbody detail page ("Why not
a match right now:").

**A real schema-migration bug was caught fixing this, before it reached
the live site**: the table already existed in the production database,
so `CREATE TABLE IF NOT EXISTS species_predictions (... non_match_
explanation ...)` silently no-opped — SQLite doesn't retroactively add
columns to an existing table that way. The very first full re-run
crashed with `no column named non_match_explanation`. Fixed with an
explicit `ALTER TABLE` migration guarded by a `PRAGMA table_info` check,
with its own regression test asserting the migration runs cleanly
against a table built with the old, pre-migration schema.

## 11. Lake Michigan live water-temperature buoys

Reported directly: "lake michigan has live tempurature gagues you can
use, double check all sites for live temperature updates." Checked
first: every one of Lake Michigan's 10 real waterbody entries
(Brown, Door, Kenosha, Manitowoc, Marinette, Milwaukee, Oconto,
Ozaukee, Racine, Sheboygan counties) was using `nws_air_proxy_live` — an
**air**-temperature proxy — confirmed true before writing any code, not
assumed.

Researched real live water-temperature sources for the Great Lakes
before integrating anything:

- **NOAA CO-OPS** (the tide/water-level station network) has real
  station IDs on the WI shoreline (Milwaukee, Kewaunee, Sturgeon Bay,
  Green Bay East) — checked live, and none of them currently offer the
  `water_temperature` product (empty response from every one). Not a
  usable source right now.
- **NOAA NDBC** (National Data Buoy Center) does publish real, live
  water temperature — verified by fetching `https://www.ndbc.noaa.gov/
  data/realtime2/<station>.txt` (a public, no-API-key, standard text
  format) for every Lake Michigan-region buoy in NDBC's own active-
  station list, keeping only the ones both real (not decommissioned —
  one candidate, 45007, 404'd, confirmed dead) and currently reporting
  actual `WTMP` values. 15 real stations survived this check, from
  Marinette-adjacent Green Bay in the north to the Illinois border in
  the south — `data/v1/lake_michigan_buoy_sites.csv`.

`get_current_temperature()` gained a new step (1b, between the existing
USGS-gauge step and the CLMN/proxy fallback): for Lake Michigan
specifically, geocode a real coordinate, find the nearest of the 15
real buoys by haversine distance, and try each in distance order until
one has a reading newer than 48 hours (a real buoy going stale/offline
seasonally is expected, not an error — the fallback chain still ends
honestly at the proxy, never a fabricated value). Live-tested against
all 10 real WI Lake Michigan counties: **all 10 now resolve to a real
NDBC buoy reading**, not a proxy.

**A second real bug was caught verifying this, unrelated to the buoy
logic itself**: no read-side query in this project
(`ui/v1_review_data.py`) filters by `run_timestamp` — every one assumes
the database holds exactly one run's data, an assumption that had never
actually been tested because this script had typically only been run
once per session. Running it a second time (needed to regenerate
`non_match_explanation` across the whole database) left both runs'
rows coexisting, caught by a real regression in a live test
(`browse?name=Devils+Lake` returned 6 rows instead of 3, not the
expected 3 distinct real waterbodies). Fixed at the source: after a new
run's data is fully committed, `run_full_batch()` now deletes every
other run's rows from all four tables, so the database always holds
exactly the latest run — matching what the staleness banner and every
UI query already assumed it could. A regression test runs the batch
twice and asserts only the second run's data survives.

## 12. Additional fishing-spot sources investigated

Reported directly: "there are a lot of fishing spots I go to which are
not on the map, find a better source for each fishing spot." Two things
checked before concluding what to do:

- This project's existing boat-access count (3,135 real sites) is
  already close to WDNR's own stated inventory ("over 2,000... and over
  100 shore fishing sites") and an independent third-party estimate
  ("3,000+ public DNR ramps") — the core point-access dataset does not
  appear to be substantially undercounting WDNR's own official
  inventory of boat ramps and developed shore-fishing piers.
- Searched WDNR's ArcGIS service catalog for a genuinely different,
  complementary access dataset and found a real, promising one: **WDNR's
  non-DNR trout-stream easement layer**
  (`FM_Trout/FM_TROUT_NONDNR_EASEMENTS_WTM_Ext`) — real public fishing
  access secured on otherwise-private land along trout streams, exactly
  the kind of informal spot a local angler might use regularly that a
  boat-launch/shore-fishing-pier inventory would never capture.

**Not integrated this cycle**: this layer is polygon geometry (a stream-
reach easement area, not a discrete access point), a genuinely
different map feature than the point markers this project's map is
built around — it would need its own UI (an area/line overlay, not a
pin-and-popup) rather than fitting the existing pattern. Documented as
real, found, and deferred, per the same judgment already applied twice
to the lake-size data (Decisions #017-#018): a real data source
existing is not sufficient reason to ship a feature built on it before
it can be done well.

## 13. Honest gaps / not done this cycle

- Lake size/depth ("habitat") data — investigated twice (§2, §6),
  deferred both times. A safe fix needs either WBIC added to the V1
  waterbody universe plus a curated per-WBIC "largest polygon" rule, or
  a genuinely different data source than WDNR's 24K Hydro layer.
- Boat access (ramp/carry-in) sites have no equivalent WDNR detail page
  to enrich the way shore-fishing sites now are — confirmed no
  `boataccess.aspx`-style page exists (404) and no such field in the
  ArcGIS layer. Their species data comes only from a V1 waterbody match,
  same as before this pass.
- The real WDNR trout-stream-easement dataset found in §12 — a genuine
  candidate for more fishing spots, not yet integrated because it's a
  different (polygon) map feature type.
- Lake Michigan salmon: species data (confirmed present, not assumed --
  Chinook Salmon, Coho Salmon, Brown Trout, Rainbow Trout, Muskellunge,
  Lake Sturgeon, and others, via a direct query) was already in V1's own
  stocking-derived `species_predictions` for Lake Michigan's 10 real
  county entries before this cycle, so the main gap for salmon fishing
  specifically was the water-temperature source, addressed in §11. A
  dedicated salmon-specific research pass (e.g. depth/thermocline
  behavior, which this project's surface-temperature-only model doesn't
  capture) was not undertaken this cycle.
- The broader "environmental intelligence" part of V2's scope beyond
  access points, AIS sightings, and shore-fishing enrichment (e.g.
  weather overlays, seasonal context beyond what V1 already provides)
  — not started, and not considered essential to call this V2 slice
  complete.
