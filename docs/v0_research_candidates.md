# V0 Research: Candidate Predictors of Freshwater / Great Lakes Fish Catch Rate

Scope: southeastern Wisconsin inland lakes (e.g. Pewaukee, Delavan, Geneva, Winnebago) and
Wisconsin waters of Lake Michigan. Outcome variable is intended to be WDNR creel-survey-derived
catch rate (catch per unit effort). This document is research only — no data was pulled, no
modeling was performed.

## Summary

- **Total candidates identified: 19**
- **Have a real, specific, accessible WI/Lake Michigan data source for V0: 11**
- **No real accessible regional data source identified (log as "considered, not testable in V0"): 8**
- Confidence labels reflect the *predictor claim's* evidentiary basis, not the data-availability
  question, which is scored separately in the last column.
- Overall research-literature finding: barometric pressure and moon phase — the two most
  "folklore-famous" predictors — have the weakest/most contested scientific support of anything
  on this list. Water temperature, season/spawning timing, and turbidity have the strongest
  support. Wind and time-of-day have solid but effect-size-uncertain support.

---

## Candidate Predictors

### 1. Water temperature (absolute value / thermal regime)
- **Claimed effect:** Strong. Governs fish metabolism and activity; each species has a
  preferred/optimal range (e.g. largemouth bass peak aggression ~72–78°F; walleye peak ~60–65°F,
  cool-water optimum 55–68°F). Activity and catchability drop sharply outside these ranges.
- **Source:** Outdoor Canada (https://www.outdoorcanada.ca/to-catch-big-summer-walleye-bass-trout-or-pike-look-for-these-key-water-temperatures/); Bass Pro Shops 1Source (https://1source.basspro.com/news-tips/fishing-information/7724/why-water-temperature-plays-role-your-fishing-success); Hooked Ontario (https://www.hookedontario.ca/articles/water-temperature-ontario-fishing); general fisheries physiology literature.
- **Confidence:** Well-established (multiple independent agency/outfitter/scientific sources, consistent with basic fish thermal physiology).
- **WI/Lake Michigan data source:** YES. USGS Water Data for the Nation / NWIS real-time and historical water temperature gauges for WI lakes and rivers (https://waterdata.usgs.gov/wi/nwis/rt, API at https://api.waterdata.usgs.gov/ and https://waterservices.usgs.gov/) cover some WI lakes/rivers, though coverage of small inland lakes like Pewaukee/Delavan/Geneva specifically needs to be verified per-lake. WDNR Surface Water Data Viewer and Citizen Lake Monitoring Network (CLMN, via UWSP Extension Lakes, https://www3.uwsp.edu/cnr-ap/UWEXLakes/) also collect lake temperature via volunteer monitoring. For Lake Michigan, NOAA GLERL/NDBC buoys (see #14) report surface water temperature directly.

### 2. Ice-out date (as a season-start / phenology signal)
- **Claimed effect:** Marks onset of the open-water fishing season and is correlated with spring
  spawning timing and early-season catchability; used in academic climate-phenology studies of
  walleye (ice-off date correlated with modeled ice phenology, r=0.71, p<0.001, across 194 Midwest
  lakes).
- **Source:** Wisconsin State Climatology Office Madison Lake Ice Summary (https://climatology.nelson.wisc.edu/first-order-station-climate-data/madison-climate/lake-ice/madison-lake-ice-summary/); UWSP CLMN Ice-on Ice-off program (https://www3.uwsp.edu/cnr-ap/UWEXLakes/Pages/programs/clmn/ice.aspx); WDNR/academic walleye phenology study across 194 Midwest lakes (spring mark-recapture surveys, 1939–2019 per search results).
- **Confidence:** Well-established (long-running agency/university records, peer-reviewed phenology research).
- **WI/Lake Michigan data source:** YES, but regionally limited. The State Climatology Office's rigorous long-record ice-out data is specific to the three Madison lakes (Mendota, Monona, Wingra) — not southeastern WI directly. UWSP CLMN volunteer ice-on/ice-off records may cover some southeastern WI lakes depending on volunteer participation (needs per-lake check for Pewaukee/Delavan/Geneva/Winnebago). No single authoritative statewide ice-out database with full SE WI lake coverage was confirmed to exist; this needs verification in the dataset-build step.

### 3. Season / spawning window (species-specific regulation timing)
- **Claimed effect:** Strong, well-documented. Catchability spikes during pre-spawn staging and
  spawning runs (e.g. walleye spawn WI ~mid-April–early May at 42–50°F water temp); WDNR sets
  season closures/openers around these windows precisely because of catchability concerns during
  spawning aggregations.
- **Source:** WDNR Walleye species page (https://dnr.wisconsin.gov/topic/Fishing/species/walleye.html); WDNR fishing regulations (https://dnr.wisconsin.gov/sites/default/files/topic/NewRegs20242025.pdf); WDNR seasons page (https://dnr.wisconsin.gov/topic/Fishing/seasons/yearnd.html).
- **Confidence:** Well-established (agency regulatory basis, biological consensus).
- **WI/Lake Michigan data source:** YES. WDNR published regulation tables give exact season open/close dates by species/zone/waterbody, usable as a calendar-based feature. Combine with water temperature (via USGS/CLMN) as a spawning-window proxy.

### 4. Time of day (dawn/dusk crepuscular feeding)
- **Claimed effect:** Moderate-strong. Many species feed most actively at dawn/dusk (crepuscular
  behavior) due to low light favoring predator ambush and reduced angler pressure at those hours.
- **Source:** General crepuscular-feeding fisheries/ecology literature summarized via fishing-industry sites (White Fish Bay Camp, Fishing Streets) citing coral reef and other species studies (e.g. PMC study on reef predator/prey timing, https://pmc.ncbi.nlm.nih.gov/articles/PMC4213059/).
- **Confidence:** Well-established qualitatively (broad ecological consensus on crepuscular feeding), though quantitative freshwater-species effect sizes for WI species specifically were not found — treat magnitude as single-source/anecdotal even though direction is well supported.
- **WI/Lake Michigan data source:** YES (trivially). Time-of-day is derivable directly from creel survey interview timestamps or sunrise/sunset tables (NOAA/US Naval Observatory almanac data) — no external dataset needed beyond date/location.

### 5. Wind speed
- **Claimed effect:** Mixed but generally positive at moderate levels. One analysis of 40,000+
  bass catches found catch rates "more than double the norm" for winds >15 mph; other sources
  suggest an ideal window of 5–12 mph (enough to break up surface glare without hampering
  boat control), with reported ~31% more hookups in 10–15 mph vs. calm conditions. Mechanism:
  wind mixes/oxygenates water and disguises lures/anglers.
- **Source:** BassForecast (https://bassforecast.com/how-wind-direction-affect-bass-fishing, https://bassforecast.com/high-percentage-fishing-wind); Beyond Braid (https://beyondbraid.com/blogs/news/fishing-in-wind).
- **Confidence:** Single-source speculative for the specific numbers (angling-industry blog claims, not peer-reviewed); the general oxygenation/light-disruption mechanism is plausible and widely repeated but not independently verified.
- **WI/Lake Michigan data source:** YES. NOAA/NWS historical hourly wind speed and direction via api.weather.gov or NCEI Climate Data Online (https://www.ncei.noaa.gov/cdo-web/) for nearby ASOS/AWOS stations; for Lake Michigan itself, NDBC buoys (#14) report wind directly.

### 6. Wind direction
- **Claimed effect:** Claimed strong directional effect (e.g. "south/SW winds boost fishing
  scores +10 to +12; east/NE winds hurt -8 to -10" per one angling-analytics site), and the
  classic angler heuristic of fishing the shoreline the wind has been blowing into for
  several days (accumulates baitfish/plankton).
  "Wind from the east, fish bite least" is a widespread folk rule tied to this.
- **Source:** BassForecast (https://bassforecast.com/how-wind-direction-affect-bass-fishing); My Backyard Life (https://mybackyardlife.com/how-does-wind-direction-affect-fishing/); general angling folklore.
- **Confidence:** Single-source speculative — the specific numeric scores are from one angling-analytics blog with no disclosed methodology; treat as anecdotal/community consensus, not peer-reviewed.
- **WI/Lake Michigan data source:** YES for the raw wind-direction data (same NWS/NDBC sources as #5). NOT available as a ready-made "which shoreline" feature — would require lake-specific shoreline geometry cross-referenced with wind direction, which is buildable but not off-the-shelf.

### 7. Cloud cover / sky condition (sunny vs. overcast)
- **Claimed effect:** Contradictory across sources. Some claim fish are "30% more active" in
  cloudy conditions and catch rates rise up to 50% with the right technique; a different
  10,000-catch dataset found sunny/partly-sunny days outperformed overcast by ~20%. Likely
  species- and season-dependent (trout may prefer shade/security of clouds; other species prefer
  sun-driven insect/prey activity).
- **Source:** Guidesly (https://guidesly.com/fishing/blog/how-weather-affects-fishing-success); Fishing Hoosier (https://www.fishinghoosier.com/post/uncover-the-hidden-benefits-of-fishing-on-cloudy-and-overcast-days); Social Fishing AU (https://socialfishing.com.au/the-weather-effect-pt-2-cloud-cover/).
- **Confidence:** Single-source speculative — conflicting angler-blog claims with no consistent quantitative consensus; no peer-reviewed source found.
- **WI/Lake Michigan data source:** YES. NWS/NCEI hourly sky-condition (cloud cover fraction) is available via api.weather.gov and NCEI CDO for regional ASOS stations.

### 8. Precipitation / rain
- **Claimed effect:** Mixed, intensity-dependent. Light rain reportedly increases dissolved
  oxygen (claimed 15–30%) and stimulates insect/baitfish activity, boosting feeding; heavy rain
  causes turbidity/flooding/temperature swings that can suppress feeding ("lockjaw" in cold rain).
  Net effect is plausibly non-monotonic in rain intensity.
- **Source:** WindRider blog (https://windrider.com/blogs/tips-and-tricks/why-fish-bite-better-in-rain-science-backed-strategies); MeatEater fact-check (https://www.themeateater.com/fish/general/fact-checker-is-fishing-better-when-its-raining); general angling-media consensus.
- **Confidence:** Single-source speculative — quantitative claims (e.g. "15-30% DO increase") are unsourced blog assertions; qualitative direction is widely repeated but not peer-reviewed for freshwater WI species specifically.
- **WI/Lake Michigan data source:** YES. NWS/NCEI hourly/daily precipitation totals via api.weather.gov and NCEI CDO for regional stations near each lake.

### 9. Barometric pressure (absolute level)
- **Claimed effect:** Popular angler belief but scientifically unsupported as a direct causal
  driver. Multiple independent research reviews conclude no controlled study has demonstrated a
  direct pressure→catch-rate relationship, because pressure cannot be isolated from correlated
  weather changes (fronts, wind, cloud, temperature).
- **Source:** Active Angling NZ, "The Barometric Pressure Myth" (https://activeanglingnz.com/2019/10/13/the-barometric-pressure-myth/); In The Spread (https://inthespread.com/blog/barometric-pressure-saltwater-fishing-science-behind-the-bite-394); general review consensus across multiple angling-science summary sites.
- **Confidence:** Well-established *negative* finding — i.e., multiple independent sources agree there is no proven direct effect, which is itself the well-established conclusion. Popular belief in a strong effect should be treated as folklore, not established science.
- **WI/Lake Michigan data source:** YES for the raw data (NWS/NCEI hourly station pressure), but the underlying predictor claim is weak/unproven, so this is a case where data exists but the hypothesis itself is scientifically shaky. Worth testing in V0 specifically because it's testable and would settle a long-standing folk claim, but expect a null result.

### 10. Barometric pressure trend (rate of change / falling vs. rising vs. stable)
- **Claimed effect:** Distinct from absolute pressure — the trend/rate-of-change hypothesis has
  slightly more support: one documented exception is Gulf of Mexico yellowfin tuna showing
  significant catch correlation with rapid pressure drops (≥0.10 inHg per 3 hours). This is a
  saltwater pelagic-species finding, not freshwater, so its transferability to WI inland lakes is
  unverified.
- **Source:** In The Spread (https://inthespread.com/blog/barometric-pressure-saltwater-fishing-science-behind-the-bite-394), citing Gulf of Mexico tuna research.
- **Confidence:** Single-source speculative for freshwater/Great Lakes applicability — the one concrete positive finding is for an unrelated species/system (saltwater pelagic tuna); no freshwater bass/walleye/panfish study found supporting pressure-trend effects.
- **WI/Lake Michigan data source:** YES for raw data (NWS/NCEI hourly pressure allows trend computation), same caveat as #9 about weak underlying evidence for freshwater species.

### 11. Moon phase / solunar tables
- **Claimed effect:** Highly contested. Proponents (solunar theory, since 1926) claim major/minor
  lunar periods correlate with feeding windows; one cited analysis found 64% of fish caught during
  solunar periods that represent only 33% of total fishing time, and trophy fish at 71% during
  solunar windows. Countering this, University of Florida research on largemouth bass found zero
  statistical correlation between moon phase and catch rate for average-sized fish, and a
  peer-reviewed study found no significant relationship between CPUE and any solunar/lunar
  illumination value tested.
- **Source:** FishingBooker overview (https://fishingbooker.com/blog/solunar-fishing-calendars-fishing-by-moon-phases/); Springer article (https://link.springer.com/article/10.1007/s42452-023-05379-8); University of Florida bass research (cited via search summary, not independently verified original source URL).
- **Confidence:** Single-source speculative / actively contested — peer-reviewed freshwater bass research contradicts the popular claim; treat solunar effects as unproven for the species/lakes in this project's scope.
- **WI/Lake Michigan data source:** YES for raw data. Moon phase/illumination is fully deterministic and computable for any date/location (US Naval Observatory / astronomical algorithms) — no external dataset needed, trivial to compute. Testability is high even though the underlying effect is scientifically doubtful — good candidate to test and likely reject.

### 12. Water clarity / turbidity
- **Claimed effect:** Well-supported negative relationship for sight-feeding predators. Largemouth
  bass catch rates negatively correlated with turbidity (vision-based feeding impairment);
  consumption rates of prey decline with turbidity, though effect may be threshold-based (no
  significant decline until ~70 NTU in one lab study). Walleye reaction distance for prey declines
  more with organic (algal) turbidity than inorganic (sediment) turbidity. Effect also alters
  optimal lure color, a secondary effect not directly relevant to catch-rate modeling.
- **Source:** ScienceDirect walleye/turbidity/lure-color study (https://www.sciencedirect.com/science/article/pii/S0380133020300496); NRC Research Press largemouth bass piscivory/turbidity study (https://cdnsciencepub.com/doi/10.1139/f99-056); Mississippi State thesis (https://scholarsjunction.msstate.edu/td/2723/); CJFAS Great Lakes water clarity review (https://cdnsciencepub.com/doi/10.1139/cjfas-2020-0376).
- **Confidence:** Well-established (multiple independent peer-reviewed studies, consistent direction).
- **WI/Lake Michigan data source:** PARTIAL/UNCERTAIN for inland lakes. WDNR/UWSP Citizen Lake Monitoring Network (CLMN) collects Secchi disk transparency readings for many WI lakes including likely candidates like Pewaukee, Delavan, Geneva, Winnebago via WDNR's Surface Water Data Viewer and the CLMN volunteer program — but frequency/coverage per lake needs per-lake verification (data is typically only every 1-2 weeks in season, from volunteers, not continuous). For Lake Michigan, NOAA CoastWatch/GLERL satellite-derived turbidity/chlorophyll products exist for the open lake but are less directly applicable to nearshore recreational fishing turbidity. Log as testable-with-caveats: real source exists but sparse/volunteer-quality.

### 13. Dissolved oxygen (DO)
- **Claimed effect:** Well-documented physiological threshold effect: warmwater species (bass,
  bluegill, walleye, perch) function well above ~5 mg/L DO; walleye tolerate down to ~2 mg/L;
  activity/behavior is impaired below species-specific hypoxia thresholds, which can create summer
  thermocline "dead zones" that concentrate fish in oxygenated layers.
- **Source:** ResearchGate review "Effects of dissolved oxygen concentration on freshwater fish: A review" (https://www.researchgate.net/publication/362634321); Fondriest Environmental (https://www.fondriest.com/environmental-measurements/parameters/water-quality/dissolved-oxygen/); Active Angling NZ (https://activeanglingnz.com/2017/02/23/the-importance-of-dissolved-oxygen/).
- **Confidence:** Well-established for the physiology (peer-reviewed review); the search did not surface a study directly linking DO to *catch rate* (as opposed to fish behavior/survival), so the leap from "DO affects fish activity/location" to "DO affects angler catch rate" is a reasonable but not directly evidenced inference.
- **WI/Lake Michigan data source:** NO reliable continuous source identified for southeastern WI inland lakes specifically. WDNR/CLMN collects some DO profile data on a subset of monitored lakes (volunteer, infrequent, depth-profile snapshots), but there is no continuous, broadly-available DO time series comparable to USGS water-temperature gauges. Log as "considered, not testable in V0" absent per-lake verification finding usable CLMN DO records with adequate temporal coverage.

### 14. Great Lakes wave height (Lake Michigan only)
- **Claimed effect:** Plausible but not independently verified in this research pass — wave
  height affects boat/shore fishing safety and access, water mixing/turbidity nearshore, and by
  analogy to the wind-speed findings (#5) likely affects catchability similarly (moderate wave
  action favorable, large waves suppress effort/access rather than fish activity per se).
- **Source:** No direct freshwater/Lake Michigan wave-height-vs-catch-rate study found in this pass; inferred from wind-speed literature (#5) plus general boating/safety commentary.
- **Confidence:** Single-source speculative / inferred, not directly evidenced.
- **WI/Lake Michigan data source:** YES — strong. NOAA National Data Buoy Center (NDBC) buoys 45007 (South Michigan, ~43 nm ESE of Milwaukee) and 45002, plus C-MAN station MLWW3 at the Port of Milwaukee (https://www.ndbc.noaa.gov/station_page.php?station=mlww3, https://www.ndbc.noaa.gov/station_page.php?station=45007) report real-time and historical wave height, wind, and other marine conditions. Note buoys are removed for winter (seasonal coverage gap, e.g. 45007 recovered 12/8/25).

### 15. Great Lakes water level (Lake Michigan only)
- **Claimed effect:** Plausible effect on nearshore habitat access, spawning habitat availability,
  and pier/shore fishing conditions; long-term water level cycles are known to affect Great Lakes
  fish habitat structure generally, but a direct short-term water-level-vs-catch-rate study was
  not found in this pass.
- **Source:** General GLERL/USGS commentary on Great Lakes water level monitoring (https://www.usgs.gov/media/images/milwaukee-water-level-gages-power-spectral-density-noaa-station-9087057-milwaukee); no direct catch-rate study identified.
- **Confidence:** Single-source speculative / inferred.
- **WI/Lake Michigan data source:** YES — strong. NOAA CO-OPS station 9087057 (Milwaukee) provides historical and real-time water level data (https://tidesandcurrents.noaa.gov/stationhome.html?id=9087057, referenced via USGS commentary). This is a specific, accessible, long-running gauge suitable for V0.

### 16. Fishing pressure / angler effort
- **Claimed effect:** Plausible negative or confounding relationship with catch rate — higher
  effort can reflect reporting/selection bias (more effort where fish are known to bite) or can
  depress catch rate through fish becoming wary/depleted locally. Academic literature treats
  angler effort as both a predictor and a confound requiring careful handling (e.g. lagged catch
  rates predicting future effort, not just the reverse).
- **Source:** Auburn University creel-methods thesis (https://etd.auburn.edu/handle/10415/7074); arXiv Bayesian-network angler-pressure paper (https://arxiv.org/abs/2402.07964); ScienceDirect angling-behavior modeling paper (https://www.sciencedirect.com/science/article/abs/pii/S0165783622000121).
- **Confidence:** Well-established as a methodologically important variable in fisheries science (multiple peer-reviewed sources), though the specific direction/magnitude for SE WI lakes is unknown and effort/catch-rate are jointly determined (potential endogeneity — a real modeling risk to flag for step 4).
- **WI/Lake Michigan data source:** YES, via the outcome dataset itself. WDNR creel survey reports (https://dnr.wisconsin.gov/topic/Fishing/reports) already report angler-hours/effort alongside catch statistics for surveyed WI waters, since effort is a standard creel-survey output. This is not an independent external predictor so much as a companion variable already embedded in the same data source used for the outcome — flag for step 4 as a potential leakage/endogeneity concern rather than a clean independent predictor.

### 17. Fish stocking history
- **Claimed effect:** Plausible positive effect on catch rate in the stocked species/year-classes
  following a stocking event, especially for species that are stocking-dependent in a given
  waterbody (e.g. walleye, muskellunge, trout in many WI lakes).
- **Source:** General fisheries management logic; WDNR stocking guideline reference found during search (streams not stocked below 75 angler-hours/acre pressure) indicates WDNR explicitly ties stocking decisions to effort/catch expectations.
- **Confidence:** Well-established as fisheries management logic (agency practice reflects assumed effect), though a direct peer-reviewed stocking-event-to-CPUE-lift study for these specific SE WI lakes was not retrieved in this pass.
- **WI/Lake Michigan data source:** YES. WDNR Fisheries Management Information System / Fish Stocking database (https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/Index) provides stocking year, species, strain, age class, and number stocked per waterbody from 1972(/1953)-present — directly queryable per lake.

### 18. Lake-specific bathymetry / structure (depth contours, drop-offs, points)
- **Claimed effect:** Strong angler consensus that fish concentrate near structure (drop-offs,
  points, weed edges) rather than being effect-uniform across a lake; this is a spatial-location
  predictor rather than a temporal one and would require per-lake spatial data, not a simple
  time-series feature.
- **Source:** General bass-fishing/structure-fishing guides (https://bassonline.com/understanding-lake-structure-for-bass-fishing-a-pro-guides-masterclass-2026/, https://deepersonar.com/global/all/blog/how-to-find-good-fishing-spot-in-open-waters-using-bathymetry); no peer-reviewed source found.
- **Confidence:** Single-source speculative from a data/statistics standpoint (widely believed, angler-consensus, but not independently quantified in scientific literature found here) — though the ecological logic (predator-cover association) is standard fisheries biology.
- **WI/Lake Michigan data source:** PARTIAL. WDNR does publish bathymetric lake maps for many WI lakes (via WDNR Surface Water Data Viewer / lake maps), so contour data exists, but it is static (not a time-varying predictor) and would only be usable as a spatial covariate if the outcome data (creel survey) is spatially resolved within a lake — WDNR creel surveys are typically whole-lake aggregates, not location-specific. Log as "considered, not testable in V0" for a whole-lake CPUE outcome; would only become usable if outcome data had finer spatial resolution.

### 19. Air temperature / short-term weather-front passage (cold front vs. stable warm pattern)
- **Claimed effect:** Widely believed among anglers that a passing cold front (rapid air-temp
  drop + pressure change + wind shift) suppresses catch rate for 1-3 days ("post-frontal
  lockjaw"), while stable warm weather sustains good catch rates. This overlaps conceptually with
  #9/#10 (pressure) and #5/#6 (wind) but is often described by anglers as a distinct composite
  "front passage" effect.
- **Source:** General angling-media consensus (e.g. Mercury Marine, Mossy Oak barometric-pressure articles reference front passage as the real driver behind the pressure folklore: https://www.mercurymarine.com/us/en/lifestyle/dockline/how-barometric-pressure-affects-fishing, https://www.mossyoak.com/our-obsession/blogs/the-fishing-and-barometric-pressure-relationship).
- **Confidence:** Single-source speculative — this is essentially the "indirect effects" reframing of the pressure myth (see #9): several sources suggest front passage as a whole (not pressure per se) is the real signal, but no controlled freshwater study isolating front-passage effects was found.
- **WI/Lake Michigan data source:** YES. NWS/NCEI hourly air temperature, pressure, and wind together (same sources as #5/#8/#9) allow constructing a composite "front passage" feature (e.g. 24h temp drop + pressure drop + wind shift) — fully buildable from existing accessible data.

---

## Predictors considered but explicitly NOT testable in V0 (no real accessible regional data source)

| # | Predictor | Why not testable |
|---|-----------|-------------------|
| 13 | Dissolved oxygen (inland lakes) | No continuous/reliable DO time series identified for SE WI inland lakes; only sparse volunteer CLMN snapshots at best. |
| 18 | Lake-specific bathymetry/structure | Static spatial data exists (WDNR lake maps) but WDNR creel survey outcome data is whole-lake aggregate, not location-resolved, so structure can't be linked to catch-rate variation in V0. |
| 6 | Wind direction → "which shoreline" effect | Raw wind direction data exists, but the specific claimed mechanism (shoreline accumulation effect) requires lake-specific shoreline geometry modeling not available as an off-the-shelf dataset. |
| 12 | Water clarity/turbidity (inland lakes) | Real source exists (WDNR/CLMN Secchi readings) but is volunteer-collected, infrequent (roughly biweekly in-season), and coverage per specific lake (Pewaukee/Delavan/Geneva/Winnebago) is unverified — flag as high-risk/likely-insufficient rather than outright excluded; needs per-lake confirmation in step 2. |
| 2 | Ice-out date (SE WI specifically) | Rigorous long-record ice-out data confirmed only for Madison-area lakes (Mendota/Monona/Wingra) via WI State Climatology Office; SE WI lake coverage depends on CLMN volunteer participation, unverified per lake. |
| 15 | Great Lakes water level → habitat/access effect | Raw water level data exists (NOAA CO-OPS Milwaukee), but no direct catch-rate study or established effect size was found — data exists, hypothesis itself is unverified/speculative (kept in main list as testable-data/speculative-hypothesis, listed here as a caution flag, not a hard exclusion). |
| 14 | Great Lakes wave height → catch effect | Same situation as #15: real data exists, but the causal claim is inferred by analogy rather than directly evidenced. |
| 10 | Barometric pressure trend (freshwater) | Data is available, but the one supporting finding is from an unrelated species/system (saltwater tuna), so applicability to WI freshwater species is unverified. |

Note: several rows above have data available but a weak/unverified underlying causal claim; they
are listed here as cautions for step 3/4 to weigh, not as a statement that the raw data itself is
inaccessible. Only DO (#13), bathymetry-as-time-varying (#18), and wind-direction-shoreline (#6)
are true "no accessible data source" exclusions; the rest are "data exists, hypothesis is weak"
cases that should be down-weighted but can still be tested cheaply since the raw inputs already
exist.

---

## Key regional data sources identified (for step 2 dataset build)

- **WDNR creel survey / fisheries survey reports** (outcome data): https://dnr.wisconsin.gov/topic/Fishing/reports
- **USGS Water Data for the Nation / NWIS** (water temp, some flow/level): https://waterdata.usgs.gov/wi/nwis/rt, API at https://api.waterdata.usgs.gov/
- **WDNR/UWSP Citizen Lake Monitoring Network (CLMN)** (Secchi clarity, ice-on/off, some DO): https://www3.uwsp.edu/cnr-ap/UWEXLakes/
- **WDNR Fish Stocking database**: https://apps.dnr.wi.gov/fisheriesmanagement/Public/Summary/Index
- **WDNR fishing regulations / season dates**: https://dnr.wisconsin.gov/topic/Fishing/seasons/yearnd.html
- **Wisconsin State Climatology Office** (Madison-lakes ice records, other climate data): https://climatology.nelson.wisc.edu/
- **NOAA NCEI Climate Data Online (CDO)** (historical hourly/daily weather incl. pressure, wind, precip, cloud cover, temp): https://www.ncei.noaa.gov/cdo-web/
- **NWS api.weather.gov** (weather station observations/forecasts): https://www.weather.gov/documentation/services-web-api
- **NOAA NDBC buoys** (Lake Michigan wave height, wind, water temp): station 45007, 45002, C-MAN MLWW3 — https://www.ndbc.noaa.gov/
- **NOAA CO-OPS** (Lake Michigan water level, Milwaukee station 9087057): https://tidesandcurrents.noaa.gov/
- Moon phase / sunrise-sunset: computable directly from astronomical algorithms — no external dataset required.

---

## Research limitations of this pass

- Web search results are dominated by angling-industry blogs and forums rather than peer-reviewed
  literature; several "well-established" labels rest on repeated-but-unsourced claims across
  multiple such blogs rather than true independent scientific replication. Where a peer-reviewed
  or agency-primary source was found, it is cited specifically above.
- No direct freshwater/Great Lakes catch-rate study was found for wave height or water level
  (Lake Michigan candidates #14/#15) — these are inferred from adjacent literature (wind-speed
  findings, general Great Lakes habitat commentary), not directly evidenced.
- Per-lake data coverage (especially CLMN Secchi/DO/ice records and USGS temperature gauges for
  Pewaukee, Delavan, Geneva, and Winnebago specifically) was not individually verified in this
  research pass and must be confirmed lake-by-lake during the step-2 dataset build.
- This document does not constitute, and should not be read as, a determination of which
  predictors will show real statistical signal — that determination is reserved for step 4
  (evaluation against baseline) per the pipeline instructions.
