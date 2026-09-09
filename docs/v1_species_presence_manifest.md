# V1 Species-Presence Manifest (Part 3a)

Two real data sources were pulled for V1, per the sources catalogued in
[`docs/v1_source_discovery_report.md`](v1_source_discovery_report.md). They
are **not interchangeable** — see the presence-classification rule below.

## 1. Statewide WDNR stocking pull

- **File:** [`data/v1/wi_stocking_statewide_2011_2025.csv`](../data/v1/wi_stocking_statewide_2011_2025.csv)
- **Source:** live query against `https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/LoadResults`
  (the same real endpoint used for the single-lake Pewaukee pull in V0),
  retrieved 2026-09-09.
- **Scope:** `STOCKING_YEAR` restricted to **2011-2025** (a 15-year recent
  window, not full program history back to the 1950s/1970s) — chosen so the
  pull stays a manageable, genuinely "recent presence" signal rather than
  an unbounded historical dump.
- **Coverage:** **24,683 real records**, **74 of 74 Wisconsin counties**,
  **2,338 distinct county+waterbody combinations**. Top species by record
  count: Walleye (4,674), Rainbow Trout (4,326), Brook Trout (3,997), Brown
  Trout (3,590), Muskellunge (1,977), Northern Pike (1,066), Yellow Perch
  (872), Largemouth Bass (854), Bluegill (666), Black Crappie (597).
- **This supersedes** the V0-era single-lake `data/v0/pewaukee_lake_stocking_1987_2025.csv`
  for V1 purposes (that file remains in place, untouched, as part of the
  V0 record).

## 2. WDNR fisheries survey report sample (real observed species composition)

- **File:** [`data/v1/wi_fisheries_survey_species_sample.csv`](../data/v1/wi_fisheries_survey_species_sample.csv)
  (308 rows) — merged from four extraction batches; source PDFs kept under
  [`data/v1/pdfs/`](../data/v1/pdfs/) (20 PDFs, real, natively-text PDFs,
  not scanned/OCR).
- **Source:** WDNR "Comprehensive Summary Report" fisheries-survey PDFs
  (electrofishing/netting), `https://dnr.wisconsin.gov/topic/Fishing/reports`,
  the highest-value new source identified in Part 2. Each row is one
  species observed in one lake's survey, with the report's own CPUE metric
  (fish/net-night, fish/mile electrofished, or a population estimate) and
  the reported value, plus free-text notes carrying extra detail (sample
  size, size structure, historical comparison) the report itself stated.
- **Coverage: 22 real lakes across 20 counties**, deliberately spread across
  the state, not concentrated in one region:

  | County | Lake(s) |
  |---|---|
  | Adams | Camelot Lake |
  | Ashland | Spider Lake |
  | Barron | Big Moon Lake |
  | Bayfield | Diamond Lake |
  | Burnett | Upper/Lower Clam Lake |
  | Columbia and Sauk | Lake Wisconsin |
  | Dane | Fish Lake |
  | Dodge | Beaver Dam Lake |
  | Green Lake | Big Green Lake, Little Green Lake |
  | Iowa | Blackhawk Lake |
  | Jefferson | Rock Lake |
  | Marathon/Portage | Lake DuBay |
  | Oconto | Bass Lake |
  | Oneida | Pelican Lake |
  | Sauk | Devils Lake |
  | Shawano | Shawano Lake |
  | Vilas | Dead Pike Lake |
  | Walworth | Lauderdale Lakes (Green/Middle/Mill Lake chain) |
  | Washburn | Stone Lake |
  | Waupaca | White Lake |
  | Waushara | Fish Lake |

- **This is a real, disclosed SAMPLE, not exhaustive statewide coverage.**
  WDNR's reports index covers all 72 counties but is itself non-exhaustive
  per-lake (not every lake is surveyed, and surveys repeat only every few
  years); this pass pulled 22 lakes as a genuinely diverse cross-section
  (northern, central, and southern WI; natural lakes and one river
  impoundment) — not a claim that these are the only or the "best" 22 lakes,
  just a real, verified, geographically-spread sample.

## 3. Presence-classification rule (Decision #005/#012 discipline)

Per the explicit instruction for this cycle: **stocking records are
positive-only evidence.** A species appearing in the stocking pull for a
lake confirms that species was introduced there; a species's *absence* from
the stocking list does **not** mean it isn't present — self-sustaining
populations are frequently stocked less or not at all specifically because
they don't need supplementing. Only real survey data (source 2) gives an
authoritative, DNR-observed species list for a lake.

| Lake status | Meaning | Applies to |
|---|---|---|
| **Survey-confirmed** | Real electrofishing/netting data exists — species list from the survey is treated as authoritative-enough for that lake | The 22 lakes in the sample above |
| **Stocking-only** | Only stocking records exist — species list is labeled "confirmed present via stocking, unconfirmed complete list," never treated as the full species set | Any of the other ~2,316 waterbodies in the stocking pull with no survey pulled this pass |
| **Neither** | No data pulled this pass | Every other WI waterbody not in either file |

## What wasn't covered (explicit gap disclosure, per Part 3d)

- The survey-report sample is 22 lakes; WDNR's reports index almost
  certainly contains several hundred comprehensive-survey PDFs statewide
  that were not pulled in this pass — this is a real, bounded sample, not
  an attempt at full coverage.
- The stocking pull is bounded to 2011-2025; older stocking history (the
  Pewaukee V0 file goes back to 1987) exists in the same database but was
  not re-pulled for the full state to keep this pull tractable.
- No lake outside the stocking pull's 2,338 waterbodies or the survey
  sample's 22 lakes has any species-presence data in this project as of
  this pass — the V1 script (Part 4) must handle "no data for this lake"
  as an explicit, honest outcome, not a silent gap.
