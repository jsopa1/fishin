# V1 River/Stream Coverage Report (Part 3)

**Status:** research and documentation only, per task instructions. No code
written, no changes to `analysis/v1_conditions_biology_forecast.py`. No
STATE.md update, no commit, no action taken — same hard-stop gate as the
rest of this project (per `CLAUDE.md`).

**Scope:** extending V1's conditions-and-biology tool from lakes to
Wisconsin rivers/streams. This report covers three things: (1) real-time
water-temperature data quality for streams, (2) real river/stream
species-presence data, and (3) a per-species physiology-transfer
assessment (lake-derived vs. stream-relevant vs. genuinely general),
plus trout-stream classification data.

---

## 1. River/stream water-temperature source: `data/v1/usgs_wi_water_temp_sites.csv`

- **185 total sites, confirmed by direct file read:** 177 rows tagged
  `site_type=ST` (stream/river) and 8 tagged `LK` (lake). Grep-confirmed
  count of `,ST,` rows in the file: 177.
- This table lists sites with **daily-value (dv)** parameter-00010
  (water temperature) coverage per its own construction — dv coverage is
  not the same claim as live instantaneous (iv) coverage, and this pass
  verified that distinction directly rather than assuming dv implies iv.

### Spot-check methodology and results

Queried the USGS Instantaneous Values (IV) web service directly
(`https://waterservices.usgs.gov/nwis/iv/?format=json&sites=<SITE>&parameterCd=00010&period=P1D`)
for **8 stream sites spread across the state** (northwest, north-central,
central, northeast, southeast/urban Milwaukee, southwest, south)
on 2026-09-09:

| Site No. | Name | Region | IV result today |
|---|---|---|---|
| 04026005 | Bois Brule River near Lake Superior | far north | **No current IV values** — `timeSeries` object exists (site/method registered) but `values` array empty over both P1D and P7D windows |
| 04073500 | Fox River at Berlin | central | **Live** — 23.7°C returned |
| 05340500 | St. Croix River at St. Croix Falls | northwest | **Live** — 23.3°C returned |
| 04087170 | Milwaukee River at Mouth, Milwaukee | southeast/urban | **No current IV values** — registered site/method, empty values array |
| 05407000 | Wisconsin River at Muscoda | southwest | **No `timeSeries` object at all** for parameter 00010 via IV (empty `timeSeries: []`) — confirmed real DV coverage exists instead (`nwis/dv` query for the same site/parameter/period returns a populated `timeSeries` object) |
| 05430500 | Rock River at Afton | south | **No `timeSeries` object at all** via IV (same pattern as Muscoda); DV query confirms a real, populated DV time series exists |
| 05357245 | Trout River at Trout Lake, Boulder Junction | north-central | **No current IV values** — registered site/method, empty values array |
| 04069500 | Peshtigo River at Peshtigo | northeast | **Live** — 23.2°C returned |

**Result: 3 of 8 spot-checked sites (37.5%) confirmed genuinely live
today** (Fox River/Berlin, St. Croix Falls, Peshtigo). **3 of 8** have a
registered IV method/site but returned zero current readings (Bois
Brule, Milwaukee River mouth, Trout River) — these may be
seasonally/temporarily offline sensors, or IV-capable equipment that
simply isn't reporting right now; not distinguishable from this pass's
data alone. **2 of 8** (Muscoda, Afton — both large-river USGS gauges)
have **no IV parameter-00010 service at all**, confirmed to instead have
real DV (daily-value) coverage only, verified by a direct successful DV
query returning a populated time series for both.

**Conclusion: the dv-coverage listing in `usgs_wi_water_temp_sites.csv`
does NOT guarantee live iv coverage.** Roughly half of spot-checked sites
have no current-moment reading available via IV; a real "conditions
right now" narrative tool cannot assume live temperature for an
arbitrary site drawn from this table — it would need a live per-site IV
check (or a DV-based "most recent daily reading" fallback, which this
pass confirms is real and available for at least Muscoda and Afton) with
explicit "no live reading available" handling for sites like Bois Brule.
This mirrors the mixed-coverage pattern V1 already documented for lakes
(`docs/v1_data_coverage_report.md`) — streams are not automatically
better just because there are more sites in the table.

**37.5% (3/8) is not necessarily statewide-representative** — this was 8
of 177 sites, geographically spread but not a random/statistically
powered sample. Flagged as a directional finding, not a precise
statewide live-coverage percentage.

---

## 2. River/stream species-presence data

### Confirmed already in hand: statewide stocking data

`data/v1/wi_stocking_statewide_2011_2025.csv` — verified by direct file
read: 24,684 lines total (24,683 records + header), real WDNR stocking
data pulled from `https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/LoadResults`,
retrieved 2026-09-09, spanning stocking years 2011-2025. Per this task's
starting context, 8,005 of these records cover 690 distinct
stream/river/creek/brook/branch-named waterbodies (identified by name
keyword) — this figure was supplied as already-verified context for this
task and was not re-derived in this pass; the file's real existence,
structure, and header schema (`source_url, retrieval_date,
stocking_year, source_type, county, waterbody, local_wb_name, species,
strain, age_class, number_stocked, avg_length_in`) were directly
re-confirmed by reading the file this pass.

This stocking data is **positive-only evidence** (per the existing V1
species-presence discipline in `CLAUDE.md`/`docs/v1_species_presence_manifest.md`):
a stocked species is confirmed present; an unstocked species is not
confirmed absent, since self-sustaining stream populations (e.g. wild
Class I trout streams) are stocked less, not more.

### New this pass: real WDNR stream/river fisheries survey reports

Verified via direct fetch of `https://dnr.wisconsin.gov/topic/Fishing/reports`
and a targeted web search, then spot-checked two report PDFs with a
direct `curl -I` request (not just a search-summary claim):

- **`Reports_AdamsWoodJuneau2025AreaTroutStreamReport.pdf`** — HTTP 200,
  `Content-Type: application/pdf`, 3,179,193 bytes, confirmed real and
  fetchable. Covers 42 trout streams / 283 miles in Adams, Wood, Juneau
  counties (per search-result summary of the page).
- **`LaCrosseMonroeVernonCrawford2024streamreport.pdf`** — HTTP 200,
  `Content-Type: application/pdf`, 1,506,088 bytes, confirmed real and
  fetchable. Electrofishing-based wadable-stream trout population
  report for La Crosse, Monroe, Crawford, Vernon counties.
- Additional real report titles found on the WDNR reports page/search
  (not individually fetched this pass, listed for reference only —
  **titles only, not independently verified by direct fetch**):
  Namekagon River smallmouth bass survey (2025), Black River gamefish
  survey (2024), North Branch Crawfish River smallmouth bass survey
  (2025), Baraboo River hoop net survey (2021), Tomahawk River
  smallmouth bass survey (2025), Vilas Tamarack Creek 2024 stream
  shocking report, Langlade/Lincoln 2024 trout stream trend report,
  Pierce/St. Croix/West Dunn 2024 wadable trout streams report,
  Marathon/Portage 2024 trout survey summary, Bayfield/(LS) 2024 wadable
  trout streams report, Dane/Sugar River 2020-2021 watershed trout
  management report, Brown/Thornberry Creek 2022 trout stream report.

**Conclusion: real, distinct-from-lake-surveys, stream/river
electrofishing survey reports exist and are publicly fetchable from
WDNR.** This is a genuine additional real data source beyond the
stocking data and beyond what was in hand at the start of this task,
though none of these PDFs were parsed for their actual species/count
data in this pass (research/verification only, per task scope) — that
extraction is a gap for a future pass, not done here.

---

## 3. Trout stream classification data

**Real, found, and directly confirmed via WDNR's own page** (first-party
`dnr.wisconsin.gov`, not a secondary source):
`https://dnr.wisconsin.gov/topic/Fishing/trout/streamclassification`

Confirmed content (fetched directly this pass):
- **Class 1** — "high-quality trout waters," natural reproduction
  sustains wild populations without stocking. **5,365 miles (40% of
  Wisconsin's total trout stream mileage).**
- **Class 2** — limited natural reproduction, stocking required to
  maintain the fishery, often producing larger fish. **6,120 miles
  (46%).**
- **Class 3** — marginal habitat, no natural reproduction, requires
  annual stocking, minimal carryover. **1,786 miles (14%).**

**Downloadable dataset confirmed to exist:** the WDNR Open Data Portal
lists a **"Classified Trout Stream Lines"** dataset
(`https://data-wi-dnr.opendata.arcgis.com/datasets/wi-dnr::classified-trout-stream-lines/about`,
also mirrored at GeoData@Wisconsin,
`https://geodata.wisc.edu/catalog/WIDNR-a95d409126754d349ecc565698683d9e9`,
described there as "Classified Trout Stream Lines Wisconsin, 2021"). The
dataset's title, mirrored cataloging across two independent
geodata-indexing services, and consistency with the real mileage figures
on WDNR's own primary page together confirm this is a real, accessible
GIS dataset — a line/shapefile-style layer, not a lake-style point/CSV
site table.

**Caveat, disclosed rather than glossed over:** this pass fetched the
dataset's landing page but the page's rendered content did not confirm
programmatic record count, format list, or an active REST endpoint
within this pass's fetch (the ArcGIS FeatureServer URL guessed from the
dataset ID this pass returned an "Invalid URL" error — the correct
service URL was not tracked down). **The dataset's real existence is
confirmed; a working direct-download/API URL for pulling it into this
project's pipeline is NOT confirmed this pass** — that is left as a
concrete next step (visit the Open Data Portal page in a browser to get
the actual REST/GeoJSON/Shapefile download link) rather than guessed at.

---

## 4. Per-species physiology stream-vs-lake transfer table

Read `docs/v1_physiology_research_candidates.md` in full (all 26
species-numbered sections plus the diel-behavior table). Classification
below is based on what the cited study/citation is actually anchored to
— a stream/river/tributary field site, a lake field site, or a
lab/aquaculture/general context not tied to either.

| # | Species | Stream/river-relevant citation present? | Lake-only citation flagged? | Notes |
|---|---|---|---|---|
| 1 | Walleye | No direct stream-temperature citation. Diel/light behavior (Ryder 1977) is water-body-general, not stream-specific. | **Yes** — feeding/activity preferendum from Trout Lake, WI (Coutant 1977a); seasonal-movement/DO study is a lake telemetry study | Spawning-trigger numbers (Hokanson 1977, Wisconsin) are not explicitly tied to lake vs. tributary spawning migration in the document's text — walleye are well known to spawn in tributary streams generally, but the doc doesn't cite a stream-specific study for this species. **Flagged as unverified for stream use** beyond the general spawning-temperature number, which is not body-of-water-specific in its citation. |
| 2 | Yellow Perch | No | **Yes** — all preferendum values (Lake Michigan, Silver/Trout/Muskellunge Lakes, WI) are lake field sites | Growth-optimum values are lab-derived (Jobling, Casselman, Leidy & Jenkins) — general, not lake-or-stream-specific. |
| 3 | Largemouth Bass | No | **Yes** — preferendum values from Norris Reservoir (TN), Lake Monona (WI) — reservoirs/lakes | Spawning trigger (Carlander 1977, Minnesota) not body-of-water-specified in the doc's text. |
| 4 | Smallmouth Bass | Partial — spawning study is Baie du Dore, **Lake** Huron (a bay, still lake-classified) | **Yes** — Lake Michigan harbor field study for feeding temperature | Smallmouth do use rivers/streams for spawning in some populations, but no river-specific citation is present here — **flagged as unverified for river use.** |
| 5 | Northern Pike | Partial — "Wisconsin Lake" cited by name for spawning trigger (explicitly a lake) | **Yes** — spawning study explicitly labeled "Wisconsin Lake"; preferendum is lab-derived | Pike also spawn in flooded marsh/backwater habitat generally, but the document's specific citation is lake-anchored — **flagged as unverified for river/stream use.** |
| 6 | Muskellunge | No | **Yes** — Stony Lake (Ontario) preferendum, growth-optimum studies not water-body-specified but the named field sites are lakes | Muskellunge do use river systems in Wisconsin (e.g. Chippewa Flowage tributaries) but no stream-specific citation appears in the doc. |
| 7 | Black Crappie | No | **Yes** — Lake Monona, WI preferendum (explicitly a lake) | |
| 8 | Bluegill | No | **Yes** — Lake Monona, WI preferendum; spawning table not water-body-specified in text but centrarchid nesting behavior is classically lake/pond-associated | |
| 9 | Chinook Salmon | **Yes, directly** — Lake Michigan preferendum values ARE the primary source, but the document explicitly notes a "thermocline-tracking mechanism" and elsewhere this project's broader context (per CLAUDE.md/other V1 docs, not re-derived here) treats Chinook tributary spawning runs (e.g. into the Kewaunee, Manitowoc, Root rivers) as real, well-documented behavior | **Yes for the feeding-temperature numbers specifically** — Lake Michigan preferendum is a lake-context number, not validated for tributary conditions during the fall spawning run, when Chinook are physically present in rivers under very different thermal/flow conditions than the open lake | **This is the single most important stream-relevant gap in the document**: Chinook/Coho salmon spend real time in Wisconsin's Lake Michigan tributary rivers each fall specifically to spawn, but every temperature threshold in the document for this species is a Lake Michigan open-water number. **Flagged explicitly: not verified to transfer to river conditions during the spawning run.** |
| 10 | Coho Salmon | Same tributary-run behavior as Chinook (general knowledge, not separately cited in the doc) | **Yes** — same Lake Michigan preferendum pattern as Chinook | Same flag as Chinook: real river presence during fall run, but only lake-context temperature numbers are cited. |
| 11 | Brown Trout | **Yes, partially** — this is Wisconsin's premier wild stream trout; many of the state's Class I/II trout streams (Section 3 above) are managed specifically for wild Brown Trout. However, the document's own cited preferendum/spawning studies (Scott & Crossman 1973, Cherry et al. 1977, Spigarelli & Smith 1976, Harrelson et al. 1984, Brown 1974) are Lake Michigan thermal-discharge and lab studies, **not stream field studies** | **Yes, materially** — most of the numeric citations trace to Lake Michigan thermal-discharge sites, not the wild stream populations this species is best known for in Wisconsin | **Real gap, explicitly flagged**: despite Brown Trout being the archetypal Wisconsin stream species, the document's actual numeric citations are lake-context. Spawning-trigger number (6.7-8.9°C, S.E. Ontario) is not body-of-water-specified in the doc's text but Brown Trout spawning is classically a stream/redd-building behavior — this is the one number in the doc most likely to be genuinely stream-relevant even though not explicitly labeled as such, but this pass did not verify the underlying Scott & Crossman 1973 source directly to confirm a stream field site. |
| 12 | Lake Trout | No | **Yes** — all field sites are lakes (Point Beach/Lake Michigan, White Lake, Lac La Ronge, Cayuga Lake, Lake Superior); spawning site "Algonquin Park, Ontario" also lake-associated (lake trout do not use streams) | Lake Trout are a genuinely lake-obligate species (do not spawn in rivers) — **not a stream-relevance gap, this species is correctly lake-only by its actual biology**, not an evidentiary gap. |
| 14 | Sauger | **Yes, directly** — preferendum table explicitly includes "stream field" (22.6°C) and "Wabash R., IN" (21.3°C) readings | No lake-only exclusivity — scatter includes reservoir and river sites | One of the few species in the document with an explicit stream-context citation already present. |
| 15 | White Crappie | Partial — "Ohio R." fall reading (10.4°C) is a river citation; other rows are lab/reservoir | Reservoir readings (Kansas Reservoir) present alongside | Mixed — has at least one real river data point, not purely lake-only. |
| 16 | Rock Bass | No | **Yes** — "Wisconsin lakes" and Lake Monona, WI explicitly named | Rock bass are common in both lakes and streams in Wisconsin; no stream-specific number cited. |
| 17 | Pumpkinseed | No | Ambiguous — cited sites are "Lake, N.Y." and "Georgian Bay, Ontario" (a bay of Lake Huron) | Lake-leaning, not stream-verified. |
| 18 | White Bass | No | Ambiguous — "power plant discharge site," lab — not clearly lake or river | Not clearly assignable either way; treat as general/unverified for either environment. |
| 19 | Rainbow Trout/Steelhead | **Yes, materially** — the document's own text explicitly discusses "Wisconsin's stocked rainbow trout include a steelhead strain that runs Lake Michigan tributaries" and flags this as "well-documented general steelhead biology" though **not independently verified against a Lake Michigan-specific source** in that pass | **Yes** — the numeric preferendum/spawning values themselves trace to Point Beach NGS (Lake Michigan discharge-adjacent), Scott & Crossman, lab studies — not river field sites, despite steelhead literally spawning in Wisconsin's Lake Michigan tributary rivers each spring | The document itself already explicitly flags this exact lake-vs-river transfer gap as "single-source-speculative for the Lake Michigan-specific run-timing claim" — this pass's independent read agrees with and reinforces that existing flag, and extends it to the numeric temperature values (not just the run-timing claim), since those too are non-tributary sourced. |
| 20 | Brook Trout | **Yes, partially** — spawning-trigger studies explicitly cite **"SW Ontario streams (Witzel & MacCrimmon 1983)"** — a genuine stream field study | Some preferendum sites are lakes (Moosehead Lake ME, Redrock Lake Ontario) alongside "southern Ontario streams" and "Lake Michigan" | **Brook Trout has the clearest genuinely stream-sourced citation in the entire document** (Witzel & MacCrimmon 1983, SW Ontario streams, for spawning trigger) — usable for Wisconsin's many wild brook trout streams (a large share of the state's Class I water) with real, if not Wisconsin-specific, stream-field backing. Feeding/preferendum values remain a mix of lake and stream sites, not purely stream-verified. |
| 21 | Cisco/Lake Herring | No | **Yes** — "Wisconsin" spawning site is understood as lake-context per this species' obligate deep-cold-lake life history (cisco do not spawn in rivers) | Correctly lake-only by actual biology, not an evidentiary gap, similar to Lake Trout. |
| 22 | Lake Whitefish | No | **Yes** — South Bay/Lake Huron, Moosehead Lake, Lake Erie/Ontario, Point Beach/Lake Michigan, Bay of Quinte/Lake Ontario — all lake sites | Correctly lake-only by actual biology (whitefish are lake-obligate). |
| 23 | White Sucker | Partial — "Connecticut R." and "Jack L., Ontario" cited together (Corbett & Powles 1983) — one of the two sites is a river | White suckers are well known to run up small streams to spawn each spring | Mixed evidence; the Connecticut R. citation gives some real river grounding, though not Wisconsin-specific. |
| 24 | Channel Catfish | No spawning-temperature citation is stream-specific (Scott & Crossman 1973, EPA 1974 — not water-body-labeled in the doc's text) | Ambiguous, not clearly lake-anchored either | Channel catfish are common in Wisconsin's larger rivers (Mississippi, Wisconsin, Fox) as well as lakes; the diel-feeding study (Lake Kasumigaura, Japan) is explicitly a **lake** study despite the species' strong river presence in Wisconsin — **flagged: diel-behavior citation is lake-context, not verified to transfer to Wisconsin's actual river catfish populations.** |
| 25 | Freshwater Drum | No | **Yes** — Lake Monona, WI (explicitly named) and Norris Reservoir | Drum are present in the Mississippi/Wisconsin/Fox rivers in real numbers but no river-context citation exists in the doc. |
| 26 | Burbot | No | Ambiguous — "surface water temperature," not body-of-water-labeled | Burbot are present in some larger WI rivers but the doc's citation is not location-specified either way. |
| 27 | Fathead Minnow | No | Ambiguous — "Quebec lake," "outdoor experimental pool, Pennsylvania" — mixed lake/lab, not river | Minimal stream relevance either way; noted as forage-species-only in the doc already. |
| 28 | Lake Sturgeon | **Yes, directly and strongly** — the Richelieu River, Quebec peer-reviewed spawning study is explicitly a **river** field study (spawning below a dam); WDNR's Wolf River (a real Wisconsin river) spawning-run viewing-location context is cited in the doc's own text | No — this species' only usable citation set is river-anchored | **The one species in this document whose core physiology citation is already stream/river-context, not lake** — directly usable for Wisconsin river conditions without a lake-to-river transfer question. Feeding-temperature/DO data remain unfound for any water-body type (a pre-existing, disclosed gap). |
| — | Barometric pressure | N/A (excluded-as-folklore, not water-body-relevant) | N/A | Unchanged. |

### Summary counts

- **Species with an explicit stream/river field-study citation already
  present in the document:** Sauger, White Crappie (partial, one river
  reading), Rainbow Trout/Steelhead (explicitly flagged by the doc
  itself as a real but unverified tributary-run mechanism), Brook Trout
  (genuine SW Ontario stream spawning study), White Sucker (partial,
  Connecticut R. reading), Lake Sturgeon (strongly, Richelieu River +
  Wolf River context). **6 of 26.**
- **Species that are correctly lake-only by their actual biology (not an
  evidentiary gap — these fish do not spawn/live in streams in a way
  that would need river data):** Lake Trout, Cisco/Lake Herring, Lake
  Whitefish. **3 of 26.**
- **Species with real, documented tributary/stream behavior in Wisconsin
  (spawning runs, wild stream populations) whose CITED numeric
  thresholds in this document are nonetheless lake-only and NOT verified
  to transfer to river conditions — the most consequential flag in this
  table:** Chinook Salmon, Coho Salmon, Brown Trout, Rainbow
  Trout/Steelhead (numeric values specifically, beyond the
  already-flagged run-timing gap), Walleye (partial), Northern Pike
  (partial), Smallmouth Bass (partial), Channel Catfish (diel-behavior
  citation specifically). **Roughly 6-8 of 26**, depending on how
  strictly "documented tributary behavior" is counted.
- **Species with no stream-vs-lake distinction findable either way
  (ambiguous/general lab or unlabeled citations):** Pumpkinseed, White
  Bass, Burbot, Fathead Minnow, Channel Catfish (spawning number
  specifically). **~5 of 26.**
- **Remaining species (lake-preferendum citations, no known strong
  stream-specific behavior in Wisconsin, not flagged as a high-priority
  gap):** Yellow Perch, Largemouth Bass, Muskellunge, Black Crappie,
  Bluegill, Rock Bass, Freshwater Drum. **7 of 26.**

**Bottom line for whoever builds the river/stream narrative logic next:**
do NOT apply this document's lake-derived preferendum/feeding-temperature
numbers to river/stream sites without an explicit disclosure that the
number is lake-derived and unverified for moving water. This is
especially consequential for Chinook Salmon, Coho Salmon, Rainbow
Trout/Steelhead, and Brown Trout, since these are exactly the species
most likely to be queried for a Wisconsin Lake Michigan tributary river
site (e.g. Fox River at Berlin, Manitowoc River, Milwaukee River — all
real sites in `usgs_wi_water_temp_sites.csv`) during their fall/spring
run, which is precisely when lake-open-water numbers are least likely to
reflect actual river conditions.

---

## 5. Explicit gap list

- **Live (IV) water-temperature coverage for streams is confirmed
  partial, not complete.** Only 3 of 8 spot-checked sites had a live
  reading today; 2 of 8 have no IV parameter-00010 service at all
  (DV-only); 3 of 8 have a registered IV method that returned no current
  values. This was 8 of 177 sites — the other 169 stream sites were not
  individually checked this pass. A full per-site IV-availability sweep
  of all 177 sites was not performed (out of this pass's time/scope) and
  is a real gap for whoever builds the river narrative logic.
- **The 690-waterbody stream stocking-coverage figure was not
  independently re-derived this pass** — it was supplied as
  already-verified context at the start of this task and only the
  underlying file's real existence/structure was re-confirmed here, not
  the specific count.
- **Stream/river WDNR survey PDFs found by title and spot-checked for
  reachability (2 of ~13 titles found), but not parsed for their actual
  species/abundance data.** Extracting real species-presence data from
  these PDFs (the way `wi_fisheries_survey_species_sample.csv` was
  apparently built for lakes) is a real next step, not done here.
- **A working direct-download/API endpoint for the "Classified Trout
  Stream Lines" GIS dataset was not confirmed this pass** — the
  dataset's real existence and WDNR's own summary mileage figures are
  confirmed, but the actual REST/GeoJSON/Shapefile URL needed to pull
  the data into this project's pipeline was not found (one guessed
  ArcGIS FeatureServer URL failed). Needs a follow-up visit to the Open
  Data Portal page itself (better done in a browser than by URL-guessing)
  to get the real service endpoint.
- **No county-by-county or stream-by-stream matching was done between
  the 177 USGS stream sites, the 690 stocking-confirmed stream
  waterbodies, and the classified-trout-stream mileage data.** Whether
  any of the 177 USGS gauge sites sit on a Class I/II/III designated
  trout stream was not checked this pass — a real, useful cross-check
  for a future pass.
- **The physiology-transfer table above is this pass's own reading and
  judgment call**, applied consistently but not independently reviewed
  by a second pass — flagged as reasoning applied to already-real
  citations, not a new primary-source claim in itself.
- **Underlying primary sources for the "not water-body-specified in the
  document's text" citations (e.g. Northern Pike's Scott & Crossman
  1973, Brown Trout's Scott & Crossman 1973 spawning study) were not
  independently re-fetched this pass** to check whether the original
  study itself was stream- or lake-based even though the physiology doc
  doesn't say — this pass worked only from what
  `v1_physiology_research_candidates.md` itself discloses, per task
  scope (verify what's there, don't re-derive the whole physiology
  document).

---

*End of report. Research and documentation only, per task instructions —
no code changes, no STATE.md update, no commit, no action taken without
explicit CEO approval, consistent with `CLAUDE.md` and DECISIONS.md #005.*
