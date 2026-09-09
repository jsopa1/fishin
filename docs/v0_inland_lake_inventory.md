# V0 Statewide Inland-Lake Creel-Data Inventory (Step 1: Inventory + Extraction)

Prepared per DECISIONS.md #008 ("Expand V0 inland-lake search beyond
Pewaukee/Delavan/Geneva"). Scope of this document: **inventory and extraction
only** — locate Wisconsin inland lakes with real, extractable angler
creel/harvest-rate data (statewide, not limited to SE Wisconsin), and attempt
to actually pull the numbers, the same way V0 pulled Lake Michigan sport
harvest data. Lake characterization, cross-lake transposition testing, and
extrapolation (steps 2-4 of the Decision #008 research cycle) are explicitly
**out of scope** for this document and are left to later steps.

Retrieval date for everything below: **2026-09-08**.

---

## 1. Method

1. Searched `https://dnr.wisconsin.gov/topic/Fishing/reports` (WDNR's
   fisheries survey report index) plus general web search for WDNR PDF
   filenames matching "Creel" statewide.
2. Downloaded every candidate PDF that appeared to be an actual angler creel
   survey (catch/harvest per unit effort), not a netting/electrofishing/trawl
   abundance survey. Netting/electrofishing/"Comp[rehensive] Survey" reports
   (dozens of which turned up in the same index) were excluded up front for
   the same reason Winnebago's trawl data was excluded in the original V0
   report: they measure population abundance, not angler catch rate, and
   substituting them would misrepresent what the data measures.
3. Attempted extraction with `pdftotext` first. This **failed silently** for
   every report that uses a multi-column results table: text came out with
   species labels and numeric columns shifted by one row relative to each
   other (verified by cross-checking against the report's own narrative
   prose, which is written in normal single-column text and does not have
   this problem). This is a real, general finding for this document, not a
   one-off: **blind `pdftotext` extraction of these WDNR creel tables is not
   safe to trust** and would have silently produced wrong numbers if used
   as-is.
4. Fixed this by rendering the actual table page to a PNG image (via
   PyMuPDF) and transcribing the table visually, cell by cell, from the
   rendered image — the same category of fix used nowhere in V0 (V0's Lake
   Michigan PDFs extracted cleanly with plain text). All numbers in the CSVs
   below were checked this way, not taken from raw `pdftotext` output.
5. Geneva-style "found but blocked" case: where a report is served only
   through a JavaScript PDF-viewer wrapper page with no static extractable
   PDF underneath, it is logged as blocked with the specific reason, exactly
   as Geneva's 2015 survey was in the original V0 report.

---

## 2. Ranked list: lakes with genuinely extracted, usable creel data

**Honest bottom line up front: 11 additional Wisconsin inland lakes were
found with real creel-survey data and successfully extracted**, on top of
Lake Michigan (the only waterbody V0's original SE-Wisconsin pass could use).
Four of the eleven (Pine, Sand, Pelican, Minocqua) have **two separate creel
survey seasons each**, 8-17 years apart, which is the closest structural
analogue available for inland lakes to Lake Michigan's multi-year time
series — WDNR does not creel-survey any inland lake annually/continuously;
each lake gets a survey every ~10-20 years, not every year. This matters for
what "multi-year coverage" can mean here: it means "this lake has multiple
point-in-time surveys to compare," not "this lake has a continuous annual
series." No inland lake in this inventory has continuous annual creel
coverage comparable to Lake Michigan's 1969-2024 series.

Ranked by recency of most-recent survey year, then by number of survey
seasons available:

| Rank | Lake | County | Survey season(s) | Species | Format/extractability | Frequency | CSV |
|---|---|---|---|---|---|---|---|
| 1 | **Minocqua Lake** | Oneida | 2024-25 *and* 2009-10 | 10 (Walleye, N. Pike, Muskellunge, Smallmouth/Largemouth Bass, Yellow Perch, Bluegill, Black Crappie, Pumpkinseed, Rock Bass, +Cisco 2024-25) | Extractable (image-transcribed; native `pdftotext` output was column-misaligned) | Periodic, ~15-yr gap | `minocqualake_creel_2009_10_2024_25.csv` (21 rows) |
| 2 | **Pelican Lake** | Oneida | 2024-25 *and* 2011-12 | 11 (as above + White Bass, Burbot) | Extractable (image-transcribed) | Periodic, ~13-yr gap | `pelicanlake_creel_2011_12_2024_25.csv` (23 rows) |
| 3 | **Devils Lake** | Sauk | Jul 2023-Jun 2024 | 13 (Brown Trout, Rainbow Trout, Bluegill, bass, panfish, Walleye, Burbot) | Extractable directly from `pdftotext -layout` (single-column table, no misalignment) | Single season (most recent known survey) | `devilslake_creel_2023_24.csv` (13 rows) |
| 4 | **Big Green Lake** | Green Lake | 2022-23 | 12 (Walleye, N. Pike, Muskellunge, bass, panfish, Lake Trout, White Bass) | Extractable (image-transcribed) | Single season in this pass | `biggreenlake_creel_2022_23.csv` (12 rows) |
| 5 | **Lake Wisconsin** | Columbia/Sauk | Jul 2022-Jun 2023 | 13 (Walleye, Sauger, crappies, bass, Bluegill, Yellow Perch, catfish, Muskellunge, Freshwater Drum) | Extractable (image-transcribed); reports open-water and ice-fishing rates separately | Single season in this pass | `lakewisconsin_creel_2022_23.csv` (14 rows) |
| 6 | **Petenwell Lake** | Adams/Juneau/Wood | Mar-Jun 2023 | 15 (Walleye, Muskellunge, N. Pike, bass, panfish, White Bass, Freshwater Drum, catfish, buffalo, Quilback, Common Carp) | Extractable, **but units differ from every other lake here**: this report's "Specific Catch/Harvest Rate" column is **fish per hour**, not hours per fish (verified by back-computing effort/catch ratios against the printed values — the other 10 lakes are consistently hours-per-fish). Flag this before combining with other lakes. | Single season in this pass | `petenwelllake_creel_2023.csv` (16 rows) |
| 7 | **Pine Lake** | Iron | 2023-24 *and* 2017-18 | 8-9 (Walleye, Muskellunge, bass, Yellow Perch, Bluegill, Black Crappie, Pumpkinseed, Rock Bass, +N. Pike 2017-18) | Extractable (image-transcribed) | Periodic, ~6-yr gap | `pinelake_creel_2017_18_2023_24.csv` (17 rows) |
| 8 | **Sand Lake** | Sawyer | 2023-24 *and* 2007-08 | 10 (Walleye, N. Pike, Muskellunge, bass, Yellow Perch, Bluegill, Black Crappie, Pumpkinseed, Rock Bass) | Extractable (image-transcribed) | Periodic, ~16-yr gap | `sandlake_creel_2007_08_2023_24.csv` (20 rows) |
| 9 | **Sawyer Lake** | Langlade | Summer 2023 | 9 (Walleye, N. Pike, bass, Yellow Perch, Bluegill, Black Crappie, Pumpkinseed, Rock Bass) | Extractable (image-transcribed) | Single season in this pass | `sawyerlake_langlade_creel_2023.csv` (9 rows) |
| 10 | **Lake Wissota** | Chippewa | 2019-20 *and* 2006-07 | 10-11 (Walleye, N. Pike, Muskellunge, bass, Bluegill, crappie, Yellow Perch, catfish, +Lake Sturgeon 2006-07) | Extractable (image-transcribed; `pdftotext` output for this one was badly scrambled) | Periodic, ~13-yr gap | `lakewissota_creel_2006_07_2019_20.csv` (21 rows) |
| 11 | **White Potato Lake** | Oconto | 2019-20 | 10 (Walleye, N. Pike, Muskellunge, Largemouth Bass, Yellow Perch, Bluegill, Black Crappie, Pumpkinseed, Rock Bass, Yellow Bullhead) | Extractable, but the table was on a different page than its own table-of-contents said (had to search the PDF text to find it) | Single season in this pass | `whitepotatolake_creel_2019_20.csv` (10 rows) |

All CSVs are at `data/v0/<file>` with columns: `source_url, source_file,
retrieval_date, waterbody, county, creel_year, species,
directed_effort_hours, pct_of_directed_effort, total_catch,
catch_rate_hrs_per_fish, total_harvest, harvest_rate_hrs_per_fish,
harvest_rate_fish_per_hour (derived), mean_harvest_length_in`. Blank cells
mean the source report itself printed no value there (typically because no
angler specifically targeting that species caught/harvested one during the
survey — the reports use `*`/`NA` for this, converted to blank here). Source
PDFs are archived at `data/v0/pdfs/`.

**Read this table's numbers as point-in-time survey estimates, not measurement
error-free constants** — same caveat V0 applied to Lake Michigan.

---

## 3. Found but blocked

| Lake | County | What was found | Why it's blocked |
|---|---|---|---|
| **Lake Winnebago — Yellow Perch Creel Survey, 2012** | Winnebago | A WDNR "Winnebago 2012 Yellow Perch Creel Survey Report" is listed and linked from the WDNR reports index — genuinely a **creel** report (not the trawl/abundance survey V0's original report already correctly excluded). This is a materially new finding: it means Winnebago's Decision #005/#008-relevant status is more nuanced than "no creel data at all." | Hosted only through a Widen JavaScript PDF-viewer wrapper (`p.widencdn.net/.../Reports_Winnebago2012YellowPerchCreelSurveyReport`), which itself only embeds an `embed.widencdn.net/pdf/plus/...` viewer page — fetching that "PDF" URL returns pdf.js viewer HTML, not the underlying PDF bytes, and the real asset URL is not present as a static link (it is fetched by client-side JS at runtime). This is the exact same failure mode as Geneva Lake's 2015 survey in the original V0 report — a genuine tooling limitation with the tools available in this pass, not evidence the data doesn't exist. Archived wrapper page: `data/v0/pdfs/Winnebago2012YellowPerch_UNREADABLE_viewer_wrapper.html`. |

No other genuine creel report encountered in this search was blocked in this
way — every other Creel-labeled WDNR PDF found was a normal static PDF and
extracted successfully (after correcting for the `pdftotext` column-alignment
problem described in Section 1).

**Recommendation for a later step:** the Winnebago 2012 yellow perch creel
report should be retried with a tool that can execute the Widen viewer's
JavaScript (e.g., a browser-automation fetch) before concluding Winnebago has
no usable creel data at all — this document could not do that, so it is
logged as blocked, not as confirmed unavailable.

---

## 4. Ruled out / explicitly not counted as creel data

- **Dozens of WDNR "Comprehensive Survey," netting, and electrofishing
  reports** turned up in the same statewide index search (Barron, Dodge,
  Marathon, Oneida, Bayfield, Douglas counties and many more). These were
  **not** treated as creel data and are not included above, for the same
  reason Winnebago's trawl-abundance data was excluded from V0's Lake
  Michigan-only evaluation: they measure fish population abundance via a
  standardized sampling method, not angler catch/harvest rate. Padding the
  ranked list above with these would repeat exactly the mistake V0 flagged
  and avoided with Winnebago.
- **Barron/Polk put-and-take trout lakes (2023)** — real WDNR data
  (`data/v0/pdfs/BarronPolkTroutLakes_2023Creel.pdf`, kept as source) but it
  reports **percentage of stocked trout recaptured** per small put-and-take
  pond, not an angler-hours catch/harvest rate. It is a genuine, different
  metric (stocking-return efficiency), not a creel harvest rate comparable to
  the other lakes in this inventory, so it was not built into a ranked-list
  CSV in this pass.
- **Wisconsin River tailwater below Prairie du Sac Dam (2020-21)**
  (`data/v0/pdfs/WisconsinRiverTailwater_2021Creel.pdf`, kept as source) —
  confirmed extractable (verified page 38's catch/harvest table renders
  cleanly), with real effort/catch/harvest and even angler-tag exploitation-
  rate data for Walleye, Sauger, Smallmouth Bass, and Muskellunge. Not
  included in the ranked list because it is a **river tailwater reach**, not
  a lake, which is outside this document's "inland lake" scope per Decision
  #008's wording. Flagged here in case a later step wants to fold river
  creel data into the broader project.
- **The three original lakes (Pewaukee, Delavan, Geneva)** — status
  unchanged from the original V0 report; not re-checked in this pass since
  Decision #008 explicitly frames this as widening the search to *other*
  lakes, not re-litigating those three.

---

## 5. What this means going into steps 2-4 (not performed here)

- 11 lakes now have real, extracted creel data — a large improvement over
  V0's zero inland lakes, and enough to plausibly support the cross-lake
  transposition testing that Decision #008 calls for next.
- Four of the eleven (Minocqua, Pelican, Pine, Sand) have two survey seasons
  each, which is the only inland-lake data in this inventory that could
  support even a crude within-lake before/after comparison — still nothing
  close to Lake Michigan's continuous annual series, and each pair is only
  2 points.
- The Petenwell Lake unit inconsistency (fish/hour vs. hours/fish used
  everywhere else) must be normalized before any cross-lake comparison — it
  is flagged in both the CSV file and this document specifically so it isn't
  missed downstream.
- None of these 11 lakes have been checked yet for predictor-side data
  (weather, water temperature, ice-out, stocking) or for whether they are
  ecologically similar enough to Pewaukee/Delavan/Geneva to make a
  transposition test meaningful — that is explicitly out of scope here and
  is left for the later steps named in Decision #008.
