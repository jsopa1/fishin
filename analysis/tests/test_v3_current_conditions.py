"""Tests for the live wind/pressure lookup.

The property that matters most here isn't formatting -- it's that this
module never crosses from reporting a number into implying a conclusion.
Nothing in here should compare wind or pressure to a threshold, rank a
species by it, or otherwise let it act like an evidentiary claim.
"""

import os
import sqlite3
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import v3_current_conditions as conditions  # noqa: E402


class TestCompass(unittest.TestCase):
    def test_north_is_n(self):
        self.assertEqual(conditions._compass(0), "N")

    def test_wraps_past_360(self):
        self.assertEqual(conditions._compass(359), "N")

    def test_south_west(self):
        self.assertEqual(conditions._compass(225), "SW")

    def test_none_stays_none(self):
        self.assertIsNone(conditions._compass(None))


class TestUnitConversion(unittest.TestCase):
    def test_query_nws_converts_kmh_to_mph_and_pa_to_inhg(self):
        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def read(self):
                import json
                return json.dumps(self._payload).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        points_payload = {"properties": {"observationStations": "https://api.weather.gov/stations"}}
        stations_payload = {"features": [{"id": "https://api.weather.gov/stations/KMSN"}]}
        obs_payload = {
            "properties": {
                "windSpeed": {"value": 16.09},  # ~10 mph
                "windDirection": {"value": 180},
                "barometricPressure": {"value": 101592.8},  # ~30.0 inHg
                "timestamp": "2026-09-15T18:00:00+00:00",
            }
        }
        responses = iter([points_payload, stations_payload, obs_payload])

        def fake_urlopen(request, timeout=None):
            return FakeResponse(next(responses))

        with mock.patch.object(conditions.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = conditions._query_nws(43.0, -89.0)

        self.assertEqual(result["status"], "ok")
        self.assertAlmostEqual(result["wind_speed_mph"], 10.0, delta=0.1)
        self.assertEqual(result["wind_direction_compass"], "S")
        self.assertAlmostEqual(result["pressure_inhg"], 30.0, delta=0.05)
        self.assertEqual(result["station"], "KMSN")


class TestSkyKind(unittest.TestCase):
    def test_common_station_descriptions_map_to_an_icon(self):
        cases = {
            "Clear": "sun", "Sunny": "sun", "Fair": "sun",
            "Partly Cloudy": "partly", "Mostly Cloudy": "cloud", "Overcast": "cloud",
            "Light Rain": "rain", "Rain Showers": "rain", "Drizzle": "rain",
            "Thunderstorm in Vicinity": "storm", "Thunderstorm with Rain": "storm",
            "Light Snow": "snow", "Freezing Rain": "rain", "Fog/Mist": "fog", "Haze": "fog",
        }
        for text, kind in cases.items():
            self.assertEqual(conditions.sky_kind(text), kind, text)

    def test_unrecognised_or_missing_text_gives_no_icon_not_a_guess(self):
        self.assertIsNone(conditions.sky_kind("Tornado Watch"))
        self.assertIsNone(conditions.sky_kind(""))
        self.assertIsNone(conditions.sky_kind(None))


class TestAirTemperatureParsing(unittest.TestCase):
    def _run(self, props):
        import json

        class R:
            def __init__(self, p):
                self.p = p

            def read(self):
                return json.dumps(self.p).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        seq = iter([
            {"properties": {"observationStations": "https://api.weather.gov/stations"}},
            {"features": [{"id": "https://api.weather.gov/stations/KMSN"}]},
            {"properties": props},
        ])
        with mock.patch.object(conditions.urllib.request, "urlopen", side_effect=lambda *a, **k: R(next(seq))):
            return conditions._query_nws(43.0, -89.0)

    def test_air_temperature_and_sky_are_reported_from_the_observation(self):
        r = self._run({"temperature": {"value": 20.0}, "textDescription": "Partly Cloudy",
                       "windSpeed": {"value": None}, "barometricPressure": {"value": None}})
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["air_temp_f"], 68)
        self.assertEqual(r["air_temp_c"], 20.0)
        self.assertEqual(r["sky"], "Partly Cloudy")
        self.assertEqual(r["sky_kind"], "partly")

    def test_an_observation_with_only_a_temperature_is_still_usable(self):
        self.assertEqual(self._run({"temperature": {"value": 10.0}})["status"], "ok")

    def test_an_observation_with_nothing_to_show_is_skipped(self):
        self.assertEqual(self._run({})["status"], "none")


class TestCurrentConditionsLookup(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")

    def test_result_is_cached_rather_than_refetched(self):
        payload = {"status": "ok", "wind_speed_mph": 8.0, "wind_direction_compass": "NW",
                   "pressure_inhg": 29.9, "observed_at": "2026-09-15T18:00:00+00:00", "station": "KMSN"}
        with mock.patch.object(conditions, "_query_nws", return_value=payload) as q:
            first = conditions.get_current_conditions(self.conn, 43.4263, -89.7281)
            second = conditions.get_current_conditions(self.conn, 43.4263, -89.7281)
        self.assertEqual(q.call_count, 1)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "ok")

    def test_service_failure_with_no_cache_returns_none(self):
        with mock.patch.object(conditions, "_query_nws", side_effect=OSError("down")):
            self.assertIsNone(conditions.get_current_conditions(self.conn, 44.0, -90.0))

    def test_service_failure_falls_back_to_stale_cache_and_flags_it(self):
        payload = {"status": "ok", "wind_speed_mph": 8.0, "wind_direction_compass": "NW",
                   "pressure_inhg": 29.9, "observed_at": "2026-09-15T18:00:00+00:00", "station": "KMSN"}
        with mock.patch.object(conditions, "_query_nws", return_value=payload):
            conditions.get_current_conditions(self.conn, 43.4263, -89.7281)
        self.conn.execute("UPDATE weather_conditions_cache SET fetched_at = '2020-01-01T00:00:00+00:00'")
        self.conn.commit()
        with mock.patch.object(conditions, "_query_nws", side_effect=OSError("down")):
            result = conditions.get_current_conditions(self.conn, 43.4263, -89.7281)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["stale"])

    def test_missing_coordinates_return_none(self):
        self.assertIsNone(conditions.get_current_conditions(self.conn, None, None))

    def test_no_station_reports_none_not_a_fabricated_reading(self):
        with mock.patch.object(conditions, "_query_nws", return_value={"status": "none"}):
            result = conditions.get_current_conditions(self.conn, 44.0, -90.0)
        self.assertEqual(result["status"], "none")


if __name__ == "__main__":
    unittest.main()
