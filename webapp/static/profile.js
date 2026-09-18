// Wires the Profile page to FishinPrefs (prefs.js). Every change is saved to
// this device immediately; nothing is sent anywhere.
(function () {
  "use strict";
  var P = window.FishinPrefs;
  if (!P) return;
  var known = window.FISHIN_SPECIES || [];
  var prefs = P.load(null, known);

  function persist() {
    P.save(null, prefs, known);
    P.applyTheme(document, prefs.theme);
  }

  function markSegment(group, value) {
    group.querySelectorAll(".view-toggle-btn").forEach(function (b) {
      var on = b.getAttribute("data-value") === value;
      b.classList.toggle("active", on);
      b.setAttribute("aria-checked", on ? "true" : "false");
    });
  }

  function render() {
    document.querySelectorAll('[data-pref="theme"]').forEach(function (g) { markSegment(g, prefs.theme); });
    document.querySelectorAll('[data-pref="spot"]').forEach(function (g) { markSegment(g, prefs.spotTypes[g.getAttribute("data-type")]); });
    var dist = document.getElementById("pref-distance");
    if (dist) dist.value = String(prefs.maxMiles);
    document.querySelectorAll('input[data-pref="species"]').forEach(function (c) {
      c.checked = prefs.species.indexOf(c.value) >= 0;
    });
    var count = document.getElementById("species-count");
    if (count) count.textContent = prefs.species.length ? prefs.species.length + " selected." : "None selected.";
  }

  document.querySelectorAll('[data-pref="theme"] .view-toggle-btn').forEach(function (b) {
    b.addEventListener("click", function () { prefs.theme = b.getAttribute("data-value"); persist(); render(); });
  });
  document.querySelectorAll('[data-pref="spot"] .view-toggle-btn').forEach(function (b) {
    b.addEventListener("click", function () {
      var type = b.closest("[data-type]").getAttribute("data-type");
      prefs.spotTypes[type] = b.getAttribute("data-value");
      persist(); render();
    });
  });
  var dist = document.getElementById("pref-distance");
  if (dist) dist.addEventListener("change", function () { prefs.maxMiles = P.sanitizeMaxMiles(dist.value); persist(); render(); });
  document.querySelectorAll('input[data-pref="species"]').forEach(function (c) {
    c.addEventListener("change", function () {
      var chosen = [];
      document.querySelectorAll('input[data-pref="species"]').forEach(function (x) { if (x.checked) chosen.push(x.value); });
      prefs.species = P.sanitizeSpecies(chosen, known);
      persist(); render();
    });
  });
  var clear = document.getElementById("species-clear");
  if (clear) clear.addEventListener("click", function () { prefs.species = []; persist(); render(); });

  render();
})();
