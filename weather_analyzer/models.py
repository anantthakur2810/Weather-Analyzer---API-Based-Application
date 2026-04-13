from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Location:
    name: str
    country: str
    admin1: str | None
    latitude: float
    longitude: float
    timezone: str = ""

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.admin1:
            parts.append(self.admin1)
        parts.append(self.country)
        return ", ".join(parts)


@dataclass(slots=True)
class WeatherReport:
    location: Location
    observed_at: datetime
    weather_summary: str
    temperature_c: float
    apparent_temperature_c: float
    humidity_pct: int
    wind_speed_kmh: float
    wind_direction_deg: int
    pressure_hpa: float
    precipitation_mm: float
    is_day: bool
    daily_high_c: float
    daily_low_c: float
    rain_chance_pct: int
    sunrise: datetime
    sunset: datetime
