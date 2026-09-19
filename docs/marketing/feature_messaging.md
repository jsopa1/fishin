# fishin: feature messaging and launch copy

Everything below is checked against what the app actually does today. The one hard rule (DECISIONS #005):
**fishin reports conditions and the science behind them. It never predicts, scores or promises a catch.**
Words to avoid: "guaranteed", "catch more", "hot spot", "likely to bite", "AI-powered". Words to use:
"in range", "documented", "sourced", "on your device".

## Positioning

**One line:** Know which Wisconsin fish are in their range right now, and why.

**Two lines:** Live water temperature from real Wisconsin sensors, checked against published fish research,
at 3,272 public boat launches, carry-ins and shore spots. Every answer shows its reasoning and its source.

**The idea in one contrast:** Other apps tell you where people caught fish. fishin tells you why they're biting.
(Keep "why they're biting" to mean *the documented conditions*, which is how the app itself states it.)

**Who it is for:** Wisconsin anglers who want to choose a spot and a species with evidence instead of hearsay,
and who do not want to hand over an account or their location to do it.

## The five screens, as benefits

| Screen | Headline | Proof point |
|---|---|---|
| **Recommended** | Your spots, ranked by what's in range now | Ranked on your phone from your own preferences. The rule is fixed and disclosed: how many of your species are in range, then evidence strength, spot type, reading quality, distance. No black box. |
| **Explore** | Map or list, then filter | 3,272 real WDNR access points. List sorts by Best match, Nearest or A to Z, and a visible chip shows when your preferences are in play. |
| **Spot** | Active fish, inactive fish, and why | Each fish sits in a green or yellow group by its documented temperature window, with the evidence tier (Confirmed or Likely) on every row. Water and air temperature, wind, moon. Stocking history, regulations and consumption advisories one tap away. |
| **Fish** | The full file on a species | Documented activity range, habitat, and recommended bait with how to use it. 27 species, public-domain photos, every claim cited. |
| **Profile** | Tune it to how you fish | Prefer, OK or Avoid per spot type, travel distance, the species you target, light or dark. No account. Stored on the device only. |

## Proof points (all true today)

- **3,272** public access points across Wisconsin: boat launches, carry-ins, shore fishing.
- **27** species with documented temperature ranges, habitat and bait, each with its sources.
- Every spot has a temperature, and it is **always labelled**: real measurement, estimated from nearby real
  readings, or air-temperature proxy. Never blended, never dressed up.
- Sensors refresh **every four hours**. Anything that cannot be refreshed at least weekly is not in the app.
- **Public-domain photos only**, each with its source and license on the page.
- **No account. No tracking of your location.** Your preferences, saved spots and location stay on your device;
  the ranking runs in your browser. The feed the app downloads is the same for everyone.
- **Open source** at github.com/jsopa1/fishin, with a public decision log of 55 entries, including the ones that
  reversed course.

## Voice

Neo-modern, calm, exact. Short sentences. Numbers over adjectives. Confident about the method, humble about the
outcome: "Here is what the water is doing and what the research says." Never hype.

## Social copy

### X / Bluesky (thread)

1. Wisconsin has 3,272 public boat launches and shore spots. Which one is right for the fish you want today?
   fishin checks live water temperature against published research and shows its work. 🧵
2. Open Recommended: your saved spots, then spots ranked by how many of your species are inside their documented
   temperature range right now. The ranking rule is fixed and visible. It's not a prediction.
3. Tap a spot: active fish in green, inactive in yellow, each with the evidence behind it (Confirmed or Likely),
   plus water and air temperature, wind, moon, stocking, regulations and advisories.
4. Tap a fish: documented activity range, habitat, and the baits agencies actually recommend, with how to use
   them. 27 species, public-domain photos, every claim cited.
5. Privacy by design: no account. Your preferences, saved spots and location never leave your phone; the ranking
   runs in your browser.
6. Open source, with a public decision log. github.com/jsopa1/fishin

### LinkedIn

> We built a fishing app around one rule: show the evidence, promise nothing. fishin compares live Wisconsin
> water temperatures with published fish-physiology research at 3,272 public access points and labels every
> reading as measured, estimated or proxy. It ranks spots on your device from your own preferences, so there
> is no account and no location data to hold. It is open source, including a public log of the decisions
> that shaped it. Built for anglers who would rather know why than be told where.

### Reddit (r/Fishing, r/Wisconsin, r/Outdoors), post title and first comment

**Title:** I built a free, open-source Wisconsin fishing conditions app that shows its sources. Looking for feedback from people who actually fish.

**First comment:** It compares live water temperature (USGS gauges, NOAA buoys, NWS) with published temperature
ranges for 27 species, at every public WDNR access point. It does not predict catches, and it says so on
every page. No account; your preferences never leave your phone. What's wrong, missing or misleading? I'd
rather hear it from you than from a comment thread six months from now.

### GitHub repository blurb

> Wisconsin conditions-and-biology fishing app. Live water temperature checked against published fish research
> at 3,272 public access points, with sources on every answer. Not a catch predictor. No accounts. Open decision log.

### Hashtags

#WisconsinFishing #Fishing #OpenSource #Outdoors #DataViz (keep to 3 per post)

## 45-second video script

| Time | On screen | Line |
|---|---|---|
| 0:00 | Title on deep ink, fish mark draws in | "Which fish are in their range right now?" |
| 0:04 | Recommended screen | "Your spots, ranked on your phone." |
| 0:11 | Ranking rule reveals as five steps | "A fixed rule. Visible. Not a prediction." |
| 0:17 | Spot screen: green Active, yellow Inactive | "Active fish, inactive fish, and why." |
| 0:24 | Fish screen: activity, habitat, bait | "Every fish, fully sourced." |
| 0:31 | Explore map to list | "3,272 real access points." |
| 0:36 | Profile: toggles, dark mode flip | "Tuned to how you fish. Stored only on your device." |
| 0:41 | Closing card | "fishin. Wisconsin fishing intelligence. Open source." |

## Assets

- Diagrams: `docs/diagrams/screen_map.svg`, `docs/diagrams/deployment_architecture.svg`
- Video: `docs/marketing/fishin-launch.mp4` (16:9) and `fishin-launch-square.mp4` (1:1) once rendered
- Screenshots: taken from the running app (`docs/marketing/screens/`)
