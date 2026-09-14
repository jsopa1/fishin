# Bait & Technique Reference — Research Report

Phase 3 of [docs/v2_fish_intelligence_platform_plan.md](v2_fish_intelligence_platform_plan.md).
Data: [`data/v1/bait_technique_reference_v1.json`](../data/v1/bait_technique_reference_v1.json).
Resolver: [`analysis/v1_bait_technique.py`](../analysis/v1_bait_technique.py).

## What this phase had to solve

The plan flagged this as "the real lift" and as a research task rather than
an engineering one, with a specific warning: bait guidance must not be
fabricated, and must carry the same evidence discipline as the physiology
data it sits next to.

That turned out to be the whole difficulty, because **bait and technique
guidance is not the same kind of knowledge as thermal physiology.** The
physiology in this project traces to peer-reviewed literature and a Great
Lakes Fishery Commission compilation. "Throw a jig" does not, and no amount
of searching will make it. Presenting the two at the same confidence would
have been exactly the overclaiming this project exists to avoid.

## What was actually found, and what wasn't

**Found, and genuinely well-established:** the physiological mechanism that
links temperature to how a fish behaves.

- Fish are ectotherms, so metabolic rate scales with water temperature. The
  Q10 coefficient for fish metabolic rate is typically around 2 — the rate
  roughly doubles per 10 °C rise within the tolerated range
  (Clarke & Johnston 1999, *Journal of Animal Ecology* 68:893–905).
- Aerobic scope and sustainable swimming performance are temperature-limited
  (Brett 1971 and the subsequent aerobic-scope literature). A fish in cold
  water is not merely disinclined to chase fast prey — it is physically less
  able to, and gains less from trying.
- Spawning temperature relocates fish to predictable habitat and switches
  behaviour from feeding to reproduction and nest defence. This project
  already holds the spawning-trigger ranges that say when.
- Above an avoidance threshold, fish leave water at that temperature for
  cooler refuge, while warm water simultaneously holds less dissolved oxygen
  and raises oxygen demand.

**Not found as research, and labelled accordingly:** the specific technique.
Searches for peer-reviewed backing on lure selection, retrieve speed and
presentation returned angling magazines and fishing blogs, not studies. The
recommendations are widely-practised convention that follows sensibly from
the physiology above — but "sensible inference from real science" is not the
same as "tested", and the file says so on every entry.

## How the honesty problem was solved

Every entry carries **two separately-tiered claims**:

| Field | What it is | Tier |
|---|---|---|
| `biological_basis` | The mechanism — why the fish behaves this way at this temperature | `well-established` |
| `angling_application` | The technique anglers use in response | `angling-convention` |

The UI renders both tiers visibly, so a reader can always see which half is
research and which half is craft. A test (`test_application_is_never_labelled_as_research`)
fails the build if the technique ever inherits the physiology's tier.

## Structure: keyed to state, not to season

The plan called for entries tied to a **condition** rather than a fixed
"use lure X", and that is what shipped. Guidance is keyed to the same four
thermal states this app already derives from
`physiology_thresholds_v1.json`:

- `below_activity_window`
- `in_activity_window`
- `in_spawning_trigger`
- `above_avoidance`

`resolve_state()` prioritises `above_avoidance` and `in_spawning_trigger`
over `in_activity_window`, because both override plain feeding behaviour: a
fish actively fleeing warm water is not "feeding normally" merely because
the number also falls inside its activity range.

Species without their own entry still receive the general physiology rather
than nothing — the mechanism holds regardless of which fish it is — and the
UI marks whether the technique shown was species-specific or general.

## Coverage

Eleven species have specific technique entries, selected by documented
waterbody count in the live database:

| Species | Waterbodies | Species-specific states |
|---|---:|---|
| Walleye | 631 | activity, cold, spawning |
| Brook Trout | 442 | activity, avoidance |
| Brown Trout | 405 | activity, cold |
| Rainbow Trout | 358 | activity, cold |
| Muskellunge | 306 | activity, cold, avoidance |
| Bluegill | 289 | activity, cold, spawning |
| Yellow Perch | 289 | activity, cold |
| Largemouth Bass | 283 | activity, cold, spawning |
| Northern Pike | 257 | activity, cold, avoidance |
| Black Crappie | 249 | activity, cold, spawning |
| Smallmouth Bass | 47 | activity, cold, spawning |

Fathead Minnow (140) and White Sucker (137) rank high by presence but were
deliberately skipped — they are forage and bait species, not angling targets.

## Deliberate omissions

- **No specific lure brands, sizes or colours.** These vary by water and by
  season in ways this project has no data to resolve, and inventing them
  would be the fabrication the whole phase was designed to avoid.
- **No claim that following the guidance will catch fish.** The guidance
  explains what the fish's thermal state implies about presentation. It does
  not predict outcome, consistent with the V0 finding.
- **Regulation-sensitive states carry a warning rather than encouragement.**
  Spawning-period entries note that Wisconsin closes or restricts seasons on
  many waters precisely then, and warm-water entries note that release
  mortality is high — for muskellunge and brook trout the honest advice is
  sometimes to stop fishing, not to switch lures.

## What would strengthen this next

- Wisconsin-specific technique sourcing from WDNR or UW Sea Grant
  publications would let some entries move from `angling-convention` to
  `agency-tier`.
- Forage-base data (what the fish is actually eating in a given water) would
  make "match the forage" advice concrete rather than generic. No such
  dataset was found in this pass.
