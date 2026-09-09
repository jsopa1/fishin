# V1 Physiology/Behavior Research Candidates (Decision #009 lineage, Part 3c)

**Status: this document supersedes `docs/v0_physiology_research_candidates.md` in
full.** It is not a patch or an addendum — every species/candidate in the V0
document is carried forward below (re-verified against a primary source where
one could be located this pass), and new species/candidates found in this
project's real Wisconsin data (`data/v1/wi_stocking_statewide_2011_2025.csv`,
`data/v1/wi_fisheries_survey_species_sample.csv`) are added. This is research
only — nothing here has been validated against outcome data, and per
`CLAUDE.md`'s V1 scope, this project (a per-lake conditions/biology narrative
tool) is not attempting catch-rate prediction at all; these are reference
thresholds for narrative generation, confirmed presence permitting.

## Method and scope

1. Re-read `docs/v0_physiology_research_candidates.md` and
   `docs/v0_physiology_eval_results.md` in full before starting, to identify
   every number already on record and every flagged gap.
2. Read the species column of `data/v1/wi_stocking_statewide_2011_2025.csv`
   (statewide WDNR stocking records, 2011-2025) and
   `data/v1/wi_fisheries_survey_species_sample.csv` (real observed species
   from 22 WI lake surveys) to build the priority species list. Top species by
   stocking-record count: Walleye, Rainbow Trout, Brook Trout, Brown Trout,
   Muskellunge, Northern Pike, Yellow Perch, Largemouth Bass, Bluegill, Black
   Crappie, Fathead Minnow, White Sucker, Chinook Salmon, Coho Salmon, Lake
   Sturgeon, Smallmouth Bass, Channel Catfish, Pumpkinseed. Additional species
   confirmed present in the real survey sample: Rock Bass, White Crappie,
   White Bass, Sauger, Cisco (Lake Herring), Burbot, Common Carp, bullheads
   (not covered — no established angling-physiology literature distinct from
   general catostomid/ictalurid patterns already covered via White
   Sucker/Channel Catfish).
3. Read `data/v1/raw/glfc_sp87_3_wismer_christie_1987_fulltext.txt` (Wismer &
   Christie 1987, GLFC Special Publication 87-3, 165 pages, already fetched
   and OCR'd/text-extracted in a prior pass — read directly by species-table
   line offset in this pass, using the document's own repeating
   `SPECIES: <scientific name> (<common name>)` headers as a table of
   contents) for every species covered. This is a primary, cross-validated,
   Great-Lakes/Wisconsin-heavy compilation of field and lab studies (Coutant
   1977a, Cherry et al. 1977, Talmage & Coutant 1980, Shuter et al. 1980,
   Hokanson 1977, Scott & Crossman 1973, and dozens more, each individually
   cited inline per data row) — the single best source available for this
   pass, and used as the primary/agency-tier anchor for every species it
   covers.
4. Attempted retrieval of Hasnain, Minns & Shuter 2010 (Ontario MNR CCRR-17)
   a third time (two prior V0-cycle attempts failed). **Failed again** — see
   Section "CCRR-17 retrieval attempt" below for the full account.
5. Web search for species/relationships not covered by GLFC Sp87-3 (Lake
   Sturgeon; diel/nocturnal behavior for species beyond walleye; a few
   dissolved-oxygen thresholds), applying the same sourcing bar as V0: peer
   reviewed journals, primary agency compilations/reports (GLFC, WDNR,
   Ontario MNR/DFO, USGS, USFWS) only for any number presented as usable.
   Charter-fishing, angling-blog, and tackle-industry sources are logged only
   when explicitly flagged as not meeting the bar (per task instruction —
   logged, not discarded, since the underlying mechanism can still be real).

## Confidence tiers (same labels as V0, applied consistently below)

- **well-established** — multiple independent primary field/lab studies agree,
  or a single very rigorous field study directly in a relevant water body.
- **agency-tier** — primary agency compilation (GLFC Sp87-3, WDNR, Ontario
  MNR/DFO) or a single solid peer-reviewed field/lab study; may show real
  study-to-study scatter, disclosed rather than collapsed.
- **single-source-speculative** — one source only, often extension/aquaculture
  context, or peer-reviewed but not species/system-specific; numeric value
  should be used cautiously.
- **excluded-as-folklore** — explicitly checked, no primary scientific support
  found; not carried forward as a usable candidate.

---

## Summary

- **Total species covered: 26** (up from V0's 12: Walleye, Yellow Perch,
  Largemouth Bass, Smallmouth Bass, Northern Pike, Muskellunge, Black
  Crappie, Bluegill, Chinook Salmon, Coho Salmon, Brown Trout, Lake Trout).
  **14 new species added this pass:** Sauger, White Crappie, Rock Bass,
  Pumpkinseed, White Bass, Rainbow Trout/Steelhead, Brook Trout, Cisco (Lake
  Herring), Lake Whitefish, White Sucker, Channel Catfish, Freshwater Drum,
  Burbot, Fathead Minnow, Lake Sturgeon. (That's 15 new names but White
  Crappie was implicitly adjacent to V0's Black Crappie coverage and is
  counted as new since V0 never gave it numbers — 26 total species sections
  below.)
- **New relationship-types logged this pass, beyond spawning/feeding
  temperature:** nocturnal/low-light feeding behavior for Black Crappie and
  Channel Catfish (joining Walleye as the third and fourth species with a
  documented diel-feeding mechanism); a peer-reviewed dissolved-oxygen
  threshold for Channel Catfish; Lake Sturgeon spring spawning-migration
  behavior (river/rapids, substrate-specific, temperature-gated); explicit
  disclosure of Muskellunge's real GLFC preferendum (24-27°C) diverging
  materially from V0's previously-used 22°C figure (see Muskellunge section).
- **GLFC Sp87-3 (Wismer & Christie 1987) yielded real, usable, often
  Wisconsin- or Lake-Michigan-specific numbers for 20 of the 26 species below**
  — every species except Lake Sturgeon, which the compilation does not cover
  at all (checked directly: no `SPECIES: Acipenser fulvescens` table exists
  anywheer in the 10,440-line extracted text, confirmed by both a targeted
  grep for `fulvescens`/`Acipenser` across the whole file, which only turns
  up the species in the front-matter master list, never in a per-species data
  table).
- **CCRR-17 (Hasnain, Minns & Shuter 2010): still not retrieved**, a third
  failed attempt across three research cycles. Full account below. This
  project's coverage gap for species this report might have filled (chiefly
  Lake Sturgeon) is instead partly closed here via GLFC-adjacent literature
  search (a real peer-reviewed Quebec field study for Lake Sturgeon spawning
  temperature, see that section) and partly left open and disclosed, not
  papered over.
- **Numbers corrected/upgraded from V0 this pass** (see each species section
  for the full before/after): Northern Pike spawning trigger upgraded from an
  extension-tier 40-48°F range to a real Wisconsin field value (Scott &
  Crossman 1973, in GLFC Sp87-3: 6.7-7.8°C = 44-46°F, tightly consistent with,
  and now a primary-sourced replacement for, V0's number); Smallmouth Bass
  spawning upgraded from a bioenergetic-modeling-adjacent 15-18°C estimate to
  a real Lake Huron field study (Shuter et al. 1980: optimum 18°C, range
  15-17°C — materially the same number, now on a stronger citation);
  Muskellunge thermal optimum **flagged as a real disagreement, not
  corrected to a single value** — V0 used 22°C from a 2024 telemetry paper,
  GLFC Sp87-3's own field/lab preferendum values cluster at 24-27.3°C, and
  growth-optimum values at 24-26.6°C, materially higher than V0's number; both
  are now disclosed side by side (see Muskellunge section) rather than
  silently overwritten; Black Crappie preferred temperature upgraded from an
  undergraduate-report-sourced 27-29°C to a real Wisconsin field value (L.
  Monona, Coutant 1977a via GLFC Sp87-3: 27.8-29.8°C — same range, now
  primary-sourced); Bluegill spawning trigger upgraded from
  extension/angling-media sources (~71.6°F/22°C) to a real GLFC-compiled
  spawning-optimum range of 22.2-23.9°C (72-75°F), broader range 17-26°C
  (63-79°F) — close to, but more precisely sourced than, V0's number.

---

## CCRR-17 retrieval attempt (third attempt, still unresolved)

Per the task's explicit invitation to try again "if you have easy search
budget," a fresh attempt was made this pass. Search located the same two
`files.ontario.ca` candidate URLs identified in the V0 predictor-eval pass
(`stdprod_093347.pdf`, `stdprod_093357.pdf`). Both were downloaded and run
through `pdftotext -layout` directly (not just summarized by a web-fetch
model, to rule out an extraction artifact) — **both are confirmed to be
different reports**: `stdprod_093347.pdf` is CCRR-21 ("Potential Effects of
Climate Change and Adaptive Strategies for Lake Simcoe and the Wetlands and
Streams Within the Watershed"), and `stdprod_093357.pdf` is CCRR-22
("Wildlife Vulnerability to Climate Change: An Assessment For the Lake Simcoe
Watershed"). Neither is CCRR-17. A general search for the report's own PDF
filename/title turned up only citing papers, never the report itself, for a
third consecutive cycle.

As a partial substitute, the DFO 2019 report identified in the V0
predictor-eval pass (Mackey, C.M., Hasler, C.T. & Enders, E.C. 2019, "Summary
of Temperature Metrics for Aquatic Invasive Fish Species in the Prairie
Region," DFO Can. Sci. Advis. Sec. Res. Doc.,
`https://waves-vagues.dfo-mpo.gc.ca/Library/40789214.pdf`) was downloaded and
text-extracted directly this pass (it was only reviewed, not parsed, in V0).
Direct `pdftotext` extraction confirms this report's "Sturgeon" coverage is
**Green Sturgeon (Acipenser medirostris)**, a Pacific-coast invasive-species
screening target, **not** Lake Sturgeon (Acipenser fulvescens) — not usable
for this project's Lake Sturgeon gap. The report's species list otherwise
overlaps heavily with species already covered by GLFC Sp87-3 in this
document (Northern Pike, Bluegill, Smallmouth Bass, Black Crappie, etc.), so
it adds no new coverage here.

**Bottom line: CCRR-17 remains unretrieved after three attempts across two
research cycles.** This is disclosed as a genuine, unresolved gap, not
worked around with a fabricated citation. The GLFC Sp87-3 compilation (fully
retrieved and read this pass) has turned out to be sufficient for 20 of 26
species covered here, which was not obvious at the start of this pass.

---

## Species candidates

### 1. Walleye — carried forward from V0, re-verified

- **Spawning trigger:** GLFC Sp87-3 spawning-table rows for *Stizostedion
  vitreum* (walleye) give: 2.2-15.6°C range (Hokanson 1977, Wisconsin), and
  narrower optimum bands from other studies: 7.8-8.9°C (Griffiths 1981),
  4.4-6.7°C, 5-10°C. **In Fahrenheit, the optimum-band cluster is
  approximately 40-52°F**, tightly matching V0's already-cited 40-52°F/peak
  44-48°F figure — now confirmed against the primary GLFC compilation rather
  than resting only on extension-tier sources as V0 flagged it. **Tier:
  agency-tier** (real field data, genuine range across studies/locations, not
  a single fixed number).
- **Feeding/activity temperature:** Preferendum values in GLFC Sp87-3: 20.6°C
  at Trout Lake, Wisconsin (Coutant 1977a) — this is the exact number V0's
  predictor-eval step already extracted and used; also 23.2°C (Norris Res.,
  TN), 16°C (Atikokan GS, Ontario), 10.6-11.2°C (epilimnion, West Blue Lake,
  Manitoba — a notably cooler outlier, disclosed not discarded). **Tier:
  agency-tier**, Wisconsin-specific value (20.6°C = 69.1°F) is the best single
  number for this project.
- **Diel/light-window feeding:** Carried forward unchanged from V0 — Ryder
  1977 walleye CPUE-vs-illuminance curve, peak catchability near 300 lux
  (dusk/dawn), driven by tapetum lucidum/scotopic vision. Still the most
  rigorously evidenced physiological mechanism in this whole document, still
  the least immediately actionable without a trip-level/sub-daily timestamp
  in outcome data — but per this project's V1 narrative-tool scope
  (`CLAUDE.md`), a per-lake "conditions right now" narrative *can* use
  current time-of-day, so this candidate may in fact become usable for V1 in
  a way it never could be for V0's catch-rate modeling. Logged accordingly.
  **Tier: well-established.**
- **Seasonal movement:** Habitat-compression telemetry study (PMC,
  `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11707865/`) carried forward
  from V0 — walleye compress into a narrower thermal+DO "optimum" band
  (18-23°C combined with DO >5 mg/L) as summer progresses, a real
  seasonal-movement/DO-interaction mechanism. **Tier: agency-tier** (single
  strong field telemetry study).
- **Sources:** GLFC Sp87-3 (Wismer & Christie 1987), lines 9709-9877 of the
  local text extract; Ryder 1977 (as in V0); PMC habitat-compression study (as
  in V0).

### 2. Yellow Perch — carried forward, re-verified

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table (*Perca
  flavescens*) gives **20.8°C at Lake Michigan** and **20.2°C at Silver
  Lake/Trout Lake, Wisconsin** (both Coutant 1977a) — these are the exact
  values V0's predictor-eval step used, now directly confirmed against the
  primary source text rather than taken on faith from that step's own
  account. Also: 12.2°C at Muskellunge Lake, Wisconsin (small fish, notably
  cooler), 21.0°C at L. Opeongo, Ontario. **Tier: agency-tier.**
- **Spawning trigger:** GLFC Sp87-3 spawning table: optimum 12°C range 7-15°C
  (EPA 1974); 7.8-12.2°C range 7-16°C (Dunford 1978); 8.4°C range 7-10°C
  (Griffiths 1978); 5-6°C (another study). **Converts to roughly 45-59°F**
  across the optimum-band cluster — this is new to the document (V0 did not
  give yellow perch a spawning-trigger number, only a growth-optimum
  temperature). **Tier: agency-tier.**
- **Growth optimum (V0's original number, re-verified):** 23-24°C region
  supported by GLFC growth table (23°C Jobling 1981, 24.2°C Casselman 1978,
  22.5°C Leidy & Jenkins 1977) — consistent with V0's aquaculture-literature
  figure, now cross-confirmed by a second, independent primary source.
  **Tier: well-established** (upgraded from V0's single-aquaculture-source
  status, now cross-confirmed).
- **Sources:** GLFC Sp87-3, lines 9327-9500 (preferred/spawning tables) and
  9462-9498 (growth table); V0's PMC/aquaculture sources retained.

### 3. Largemouth Bass — carried forward, re-verified

- **Feeding/activity (thermal preference):** GLFC Sp87-3 preferendum table
  (*Micropterus salmoides*): 26.6-27.7°C (Norris Res., TN), 27-30°C (L.
  Monona, Wisconsin), 29.3-30.9°C (L. Monona, Wisconsin, another row),
  26.5-29.1°C (Savannah GS, S.C.). **A real, tight, Wisconsin-anchored
  cluster around 27-30°C (81-86°F)** — slightly higher than V0's cited
  25-28°C, but the same ballpark; the discrepancy is disclosed rather than
  silently reconciled, since both numbers trace to real field studies (V0's
  from aquaculture-context growth studies, this pass's from direct field
  preferendum telemetry). **Tier: agency-tier**, and specifically upgraded
  from V0's "moderate rigor, aquaculture-context caveats" framing — this is
  now a genuine field preferendum, not a growth-lab number.
- **Growth optimum:** GLFC growth table: juvenile 25°C, subadult 26-28°C —
  matches V0's originally-cited 25-28°C range closely.
- **Spawning trigger:** GLFC spawning table: optimum 15.6-21°C range 13-26°C
  (Carlander 1977, field); 20°C (Minnesota, Carlander 1977). **Converts to
  roughly 60-70°F optimum, 55-79°F full range** — new to this document (V0
  did not give largemouth a spawning number).
- **V0's feeding-rate-vs-temperature conflict (18°C higher feeding than
  warmer temps, Env. Biol. Fishes) — retained unchanged**, still flagged as
  a genuine within-primary-literature disagreement, not resolved by this
  pass's GLFC data (GLFC's numbers are about preference/growth, not feeding
  rate specifically, so they do not directly adjudicate this conflict).
  **Tier: agency-tier for preference/spawning, single-source-speculative
  still applies specifically to the feeding-rate-inversion claim.**
- **Sources:** GLFC Sp87-3, lines 8970-9097; V0's Env. Biol. Fishes and PMC
  sources retained for the feeding-rate conflict.

### 4. Smallmouth Bass — carried forward, upgraded

- **Spawning trigger — upgraded from V0's number.** GLFC Sp87-3 spawning
  table (*Micropterus dolomieui*): **optimum 18°C, range 15-17°C, Baie du
  Dore, Lake Huron (Shuter et al. 1980)** — a real Great Lakes field study,
  materially the same as V0's previously-cited 15-18°C (59-64°F) figure, now
  resting on a directly-confirmed primary citation rather than a
  bioenergetic-modeling-adjacent secondary source. Egg/larval development
  optimum 21°C, range 13-26°C (also Shuter et al. 1980). **Tier: upgraded to
  well-established** (direct Great Lakes field study, not a modeling
  estimate).
- **Feeding/activity temperature:** V0's Lake Michigan harbor field study
  (22°C bioenergetic optimum, ~25°C behavioral preference, active avoidance
  of both warmer and colder water) retained unchanged — GLFC Sp87-3 does not
  have a separate preferred-temperature table for smallmouth bass in the
  extracted text (only the spawning/development table was located), so this
  candidate's feeding-temperature number still rests on V0's original,
  directly-relevant Lake Michigan source. **Tier: well-established**
  (field-validated in the exact system this project's earlier V0 cycle
  covered).
- **Sources:** GLFC Sp87-3, lines 8849-8889; V0's ScienceDirect/ResearchGate
  sources retained for feeding-temperature preference.

### 5. Northern Pike — carried forward, upgraded

- **Spawning trigger — upgraded from V0's number.** GLFC Sp87-3 spawning
  table (*Esox lucius*): **6.7-7.8°C, Wisconsin Lake (Scott & Crossman
  1973)** — a real, Wisconsin-specific, primary field citation. Converts to
  **44-46°F**, essentially the same trigger V0 cited (40-48°F) from
  extension-tier sources, now confirmed against a primary Wisconsin source.
  Other GLFC rows: MWAT 9.4-14.4°C (L. Simcoe, Ontario), 4.4-11.1°C, range
  2.2-16.6°C (power plant outfall, wider/less relevant). **Tier: upgraded to
  agency-tier** (was extension-tier in V0).
- **Feeding/activity temperature:** GLFC preferendum table: **19-20°C (Lab,
  Casselman 1978)** — this is the exact number V0 already cited as the
  "physiological optimum" (19-21°C), now directly confirmed in the primary
  source. Growth optimum: 19-21°C juvenile/subadult, 20.9°C (McCauley &
  Casselman 1980, 2-3 yr fish) — matches V0's growth-optimum figure closely.
  **Tier: agency-tier.**
- **V0's Minnesota telemetry finding** (large pike preferring 16-21°C in
  August even with warmer water available) and **upper lethal limit ~29.4°C**
  retained unchanged, both still well-supported.
- **Sources:** GLFC Sp87-3, lines 4165-4370; V0's ResearchGate/KMAE sources
  retained.

### 6. Muskellunge — carried forward, **real disagreement flagged, not
   resolved**

- **Thermal optimum — GENUINE DISAGREEMENT between sources, disclosed, not
  collapsed to one number.** V0 cited ~22°C (72°F) from Bieber et al. 2024
  telemetry/radio-tracking (a 2024 peer-reviewed paper, directly on
  muskellunge). GLFC Sp87-3's own preferendum table (*Esox masquinongy*)
  gives a materially higher cluster: **>25.5°C (Stony Lake, Ontario, Minor &
  Crossman 1978), 24°C (Jobling 1981), 25.1°C and 21.9°C (Lab, Talmage &
  Coutant 1980), 27.3°C and 25.6°C (Scott & Crossman 1973).** Growth-optimum
  table: **24-26.6°C.** This is a real, disclosed disagreement between two
  legitimate primary sources spanning ~45 years (1973-2024) — not resolved
  here. Possible explanations (not confirmed): different life stages, summer
  thermal-refuging behavior (see below) meaning muskellunge are *found* in
  cooler water even when their physiological preferendum is warmer, or
  regional/study-population differences. **Tier: agency-tier for both
  numbers, flagged explicitly as conflicting — any use of a single
  "muskellunge optimum temperature" value should disclose which source it
  is drawing from.**
- **Spawning trigger:** GLFC spawning table: optimum ~13°C, range 9.5-15.5°C
  and 9.4-15°C (two rows), also >10°C (Miles 1978, W. Virginia — likely a
  warmer regional population) and 10.5-15.5°C (Haas 1978). **Converts to
  roughly 49-60°F** — new to this document (V0 did not give muskellunge a
  spawning-trigger number).
- **Activity decline above 25°C, mortality-risk threshold ~26°C, thermal
  refuging behavior** — retained unchanged from V0 (Bieber et al. 2024;
  ScienceDirect mortality study). Note this is now in some tension with
  GLFC's higher preferendum numbers above (if physiological preference is
  24-27°C, "activity declines above 25°C" sits right inside, not above, that
  band) — flagged as an open question for whoever uses this candidate next,
  not adjudicated here.
- **Sources:** GLFC Sp87-3, lines 4265-4370; V0's Bieber et al. 2024 and
  ScienceDirect sources retained.

### 7. Black Crappie — carried forward, upgraded

- **Preferred temperature — upgraded from V0's number.** GLFC Sp87-3
  preferendum table (*Pomoxis nigromaculatus*): **27.8-29.8°C, Lake Monona,
  Wisconsin (Coutant 1977a, large fish, daytime)** — a real, Wisconsin-
  specific, primary field value, essentially identical to V0's
  undergraduate-report-sourced 27-29°C figure, now resting on a much
  stronger citation. Other rows: 20.5-24.6°C across seasons (winter through
  fall), 21-22°C (small fish, lab). **Tier: upgraded to agency-tier** (was
  explicitly flagged "weakest evidence" in V0).
- **Spawning trigger:** **Not found in GLFC Sp87-3** — the extracted text's
  black crappie section contains thermal-tolerance and preferred-temperature
  tables but no distinct spawning-and-development table (checked directly;
  the text transitions straight from the black-crappie preferred-temperature
  table into the next species' thermal-tolerance table). V0's original
  undergraduate-report-sourced feeding-events-vs-temperature finding (22.2%
  increase in feeding events with a 2°C rise) is retained unchanged, still
  flagged as weaker evidence (student research report, not a journal
  article). **Tier: single-source-speculative for this specific number,
  unchanged from V0.**
- **Sources:** GLFC Sp87-3, lines 9188-9250; V0's Minnesota State student
  research and 1968 CJFAS sources retained.
- **NEW — diel/low-light feeding (logged, not in V0):** Black crappie feed
  most actively during a nocturnal/crepuscular window, roughly midnight-2am
  with dusk/dawn secondary activity, driven by scotopic vision (tapetum
  lucidum, red-sensitive retinene2 pigment) analogous to walleye's mechanism.
  Diet studies show nocturnal prey (free-swimming Chaoborus/Procladius
  midge larvae) dominate stomach contents at night. **Sourcing note: the
  scotopic-vision/nocturnal-feeding-timing claim traces to general
  fish-biology reference compilations (Animal Diversity Web-tier sources) in
  this search pass, not a directly located journal article on black crappie
  specifically** — flagged as **not meeting this cycle's strict sourcing
  bar** for the specific clock-time claim, though the underlying prey-based
  diet evidence (nocturnal Chaoborus/Procladius dominance) does trace to real
  feeding-biology literature (the same Canadian Journal of Fisheries and
  Aquatic Sciences 1968 paper already cited in V0,
  `https://cdnsciencepub.com/doi/10.1139/f68-024`). **Tier:
  single-source-speculative for the specific nocturnal-timing claim; the
  general diel-shift/scotopic-vision mechanism is directionally consistent
  with well-established centrarchid/percid visual physiology (same family of
  mechanism as walleye) but not independently verified to the same standard
  here.**

### 8. Bluegill — carried forward, upgraded

- **Spawning trigger — upgraded from V0's number.** GLFC Sp87-3 spawning
  table (*Lepomis macrochirus*): **optimum 22.2-23.9°C, range 17-26°C**
  (Spotila et al. 1979 / Carlander 1977) — converts to **72-75°F optimum,
  63-79°F full range**, very close to V0's extension-sourced ~71.6°F
  (22°C)/65-80°F figures, now resting on a real primary compilation instead
  of angling-media sources (USAngler, Panfish Nation) as V0 explicitly
  flagged. **Tier: upgraded to agency-tier** (was explicitly flagged
  "extension-tier, not primary literature" in V0).
- **Feeding/activity (thermal preference):** GLFC preferendum table: 31°C
  (Cravens 1982), 31.2°C juvenile, 29.4-31.3°C (L. Monona, Wisconsin) — new
  to this document, V0 did not give bluegill a feeding-temperature number.
  Growth optimum: 30-31°C (multiple studies). **Tier: agency-tier.**
- **Repeat-spawning-through-summer claim** (V0's ~30-day interval while temp
  stays above 71.6°F) — not independently confirmed by GLFC Sp87-3 in this
  pass (the compilation's spawning table gives a temperature range, not a
  repeat-interval figure); retained from V0 but **still flagged as
  extension-tier** for the specific 30-day interval number.
- **Sources:** GLFC Sp87-3, lines 8456-8651; V0's extension sources retained
  for the repeat-spawning-interval claim only.

### 9. Chinook Salmon (Lake Michigan) — carried forward, re-verified

- **Feeding/activity temperature — carried forward from V0's predictor-eval
  upgrade, now independently re-confirmed in this pass's own read of the
  source text.** GLFC Sp87-3 preferendum table (*Oncorhynchus tshawytscha*):
  **11.7°C, Lake Michigan, adult (Coutant 1977a)** — confirms V0's
  eval-stage number exactly. Also 17.3°C ("thermal discharge" — an
  artificially warmed location, not representative of normal lake
  conditions) and 12-14°C (Lab, Scott & Crossman 1973, small fish). **Tier:
  well-established** (multiple Lake Michigan-specific field readings).
- **Growth optimum:** 14.4°C (fingerling), consistent with the general
  cold-water salmonid growth-optimum cluster.
- **Thermocline-tracking mechanism** — retained unchanged from V0, still
  real, still limited in practical use by the fact that surface buoy data
  (the only Lake Michigan water-temperature data this project has) cannot
  see the depth-following behavior described.
- **Sources:** GLFC Sp87-3, lines 2599-2685.

### 10. Coho Salmon (Lake Michigan) — carried forward, re-verified

- **Feeding/activity temperature:** GLFC preferendum table (*Oncorhynchus
  kisutch*): **11.4°C, Lake Michigan, adult, spring (Coutant 1977a)** —
  confirms V0's eval-stage number exactly. Also 16.6°C (Lab, Brown 1974,
  higher), 15/13°C (Point Beach, Lake Michigan, Michaud 1981). **Tier:
  well-established.**
- **Growth optimum:** 14.8°C (Jobling 1981) — very close to Chinook's 14.4°C,
  consistent with V0's "runs slightly warmer than Chinook" framing being
  directionally right even though the specific preferendum values (11.4 vs.
  11.7°C) are nearly identical rather than clearly separated in this source.
- **Sources:** GLFC Sp87-3, lines 2433-2477.

### 11. Brown Trout — carried forward, re-verified, range disclosed

- **Feeding/activity temperature — the V0 eval-doc's disclosed range
  re-confirmed directly in this pass.** GLFC Sp87-3 preferendum table (*Salmo
  trutta*): **18.3-23.9°C** (Scott & Crossman 1973, wide range), **13.8°C**
  (Lab, rising water temps, Cherry et al. 1977), **12.2°C** (max body temp,
  small fish, Spigarelli & Smith 1976), **12.4-17.6°C and 19.9°C** (Lake
  Michigan thermal discharge, Harrelson et al. 1984), **17.4°C** (Lake
  Michigan thermal discharge, Brown 1974), **12-16°C** (another row). This is
  a genuinely wide 12.2-23.9°C spread across studies/methods/life stages —
  the V0 eval step's disclosed 12.2-19.9°C range is a reasonable summary of
  the tighter Lake-Michigan-specific cluster within this wider full range.
  **Tier: agency-tier, wide real range disclosed rather than collapsed.**
- **Spawning trigger:** GLFC spawning table: **6.7-8.9°C, S.E. Ontario (Scott
  & Crossman 1973)**, also 4-11°C and 1.9-11.2°C ranges from other studies.
  Converts to roughly **40-48°F** — new to this document, V0 did not give
  brown trout a spawning-trigger number.
- **Sources:** GLFC Sp87-3, lines 2892-3022.

### 12. Lake Trout — carried forward, gap resolved (was flagged incomplete
    in V0, resolved in V0's own predictor-eval step, re-confirmed here)

- **Feeding/activity temperature:** GLFC preferendum table (*Salvelinus
  namaycush*): **11.8°C, Point Beach, Lake Michigan (Talmage & Coutant
  1980)** — confirms the number V0's predictor-eval step already extracted.
  Full scatter across studies: 10-15.5°C (multiple locations — White Lake
  Ontario 14°C, Lac La Ronge Saskatchewan 13°C, Cayuga Lake NY 11°C, Lake
  Superior 11.5-11.7°C). **Converts to roughly 50-60°F**, close to V0's
  original 40-52°F estimate but running a bit warmer in the confirmed primary
  data — disclosed, not silently corrected past what the source actually
  shows. **Tier: agency-tier, gap V0 flagged as "citation incomplete" is now
  closed.**
- **Spawning trigger:** GLFC spawning table: **8.9-13.9°C, Algonquin Park,
  Ontario (Scott & Crossman 1973)**, also 7.1-14.4°C and 5.5-10°C (MacLean et
  al. 1981). Converts to roughly **41-57°F**, i.e. fall spawning in cooling
  water — new to this document.
- **Sources:** GLFC Sp87-3, lines 3202-3311.

### 13. Barometric pressure — EXCLUDED, carried forward unchanged

Carried forward from V0 verbatim: explicitly checked, no primary scientific
support found across multiple independent sources; excluded per this
project's evidentiary-bar rule against angling folklore. Not re-litigated
this pass. **Tier: excluded-as-folklore.**

---

## New species this pass

### 14. Sauger — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table
  (*Stizostedion canadense*): a wide, somewhat inconsistent scatter —
  19.2°C (Norris Res., TN), 22.6°C (stream field), 21.3°C (Wabash R., IN),
  18.6-19.2°C and 22-28°C (Ohio R. power plant sites), 19°C (Lewis & Clark
  Res., S.D.). One row gives seasonal bands: summer 27-29°C, fall 14-21°C,
  winter 8-11°C, spring 7.2°C — a genuine seasonal-cycle pattern, not just
  scatter, but the underlying individual-study numbers disagree by several
  °C even within the same season, so **this is disclosed as real scatter,
  not resolved to one number.** **Tier: agency-tier but noisier than most
  other species in this compilation** — treat any single derived "sauger
  optimum" cautiously.
- **Spawning trigger:** GLFC spawning table: 4-14.4°C range (Hokanson 1977,
  N. Dakota/Tennessee); optimum 9-15°C (incubation), 12-15°C (EPA 1974),
  10°C range 6-14°C (another row). **Converts to roughly 43-59°F optimum
  cluster.** **Tier: agency-tier.**
- **Growth optimum:** 22°C, range 16.1-26°C (Smith & Koenst 1975).
- **Sources:** GLFC Sp87-3, lines 9585-9708.

### 15. White Crappie — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table (*Pomoxis
  annularis*): 19.8°C (winter, lab), 18.3°C (spring, lab), 10.4°C (fall, Ohio
  R.), 19.4°C (summer, Kansas Reservoir, O'Brien et al. 1984); another row:
  summer 24-30°C, fall 26°C, winter 8°C. **Notably cooler-running than Black
  Crappie's 27.8-29.8°C Wisconsin summer preferendum** — a real,
  species-level distinction worth preserving if both species are ever
  modeled together. **Tier: agency-tier.**
- **Spawning trigger:** GLFC spawning table: optimum 16-20°C range 14-23°C
  (EPA 1974); optimum 18-20°C (another row); optimum 14-16°C (a third row).
  **Converts to roughly 61-68°F optimum cluster, 57-73°F full range.**
  **Tier: agency-tier.**
- **Sources:** GLFC Sp87-3, lines 9098-9187.

### 16. Rock Bass — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table
  (*Ambloplites rupestris*): **21.3°C, Wisconsin lakes (Coutant 1977a)**,
  **20.7°C, Lake Monona, Wisconsin** — two directly Wisconsin-sourced field
  values, unusually strong for this project's purposes. Seasonal scatter:
  winter 21.6°C, spring 19.6-20.5°C, summer 18.7-20.2°C, fall 22.8°C — a
  real but fairly narrow (18.7-22.8°C) seasonal band overall. **Tier:
  well-established** (two independent Wisconsin field sources agreeing
  closely).
- **Spawning trigger:** GLFC spawning table: optimum 20.5-21°C (Lab/Michigan
  pond, Brown 1974); range 15.6-21.1°C (another study). **Converts to
  roughly 69-70°F optimum, 60-70°F full range.** **Tier: agency-tier.**
- **Sources:** GLFC Sp87-3, lines 8072-8192.

### 17. Pumpkinseed — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Lepomis gibbosus*):
  optimum 24-28°C, range 20-29°C (Lake, N.Y., Brown 1974); range 20-27.8°C
  (Georgian Bay, Ontario, Scheider & Becker et al. 1975); a notably cooler
  second row from the same Georgian Bay source: range 13-18°C. **Converts to
  roughly 68-84°F for the warmer cluster, 55-64°F for the cooler row** — a
  real disagreement even within the same source/location, disclosed rather
  than averaged away. **Tier: agency-tier, real within-source scatter
  disclosed.**
- **Feeding/activity temperature / growth optimum:** **Not found in the
  extracted GLFC Sp87-3 text** — the pumpkinseed section in the local file
  contains only the spawning-and-development table, no separate
  preferred-temperature or growth table (checked directly; the text
  transitions straight to bluegill's thermal-tolerance table after the
  pumpkinseed spawning table). **Gap disclosed, not filled with a
  lower-tier substitute.**
- **Sources:** GLFC Sp87-3, lines 8418-8455.

### 18. White Bass — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table (*Morone
  chrysops*): adult summer 28-30°C (Lab, Coutant 1977a), 29-34°C (power
  plant discharge site — warmer, less representative), YOY summer 27.8-31°C,
  adult winter/spring 12-17°C, adult fall 16-17°C. **A real, wide seasonal
  swing (roughly 12-30°C, 54-86°F) rather than a single value** — disclosed
  as a seasonal range, not a fixed optimum. **Tier: agency-tier.**
- **Spawning trigger:** GLFC spawning table: range 12-24°C, optimum 19°C
  MWAT (EPA 1974); range 14.4-21.1°C (McCormick 1978); optimum 14.7-16.3°C
  (another row); range 13-26°C (a fourth row). **Converts to roughly
  53-70°F optimum cluster.** **Tier: agency-tier.**
- **Sources:** GLFC Sp87-3, lines 7986-8071.

### 19. Rainbow Trout / Steelhead — new (WI's #2 most-stocked species by
    record count in the real data)

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table (*Salmo
  gairdneri*) shows very wide scatter across studies: 13-15°C (fry, Lab,
  Talmage & Coutant 1980), 18.9-21.7°C (Coutant 1977a), 11.3-22.2°C
  (multiple Spotila/Jobling/Cherry et al. rows), 11.6°C (McCauley & Huggins
  1976), 17.5°C (Spigarelli & Smith 1976), 15-17°C (Point Beach NGS, Lake
  Michigan discharge-adjacent field readings). **This is genuinely the
  widest and least converged scatter of any salmonid in this document** —
  reported here as a real range (roughly 11-22°C, 52-72°F) rather than
  forced into one number. **Tier: agency-tier, wide disclosed range.**
- **Spawning trigger:** GLFC spawning table: range 10-15.5°C (Scott &
  Crossman 1973); optimum 7-10°C range 3.2-15.5°C (Spotila et al. 1979);
  optimum 6-8°C range 0.3-10°C (Moore 1979); range 5.5-13°C. **Converts to
  roughly 43-60°F optimum cluster** — consistent with rainbow trout/steelhead
  being an early-spring spawner in Wisconsin tributaries, ahead of most
  warm-water species.
- **Growth optimum:** 16.5-17.2°C (Jobling 1981), 12.8°C (Brown 1974,
  wider-range study).
- **Seasonal movement (steelhead-strain specific, not from GLFC Sp87-3):**
  Wisconsin's stocked rainbow trout include a steelhead strain that runs
  Lake Michigan tributaries; anadromous-form spring/fall tributary migration
  is well-documented general steelhead biology but a Lake-Michigan-specific
  primary citation for run timing was not located within this pass's time
  budget — **flagged as a real, well-established general mechanism, not
  independently verified against a Lake Michigan-specific source here.**
  **Tier: single-source-speculative for the Lake Michigan-specific run-timing
  claim; general steelhead migratory-run biology is well-established
  elsewhere in the literature.**
- **Sources:** GLFC Sp87-3, lines 2686-2891.

### 20. Brook Trout — new (WI's #3 most-stocked species by record count)

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table
  (*Salvelinus fontinalis*): 19-20.3°C across several field sites (Moosehead
  Lake, Maine; Redrock Lake, Ontario; southern Ontario streams; Lake
  Michigan) — a fairly tight cluster for a wild-population preferendum.
  Lab/fed-vs-starved comparison: 15.7°C (fed) vs. 14.8°C (starved) — a real,
  specific finding that feeding state itself shifts the measured
  preferendum, worth flagging as a methodological note for anyone using
  preferendum values generally. **Tier: agency-tier.**
- **Spawning trigger:** GLFC spawning table: optimum 10.7°C (Minnesota,
  Brown 1974); range 2.2-11.7°C (SW Ontario streams, Witzel & MacCrimmon
  1983); range 4-13°C (another row). **Converts to roughly 36-56°F**, a fall
  spawner in cold water, consistent with brook trout's well-known
  cold-adapted life history. **Tier: agency-tier.**
- **Sources:** GLFC Sp87-3, lines 3023-3201.

### 21. Cisco / Lake Herring — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Coregonus artedii*):
  **optimum 3.3°C, range 3.3-5°C, Wisconsin (Scott & Crossman 1973)** — a
  directly Wisconsin-sourced, very cold, late-fall/early-winter spawning
  trigger (**38-41°F**), consistent with cisco's well-known deep, cold-water,
  fall-spawning life history. Other rows: range 1.0-5.0°C, incubation 5.6°C.
  **Tier: agency-tier**, Wisconsin-specific.
- **Feeding/activity temperature:** **No dedicated preferred-temperature
  table located for Cisco specifically in the extracted GLFC text** — only
  the spawning table was found (the compilation's next Coregonus species,
  bloater, does have a preferred-temperature table, but that is a distinct
  species, not substituted here). **Gap disclosed.**
- **Sources:** GLFC Sp87-3, lines 3440-3488.

### 22. Lake Whitefish — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table
  (*Coregonus clupeaformis*): 12.7°C (small, 2 yr, Lab), 17°C (juvenile,
  South Bay, Lake Huron), 12-16°C and 13.5°C (larvae, Lab), 15.5°C
  (Moosehead Lake, Maine), 10°C (Lake Erie/Lake Ontario, surface water,
  Brown 1974), 4°C (young, Point Beach, Lake Michigan — a notably cold
  outlier for young fish). **A real range of roughly 4-17°C (39-63°F)**
  across life stages, consistent with lake whitefish being a cold, deep,
  benthic-feeding coregonid. **Tier: agency-tier.**
- **Spawning trigger:** GLFC spawning table: range 0.5-4.5°C (Lake Erie);
  optimum 0.5°C range 0.5-6.1°C (Bay of Quinte, Lake Ontario). **Converts to
  roughly 33-40°F** — a very cold, late-fall spawner, consistent with
  cisco's spawning window (they are congeners). **Tier: agency-tier.**
- **Sources:** GLFC Sp87-3, lines 3638-3719.

### 23. White Sucker — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Catostomus commersoni*):
  **optimum 10°C, range 4-18°C, MWAT 10°C (EPA 1974)**; a second row,
  optimum 15.2°C range 10-20°C (Brown 1974); range 12.2-24°C (Marcy 1976b,
  wider/warmer, possibly a different regional population); range 3-16.5°C
  and 6-16.8°C (Connecticut R. and Jack L., Ontario, Corbett & Powles 1983).
  **Converts to roughly 39-64°F across the full disclosed range, with the
  10°C/4-18°C row (39-64°F) being the best-supported single estimate** — a
  classic early-spring spawner, consistent with white sucker's well-known
  life history (spawns before most gamefish). **Tier: agency-tier.**
- **Growth optimum:** 24-27°C (larvae/juvenile, several rows) — notably
  warmer than the spawning trigger, consistent with a species that spawns
  cold but grows fastest in warm water.
- **Sources:** GLFC Sp87-3, lines 6536-6613.

### 24. Channel Catfish — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Ictalurus punctatus*):
  **optimum 26.7°C, range 23.9-29.5°C (Scott & Crossman 1973)**; a second
  row, optimum 22°C range 22.8-23.9°C (EPA 1974). **Converts to roughly
  73-85°F for the warmer/wider row, 73-75°F for the narrower row** — a
  genuinely late, warm-water spawner among this project's species, well
  after most panfish/gamefish. **Tier: agency-tier.**
- **Feeding/activity temperature / growth optimum:** **Not found in the
  extracted GLFC Sp87-3 text** — the channel catfish section in the local
  file contains only the spawning table (checked directly; text transitions
  straight from the channel-cat spawning table to the next species, stone
  cat). **Gap disclosed, not filled with a lower-tier substitute for this
  specific number.**
- **NEW — diel/nocturnal feeding (well-established, peer-reviewed, directly
  on this species):** A direct field study (juvenile channel catfish,
  offshore breakwaters, Lake Kasumigaura, Japan) found juveniles more
  abundant and actively feeding at night than during the day, with prey
  composition (chironomid larvae, cladocerans) shifting between day and
  night, consistent with genuine diel foraging-behavior change rather than
  just fish being harder to see at night. **Not a Great Lakes/Wisconsin
  study, but a direct, peer-reviewed, species-specific field study — meets
  this cycle's sourcing bar.** **Tier: well-established** (direct
  species-specific peer-reviewed field study, though not local to this
  project's geography).
  - Source: "Nocturnal activity and feeding of juvenile channel catfish,
    Ictalurus punctatus, around offshore breakwaters in Lake Kasumigaura,
    Japan," Ichthyological Research, Springer:
    `https://link.springer.com/article/10.1007/s10228-018-0653-4`
- **NEW — dissolved-oxygen threshold (aquaculture-context, flagged):**
  Aquaculture literature identifies a critical minimum DO around **3 mg/L**
  for channel catfish (below which mechanical aeration is applied to avoid
  losses) and consistent, significant negative growth/consumption effects
  below **4.5 mg/L**. **Sourcing note: this traces to pond-aquaculture
  production literature (Boyd 2018, Journal of the World Aquaculture
  Society; production studies), not a wild-population field study** —
  **flagged as not fully meeting this cycle's strict wild-catchability
  sourcing bar**, though the underlying physiological DO-tolerance mechanism
  is real and the specific mg/L numbers are peer-reviewed. **Tier:
  single-source-speculative for direct application to wild lake
  populations; the DO-sensitivity mechanism itself is well-established
  ictalurid physiology.**
- **Sources:** GLFC Sp87-3, lines 7306-7341; Springer 2018 (above); Boyd
  2018 and related aquaculture DO literature (flagged).

### 25. Freshwater Drum — new

- **Feeding/activity temperature:** GLFC Sp87-3 preferendum table
  (*Aplodinotus grunniens*): **29.5-30.3°C, Lake Monona, Wisconsin, summer
  (Coutant 1977a)** — a directly Wisconsin-sourced summer preferendum,
  among the warmest of any species in this document, consistent with
  freshwater drum's known warm-water/turbid-water tolerance. Also 31.3°C
  (fall, Lab), 22.2°C (large fish, Norris Res., TN), 19.6-26.5°C (a cooler
  scatter of other rows). **Tier: agency-tier**, Wisconsin-specific summer
  value is the strongest single number.
- **Spawning trigger:** GLFC spawning table: **optimum 21°C, range
  18-22.2°C, Wisconsin (Brown 1974)** — a second directly Wisconsin-sourced
  value. Converts to **64-72°F**. **Tier: agency-tier**, Wisconsin-specific.
- **Growth optimum:** 22°C (Brown 1974).
- **Sources:** GLFC Sp87-3, lines 10163-10235.

### 26. Burbot — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Lota lota*): **optimum
  0.6-1.7°C, surface water temperature (Scott & Crossman 1973)** — an
  extremely cold, under-ice, mid-winter spawning trigger (roughly **33-35°F**
  — essentially at the freezing point), consistent with burbot being the
  only member of the cod family in Great Lakes fresh water and one of the
  very few North American freshwater fish to spawn under ice in winter. Also
  0-1.5°C (incubation), hatching below 8-10°C. **Tier: agency-tier.**
- **Growth optimum:** 15.6-18.3°C — notably much warmer than the spawning
  trigger, another species where spawning-cold and growth-warm are cleanly
  separated in the data.
- **Feeding/activity (preferred temperature) table:** present as a header in
  the extracted text but **no data rows found beneath it** — the burbot
  preferred-temperature table appears to be an empty/unfilled table in the
  original 1987 compilation itself (not an extraction failure on this pass's
  part — the header exists with no numeric content below it, and the growth
  table immediately follows). **Gap disclosed** — this is a rare case where
  the primary source itself apparently had a data gap for this metric in
  1987.
- **Sources:** GLFC Sp87-3, lines 7536-7580.

### 27. Fathead Minnow — new

- **Spawning trigger:** GLFC Sp87-3 spawning table (*Pimephales promelas*):
  onset ~15.6°C (spring, Carlander 1969); range 15.6-17.8°C (minimum temp,
  Quebec lake, Scott & Crossman 1973); cessation range 15.6-18.4°C (fall);
  a warmer outlier row, >27°C (summer, Gale & Buynak 1982); range
  15.6-28.9°C (outdoor experimental pool, Pennsylvania). **Converts to
  roughly 60-64°F onset, with spawning continuing into much warmer water
  through summer (up to ~84°F in the widest row)** — consistent with fathead
  minnow's well-known status as a prolific multi-brood summer spawner.
  **Tier: agency-tier.**
- **Relevance note:** Fathead minnow is present in the real WI stocking data
  primarily as **forage/baitfish stocking** (private ponds, forage
  establishment), not as an angling target species — included here for
  completeness since it appears in the real data, but has essentially no
  angler-catchability-relevant literature the way gamefish do; the spawning
  number above is the only usable metric found.
- **Sources:** GLFC Sp87-3, lines 5898-5935.

### 28. Lake Sturgeon — new, **not covered by GLFC Sp87-3 at all**

- **GLFC Sp87-3 coverage: none.** Directly confirmed by searching the entire
  10,440-line extracted text for `Acipenser fulvescens` and `sturgeon` —
  Lake Sturgeon appears only in the compilation's front-matter master
  species list (as a species considered "least represented" thermally in
  the introduction's own text, alongside darters, minnows, and suckers) and
  never in a per-species data table. This is a genuine, disclosed gap in
  the primary source this document otherwise relies on heavily.
- **Spawning trigger — from independent literature, converging agency +
  peer-reviewed sources:**
  - **Wisconsin DNR (agency, media-reported):** "sturgeon usually spawn when
    the water temperature is about 53 degrees Fahrenheit" (11.7°C), with
    the trigger shifting to 58-59°F in low-water-flow/fast-warming years
    and as low as 53°F in high-flow/slow-warming years. **Sourcing note:
    this specific quote is reported via a local news article
    (fox11online.com) attributing it to WDNR, not a WDNR document directly
    retrieved and read in this pass — flagged as agency-adjacent
    (media-reported agency statement), not a directly-cited primary WDNR
    report.**
    Source: `https://fox11online.com/news/local/as-waters-warm-wisconsin-dnr-says-the-start-of-sturgeon-spawning-is-near-department-natural-resources-wolf-river-shiocton-bamboo-bend`
  - **Peer-reviewed field study (Richelieu River, Quebec):** spawning
    occurred at water temperatures averaging **13.4°C (range 11.5-15.5°C)**;
    females moved onto spawning sites across a broader 8.8-19.1°C range,
    with peak spawning activity concentrated at 11.5-16.0°C; males began
    cruising spawning grounds from 8.8-16.0°C. Egg incubation survival
    highest within a narrower 14-16°C sub-range of a broader 10-18°C
    viable-incubation range.
    Source: "Biology of lake sturgeon (Acipenser fulvescens) spawning below
    a dam on the Richelieu River, Quebec: behaviour, egg deposition, and
    endocrinology," Canadian Journal of Zoology:
    `https://cdnsciencepub.com/doi/10.1139/cjz-2012-0298`
  - **These two independent sources converge well**: 53°F = 11.7°C sits
    almost exactly at the low end of the peer-reviewed study's 11.5-16.0°C
    peak-activity band, and the peer-reviewed study's 13.4°C mean converts
    to 56.1°F, squarely inside the WDNR-quoted 53-59°F range. **Tier:
    agency-tier overall** (the peer-reviewed Quebec field study alone would
    justify well-established, but it is one river system, not
    Wisconsin-specific, so agency-tier is the more conservative call;
    the Wisconsin-specific number is media-reported-agency, not a directly
    read primary document).
- **Seasonal movement:** Well-documented spring spawning-run behavior into
  rivers/rapids over rock or gravel substrate (Wolf River, Wisconsin being
  the most visible real-world example, per the WDNR viewing-location pages
  reviewed this pass), a genuine seasonal nearshore/riverine migration
  distinct from this species' otherwise deep, lake-dwelling year-round
  habitat use. **Tier: well-established as a general life-history pattern**
  (widely documented across the primary literature reviewed above and
  multiple state/provincial agency sources), though a single quantitative
  migration-timing/distance metric specific to Wisconsin beyond the
  temperature trigger above was not located in this pass.
- **Feeding/activity temperature, dissolved-oxygen thresholds, diel
  patterns:** **Not located within this pass's search budget.** Logged as
  an open gap for a future cycle, not fabricated.

---

## Diel/light-driven activity — cross-species log (per task instruction:
   logged even where not currently actionable)

| Species | Mechanism | Tier | Source |
|---|---|---|---|
| Walleye | Scotopic vision, tapetum lucidum; CPUE peaks ~300 lux (dusk/dawn) | well-established | Ryder 1977 (carried forward from V0) |
| Black Crappie | Scotopic vision (tapetum lucidum, retinene2 pigment); nocturnal/crepuscular feeding peak reported ~midnight-2am; nocturnal-prey (Chaoborus/Procladius) dominance in diet | single-source-speculative for timing specifics; general mechanism plausible | General fish-biology references (not journal-tier for the clock-time claim); CJFAS 1968 (`10.1139/f68-024`) for diet/prey evidence |
| Channel Catfish | Nocturnal activity increase and diel diet-composition shift (chironomids/cladocerans) | well-established | Springer/Ichthyological Research 2018, Lake Kasumigaura, Japan |

Per the same data-granularity caveat V0 raised: this project's real
Wisconsin stocking and survey data (`data/v1/wi_stocking_statewide_2011_2025.csv`,
`data/v1/wi_fisheries_survey_species_sample.csv`) has no trip-level or
sub-daily catch timestamp either — these remain logged as real science, not
yet testable against this project's specific outcome data, exactly as V0
handled walleye diel behavior. Per `CLAUDE.md`, this V1 cycle's actual
deliverable (a per-lake conditions narrative, not catch-rate validation) may
be able to use current time-of-day directly in a narrative sense (e.g. "low
light conditions favor walleye/crappie/catfish feeding activity right now")
without needing historical trip-level outcome data to validate a
correlation — flagged for whoever builds that narrative logic next.

---

## Notes for next steps

1. All three new diel-feeding species-mechanisms (walleye carried forward,
   black crappie and channel catfish new) point toward the same underlying
   biology (low-light visual advantage for predation) recurring across
   families (Percidae, Centrarchidae, Ictaluridae) — worth treating as a
   general "many gamefish feed more actively at dawn/dusk/night" narrative
   building block rather than three unrelated species-specific facts, if
   the V1 narrative tool wants a general low-light framing.
2. Muskellunge's real thermal-optimum disagreement (Section 6 above, 22°C
   vs. 24-27°C) should be resolved with an explicit choice (and stated
   rationale) by whoever builds narrative logic using this candidate — this
   document intentionally does not pick a winner.
3. Lake Sturgeon's coverage remains the thinnest in this document — GLFC
   Sp87-3 gives nothing, CCRR-17 remains unretrieved after three attempts,
   and this pass located only a spawning-temperature number (well-converged
   across two sources) with no feeding-temperature, DO, or diel data found.
   A future cycle attempting a fourth CCRR-17 retrieval, or searching
   specifically for Lake Sturgeon feeding-ecology/DO literature, would close
   a real gap.
4. Species present in the real WI data but still not covered by any
   document in this project: bullheads (black/brown/yellow — all three
   appear in the real survey sample), Common Carp, Golden Shiner, and
   various hybrid/rough-fish categories in the stocking data. These were
   checked against GLFC Sp87-3's table of contents (all three bullhead
   species and carp do have entries: lines 7061-7402 for bullheads,
   4628-4820 for carp) but were judged out of scope for this pass given the
   task's explicit species-priority list — logged here so a future pass
   does not have to re-discover that these tables exist in the local source
   file if they become priority species later.
5. Barometric pressure (Section 13) remains excluded; not re-litigated.

---

*End of document. This is a research-only document (per this project's
`CLAUDE.md`, no STATE.md update, no commit, no action on any recommendation
without explicit CEO approval). It supersedes
`docs/v0_physiology_research_candidates.md` for all future reference —
that V0 document should be treated as historical/superseded, not as an
independent second source.*
