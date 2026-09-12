# Roadmap

**CURRENT ACTIVE PHASE: V1 — Fishing Forecast**

Later phases (V2-V4) are inactive until V1 is sufficiently developed and reviewed.

## V0 — Prediction Feasibility

Establish whether public observations and environmental data support a validated fishing-conditions prediction.

**Status: Complete.** See [DECISIONS.md](DECISIONS.md) entries #001-#009 for
the full decision trail. *(Note: this roadmap was asked to cite
`docs/v0_final_conclusion_report.md` as the conclusion document — no file
under that name exists in this repo. The four reports below, together, are
V0's actual documented conclusion; flagging this discrepancy here rather
than inventing or silently retitling a file.)*

**Conclusion: general catch-rate prediction is not demonstrated with
currently available public data.** One narrow statistical signal was found
(wave height vs. Lake Michigan yellow perch harvest rate, r=0.865, p=0.001)
but is based on a single small sample (n=10) and is **not carried forward
into V1** as a feature — noted here as a research finding only, not a
product claim. V0 is **closed — not reopened by later phases**:

- [docs/V0_FEASIBILITY_REPORT.md](docs/V0_FEASIBILITY_REPORT.md) — Lake
  Michigan / inland-lake catch-rate feasibility (the core V0 pilot,
  DECISIONS.md #007)
- [docs/v0_lake_transfer_report.md](docs/v0_lake_transfer_report.md) —
  statewide inland-lake search + cross-lake predictor transfer test
  (DECISIONS.md #008)
- [docs/v0_inland_predictability_results.md](docs/v0_inland_predictability_results.md) —
  pooled inland-lake weather/characteristics predictability test
- [docs/v0_physiology_predictors_report.md](docs/v0_physiology_predictors_report.md) —
  established fish physiology/behavior as a candidate-predictor class
  (DECISIONS.md #009)

## V1 — Fishing Forecast

Location + species + date/time → forecast. Per DECISIONS.md #010-#012, this
phase pivoted away from GLATOS telemetry (deferred, see #011) to a
**conditions & biology narrative**: real current water temperature +
established fish physiology + real species-presence data, combined into a
per-waterbody output labeled clearly as **general biology-based seasonal
context — never a validated catch-rate prediction.**

Per DECISIONS.md #013/#014, coverage expanded from a single-lake demo to
lakes, ponds, rivers, and streams statewide — every waterbody in the real
WDNR stocking pull (~2,338, including 690 streams/rivers) surfaces a
stocking-only result, a growing set of lakes has real survey-confirmed
data, and a real 185-site USGS network provides live water temperature
(the primary real-time source for streams specifically).

**Status: In progress.** See [DECISIONS.md](DECISIONS.md) #010-#014 and
[CLAUDE.md](CLAUDE.md) for current scope; `analysis/v1_conditions_biology_forecast.py`
for the working implementation (supersedes the earlier `mvp/` script).

## V2 — Where Should I Fish?

Maps, water bodies, access points, habitat, and environmental intelligence.

**Status: First slice complete.** Shipped and polished: a statewide
access-point map (`analysis/v2_access_points.py`, `/map` in the web app)
showing 3,272 real Wisconsin public boat access and shore fishing sites,
pulled live from WDNR's own ArcGIS service, linked to an existing V1
waterbody detail page wherever a confident name/county match exists,
clustered for performance, with search-to-zoom on filter — plus an
optional, off-by-default layer of 557 real, WDNR-verified aquatic
invasive species sightings (`analysis/v2_invasive_species.py`) across 6
commonly-tracked species. Shore-fishing sites are further enriched with
real per-site data scraped live from WDNR's own detail pages
(`analysis/v2_shore_fishing_details.py`) — available fish species,
directions, amenities, ADA accessibility — filling the species-data gap
for sites outside V1's waterbody universe. The map now has a species
filter spanning both real data sources — deduplicated via
[`analysis/v2_species_canonicalization.py`](analysis/v2_species_canonicalization.py),
which collapses 61 real raw WDNR species phrases into 39 real distinct
species without altering the raw text shown on the site — and a
toggleable list view showing the same "one-stop-shop" per-site detail
as the map's popups. Every V1 species prediction that isn't currently a
match now explains why not (`describe_threshold_gap()`), and Lake
Michigan's 10 real waterbody entries resolve to a live NOAA NDBC buoy
water-temperature reading instead of an air-temperature proxy.
Full account: [docs/v2_access_points_report.md](docs/v2_access_points_report.md);
decisions: [DECISIONS.md](DECISIONS.md) #016-#020.

Real per-lake size/depth data was investigated **twice**, independently
(name-based matching, then a spatial point-in-polygon join), and
deliberately closed out both times — WDNR's available hydrography layer
fragments complex shorelines into many small polygons, so neither
approach reliably identifies "the lake" without a materially larger
curation effort than this slice's scope justifies. Not pursuing a third
attempt at the same source was itself the disciplined call, not a gap.

Broader "habitat scoring" and open-ended "environmental intelligence"
(e.g. weather overlays) remain future, uncommitted V2 extensions — real
possibilities, not yet scoped or started, and not required for this
slice to count as done.

**Second slice, planned (Decision #021)**: a CEO-directed deepening of
this same "Where Should I Fish?" scope into a real spot-level fishing
intelligence platform — click a spot on the map, get water temperature
(real, honestly estimated, or honestly unavailable), likely species and
why, and bait/technique recommendations with real citations. Full plan:
[docs/v2_fish_intelligence_platform_plan.md](docs/v2_fish_intelligence_platform_plan.md).
**Status: planned, build starting.**

## V3 — Continuous Validation

Fishing-trip logging, catch observations, weather attachment, and
prediction-vs-outcome evaluation — the intended future path to real
user-generated ground truth, which V0 found the project currently lacks
(WDNR creel data proved too coarse and too sparse for most Wisconsin
lakes — see the V0 reports above).

**Status: Not started.**

## V4 — Personal Fishing Intelligence

Personalized recommendations based on individual fishing history.

**Status: Not started.**
