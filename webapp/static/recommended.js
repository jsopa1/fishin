// Recommended screen glue (V4 Phase 4). Loads the non-personal feed, ranks it in
// the browser with recommend.js using the Profile preferences, saved spots and
// (only if the visitor allows it) location - none of which are ever sent to the
// server. The location is held in memory for this page view and not stored.
(function () {
  "use strict";
  var P = window.FishinPrefs, R = window.FishinRecommend;
  if (!P || !R) return;

  var TYPE_LABEL = { boat_ramp: "Boat launch", boat_carry_in: "Carry-in", shore_fishing: "Shore spot" };
  var els = {
    loading: document.getElementById("rec-loading"),
    status: document.getElementById("rec-status"),
    prefs: document.getElementById("rec-prefs"),
    locate: document.getElementById("rec-locate"),
    savedWrap: document.getElementById("saved-section"),
    savedList: document.getElementById("saved-list"),
    recHead: document.getElementById("rec-list-heading"),
    recList: document.getElementById("rec-list"),
    disclosure: document.getElementById("rec-disclosure"),
  };
  var state = { feed: null, location: null, locating: false };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function loadSaved() {
    try {
      var raw = JSON.parse(localStorage.getItem("fishin.saved.v1"));
      return Array.isArray(raw) ? raw.filter(function (s) { return s && isFinite(s.lat) && isFinite(s.lon); }) : [];
    } catch (e) { return []; }
  }

  function prefsSummary(prefs) {
    if (!P.hasAnyPreference(prefs)) {
      return 'No preferences set yet. <a href="/profile">Choose your fish and spot types</a> to tailor this list.';
    }
    var bits = [];
    if (prefs.species.length) bits.push(prefs.species.length + " target species");
    var prefer = P.SPOT_TYPES.filter(function (t) { return prefs.spotTypes[t] === "prefer"; }).map(function (t) { return TYPE_LABEL[t].toLowerCase() + "s"; });
    var avoid = P.SPOT_TYPES.filter(function (t) { return prefs.spotTypes[t] === "avoid"; }).map(function (t) { return TYPE_LABEL[t].toLowerCase() + "s"; });
    if (prefer.length) bits.push("prefer " + prefer.join(", "));
    if (avoid.length) bits.push("avoid " + avoid.join(", "));
    bits.push(prefs.maxMiles ? "within " + prefs.maxMiles + " miles" : "any distance");
    return "Using your preferences: " + esc(bits.join(" · ")) + '. <a href="/profile">Change</a>';
  }

  function render() {
    if (!state.feed) return;
    var prefs = P.load(null);
    var result = R.rank(state.feed, { prefs: prefs, location: state.location, saved: loadSaved() });

    els.loading.hidden = true;
    els.prefs.innerHTML = prefsSummary(prefs);
    els.disclosure.textContent = result.disclosure;

    els.savedList.innerHTML = result.saved.length
      ? result.saved.map(R.cardHtml).join("")
      : '<p class="rec-empty">No saved spots yet. Open any spot and tap &ldquo;Save this spot&rdquo;.</p>';

    els.recHead.hidden = false;
    els.recList.innerHTML = result.recommended.length
      ? result.recommended.map(R.cardHtml).join("")
      : '<p class="rec-empty">No spots match right now. Try widening your travel distance in your <a href="/profile">Profile</a>, or <a href="/map">explore the map</a>.</p>';

    els.status.textContent = state.location ? "Using your location on this device." : "Turn on location to sort by distance.";
    if (window.FishinTags) window.FishinTags.wire(document.getElementById("recommended"));
  }

  function locate() {
    if (!navigator.geolocation || state.locating) {
      if (!navigator.geolocation) els.status.textContent = "Location isn't available in this browser.";
      return;
    }
    state.locating = true;
    els.status.textContent = "Finding your location…";
    navigator.geolocation.getCurrentPosition(function (pos) {
      state.locating = false;
      state.location = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      render();
    }, function () {
      state.locating = false;
      els.status.textContent = "Couldn't get your location, so distance isn't used.";
    }, { enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 });
  }

  els.locate.addEventListener("click", locate);

  // Location is only read on a tap - or silently if the browser already holds a
  // grant from an earlier visit, which is the visitor's own earlier choice.
  try {
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: "geolocation" }).then(function (p) { if (p.state === "granted") locate(); });
    }
  } catch (e) { /* not supported: the button still works */ }

  fetch(window.FISHIN_FEED_URL, { headers: { Accept: "application/json" } })
    .then(function (r) { if (!r.ok) throw new Error("feed " + r.status); return r.json(); })
    .then(function (feed) { state.feed = feed.spots || []; render(); })
    .catch(function () {
      els.loading.textContent = "Current conditions couldn't be loaded. You can still explore the map or your saved spots.";
      var saved = loadSaved();
      if (saved.length) {
        els.savedList.innerHTML = saved.slice(0, 8).map(function (s) {
          return R.cardHtml({ name: s.name, water: s.water, county: s.county, type: null, quality: null, count: 0, inRange: [], spawning: [], nearest: null, distanceKm: null,
            url: "/spot?lat=" + encodeURIComponent(s.lat) + "&lon=" + encodeURIComponent(s.lon) + "&name=" + encodeURIComponent(s.name || "") });
        }).join("");
      }
    });
})();
