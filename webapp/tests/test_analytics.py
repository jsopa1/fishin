"""Tests for the self-hosted, privacy-respecting analytics events.

The property that matters most isn't the row count -- it's that nothing
here can ever identify a visitor. The schema-level test below is a
regression guard: if someone later adds an ip_address or user_agent
column to make debugging easier, this test fails and forces a deliberate
decision, rather than that column silently shipping.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import user_data as udata  # noqa: E402


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.db_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(cls.db_file)
        cls._prior_env = os.environ.get("FISHIN_USER_DB_PATH")
        os.environ["FISHIN_USER_DB_PATH"] = cls.db_file
        flask_app_module.app.testing = True
        cls.client = flask_app_module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if cls._prior_env is None:
            os.environ.pop("FISHIN_USER_DB_PATH", None)
        else:
            os.environ["FISHIN_USER_DB_PATH"] = cls._prior_env
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)

    def _events(self, event_type=None):
        conn = udata.connect()
        if event_type:
            rows = conn.execute("SELECT * FROM events WHERE event_type = ?", (event_type,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM events").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def test_events_table_has_no_identifying_columns(self):
        conn = udata.connect()
        columns = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
        conn.close()
        self.assertEqual(
            columns,
            {"id", "event_type", "page_path", "referrer", "session_id", "occurred_at"},
            msg="events table gained or lost a column -- if this added ip_address/user_agent, that's a privacy regression",
        )
        forbidden = {"ip", "ip_address", "user_agent", "useragent", "fingerprint"}
        self.assertFalse(columns & forbidden)

    def test_a_real_page_view_logs_exactly_one_pageview_event(self):
        before = len(self._events("pageview"))
        self.client.get("/")
        after = len(self._events("pageview"))
        self.assertEqual(after, before + 1)

    def test_excluded_paths_are_never_logged(self):
        before = len(self._events())
        self.client.get("/healthz")
        self.client.get("/manifest.json")
        self.client.get("/robots.txt")
        self.client.get("/map/data")
        self.assertEqual(len(self._events()), before)

    def test_save_beacon_records_a_save_event_without_any_coordinate(self):
        before = len(self._events("save"))
        resp = self.client.post("/events/save", data={"page": "/spot"})
        self.assertEqual(resp.status_code, 204)
        events = self._events("save")
        self.assertEqual(len(events), before + 1)
        newest = events[-1]
        self.assertEqual(newest["page_path"], "/spot")
        # No field anywhere on this row could carry a lat/lon.
        for value in newest.values():
            self.assertNotIn(",-8", str(value), msg="a coordinate-shaped value leaked into an event row")

    def test_pageviews_share_a_session_id_across_requests_in_one_browser_session(self):
        self.client.get("/")
        self.client.get("/browse")
        rows = self._events("pageview")
        session_ids = {r["session_id"] for r in rows[-2:]}
        self.assertEqual(len(session_ids), 1)


if __name__ == "__main__":
    unittest.main()
