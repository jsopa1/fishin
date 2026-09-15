"""Pure data-layer tests for webapp/user_data.py -- no Flask, a fresh
temp SQLite file per test so nothing here touches a developer's real
data/v1/user_data.db.
"""

import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import user_data as udata  # noqa: E402


class UserDataTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_file)
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        udata.ensure_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_ensure_schema_creates_all_tables(self):
        tables = {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        for expected in ("users", "catches", "login_attempts", "feedback", "events"):
            self.assertIn(expected, tables)

    def test_create_user_hashes_password_not_stored_in_plaintext(self):
        udata.create_user(self.conn, email="a@b.com", password="correct horse battery")
        user = udata.get_user_by_email(self.conn, "a@b.com")
        self.assertNotEqual(user["password_hash"], "correct horse battery")
        self.assertNotIn("correct horse battery", user["password_hash"])
        self.assertTrue(udata.verify_password(user, "correct horse battery"))
        self.assertFalse(udata.verify_password(user, "wrong password"))

    def test_create_user_rejects_duplicate_email_case_insensitively(self):
        udata.create_user(self.conn, email="A@B.com", password="password123")
        with self.assertRaises(udata.EmailAlreadyRegistered):
            udata.create_user(self.conn, email="a@b.com", password="different123")

    def test_create_and_list_catches_round_trip(self):
        uid = udata.create_user(self.conn, email="angler@example.com", password="password123")
        udata.create_catch(
            self.conn, user_id=uid, species="Walleye", lat=45.0, lon=-89.0,
            spot_name="Test Landing", caught_at="2026-09-01", notes="nice one",
            kept_or_released="released",
        )
        catches = udata.list_catches_for_user(self.conn, uid)
        self.assertEqual(len(catches), 1)
        self.assertEqual(catches[0]["species"], "Walleye")
        self.assertEqual(catches[0]["kept_or_released"], "released")

    def test_catch_is_keyed_by_lat_lon_name_not_access_point_id(self):
        uid = udata.create_user(self.conn, email="angler2@example.com", password="password123")
        udata.create_catch(
            self.conn, user_id=uid, species="Bluegill", lat=44.5, lon=-88.5,
            spot_name="A Landing", caught_at="2026-09-01", notes=None, kept_or_released="unknown",
        )
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(catches)").fetchall()}
        self.assertNotIn("access_point_id", columns)
        self.assertIn("lat", columns)
        self.assertIn("lon", columns)
        self.assertIn("spot_name", columns)

    def test_delete_catch_only_removes_when_owned_by_that_user(self):
        uid_a = udata.create_user(self.conn, email="a@example.com", password="password123")
        uid_b = udata.create_user(self.conn, email="b@example.com", password="password123")
        catch_id = udata.create_catch(
            self.conn, user_id=uid_a, species="Northern Pike", lat=45.0, lon=-89.0,
            spot_name=None, caught_at="2026-09-01", notes=None, kept_or_released="unknown",
        )
        self.assertFalse(udata.delete_catch(self.conn, catch_id=catch_id, user_id=uid_b))
        self.assertEqual(len(udata.list_catches_for_user(self.conn, uid_a)), 1)
        self.assertTrue(udata.delete_catch(self.conn, catch_id=catch_id, user_id=uid_a))
        self.assertEqual(len(udata.list_catches_for_user(self.conn, uid_a)), 0)

    def test_recent_failed_login_count_windows_correctly(self):
        import datetime

        email = "windowtest@example.com"
        now = datetime.datetime.utcnow()
        recent_fail = (now - datetime.timedelta(minutes=2)).isoformat()
        old_fail = (now - datetime.timedelta(minutes=30)).isoformat()
        self.conn.execute(
            "INSERT INTO login_attempts (email, attempted_at, success) VALUES (?, ?, 0)",
            (email, recent_fail),
        )
        self.conn.execute(
            "INSERT INTO login_attempts (email, attempted_at, success) VALUES (?, ?, 0)",
            (email, old_fail),
        )
        self.conn.execute(
            "INSERT INTO login_attempts (email, attempted_at, success) VALUES (?, ?, 1)",
            (email, recent_fail),
        )
        self.conn.commit()
        count = udata.recent_failed_login_count(self.conn, email=email, window_minutes=15)
        self.assertEqual(count, 1)

    def test_create_feedback_round_trip(self):
        udata.create_feedback(
            self.conn, page_path="/spot", message="test message", contact=None, user_id=None
        )
        row = self.conn.execute("SELECT * FROM feedback").fetchone()
        self.assertEqual(row["message"], "test message")
        self.assertEqual(row["page_path"], "/spot")


if __name__ == "__main__":
    unittest.main()
