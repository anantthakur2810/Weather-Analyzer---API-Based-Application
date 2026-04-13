from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from weather_analyzer.config import get_api_key
from weather_analyzer.models import Location, WeatherReport

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherApiError(RuntimeError):
    """Raised when the weather service cannot be reached or parsed."""


class OpenWeatherMapClient:
    def __init__(self, api_key: str, timeout: int = 15) -> None:
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls, timeout: int = 15, env_path: str = ".env") -> "OpenWeatherMapClient":
        return cls(api_key=get_api_key(env_path), timeout=timeout)

    def fetch_report(self, city: str) -> WeatherReport:
        location = self._lookup_location(city)
        current_payload = self._fetch_json(
            CURRENT_WEATHER_URL,
            {
                "lat": location.latitude,
                "lon": location.longitude,
                "appid": self.api_key,
                "units": "metric",
            },
        )
        forecast_payload = self._fetch_json(
            FORECAST_URL,
            {
                "lat": location.latitude,
                "lon": location.longitude,
                "appid": self.api_key,
                "units": "metric",
            },
        )
        return self._parse_report(location, current_payload, forecast_payload)

    def _lookup_location(self, city: str) -> Location:
        payload = self._fetch_json(
            GEOCODING_URL,
            {
                "q": city,
                "limit": 1,
                "appid": self.api_key,
            },
        )
        if not payload:
            raise WeatherApiError(f"No location match found for '{city}'.")

        match = payload[0]
        return Location(
            name=match["name"],
            country=match["country"],
            admin1=match.get("state"),
            latitude=float(match["lat"]),
            longitude=float(match["lon"]),
            timezone="",
        )

    def _fetch_json(self, base_url: str, params: dict[str, object]) -> dict | list:
        url = f"{base_url}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            detail = exc.reason
            try:
                detail = json.load(exc).get("message", detail)
            except Exception:
                pass
            raise WeatherApiError(f"API request failed ({exc.code}): {detail}.") from exc
        except URLError as exc:
            raise WeatherApiError(f"Unable to reach weather service: {exc.reason}") from exc
        except Exception as exc:
            raise WeatherApiError(f"Unable to reach weather service: {exc}") from exc

    def _parse_report(self, location: Location, current: dict, forecast: dict) -> WeatherReport:
        if not current or not forecast:
            raise WeatherApiError("Weather payload is missing expected fields.")

        timezone_offset = int(current.get("timezone", 0))
        observed_at = self._local_datetime_from_timestamp(current["dt"], timezone_offset)
        sunrise = self._local_datetime_from_timestamp(current["sys"]["sunrise"], timezone_offset)
        sunset = self._local_datetime_from_timestamp(current["sys"]["sunset"], timezone_offset)
        daily_high_c, daily_low_c, rain_chance_pct = self._summarize_today(
            forecast.get("list") or [],
            observed_at,
            timezone_offset,
            float(current["main"]["temp"]),
        )

        weather_items = current.get("weather") or []
        weather_summary = weather_items[0]["description"].title() if weather_items else "Unknown conditions"

        return WeatherReport(
            location=location,
            observed_at=observed_at,
            weather_summary=weather_summary,
            temperature_c=float(current["main"]["temp"]),
            apparent_temperature_c=float(current["main"]["feels_like"]),
            humidity_pct=int(current["main"]["humidity"]),
            wind_speed_kmh=float(current.get("wind", {}).get("speed", 0.0)) * 3.6,
            wind_direction_deg=int(current.get("wind", {}).get("deg", 0)),
            pressure_hpa=float(current["main"]["pressure"]),
            precipitation_mm=self._extract_precipitation(current),
            is_day=sunrise <= observed_at <= sunset,
            daily_high_c=daily_high_c,
            daily_low_c=daily_low_c,
            rain_chance_pct=rain_chance_pct,
            sunrise=sunrise,
            sunset=sunset,
        )

    @staticmethod
    def _local_datetime_from_timestamp(timestamp: int, timezone_offset: int) -> datetime:
        utc_value = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        local_value = utc_value + timedelta(seconds=timezone_offset)
        return local_value.replace(tzinfo=None)

    @staticmethod
    def _extract_precipitation(current: dict) -> float:
        rain = current.get("rain") or {}
        snow = current.get("snow") or {}
        precipitation_values = [
            float(rain.get("1h", 0.0)),
            float(rain.get("3h", 0.0)),
            float(snow.get("1h", 0.0)),
            float(snow.get("3h", 0.0)),
        ]
        return max(precipitation_values, default=0.0)

    def _summarize_today(
        self,
        forecast_items: list[dict],
        observed_at: datetime,
        timezone_offset: int,
        fallback_temp: float,
    ) -> tuple[float, float, int]:
        today_entries = [
            item
            for item in forecast_items
            if self._local_datetime_from_timestamp(item["dt"], timezone_offset).date() == observed_at.date()
        ]

        if not today_entries:
            return fallback_temp, fallback_temp, 0

        high = max(float(item["main"]["temp_max"]) for item in today_entries)
        low = min(float(item["main"]["temp_min"]) for item in today_entries)
        rain_chance = max(int(round(float(item.get("pop", 0.0)) * 100)) for item in today_entries)
        return high, low, rain_chance
