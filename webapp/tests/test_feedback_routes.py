"""Tests for the in-app feedback route.

Uses a temp, isolated FISHIN_USER_DB_PATH for the whole class so these
tests never touch a developer's real local data/v1/user_data.db --
webapp/user_data.py reads that env var fresh on every connect(), so
setting it before each request is enough, no monkeypatching needed.
"""

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import user_data as udata  # noqa: E402


class FeedbackRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.db_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(cls.db_file)  # udata.connect() creates it fresh
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

    def _feedback_count(self):
        conn = udata.connect()
        n = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        conn.close()
        return n

    def _csrf_token(self):
        body = self.client.get("/feedback").data.decode()
        match = re.search(r'name="csrf_token" value="([^"]+)"', body)
        self.assertIsNotNone(match, "feedback form did not render a csrf_token field")
        return match.group(1)

    def test_feedback_page_loads_and_contains_csrf_token(self):
        body = self.client.get("/feedback").data
        self.assertIn(b'name="csrf_token"', body)

    def test_feedback_post_without_csrf_token_rejected(self):
        before = self._feedback_count()
        resp = self.client.post("/feedback", data={"message": "the water temp looks wrong here"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self._feedback_count(), before)

    def test_feedback_post_with_valid_csrf_stores_submission(self):
        token = self._csrf_token()
        before = self._feedback_count()
        resp = self.client.post("/feedback", data={
            "csrf_token": token, "message": "this page would not load for me", "page": "/spot",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"recorded", resp.data)
        self.assertEqual(self._feedback_count(), before + 1)

        conn = udata.connect()
        row = conn.execute("SELECT message, page_path FROM feedback ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        self.assertEqual(row["message"], "this page would not load for me")
        self.assertEqual(row["page_path"], "/spot")

    def test_feedback_requires_nonempty_message(self):
        token = self._csrf_token()
        before = self._feedback_count()
        resp = self.client.post("/feedback", data={"csrf_token": token, "message": "   "})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self._feedback_count(), before)

    def test_footer_report_a_problem_link_still_present_on_every_page(self):
        for path in ("/", "/map"):
            body = self.client.get(path).data
            self.assertIn(b"Report a problem", body)


if __name__ == "__main__":
    unittest.main()
