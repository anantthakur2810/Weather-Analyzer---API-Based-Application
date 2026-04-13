from datetime import datetime
import unittest

from weather_analyzer.insights import build_insights
from weather_analyzer.models import Location, WeatherReport


def make_report(**overrides) -> WeatherReport:
    location = Location(
        name="Pune",
        country="India",
        admin1="Maharashtra",
        latitude=18.52,
        longitude=73.86,
        timezone="Asia/Kolkata",
    )
    baseline = {
        "location": location,
        "observed_at": datetime(2026, 4, 2, 9, 30),
        "weather_summary": "Clear sky",
        "temperature_c": 24.0,
        "apparent_temperature_c": 24.5,
        "humidity_pct": 40,
        "wind_speed_kmh": 10.0,
        "wind_direction_deg": 180,
        "pressure_hpa": 1012.0,
        "precipitation_mm": 0.0,
        "is_day": True,
        "daily_high_c": 30.0,
        "daily_low_c": 18.0,
        "rain_chance_pct": 10,
        "sunrise": datetime(2026, 4, 2, 6, 10),
        "sunset": datetime(2026, 4, 2, 18, 40),
    }
    baseline.update(overrides)
    return WeatherReport(**baseline)


class BuildInsightsTests(unittest.TestCase):
    def test_comfortable_clear_day_produces_positive_guidance(self) -> None:
        report = make_report()

        insights = build_insights(report)

        self.assertIn("Conditions look comfortable for most outdoor plans.", insights)
        self.assertIn(
            "Clear conditions and low rain probability make this a good window for travel or errands.",
            insights,
        )

    def test_overcast_day_uses_low_rain_language_without_claiming_clear_skies(self) -> None:
        report = make_report(weather_summary="Overcast")

        insights = build_insights(report)

        self.assertIn(
            "Rain risk looks low, so travel and outdoor errands should be easier to plan.",
            insights,
        )
        self.assertNotIn(
            "Clear conditions and low rain probability make this a good window for travel or errands.",
            insights,
        )

    def test_hot_rainy_and_windy_conditions_surface_multiple_risks(self) -> None:
        report = make_report(
            apparent_temperature_c=38.0,
            humidity_pct=84,
            rain_chance_pct=85,
            precipitation_mm=3.5,
            wind_speed_kmh=42.0,
            pressure_hpa=1002.0,
        )

        insights = build_insights(report)

        self.assertIn(
            "Heat stress is possible outdoors. Hydration and shade will matter today.",
            insights,
        )
        self.assertIn(
            "Humidity is high, so it may feel muggy even without extreme temperatures.",
            insights,
        )
        self.assertIn(
            "Rain looks likely, so carrying an umbrella would be sensible.",
            insights,
        )
        self.assertIn(
            "Strong winds could affect driving comfort, cycling, or outdoor setups.",
            insights,
        )
        self.assertIn(
            "Lower pressure suggests unsettled weather may continue through the day.",
            insights,
        )


if __name__ == "__main__":
    unittest.main()
