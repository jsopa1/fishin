// Saved spots, shared by every screen: the heart on a spot card and the Save button on a
// spot page read and write the same list, so a spot saved in one place shows as saved in
// the other. Kept in this browser only -- no account, no server -- because for an angler a
// spot is exactly the thing you do not want uploaded. Only the anonymous fact that a save
// happened is counted (navigator.sendBeacon to /events/save), never the coordinates.
(function () {
  "use strict";
  var KEY = "fishin.saved.v1";
  var LIMIT = 200;
  var MATCH_DEG = 0.0002; // card coordinates are rounded to 5 decimals, spot pages are not
  var listeners = [];

  function read() {
    try {
      var raw = JSON.parse(localStorage.getItem(KEY));
      return Array.isArray(raw) ? raw : [];
    } catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, LIMIT))); }
    catch (e) { /* private mode or quota: saving is a convenience, never an error */ }
  }
  function same(s, lat, lon) {
    return Math.abs(Number(s.lat) - lat) < MATCH_DEG && Math.abs(Number(s.lon) - lon) < MATCH_DEG;
  }
  function indexOf(list, lat, lon) {
    lat = Number(lat); lon = Number(lon);
    for (var i = 0; i < list.length; i++) if (same(list[i], lat, lon)) return i;
    return -1;
  }

  function isSaved(lat, lon) { return indexOf(read(), lat, lon) >= 0; }

  // spot: {name, water, county, lat, lon}. Returns true when the spot is now saved.
  function toggle(spot) {
    var list = read();
    var at = indexOf(list, spot.lat, spot.lon);
    var saved;
    if (at >= 0) { list.splice(at, 1); saved = false; }
    else {
      list.unshift({ id: spot.lat + "," + spot.lon, name: spot.name || "", water: spot.water || "", county: spot.county || "", lat: spot.lat, lon: spot.lon });
      saved = true;
      if (navigator.sendBeacon) navigator.sendBeacon("/events/save", new URLSearchParams({ page: window.location.pathname }));
    }
    write(list);
    listeners.forEach(function (fn) { try { fn(); } catch (e) { /* one listener never blocks the rest */ } });
    return saved;
  }

  function spotFrom(el) {
    return { name: el.dataset.name, water: el.dataset.water, county: el.dataset.county, lat: el.dataset.lat, lon: el.dataset.lon };
  }

  // Reflect saved state on every heart inside `root`.
  function paint(root) {
    var list = read();
    (root || document).querySelectorAll(".card-save").forEach(function (btn) {
      var on = indexOf(list, btn.dataset.lat, btn.dataset.lon) >= 0;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.setAttribute("aria-label", (on ? "Remove " : "Save ") + (btn.dataset.name || "this spot") + (on ? " from saved spots" : ""));
    });
  }

  function toast(text) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = text;
    el.hidden = false;
    clearTimeout(toast.t);
    toast.t = setTimeout(function () { el.hidden = true; }, 2400);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".card-save");
    if (!btn) return;
    e.preventDefault();
    var saved = toggle(spotFrom(btn));
    paint(document);
    toast(saved ? "Saved to your spots" : "Removed from your spots");
  });

  window.FishinSaved = {
    list: read, isSaved: isSaved, toggle: toggle, paint: paint, toast: toast,
    onChange: function (fn) { listeners.push(fn); },
  };
})();
