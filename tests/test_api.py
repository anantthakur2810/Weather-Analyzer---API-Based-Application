from datetime import datetime, timezone
import unittest

from weather_analyzer.api import OpenWeatherMapClient
from weather_analyzer.models import Location


def to_timestamp(year: int, month: int, day: int, hour: int, minute: int) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp())


class OpenWeatherMapClientTests(unittest.TestCase):
    def test_parse_report_builds_daily_summary_from_forecast_items(self) -> None:
        client = OpenWeatherMapClient(api_key="test-key")
        location = Location(
            name="Pune",
            country="IN",
            admin1="Maharashtra",
            latitude=18.52,
            longitude=73.86,
        )
        current_payload = {
            "dt": to_timestamp(2024, 4, 4, 6, 40),
            "timezone": 19800,
            "weather": [{"description": "overcast clouds"}],
            "main": {
                "temp": 30.2,
                "feels_like": 33.1,
                "humidity": 56,
                "pressure": 1002,
            },
            "wind": {"speed": 5.0, "deg": 270},
            "rain": {"1h": 0.8},
            "sys": {
                "sunrise": to_timestamp(2024, 4, 4, 0, 15),
                "sunset": to_timestamp(2024, 4, 4, 12, 41),
            },
        }
        forecast_payload = {
            "list": [
                {
                    "dt": to_timestamp(2024, 4, 4, 3, 0),
                    "main": {"temp_min": 25.0, "temp_max": 31.0},
                    "pop": 0.2,
                },
                {
                    "dt": to_timestamp(2024, 4, 4, 9, 0),
                    "main": {"temp_min": 27.0, "temp_max": 34.0},
                    "pop": 0.6,
                },
                {
                    "dt": to_timestamp(2024, 4, 5, 3, 0),
                    "main": {"temp_min": 22.0, "temp_max": 29.0},
                    "pop": 0.1,
                },
            ]
        }

        report = client._parse_report(location, current_payload, forecast_payload)

        self.assertEqual(report.weather_summary, "Overcast Clouds")
        self.assertEqual(report.observed_at, datetime(2024, 4, 4, 12, 10))
        self.assertAlmostEqual(report.wind_speed_kmh, 18.0)
        self.assertEqual(report.daily_high_c, 34.0)
        self.assertEqual(report.daily_low_c, 25.0)
        self.assertEqual(report.rain_chance_pct, 60)
        self.assertAlmostEqual(report.precipitation_mm, 0.8)
        self.assertTrue(report.is_day)


if __name__ == "__main__":
    unittest.main()
