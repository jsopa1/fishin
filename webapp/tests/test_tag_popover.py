"""The tag popover ("Confirmed", "Likely", "estimated", ...) must open next to its tag
wherever the page is scrolled, and be legible in dark mode.

The bug: the popover is position: fixed (viewport coordinates) but the script added the
page scroll offset, so on a long page like the spot page it opened off-screen and the tag
looked dead. Verified live in a browser after the fix; these tests keep it from returning.

Run: python -m pytest webapp/tests/test_tag_popover.py
"""

import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"
JS = (STATIC / "tags-explainer.js").read_text(encoding="utf-8")
CSS = (STATIC / "style.css").read_text(encoding="utf-8")


class PopoverPositioning(unittest.TestCase):
    def test_css_is_fixed_so_the_script_must_use_viewport_coordinates(self):
        self.assertRegex(CSS, r"\.tag-popover \{\s*position: fixed;")
        body = JS[JS.index("function showPopoverFor"):JS.index("function wireExplainable")]
        self.assertNotIn("scrollY", body)
        self.assertNotIn("pageYOffset", body)

    def test_it_flips_above_the_tag_and_stays_inside_the_viewport(self):
        body = JS[JS.index("function showPopoverFor"):JS.index("function wireExplainable")]
        self.assertIn("rect.top - h", body)          # flip above when there is no room below
        self.assertIn("vw - w - 8", body)            # clamp to the right edge
        self.assertIn("Math.max(8", body)            # and to the left/top

    def test_it_closes_on_scroll_click_and_escape(self):
        self.assertIn('addEventListener("scroll", hidePopover', JS)
        self.assertIn('addEventListener("click", hidePopover', JS)
        self.assertIn('"Escape"', JS)

    def test_dynamically_added_tags_can_be_wired(self):
        self.assertIn("window.FishinTags", JS)


class PopoverDarkMode(unittest.TestCase):
    def test_it_has_an_edge_and_a_lighter_surface_in_both_dark_modes(self):
        self.assertRegex(CSS, r"\.tag-popover \{[^}]*border: 1px solid")
        self.assertIn(':root[data-theme="dark"] .tag-popover {', CSS)
        self.assertIn(':root:not([data-theme="light"]) .tag-popover {', CSS)


def contrast(fg, bg):
    def lum(h):
        h = h.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    a, b = lum(fg), lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class DarkTagContrast(unittest.TestCase):
    """Every tag colour pair, in the dark tokens, meets WCAG AA (4.5:1)."""

    def tokens(self):
        block = CSS[CSS.index(':root[data-theme="dark"] {'):]
        block = block[:block.index("}")]
        return dict(re.findall(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block))

    def test_confirmed_likely_and_the_reading_tags_are_readable(self):
        t = self.tokens()
        pairs = {
            "confirmed/real": (t["--survey"], t["--survey-bg"]),
            "likely/estimated": (t["--stocking"], t["--stocking-bg"]),
            "agency tier": (t["--water"], t["--water-bg"]),
            "proxy": (t["--gray-700"], t["--gray-100"]),
        }
        for name, (fg, bg) in pairs.items():
            self.assertGreaterEqual(contrast(fg, bg), 4.5, name)

    def test_the_popover_text_is_readable_on_its_dark_surface(self):
        self.assertGreaterEqual(contrast("#eef1f5", "#2a3140"), 7)


if __name__ == "__main__":
    unittest.main()
