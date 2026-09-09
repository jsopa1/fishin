# V1 Source Discovery Report — Additional Wisconsin Data Sources

Retrieval date: **2026-09-09**. This is a source-discovery-and-verification pass only — **no
data was pulled or extracted** for the actual V1 build. Every source below was checked against
`docs/v0_research_candidates.md`, `docs/v0_physiology_research_candidates.md`, and
`docs/v0_dataset_manifest.md` to avoid re-reporting sources already catalogued (WDNR CLMN, WDNR
Fish Stocking database, NWS api.weather.gov, NOAA NDBC, NOAA CO-OPS, WDNR fisheries-reports index
as a *creel*-survey source, USGS NWIS in general, WDNR Surface Water Data Viewer facts pages).
Where a URL was actually fetched/curled in this pass, that is stated explicitly; where a source
looks promising but could not be verified, that is also stated explicitly rather than assumed.

---

## Part 1 — Species-presence sources (beyond the stocking database)

### 1a. WDNR Fisheries Survey Reports — "Comprehensive Summary Report" format (electrofishing/netting, ACTUAL OBSERVED species composition) — **NEW, REAL, VERIFIED, HIGH VALUE**

- **What it measures:** Actual observed species composition and relative abundance from
  standardized electrofishing (spring bass/panfish shocking, boom shocking) and netting (spring
  fyke netting for walleye/pike/muskellunge) surveys — CPUE per species (fish per mile
  electrofished, fish per net night), size structure (PSD, length-frequency), age/growth,
  population estimates (mark-recapture), and year-over-year trend tables back to as early as 2003
  in some reports. This is the real, DNR-observed analog to "what species are actually in this
  lake and how abundant," which is a materially stronger signal than the stocking database (which
  only shows what was *put in*, not what was caught/confirmed present).
- **Access method (verified working):** `https://dnr.wisconsin.gov/topic/Fishing/reports` —
  organized alphabetically by all 72 WI counties, each linking to individual PDF reports
  (`https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_<County><Lake><Year><Type>.pdf`).
  **Directly fetched and read one full example in this pass**:
  `Reports_GreenLakeLittle GreenLake2024Comp.pdf` (Little Green Lake, Green Lake County, 2024
  Comprehensive Summary Report) — a native-text (not scanned/OCR-needed) 12-page PDF, successfully
  extracted in full via the Read tool. Confirmed real tables for Northern Pike, Walleye,
  Muskellunge, Largemouth Bass, Bluegill, Pumpkinseed, Black Crappie, Yellow Perch, plus a named
  "Other Species" list (brown bullhead, common carp, golden shiner, green sunfish, white sucker,
  yellow bullhead) and the lake's full stocking history table appended at the end.
- **Geographic coverage:** Statewide by design (all 72 counties have a reports section), though
  the page itself notes these are "not complete listings of all DNR survey efforts" — coverage is
  a real but non-exhaustive sample, concentrated on lakes with active fisheries management
  interest. This pass confirmed a genuinely new lake/report (Little Green Lake, Green Lake County)
  not previously pulled in any prior V0 cycle document, demonstrating the index extends well
  beyond the SE Wisconsin lakes checked before.
- **Species coverage:** Whatever species the survey's gear catches — in the verified example:
  Northern Pike, Walleye, Muskellunge, Largemouth Bass, Bluegill, Pumpkinseed, Black Crappie,
  Yellow Perch as primary tables, plus bycatch species noted narratively.
- **Recency:** Point-in-time snapshot surveys, repeated on a multi-year cycle (the Little Green
  Lake example shows comparison years 2003/2008/2013/2018/2024) — this is **historical/periodic**,
  not real-time, but is the most current a fisheries-survey species record gets for a given lake
  (most recent survey year varies by lake, up to 2024 in the verified example).
- **Caveat:** This is the *same report family* already used for Lake Winnebago's trawl survey
  (`WinnebagoTrawling_2023.pdf`) and attempted-but-failed for Geneva Lake's 2015 comprehensive
  survey (blocked by a Widen DAM JS viewer) in V0 — so the *source itself* is not new, but this
  pass newly confirms (a) the Comprehensive Summary Report PDF format used for most lakes (as
  opposed to Geneva's older Widen-hosted format) is a standard, static, directly-downloadable,
  natively-extractable PDF — not blocked by the same JS-viewer tooling limitation — and (b) the
  reports index has vastly more statewide coverage than the SE Wisconsin/Winnebago-only sample
  used so far. This is the single most valuable new finding of this pass for the species-presence
  question.

### 1b. WDNR "Find a Lake" fish species list (`apps.dnr.wi.gov/lakes/lakepages`) — real but low-signal — **PARTIALLY NEW**

- **What it measures:** A general, non-quantified "fish present" species checklist per lake
  (already used in V0 for Pewaukee/Delavan as a fallback when no creel data existed, per
  `v0_lake_characteristics.md`) — flagged here explicitly as NOT creel/survey-derived, just a
  general presence list.
- **Access method:** `https://apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic=<WBIC>&page=facts`
  — same tool already used in V0 for physical characteristics; the fish-species-present field on
  the same page was not the focus of the V0 pull but is present.
- **Geographic coverage:** Statewide (any lake with a WBIC).
- **Recency:** Static/not dated — best treated as "current management-list" rather than a survey
  snapshot.
- **Verdict:** Real and accessible, but lower evidentiary value than 1a (no CPUE/abundance, no
  survey date) — useful only as a fallback when no fisheries survey report (1a) exists for a lake.

### 1c. WDNR Open Data Portal (ArcGIS Hub, `data-wi-dnr.opendata.arcgis.com`) — real infrastructure, fish-specific layer not confirmed — **NEW, PARTIALLY VERIFIED**

- **What it measures:** A statewide ArcGIS Hub of DNR GIS layers, downloadable as
  shapefile/GeoJSON/CSV or queryable via a REST feature-service API (bulk/programmatic access,
  unlike the one-PDF-per-lake reports approach). **Verified accessible**: the portal's search API
  (`https://data-wi-dnr.opendata.arcgis.com/api/search/v1`) responded with valid JSON in this
  pass. Confirmed real datasets found via web search: "Outstanding and Exceptional Lakes" (211
  records), "High-Quality Lakes & Large Rivers" (826 records), "305(b) Assessed Lakes" (Clean
  Water Act assessment status), "Classified Trout Spring Ponds," "Public Boat Access Sites."
- **Geographic coverage:** Statewide, bulk/vector format (a real advantage over one-PDF-per-lake
  sources for programmatic use).
- **Species coverage:** **Not confirmed in this pass** — a search specifically for a bulk
  fish-survey-species or fish-stocking feature layer on this portal did not surface one; the
  datasets found in this pass are lake water-quality/classification layers, not species-presence
  layers. **This should be treated as "infrastructure exists and is real, but a fish-species-
  specific layer on it was not found/verified" — do not assume one exists without a further,
  dedicated search.**
- **Verdict:** Real and worth flagging as infrastructure for Part 3 (lake characteristics) even
  though its species-presence utility is unconfirmed.

### 1d. WDNR Natural Heritage Inventory (NHI) — checked, REJECTED for this purpose

- **What it measures:** Rare, threatened, and endangered species occurrences (plants, animals,
  natural communities) by county/township — `https://dnr.wisconsin.gov/topic/nhi/calypso/portal`.
  **Verified accessible** (200 status on the portal URL).
- **Verdict: REJECTED.** This database is scoped to rare/endangered species, not general gamefish
  presence — essentially never useful for the common sportfish (walleye, bass, panfish, pike,
  muskellunge) this project's narrative tool targets. Logged here only to document it was checked
  and explicitly ruled out, not overlooked.

---

## Part 2 — Water-temperature sources (real sensor/monitoring data, not weather forecasts)

### 2a. North Temperate Lakes LTER (NTL-LTER) / Environmental Data Initiative (EDI) — REAL, narrow geographic scope — **NEW**

- **What it measures:** High-frequency (sub-hourly) water-temperature depth profiles from
  instrumented buoys/rafts with thermistor chains, some running continuously since 1989.
- **Access method (verified accessible, not fully load-tested):** Data are archived at the
  Environmental Data Initiative repository. **Verified**: the EDI data-package page for one
  dataset returned HTTP 200
  (`https://portal.edirepository.org/nis/mapbrowse?packageid=knb-lter-ntl.5.24`). Individual
  dataset landing pages exist at `lter.limnology.wisc.edu/dataset/...` for each buoy/lake.
  **Caveat found during this pass:** a web search result stated that, beginning July 30, 2026, EDI
  requires authentication for programmatic REST API access as an anti-DoS measure — this was
  reported by a search summary, not independently confirmed by a direct authenticated-API test in
  this pass, so treat as **plausible but unverified**; the human-facing data-package pages
  (dataset browse/download) were confirmed accessible without authentication.
- **Geographic coverage:** Narrow and specific — Sparkling Lake, Trout Lake, Trout Bog, Crystal
  Lake (Vilas/Oneida County area, the "Northern Highland Lake District" in north-central WI), plus
  Lake Mendota (Dane County, via the related SSEC buoy program, see 2c below). **This is NOT
  statewide** — it is a small, fixed set of long-term research lakes.
  Only useful if the target lake for a given narrative is one of these specific research lakes.
- **Species coverage:** N/A (water temperature only).
- **Recency:** Continuous/high-frequency historically, but data-release cadence to the public
  archive (EDI) is likely batch/annual, not live-streaming — **not confirmed as real-time** in
  this pass; best treated as "continuous historical record with an unknown publication lag,"
  distinct from the live buoy displays in 2c/2e below.

### 2b. USGS NWIS — expanded/corrected finding for Wisconsin lake water temperature (parameter 00010) — **NEW, REAL, DIRECTLY QUERIED**

This directly extends and partially corrects the V0 dataset manifest's finding ("USGS confirmed
no temp parameter" — that finding was correct for the *specific* Winnebago/Geneva/Delavan gage-
height sites checked in V0, but this pass ran a fresh statewide query and found real WI lake sites
that do carry parameter 00010).

- **Access method (live-tested in this pass):**
  `https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd=WI&siteType=LK&parameterCd=00010&hasDataTypeCd=dv`
  — a direct site-service query for all Wisconsin sites of type "LK" (lake) carrying daily-value
  water temperature. This returned **8 real WI lake sites**, verified by direct curl in this pass:

  | USGS site # | Name | Water-temp record range (verified via `seriesCatalogOutput=true`) |
  |---|---|---|
  | 05429000 | LAKE MONONA AT MADISON, WI | **dv: 2023-09-10 to 2026-09-08 (978 obs); iv (instantaneous/real-time): 2026-05-11 to 2026-09-09 (today)** |
  | 423755088341700 | DELAVAN LAKE INLET-BASE SITE-NEAR LAKE LAWN, WI | dv: 1994-04-15 to 1994-09-29 only (158 obs) — historical-only |
  | 455946089415704 | LITTLE ROCK LAKE (WATER TEMP) NEAR WOODRUFF, WI | dv: 1984-04-25 to 1986-09-25 — historical-only |
  | 04085500 | CEDAR LAKE NEAR KIEL, WI | dv: 1974–1977 — historical-only |
  | 054279485 | STRICKER'S POND AT MIDDLETON, WI | dv: 1981–1982 — historical-only |
  | 453100089343002 | LAKE CLARA NEAR TOMAHAWK, WI | not individually re-verified this pass; present in site list |
  | 461342091561002 | ROUND LAKE NEAR GORDON, WI | not individually re-verified this pass; present in site list |
  | 462458091274402 | EAST EIGHTMILE LAKE NEAR IRON RIVER, WI | not individually re-verified this pass; present in site list |

- **Headline finding: Lake Monona (Madison, Dane County) has a genuinely LIVE, current USGS water-
  temperature gauge.** Directly confirmed via a live instantaneous-values (`iv`) API call in this
  pass (`https://waterservices.usgs.gov/nwis/iv/?format=json&sites=05429000&parameterCd=00010&period=P1D`),
  which returned real data through **2026-09-09 (today's retrieval date)**. This is the first
  confirmed real-time USGS water-temperature source for a WI lake found across this project's V0
  and V1 research passes — the V0 pass checked different sites (gage-height-only sites on
  Winnebago/Geneva/Delavan) and never found a live temperature series; this one exists on a
  different lake (Monona) that V0 did not check.
- **Correction/nuance on Delavan Lake specifically:** V0 concluded "no water-temperature parameter
  at the Delavan site checked." This pass found a *different* USGS site number for Delavan
  (423755088341700, "Delavan Lake Inlet") that **does** carry parameter 00010 — but only for a
  single 1994 season (158 daily values), not current. So the corrected, precise statement is:
  Delavan Lake has at least one USGS site with historical (1994) water temperature, but no current/
  live temperature site was found for it — V0's practical conclusion (no usable current temp data
  for Delavan) still stands, but the "confirmed absent" framing was too strong; it should read
  "confirmed historical-only, not current."
- **Geographic coverage:** Statewide search performed (`stateCd=WI`), but real usable (temperature-
  bearing) sites are sparse — 8 lake sites total found statewide, and only 1 of the 8 checked in
  detail (Monona) is current/live. The other ~7 are historical-only snapshots from the 1970s–1990s.
- **Recency:** Mixed — Monona is live/real-time; all others found are historical-only. This is an
  important nuance for the V1 narrative tool, which requires *current* data — Monona is usable,
  the rest generally are not without further per-site verification (Lake Clara, Round Lake, East
  Eightmile Lake were not individually re-checked for their date ranges in this pass and should be
  verified before use).

### 2c. UW-Madison SSEC Lake Mendota Buoy — REAL, live, single-lake — **NEW**

- **What it measures:** Near-real-time wind speed/direction, air temperature, dew point/relative
  humidity, a vertical water-temperature profile, dissolved oxygen, chlorophyll, and phycocyanin.
- **Access method (verified accessible):** `https://metobs.ssec.wisc.edu/mendota/buoy/text_popup/`
  returned HTTP 200 and valid HTML in this pass (a UW-Madison Space Science and Engineering Center
  / RAIN platform page). This is a human-facing display page; a machine-readable API/CSV endpoint
  was not separately located/tested in this pass.
- **Geographic coverage:** Lake Mendota (Dane County) only.
- **Recency:** Near-real-time (buoy display), seasonal (buoy deployed only during ice-free months,
  standard for this class of instrument, consistent with the NDBC/GLOS buoys already known to be
  seasonally removed).

### 2d. Clean Lakes Alliance / "LakeForecast.org" (Yahara CLEAN partnership) — REAL, dashboard-only, unverified programmatic access — **NEW**

- **What it measures:** Near-shore water temperature and clarity, collected by ~96 trained
  volunteers at 87 nearshore + 7 offshore monitoring stations, plus formal water-quality testing at
  25 public beaches, across all five Yahara lakes.
- **Access method (verified accessible, dashboard only):** `https://lakeforecast.org/cleanlakesalliance/`
  returned HTTP 200 and displayed a live temperature reading (75°F at fetch time) in this pass.
  **No API, CSV export, or machine-readable data format was found or confirmed in this pass** — it
  presents as a human-facing map/dashboard (also available as a mobile app). This should be logged
  as "real, accessible-to-a-human, but programmatic/bulk access NOT verified" rather than assumed
  available.
- **Geographic coverage:** The five Yahara lakes — Mendota, Monona, Waubesa, Kegonsa, Wingra (all
  Dane County) — plus 25 Madison-area beaches.
- **Recency:** Real-time/near-real-time during the active season, but **seasonal only** — testing
  runs Memorial Day through Labor Day; at the time of this pass's fetch, the page itself stated
  "all beaches are now considered closed for the season," consistent with the September retrieval
  date.
- **Verdict:** A real example of a "lake district/association"-style local monitoring partnership
  with genuinely accessible (if dashboard-only, not API) data, as the task asked to check for. This
  is the one clear example of this category found and verified in this pass; a broader survey of
  additional individual WI lake districts/associations was not performed beyond this one (explicit
  time-boxing — see summary/limitations below).

### 2e. GLOS Seagull API (Great Lakes Observing System) — REAL, working REST API, verified live — **NEW, HIGH VALUE**

- **What it measures:** Real-time and historical buoy observations across the Great Lakes,
  including water temperature, wind, and (on some platforms) water-quality parameters (dissolved
  oxygen, chlorophyll, pH, conductivity) beyond what NDBC's standard meteorological files provide.
- **Access method (directly tested and confirmed working in this pass):**
  - `https://seagull-api.glos.org/api/v1/parameters` — returned real JSON parameter metadata
    (confirmed via direct curl).
  - `https://seagull-api.glos.org/api/v1/obs-datasets?platform_id=153` — returned real dataset
    metadata for a Wisconsin-relevant platform (see below).
  - Per public documentation found (not independently re-verified beyond the calls above):
    `/api/v1/obs` (historical observations by platform/dataset), `/api/v1/obs-latest` (latest
    reading, refreshed ~every 10 minutes), `/api/v2/obs` (column-format variant).
  - No authentication was required for the endpoints actually tested in this pass.
- **Wisconsin-relevant platforms confirmed real:**
  - **Atwater 20-meter buoy (ATW20)**, obs_dataset_id 2 — ~2 km offshore of Milwaukee's Atwater
    Beach, operated by UW-Milwaukee School of Freshwater Sciences; WMO/NDBC-shared ID 45013;
    30-minute-interval meteorological + water-quality sensors + a vertical temperature-sensor
    string. (This overlaps with the already-known NDBC network in terms of raw met/water-temp
    data, but the Seagull API additionally exposes water-quality parameters — DO, chlorophyll,
    etc. — not in NDBC's standard meteorological files, which is new value.)
  - **Salmon Unlimited Wisconsin buoy (Racine)**, platform 153 — ~6 miles SE of Racine, a
    partnership between Salmon Unlimited of Wisconsin (Racine chapter) and UW-Milwaukee SFS,
    deployed since 2022, in-season (recreational season) only.
- **Geographic coverage:** Lake Michigan nearshore Wisconsin waters (Milwaukee, Racine area
  confirmed; UWM SFS operates a broader "fleet" of buoys per search results, not individually
  enumerated in this pass).
  **This is genuinely new value for the already-in-scope Lake Michigan/nearshore area** — an
  alternate, richer, actively-maintained real-time API distinct from NDBC/CO-OPS, worth adding as
  a redundant/supplementary source, especially for water-quality parameters NDBC doesn't carry.
- **Recency:** Live/real-time (obs-latest updates ~every 10 minutes per documentation found),
  seasonal (buoys removed in winter, consistent with the Lake Michigan buoy pattern already known
  from NDBC 45007).

### 2f. Water Action Volunteers (WAV) — REAL, streams not lakes, partially verified — **NEW but limited applicability**

- **What it measures:** Volunteer-collected stream (not lake) water quality including continuous
  hourly water temperature at some stations via deployed thermistor loggers.
- **Access method:** `https://wav.extension.wisc.edu/` (UW-Madison Division of Extension /
  WDNR partnership) — **verified accessible** (200 status), and its data-dashboard page
  (`wateractionvolunteers.org/data/dashboard/`) 302-redirects to
  `wav.extension.wisc.edu/data/dashboard/`, which also returned 200 in this pass. The specific
  claim of a downloadable/CSV dataset was reported via web search summary but **not independently
  confirmed by finding an actual export/API endpoint** in this pass — logged as accessible-to-a-
  human, download/API mechanism unverified.
- **Geographic coverage:** Streams and rivers statewide (86,000+ miles per program description) —
  **not lakes**. Relevant to this project only indirectly, e.g. as an inflow-temperature proxy for
  a lake fed by a monitored stream, which is a stretch use-case not directly applicable to the
  "per-lake water temperature" need.
- **Verdict:** Real program, real data exists, but **out of scope for this project's lake-specific
  need** except as a minor/indirect proxy; flagged for completeness per the task's instruction to
  check WAV specifically, but not recommended as a primary V1 source.

### 2g. "Wisconsin Buoy Network" as a named single entity — NOT FOUND, does not appear to exist

- The task asked to check for a "Wisconsin Buoy Network" specifically. **No single named
  statewide network by this or a similar name was found.** What exists instead is a patchwork of
  independently-operated buoy programs: NTL-LTER research buoys (2a), the UW SSEC Lake Mendota
  buoy (2c), the GLOS/UWM School of Freshwater Sciences buoy fleet (2e), and a separately-found
  "WISC-Watch" project in the Apostle Islands (Lake Superior, Bayfield/Ashland County — wave
  height, water temperature, wind; **found via search only, URL not independently fetched/verified
  in this pass** — flag as unverified). Report this explicitly as "checked, no single network
  found" rather than silently omitting the question.

---

## Part 3 — Other lake/waterbody characteristics not yet catalogued

- **WDNR Open Data Portal (ArcGIS Hub)** — see 1c above. Real, verified-accessible statewide GIS
  infrastructure for lake classification/quality layers (Outstanding/Exceptional Lakes,
  High-Quality Lakes & Large Rivers, 305(b) Assessed Lakes, Classified Trout Spring Ponds, Public
  Boat Access Sites). Not previously catalogued in `v0_lake_characteristics.md`, which used the
  per-lake "Find a Lake" facts pages instead of this bulk portal. Worth noting for V1 as a
  potentially more efficient bulk-query alternative to one-lake-at-a-time facts-page lookups, for
  characteristics like lake-quality classification and public access points — though this pass did
  not attempt an actual bulk data pull/schema check, only confirmed the portal and several
  individual datasets exist and are reachable.
- No other genuinely new, load-bearing lake/waterbody-characteristic source (distinct from
  species-presence and water-temperature, i.e. things like bathymetry, watershed, trophic status)
  was identified in this pass beyond what the ArcGIS portal implies exists; a deeper dive into that
  portal's full dataset catalog was not performed and would be a reasonable next step if the V1
  build wants bulk statewide lake-characteristic data rather than one-lake-at-a-time facts pages.

---

## Summary table — newly usable vs. checked-and-rejected

| Source | Category | Status | Real/verified this pass? | Recency | Geographic scope |
|---|---|---|---|---|---|
| WDNR Fisheries Survey Reports (Comprehensive Summary Report format) | Species presence | **NEWLY USABLE — high value** | Yes, PDF fully extracted | Periodic (multi-year survey cycle) | Statewide (all 72 counties, non-exhaustive per-lake) |
| WDNR "Find a Lake" fish-species-present list | Species presence | Usable, low signal | Yes (page format already used in V0) | Static/undated | Statewide |
| WDNR Open Data Portal (ArcGIS Hub) | Species presence / lake characteristics | Infrastructure usable; fish-specific layer unconfirmed | Partially (search API + several dataset pages verified) | Varies by layer | Statewide, bulk/GIS |
| WDNR Natural Heritage Inventory (NHI) | Species presence | **REJECTED** — rare species only, not gamefish | Yes (portal accessible) | N/A | Statewide |
| North Temperate Lakes LTER / EDI | Water temperature | Usable, narrow scope | Yes (EDI page 200; auth-for-API-in-2026 caveat unverified) | Continuous historical, live status unconfirmed | 4-5 specific research lakes (Vilas/Oneida + Mendota) |
| USGS NWIS — Lake Monona (05429000) | Water temperature | **NEWLY USABLE — live, high value** | Yes, live IV data confirmed through today | **Real-time** | Lake Monona (Dane Co.) only |
| USGS NWIS — 7 other WI lake sites found | Water temperature | Historical-only (2 confirmed, 3 unverified date ranges) | Yes (site-service query) | Historical only (1970s-1990s), except 3 sites not individually re-checked | Scattered single lakes statewide |
| UW SSEC Lake Mendota Buoy | Water temperature | Usable, single lake | Yes (page 200) | Near-real-time, seasonal | Lake Mendota only |
| Clean Lakes Alliance / LakeForecast.org | Water temperature | Usable (dashboard only, no API confirmed) | Yes (page 200, live reading seen) | Real-time in-season only (Mem. Day-Labor Day) | 5 Yahara lakes + Madison beaches |
| GLOS Seagull API | Water temperature (+ extra water-quality params) | **NEWLY USABLE — high value, real REST API** | Yes, live API calls succeeded | Real-time (~10 min refresh), seasonal | Lake Michigan WI nearshore (Milwaukee, Racine confirmed) |
| Water Action Volunteers (WAV) | Water temperature | Usable in principle, wrong geometry (streams) | Yes (pages 200/302→200) | Continuous in-season, hourly | Statewide streams, NOT lakes |
| "Wisconsin Buoy Network" (named) | Water temperature | **NOT FOUND — does not exist as a single entity** | N/A | N/A | N/A |
| Apostle Islands WISC-Watch | Water temperature | Found via search only, **not independently verified** | No | Unknown | Lake Superior / Bayfield-Ashland Co. only |

---

## Honesty notes / limitations of this pass

- The task asked to check "a reasonable sample" of county lake districts/associations; only one
  (Clean Lakes Alliance / Yahara CLEAN) was actually fetched and verified in depth. This should not
  be read as "no other WI lake district publishes real data" — it is an unexplored space beyond
  this one confirmed example, flagged honestly rather than padded with unverified guesses.
- The EDI API authentication change reportedly taking effect "July 30, 2026" (i.e., already in
  effect as of this September 2026 retrieval) was reported by a web-search summary, not by an
  actual authenticated-vs-unauthenticated API call test in this pass — flag as needing direct
  confirmation before relying on NTL-LTER data programmatically.
- Only 2 of the 8 USGS WI lake-temperature sites found had their date ranges individually
  re-verified via `seriesCatalogOutput=true` in this pass (Delavan Inlet, Little Rock Lake) beyond
  the headline Monona check; Lake Clara, Round Lake, and East Eightmile Lake should be
  individually re-checked before being relied on as either current or historical-only.
- The WDNR Open Data Portal was confirmed to exist and respond to API queries, but no dedicated
  fish-species-presence feature layer was found on it in this pass — this is a "not found in this
  search," not a confirmed "does not exist."
- No data was extracted, pulled, or transcribed in this pass, per the task's explicit scope —
  every number above (date ranges, record counts, platform IDs) came from a live API/page response
  captured during verification, not from memory or estimation.
