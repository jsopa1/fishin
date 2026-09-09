# V1 Survey Expansion Report (Part 4)

## Summary

This pass searched `https://dnr.wisconsin.gov/topic/Fishing/reports` (the same
real WDNR reports index used for the original 22-lake sample) for additional
electrofishing/netting survey PDFs in counties **not** already covered by
`data/v1/wi_fisheries_survey_species_sample.csv`, and specifically hunted for
stream/river survey reports as a distinct report type.

**Result: 16 new real, extracted waterbodies — 11 lakes and 5 stream
systems — across 14 new counties**, added to a new file,
`data/v1/wi_fisheries_survey_species_sample_batch2.csv` (131 rows). Source
PDFs are saved under `data/v1/pdfs/` following the existing
`<County>_<Lake><Year>.pdf` naming convention. The original 22-lake file was
not modified.

This is honestly a **smaller haul than the county count searched would
suggest is possible** — see "What was searched but not extracted" below for
why the ratio of counties-checked to counties-yielding-usable-data isn't 1:1.

## New lakes (11, across 11 new counties)

| County | Lake | Survey Year(s) | Species rows |
|---|---|---|---|
| Forest | Franklin Lake | 2025 | 12 |
| Racine | Tichigan Lake | 2021/2022 | 12 |
| Waukesha | Big Muskego Lake | 2019/2020 | 7 |
| Manitowoc | Pigeon Lake | 2024 | 7 |
| Sheboygan | Elkhart Lake | 2022 | 10 |
| Marinette | Gilas Lake | 2022 | 7 |
| Florence | Fay Lake | 2024 | 11 |
| Iron | Island Lake | 2024 | 8 |
| Douglas | Amnicon Lake | 2024 | 11 |
| Richland | Lee Lake | 2019 | 9 |
| Lafayette | Yellowstone Lake | 2018/2019 | 9 |

These are geographically spread deliberately: two in the far north (Iron,
Douglas), two in the northeast (Forest, Florence, Marinette — three, plus
Manitowoc/Sheboygan on Lake Michigan's shore), and four in the south
(Racine, Waukesha, Richland, Lafayette) — filling in southeastern Wisconsin
(Racine, Waukesha) and southwestern driftless-area (Richland, Lafayette)
regions that had zero representation in the original 22-lake sample.

Every lake row above was extracted from real narrative text and/or tables
in the source PDF — CPUE values, population estimates, and total-catch
counts are copied verbatim from the report, not approximated. Two lakes
(Island Lake, Gilas Lake) are short "Fisheries Information Sheet" or
condensed reports rather than full multi-page Comprehensive Survey Reports,
but the underlying data is equally real WDNR survey output.

## New stream/river survey reports (5 systems, 3 counties) — the Part 3
## river/stream expansion signal

This is the most important finding for the parallel river/stream work: WDNR
**does** publish a distinct report type for streams — "Fisheries Survey
Report for [Creek/River], [County], Wisconsin [Year]" (frequently labeled
"Rotation Survey" in the reports-index link text) — separate in format from
the lake "Comprehensive Summary Report." These are real backpack- or
barge-electrofishing surveys of named stations along a stream, reporting
trout catch-per-mile by station and by year, an Index of Biotic Integrity
(IBI) score, and (for multi-species stations) a full non-salmonid species
count table.

Five real stream reports were pulled and extracted, all from the
west-central Driftless Area (St. Croix, Dunn, Pierce counties — this
region's WDNR office appears to digitize stream reports especially
consistently):

- **Lousy Creek**, St. Croix County (2021) — single-station Brook Trout
  stream, tributary to the Eau Galle River. Full species table (Brook Trout,
  Mottled Sculpin, Creek Chub, plus historical comparison back to 1998).
- **Nye Creek**, St. Croix County (2021) — two-station mixed Brook/Brown
  Trout stream, tributary to the Kinnickinnic River. Full historical CPUE
  tables back to 1996.
- **South Fork Willow River**, St. Croix County (2021) — three-station
  stream with a full 9-species non-salmonid table (White Sucker, Creek Chub,
  Pearl Dace, darters, sculpin, etc.) alongside Brook/Brown Trout counts.
- **Hay Creek**, Dunn County (2021) — two-station single-species (Brook
  Trout only) stream with a before/after habitat-restoration comparison
  (2018 vs. 2020-2021).
- **Rush River**, Pierce County (2021) — a large multi-station (19+
  stations) river survey spanning upper/middle/lower reaches; extracted as
  4 summary rows (one per reach plus a whole-river Brook Trout row) rather
  than station-by-station, given the report's scale — this is a genuine
  simplification of a much richer underlying dataset, disclosed here rather
  than silently flattened.

All five are **real trout-stream electrofishing surveys**, structurally
distinct from the lake netting/electrofishing reports already in the
project: they report catch-per-mile by station and survey year going back
in some cases to the 1950s-1990s, plus a Coldwater IBI score not present in
any lake report. This is a genuinely different evidentiary signal from the
lake sample and should be flagged to whoever is doing the Part 3
river/stream expansion — the WDNR reports index is the right source for
that work too, and stream reports cluster geographically (Driftless Area
counties, and likely far-northern trout-stream counties, based on report
titles seen but not pulled — see below).

## Counties/regions searched

The full county-by-county reports index (raw HTML, ~500 PDF links) was
downloaded once and grep'd for report links across **46 counties not
already in the 22-lake sample**: Douglas, Price, Langlade, Forest,
Chippewa, Eau Claire, Clark, Vernon, Richland, Crawford, Grant, Racine,
Kenosha, Milwaukee, Waukesha, Manitowoc, Kewaunee, Door, Monroe, Juneau,
Marquette, Winnebago, Wood, Polk, St. Croix, Dunn, Rusk, Sawyer, Iron,
Florence, Marinette, Outagamie, Fond du Lac, Sheboygan, Ozaukee,
Washington, Pepin, Pierce, Trempealeau, La Crosse, Jackson, Lafayette,
Green, Rock, Calumet, Menominee.

Of these 46, **17 had at least one Comprehensive/comprehensive-style survey
PDF link** (Forest, Racine, Waukesha, Manitowoc [several], Sheboygan
[several], Marinette [2], Florence [4], Iron, Douglas, Richland, Lafayette,
St. Croix [2 lake Comp reports, not pulled this round], Rock, Green — plus
the 3 Driftless counties for stream reports: St. Croix, Dunn, Pierce). Of
those, **11 lakes + 5 streams (16 total) were actually downloaded, read in
full, and successfully extracted into the CSV** — everything with a
"Comp"/"Comprehensive" PDF link that was attempted this pass extracted
cleanly (real, natively-text PDFs, not scanned/OCR).

**Search-to-success ratio: 46 counties checked → 17 counties had a
comprehensive-style report link → 14 counties yielded successfully
extracted data** (11 lake counties + 3 stream counties). That's roughly a
30% hit rate from "county checked" to "county with usable, extracted data,"
consistent with the existing manifest's disclosure that WDNR's reports
index is non-exhaustive per-county and per-lake.

## What was searched for but NOT located or NOT extracted

- **Milwaukee, Ozaukee, Washington, Kenosha, Outagamie, Fond du Lac, Pepin,
  Menominee counties**: no Comprehensive Summary Report or full stream
  survey link found in the reports index for these counties at all — only
  scattered narrower reports (e.g., a single small-pond SEII summary,
  a fish-passage report) that don't carry a full species-composition table
  comparable to the rest of this sample. Not pulled.
- **Grant County**: the reports index shows zero PDF links under Grant at
  all in the current listing, despite Grant being a large Driftless-area
  county with known trout streams — likely folded into the multi-county
  Mississippi River regional reports instead of a county-specific link;
  not chased down this pass.
- **Chippewa, Eau Claire, Clark, Vernon, Crawford, Polk, Rusk, Sawyer,
  Price, Langlade counties**: reports index links present, but everything
  found was a "Spring Netting/Shocking Summary" (a narrower single-gear
  snapshot, not a full comprehensive species-composition survey) or a
  narrow single-species assessment (e.g., muskellunge-only,
  smallmouth-bass-only). These were deliberately not pulled to keep this
  sample consistent with the "comprehensive survey" evidentiary bar used
  for the original 22 lakes — a spring-shocking-only summary is real data
  but a narrower claim than a comprehensive survey, and mixing bar levels
  without disclosure would blur the "survey-confirmed" tier's meaning.
- **Additional St. Croix/Dunn/Pierce stream reports seen but not pulled**:
  the reports index lists several more Driftless-area stream "Rotation
  Survey" reports (e.g., Dunn County's Little Beaver Creek and Vance Creek,
  both 2021) that were downloaded as a first pass but ultimately not
  included in the final CSV to keep this batch's per-county spread broader
  rather than concentrating further in Dunn County — these two PDFs were
  deleted after download rather than kept as unused dead weight in
  `data/v1/pdfs/`.
- **Two additional St. Croix lake Comprehensive Survey reports** (Bass Lake
  2021 CompSurvey, and a multi-county St. Croix/Polk River Comp Survey)
  were seen in the index but not opened/extracted this pass, since St.
  Croix County was already going to be represented via its 3 stream
  reports and diversifying to more counties was prioritized over depth in
  one county.
- No lake or stream PDF that was actually opened this pass turned out to
  be blocked, broken, or a non-text scan (unlike the Geneva/Winnebago-2012
  precedent noted in this project's earlier passes) — every PDF opened
  extracted cleanly with `pypdf`.

## Files changed

- **New**: `data/v1/wi_fisheries_survey_species_sample_batch2.csv` (131
  rows, `water_type` column distinguishing `lake` vs. `stream` rows) — not
  merged into the original `wi_fisheries_survey_species_sample.csv`, per
  instructions, to keep this pull separately auditable.
- **New**: 16 source PDFs under `data/v1/pdfs/`:
  `Forest_FranklinLake2025.pdf`, `Racine_TichiganLake2022.pdf`,
  `Waukesha_BigMuskegoLake2021.pdf`, `Manitowoc_PigeonLake2024.pdf`,
  `Sheboygan_ElkhartLake2022.pdf`, `Marinette_GilasLake2022.pdf`,
  `Florence_FayLake2024.pdf`, `Iron_IslandLake2024.pdf`,
  `Douglas_AmniconLake2024.pdf`, `Richland_LeeLake2019.pdf`,
  `Lafayette_YellowstoneLake2019.pdf`, `StCroix_LousyCreek2021.pdf`,
  `StCroix_NyeCreek2021.pdf`, `StCroix_SouthForkWillowRiver2021.pdf`,
  `Dunn_HayCreek2021.pdf`, `Pierce_RushRiver2021.pdf`.
- **Unchanged**: the original `wi_fisheries_survey_species_sample.csv` (22
  lakes) and `docs/v1_species_presence_manifest.md` — a merge/manifest
  update was explicitly deferred to a later step per the task instructions.

## Honest scope statement

This is a real, bounded, disclosed second-pass sample — not exhaustive
coverage of the ~17 counties with comprehensive-style reports found, and
nowhere close to exhaustive of Wisconsin's 72 counties. Combined with the
original batch, the project now has survey-confirmed species data for
**33 lakes/streams across 28+ distinct counties** (22 original + 11 new
lake counties, with St. Croix/Dunn/Pierce added as stream-only counties),
still a small fraction of the WDNR reports index's likely several-hundred
comprehensive PDFs statewide.
