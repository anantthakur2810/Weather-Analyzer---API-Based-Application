from __future__ import annotations

import os
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing."""


def load_env_file(path: str = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_api_key(env_path: str = ".env") -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if api_key:
        return api_key

    api_key = load_env_file(env_path).get("OPENWEATHER_API_KEY", "").strip()
    if api_key:
        return api_key

    raise ConfigurationError(
        "Missing OpenWeatherMap API key. Add OPENWEATHER_API_KEY to .env or set it in your environment."
    )
