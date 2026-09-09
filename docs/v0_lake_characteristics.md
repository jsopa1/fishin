# V0 Lake Characterization (Step 2: Characterize Each Lake With Usable Data)

Prepared per DECISIONS.md #008, step 2 of the research cycle that step 1
(`docs/v0_inland_lake_inventory.md`) fed into. Scope: pull real, sourced
physical/limnological characteristics for every lake with usable creel
outcome data from step 1 (11 inland lakes + Lake Michigan), plus Pewaukee
and Delavan Lake for reference/context only (they do **not** have usable
outcome data and are marked as such throughout). Geneva Lake was skipped as
lower priority per the task instructions.

Retrieval date: **2026-09-08**. Full table:
`data/v0/lake_characteristics.csv` (14 rows, one per lake).

**This document is purely descriptive.** It does not test, model, or claim
that any lake's physical similarity to another implies its creel data would
transfer between them -- that is explicitly a later step in Decision #008's
research cycle.

---

## 1. Method and sources

For each of the 11 inland lakes with usable creel data, two independent
WDNR-sourced numbers were pulled and both kept in the CSV:

1. **The creel survey PDF's own "Physical Characteristics" section**
   (`data/v0/pdfs/*.pdf`) -- every one of these reports states surface area,
   max depth, and lake type (drainage/seepage/flowage) in its introduction,
   confirmed by direct `pdftotext -layout` extraction and grep on the
   "PHYSICAL CHARACTERISTICS" heading in each PDF.
2. **WDNR's "Find a Lake" / Surface Water Data Viewer facts page**
   (`apps.dnr.wi.gov/lakes/lakepages/LakeDetail.aspx?wbic=<WBIC>&page=facts`),
   looked up by matching each lake's correct Wisconsin Waterbody
   Identification Code (WBIC) -- verified against county and acreage before
   use, since several lake names in this set (Pine Lake, Sand Lake) are
   reused across multiple WI counties. This page is also the only source
   that reliably reports **mean depth** and **trophic status**, which the
   creel PDFs' intro sections do not state.

Lake Michigan's whole-lake bathymetry came from NOAA/EPA-sourced figures
(Britannica, NOAA Great Lakes bathymetry page) since it has no WDNR
Find-a-Lake page (that tool covers inland lakes only). Pewaukee and Delavan
used the same WDNR Find-a-Lake facts-page method as the 11 inland lakes.

**Primary species** for the 11 inland lakes + Lake Michigan were derived
directly from each lake's own creel-survey data already extracted in step 1
(`data/v0/*_creel_*.csv`), taking the top species by `pct_of_directed_effort`
(inland lakes, most recent survey season where two exist) or by total
harvest (Lake Michigan, most recent year, `lake_michigan_creel_harvest_rate_annual_by_species.csv`)
-- this is real angler-behavior data, not a guess. Pewaukee and Delavan have
no creel data to do this with, so their species lists are WDNR's general
"fish present" list instead, and are explicitly flagged in the CSV as not
being creel-derived.

**Nothing was estimated or backfilled.** Every blank/"not found" cell in the
CSV means neither the creel PDF nor the WDNR facts page reported that value
in this pass -- it is left blank rather than guessed.

---

## 2. What was found

All 14 lakes got at least: county, surface area, max depth, lake type, and
(for the 11 inland + Lake Michigan) a real creel-derived primary-species
list. That's a complete physical baseline for every lake in scope.

**Fully characterized (all 7 columns populated, including mean depth and
trophic status):** Minocqua, Devils Lake, Big Green Lake, Pine Lake, Sand
Lake, White Potato Lake, Lake Michigan, Pewaukee, Delavan Lake -- 9 of 14.

**Partially characterized (missing mean depth and/or trophic status on the
WDNR facts page):**
- **Pelican Lake** -- mean depth not found (trophic status: eutrophic, found).
- **Lake Wisconsin** -- mean depth not found (trophic status: eutrophic, found).
- **Petenwell Lake** -- mean depth and trophic status both not found.
- **Sawyer Lake** -- trophic status not found (mean depth: 10 ft, found).
- **Lake Wissota** -- mean depth and trophic status both not found.

So: **9 of 14 lakes fully characterized, 5 partially characterized** (all 5
partial cases are missing only mean depth and/or trophic status -- surface
area, max depth, lake type, and primary species are populated for all 14).

**A data-quality finding worth flagging going into later steps:** for most
of the 11 inland lakes, the creel PDF's own stated surface area/max depth
and the WDNR Find-a-Lake facts page's stated surface area/max depth do not
match exactly, even though both are WDNR sources. Examples: Minocqua
(1,360 vs 1,339 acres), Pelican (3,585 vs 3,545 acres), Pine Lake (312 vs
300 acres), Sand Lake (928 vs 949 acres), and most notably Lake Wissota
(6,300 vs 6,148 acres; 72 vs 64.4 ft max depth -- a real, non-trivial
discrepancy, not rounding noise). This likely reflects different survey
years/methods behind each WDNR product rather than an error in either one,
but it means "acres" and "max depth ft" in the combined dataset carry some
irreducible measurement disagreement even within a single agency's own
publications. Both figures are kept side-by-side in the CSV's `notes`
column rather than silently picking one.

---

## 3. Descriptive groupings and comparisons (no predictive claims)

Looking across the `lake_type`, `surface_area_acres`, `max_depth_ft`, and
`trophic_status` columns:

- **Lake type split (11 inland lakes):** 6 drainage lakes (Minocqua,
  Pelican, Big Green, Pine, Sand -- plus Pewaukee and Delavan, which brings
  the drainage total to 7 of 13 non-Great-Lake waterbodies), 3 seepage lakes
  (Devils, Sawyer, White Potato), and 3 impoundments/flowages (Lake
  Wisconsin, Petenwell, Lake Wissota -- all three are Wisconsin/Chippewa
  River reservoirs behind dams), plus Lake Michigan as the sole Great Lake.
  Pewaukee and Delavan are both drainage lakes, same as the majority type
  among the 11.

- **Trophic status:** where found, mesotrophic dominates (Minocqua, Devils,
  Big Green, Pine, Sand, White Potato, Pewaukee, Delavan -- 8 lakes), with
  Pelican and Lake Wisconsin the only two confirmed **eutrophic** lakes in
  the set, and Lake Michigan the only confirmed **oligotrophic** waterbody.
  Petenwell, Sawyer, and Lake Wissota have no confirmed trophic status yet.

- **Very similar pairs on these dimensions:**
  - **Pewaukee Lake (2,437 ac, 45 ft max, 15 ft mean, drainage,
    mesotrophic) and Delavan Lake (1,906 ac, 52 ft max, 21 ft mean,
    drainage, mesotrophic)** are themselves close to each other on every
    physical dimension -- unsurprising since both are the original V0
    SE-Wisconsin lakes lacking outcome data, but worth noting they were
    already similar to begin with.
  - **Sand Lake (949 ac, 50 ft max, 21 ft mean, drainage, mesotrophic) and
    Pine Lake (300 ac, 41 ft max, 17 ft mean, drainage, mesotrophic)** are
    similar in depth profile and trophic status despite Sand Lake being
    roughly 3x the surface area -- both are also both Northwoods drainage
    lakes with 2-season creel data (per step 1).
  - **Devils Lake (374 ac, 47 ft max, 30 ft mean, seepage, mesotrophic) and
    Sawyer Lake (149 ac, 31 ft max, 10 ft mean, seepage)** share lake type
    but differ noticeably in depth profile -- Devils Lake's mean-to-max
    depth ratio (30/47 = 0.64) indicates a comparatively steep-sided basin,
    while Sawyer Lake's (10/31 = 0.32) is much shallower on average relative
    to its deepest point.
  - **Pewaukee Lake and Minocqua Lake** are close in surface area (2,437 vs
    1,339-1,360 ac) and trophic status (both mesotrophic), though Pewaukee
    lacks the creel data Minocqua has.

- **Notably different from the rest of the set:**
  - **White Potato Lake (1,023 ac, only 11 ft max depth, 5 ft mean)** is by
    far the shallowest lake in the set relative to its surface area --
    every other lake with a comparable footprint (Minocqua 1,339 ac/60 ft,
    Pelican 3,545 ac/39 ft) is several times deeper. A lake this shallow
    stratifies differently (likely polymictic rather than stratifying)
    from the deeper lakes in this set, which is a real physical difference
    worth carrying into any later transferability discussion, not just a
    number.
  - **Big Green Lake (7,920 ac, 236 ft max, 104 ft mean)** is the extreme
    outlier at the other end -- the deepest natural inland lake in
    Wisconsin, roughly 4-5x deeper than any other lake in this set. Its
    stratified, two-story (coldwater + warmwater) character is physically
    unlike every other lake here except arguably Lake Michigan.
  - **Petenwell Lake (23,173 ac) and Lake Wisconsin (7,197 ac) and Lake
    Wissota (6,148 ac)** are the three impoundments and are also the three
    largest inland lakes in the set by surface area, but all three are
    comparatively shallow (44, 24, and 64.4 ft max depth respectively) --
    consistent with them being dammed river reaches rather than
    kettle/glacial lake basins, unlike the seepage and most of the drainage
    lakes above.
  - **Lake Michigan** is categorically different from every inland lake
    here on every dimension: orders of magnitude larger in surface area,
    ~4x deeper than even Big Green Lake, oligotrophic rather than
    meso/eutrophic, and a fundamentally different hydrology (open Great
    Lake with currents and thermoclines vs. closed or river-fed inland
    basins). This physical gap is exactly what makes it the least likely
    candidate for cross-lake transposition and the most likely to need its
    own standalone treatment in later steps.

---

## 4. What's still missing, going into later steps

- Mean depth and/or trophic status for Pelican, Lake Wisconsin, Petenwell,
  Sawyer, and Lake Wissota were not found on the WDNR Find-a-Lake facts
  pages in this pass. A later step could try WDNR's underlying water-quality
  database (SWIMS) or county lake-association reports for these, but this
  pass did not fabricate values to fill the gaps.
- A Wisconsin-waters-only surface area for Lake Michigan was not found;
  only whole-lake figures are recorded, explicitly flagged as such.
- Littoral substrate and water clarity/color detail (present in every creel
  PDF's Physical Characteristics section, e.g. "soft, slightly acidic,
  clear water" for Minocqua vs. "tannic, stained waters" for Lake Wisconsin)
  was read during extraction but not built into a CSV column, since it
  wasn't part of the requested schema -- worth pulling in a later step if
  water color/clarity turns out to matter for transferability.
- No predictor-side data (weather, ice-out, stocking, water temperature) or
  any similarity scoring/testing was done here -- both remain explicitly
  out of scope for this document, per Decision #008's step structure.
