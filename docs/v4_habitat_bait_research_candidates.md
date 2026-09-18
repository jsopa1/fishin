# V4 Habitat & Bait Research (Phase 0 of the UX redesign)

**Status: in progress - 18 of 27 species researched.** Spec:
[v4_ux_goal_loop_spec.md](v4_ux_goal_loop_spec.md). Data:
[habitat_reference_v1.json](../data/v1/habitat_reference_v1.json),
[bait_catalog_v1.json](../data/v1/bait_catalog_v1.json),
[species_bait_map_v1.json](../data/v1/species_bait_map_v1.json). Guards:
`analysis/tests/test_v4_habitat_bait_data.py` (structure) and
`analysis/verify_v4_research_quotes.py` (re-fetches every source and confirms every stored
quote is present verbatim; last run: 235/235 quotes found across 19 sources before the
latest batches - rerun before each commit).

## Method

Same bar as `docs/v1_physiology_research_candidates.md`. Primary sources are Wisconsin DNR
Bureau of Fisheries Management species fact sheets (PDF), WDNR species pages, and
peer-reviewed field studies. Tackle-maker marketing, forums and blogs are not used. A source
is only cited after its full text was read; a search-result or fetch-tool summary is never
treated as verification. Every claim stores its citation, URL, retrieval date and a verbatim
quote, and quotes are added to the data only if they are found word-for-word in the
extracted source text (any mismatch aborts the write). Tiers: well-established (>=2
independent sources), agency-tier (agency statement or one solid peer-reviewed study),
single-source-speculative. Bait guidance is the *what* and *how* the agency states; it is
angling convention, not tested science, and is never presented as research (Decision #005).
Bait count per species is whatever the sources support; every bait links to a species only
with a quoted source. `states` is `["any"]` because none of the sources tie a bait to a
specific thermal state - the earlier temperature-state guesses were removed.

## Coverage so far

| Species | Habitat claims | Bait links | Technique notes |
|---|---|---|---|
| Black Crappie | 6 | 7 | 1 |
| Bluegill | 7 | 5 | 0 |
| Brook Trout | 5 | 5 | 0 |
| Brown Trout | 5 | 4 | 0 |
| Channel Catfish | 5 | 14 | 1 |
| Chinook Salmon | 4 | 6 | 0 |
| Coho Salmon | 3 | 6 | 0 |
| Lake Sturgeon | 3 | 2 | 1 |
| Lake Trout | 3 | 4 | 0 |
| Largemouth Bass | 6 | 4 | 1 |
| Muskellunge | 6 | 4 | 1 |
| Northern Pike | 5 | 4 | 1 |
| Pumpkinseed | 4 | 6 | 0 |
| Rainbow Trout | 4 | 10 | 0 |
| Smallmouth Bass | 3 | 4 | 1 |
| Walleye | 8 | 9 | 2 |
| White Crappie | 6 | 7 | 1 |
| Yellow Perch | 5 | 7 | 3 |
| **Total** | **88** | | |

Bait catalog: 48 items. Not yet researched: Sauger, Rock Bass, White Bass, Burbot,
Freshwater Drum, Lake Whitefish, Cisco, White Sucker, Fathead Minnow (WDNR has no fact
sheet for these; other agency sources are being sought).

## Disagreements and limits (disclosed, not resolved)

- Yellow perch spawning temperature: WDNR fact sheet 44-52 F vs WDNR species page 45-52 F.
- Muskellunge: WDNR's 33-78 F comfort range sits beside the already-disputed thermal optimum in
  the app's physiology data; shown together, not merged.
- Trout and salmon sheets (Brook, Brown, Rainbow, Lake, Chinook, Coho) are Lake Michigan
  sport-fish publications; lake statements are specific to Lake Michigan and inland
  conditions are not covered by them.
- The Channel Catfish PDF text has OCR spacing artifacts (e.g. "7 5 degrees"); quoted as
  extracted.
- Raabe & Bozek 2012 (walleye spawning) is one Wisconsin lake.

## Wisconsin bait regulations

Only rules WDNR states on the pages read are recorded (each with a quote): live crayfish may
not be possessed while fishing on inland waters except the Mississippi River (Smallmouth Bass
page). Every other bait is explicitly `NOT_YET_RESEARCHED` - a dedicated regulations pass
(NR 19/20: live baitfish, egg baits, invasive-species rules) is required before Fish Detail
may present any live bait as usable on all waters.

## Failed retrievals (logged, nothing claimed from them)

- Knight 1984, *Piscivory by Walleyes and Yellow Perch in Western Lake Erie*, Trans. Am. Fish.
  Soc. 113:677-693 - HTTP 403; abstract unread, not cited.
- WDNR species pages for Channel Catfish, Lake Sturgeon, Pumpkinseed and the trout/salmon
  group contain only links to PDFs; the PDFs were used instead.
