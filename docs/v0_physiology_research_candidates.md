# V0 Physiology/Behavior Predictor Research Candidates (Decision #009, Step 1)

Research pass for Decision #009: testing established fish physiology/behavior
science (not weather, not lake geometry) as a candidate-predictor class
against the project's real outcome data. This document is **research only**
— nothing here has been validated against outcome data. That is step 2
(predictor-eval), done by a separate agent. No code was written or run to
produce this file.

## Method and scope

Searched peer-reviewed fisheries journals, agency technical reports
(Ontario MNR, Great Lakes Fishery Commission, WDNR), and university
extension fact sheets citing primary literature, for quantifiable
physiology/behavior relationships in the species actually present in the
project's outcome data. Checked `data/v0/*_creel_*.csv`,
`lake_michigan_creel_*`, and `lake_characteristics.csv` for the real
species list and data granularity before scoring "computable."

**Species confirmed in outcome data:**
- Lake Michigan (`lake_michigan_creel_harvest_rate_annual_by_species.csv`,
  `lake_michigan_creel_monthly_by_species_2022_2024.csv`): salmonids
  (Coho Salmon, "All salmonids combined" — Chinook/Lake Trout/Brown
  Trout/Rainbow Trout referenced in category text), Yellow Perch,
  Walleye mentioned in some monthly data.
- 11 inland lakes (`*_creel_*.csv`): Walleye, Yellow Perch, Largemouth
  Bass, Smallmouth Bass, Northern Pike, Muskellunge, Black Crappie,
  White Crappie, Bluegill, Brown Trout (Devils Lake), Lake Trout, Rainbow
  Trout, Sauger, Cisco, Burbot, and several catfish/carp/rough-fish
  species not covered here as they have essentially no established
  angling-physiology literature and are not primary targets.

**Data granularity constraint that affects "computable" scoring below:**
inland-lake creel records are one row per species per multi-month/
multi-year creel *season* (e.g. "2023-24", "Jul 2022-Jun 2023") — there is
no daily or trip-level timestamp. Lake Michigan monthly data is one row
per species per ~1-2 month period (e.g. "March/April", "May"), still not
daily. This means diel (day/night) and dawn/dusk-light-window predictors,
however well-evidenced physiologically, **cannot be computed against this
project's outcome data at its current temporal resolution** — there is no
trip-level catch record to attach a light-condition value to. Seasonal/
seasonal-average temperature and spawn-timing predictors remain computable
at the existing monthly/seasonal resolution. This is flagged per-candidate
below rather than used to exclude candidates outright, since the outcome
data's resolution could in principle be a separate limitation from the
predictor's validity.

**Water temperature data availability:** Lake Michigan has real daily water
temperature (WTMP) from the NDBC 45007 buoy (`lake_michigan_ndbc_45007_daily.csv`).
Inland lakes have **no water temperature data** in `data/v0/` — only air
temperature (TMAX/TMIN, tenths of °C, GHCN daily format) from nearby
COOP/USW stations. Any inland-lake predictor requiring water temperature
would need water temp estimated/modeled from air temperature and day-of-year
(a real but nontrivial extra step, and a source of additional error) or
would need new data acquisition; this is flagged per candidate.

---

## Summary

- **Total candidates recorded: 17** (16 physiology/behavior claims + 1
  explicitly-tested-and-excluded folklore claim, barometric pressure,
  included only to document that it was checked and does not meet this
  cycle's evidentiary bar)
- **Quantifiable/computable in principle from data this project can
  obtain or derive: 12**
  - Directly computable now (data already in `data/v0/`, at least for
    Lake Michigan): 5 (temperature-window candidates for LM species using
    NDBC WTMP)
  - Computable only after new data acquisition or derivation (inland water
    temp estimation, or spawn-date/ice-out lookup): 7
- **Not computable against this project's outcome data at its current
  temporal resolution** (diel/light-window predictors — real science, but
  no trip-level timestamp exists in the creel data to test them against): 4
- **Excluded — does not meet this cycle's evidentiary bar** (folklore /
  no primary scientific source / consensus is "no effect"): 1 (barometric
  pressure)

Species covered: Walleye, Yellow Perch, Largemouth Bass, Smallmouth Bass,
Northern Pike, Muskellunge, Black Crappie, Bluegill, Chinook Salmon, Coho
Salmon, Brown Trout, Lake Trout.

Notable finding: evidence quality is uneven. Species-specific optimal/
final-preferendum temperature values are well supported by primary
literature and agency compilations (Ryder 1977 for walleye light response;
Wismer & Christie 1987 / GLFC Sp87-3 as a cross-species compiled agency
source; Hasnain, Minns & Shuter 2010, Ontario MNR CCRR-17, as a
peer-reviewed cross-species compilation). Diel/light-window feeding
behavior is arguably the *most* rigorously evidenced physiological
mechanism found (walleye scotopic vision, Ryder 1977 CPUE-vs-illuminance
curve) but is the *least* usable here, purely because the outcome data
has no sub-daily timestamp. Barometric pressure — a very common angling
folklore claim — was explicitly checked and found to have no primary
scientific support; multiple sources state controlled studies have found
no consistent relationship, so it is excluded per this cycle's rule
against angling folklore.

---

## Candidate list

### 1. Walleye — feeding activity peaks near dusk/dawn low-light conditions (dawn/dusk illuminance ~300 lux)
- **Species:** Walleye
- **Claim:** Walleye catch-per-unit-effort (CPUE) rises as surface illuminance
  drops from ~32,000 lux toward ~100 lux, peaking at approximately 300 lux
  (i.e., the dusk/dawn twilight window), then falls off further into
  darkness. Mechanistically explained by walleye's tapetum lucidum and
  scotopic (low-light) visual adaptation, which gives them a foraging
  advantage over prey at low light.
- **Strength of evidence:** Field study (Ryder 1977, angling CPUE vs.
  measured illuminance) + supporting lab/physiological studies on walleye
  scotopic visual sensitivity (2024-2025 papers). Strong, specific,
  frequently-cited primary literature.
- **Source citations:**
  - Ryder, R.A. 1977. "Effects of ambient light variations on behavior of
    yearling, subadult, and adult walleyes (Stizostedion vitreum
    vitreum)." J. Fish. Res. Board Can. 34(10):1481-1491 (cited via
    https://academic.oup.com/tafs/article/133/3/588/7888567 and
    https://peerj.com/articles/21156/)
  - Evaluating the scotopic visual sensitivity of walleye — PeerJ/PMC:
    https://peerj.com/articles/21156/ ,
    https://pmc.ncbi.nlm.nih.gov/articles/PMC13135330/
  - Visual sensitivity, foraging behavior, and success of walleye under
    ecologically relevant downwelling light — Env. Biol. Fishes (2024):
    https://link.springer.com/article/10.1007/s10641-024-01650-y
- **Quantifiable/computable:** Quantifiable, yes (specific lux value, and
  sun-angle/twilight timing is exactly computable from date+lat/lon with
  no new data). **Computable against this project's outcome data: NO** —
  all Walleye records in `data/v0/*_creel_*.csv` are seasonal aggregates
  with no trip-level timestamp; there is no sub-daily catch record to
  attach a light-condition value to. Flagged as real science, not usable
  at current data resolution.

### 2. Walleye — reduced/selective feeding below ~50°F (10°C), broad activity range ~55-75°F, preference cluster ~62-68°F
- **Species:** Walleye
- **Claim:** Walleye tolerate water down to ~35°F but feed less often and
  more selectively below ~50°F (10°C); general activity/feeding range is
  roughly 55-75°F, with a preference cluster around 62-68°F (16-20°C) and
  telemetry-documented "optimum" habitat band of 18-23°C (64-73°F) when
  combined with dissolved oxygen >5 mg/L.
- **Strength of evidence:** Field telemetry study (habitat-compression /
  suitable-vs-optimum-habitat study) + secondary agency/extension
  synthesis. Field telemetry study is solid; the specific °F cluster
  numbers come from a mix of primary field study and downstream
  fishing-oriented syntheses, so treat the general band as well-evidenced
  but the precise boundary numbers as approximate.
- **Source citations:**
  - "The influence of thermal and hypoxia induced habitat compression on
    walleye (Sander vitreus) movements in a temperate lake" — PMC:
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11707865/
  - Hasnain, Minns & Shuter 2010, Ontario MNR CCRR-17, "Key Ecological
    Temperature Metrics for Canadian Freshwater Fishes" (cross-species
    compiled optimal growth temp / final temperature preferendum values;
    PDF not directly retrievable during this pass, cited via secondary
    academic references, e.g.
    https://cdnsciencepub.com/doi/10.1139/cjfas-2012-0217 — should be
    re-sourced directly in step 2 if this candidate is tested)
- **Quantifiable/computable:** Quantifiable, yes (numeric °F/°C bands).
  **Computable for Lake Michigan: YES** — NDBC WTMP daily data exists and
  Walleye appears in some LM monthly records; average WTMP over a
  reporting period could be compared to the preferred band.
  **Computable for inland lakes: only with new water-temp data/estimation**
  — no water temp column exists in inland `data/v0/` files; would require
  either acquiring gauge/DNR water-temp records or modeling water temp
  from the existing air-temp weather files (approximate, added error).

### 3. Walleye — spawning triggered at water temperature ~40-52°F, peak spawn ~44-48°F
- **Species:** Walleye
- **Claim:** Walleye spawning begins around 40°F, with peak spawning
  activity commonly cited at 44-48°F (some sources cite peak 48-54°F);
  photoperiod (day length) is a co-trigger alongside temperature.
- **Strength of evidence:** Widely repeated in agency/extension material
  and secondary literature; the temperature-trigger relationship itself
  is well-established biology, though the precise °F window varies
  somewhat by source/region (a range of 40-54°F appears across sources,
  suggesting real regional variability rather than a single fixed
  threshold).
- **Source citations:**
  - North Dakota Game and Fish, "A Look Back": https://gf.nd.gov/magazine/2016/may/look-back
  - Multiple extension/agency-adjacent sources converge on the 40-54°F
    window; treat as agency/extension-tier evidence, not primary field
    study, for this specific numeric range.
- **Quantifiable/computable:** Quantifiable (numeric threshold), yes.
  **Computable:** requires knowing the date water temperature first/
  consistently crosses the trigger band each spring — computable for Lake
  Michigan (NDBC WTMP exists) at the monthly resolution of the LM data
  (would test "was the spawn-window month's average temp within/near the
  trigger band"); for inland lakes only with water-temp
  estimation/acquisition as above. Because outcome data is seasonal, not
  daily, this becomes a coarse "was spawn-season temperature in range"
  predictor rather than a fine-grained one.

### 4. Yellow Perch — optimal temperature ~23-24°C (73-75°F)
- **Species:** Yellow Perch
- **Claim:** Yellow perch optimal temperature (for growth/physiological
  performance) is approximately 23-24°C.
- **Strength of evidence:** Peer-reviewed aquaculture/physiology
  literature (growth-performance studies), though these are
  growth-optimum studies (partly aquaculture-context), not wild-population
  catchability field studies — a meaningful evidentiary gap between
  "optimal for growth" and "optimal for catchability."
  Also cross-referenced against Ontario MNR / GLFC-style compiled thermal
  preferenda for wild populations.
- **Source citations:**
  - "Optimal Feeding Rates for Growth Performance... Fingerling Yellow
    Perch" — PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12108393/
  - "The Preferred Temperature of Fish and their Midsummer Distribution
    in Temperate Lakes and Streams" (cited via ResearchGate):
    https://www.researchgate.net/publication/237176917_The_Preferred_Temperature_of_Fish_and_their_Midsummer_Distribution_in_Temperate_Lakes_and_Streams
- **Quantifiable/computable:** Quantifiable, yes. **Computable:** Lake
  Michigan — yes, via NDBC WTMP, at monthly resolution (Yellow Perch is
  in the LM harvest-rate data). Inland lakes — only with water-temp
  estimation/acquisition. Flag: growth-optimum temperature is not
  necessarily the same as catchability-optimum temperature; this should
  be tested as "distance from growth-optimum," acknowledging it is an
  indirect proxy, not a direct catchability study.

### 5. Largemouth Bass — thermal optimum for growth ~25-29°C (77-84°F); higher feeding rates at lower temps in some studies
- **Species:** Largemouth Bass
- **Claim:** Largemouth bass thermal optima for growth are commonly cited
  at 25-28°C (77-82°F), with optimum growth in juveniles at 25°C in some
  studies; however, one controlled study found *higher* maximum feeding
  rates at 18°C than at higher temperatures, and handling time increased
  with temperature — so "warmer = more feeding" is not uniformly
  supported even within the primary literature.
- **Strength of evidence:** Mixed — some findings from controlled lab/
  aquaculture growth studies (moderate rigor, some aquaculture-context
  caveats), one specific feeding-rate-vs-temperature lab study
  (Springer/Env. Biol. Fishes — reasonably rigorous, direct feeding-rate
  measurement).
- **Source citations:**
  - "Temperature regime drives differential predatory performance in
    Largemouth Bass and Florida Bass" — Env. Biol. Fishes:
    https://link.springer.com/article/10.1007/s10641-019-00933-z
  - "Effects of Different Feeding Regimes on Growth Rates... at High
    Water Temperatures" — PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9597755/
- **Quantifiable/computable:** Quantifiable (numeric °C optima), yes, but
  flagged as **conflicting evidence within the primary literature itself**
  — growth-optimum and feeding-rate-optimum diverge, so any predictor
  built on this should be tested as two separate hypotheses (distance
  from growth-optimum vs. distance from feeding-rate optimum), not
  merged. **Computable:** inland lakes only, with water-temp
  estimation/acquisition (Largemouth Bass is not in LM data).

### 6. Smallmouth Bass — thermal preference ~22-25°C (72-77°F); avoids water above/below this in behavioral thermoregulation study
- **Species:** Smallmouth Bass
- **Claim:** Smallmouth bass show a thermal preference around 22°C
  (bioenergetic growth optimum) to 25°C (behavioral preference), and in a
  Lake Michigan harbor field study actively avoided both warmer
  in-harbor water and colder open-lake water in favor of habitat near
  22°C. Spawning occurs near 59-64°F (15-18°C), notably cooler than
  largemouth bass spawning temperature.
- **Strength of evidence:** Field telemetry/behavioral study specifically
  in Lake Michigan (directly relevant water body) + bioenergetic modeling
  study. Comparatively strong — field-validated in the exact system this
  project covers.
- **Source citations:**
  - "Movement patterns of smallmouth and largemouth bass in and around a
    Lake Michigan harbor: The importance of water temperature" —
    ScienceDirect: https://www.sciencedirect.com/science/article/abs/pii/S038013301200038X
  - "Behavioral and physiological responses of Smallmouth Bass to a
    dynamic thermal environment": https://www.researchgate.net/publication/287679437
- **Quantifiable/computable:** Quantifiable, yes. **Computable:** inland
  lakes only (Smallmouth Bass appears in `data/v0` inland creel files,
  not confirmed in LM species list checked), requires water-temp
  estimation/acquisition since no inland water-temp data exists yet.

### 7. Northern Pike — activity/feeding optimum ~55-65°F (13-18°C); physiological optimum ~19-21°C (66-70°F); avoidance above ~75°F; upper lethal ~29.4°C
- **Species:** Northern Pike
- **Claim:** Peak pike activity is generally 55-65°F, with a
  physiological growth optimum of 19-21°C (66-70°F); pike begin avoiding
  water above ~75°F (coldwater/coolwater-adapted species), and the upper
  lethal limit is documented around 29.4°C. Field telemetry in Minnesota
  lakes found large pike preferring 16-21°C in August even when warmer
  water (up to 28°C) was available.
- **Strength of evidence:** Field telemetry study (Minnesota lakes,
  large-vs-small pike depth/temperature use) is solid; the specific
  activity-optimum range (55-65°F) is more agency/extension-tier;
  physiological growth optimum and lethal limit come from
  laboratory/experimental physiology studies.
- **Source citations:**
  - "TEMPERATURES AND DEPTHS USED BY LARGE VERSUS SMALL NORTHERN PIKE IN
    THREE MINNESOTA LAKES" — ResearchGate:
    https://www.researchgate.net/publication/316857743
  - "Effects of temperature on the survival and development of the early
    life stages of northern pike" — KMAE:
    https://www.kmae-journal.org/articles/kmae/full_html/2022/01/kmae210086/kmae210086.html
  - Pike thermal-regime guidance report (agency-adjacent):
    https://pacgb.com/wpd/wp-content/uploads/2024/09/Pike-CR-Warm-Water-Report.pdf
- **Quantifiable/computable:** Quantifiable, yes. **Computable:** inland
  lakes only (Northern Pike is in inland creel data), requires water-temp
  estimation/acquisition.

### 8. Northern Pike — spawning trigger ~40-48°F, earliest gamefish to spawn in spring
- **Species:** Northern Pike
- **Claim:** Northern pike spawn earliest among gamefish in spring,
  triggered around 40-48°F water temperature.
- **Strength of evidence:** Widely repeated across extension/agency
  sources; consistent with the well-established early-life-stage cold-
  temperature-preference physiology (KMAE study above shows post-hatch
  survival peaks at 6-10°C, consistent with a cold spawning trigger), but
  the specific 40-48°F spawning-trigger figure itself is extension-tier,
  not a primary field study located in this pass.
- **Source citations:**
  - bassresource.com "Northern Fishes in Ponds" (extension-style
    compilation): https://www.bassresource.com/fish_biology/walleye-bass-perch.html
  - Supporting primary physiology: KMAE 2022 (northern pike early life
    stage temperature effects), cited above.
- **Quantifiable/computable:** Quantifiable, yes. **Computable:** same
  constraints as #7 (inland lakes, needs water-temp
  estimation/acquisition); usable only at seasonal resolution given
  outcome-data granularity.

### 9. Muskellunge — thermal optimum ~22°C (72°F); activity declines above 25°C; mortality-risk threshold ~26°C; thermal refuging behavior in summer
- **Species:** Muskellunge
- **Claim:** Muskellunge thermal optimum is approximately 22°C; activity
  declines above 25°C; 26°C is associated with elevated post-release
  angling mortality (physiological stress); in summer, muskellunge seek
  thermal refugia near the thermocline (>2°C cooler than surface) even
  though ambient surface temps can exceed 26-32°C.
- **Strength of evidence:** Field telemetry/radio-tracking studies
  (multiple, including a 2024 Aquaculture Fish & Fisheries paper) — solid,
  species- and behavior-specific.
- **Source citations:**
  - "Spatial ecology and thermal preferences of muskellunge" (Bieber et
    al. 2024, Aquaculture, Fish and Fisheries):
    https://fishlab.nres.illinois.edu/wp-content/uploads/2025/10/Bieber_et_al_2024_Aquaculture_Fish_Fisheries_Muskie_movements.pdf
  - "Behavior, escapement, and mortality of adult Muskellunge in
    Midwestern reservoirs" — ScienceDirect:
    https://www.sciencedirect.com/science/article/abs/pii/S0165783621000734
- **Quantifiable/computable:** Quantifiable, yes (specific °C values).
  **Computable:** inland lakes only (Muskellunge is in inland creel data),
  requires water-temp estimation/acquisition. Note: the mortality-risk
  threshold (26°C) is about catch-and-release survival, not catchability,
  so only the activity/thermal-optimum piece is relevant as a
  catch-rate predictor candidate; flagging this distinction so it is not
  conflated in step 2.

### 10. Black Crappie — preferred temperature ~27-29°C (81-84°F) for adults/juveniles; broader "optimal activity" band cited 22-25°C in some sources; feeding events increased 22% with a 2°C rise in one study
- **Species:** Black Crappie
- **Claim:** Preferred temperature for juvenile/adult black crappie is
  27-29°C in one telemetry-adjacent source; a separate study found a 2°C
  temperature increase over 4 weeks produced a 22.2% increase in feeding
  events; growth was fastest at optimal temperatures and markedly slower
  (48% slower) at cold and (82% slower) at hot extremes.
- **Strength of evidence:** Mixed — the feeding-events study
  (Minnesota State student research, published via institutional
  repository) is a direct, controlled feeding-behavior experiment, which
  is unusually good evidence quality for a catchability-adjacent claim,
  but it is a student/undergraduate research report rather than a
  journal article, and the 27-29°C "preferred temperature" figure lacks a
  clearly identified primary citation in this pass.
- **Source citations:**
  - "Effect of Increased Water Temperature on Warm Water Fish Feeding
    Behavior and Habitat Use" — Minnesota State student research:
    https://cornerstone.lib.mnsu.edu/jur/vol11/iss1/13/
  - "Feeding Biology of the Black Crappie, Pomoxis nigromaculatus" —
    Canadian Journal of Fisheries and Aquatic Sciences (1968, classic
    primary study, general biology not specifically thermal):
    https://cdnsciencepub.com/doi/10.1139/f68-024
- **Quantifiable/computable:** Quantifiable (numeric bands), yes, but
  **evidence quality flagged as weaker** than most other candidates here
  (undergraduate research report as primary source for the specific
  numbers; classic 1968 paper is about feeding biology generally, not a
  thermal-catchability metric). Recommend treating this as lower priority
  than candidates 1-9. **Computable:** inland lakes only, requires
  water-temp estimation/acquisition.

### 11. Bluegill — spawning trigger ~65-80°F (commonly cited peak initiation ~71.6°F), repeat spawning through summer at ~30-day intervals while temp remains above ~71.6°F
- **Species:** Bluegill
- **Claim:** Bluegill spawning is triggered by water temperature reaching
  the mid-60s to 80°F range, with repeat/multiple-brood spawning through
  the season roughly every 30 days as long as temperature stays above
  ~71.6°F (22°C).
- **Strength of evidence:** Extension/agling-media-adjacent sources
  dominate; the underlying temperature-triggered-spawning mechanism is
  well established general fish reproductive physiology, but a primary
  field or lab citation with this specific numeric window was not
  located in this pass — flagging as **extension-tier, not primary
  literature**, for the precise numbers.
- **Source citations:**
  - USAngler "When Do Bluegill Spawn?": https://usangler.com/when-do-bluegill-spawn/
  - Panfish Nation "Bluegill Spawn": https://panfishnation.com/bluegill-spawn/
  - (General spawning-temperature-trigger physiology is well established
    across sunfish species in primary literature; the specific °F cited
    here should be re-verified against a primary source, e.g. a state
    fisheries agency creel/biology report, before being treated as final
    in step 2.)
- **Quantifiable/computable:** Quantifiable (numeric threshold), yes.
  **Computable:** inland lakes only (Bluegill is in inland creel data —
  e.g., Minocqua Lake top species), requires water-temp
  estimation/acquisition, and only usable at the seasonal resolution the
  outcome data provides.

### 12. Chinook Salmon (Lake Michigan) — feeds most actively ~50-58°F, prime window ~52-56°F; follows thermocline, stacks at 52°F water in summer even when surface exceeds 70°F
- **Species:** Chinook Salmon
- **Claim:** Chinook (king) salmon feed most actively in 50-58°F water,
  with prime activity at 52-56°F; in summer stratification, Chinook
  track the thermocline and can be found at 60-120 ft depth in ~52°F
  water while Lake Michigan surface water exceeds 70°F.
- **Strength of evidence:** Mixed — thermocline-following behavior in
  cold-water salmonids is well-established general physiology (supported
  indirectly by broader salmonid thermal-behavior telemetry literature,
  e.g. Chinook/steelhead thermal exposure studies in river systems), but
  the specific 50-58°F Lake Michigan feeding-activity figures found in
  this pass trace to charter-fishing-industry sources
  (saugatuckcharterfishing.com, fishing-reports.ai), not a primary
  scientific study. **This numeric claim does not meet this cycle's
  evidentiary bar as stated** — flagged rather than excluded outright,
  because the underlying thermocline-tracking mechanism is real and well
  documented, but the specific temperature numbers need a primary source
  (e.g. Wismer & Christie 1987 GLFC compilation, or a Lake Michigan
  Chinook telemetry study) before being used as a predictor value.
- **Source citations:**
  - Thermal exposure of adult Chinook salmon and steelhead — PLOS ONE
    (river system, not Lake Michigan specifically, but directly relevant
    telemetry methodology and general thermal-behavior finding):
    https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0204274
  - Charter-fishing sources for the specific °F figures (flagged,
    not primary science): https://saugatuckcharterfishing.com/understanding-salmon-behavior-in-lake-michigan-seasonal-patterns-that-affect-your-catch/
  - General cold-water thermal preference/thermocline-tracking is also
    supported by lake trout/Chinook growth-modeling work: "Predicted
    growth of lake trout and Chinook salmon in a warming lake" —
    ScienceDirect: https://www.sciencedirect.com/science/article/pii/S0380133024000376
- **Quantifiable/computable:** Partially — the general "cold water
  preference, tracks thermocline" mechanism is real science and
  quantifiable in principle (distance of surface/near-surface WTMP from
  a stated optimal band), but **the specific numeric range used above
  should be treated as unverified** pending a primary source. NDBC WTMP
  surface data exists for Lake Michigan and Chinook/"All salmonids
  combined" appears in the outcome data, so this is directly computable
  once/if a primary-sourced numeric band is confirmed — but note that
  surface buoy WTMP is a poor proxy for the depth-following behavior
  described (fish may be well below the thermocline while surface WTMP
  reads warm), so even with a verified number, this predictor's real-world
  applicability with only surface buoy data is limited.

### 13. Coho Salmon (Lake Michigan) — prefers slightly warmer water than Chinook (~54-60°F), more tolerant of shallow/changing conditions
- **Species:** Coho Salmon
- **Claim:** Coho salmon prefer 54-60°F, running slightly warmer than
  Chinook, and tolerate shallower/more variable thermal conditions.
- **Strength of evidence:** Same evidentiary issue as #12 — general
  cross-species salmonid thermal-preference ranking (Coho warmer-tolerant
  than Chinook, Chinook warmer-tolerant than lake trout) is consistent
  with established salmonid thermal ecology, but the specific °F figures
  found trace to charter-fishing/recreational sources, not a primary
  study located in this pass.
- **Source citations:** Same as #12 (saugatuckcharterfishing.com;
  general salmonid thermal ecology literature).
- **Quantifiable/computable:** Same caveat as #12 — mechanism plausible
  and in-principle computable (Coho appears directly in LM monthly data,
  e.g. "Coho Salmon" rows with monthly harvest rate; NDBC WTMP exists),
  but specific numeric band needs primary-source verification before
  use.

### 14. Brown Trout — annual modal selected temperature ~12°C (54°F); upper preferred limit ~16°C (61°F) in Lake Michigan
- **Species:** Brown Trout
- **Claim:** Brown trout in Lake Michigan select a modal temperature of
  about 12°C on an annual basis (the reported optimum metabolic
  temperature for the species), with an upper preferred-temperature
  estimate around 16°C.
- **Strength of evidence:** Field study specifically referencing Lake
  Michigan brown trout movement relative to thermal gradients — directly
  relevant water body, reasonably strong.
- **Source citations:**
  - "Selected temperatures and thermal experience of brown trout, Salmo
    trutta, in a steep thermal gradient in nature" — Env. Biol. Fishes:
    https://link.springer.com/content/pdf/10.1007/BF00005180.pdf
- **Quantifiable/computable:** Quantifiable, yes. **Computable:** Brown
  Trout appears in inland creel data (Devils Lake) — inland requires
  water-temp estimation/acquisition. Not confirmed present in the LM
  species-level harvest data checked (LM data used "All salmonids
  combined" as a category which would implicitly include brown trout,
  but species-level LM brown trout rows were not confirmed in the files
  read) — verify species-level availability in step 2 before use.

### 15. Lake Trout — cold-water preference ~40-52°F (4-11°C)
- **Species:** Lake Trout
- **Claim:** Lake trout, as the coldest-water-adapted salmonid group in
  the Great Lakes, prefer roughly 40-52°F.
- **Strength of evidence:** General secondary/extension-tier synthesis;
  broadly consistent with lake trout being the coldest-preference
  salmonid (supported indirectly by the lake trout/Chinook
  growth-modeling paper above and general Great Lakes thermal-guild
  literature), but a primary field study with this specific numeric band
  was not directly retrieved in this pass (attempted retrieval of the
  Wismer & Christie 1987 GLFC compilation, which would be the ideal
  primary source, but the PDF could not be parsed during this research
  pass — recommend re-attempting direct retrieval in step 2 if this
  candidate is pursued).
- **Source citations:**
  - Great Lakes Fishery Commission, Wismer, D.F. & Christie, W.J. 1987.
    "Temperature Relationships of Great Lakes Fishes: A Data
    Compilation." GLFC Special Publication 87-3.
    https://www.glfc.org/pubs/SpecialPubs/Sp87_3.pdf (PDF exists and is
    the correct primary compiled source for this and several other
    candidates in this list; could not be text-extracted during this
    research pass due to tooling limits — flagging for direct follow-up)
  - "Predicted growth of lake trout and Chinook salmon in a warming
    lake" — ScienceDirect: https://www.sciencedirect.com/science/article/pii/S0380133024000376
- **Quantifiable/computable:** Quantifiable, yes, but **evidence citation
  incomplete** — recommend re-sourcing directly from Wismer & Christie
  1987 before treating the number as final. Lake Trout appears in inland
  creel data; also may be present in LM data under "All salmonids
  combined." Computable for LM via NDBC WTMP; inland requires water-temp
  estimation/acquisition.

### 16. Cross-species — Ontario MNR (Hasnain, Minns & Shuter 2010, CCRR-17) compiled thermal metrics as a reusable primary-adjacent source
- **Species:** Cross-species (173 North American freshwater fish species,
  including essentially all species in this project's outcome data)
- **Claim:** Not a single relationship but a pointer to a
  peer-reviewed, cross-validated compilation of optimal growth
  temperature (OGT), final temperature preferendum (FTP), upper incipient
  lethal temperature (UILT), critical thermal maximum (CTMax), optimum
  spawning temperature (OS), and optimum egg development temperature (OE)
  for 173 species, with metrics shown to correlate with thermal
  preference class, reproductive guild, and spawning season.
- **Strength of evidence:** Peer-reviewed / agency technical report,
  itself a meta-compilation of primary literature — the strongest single
  source type available for this cycle if it can be obtained in full.
  Could not be retrieved as full text in this research pass (search
  returned only citing papers, not the report itself); recommend a
  direct follow-up fetch attempt (Ontario.ca government document
  repository) before step 2 if precise numeric values are needed for
  species not otherwise covered above (e.g. Sauger, Cisco, Burbot,
  Rainbow Trout).
- **Source citations:**
  - Hasnain, S.S., Minns, C.K., Shuter, B.J. 2010. "Key Ecological
    Temperature Metrics for Canadian Freshwater Fishes." Ontario
    Ministry of Natural Resources Climate Change Research Report
    CCRR-17. (cited via multiple secondary academic sources, e.g.
    https://cdnsciencepub.com/doi/10.1139/cjfas-2012-0217 ; direct PDF
    not retrieved in this pass)
- **Quantifiable/computable:** N/A directly (this is a source pointer, not
  a standalone testable candidate) — logged so step 2 knows where to look
  if more species-specific numeric values are needed.

### 17. Barometric pressure and catch rate/fish activity — EXCLUDED, does not meet evidentiary bar
- **Species:** Cross-species (general claim, commonly applied to all
  species in angling folklore)
- **Claim:** Rising/falling/absolute barometric pressure directly affects
  fish activity and catch rates (extremely common angling claim).
- **Strength of evidence:** Explicitly checked because it is one of the
  most common "physiological" claims in angling culture. Result: no
  primary scientific support found. Multiple independent sources state
  that controlled scientific studies have failed to demonstrate a direct,
  consistent relationship between barometric pressure and fish activity;
  one source notes any observed pressure-linked effects likely reflect
  correlated environmental factors (e.g. frontal-passage temperature/wind
  changes) rather than pressure itself acting as a physiological driver.
- **Source citations:**
  - "THE BAROMETRIC PRESSURE MYTH" — Active Angling New Zealand (explicitly
    surveys the lack of scientific support):
    https://activeanglingnz.com/2019/10/13/the-barometric-pressure-myth/
  - "Understanding Barometric Pressure in Fishing" — Wired2Fish:
    https://www.wired2fish.com/fish-biology/understanding-barometric-pressure-in-fishing
- **Quantifiable/computable:** N/A — **excluded per this cycle's explicit
  rule against angling folklore without primary scientific backing.**
  Included in this document only to record that it was checked and
  rejected, not as a candidate to carry into step 2. (Note: this is
  distinct from, and should not be confused with, the physiologically
  real thermal/dissolved-oxygen habitat-compression mechanisms in
  candidates #2 and #9, which are genuinely evidenced.)

---

## Notes for step 2 (predictor-eval)

1. Prioritize candidates #1-#9 (walleye light/temperature, yellow perch
   temperature, bass temperature, pike temperature, muskellunge
   temperature) — best evidence quality and most directly tied to
   species actually generating the bulk of the outcome data.
2. Candidate #1 (walleye diel/light-window feeding) cannot be tested
   against this project's current outcome data — no trip-level timestamp
   exists. Do not attempt to force a test of this one without first
   confirming a data-granularity fix; otherwise it should be logged as
   "considered, not testable in V0" per the pipeline's dataset-build
   step.
3. Every inland-lake temperature candidate (#2-#11, #14, #15) requires
   either acquiring real inland water-temperature data or deriving an
   estimate from the existing air-temperature weather files — this is a
   dataset-build task (step 2 for this cycle, "step 2" in the CLAUDE.md
   pipeline sense = dataset build), not something already available.
   Flag the estimation-from-air-temp approach as introducing additional
   error that should be acknowledged in any eventual report.
4. Candidates #12 and #13 (Chinook/Coho specific °F activity windows)
   have a real, well-evidenced underlying mechanism (thermocline
   tracking) but the specific numeric values currently sourced are from
   charter-fishing industry pages, not primary science — attempt to
   re-source numeric values directly from Wismer & Christie (1987, GLFC
   Sp87-3) or a Lake Michigan-specific Chinook/Coho telemetry study
   before using these numbers in a model; if a primary numeric source
   cannot be found, use the general "distance from typical Great Lakes
   salmonid coldwater preference" framing instead of the specific claimed
   °F bounds.
5. Candidate #16 (Hasnain et al. 2010, Ontario MNR CCRR-17) should be
   fetched directly if possible before step 2 begins — it would let many
   of the "extension-tier" numeric flags above (bluegill, black crappie,
   pike spawning trigger) be upgraded to a genuine peer-reviewed
   cross-species source instead.
6. Candidate #17 (barometric pressure) is excluded and should not be
   carried forward.
