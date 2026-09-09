# V0 Dataset Manifest — Step 2 (Dataset Build)

Retrieval date for all items below: **2026-09-08**, unless otherwise noted.
Scope: Pewaukee Lake (Waukesha Co.), Delavan Lake (Walworth Co.), Geneva Lake (Walworth Co.),
Lake Winnebago (Winnebago Co.), and Wisconsin waters of Lake Michigan (Milwaukee/Racine/Kenosha
nearshore + Green Bay, as reported by WDNR).

All files are under `C:\Users\jsopa\Documents\fishin1\fishin\fishin\data\v0\`. Raw downloaded
source files (PDFs, raw JSON/NDBC text) are under `data\v0\pdfs\` and `data\v0\raw\`.

**Headline finding, stated plainly up front:** creel-survey-style outcome data (angler catch/harvest
per unit effort) with real accessible WDNR sources was found for **only 1 of the 4 named inland
lakes' analog** — actually for **0 of the 4 inland lakes** (no creel surveys exist for
Pewaukee, Delavan, or Geneva; Winnebago has fisheries-survey CPUE but not angler creel) — and for
**Lake Michigan (WI waters + Green Bay)**, which has a rich, long-running (1969–2024), publicly
documented creel survey. This asymmetry is real, not a search failure: WDNR does not run creel
surveys on these three small SE Wisconsin lakes; creel surveys are labor-intensive and WDNR
concentrates them on Lake Michigan/Green Bay, Lake Superior, the Winnebago System (trawl/fyke,
not creel), and a rotating set of "put-and-take" or heavily-fished lakes elsewhere in the state.

---

## 1. Outcome data (creel / catch-rate)

### 1a. Lake Michigan + Green Bay (Wisconsin waters) — REAL, STRONG
- **Source:** WDNR annual "Open Water Sportfishing Effort and Harvest" reports (the Lake Michigan
  Creel Survey, running since 1969).
  - `data/v0/pdfs/LakeMichigan_SportHarvest_2024.pdf` —
    https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/LM_LakeMichiganSportHarvestReport2024.pdf
    (covers 2015–2024 annual tables, 2024 monthly detail)
  - `data/v0/pdfs/LakeMichigan_SportHarvest_2022.pdf` —
    https://dnr.wisconsin.gov/sites/default/files/topic/LM_LakeMichiganSportHarvestReport2022.pdf
    (covers 2013–2022 annual tables, 2022 monthly detail)
- **Extraction method:** Direct PDF text/table extraction (native text layer, not OCR) via the
  Read tool. Full text and all tables extracted successfully; no OCR or scanning was needed.
- **Structured output CSVs:**
  - `lake_michigan_creel_effort_by_location_annual.csv` — angler-hours by county
    (Kenosha/Racine/Milwaukee, the nearshore-to-scope counties) + WI-wide total, 2013–2024, with
    standard deviations as reported.
  - `lake_michigan_creel_harvest_rate_annual_by_species.csv` — annual harvest, harvest-rate
    (fish/angler-hour, i.e. the CPUE-equivalent outcome variable), for "all salmonids combined"
    and yellow perch, 2013–2024.
  - `lake_michigan_creel_monthly_by_species_2022_2024.csv` — sub-annual (bi-monthly/monthly)
    harvest and effort by species (coho, yellow perch, walleye shown; more species available in
    source PDFs but not all transcribed) for 2022 and 2024, all fishery types combined.
- **Row counts:** 51 rows (effort), 24 rows (species harvest rate), 30 rows (monthly).
- **Date range:** 2013–2024 (annual), monthly detail for 2022 and 2024 only (the two report years
  actually read in full; 2013–2021, 2023 monthly tables exist in the same PDFs' underlying source
  years but were not separately re-fetched — the 2024 report includes a full monthly breakdown for
  2024, the 2022 report for 2022).
- **Important caveat:** this is a **harvest rate** (fish kept per angler-hour), which is the
  standard creel-survey catch-rate metric WDNR publishes — not total-catch CPUE (released fish are
  not counted in harvest rate). This is the best available real proxy for catch rate on Lake
  Michigan; flag this definitional point for step 4.
- **Caveat on effort-as-predictor:** angler-hours are the denominator of the harvest-rate outcome
  itself, so — consistent with the research doc's own caution on candidate #16 — do not treat
  effort as an independent predictor of harvest rate without addressing this structural coupling.

### 1b. Lake Winnebago — REAL, but NOT angler creel (fisheries-survey CPUE instead)
- **Source:** WDNR Lake Winnebago Bottom Trawling Assessment Report, 2023 —
  `data/v0/pdfs/WinnebagoTrawling_2023.pdf` —
  https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/LakeWinnebagoBottomTrawlingReport2023.pdf
  (also downloaded but not parsed: `WinnebagoTrawling_2024.pdf`, the 2024 edition, as a raw source
  for future extension).
- **Extraction method:** Direct PDF text extraction. The report's Appendix 3 (adult fish, top
  species) and Appendix 4 (young-of-year fish) contain full year-by-year data tables
  (1986–2023), which were transcribed directly from the extracted table text.
- **Structured output CSVs:**
  - `winnebago_trawl_adult_cpue_1986_2023.csv` — adult catch-per-trawl for freshwater drum, yellow
    perch, emerald shiner, walleye, white bass, white sucker, channel catfish, common carp,
    bluegill, quillback. 38 rows (1986–2023).
  - `winnebago_trawl_yoy_cpue_1986_2023.csv` — young-of-year catch-per-trawl for trout perch,
    freshwater drum, black crappie, walleye, yellow perch, white bass, emerald shiner, gizzard
    shad, sauger, bluegill. 38 rows (1986–2023).
- **What this is NOT:** this is a standardized **fisheries bottom-trawl research survey** (research
  vessel, 138 net pulls/year, same 3 weeks each August–October since 1986), reported as
  fish-per-trawl-tow. It is **not** an angler creel survey and does not measure angler catch rate,
  effort, or success. It is a legitimate, real, long-running WDNR abundance index and may be a
  reasonable proxy predictor variable (e.g., walleye/perch abundance index as a predictor of
  angler success) but should **not** be used as the outcome variable for a "catch rate" model
  without relabeling the research question. This distinction should be made explicit in step 4/5.
- **No angler-creel data exists for Lake Winnebago** in the WDNR fisheries survey reports index;
  none was found in this pass.

### 1c. Pewaukee Lake, Delavan Lake, Geneva Lake — NOT FOUND (reclassify as not testable in V0)
- WDNR's "Fisheries Survey Reports" index (https://dnr.wisconsin.gov/topic/Fishing/reports),
  organized by county, was checked directly (Waukesha County and Walworth County sections, full
  list read via browser automation).
  - **Waukesha County section:** no Pewaukee Lake report of any kind listed (comprehensive,
    electrofishing, or creel). Reports exist for Upper/Middle Genesee Lake, Lake Keesus, Big
    Muskego, Ashippun, Nagawicka, Lac La Belle, Oconomowoc Lake — but not Pewaukee.
  - **Walworth County section:** no Delavan Lake report. One **Geneva Lake Comprehensive Survey,
    2015** is listed (electrofishing-based fisheries survey, not creel) —
    https://p.widencdn.net/lcgdv3/Reports_WalworthGeneva2015Comprehensive.
- **Geneva Lake 2015 survey — attempted, not extractable.** This report is hosted on a Widen
  Digital Asset Management PDF.js viewer (`embed.widencdn.net`) that renders the PDF client-side
  via JavaScript rather than serving a static PDF file. `curl` downloads returned an HTML wrapper
  page, not PDF bytes, both from the public link and its embed iframe target. Browser automation
  loaded the outer wrapper but could not read text out of the cross-origin iframe's canvas-rendered
  PDF viewer. Saved as
  `data/v0/pdfs/WalworthGeneva_2015_Comprehensive_UNREADABLE_viewer_wrapper.html` for reference.
  **This is a genuine tooling limitation, not a "no data exists" case** — a human with a browser
  could read this PDF; it was not extractable with the tools available in this pass.
- **Conclusion:** no accessible, extractable creel or fisheries-survey catch-rate data was
  obtained for Pewaukee Lake or Delavan Lake. Geneva Lake has one 2015 comprehensive survey that
  is known to exist but could not be extracted. **All three lakes are reclassified from the step-1
  research doc's implicit assumption of "outcome data will exist for all 4 named lakes" to:
  outcome data not obtained in V0 for Pewaukee, Delavan, or Geneva.**

---

## 2. Predictor data — what was obtained

### 2a. Water temperature (candidate #1)
- **Lake Michigan:** obtained as part of the NDBC buoy 45007 daily aggregate (see 2f below) —
  `WTMP_mean`/`WTMP_max` columns in `lake_michigan_ndbc_45007_daily.csv`.
- **Inland lakes:** **NOT obtained.** USGS NWIS was queried directly
  (`waterservices.usgs.gov/nwis/site` with `seriesCatalogOutput=true`) for the specific USGS lake
  monitoring sites found on Winnebago, Geneva, and Delavan (see 2h below) — **none of them have a
  water-temperature parameter (USGS parameter code 00010) on record.** Only gage height (00065,
  i.e. water level) is available at these sites. No USGS site of type "LK" was found for Pewaukee
  Lake at all. CLMN (Citizen Lake Monitoring Network) volunteer temperature data was not queried
  in this pass (time-boxed); it remains a theoretical possibility per the research doc but is
  unverified. **Reclassify inland-lake water temperature: not obtained in V0; downgrade from "YES"
  to "considered, not obtained — CLMN volunteer data unverified, USGS confirmed unavailable."**

### 2b. Season / spawning window (candidate #3) — trivially available, not separately fetched
- Fully computable from WDNR regulation dates and calendar/date fields already present in the
  creel and stocking data obtained above. No separate file created; flag as buildable in step 3/4
  from existing date columns.

### 2c. Time of day (candidate #4) — not applicable at this data granularity
- The Lake Michigan creel data obtained is aggregated to monthly/annual harvest rates, not
  individual angler-interview timestamps, so time-of-day cannot be derived from what was
  extracted. Sunrise/sunset tables remain computable in principle but were not fetched.

### 2d. Moon phase (candidate #11) — not fetched; fully computable, deferred to step 3/4
- No external data needed; deterministic astronomical calculation. Not built in this pass since it
  requires the outcome data's exact dates to key against, which do not exist at daily resolution
  for the inland lakes (see part 1).

### 2e. Wind speed / direction (candidates #5, #6) — REAL, obtained for Lake Michigan only
- Obtained as part of NDBC buoy 45007 daily aggregate (`WDIR_mean/max`, `WSPD_mean/max`,
  `GST_mean/max` in `lake_michigan_ndbc_45007_daily.csv`). See 2f.
- **Inland lakes: not obtained.** NWS api.weather.gov / NCEI CDO station data for stations near
  Pewaukee/Delavan/Geneva/Winnebago was not queried in this pass due to time constraints; flagged
  as a real, likely-accessible source per the research doc but unverified/not pulled in V0.

### 2f. Barometric pressure + trend, cloud cover (candidates #7, #9, #10) — partial
- Barometric pressure: obtained for Lake Michigan via NDBC buoy (`PRES_mean/max` in the same
  daily-aggregate file); trend is directly computable from this day-over-day series in step 3/4.
- Cloud cover: **not obtained** (NDBC buoys do not report cloud cover; would require NWS/NCEI ASOS
  station data, not queried in this pass).
- Inland lakes: **not obtained** for either pressure or cloud cover (same NWS/NCEI gap as 2e).

### 2g. Precipitation (candidate #8) — NOT obtained
- Not queried in this pass (NWS/NCEI daily precipitation totals) for either Lake Michigan or
  inland-lake stations, due to time constraints.

### 2h. Great Lakes wave height (candidate #14) — REAL, obtained
- **Source:** NOAA NDBC buoy **45007** (South Michigan buoy, WI nearshore), standard meteorological
  historical data files, years 2015–2024:
  `https://www.ndbc.noaa.gov/view_text_file.php?filename=45007h{YYYY}.txt.gz&dir=data/historical/stdmet/`
- **Extraction method:** Bulk download of the raw fixed-width/whitespace-delimited annual text
  files (`data/v0/raw/ndbc_45007_YYYY.txt`, ~2015–2024, one file per year, some years partial —
  buoy is removed seasonally in winter, consistent with the research doc's noted coverage gap),
  aggregated in Python to **daily mean/max** for wave height (WVHT), dominant/average wave period
  (DPD/APD), wind speed/gust/direction (WSPD/GST/WDIR), sea-level pressure (PRES), air temp (ATMP),
  and water temp (WTMP). Missing-value sentinel codes (99.0/999.0) were filtered out before
  averaging.
- **Output:** `lake_michigan_ndbc_45007_daily.csv` — **1,941 daily rows**, spanning 2015–2024
  (open-water season only each year; buoy removed in winter).
- **Applies to:** Lake Michigan (WI waters) only, per scope — this buoy has no bearing on the
  inland lakes.

### 2i. Great Lakes water level (candidate #15) — REAL, obtained
- **Source:** NOAA CO-OPS station 9087057 (Milwaukee) —
  `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter` (`product=daily_mean`, `datum=IGLD`).
- **Extraction method:** Direct JSON API calls, one per year 2013–2024, parsed to CSV.
- **Output:** `lake_michigan_coops_9087057_water_level_daily.csv` — **4,382 daily rows**, full
  daily coverage, 2013–2024 (matches the Lake Michigan creel-data date range exactly).

### 2j. Fishing pressure / effort (candidate #16) — embedded in outcome data
- Already present as `angler_hours` columns in the Lake Michigan creel CSVs (part 1a). Per the
  research doc's own flag, this is a companion/potentially-endogenous variable relative to harvest
  rate, not an independent external predictor — carried forward as a caution for step 4, not
  re-fetched separately.

### 2k. Stocking history (candidate #17) — REAL, confirmed accessible for all 4 inland lakes
- **Source:** WDNR Fisheries Management Information System stocking database —
  https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/Index. This is an interactive
  ASP.NET tool; direct AJAX endpoints were identified via network-request inspection
  (`GetCounties`, `GetStockedWBICs?countyCode=NN`, `LoadResults`).
- **Confirmed present via `GetStockedWBICs`** (waterbody-lookup API call) for all four target
  lakes: Pewaukee Lake (Waukesha, county code 68), Delavan Lake and Geneva Lake (Walworth, county
  code 65), Lake Winnebago (Winnebago, county code 71). This directly overturns nothing in the
  research doc (which already rated this candidate YES) but confirms it per-lake as requested.
- **Extracted in full:** `pewaukee_lake_stocking_1987_2025.csv` — **65 records**, 1987–2025,
  species/strain/age-class/number-stocked/avg-length, sourced from the live query-result table
  (`county=Waukesha, waterbody=PEWAUKEE LAKE`), read directly off the rendered results table (100
  of 128 total available records were on the first results page at page-size 100; the remaining
  ~28 older records, back to the site's earliest data, were not transcribed due to time budget).
  Records show sustained walleye and muskellunge stocking, consistent with WDNR management
  practice for this lake.
- **Not extracted (time-boxed) but confirmed accessible:** Delavan Lake, Geneva Lake, and Lake
  Winnebago stocking records. The same query mechanism works for these lakes (confirmed via the
  `GetStockedWBICs` lookup returning each lake by name); full record extraction was not completed
  for these three in this pass. This is a real, near-zero-marginal-cost extension for a future
  pass — flagged, not fabricated.
- **Lake Michigan stocking** (trout/salmon program) is coordinated through a related but distinct
  WDNR/GLFC system and was not queried in this pass.

---

## 3. Updated testable-vs-not classification

| # | Candidate | Step-1 status | Step-2 outcome | Updated status |
|---|-----------|---------------|-----------------|------------------|
| 1 | Water temperature | YES (needs per-lake check) | Lake Michigan: obtained (buoy). Inland lakes: USGS confirmed **no temp parameter** at the Winnebago/Geneva/Delavan sites found; no USGS site for Pewaukee at all. | Lake Michigan: **testable**. Inland lakes: **not obtained in V0** (CLMN unverified). |
| 3 | Season / spawning window | YES | Trivially derivable from dates already in outcome data | **testable** (Lake Michigan only, since only it has outcome data) |
| 4 | Time of day | YES (trivial) | Outcome data extracted is monthly/annual aggregate, not per-interview | **not usable at this data resolution** |
| 5 | Wind speed | YES | Lake Michigan: obtained (buoy). Inland: not queried. | Lake Michigan: **testable**. Inland: **not obtained**. |
| 6 | Wind direction | YES (shoreline effect NOT testable, per step 1) | Lake Michigan: raw direction obtained (buoy) | Lake Michigan: **testable** (raw direction only, not shoreline-accumulation). Inland: **not obtained**. |
| 7 | Cloud cover | YES | Not queried (no NWS/NCEI pull this pass) | **not obtained** |
| 8 | Precipitation | YES | Not queried | **not obtained** |
| 9 | Barometric pressure (absolute) | YES (weak hypothesis) | Lake Michigan: obtained (buoy) | Lake Michigan: **testable**. Inland: **not obtained**. |
| 10 | Barometric pressure trend | YES (weak hypothesis) | Same buoy series allows trend computation | Lake Michigan: **testable**. Inland: **not obtained**. |
| 11 | Moon phase | YES (trivial) | Not built (needs daily outcome dates; inland lakes lack daily outcome data) | Lake Michigan: **buildable in step 3/4**. Inland: moot (no outcome data). |
| 2 | Ice-out date | NOT testable (step 1) | Not queried in this pass | unchanged: **not tested** |
| 12 | Water clarity/turbidity (inland) | caution flag | Not queried (CLMN not pulled) | unchanged: **not tested** |
| 13 | Dissolved oxygen (inland) | NOT testable | Not queried | unchanged: **not testable** |
| 14 | Lake Michigan wave height | YES | **Obtained** (NDBC buoy 45007, 1,941 daily rows) | **testable** |
| 15 | Lake Michigan water level | YES | **Obtained** (NOAA CO-OPS 9087057, 4,382 daily rows) | **testable** |
| 16 | Fishing pressure/effort | YES (endogeneity caution) | Embedded in Lake Michigan creel data | **testable with caution** (Lake Michigan only) |
| 17 | Stocking history | YES | **Obtained in full for Pewaukee** (65 records); confirmed accessible but not extracted for Delavan/Geneva/Winnebago | Pewaukee: **testable**. Others: **accessible, extraction incomplete**. Moot for lakes with no outcome data (Delavan, Geneva). |
| 18 | Bathymetry/structure | NOT testable | Not pursued | unchanged: **not testable** |
| 19 | Air temp / front passage | YES | Air temp obtained for Lake Michigan (buoy ATMP); front-passage composite not built | Lake Michigan: **buildable**. Inland: **not obtained**. |

**Net effect on the pipeline:** V0 evaluation (step 4) is realistically only possible for
**Lake Michigan (WI waters)**, where a real outcome variable (harvest rate) and 6+ real predictor
variables (water temp, wind speed/direction, pressure ± trend, wave height, water level, air
temp, effort) all exist with overlapping 2015–2024 daily/monthly coverage. For the three named SE
Wisconsin inland lakes, **no creel/catch-rate outcome data was obtained**, so no predictor
evaluation is possible for them in V0 regardless of predictor-data availability. Lake Winnebago has
a real, rich fisheries-abundance CPUE dataset (1986–2023) but it answers a different question
(species abundance from a standardized research survey) than "angler catch rate," and pairing it
against inland-lake weather/water predictors was not attempted here since no matching daily
predictor series were pulled for Winnebago in this pass.

---

## 4. What was attempted but failed or was not pursued, with reasons

| Attempt | Result | Reason |
|---|---|---|
| WDNR creel survey for Pewaukee Lake | Not found | No such report exists in WDNR's fisheries survey reports index; WDNR does not appear to creel-survey this lake. |
| WDNR creel survey for Delavan Lake | Not found | Same as above. |
| WDNR creel survey for Geneva Lake | Not found (only a 2015 electrofishing comprehensive survey exists, not creel) | Same as above. |
| WDNR creel survey for Lake Winnebago | Not found (trawl/fyke surveys exist instead) | WDNR's Winnebago System monitoring uses standardized trawl/fyke assessments, not angler creel, for this system. |
| Geneva Lake 2015 comprehensive survey PDF text extraction | Failed | Hosted via a Widen DAM JavaScript PDF.js viewer (`embed.widencdn.net`); `curl` returns an HTML shell, not the PDF; browser automation could not read the cross-origin iframe's rendered content. Tooling limitation, not a data-availability limitation. |
| USGS water temperature for Winnebago/Geneva/Delavan | Confirmed absent | Directly checked each site's parameter catalog (`seriesCatalogOutput=true`); only gage height (00065) is offered, no parameter 00010 (temperature). |
| USGS site for Pewaukee Lake | None found | `waterservices.usgs.gov/nwis/site` query for WI lake-type sites returned no Pewaukee entry. |
| CLMN (Citizen Lake Monitoring Network) Secchi/temp/DO/ice data, per-lake | Not attempted | Time-boxed; flagged in the research doc as needing per-lake verification, still unverified after this pass. |
| NWS api.weather.gov / NCEI CDO station pulls (wind, pressure, cloud cover, precipitation, air temp) for inland lakes | Not attempted | Time-boxed; would require identifying the nearest ASOS/AWOS station per lake and paginated API calls; deferred. |
| Lake Michigan stocking records (trout/salmon program) | Not attempted | Different WDNR/GLFC system than the general Fish Stocking database used for inland lakes; deferred. |
| Delavan/Geneva/Winnebago full stocking record extraction | Confirmed accessible, not completed | Same WDNR stocking tool as Pewaukee (confirmed via `GetStockedWBICs` lookup); time-boxed after completing the Pewaukee example. |
| Moon phase / sunrise-sunset computation | Not built | Deferred to step 3/4 since it is deterministic and cheap to compute once exact outcome-data dates are finalized; not worth pre-building without knowing final date keys. |

---

## 5. File index

```
data/v0/
  lake_michigan_creel_effort_by_location_annual.csv          (51 rows, 2013-2024)
  lake_michigan_creel_harvest_rate_annual_by_species.csv      (24 rows, 2013-2024)
  lake_michigan_creel_monthly_by_species_2022_2024.csv        (30 rows, 2022 & 2024)
  lake_michigan_ndbc_45007_daily.csv                          (1,941 rows, 2015-2024)
  lake_michigan_coops_9087057_water_level_daily.csv           (4,382 rows, 2013-2024)
  winnebago_trawl_adult_cpue_1986_2023.csv                    (38 rows, 1986-2023)
  winnebago_trawl_yoy_cpue_1986_2023.csv                      (38 rows, 1986-2023)
  usgs_inland_lakes_gage_height_daily.csv                     (1,095 rows: Winnebago 2023, Geneva 2023, Delavan 2009)
  pewaukee_lake_stocking_1987_2025.csv                        (65 rows, 1987-2025)
  aggregate_ndbc.py                                            (aggregation script used to build the NDBC daily CSV)
  pdfs/
    LakeMichigan_SportHarvest_2024.pdf
    LakeMichigan_SportHarvest_2022.pdf
    WinnebagoTrawling_2023.pdf
    WinnebagoTrawling_2024.pdf                                 (downloaded, not yet parsed)
    WalworthGeneva_2015_Comprehensive_UNREADABLE_viewer_wrapper.html  (failed extraction, kept for reference)
  raw/
    coops_milwaukee_2013.json ... coops_milwaukee_2024.json    (NOAA CO-OPS raw API responses)
    ndbc_45007_2015.txt ... ndbc_45007_2024.txt                (NDBC raw standard-meteorological annual files)
    usgs_winnebago_gageheight_2023.json
    usgs_geneva_gageheight_2023.json
    usgs_delavan_gageheight_2009.json
```

## 6. Honesty summary

- Real, usable, multi-year outcome data was obtained for **Lake Michigan only**.
- Real predictor data with genuine daily/annual resolution overlapping the Lake Michigan outcome
  data was obtained for: water temp, wind speed/direction, barometric pressure (+ computable
  trend), wave height, water level, air temperature, and fishing effort — all for Lake Michigan.
- For the three named SE Wisconsin inland lakes, **no creel or angler catch-rate data exists** in
  WDNR's public reports as far as this pass could determine — this is the single most important
  finding for deciding whether step 4 (evaluation) is possible for those lakes: **it is not**,
  regardless of predictor availability, because there is no outcome variable to predict.
- Lake Winnebago has strong historical fisheries-survey (trawl) abundance data, but it is not an
  angler catch-rate outcome and was not paired with matching daily predictor data in this pass.
- Stocking history was fully extracted for Pewaukee Lake as a proof of concept and confirmed
  accessible (not yet extracted) for the other three lakes.
- Weather-API pulls (NWS/NCEI) for the inland lakes and cloud cover/precipitation for anywhere
  were not attempted in this pass — this is a time-budget limitation, not a confirmed
  unavailability, and is explicitly flagged as such rather than silently omitted.
