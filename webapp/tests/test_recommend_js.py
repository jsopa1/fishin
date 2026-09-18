"""Runs webapp/static/recommend.js under Node against fixed vectors.

The ranking is the one place a "recommendation" could quietly become a
prediction or a black box, so every rule in the spec has a test here: the
lexicographic key, each edge case, determinism, and the always-present
disclosure. Skipped (not failed) when Node is not installed.

Run: python -m pytest webapp/tests/test_recommend_js.py
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

RECOMMEND_JS = Path(__file__).resolve().parents[1] / "static" / "recommend.js"

HARNESS = r"""
const R = require(process.argv[1]);
const spot = (n, o) => Object.assign({ n, w: "Lake " + n, c: "Dane", t: "boat_ramp", lat: 43.0, lon: -89.0, q: "real", a: [], s: [], i: [] }, o || {});
const names = (res) => res.recommended.map((c) => c.name);
const P = (o) => Object.assign({ spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "ok" }, species: [], maxMiles: 50 }, o || {});
const out = {};

// 1. Each key breaks ties only in the one before it.
const keyFeed = [
  spot("D-quality-est", { q: "estimated", a: [["WALLEYE", "c"]] }),
  spot("C-quality-real", { q: "real", a: [["WALLEYE", "c"]] }),
  spot("B-two-likely", { a: [["WALLEYE", "l"], ["BLUEGILL", "l"]] }),
  spot("A-two-one-confirmed", { a: [["WALLEYE", "c"], ["BLUEGILL", "l"]] }),
  spot("E-three", { q: "proxy", a: [["WALLEYE", "l"], ["BLUEGILL", "l"], ["MUSKELLUNGE", "l"]] }),
  spot("F-none"),
];
out.keyOrder = names(R.rank(keyFeed, { prefs: P() }));

// 2. Prefer breaks a tie that count/confirmed leave, and only that tie.
out.preferTie = names(R.rank([
  spot("plain", { t: "boat_ramp", a: [["WALLEYE", "c"]] }),
  spot("liked", { t: "shore_fishing", a: [["WALLEYE", "c"]] }),
], { prefs: P({ spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "prefer" } }) }));
out.preferDoesNotBeatCount = names(R.rank([
  spot("liked-but-fewer", { t: "shore_fishing", a: [["WALLEYE", "c"]] }),
  spot("plain-but-more", { t: "boat_ramp", a: [["WALLEYE", "c"], ["BLUEGILL", "c"]] }),
], { prefs: P({ spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "prefer" } }) }));

// 3. Target species reorder results; with none set every species counts.
const targetFeed = [
  spot("many-others", { a: [["BLUEGILL", "c"], ["BLACK CRAPPIE", "c"], ["YELLOW PERCH", "c"]] }),
  spot("has-walleye", { a: [["WALLEYE", "l"]] }),
];
out.noTargets = names(R.rank(targetFeed, { prefs: P() }));
out.withTarget = names(R.rank(targetFeed, { prefs: P({ species: ["WALLEYE"] }) }));

// 4. Avoid removes a type from recommendations; a saved spot is still shown.
const avoidFeed = [
  spot("ramp", { t: "boat_ramp", a: [["WALLEYE", "c"]] }),
  spot("shore", { t: "shore_fishing", lat: 43.5, a: [["WALLEYE", "c"], ["BLUEGILL", "c"]] }),
];
const avoidPrefs = P({ spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "avoid" } });
out.avoid = names(R.rank(avoidFeed, { prefs: avoidPrefs }));
const avoidSaved = R.rank(avoidFeed, { prefs: avoidPrefs, saved: [{ lat: 43.5, lon: -89.0, name: "shore" }] });
out.avoidSaved = { saved: avoidSaved.saved.map((c) => c.name), rec: names(avoidSaved) };

// 5. Spawning-range matches are shown but never used to rank.
const spawn = R.rank([
  spot("spawning-only", { s: ["WALLEYE", "NORTHERN PIKE", "MUSKELLUNGE"] }),
  spot("one-in-window", { a: [["BLUEGILL", "l"]] }),
], { prefs: P() });
out.spawn = { order: names(spawn), shown: spawn.recommended.find((c) => c.name === "spawning-only").spawning };

// 6. No location: no distance, statewide, and the disclosure says so.
const noLoc = R.rank(keyFeed, { prefs: P(), location: null });
out.noLocation = { known: noLoc.meta.locationKnown, radius: noLoc.meta.radiusMiles, dist: noLoc.recommended[0].distanceKm, note: /Location is off/.test(noLoc.disclosure) };

// 7. Radius ladder: too few nearby -> widen, and say which radius was used.
const far = [];
for (let k = 0; k < 6; k++) far.push(spot("far" + k, { lat: 43.0 + 1.0 + k * 0.01, lon: -89.0, a: [["WALLEYE", "c"]] })); // ~111 km north
const near = [spot("near0", { lat: 43.001, a: [["BLUEGILL", "l"]] })];
const ladder1 = R.rank(near.concat(far), { prefs: P({ maxMiles: 10 }), location: { lat: 43.0, lon: -89.0 } });
out.ladder = { radius: ladder1.meta.radiusMiles, first: ladder1.recommended[0].name, count: ladder1.recommended.length, text: /within 100 miles|across Wisconsin|within 200 miles/.test(ladder1.disclosure) };
const enough = [];
for (let k = 0; k < 5; k++) enough.push(spot("n" + k, { lat: 43.0 + k * 0.001, a: [["BLUEGILL", "l"]] }));
const noLadder = R.rank(enough.concat(far), { prefs: P({ maxMiles: 10 }), location: { lat: 43.0, lon: -89.0 } });
out.noLadder = { radius: noLadder.meta.radiusMiles, names: names(noLadder).filter((n) => n.startsWith("far")).length };
out.anyDistance = R.rank(near.concat(far), { prefs: P({ maxMiles: 0 }), location: { lat: 43.0, lon: -89.0 } }).meta.radiusMiles;

// 8. Distance breaks a tie only after every earlier key.
const distFeed = [
  spot("farther", { lat: 43.2, a: [["WALLEYE", "c"]] }),
  spot("closer", { lat: 43.05, a: [["WALLEYE", "c"]] }),
];
out.distance = names(R.rank(distFeed, { prefs: P(), location: { lat: 43.0, lon: -89.0 } }));

// 9. Targets match nothing anywhere: never an empty list.
const miss = R.rank(targetFeed, { prefs: P({ species: ["LAKE STURGEON"] }) });
out.targetMiss = { miss: miss.meta.targetMiss, mode: miss.meta.mode, order: names(miss), note: /None of your target species/.test(miss.disclosure) };

// 10. Nothing in range anywhere (ice season): rank by how close a window is.
const ice = R.rank([
  spot("cold-far", { i: [["WALLEYE", "c", 20.0]] }),
  spot("cold-near", { i: [["WALLEYE", "c", 3.2], ["BLUEGILL", "l", 30]] }),
  spot("no-window"),
], { prefs: P() });
out.ice = { mode: ice.meta.mode, order: names(ice), nearest: ice.recommended[0].nearest, note: /how close a species is to its range/.test(ice.disclosure) };

// 11. Determinism: same input twice, and input order does not matter.
const shuffled = keyFeed.slice().reverse();
const a1 = JSON.stringify(R.rank(keyFeed, { prefs: P() })), a2 = JSON.stringify(R.rank(keyFeed, { prefs: P() }));
out.deterministic = a1 === a2;
out.orderIndependent = JSON.stringify(names(R.rank(keyFeed, { prefs: P() }))) === JSON.stringify(names(R.rank(shuffled, { prefs: P() })));
const tied = [spot("Z", { lat: 43.1 }), spot("A", { lat: 43.2 }), spot("M", { lat: 43.3 })];
out.tieBreak = names(R.rank(tied, { prefs: P() }));

// 12. Saved spots: same key, no radius filter, not repeated in recommended, unmatched ones still listed.
const savedFeed = [
  spot("saved-weak", { lat: 45.0, a: [["BLUEGILL", "l"]] }),
  spot("saved-strong", { lat: 45.1, a: [["WALLEYE", "c"], ["BLUEGILL", "c"]] }),
  spot("other", { lat: 43.0, a: [["WALLEYE", "c"]] }),
];
const sv = R.rank(savedFeed, { prefs: P({ maxMiles: 10 }), location: { lat: 43.0, lon: -89.0 },
  saved: [{ lat: 45.0, lon: -89.0, name: "saved-weak" }, { lat: 45.1, lon: -89.0, name: "saved-strong" }, { lat: 40.0, lon: -80.0, name: "gone", water: "Gone Lake", county: "X" }] });
out.saved = { saved: sv.saved.map((c) => c.name), rec: names(sv), noData: sv.saved.find((c) => c.name === "gone").count };

// 13. Display limit and empty feed.
const many = []; for (let k = 0; k < 30; k++) many.push(spot("s" + String(k).padStart(2, "0"), { lat: 43 + k * 0.001, a: [["WALLEYE", "c"]] }));
out.limit = R.rank(many, { prefs: P() }).recommended.length;
const empty = R.rank([], { prefs: P() });
out.empty = { rec: empty.recommended.length, saved: empty.saved.length, hasDisclosure: empty.disclosure.length > 0 };

// 14. Disclosure is always present and always disclaims prediction.
out.disclosures = [noLoc, ladder1, miss, ice, empty, R.rank(keyFeed, { prefs: P({ species: ["WALLEYE"], spotTypes: { boat_ramp: "prefer", boat_carry_in: "avoid", shore_fishing: "ok" } }) })]
  .map((r) => /not a prediction of catch success/.test(r.disclosure));

// 15. The card says only what the feed says.
const c0 = R.rank([spot("x", { a: [["WALLEYE", "c"], ["BLUEGILL", "l"]], s: ["MUSKELLUNGE"], q: "estimated" })], { prefs: P() }).recommended[0];
out.card = { count: c0.count, confirmed: c0.confirmed, inRange: c0.inRange.map((e) => e.species + ":" + e.tier), spawning: c0.spawning, quality: c0.quality, url: c0.url };

// 16. Alphabetical sort is independent of the ranking.
out.alpha = R.sortAlphabetical([spot("b", { w: "Zed" }), spot("a", { w: "Alpha" })]).map((s) => s.w);
out.alphaCase = R.sortAlphabetical([spot("x", { w: "Zed" }), spot("CHEROKEE", { w: "Lake", n: "CHEROKEE PARK" }), spot("c", { w: "Lake", n: "Crystal Lake" })]).map((s) => s.n);
// 17. Explore (rankOnly): preferences order but never hide, the radius does not apply, and the
// order equals the normal ranking of the same spots.
const ex = [
  spot("shore-far", { t: "shore_fishing", lat: 46.0, a: [["WALLEYE", "c"], ["BLUEGILL", "c"]] }),
  spot("ramp-near", { t: "boat_ramp", lat: 43.001, a: [["WALLEYE", "c"]] }),
  spot("carry", { t: "boat_carry_in", lat: 44.0, a: [] }),
];
const exPrefs = P({ maxMiles: 10, spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "avoid" } });
const exRank = R.rank(ex, { prefs: exPrefs, location: { lat: 43.0, lon: -89.0 }, rankOnly: true, limit: 60 });
const exNormal = R.rank(ex, { prefs: exPrefs, location: { lat: 43.0, lon: -89.0 } });
out.rankOnly = {
  order: names(exRank), normal: names(exNormal), radius: exRank.meta.radiusMiles, flag: exRank.meta.rankOnly,
  text: /Your filters decide which spots are listed/.test(exRank.disclosure), predicts: /not a prediction of catch success/.test(exRank.disclosure),
  noRadiusSentence: !/Showing spots within/.test(exRank.disclosure),
};
const plain = R.rank(ex, { prefs: P(), rankOnly: true, limit: 60 });
out.rankOnlyEqualsNormalWhenNothingIsHidden = JSON.stringify(names(plain)) === JSON.stringify(names(R.rank(ex, { prefs: P() })));

// 18. Shared card markup: escapes, names tiers, and never claims a bite.
const html = R.cardHtml(R.rank([spot('<img src=x onerror=alert(1)>', { w: 'A & B', a: [["WALLEYE", "c"], ["BLUEGILL", "l"]], s: ["MUSKELLUNGE"], q: "proxy" })], { prefs: P() }).recommended[0]);
out.cardHtml = {
  escaped: html.indexOf("<img") === -1 && html.indexOf("&lt;img") !== -1,
  ampersand: html.indexOf("A &amp; B") !== -1,
  confirmed: /evidence-confirmed">Confirmed/.test(html), likely: /evidence-likely">Likely/.test(html),
  inRangeWording: html.indexOf("In range now:") !== -1, noBiteClaim: !/bite|catch|likely to/i.test(html.replace(/evidence-likely">Likely/, "")),
  titled: html.indexOf("<strong>Walleye</strong>") !== -1 && html.indexOf("Muskellunge") !== -1 && html.indexOf("WALLEYE") === -1,
  spawn: html.indexOf("check regulations") !== -1, proxy: html.indexOf("air-temperature proxy") !== -1,
};
const iceHtml = R.cardHtml(R.rank([spot("cold", { i: [["WALLEYE", "c", 3.2]] })], { prefs: P() }).recommended[0]);
out.iceHtml = /Closest to its range/.test(iceHtml) && /3\.2&deg;F outside it/.test(iceHtml);
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class RecommendJsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(["node", "-e", HARNESS, str(RECOMMEND_JS)], capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        cls.out = json.loads(proc.stdout)

    def test_each_key_breaks_ties_only_in_the_one_before(self):
        # count desc (E three > A,B two > C,D one > F none); A beats B (confirmed);
        # C beats D (real beats estimated). E has the worst reading quality yet wins on count.
        self.assertEqual(
            self.out["keyOrder"],
            ["E-three", "A-two-one-confirmed", "B-two-likely", "C-quality-real", "D-quality-est", "F-none"],
        )

    def test_prefer_only_breaks_ties(self):
        self.assertEqual(self.out["preferTie"], ["liked", "plain"])
        self.assertEqual(self.out["preferDoesNotBeatCount"], ["plain-but-more", "liked-but-fewer"])

    def test_target_species_reorder_the_results(self):
        self.assertEqual(self.out["noTargets"], ["many-others", "has-walleye"])
        self.assertEqual(self.out["withTarget"], ["has-walleye", "many-others"])

    def test_avoid_hides_a_type_from_recommendations_but_not_from_saved_spots(self):
        self.assertEqual(self.out["avoid"], ["ramp"])
        self.assertEqual(self.out["avoidSaved"], {"saved": ["shore"], "rec": ["ramp"]})

    def test_spawning_matches_are_shown_but_never_ranked(self):
        self.assertEqual(self.out["spawn"]["order"], ["one-in-window", "spawning-only"])
        self.assertEqual(self.out["spawn"]["shown"], ["WALLEYE", "NORTHERN PIKE", "MUSKELLUNGE"])

    def test_no_location_means_no_distance_and_says_so(self):
        n = self.out["noLocation"]
        self.assertFalse(n["known"])
        self.assertIsNone(n["radius"])
        self.assertIsNone(n["dist"])
        self.assertTrue(n["note"])

    def test_the_radius_widens_when_too_few_spots_are_close_and_says_so(self):
        self.assertEqual(self.out["ladder"]["count"], 7)
        self.assertEqual(self.out["ladder"]["first"], "far0")  # confirmed walleye beats the near bluegill
        self.assertGreater(self.out["ladder"]["radius"] or 999, 10)
        self.assertTrue(self.out["ladder"]["text"])

    def test_the_radius_is_kept_when_enough_spots_are_close(self):
        self.assertEqual(self.out["noLadder"], {"radius": 10, "names": 0})

    def test_any_distance_is_statewide(self):
        self.assertIsNone(self.out["anyDistance"])

    def test_distance_breaks_ties_last(self):
        self.assertEqual(self.out["distance"], ["closer", "farther"])

    def test_target_species_matching_nothing_never_produces_an_empty_list(self):
        m = self.out["targetMiss"]
        self.assertTrue(m["miss"])
        self.assertEqual(m["mode"], "all")
        self.assertEqual(m["order"], ["many-others", "has-walleye"])
        self.assertTrue(m["note"])

    def test_when_nothing_is_in_range_spots_rank_by_closeness_to_a_window(self):
        i = self.out["ice"]
        self.assertEqual(i["mode"], "closest")
        self.assertEqual(i["order"], ["cold-near", "cold-far", "no-window"])
        self.assertEqual(i["nearest"], {"species": "WALLEYE", "distanceF": 3.2})
        self.assertTrue(i["note"])

    def test_same_input_gives_identical_output_and_input_order_is_irrelevant(self):
        self.assertTrue(self.out["deterministic"])
        self.assertTrue(self.out["orderIndependent"])

    def test_full_ties_resolve_by_waterbody_name(self):
        self.assertEqual(self.out["tieBreak"], ["A", "M", "Z"])

    def test_saved_spots_use_the_same_key_skip_the_radius_and_are_not_repeated(self):
        s = self.out["saved"]
        self.assertEqual(s["saved"], ["saved-strong", "saved-weak", "gone"])
        self.assertEqual(s["rec"], ["other"])
        self.assertEqual(s["noData"], 0)

    def test_at_most_ten_are_recommended_and_an_empty_feed_is_safe(self):
        self.assertEqual(self.out["limit"], 10)
        self.assertEqual(self.out["empty"], {"rec": 0, "saved": 0, "hasDisclosure": True})

    def test_the_disclosure_is_always_present_and_always_disclaims_prediction(self):
        self.assertEqual(self.out["disclosures"], [True] * 6)

    def test_a_card_reports_only_what_the_feed_says(self):
        c = self.out["card"]
        self.assertEqual(c["count"], 2)
        self.assertEqual(c["confirmed"], 1)
        self.assertEqual(c["inRange"], ["WALLEYE:confirmed", "BLUEGILL:likely"])
        self.assertEqual(c["spawning"], ["MUSKELLUNGE"])
        self.assertEqual(c["quality"], "estimated")
        self.assertTrue(c["url"].startswith("/spot?lat="))

    def test_alphabetical_sort_is_independent_of_the_ranking(self):
        self.assertEqual(self.out["alpha"], ["Alpha", "Zed"])
        self.assertEqual(self.out["alphaCase"], ["CHEROKEE PARK", "Crystal Lake", "x"])  # folds case: Che < Cry

    def test_explore_ordering_never_hides_a_spot_and_ignores_the_radius(self):
        r = self.out["rankOnly"]
        self.assertTrue(r["flag"])
        self.assertEqual(sorted(r["order"]), ["carry", "ramp-near", "shore-far"])  # the avoided shore spot is still listed
        self.assertEqual(r["order"], ["shore-far", "ramp-near", "carry"])  # ordered by species count, not hidden or by distance
        self.assertNotIn("shore-far", r["normal"])  # Recommended, by contrast, honours "avoid"
        self.assertIsNone(r["radius"])
        self.assertTrue(r["text"])
        self.assertTrue(r["predicts"])
        self.assertTrue(r["noRadiusSentence"])

    def test_explore_order_matches_recommended_order_when_nothing_is_excluded(self):
        self.assertTrue(self.out["rankOnlyEqualsNormalWhenNothingIsHidden"])

    def test_card_markup_escapes_names_and_states_tiers_without_claiming_a_bite(self):
        c = self.out["cardHtml"]
        for key, value in c.items():
            self.assertTrue(value, key)

    def test_the_nothing_in_range_card_says_how_far_outside_the_window(self):
        self.assertTrue(self.out["iceHtml"])


if __name__ == "__main__":
    unittest.main()
