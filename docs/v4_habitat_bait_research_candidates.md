# V4 Habitat & Bait Research (Phase 0 of the UX redesign)

**Status: in progress - 1 of 27 species started (Walleye, partial).** Spec:
[v4_ux_goal_loop_spec.md](v4_ux_goal_loop_spec.md). Data:
[habitat_reference_v1.json](../data/v1/habitat_reference_v1.json),
[bait_catalog_v1.json](../data/v1/bait_catalog_v1.json),
[species_bait_map_v1.json](../data/v1/species_bait_map_v1.json). Guards:
`analysis/tests/test_v4_habitat_bait_data.py`.

## Method

Same bar as `docs/v1_physiology_research_candidates.md`. Sources: Wisconsin
DNR species and management pages, USGS/USFWS, peer-reviewed field studies
(AFS journals), diet studies, agency angler-education material. Tackle-maker
marketing, forums and blogs are not used. Every claim stores its citation, URL,
retrieval date and a **verbatim quote** so the QA pass (re-check every 5th claim
against the source) can be done mechanically. Tiers: well-established (>=2
independent sources), agency-tier (agency statement or one solid peer-reviewed
study), single-source-speculative. A search-result summary is never treated as
verification; a claim is only recorded after the source page itself was read.
Bait guidance keeps forage/diet basis (research) separate from technique
(angling convention). Bait count per species is whatever the sources support.

## Progress

| Family | Species | State |
|---|---|---|
| Percids | Walleye | habitat: 3 claims; bait: 5 links (all from one WDNR page, agency-tier); how-to-use, regulations and diet-study basis still open |
| Percids | Sauger, Yellow Perch | not started |
| Centrarchids, esocids, salmonids, catfish/sturgeon/other | 23 species | not started |

## Failed retrievals (logged, nothing claimed from them)

- Knight 1984, *Piscivory by Walleyes and Yellow Perch in Western Lake Erie*,
  Trans. Am. Fish. Soc. 113:677-693 - HTTP 403; abstract unread, not cited.

## Walleye notes

- Habitat claims: daytime depth vs turbidity (WDNR), spawning timing/temperature
  (WDNR; consistent with the spawning band already in the physiology file),
  spawning substrate and depth (Raabe & Bozek 2012, one Wisconsin lake - flagged
  as a single-lake result).
- Bait: WDNR names minnows first, then leeches, small bullheads, nightcrawlers
  and small plugs. Only the *what*, no how-to-use text - left as "not yet
  documented" rather than filled from unsourced angling lore.
- Wisconsin bait regulations for every item: NOT_YET_RESEARCHED (explicit in the
  catalog); a dedicated regulations pass (NR 19/20, live baitfish, invasives) is
  required before Fish Detail may show a bait as usable everywhere.
- Not yet documented: summer/winter structure, river habitat, lake-class fit.
