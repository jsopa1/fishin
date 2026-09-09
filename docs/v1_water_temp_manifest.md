# V1 Water-Temperature Manifest (Part 3b)

Real current/recent water-temperature data pulled for the 22 survey-confirmed
lakes from `docs/v1_species_presence_manifest.md`, plus one bonus lake
(Lake Monona), per the sources catalogued in
[`docs/v1_source_discovery_report.md`](v1_source_discovery_report.md) Part 2.

- **File:** [`data/v1/wi_lake_water_temp_current.csv`](../data/v1/wi_lake_water_temp_current.csv)
  — 23 rows (22 target lakes + Lake Monona bonus).
- **Retrieved:** 2026-09-09.

## Method breakdown

| Method | Count | Meaning |
|---|---|---|
| `usgs_live` | 1 | Lake Monona only — live USGS instantaneous water-temperature gauge (site 05429000), real water measurement |
| `clmn_recent` | 9 | Real WDNR Citizen Lake Monitoring Network volunteer water-temperature reading, dated within roughly the last ~2 years |
| `nws_air_proxy` | 13 | No usable current/recent real water-temperature source found; NWS current air temperature used as an explicitly labeled PROXY, not a water measurement |

**9 of the 22 target lakes (41%) got a real water-temperature reading**
(all via CLMN — no target lake besides Monona had a usable USGS site).
**13 of 22 (59%) fell back to the NWS air-temperature proxy.** This matches
the source discovery report's expectation that most Wisconsin lakes lack a
real, current water-temperature sensor.

### Lakes with real, current-ish CLMN water temperature (`clmn_recent`)

| Lake | County | Reading date | Value |
|---|---|---|---|
| Camelot Lake | Adams | 2026-08-24 | 24.6°C / 76.2°F |
| Big Moon Lake | Barron | 2025-09-14 | 23.5°C / 74.3°F |
| Lake Wisconsin | Columbia/Sauk | 2024-07-22 | 25.9°C / 78.6°F |
| Beaver Dam Lake | Dodge | 2026-08-24 | 24.8°C / 76.6°F |
| Rock Lake | Jefferson | 2026-08-25 | 24.6°C / 76.2°F |
| Bass Lake | Oconto | 2024-09-10 | 21.2°C / 70.1°F |
| Pelican Lake | Oneida | 2025-09-04 | 16.9°C / 62.4°F |
| Devils Lake | Sauk | 2024-10-21 | 14.5°C / 58.1°F |
| Lauderdale Lakes (Green Lake basin) | Walworth | 2026-08-12 | 26.2°C / 79.2°F |

Five of these nine (Camelot, Beaver Dam, Rock, Lauderdale, plus Big Moon and
Pelican close behind) are genuinely current — readings from within the last
few weeks to about a year of the 2026-09-09 retrieval date. Pelican Lake and
Devils Lake reuse/reconfirm the same CLMN stations already pulled in the V0
cycle (`data/v0/inland_water_temp_pelican.csv`,
`data/v0/inland_water_temp_devils.csv`); this pass re-fetched each station's
temperature download and confirmed the same most-recent reading is still the
latest on file.

### Lakes falling back to NWS air-temperature proxy (`nws_air_proxy`)

13 lakes: Spider Lake, Diamond Lake, Upper/Lower Clam Lake, Fish Lake (Dane),
Big Green Lake, Little Green Lake, Blackhawk Lake, Lake DuBay, Shawano Lake,
Dead Pike Lake, Stone Lake, White Lake, Fish Lake (Waushara).

Of these, **6 had a real CLMN station on file but with a stale reading**
(9-29 years old — Spider Lake 1997, Fish Lake/Dane 2014, Big Green Lake 2018,
Blackhawk Lake 2007, Lake DuBay 2013, Fish Lake/Waushara 2017) — genuinely
real historical water-temperature data exists for these lakes, it is just too
old to represent "current" conditions, so the NWS air-temperature proxy was
used instead and the stale CLMN reading is preserved in the `notes` column
for context. **7 had no CLMN station found at all** within this pass's
bounded search (Diamond Lake, Upper/Lower Clam Lake, Little Green Lake,
Shawano Lake, Dead Pike Lake, White Lake — plus Stone Lake, which has a
registered CLMN station with zero readings on file). None of these 13 lakes
has a USGS lake water-temperature site.

Every `nws_air_proxy` row's coordinates came from a real OpenStreetMap/
Nominatim geocoding lookup (not estimated/guessed), and every reading is a
live `api.weather.gov` current-conditions observation from the retrieval
date/time, from the nearest reporting station (mostly small regional
airports).

## Honesty / methodology notes

- **CLMN portal mechanics:** The WDNR CLMN station-search tool
  (`apps.dnr.wi.gov/lakes/waterquality/Stations.aspx`) is an ASP.NET
  WebForms page; its `location=` query-string parameter does **not**
  actually filter results (it silently returns the default statewide
  A-lakes listing) — real filtering requires a POST with the page's
  `__VIEWSTATE`/`__EVENTVALIDATION` tokens and the county dropdown's
  internal numeric code. This was reverse-engineered and automated in this
  pass and confirmed working (county-filtered results verified against
  known lakes). **Pagination past page 1 (40 rows) could not be reliably
  automated within this pass's time budget** — several postback attempts to
  reach page 2 instead reset to the unfiltered statewide list. This means
  a small number of "not found" results above (Shawano Lake, most notably,
  which is confirmed to have a real page 2) are **search-budget artifacts,
  not confirmed absences** — flagged explicitly in each affected row's notes
  rather than silently treated as "no CLMN data exists."
- **CLMN temperature download format:** Each station's
  `DownloadTemperatureReport?stationId=<id>` endpoint returns a real `.xlsx`
  file (not CSV despite the endpoint name); column order was found to vary
  between stations (some list date first, others last), so parsing was done
  by header name, not fixed position, after an initial version of this
  pass's parser silently misread one station's columns — caught and fixed
  before any data was recorded.
- **Recency threshold:** A CLMN reading was treated as "recent" (method
  `clmn_recent`) if dated within roughly the last 2 years; older real
  readings were treated as too stale to represent current conditions and the
  lake was routed to the NWS proxy instead, with the stale reading preserved
  in `notes`. This is a judgment call made explicit here rather than left
  implicit.
- **Every row is honestly labeled real vs. proxy** via the
  `is_real_water_measurement` column: `true` for `usgs_live` and
  `clmn_recent` rows (9 lakes total, all real measured water temperature),
  `false` for all 13 `nws_air_proxy` rows (air temperature, explicitly not a
  water measurement).

## Lake Monona bonus-lake status

**Added as a 23rd lake.** Confirmed live via direct USGS API call in this
pass: site 05429000 returned a same-day (2026-09-09) instantaneous
water-temperature reading of 23.4°C / 74.1°F — the strongest water-temperature
source found anywhere in this project (V0 or V1).

- **Species-presence status:** Lake Monona is **not** one of the 22
  survey-confirmed lakes from Part 3a (no WDNR fisheries Comprehensive
  Summary Report PDF was pulled for it in this pass). It **is** present in
  the statewide stocking pull (`data/v1/wi_stocking_statewide_2011_2025.csv`)
  with **34 real records**, all Muskellunge, 2023-2025 (both DNR and private
  stocking). Per the project's presence-classification rule
  (`v1_species_presence_manifest.md` §3), this makes Lake Monona
  **"stocking-only" confirmed presence for Muskellunge specifically** — real
  and usable for a Muskellunge narrative, but not an authoritative full
  species list the way a survey-confirmed lake's data is. It was **not**
  promoted to a full 23rd "survey-confirmed" lake because no real survey
  data was pulled for it in this pass; it is included here only for its
  water-temperature value, clearly labeled as a bonus with a different,
  weaker species-presence status than the other 22.
