"""Spot air-temperature proxy (V4): every spot gets a temperature, honestly labelled.

Runs against a temporary COPY of the committed database so the tracked file is
never modified. No network: the NWS fetch is injected.

Run: python -m pytest ui/tests/test_v4_spot_air_proxy.py
"""

import datetime
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v1_review_data as data  # noqa: E402
import v4_recommend_feed as feed_module  # noqa: E402
import v4_spot_air_proxy as proxy  # noqa: E402


def fake_fetch(temp_c=14.0):
    return lambda lat, lon: (temp_c, "KTEST", datetime.datetime.now(datetime.timezone.utc).isoformat())


class ProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.path = os.path.join(cls.dir, "copy.db")
        shutil.copy(data.find_db_path(), cls.path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def setUp(self):
        self.conn = data.connect(self.path)
        proxy.ensure_table(self.conn)
        self.conn.execute("DELETE FROM spot_air_proxy")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _gap_spots(self, **kw):
        out = []
        for r in self.conn.execute("SELECT latitude, longitude, matched_waterbody_name, matched_county FROM access_points"):
            if data.get_spot_temperature(self.conn, r[0], r[1], r[2], r[3], **kw) is None:
                out.append(r)
        return out

    def test_there_are_gap_spots_and_none_of_them_is_matched_to_a_waterbody(self):
        gaps = self._gap_spots(use_spot_proxy=False)
        self.assertGreater(len(gaps), 100)
        self.assertTrue(all(g[2] is None for g in gaps))

    def test_after_a_refresh_no_spot_is_left_without_a_temperature(self):
        result = proxy.refresh(self.conn, fetch=fake_fetch(), sleep=lambda s: None)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["updated"], result["cells"])
        self.assertEqual(self._gap_spots(), [])

    def test_a_gap_spot_is_labelled_a_proxy_and_never_a_measurement(self):
        proxy.refresh(self.conn, fetch=fake_fetch(11.5), sleep=lambda s: None)
        gap = self._gap_spots(use_spot_proxy=False)[0]
        t = data.get_spot_temperature(self.conn, gap[0], gap[1], gap[2], gap[3])
        self.assertEqual(t["resolution"], "spot_air_proxy")
        self.assertFalse(t["is_real"])
        self.assertEqual(t["method"], "nws_air_proxy_spot")
        self.assertAlmostEqual(t["value_c"], 11.5)
        self.assertIn("KTEST", t["source"])

    def test_spots_that_already_had_a_temperature_are_unchanged(self):
        before = {}
        rows = self.conn.execute("SELECT latitude, longitude, matched_waterbody_name, matched_county FROM access_points").fetchall()[::40]
        for r in rows:
            before[(r[0], r[1])] = data.get_spot_temperature(self.conn, r[0], r[1], r[2], r[3], use_spot_proxy=False)
        proxy.refresh(self.conn, fetch=fake_fetch(3.0), sleep=lambda s: None)
        for r in rows:
            after = data.get_spot_temperature(self.conn, r[0], r[1], r[2], r[3])
            b = before[(r[0], r[1])]
            if b is not None:
                self.assertEqual(after["resolution"], b["resolution"])
                self.assertEqual(after["value_c"], b["value_c"])

    def test_a_reading_older_than_the_limit_is_dropped_not_shown(self):
        gap = self._gap_spots(use_spot_proxy=False)[0]
        old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=proxy.MAX_AGE_HOURS + 1)).isoformat()
        self.conn.execute("INSERT INTO spot_air_proxy VALUES (?, ?, ?, ?, ?)", (proxy.cell_key(gap[0], gap[1]), 9.0, "KOLD", old, old))
        self.conn.commit()
        self.assertIsNone(proxy.lookup(self.conn, gap[0], gap[1]))
        self.assertIsNone(data.get_spot_temperature(self.conn, gap[0], gap[1], gap[2], gap[3]))

    def test_a_fresh_reading_is_used(self):
        gap = self._gap_spots(use_spot_proxy=False)[0]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.conn.execute("INSERT INTO spot_air_proxy VALUES (?, ?, ?, ?, ?)", (proxy.cell_key(gap[0], gap[1]), 9.0, "KNEW", now, now))
        self.conn.commit()
        self.assertEqual(proxy.lookup(self.conn, gap[0], gap[1])["value_c"], 9.0)

    def test_a_failed_fetch_keeps_the_previous_reading_and_counts_the_failure(self):
        gap = self._gap_spots(use_spot_proxy=False)[0]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        key = proxy.cell_key(gap[0], gap[1])
        self.conn.execute("INSERT INTO spot_air_proxy VALUES (?, ?, ?, ?, ?)", (key, 9.0, "KKEEP", now, now))
        self.conn.commit()

        def failing(lat, lon):
            raise urllib.error.URLError("down")

        result = proxy.refresh(self.conn, fetch=failing, sleep=lambda s: None, limit=None)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["failed"], result["cells"])
        self.assertEqual(self.conn.execute("SELECT station FROM spot_air_proxy WHERE cell = ?", (key,)).fetchone()[0], "KKEEP")

    def test_implausible_values_are_never_stored(self):
        result = proxy.refresh(self.conn, fetch=lambda lat, lon: (-999999, "KBAD", None), sleep=lambda s: None)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM spot_air_proxy").fetchone()[0], 0)

    def test_a_cold_winter_air_reading_is_accepted(self):
        result = proxy.refresh(self.conn, fetch=fake_fetch(-18.0), sleep=lambda s: None, limit=2)
        self.assertEqual(result["updated"], 2)

    def test_a_missing_table_means_no_proxy_not_an_error(self):
        bare = sqlite3.connect(":memory:")
        self.assertIsNone(proxy.lookup(bare, 46.0, -89.0))

    def test_the_feed_marks_these_spots_as_proxy(self):
        proxy.refresh(self.conn, fetch=fake_fetch(), sleep=lambda s: None)
        gap = self._gap_spots(use_spot_proxy=False)[0]
        point = dict(self.conn.execute(
            "SELECT * FROM access_points WHERE latitude = ? AND longitude = ?", (gap[0], gap[1])).fetchone())
        self.assertEqual(feed_module.build_row(self.conn, point)["q"], "proxy")

    def test_every_documented_species_gets_an_activity_read_at_a_gap_spot(self):
        proxy.refresh(self.conn, fetch=fake_fetch(15.0), sleep=lambda s: None)
        gap = self._gap_spots(use_spot_proxy=False)[0]
        detail = data.get_spot_detail(self.conn, gap[0], gap[1])
        act = detail["species_activity"]
        self.assertGreater(len(act["active"]) + len(act["inactive"]), 0)


class CacheKeyTests(unittest.TestCase):
    """The derived caches must follow the data, not the file: visitors' weather
    lookups write to the same database file all day."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "copy.db")
        shutil.copy(data.find_db_path(), self.path)
        self.conn = data.connect(self.path)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_weather_cache_write_does_not_change_the_fingerprint(self):
        before = data._db_fingerprint(self.conn)
        self.conn.execute("CREATE TABLE IF NOT EXISTS weather_conditions_cache (cache_key TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT)")
        self.conn.execute("INSERT OR REPLACE INTO weather_conditions_cache VALUES ('x', 'now', '{}')")
        self.conn.commit()
        self.assertEqual(data._db_fingerprint(self.conn), before)

    def test_a_sensor_refresh_changes_the_fingerprint(self):
        before = data._db_fingerprint(self.conn)
        self.conn.execute(
            "INSERT INTO temperature_refreshes (started_at, finished_at, waterbodies_checked, waterbodies_updated, failures) "
            "VALUES ('2099-01-01T00:00:00+00:00', '2099-01-01T00:01:00+00:00', 1, 1, 0)")
        self.conn.commit()
        self.assertNotEqual(data._db_fingerprint(self.conn), before)

    def test_a_new_air_proxy_fetch_changes_the_fingerprint(self):
        before = data._db_fingerprint(self.conn)
        proxy.ensure_table(self.conn)
        self.conn.execute("INSERT INTO spot_air_proxy VALUES ('46.00,-89.00', 10.0, 'K', 'now', '2099-01-01T00:00:00+00:00')")
        self.conn.commit()
        self.assertNotEqual(data._db_fingerprint(self.conn), before)

    def test_an_in_memory_database_is_never_cached(self):
        self.assertIsNone(data._db_fingerprint(sqlite3.connect(":memory:")))


if __name__ == "__main__":
    unittest.main()
