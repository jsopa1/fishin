"""Runs webapp/static/prefs.js under Node against fixed cases.

The preferences module is pure and takes its storage as an argument precisely
so it can be tested here without a browser. Skipped (not failed) when Node is
not installed, since Node is not a dependency of the app itself.

Run: python -m pytest webapp/tests/test_prefs_js.py
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

PREFS_JS = Path(__file__).resolve().parents[1] / "static" / "prefs.js"

HARNESS = r"""
const P = require(process.argv[1]);
class FakeStorage {
  constructor(seed) { this.d = Object.assign({}, seed || {}); }
  getItem(k) { return k in this.d ? this.d[k] : null; }
  setItem(k, v) { this.d[k] = String(v); }
}
class BrokenStorage { getItem() { throw new Error("blocked"); } setItem() { throw new Error("blocked"); } }
const out = {};
out.defaults = P.defaults();
out.emptyLoad = P.load(new FakeStorage());
out.garbageLoad = P.load(new FakeStorage({
  "fishin.prefs.theme.v1": "neon",
  "fishin.prefs.spotTypes.v1": "{not json",
  "fishin.prefs.species.v1": JSON.stringify(["walleye", "WALLEYE", 7, "  yellow perch ", "DRAGON"]),
  "fishin.prefs.maxDistance.v1": "\"far\"",
}));
out.garbageLoadKnownOnly = P.load(new FakeStorage({
  "fishin.prefs.species.v1": JSON.stringify(["walleye", "DRAGON", "yellow perch"]),
}), ["WALLEYE", "YELLOW PERCH"]);
const s = new FakeStorage();
const saved = P.save(s, { theme: "dark", spotTypes: { boat_ramp: "prefer", boat_carry_in: "avoid", shore_fishing: "bogus" }, species: ["Walleye"], maxMiles: 100 });
out.saved = saved;
out.roundTrip = P.load(s);
out.badSaveIsSanitized = (function () {
  const t = new FakeStorage();
  P.save(t, { theme: "x", spotTypes: null, species: "nope", maxMiles: 7 });
  return P.load(t);
})();
out.broken = { load: P.load(new BrokenStorage()), save: P.save(new BrokenStorage(), P.defaults()) };
out.allowed = { avoid: P.isSpotTypeAllowed({ spotTypes: { boat_ramp: "avoid" } }, "boat_ramp"), prefer: P.isSpotTypeAllowed({ spotTypes: { boat_ramp: "prefer" } }, "boat_ramp") };
out.hasAny = { fresh: P.hasAnyPreference(P.defaults()), species: P.hasAnyPreference(Object.assign(P.defaults(), { species: ["WALLEYE"] })), far: P.hasAnyPreference(Object.assign(P.defaults(), { maxMiles: 0 })) };
const attrs = {};
const fakeDoc = { documentElement: { setAttribute: (k, v) => { attrs[k] = v; }, removeAttribute: (k) => { delete attrs[k]; } } };
P.applyTheme(fakeDoc, "dark"); out.themeDark = Object.assign({}, attrs);
P.applyTheme(fakeDoc, "system"); out.themeSystem = Object.assign({}, attrs);
P.applyTheme(fakeDoc, "garbage"); out.themeGarbage = Object.assign({}, attrs);
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class PrefsJsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(["node", "-e", HARNESS, str(PREFS_JS)], capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        cls.out = json.loads(proc.stdout)

    def test_defaults_are_neutral(self):
        d = self.out["defaults"]
        self.assertEqual(d["theme"], "system")
        self.assertEqual(d["species"], [])
        self.assertEqual(set(d["spotTypes"].values()), {"ok"})
        self.assertEqual(d["maxMiles"], 50)

    def test_an_empty_store_loads_the_defaults(self):
        self.assertEqual(self.out["emptyLoad"], self.out["defaults"])

    def test_garbage_in_storage_falls_back_instead_of_breaking(self):
        g = self.out["garbageLoad"]
        self.assertEqual(g["theme"], "system")
        self.assertEqual(set(g["spotTypes"].values()), {"ok"})
        self.assertEqual(g["maxMiles"], 50)
        self.assertEqual(g["species"], ["DRAGON", "WALLEYE", "YELLOW PERCH"])  # deduped, non-strings dropped

    def test_unknown_species_are_dropped_when_the_known_list_is_given(self):
        self.assertEqual(self.out["garbageLoadKnownOnly"]["species"], ["WALLEYE", "YELLOW PERCH"])

    def test_a_save_round_trips_and_sanitizes_each_field(self):
        self.assertTrue(self.out["saved"])
        r = self.out["roundTrip"]
        self.assertEqual(r["theme"], "dark")
        self.assertEqual(r["spotTypes"], {"boat_ramp": "prefer", "boat_carry_in": "avoid", "shore_fishing": "ok"})
        self.assertEqual(r["species"], ["WALLEYE"])
        self.assertEqual(r["maxMiles"], 100)

    def test_a_bad_value_can_never_be_persisted(self):
        self.assertEqual(self.out["badSaveIsSanitized"], self.out["defaults"])

    def test_blocked_storage_degrades_to_defaults_without_throwing(self):
        self.assertEqual(self.out["broken"]["load"], self.out["defaults"])
        self.assertFalse(self.out["broken"]["save"])

    def test_avoid_excludes_a_spot_type_and_prefer_does_not(self):
        self.assertFalse(self.out["allowed"]["avoid"])
        self.assertTrue(self.out["allowed"]["prefer"])

    def test_has_any_preference(self):
        self.assertEqual(self.out["hasAny"], {"fresh": False, "species": True, "far": True})

    def test_theme_attribute_is_set_removed_and_sanitized(self):
        self.assertEqual(self.out["themeDark"], {"data-theme": "dark"})
        self.assertEqual(self.out["themeSystem"], {})
        self.assertEqual(self.out["themeGarbage"], {})


if __name__ == "__main__":
    unittest.main()
