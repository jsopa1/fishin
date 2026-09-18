// Anonymous, on-device preferences (V4 Phase 3). Everything here lives in
// localStorage and is never sent to the server. The functions are pure and
// take the storage object as an argument so they can be tested under Node
// (webapp/tests/test_prefs_js.py); in the browser they default to
// window.localStorage, and every access is wrapped because storage can be
// missing or throw (private windows, blocked site data).
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.FishinPrefs = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var KEYS = {
    theme: "fishin.prefs.theme.v1",
    spotTypes: "fishin.prefs.spotTypes.v1",
    species: "fishin.prefs.species.v1",
    maxMiles: "fishin.prefs.maxDistance.v1",
  };
  var SPOT_TYPES = ["boat_ramp", "boat_carry_in", "shore_fishing"];
  var LEVELS = ["prefer", "ok", "avoid"];
  var THEMES = ["system", "light", "dark"];
  var DISTANCES_MI = [10, 25, 50, 100, 200, 0]; // 0 = any distance
  var DEFAULT_MAX_MILES = 50;

  function defaults() {
    return {
      theme: "system",
      spotTypes: { boat_ramp: "ok", boat_carry_in: "ok", shore_fishing: "ok" },
      species: [],
      maxMiles: DEFAULT_MAX_MILES,
    };
  }

  function sanitizeTheme(v) {
    return THEMES.indexOf(v) >= 0 ? v : "system";
  }

  function sanitizeSpotTypes(raw) {
    var out = defaults().spotTypes;
    if (raw && typeof raw === "object") {
      SPOT_TYPES.forEach(function (t) {
        if (LEVELS.indexOf(raw[t]) >= 0) out[t] = raw[t];
      });
    }
    return out;
  }

  // `allowed` (optional) restricts to known species names; unknown or
  // non-string entries are dropped rather than trusted.
  function sanitizeSpecies(raw, allowed) {
    if (!Array.isArray(raw)) return [];
    var seen = {};
    var out = [];
    raw.forEach(function (s) {
      if (typeof s !== "string") return;
      var name = s.trim().toUpperCase();
      if (!name || seen[name]) return;
      if (allowed && allowed.indexOf(name) < 0) return;
      seen[name] = true;
      out.push(name);
    });
    return out.sort();
  }

  // 0 means "any distance", so an absent/blank/non-numeric stored value must
  // NOT coerce to 0 (Number(null) === 0): a fresh visitor gets the default.
  function sanitizeMaxMiles(v) {
    if (typeof v !== "number" && typeof v !== "string") return DEFAULT_MAX_MILES;
    if (typeof v === "string" && v.trim() === "") return DEFAULT_MAX_MILES;
    var n = Number(v);
    return DISTANCES_MI.indexOf(n) >= 0 ? n : DEFAULT_MAX_MILES;
  }

  function defaultStorage() {
    try {
      return typeof localStorage !== "undefined" ? localStorage : null;
    } catch (e) {
      return null;
    }
  }

  function readJson(storage, key) {
    try {
      var raw = storage.getItem(key);
      return raw === null || raw === undefined ? null : JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  function load(storage, allowedSpecies) {
    storage = storage || defaultStorage();
    if (!storage) return defaults();
    var theme = null;
    try {
      theme = storage.getItem(KEYS.theme);
    } catch (e) {
      theme = null;
    }
    return {
      theme: sanitizeTheme(theme),
      spotTypes: sanitizeSpotTypes(readJson(storage, KEYS.spotTypes)),
      species: sanitizeSpecies(readJson(storage, KEYS.species), allowedSpecies),
      maxMiles: sanitizeMaxMiles(readJson(storage, KEYS.maxMiles)),
    };
  }

  // Saves only the sanitized form, so a bad value can never be persisted.
  function save(storage, prefs, allowedSpecies) {
    storage = storage || defaultStorage();
    if (!storage) return false;
    try {
      storage.setItem(KEYS.theme, sanitizeTheme(prefs.theme));
      storage.setItem(KEYS.spotTypes, JSON.stringify(sanitizeSpotTypes(prefs.spotTypes)));
      storage.setItem(KEYS.species, JSON.stringify(sanitizeSpecies(prefs.species, allowedSpecies)));
      storage.setItem(KEYS.maxMiles, JSON.stringify(sanitizeMaxMiles(prefs.maxMiles)));
      return true;
    } catch (e) {
      return false;
    }
  }

  function applyTheme(doc, theme) {
    var t = sanitizeTheme(theme);
    if (t === "system") doc.documentElement.removeAttribute("data-theme");
    else doc.documentElement.setAttribute("data-theme", t);
    return t;
  }

  // "Avoid" removes a spot type from recommendations; "prefer" is only a
  // tiebreaker (see recommend.js) - it never excludes anything.
  function isSpotTypeAllowed(prefs, type) {
    return prefs.spotTypes[type] !== "avoid";
  }

  function hasAnyPreference(prefs) {
    var d = defaults();
    return (
      prefs.species.length > 0 ||
      SPOT_TYPES.some(function (t) { return prefs.spotTypes[t] !== d.spotTypes[t]; }) ||
      prefs.maxMiles !== d.maxMiles
    );
  }

  return {
    KEYS: KEYS, SPOT_TYPES: SPOT_TYPES, LEVELS: LEVELS, THEMES: THEMES, DISTANCES_MI: DISTANCES_MI,
    defaults: defaults, load: load, save: save, applyTheme: applyTheme,
    sanitizeTheme: sanitizeTheme, sanitizeSpotTypes: sanitizeSpotTypes,
    sanitizeSpecies: sanitizeSpecies, sanitizeMaxMiles: sanitizeMaxMiles,
    isSpotTypeAllowed: isSpotTypeAllowed, hasAnyPreference: hasAnyPreference,
  };
});
