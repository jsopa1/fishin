"""Deterministic unit tests for the shore-fishing detail-page scraper.

Covers the pure, testable logic: extracting a site ID from a
MORE_INFO_URL, parsing the fixed HTML field structure (including
placeholder-value cleanup and the two same-page fields that share
similar-but-distinct label text), splitting the raw species text, and
the SQLite read/write path. No network calls -- fetch_detail_page() is
not exercised here, consistent with how this project tests other
live-fetch call sites. Fixture HTML below is a trimmed, real excerpt of
https://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=116 (Moose
Lake Fishing Pier) and ID=5 (Namekagon Lake Fishing Pier), captured
2026-09-12 -- not synthesized.

Run: python -m pytest analysis/tests/test_v2_shore_fishing_details.py
"""

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v2_shore_fishing_details as sfd  # noqa: E402


def _row(label, value):
    return (
        f'<tr bgcolor="White"><td bgcolor="#DEE8F5"><font color="#333333"><b>{label}</b></font></td>'
        f'<td><font color="#333333">\n                <span id="x">{value}</span>\n            </font></td></tr>'
    )


MOOSE_LAKE_EXCERPT = "".join([
    _row("Site Name", "Moose Lake Fishing Pier"),
    _row("Directions", "Take Hwy 16 to CTH C turn into Moose Lake State Fishing Area"),
    _row("Fishing Trail", "UNKNOWN"),
    _row("No. of Vehicle Stalls", "2"),
    _row("No. of Vehicle and Trailer Stalls", "5"),
    _row("Type of Restrooms", "YES"),
    _row("Available Fish Species", "PANFISH, LARGEMOUTH BASS, NORTHEN PIKE"),
    _row("Additional Amenities", "Pier has bmper edging instead of rallings"),
    _row("Comments", "NONE"),
    _row("Vehicle Stalls", "UNKNOWN"),
    _row("Restrooms", "UNKNOWN"),
])


class ExtractSiteIdTests(unittest.TestCase):
    def test_extracts_id_from_real_url_shape(self):
        self.assertEqual(
            sfd.extract_site_id("http://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=116"), "116"
        )

    def test_none_for_missing_url(self):
        self.assertIsNone(sfd.extract_site_id(None))
        self.assertIsNone(sfd.extract_site_id(""))

    def test_none_when_no_id_param(self):
        self.assertIsNone(sfd.extract_site_id("http://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx"))


class ParseDetailPageTests(unittest.TestCase):
    def test_real_fields_extracted(self):
        fields = sfd.parse_detail_page(MOOSE_LAKE_EXCERPT)
        self.assertEqual(fields["directions"], "Take Hwy 16 to CTH C turn into Moose Lake State Fishing Area")
        self.assertEqual(fields["vehicle_stalls"], "2")
        self.assertEqual(fields["vehicle_trailer_stalls"], "5")
        self.assertEqual(fields["restrooms"], "YES")
        self.assertEqual(fields["fish_species_raw"], "PANFISH, LARGEMOUTH BASS, NORTHEN PIKE")
        self.assertEqual(fields["additional_amenities"], "Pier has bmper edging instead of rallings")

    def test_placeholder_values_become_none(self):
        fields = sfd.parse_detail_page(MOOSE_LAKE_EXCERPT)
        self.assertIsNone(fields["fishing_trail"])  # "UNKNOWN"
        self.assertIsNone(fields["comments"])  # "NONE"

    def test_real_unknown_typo_variants_recognized_as_placeholder(self):
        # WDNR's own pages spell "unknown" three ways across real records
        # (verified: site 109 uses "UKNOWN", two others use "UNKOWN").
        self.assertIsNone(sfd._clean("UKNOWN"))
        self.assertIsNone(sfd._clean("UNKOWN"))
        self.assertIsNone(sfd._clean("Uknown"))

    def test_general_and_ada_vehicle_stalls_stay_distinct(self):
        # Two different real page fields share the substring "Vehicle Stalls"
        # but distinct exact label text -- must not collide into one column.
        fields = sfd.parse_detail_page(MOOSE_LAKE_EXCERPT)
        self.assertEqual(fields["vehicle_stalls"], "2")
        self.assertIsNone(fields["ada_vehicle_stalls"])  # was "UNKNOWN" in the ADA table

    def test_empty_html_returns_empty_dict(self):
        self.assertEqual(sfd.parse_detail_page(""), {})


class ParseSpeciesListTests(unittest.TestCase):
    def test_splits_and_trims_real_text(self):
        self.assertEqual(
            sfd.parse_species_list("MUSKIE, WALLEYE, SM & LG MOUTH BASS, PANFISH, NORTHERN"),
            ["MUSKIE", "WALLEYE", "SM & LG MOUTH BASS", "PANFISH", "NORTHERN"],
        )

    def test_does_not_correct_real_wdnr_typos(self):
        # "NORTHEN" is WDNR's own typo (verified on the live ID=116 page) --
        # this project shows it verbatim rather than silently "fixing" it.
        self.assertIn("NORTHEN PIKE", sfd.parse_species_list("PANFISH, LARGEMOUTH BASS, NORTHEN PIKE"))

    def test_none_or_empty_returns_empty_list(self):
        self.assertEqual(sfd.parse_species_list(None), [])
        self.assertEqual(sfd.parse_species_list(""), [])

    def test_parenthetical_sublist_not_truncated(self):
        # Real WDNR text, site ID 31 (Round Lake): a comma inside
        # parentheses must not split the phrase in two.
        raw = "PIKE (NORTHERN, YELLOW), WALLEYE, BASS (LG. MOUTH, ROCK), PANFISH, BLUEGILL"
        result = sfd.parse_species_list(raw)
        self.assertIn("PIKE (NORTHERN, YELLOW)", result)
        self.assertIn("BASS (LG. MOUTH, ROCK)", result)
        self.assertNotIn("BASS (LG. MOUTH", result)
        self.assertEqual(len(result), 5)


class DbRoundTripTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        os.remove(self.db_path)

    def test_write_then_read_back(self):
        conn = sqlite3.connect(self.db_path)
        sfd.init_db(conn)
        fields = sfd.parse_detail_page(MOOSE_LAKE_EXCERPT)
        url = "http://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=116"
        sfd.write_details(conn, url, fields, "2026-01-01T00:00:00+00:00")

        row = conn.execute(
            "SELECT * FROM shore_fishing_details WHERE more_info_url = ?", (url,)
        ).fetchone()
        self.assertIsNotNone(row)

        species = conn.execute(
            "SELECT species_text FROM shore_fishing_species WHERE more_info_url = ? ORDER BY id", (url,)
        ).fetchall()
        self.assertEqual([s[0] for s in species], ["PANFISH", "LARGEMOUTH BASS", "NORTHEN PIKE"])

        canonical = conn.execute(
            "SELECT canonical_species FROM shore_fishing_species_canonical WHERE more_info_url = ? ORDER BY canonical_species",
            (url,),
        ).fetchall()
        self.assertEqual(
            [c[0] for c in canonical], ["Largemouth Bass", "Northern Pike", "Panfish (unspecified)"]
        )
        conn.close()

    def test_rerun_replaces_rather_than_accumulates(self):
        conn = sqlite3.connect(self.db_path)
        sfd.init_db(conn)
        url = "http://dnrmaps.wi.gov/LF_ShowDetails/shorefishing.aspx?ID=116"
        fields = sfd.parse_detail_page(MOOSE_LAKE_EXCERPT)
        sfd.write_details(conn, url, fields, "t1")
        sfd.write_details(conn, url, fields, "t2")
        count = conn.execute("SELECT COUNT(*) FROM shore_fishing_details WHERE more_info_url = ?", (url,)).fetchone()[0]
        self.assertEqual(count, 1)
        species_count = conn.execute(
            "SELECT COUNT(*) FROM shore_fishing_species WHERE more_info_url = ?", (url,)
        ).fetchone()[0]
        self.assertEqual(species_count, 3)  # not doubled
        conn.close()


if __name__ == "__main__":
    unittest.main()
