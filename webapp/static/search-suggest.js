// Suggestions under the home search box, the way AllTrails' search offers places as you type.
// Built in the browser from the same non-personal feed the ranked rows use (no extra request,
// nothing typed is sent anywhere until the visitor submits). Lakes and rivers first, each
// opening Explore filtered to that water; then individual access points by name. Without the
// feed, or with no match, the box is a plain form that searches Explore on Enter.
(function () {
  "use strict";
  var input = document.getElementById("hero-search-input");
  var list = document.getElementById("hero-suggest");
  if (!input || !list) return;
  var form = input.form;
  var MAX_WATERS = 6, MAX_SPOTS = 3;
  var waters = null, spots = null, items = [], active = -1;

  function title(s) {
    return String(s || "").toLowerCase().replace(/(^|[^a-z'])([a-z])/g, function (m, pre, c) { return pre + c.toUpperCase(); });
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // One suggestion per water name (Explore filters by name), labelled with the county most of its
  // access points give. WDNR's records spell counties inconsistently ("Dane", "DANE", blank).
  function index(feed) {
    var byWater = {};
    spots = [];
    feed.forEach(function (sp) {
      if (sp.w) {
        var key = sp.w.toLowerCase();
        var w = byWater[key] = byWater[key] || { name: sp.w, n: 0, lower: key, counties: {} };
        w.n++;
        var c = String(sp.c || "").trim();
        if (c && c.toLowerCase() !== "null") { c = title(c); w.counties[c] = (w.counties[c] || 0) + 1; }
      }
      if (sp.n) spots.push({ name: sp.n, lower: sp.n.toLowerCase(), water: sp.w, lat: sp.lat, lon: sp.lon });
    });
    waters = Object.keys(byWater).map(function (k) {
      var w = byWater[k], names = Object.keys(w.counties);
      w.county = names.sort(function (a, b) { return w.counties[b] - w.counties[a]; })[0] || "";
      return w;
    });
  }

  function rank(pool, q, limit) {
    var starts = [], words = [], within = [];
    pool.forEach(function (x) {
      var at = x.lower.indexOf(q);
      if (at === 0) starts.push(x);
      else if (at > 0 && /[^a-z0-9]/.test(x.lower.charAt(at - 1))) words.push(x);
      else if (at > 0) within.push(x);
    });
    var by = function (a, b) { return (b.n || 0) - (a.n || 0) || (a.lower < b.lower ? -1 : 1); };
    return starts.sort(by).concat(words.sort(by), within.sort(by)).slice(0, limit);
  }

  function close() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    active = -1;
  }

  function setActive(i) {
    var opts = list.querySelectorAll('[role="option"]');
    opts.forEach(function (o, k) { o.setAttribute("aria-selected", k === i ? "true" : "false"); });
    active = i;
    if (i >= 0 && opts[i]) {
      input.setAttribute("aria-activedescendant", opts[i].id);
      opts[i].scrollIntoView({ block: "nearest" });
    } else input.removeAttribute("aria-activedescendant");
  }

  function show() {
    var q = input.value.trim().toLowerCase();
    if (!waters || q.length < 2) { close(); return; }
    var w = rank(waters, q, MAX_WATERS), s = rank(spots, q, MAX_SPOTS);
    items = w.map(function (x) {
      return { href: form.action + "?waterbody=" + encodeURIComponent(x.name), main: title(x.name), sub: [x.county, x.n + (x.n === 1 ? " access point" : " access points")].filter(Boolean).join(" · "), icon: "waves" };
    }).concat(s.map(function (x) {
      return { href: "/spot?lat=" + encodeURIComponent(x.lat) + "&lon=" + encodeURIComponent(x.lon) + "&name=" + encodeURIComponent(x.name), main: x.name, sub: title(x.water), icon: "map-pin" };
    }));
    if (!items.length) { close(); return; }
    list.innerHTML = items.map(function (it, i) {
      return '<li role="option" id="hero-suggest-' + i + '" aria-selected="false" data-i="' + i + '">' +
        '<svg class="icon" aria-hidden="true"><use href="#icon-' + it.icon + '"/></svg>' +
        '<span><span class="suggest-main">' + esc(it.main) + '</span><span class="suggest-sub">' + esc(it.sub) + "</span></span></li>";
    }).join("");
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    active = -1;
  }

  function go(i) { if (items[i]) window.location.href = items[i].href; }

  input.addEventListener("input", show);
  input.addEventListener("focus", show);
  input.addEventListener("keydown", function (e) {
    if (list.hidden) return;
    var n = items.length;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((active + 1) % n); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive(active <= 0 ? n - 1 : active - 1); }
    else if (e.key === "Enter" && active >= 0) { e.preventDefault(); go(active); }
    else if (e.key === "Escape") { close(); }
  });
  list.addEventListener("mousedown", function (e) { e.preventDefault(); }); // keep focus in the box
  list.addEventListener("click", function (e) {
    var li = e.target.closest("[data-i]");
    if (li) go(Number(li.dataset.i));
  });
  document.addEventListener("click", function (e) { if (!form.contains(e.target)) close(); });

  if (window.FishinFeed) index(window.FishinFeed);
  document.addEventListener("fishin:feed", function (e) {
    index(e.detail || []);
    if (document.activeElement === input) show();
  });
})();
