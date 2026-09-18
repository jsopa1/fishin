// Explains the evidence-tier tags (survey_confirmed, proxy, confidence-*,
// etc.) at the point of use, without touching a single template. Every
// `.tag` element already carries its evidentiary meaning as a CSS class
// -- this just reads that class back and shows what it means in plain
// English. Vanilla JS, no framework, no new dependency.
//
// The same popover also drives any element carrying a `data-explain`
// attribute directly (e.g. a species name or an activity badge on the
// spot dashboard) -- one shared click/keyboard/dismiss mechanism instead
// of a second UI pattern for per-instance, server-rendered text.
(function () {
  "use strict";

  var EXPLANATIONS = {
    survey_confirmed: "An actual WDNR fisheries survey observed this species in this water — the strongest evidence this site shows.",
    stocking_only: "WDNR has stocked this species here. Real positive evidence, but not a complete species list — a water can hold species that were never stocked.",
    real: "From an actual temperature sensor (USGS gauge, NOAA buoy, or WDNR reading) — not estimated.",
    estimated: "Interpolated from nearby real sensor readings, not measured at this exact spot.",
    proxy: "A regional air-temperature stand-in, used only when no water-temperature reading is available nearby. Air and water temperature can diverge, especially in spring and fall.",
    no_data: "No real, estimated, or proxy temperature reading is currently available here.",
    evidence: "How strong the source data is behind this specific statement.",
    "evidence-confirmed": "A WDNR fisheries survey or a real, dated citizen sighting actually documented this species here.",
    "evidence-likely": "Positive but indirect evidence only: stocked here, or recorded elsewhere in this county. Not proof it is here now.",
    "tier-well-established": "Two or more independent sources agree on this statement.",
    "tier-agency-tier": "Stated by a state or federal fisheries agency, or found in one solid peer-reviewed study.",
    "tier-single-source-speculative": "Only one source, and not specific to this species or water - use cautiously.",
    "reg-stated": "A Wisconsin rule that applies to this bait, quoted from the agency source below.",
    "reg-unreviewed": "Wisconsin rules for this bait have not been reviewed here. This is not a statement that it is allowed.",
  };

  function explanationFor(tagEl) {
    var classes = tagEl.className.split(/\s+/);
    for (var i = 0; i < classes.length; i++) {
      var c = classes[i];
      if (c === "tag" || c === "") continue;
      if (c.indexOf("confidence-") === 0) {
        var level = c.replace("confidence-", "");
        return "How confident this estimate is, based on how close and recent the nearby real readings were (" + level + " confidence).";
      }
      if (EXPLANATIONS[c]) return EXPLANATIONS[c];
    }
    return null;
  }

  var popover = null;
  function ensurePopover() {
    if (popover) return popover;
    popover = document.createElement("div");
    popover.className = "tag-popover";
    popover.hidden = true;
    popover.setAttribute("role", "tooltip");
    document.body.appendChild(popover);
    return popover;
  }

  function hidePopover() {
    if (popover) popover.hidden = true;
  }

  function showPopoverFor(tagEl, text) {
    var pop = ensurePopover();
    pop.textContent = text;
    pop.hidden = false;
    var rect = tagEl.getBoundingClientRect();
    var top = rect.bottom + window.scrollY + 6;
    var left = rect.left + window.scrollX;
    // Measure after making visible so offsetWidth is real, then clamp to viewport.
    var maxLeft = window.scrollX + document.documentElement.clientWidth - pop.offsetWidth - 8;
    if (left > maxLeft) left = Math.max(8, maxLeft);
    pop.style.top = top + "px";
    pop.style.left = left + "px";
  }

  function wireExplainable(el, text) {
    // A button-worthy element is often nested inside a card/row <a>
    // (e.g. the browse and explore list views) -- without preventDefault
    // the click still follows that link even though this listener runs
    // first.
    if (el.tagName !== "BUTTON") {
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
    }
    var baseLabel = el.getAttribute("aria-label") || el.textContent.trim();
    el.setAttribute("aria-label", baseLabel + ". " + text);
    el.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      showPopoverFor(el, text);
    });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        e.stopPropagation();
        showPopoverFor(el, text);
      } else if (e.key === "Escape") {
        hidePopover();
      }
    });
  }

  function wireTags() {
    var tags = document.querySelectorAll(".tag");
    tags.forEach(function (tagEl) {
      var text = explanationFor(tagEl);
      if (!text) return;
      wireExplainable(tagEl, text);
    });
    return tags.length;
  }

  function wireDataExplain() {
    var els = document.querySelectorAll("[data-explain]");
    els.forEach(function (el) {
      var text = el.getAttribute("data-explain");
      if (!text) return;
      wireExplainable(el, text);
    });
    return els.length;
  }

  function wireIntroBanner(tagCount) {
    var banner = document.getElementById("tag-intro-banner");
    var dismiss = document.getElementById("tag-intro-dismiss");
    if (!banner || !dismiss || !tagCount) return;
    var KEY = "fishin.tagsIntroSeen.v1";
    var seen = false;
    try { seen = localStorage.getItem(KEY) === "1"; } catch (e) { seen = false; }
    if (!seen) banner.hidden = false;
    dismiss.addEventListener("click", function () {
      banner.hidden = true;
      try { localStorage.setItem(KEY, "1"); } catch (e) { /* ignore */ }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var tagCount = wireTags();
    var explainCount = wireDataExplain();
    wireIntroBanner(tagCount);
    if (tagCount + explainCount > 0) {
      document.addEventListener("click", hidePopover);
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") hidePopover();
      });
      window.addEventListener("scroll", hidePopover, { passive: true });
    }
  });
})();
