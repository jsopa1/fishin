"""HTTP-level tests for signup/login/logout and the catch log.

Isolated FISHIN_USER_DB_PATH per class, same as test_feedback_routes.py
and test_analytics.py -- never touches a developer's real local
data/v1/user_data.db.
"""

import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402
import user_data as udata  # noqa: E402


class AccountsRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.db_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(cls.db_file)
        cls._prior_env = os.environ.get("FISHIN_USER_DB_PATH")
        os.environ["FISHIN_USER_DB_PATH"] = cls.db_file
        flask_app_module.app.testing = True

    @classmethod
    def tearDownClass(cls):
        if cls._prior_env is None:
            os.environ.pop("FISHIN_USER_DB_PATH", None)
        else:
            os.environ["FISHIN_USER_DB_PATH"] = cls._prior_env
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)

    def setUp(self):
        # A fresh client per test -- session state (login) must not leak
        # between tests.
        self.client = flask_app_module.app.test_client()

    def _csrf_token(self, path):
        body = self.client.get(path).data.decode()
        match = re.search(r'name="csrf_token" value="([^"]+)"', body)
        self.assertIsNotNone(match, f"{path} did not render a csrf_token field")
        return match.group(1)

    def _signup(self, email, password="password123"):
        token = self._csrf_token("/signup")
        return self.client.post("/signup", data={"csrf_token": token, "email": email, "password": password})

    def test_signup_then_account_page_accessible(self):
        resp = self._signup("newuser@example.com")
        self.assertEqual(resp.status_code, 302)
        account_resp = self.client.get("/account")
        self.assertEqual(account_resp.status_code, 200)
        self.assertIn(b"My Catches", account_resp.data)

    def test_signup_rejects_duplicate_email(self):
        self._signup("dupe@example.com")
        resp = self._signup("dupe@example.com")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"already exists", resp.data)

    def test_signup_without_csrf_token_rejected_400(self):
        resp = self.client.post("/signup", data={"email": "nocsrf@example.com", "password": "password123"})
        self.assertEqual(resp.status_code, 400)

    def test_login_with_wrong_password_shows_generic_error(self):
        self._signup("wrongpw@example.com", password="rightpassword")
        self.client.post("/logout", data={"csrf_token": self._csrf_token("/account")})
        token = self._csrf_token("/login")
        resp = self.client.post("/login", data={
            "csrf_token": token, "email": "wrongpw@example.com", "password": "wrongpassword",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Incorrect email or password", resp.data)
        # The error text itself never distinguishes "wrong password" from
        # "no such account" -- both produce this exact same message.
        errors_block = re.search(rb'<div class="form-errors">(.*?)</div>', resp.data, re.DOTALL)
        self.assertIsNotNone(errors_block)
        self.assertNotIn(b"exist", errors_block.group(1).lower())

    def test_login_locks_out_after_repeated_failures(self):
        self._signup("lockout@example.com", password="correctpassword")
        self.client.post("/logout", data={"csrf_token": self._csrf_token("/account")})
        for _ in range(8):
            token = self._csrf_token("/login")
            self.client.post("/login", data={
                "csrf_token": token, "email": "lockout@example.com", "password": "wrong",
            })
        token = self._csrf_token("/login")
        resp = self.client.post("/login", data={
            "csrf_token": token, "email": "lockout@example.com", "password": "correctpassword",
        })
        self.assertEqual(resp.status_code, 429)
        self.assertIn(b"Too many failed attempts", resp.data)

    def test_account_page_requires_login_redirects_to_login(self):
        resp = self.client.get("/account")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_logout_clears_session_and_account_page_then_redirects(self):
        self._signup("logouttest@example.com")
        self.assertEqual(self.client.get("/account").status_code, 200)
        token = self._csrf_token("/account")
        self.client.post("/logout", data={"csrf_token": token})
        self.assertEqual(self.client.get("/account").status_code, 302)

    def test_log_a_catch_appears_in_account_history(self):
        self._signup("catchlogger@example.com")
        token = self._csrf_token("/account")
        resp = self.client.post("/account/catches", data={
            "csrf_token": token, "species": "Muskellunge", "lat": "45.5", "lon": "-89.5",
            "spot_name": "Test Bay", "caught_at": "2026-09-15", "kept_or_released": "released",
            "notes": "big one",
        })
        self.assertEqual(resp.status_code, 302)
        account_body = self.client.get("/account").data
        self.assertIn(b"Muskellunge", account_body)
        self.assertIn(b"Test Bay", account_body)

    def test_only_owner_can_delete_their_catch(self):
        self._signup("owner@example.com")
        token = self._csrf_token("/account")
        self.client.post("/account/catches", data={
            "csrf_token": token, "species": "Crappie", "lat": "44.0", "lon": "-88.0",
            "caught_at": "2026-09-15", "kept_or_released": "unknown",
        })
        conn = udata.connect()
        catch_id = conn.execute("SELECT id FROM catches WHERE species = 'Crappie'").fetchone()[0]
        conn.close()

        other_client = flask_app_module.app.test_client()
        fd, _ = tempfile.mkstemp()
        os.close(fd)
        token2 = re.search(
            r'name="csrf_token" value="([^"]+)"', other_client.get("/signup").data.decode()
        ).group(1)
        other_client.post("/signup", data={"csrf_token": token2, "email": "intruder@example.com", "password": "password123"})
        token3 = re.search(
            r'name="csrf_token" value="([^"]+)"', other_client.get("/account").data.decode()
        ).group(1)
        other_client.post(f"/account/catches/{catch_id}/delete", data={"csrf_token": token3})

        conn = udata.connect()
        remaining = udata.list_catches_for_user(conn, self._user_id("owner@example.com", conn))
        conn.close()
        self.assertEqual(len(remaining), 1)

    def _user_id(self, email, conn=None):
        own_conn = conn is None
        if own_conn:
            conn = udata.connect()
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if own_conn:
            conn.close()
        return row[0]

    def test_password_never_echoed_in_any_response_body(self):
        resp = self._signup("secretcheck@example.com", password="supersecretpassword")
        self.assertNotIn(b"supersecretpassword", resp.data)
        account_body = self.client.get("/account").data
        self.assertNotIn(b"supersecretpassword", account_body)

    def test_account_feature_does_not_touch_anonymous_save_spot_flow(self):
        points = self.client.get("/map/data").get_json()["points"]
        p = points[0]
        spot_body = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn("localStorage", spot_body)
        self.assertIn('id="save-spot"', spot_body)
        home_body = self.client.get("/").data.decode()
        self.assertIn("never uploaded anywhere", home_body)

        # Logged in, the spot page additionally (not instead) offers the
        # account-based catch log.
        self._signup("spotpageuser@example.com")
        spot_body_logged_in = self.client.get("/spot?lat={}&lon={}".format(p["lat"], p["lon"])).data.decode()
        self.assertIn("localStorage", spot_body_logged_in)
        self.assertIn('id="save-spot"', spot_body_logged_in)
        self.assertIn("Log a catch here", spot_body_logged_in)


if __name__ == "__main__":
    unittest.main()
