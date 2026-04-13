from __future__ import annotations

import argparse
from typing import Sequence

from weather_analyzer.api import OpenWeatherMapClient, WeatherApiError
from weather_analyzer.config import ConfigurationError
from weather_analyzer.insights import build_insights


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather-analyzer",
        description="Fetch and analyze real-time weather data for a city.",
    )
    parser.add_argument(
        "city",
        nargs="*",
        help="City name to search, for example: New Delhi",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="API timeout in seconds.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to the .env file containing OPENWEATHER_API_KEY.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    city = " ".join(args.city).strip()
    if not city:
        city = input("Enter a city name: ").strip()

    if not city:
        parser.error("a city name is required")

    try:
        client = OpenWeatherMapClient.from_env(timeout=args.timeout, env_path=args.env_file)
        report = client.fetch_report(city)
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1
    except WeatherApiError as exc:
        print(f"Error: {exc}")
        return 1

    print(render_report(report))
    return 0


def render_report(report) -> str:
    insights = build_insights(report)

    lines = [
        "Weather Analyzer",
        f"Location: {report.location.display_name}",
        f"Observed: {report.observed_at:%Y-%m-%d %H:%M}",
        "",
        "Current Conditions",
        f"- Weather: {report.weather_summary}",
        f"- Temperature: {report.temperature_c:.1f} C",
        f"- Feels like: {report.apparent_temperature_c:.1f} C",
        f"- Humidity: {report.humidity_pct}%",
        f"- Wind: {report.wind_speed_kmh:.1f} km/h at {report.wind_direction_deg} deg",
        f"- Pressure: {report.pressure_hpa:.1f} hPa",
        f"- Precipitation: {report.precipitation_mm:.1f} mm",
        "",
        "Today's Outlook",
        f"- High / Low: {report.daily_high_c:.1f} C / {report.daily_low_c:.1f} C",
        f"- Rain Chance: {report.rain_chance_pct}%",
        f"- Sunrise / Sunset: {report.sunrise:%H:%M} / {report.sunset:%H:%M}",
        "",
        "Insights",
    ]
    lines.extend(f"- {item}" for item in insights)
    return "\n".join(lines)
