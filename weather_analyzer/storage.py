from __future__ import annotations

from contextlib import closing
from datetime import datetime
import sqlite3
from pathlib import Path

from weather_analyzer.models import WeatherReport


class HistoryStore:
    def __init__(self, db_path: str = "weather_history.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    resolved_name TEXT NOT NULL,
                    admin1 TEXT,
                    country TEXT NOT NULL,
                    checked_at TEXT NOT NULL,
                    temperature_c REAL NOT NULL,
                    weather_summary TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def record_check(self, query_text: str, report: WeatherReport) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO weather_checks (
                    query_text,
                    resolved_name,
                    admin1,
                    country,
                    checked_at,
                    temperature_c,
                    weather_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query_text,
                    report.location.name,
                    report.location.admin1,
                    report.location.country,
                    datetime.now().isoformat(timespec="seconds"),
                    report.temperature_c,
                    report.weather_summary,
                ),
            )
            connection.commit()

    def list_recent(self, limit: int = 10) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 50))
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    query_text,
                    resolved_name,
                    admin1,
                    country,
                    checked_at,
                    temperature_c,
                    weather_summary
                FROM weather_checks
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        history: list[dict[str, object]] = []
        for row in rows:
            display_parts = [row["resolved_name"]]
            if row["admin1"]:
                display_parts.append(row["admin1"])
            display_parts.append(row["country"])
            history.append(
                {
                    "id": row["id"],
                    "query": row["query_text"],
                    "display_name": ", ".join(display_parts),
                    "checked_at": row["checked_at"],
                    "temperature_c": row["temperature_c"],
                    "weather_summary": row["weather_summary"],
                }
            )
        return history

    def known_city_names(self, limit: int = 200) -> list[str]:
        safe_limit = max(1, min(limit, 500))
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT resolved_name
                FROM weather_checks
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [row["resolved_name"] for row in rows]
