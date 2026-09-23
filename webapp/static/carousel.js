// Horizontal card rows, as on AllTrails' home page: swipe on touch screens, and round
// previous/next arrows on wider screens. Each `.row-arrows[data-row="<id>"]` gets two buttons
// that page the row with that id by about one screenful; an arrow is hidden when there is
// nothing further in its direction, rather than shown disabled.
(function () {
  "use strict";
  var rows = [];

  function button(dir, label) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "row-arrow";
    b.setAttribute("aria-label", label);
    b.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#icon-chevron-' + dir + '"/></svg>';
    return b;
  }

  function update(r) {
    var el = r.row, max = el.scrollWidth - el.clientWidth - 2;
    r.prev.hidden = el.scrollLeft <= 2;
    r.next.hidden = el.scrollLeft >= max;
    r.host.hidden = max <= 0;
  }

  function page(el, sign) {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollBy({ left: sign * Math.max(el.clientWidth * 0.9, 240), behavior: reduce ? "auto" : "smooth" });
  }

  document.querySelectorAll(".row-arrows[data-row]").forEach(function (host) {
    var row = document.getElementById(host.dataset.row);
    if (!row) return;
    var r = { host: host, row: row, prev: button("left", "Scroll back"), next: button("right", "Scroll forward") };
    host.appendChild(r.prev);
    host.appendChild(r.next);
    r.prev.addEventListener("click", function () { page(row, -1); });
    r.next.addEventListener("click", function () { page(row, 1); });
    row.addEventListener("scroll", function () { update(r); }, { passive: true });
    rows.push(r);
    update(r);
  });
  window.addEventListener("resize", function () { rows.forEach(update); });

  window.FishinCarousel = { refresh: function () { rows.forEach(update); } };
})();
