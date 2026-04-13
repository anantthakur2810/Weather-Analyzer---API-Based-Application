from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from weather_analyzer.models import Location, WeatherReport
from weather_analyzer.storage import HistoryStore


class HistoryStoreTests(unittest.TestCase):
    def test_records_and_reads_recent_history(self) -> None:
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.db"
            store = HistoryStore(str(db_path))
            report = WeatherReport(
                location=Location(
                    name="Pune",
                    country="IN",
                    admin1="Maharashtra",
                    latitude=18.52,
                    longitude=73.86,
                ),
                observed_at=datetime(2026, 4, 4, 20, 30),
                weather_summary="Clear Sky",
                temperature_c=29.4,
                apparent_temperature_c=31.2,
                humidity_pct=51,
                wind_speed_kmh=8.0,
                wind_direction_deg=200,
                pressure_hpa=1009.0,
                precipitation_mm=0.0,
                is_day=False,
                daily_high_c=32.0,
                daily_low_c=24.0,
                rain_chance_pct=10,
                sunrise=datetime(2026, 4, 4, 6, 10),
                sunset=datetime(2026, 4, 4, 18, 40),
            )

            store.record_check("Poona", report)

            history = store.list_recent()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["query"], "Poona")
            self.assertEqual(history[0]["display_name"], "Pune, Maharashtra, IN")
            self.assertEqual(store.known_city_names(), ["Pune"])


if __name__ == "__main__":
    unittest.main()
