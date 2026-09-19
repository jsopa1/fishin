// Deterministic, disclosed ranking for the Recommended screen (V4 Phase 4).
//
// This runs in the visitor's browser on purpose: the server publishes one
// non-personal feed (ui/v4_recommend_feed.py) and the visitor's location, saved
// spots and Profile preferences never leave the device (DECISIONS #047/#049).
//
// It is NOT a catch prediction and never says so. It orders spots by a fixed,
// lexicographic key - there are no weights to tune and no randomness - and the
// same inputs always give the same output (webapp/tests/test_recommend_js.py
// runs it under Node against fixed vectors).
//
// Sort key, in priority order (each only breaks ties in the one before):
//   1. how many species are inside their documented temperature range now
//      (your target species if you set any, otherwise all documented species;
//      spawning-range matches never count - many Wisconsin seasons are closed)
//   2. how many of those are Confirmed (survey / sighting) rather than Likely
//   3. spot type marked "Prefer" in the Profile
//   4. temperature reading quality: real > estimated > air-temperature proxy
//   5. distance, nearest first (only when location is known)
//   6. waterbody name, facility name, coordinates - a final stable tiebreak
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.FishinRecommend = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var KM_PER_MILE = 1.609344;
  var TYPE_PLURAL = { boat_ramp: "boat launches", boat_carry_in: "carry-ins", shore_fishing: "shore spots" };
  var LADDER_MILES = [50, 100, 200]; // then statewide
  var MIN_RESULTS = 5;               // fewer candidates than this inside the radius -> widen it
  var DISPLAY = 10;
  var MAX_SAVED = 20;
  var QUALITY_RANK = { real: 2, estimated: 1, proxy: 0 };
  var SAVED_MATCH_DEG = 0.0002;      // feed coordinates are rounded to 5 decimals

  function haversineKm(lat1, lon1, lat2, lon2) {
    var r = 6371.0088, toRad = Math.PI / 180;
    var dLat = (lat2 - lat1) * toRad, dLon = (lon2 - lon1) * toRad;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * r * Math.asin(Math.sqrt(a));
  }

  function qualityRank(q) { return q in QUALITY_RANK ? QUALITY_RANK[q] : -1; }

  function cmpStr(a, b) { a = a || ""; b = b || ""; return a < b ? -1 : a > b ? 1 : 0; }

  // Species -> {tier} in window, optionally restricted to a target set.
  function inRange(spot, targetSet) {
    var out = [];
    (spot.a || []).forEach(function (e) {
      if (!targetSet || targetSet[e[0]]) out.push({ species: e[0], tier: e[1] === "c" ? "confirmed" : "likely" });
    });
    out.sort(function (x, y) {
      return (x.tier === y.tier ? 0 : x.tier === "confirmed" ? -1 : 1) || cmpStr(x.species, y.species);
    });
    return out;
  }

  // Smallest distance (degrees F) from a documented window, among species
  // currently outside it; used only when nothing is in range anywhere.
  function nearestOutside(spot, targetSet) {
    var best = null;
    (spot.i || []).forEach(function (e) {
      if (targetSet && !targetSet[e[0]]) return;
      if (best === null || e[2] < best.distanceF || (e[2] === best.distanceF && e[0] < best.species)) {
        best = { species: e[0], distanceF: e[2] };
      }
    });
    return best;
  }

  function toSet(list) {
    var set = {};
    (list || []).forEach(function (s) { set[s] = true; });
    return set;
  }

  function radiusRungsKm(maxMiles, hasLocation) {
    if (!hasLocation || !maxMiles) return [Infinity];
    var miles = [maxMiles].concat(LADDER_MILES.filter(function (m) { return m > maxMiles; }));
    return miles.map(function (m) { return m * KM_PER_MILE; }).concat([Infinity]);
  }

  function annotate(spot, loc) {
    return {
      spot: spot,
      distanceKm: loc ? haversineKm(loc.lat, loc.lon, spot.lat, spot.lon) : null,
    };
  }

  function compare(a, b) {
    return (
      (b.k1 - a.k1) ||
      (b.k2 - a.k2) ||
      (b.k3 - a.k3) ||
      (b.k4 - a.k4) ||
      (a.distanceKm !== null && b.distanceKm !== null ? a.distanceKm - b.distanceKm : 0) ||
      cmpStr(a.spot.w, b.spot.w) || cmpStr(a.spot.n, b.spot.n) ||
      (a.spot.lat - b.spot.lat) || (a.spot.lon - b.spot.lon)
    );
  }

  function score(item, mode, targetSet, prefs) {
    var spot = item.spot;
    var counted = inRange(spot, mode === "targets" ? targetSet : null);
    var nearest = mode === "closest" ? nearestOutside(spot, targetSet && hasWindowFor(item, targetSet) ? targetSet : null) : null;
    item.counted = counted;
    item.nearest = nearest;
    item.k1 = mode === "closest" ? (nearest ? -nearest.distanceF : -1e9) : counted.length;
    item.k2 = mode === "closest" ? 0 : counted.filter(function (c) { return c.tier === "confirmed"; }).length;
    item.k3 = prefs.spotTypes && prefs.spotTypes[spot.t] === "prefer" ? 1 : 0;
    item.k4 = qualityRank(spot.q);
    return item;
  }

  function hasWindowFor(item, targetSet) {
    return (item.spot.i || []).some(function (e) { return targetSet[e[0]]; });
  }

  function chooseMode(cands, targets, targetSet) {
    var targetMiss = false;
    if (targets.length) {
      if (cands.some(function (c) { return inRange(c.spot, targetSet).length > 0; })) {
        return { mode: "targets", targetMiss: false };
      }
      targetMiss = true;
    }
    if (cands.some(function (c) { return (c.spot.a || []).length > 0; })) {
      return { mode: "all", targetMiss: targetMiss };
    }
    return { mode: "closest", targetMiss: targetMiss };
  }

  function findSavedInFeed(feedSpots, s) {
    var best = null, bestD = Infinity;
    feedSpots.forEach(function (sp) {
      var dLat = Math.abs(sp.lat - s.lat), dLon = Math.abs(sp.lon - s.lon);
      if (dLat < SAVED_MATCH_DEG && dLon < SAVED_MATCH_DEG) {
        var d = dLat + dLon + (s.name && sp.n !== s.name ? 1 : 0);
        if (d < bestD) { bestD = d; best = sp; }
      }
    });
    return best;
  }

  function sameSpot(a, b) {
    return Math.abs(a.lat - b.lat) < SAVED_MATCH_DEG && Math.abs(a.lon - b.lon) < SAVED_MATCH_DEG && a.n === b.n;
  }

  function spotUrl(spot) {
    return "/spot?lat=" + encodeURIComponent(spot.lat) + "&lon=" + encodeURIComponent(spot.lon) +
      "&name=" + encodeURIComponent(spot.n || "");
  }

  function card(item) {
    var sp = item.spot;
    return {
      name: sp.n, water: sp.w, county: sp.c, type: sp.t, quality: sp.q || null, tempC: sp.v === undefined ? null : sp.v,
      count: item.counted.length,
      confirmed: item.counted.filter(function (c) { return c.tier === "confirmed"; }).length,
      inRange: item.counted,
      spawning: sp.s || [],
      nearest: item.nearest,
      distanceKm: item.distanceKm,
      url: spotUrl(sp),
    };
  }

  function disclosure(meta, prefs) {
    var subject = meta.mode === "targets" ? "how many of your target species" : "how many species";
    var lines = [
      "Ranked by " + subject + " are inside their documented temperature range right now, then " +
      "evidence strength, spot-type preference, reading quality and distance. " +
      "This is not a prediction of catch success.",
    ];
    var applied = [];
    if (meta.preferencesApplied.species.length) applied.push("target species: " + meta.preferencesApplied.species.length + " selected");
    var plural = function (t) { return TYPE_PLURAL[t] || t; };
    if (meta.preferencesApplied.preferTypes.length) applied.push("preferring " + meta.preferencesApplied.preferTypes.map(plural).join(", "));
    if (meta.preferencesApplied.avoidTypes.length) applied.push("avoiding " + meta.preferencesApplied.avoidTypes.map(plural).join(", "));
    lines.push(applied.length ? "Your Profile preferences applied: " + applied.join(", ") + "." : "No Profile preferences set, so every species and spot type counts equally.");
    if (meta.rankOnly) {
      lines.push("Your filters decide which spots are listed; preferences only change their order.");
      if (!meta.locationKnown) lines.push("Location is off, so distance is not used.");
    } else if (!meta.locationKnown) lines.push("Location is off, so distance is not used and spots from across Wisconsin are shown.");
    else if (meta.radiusMiles === null) lines.push("Showing spots from across Wisconsin (nothing close enough within your travel distance).");
    else lines.push("Showing spots within " + meta.radiusMiles + " miles.");
    if (meta.targetMiss) lines.push("None of your target species are in range at any spot right now, so spots are ranked by all documented species instead.");
    if (meta.mode === "closest") lines.push("No species is inside its documented range at any spot right now, so spots are ranked by how close a species is to its range.");
    return lines.join(" ");
  }

  // feed: [{n,w,c,t,lat,lon,q,a,s,i}]
  // ctx:  {prefs, location:{lat,lon}|null, saved:[{lat,lon,name,...}], limit}
  function rank(feed, ctx) {
    ctx = ctx || {};
    var prefs = ctx.prefs || { spotTypes: {}, species: [], maxMiles: 50 };
    var loc = ctx.location && isFinite(ctx.location.lat) && isFinite(ctx.location.lon) ? ctx.location : null;
    var limit = ctx.limit || DISPLAY;
    var targets = prefs.species || [];
    var targetSet = toSet(targets);

    // rankOnly (Explore): the visitor has already chosen which spots to look at
    // with explicit filters or a search, so preferences may only ORDER them -
    // never hide them - and the travel radius does not apply.
    var rankOnly = !!ctx.rankOnly;
    var allowed = feed.filter(function (sp) { return rankOnly || !(prefs.spotTypes && prefs.spotTypes[sp.t] === "avoid"); })
      .map(function (sp) { return annotate(sp, loc); });

    var rungs = rankOnly ? [Infinity] : radiusRungsKm(prefs.maxMiles, !!loc), cands = allowed, radiusMiles = null;
    for (var r = 0; r < rungs.length; r++) {
      var inside = allowed.filter(function (c) { return c.distanceKm === null || c.distanceKm <= rungs[r]; });
      if (inside.length >= MIN_RESULTS || r === rungs.length - 1) {
        cands = inside;
        radiusMiles = rungs[r] === Infinity ? null : Math.round(rungs[r] / KM_PER_MILE);
        break;
      }
    }

    var picked = chooseMode(cands, targets, targetSet);
    var tset = picked.mode === "targets" || (picked.mode === "closest" && targets.length) ? targetSet : null;
    cands.forEach(function (c) { score(c, picked.mode, tset, prefs); });
    cands.sort(compare);

    // Saved spots: same key, no radius filter, and "avoid" does not hide a spot
    // the visitor chose to save themselves.
    var savedItems = [];
    (ctx.saved || []).slice(0, MAX_SAVED).forEach(function (s) {
      var sp = findSavedInFeed(feed, s) || { n: s.name, w: s.water, c: s.county, t: null, lat: Number(s.lat), lon: Number(s.lon), q: null, a: [], s: [], i: [] };
      savedItems.push(score(annotate(sp, loc), picked.mode, tset, prefs));
    });
    savedItems.sort(compare);

    var recommended = cands.filter(function (c) {
      return !savedItems.some(function (s) { return sameSpot(s.spot, c.spot); });
    }).slice(0, limit);

    var meta = {
      mode: picked.mode,
      targetMiss: picked.targetMiss,
      locationKnown: !!loc,
      rankOnly: rankOnly,
      radiusMiles: radiusMiles,
      candidateCount: cands.length,
      preferencesApplied: {
        species: targets.slice(),
        preferTypes: Object.keys(prefs.spotTypes || {}).filter(function (t) { return prefs.spotTypes[t] === "prefer"; }).sort(),
        avoidTypes: Object.keys(prefs.spotTypes || {}).filter(function (t) { return prefs.spotTypes[t] === "avoid"; }).sort(),
      },
    };
    return {
      saved: savedItems.map(card),
      recommended: recommended.map(card),
      disclosure: disclosure(meta, prefs),
      meta: meta,
    };
  }

  var TYPE_LABEL = { boat_ramp: "Boat launch", boat_carry_in: "Carry-in", shore_fishing: "Shore spot" };
  var QUALITY_TAG = { real: ["real", "real measurement"], estimated: ["estimated", "estimated"], proxy: ["proxy", "air-temperature proxy"] };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function title(s) {
    return String(s).toLowerCase().replace(/(^|[^a-z])([a-z])/g, function (m, pre, c) { return pre + c.toUpperCase(); });
  }

  // One card layout for every list that shows ranked spots (Recommended, Explore),
  // so a spot reads the same wherever it appears. Says only what the feed says:
  // wording is "in range now", never "likely to bite" (DECISIONS #005).
  function cardHtml(c) {
    var sub = [c.water ? esc(c.water) + (c.county ? " (" + esc(c.county) + ")" : "") : "", TYPE_LABEL[c.type] || ""]
      .filter(Boolean).join(" &middot; ");

    // The three numbers people scan for, big and first. How much to trust the
    // temperature is stated in words under it, not in a coloured badge.
    function metric(num, unit, label, sub2, cls) {
      return '<div class="card-metric ' + cls + '"><span class="card-metric-num">' + num + (unit ? '<small>' + unit + "</small>" : "") + "</span>" +
        '<span class="card-metric-label">' + label + "</span>" + (sub2 ? '<span class="card-metric-sub">' + sub2 + "</span>" : "") + "</div>";
    }
    var metrics = [];
    metrics.push(metric(c.count, "", "species in range now", c.count > 0 ? c.confirmed + " confirmed" : "", "metric-range"));
    if (c.tempC !== null && c.tempC !== undefined) {
      var tLabel = c.quality === "proxy" ? "air-temperature proxy" : c.quality === "estimated" ? "estimated water temp" : "water temp";
      metrics.push(metric(Math.round(c.tempC * 9 / 5 + 32), "&deg;F", tLabel, "", "metric-temp metric-" + (c.quality || "none")));
    } else {
      metrics.push(metric("&ndash;", "", "no temperature reading", "", "metric-temp metric-none"));
    }
    if (c.distanceKm !== null && c.distanceKm !== undefined) {
      metrics.push(metric(Math.round(c.distanceKm / KM_PER_MILE), "mi", "away", "", "metric-away"));
    }

    var line;
    if (c.count > 0) {
      line = c.inRange.slice(0, 4).map(function (e) {
        var confirmed = e.tier === "confirmed";
        return '<span class="card-sp ' + (confirmed ? "sp-confirmed" : "sp-likely") + '" title="' + (confirmed ? "Confirmed by survey or sighting" : "Likely present (documented, not surveyed)") + '">' +
          esc(title(e.species)) + (confirmed ? '<svg class="icon" aria-hidden="true"><use href="#icon-check-circle"/></svg><span class="sr-only"> (confirmed)</span>' : '<span class="sr-only"> (likely)</span>') + "</span>";
      }).join("") + (c.inRange.length > 4 ? '<span class="card-sp-more">+' + (c.inRange.length - 4) + " more</span>" : "");
      line = '<p class="rec-line card-species">' + line + "</p>";
    } else if (c.nearest) {
      line = '<p class="rec-line">Nothing is in range right now. Closest to its range: <strong>' + esc(title(c.nearest.species)) + "</strong>, " + c.nearest.distanceF + "&deg;F outside it.</p>";
    } else if (!c.quality) {
      line = '<p class="rec-line">No current conditions are available for this spot.</p>';
    } else {
      line = '<p class="rec-line">No documented species are in range here right now.</p>';
    }
    var note = c.spawning && c.spawning.length
      ? '<p class="rec-note">Also in a spawning range: ' + esc(c.spawning.slice(0, 3).map(title).join(", ")) + " &mdash; check regulations before fishing.</p>" : "";

    return '<a class="list-card" href="' + esc(c.url) + '">' +
      '<p class="list-card-title">' + esc(c.name) + '</p>' +
      '<p class="list-card-sub"><svg class="icon" aria-hidden="true"><use href="#icon-map-pin"/></svg> ' + sub + "</p>" +
      '<div class="card-metrics">' + metrics.join("") + "</div>" +
      line + note +
      '<span class="list-card-link">Open spot report &rarr;</span></a>';
  }

  // Alphabetical order for Explore's "A-Z" option; the alternative to `rank`.
  function sortAlphabetical(spots) {
    // Case-insensitive first: WDNR names come in mixed and ALL-CAPS forms, and a
    // code-point sort would put "CHEROKEE PARK" ahead of "Crystal Lake".
    var fold = function (v) { return (v || "").toLowerCase(); };
    return spots.slice().sort(function (a, b) {
      return cmpStr(fold(a.w), fold(b.w)) || cmpStr(fold(a.n), fold(b.n)) ||
        cmpStr(a.w, b.w) || cmpStr(a.n, b.n) || (a.lat - b.lat) || (a.lon - b.lon);
    });
  }

  return {
    rank: rank, cardHtml: cardHtml, sortAlphabetical: sortAlphabetical, haversineKm: haversineKm,
    KM_PER_MILE: KM_PER_MILE, TYPE_PLURAL: TYPE_PLURAL, MIN_RESULTS: MIN_RESULTS, DISPLAY: DISPLAY, MAX_SAVED: MAX_SAVED,
  };
});
