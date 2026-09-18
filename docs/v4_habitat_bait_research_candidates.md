# V4 Habitat & Bait Research (Phase 0 of the UX redesign)

**Status: species research complete for all 27 of 27 species; Wisconsin bait-regulation pass done for most baits; public-domain images done for all 27 species and 7 baits.**
Spec: [v4_ux_goal_loop_spec.md](v4_ux_goal_loop_spec.md). Data:
[habitat_reference_v1.json](../data/v1/habitat_reference_v1.json),
[bait_catalog_v1.json](../data/v1/bait_catalog_v1.json),
[species_bait_map_v1.json](../data/v1/species_bait_map_v1.json). Guards:
`analysis/tests/test_v4_habitat_bait_data.py` (structure, coverage of all 27 species) and
`analysis/verify_v4_research_quotes.py` (re-fetches every source and confirms every stored quote is present verbatim;
last run: **366 of 366 quotes found across 33 sources**; a negative control confirmed it fails on an altered quote).

## Method

Same bar as `docs/v1_physiology_research_candidates.md`. Primary sources are Wisconsin DNR
Bureau of Fisheries Management species fact sheets (PDF) and species pages, plus other state
and federal agency profiles where WDNR publishes none (Minnesota DNR, Iowa DNR, Michigan DNR,
Indiana DNR, US Fish & Wildlife Service) and peer-reviewed field studies. Tackle-maker
marketing, forums and blogs are not used. A source is cited only after its full text was read;
a search-result or fetch-tool summary is never treated as verification. Every claim stores its
citation, URL, retrieval date and a verbatim quote, and a quote enters the data only if it is
found word-for-word in the extracted source text. Claims whose only source is a non-Wisconsin
agency carry `wi_applicable: false`. Tiers: well-established (>=2 independent sources),
agency-tier (agency statement or one solid peer-reviewed study). Bait guidance is what the agency
states; it is angling convention, not tested science, and is never presented as research
(Decision #005). Bait count per species is whatever the sources support; a bait is linked to a
species only with a quoted source. `states` is `["any"]` because no source ties a bait to a
specific thermal state - an earlier guess was removed. Species whose source names no bait carry
`reason_no_links` instead of a guess.

## Coverage

| Species | Habitat claims | Bait links | Technique notes | Source hosts |
|---|---|---|---|---|
| Black Crappie | 6 | 7 | 1 | dnr.wisconsin.gov |
| Bluegill | 7 | 5 | 0 | dnr.wisconsin.gov |
| Brook Trout | 5 | 5 | 0 | dnr.wisconsin.gov |
| Brown Trout | 5 | 4 | 0 | dnr.wisconsin.gov |
| Burbot | 4 | 3 | 1 | dnr.wisconsin.gov, www.dnr.state.mn.us |
| Channel Catfish | 5 | 14 | 1 | dnr.wisconsin.gov |
| Chinook Salmon | 4 | 6 | 0 | dnr.wisconsin.gov |
| Cisco | 3 | 0 | 0 | www.fws.gov |
| Coho Salmon | 3 | 6 | 0 | dnr.wisconsin.gov |
| Fathead Minnow (not an angling target) | 2 | 0 | 0 | programs.iowadnr.gov |
| Freshwater Drum | 3 | 4 | 0 | www.in.gov |
| Lake Sturgeon | 3 | 2 | 1 | dnr.wisconsin.gov |
| Lake Trout | 3 | 4 | 0 | dnr.wisconsin.gov |
| Lake Whitefish | 3 | 0 | 0 | www.michigan.gov |
| Largemouth Bass | 6 | 4 | 1 | dnr.wisconsin.gov |
| Muskellunge | 6 | 4 | 1 | dnr.wisconsin.gov |
| Northern Pike | 5 | 4 | 1 | dnr.wisconsin.gov |
| Pumpkinseed | 4 | 6 | 0 | dnr.wisconsin.gov |
| Rainbow Trout | 4 | 10 | 0 | dnr.wisconsin.gov |
| Rock Bass | 2 | 5 | 0 | www.michigan.gov |
| Sauger | 4 | 4 | 1 | programs.iowadnr.gov, www.dnr.state.mn.us |
| Smallmouth Bass | 3 | 4 | 1 | dnr.wisconsin.gov |
| Walleye | 8 | 9 | 2 | dnr.wisconsin.gov, www.usgs.gov |
| White Bass | 3 | 3 | 0 | www.michigan.gov |
| White Crappie | 6 | 7 | 1 | dnr.wisconsin.gov |
| White Sucker (not an angling target) | 2 | 0 | 0 | programs.iowadnr.gov |
| Yellow Perch | 5 | 7 | 3 | dnr.wisconsin.gov |
| **Total** | **114** | | | |

Bait catalog: 51 items.

## Disagreements and limits (disclosed, not resolved)

- Yellow perch spawning temperature: WDNR fact sheet 44-52 F vs WDNR species page 45-52 F.
- Muskellunge: WDNR's 33-78 F comfort range sits beside the already-disputed thermal optimum in
  the app's physiology data; shown together, not merged.
- Brown trout: WDNR's Lake Michigan sheet lists a 65-75 F preferred range, far warmer than the
  other trout/salmon sheets (48-57 F); reproduced as stated, not reconciled.
- The trout and salmon sheets (Brook, Brown, Rainbow, Lake, Chinook, Coho) are Lake Michigan
  sport-fish publications; lake statements are specific to Lake Michigan.
- Sauger, White Bass, Rock Bass, Lake Whitefish, Cisco, Freshwater Drum, Burbot (partly), White
  Sucker and Fathead Minnow rest on non-Wisconsin agency pages (no WDNR fact sheet exists);
  marked `wi_applicable: false`.
- Rock Bass and Lake Whitefish have no structure/bait statements on the pages read; left
  undocumented. Lake Whitefish and Cisco list no baits for that reason.
- The Channel Catfish PDF text has OCR spacing artifacts (e.g. "7 5 degrees"); quoted as extracted.
- Raabe & Bozek 2012 (walleye spawning) is one Wisconsin lake.

## Wisconsin bait regulations

Sourced from WDNR's "How VHS rules affect anglers" Q&A, WDNR's "Using fish as bait" page and Wis.
Admin. Code NR 20.06, each with verbatim quotes (`wi_regulation_sources` in the catalog):

- Live minnows: wild-caught minnows only on the water they came from; bought minnows reusable under
  conditions (up to 2 gallons, no lake water, no other fish); minnow harvest closed on VHS waters;
  NR 20.06(11) - a minnow 8 inches or longer needs a quick-strike rig or non-offset circle hook.
- Other fish as bait (suckers, chubs, bullheads): only fish caught in that water, unless dead and
  preserved; live game/rough fish generally cannot be moved; counts toward bag limit. Whether
  NR 20.06(11) covers 10-14 inch live suckers (as WDNR's musky sheet describes) is *not* determined
  by the pages read - the catalog says so and tells the reader to check current regulations.
- Dead/frozen bait: caught on that water or preserved without refrigeration; exceptions for Lake
  Michigan/Green Bay. Spawn: Lake Michigan spawn on Lake Superior only if preserved.
- Worms, leeches, insects, larvae: generally legal; drain all water from containers when leaving.
- Live crayfish: not to be possessed while fishing on inland waters except the Mississippi River.
- Artificial lures: NR 20.06 limits (3 hooks/baits/lures; artificial-only waters).

Still `NOT_YET_RESEARCHED` (11 items, each with its reason): crayfish tails, shrimp, tip-ups (line/tip-up
count rules), stink bait, meat strips, dough balls, frogs, grasshoppers, clams, and the two
unspecified-live-bait entries. Fish Detail must show these with no "cleared for use" claim.

## Public-domain images

`data/v1/image_manifest_v1.json` records every shipped image (files under `webapp/static/img/species/` and
`.../baits/`): Commons file page, original URL, author/credit, date, license string, and the public-domain
template found on the page. **Double check applied to each image:** the Commons license field must read
"Public domain" or CC0 *and* a public-domain template must exist in the page wikitext. Result: all 27 species
and 7 baits pass (`analysis/verify_v4_images.py`: 34 checked, 0 failing). Species images are US Fish & Wildlife
Service illustrations (Duane Raver, Timothy Knepp) or USFWS photographs (US government works), except Lake
Whitefish, a pre-1929 engraving (H. L. Todd, PD-US). Files are the 800px versions Commons serves.

Every image was viewed after download. Three bait images were **rejected after review** and not shipped: a
microscope slide of an earthworm, a photo of students sampling a stream (no hellgrammite visible) and a shed
dragonfly skin; two more (earthworm, crankbaits) failed the template check. Baits with no verified image
(worms, nightcrawlers, leeches, plugs, spinners, shrimp, frogs, stink bait, spawn, tip-ups and others) show an
explicit no-image state. Bait-fish entries (minnows, suckers) reuse the fathead-minnow / white-sucker species
image and say so. The Chinook, Coho and Cisco pictures are USFWS-identified photos of fish in the hand;
species identity rests on the USFWS file title.

## Failed retrievals (logged, nothing claimed from them)

- Knight 1984, *Piscivory by Walleyes and Yellow Perch in Western Lake Erie*, Trans. Am. Fish.
  Soc. 113:677-693 - HTTP 403; abstract unread, not cited.
- WDNR species pages for Channel Catfish, Lake Sturgeon, Pumpkinseed and the trout/salmon group
  hold only links to PDFs; the PDFs were used instead.
- Minnesota DNR MinnAqua profiles for Cisco and Freshwater Drum: HTTP 404 (USFWS and Indiana DNR used).
