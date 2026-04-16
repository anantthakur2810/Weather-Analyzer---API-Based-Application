from __future__ import annotations

from argparse import ArgumentParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from weather_analyzer.api import OpenWeatherMapClient, WeatherApiError
from weather_analyzer.config import ConfigurationError
from weather_analyzer.insights import build_insights
from weather_analyzer.storage import HistoryStore
from weather_analyzer.suggestions import suggest_city_names

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")


def serialize_report(report) -> dict[str, object]:
    return {
        "location": {
            "name": report.location.name,
            "admin1": report.location.admin1,
            "country": report.location.country,
            "display_name": report.location.display_name,
            "latitude": report.location.latitude,
            "longitude": report.location.longitude,
        },
        "observed_at": report.observed_at.isoformat(timespec="minutes"),
        "weather_summary": report.weather_summary,
        "temperature_c": report.temperature_c,
        "apparent_temperature_c": report.apparent_temperature_c,
        "humidity_pct": report.humidity_pct,
        "wind_speed_kmh": report.wind_speed_kmh,
        "wind_direction_deg": report.wind_direction_deg,
        "pressure_hpa": report.pressure_hpa,
        "precipitation_mm": report.precipitation_mm,
        "is_day": report.is_day,
        "daily_high_c": report.daily_high_c,
        "daily_low_c": report.daily_low_c,
        "rain_chance_pct": report.rain_chance_pct,
        "sunrise": report.sunrise.isoformat(timespec="minutes"),
        "sunset": report.sunset.isoformat(timespec="minutes"),
    }


class WeatherWebApplication:
    def __init__(self, env_file: str = ".env", db_path: str = "weather_history.db", timeout: int = 15) -> None:
        self.client = OpenWeatherMapClient.from_env(timeout=timeout, env_path=env_file)
        self.history = HistoryStore(db_path=db_path)

    def fetch_weather(self, city: str) -> dict[str, object]:
        report = self.client.fetch_report(city)
        self.history.record_check(city, report)
        return {
            "report": serialize_report(report),
            "insights": build_insights(report),
            "history": self.history.list_recent(),
            "suggestions": [],
        }

    def get_history(self, limit: int = 10) -> dict[str, object]:
        return {"history": self.history.list_recent(limit=limit)}

    def clear_history(self) -> dict[str, object]:
        self.history.clear_history()
        return {"history": []}

    def suggest_cities(self, query: str) -> list[str]:
        return suggest_city_names(query, history_candidates=self.history.known_city_names())


class WeatherHttpServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], app: WeatherWebApplication) -> None:
        super().__init__(server_address, WeatherRequestHandler)
        self.app = app


class WeatherRequestHandler(BaseHTTPRequestHandler):
    server: WeatherHttpServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/weather":
            self._handle_weather(parsed)
            return
        if parsed.path == "/api/history":
            self._handle_history(parsed)
            return
        self._serve_frontend(parsed.path)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/history":
            self._send_json(HTTPStatus.OK, self.server.app.clear_history())
            return
        self._send_plaintext(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def do_OPTIONS(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_cors_headers()
            self.end_headers()
            return
        self._send_plaintext(HTTPStatus.NOT_FOUND, "Endpoint not found.")

    def _handle_weather(self, parsed) -> None:
        query = parse_qs(parsed.query).get("city", [""])[0].strip()
        if not query:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "City name is required.", "suggestions": []})
            return

        try:
            payload = self.server.app.fetch_weather(query)
            self._send_json(HTTPStatus.OK, payload)
        except WeatherApiError as exc:
            message = str(exc)
            suggestions = self.server.app.suggest_cities(query)
            status = HTTPStatus.NOT_FOUND if "No location match found" in message else HTTPStatus.BAD_GATEWAY
            self._send_json(status, {"error": message, "suggestions": suggestions})

    def _handle_history(self, parsed) -> None:
        raw_limit = parse_qs(parsed.query).get("limit", ["10"])[0]
        try:
            limit = int(raw_limit)
        except ValueError:
            limit = 10
        self._send_json(HTTPStatus.OK, self.server.app.get_history(limit=limit))

    def _serve_frontend(self, request_path: str) -> None:
        if not DIST_DIR.exists():
            self._send_plaintext(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "Frontend build not found. Run npm.cmd install and npm.cmd run dev for development, or npm.cmd run build before serving with Python.",
            )
            return

        relative_path = request_path.lstrip("/") or "index.html"
        candidate = (DIST_DIR / relative_path).resolve()
        dist_root = DIST_DIR.resolve()

        if str(candidate).startswith(str(dist_root)) and candidate.exists() and candidate.is_file():
            self._send_file(candidate)
            return

        index_file = DIST_DIR / "index.html"
        if index_file.exists():
            self._send_file(index_file)
            return

        self._send_plaintext(HTTPStatus.NOT_FOUND, "Frontend file not found.")

    def _send_file(self, path: Path) -> None:
        content_type, _ = mimetypes.guess_type(path.name)
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_plaintext(self, status: HTTPStatus, message: str) -> None:
        body = message.encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", CORS_ALLOW_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args) -> None:
        return


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Run the Weather Analyzer backend server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the web server to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the web server to.")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file containing OPENWEATHER_API_KEY.")
    parser.add_argument("--db-path", default="weather_history.db", help="Path to the SQLite database file.")
    parser.add_argument("--timeout", type=int, default=15, help="API timeout in seconds.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        app = WeatherWebApplication(env_file=args.env_file, db_path=args.db_path, timeout=args.timeout)
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1

    server = WeatherHttpServer((args.host, args.port), app)
    print(f"Weather Analyzer backend running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
