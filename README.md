# Weather Analyzer - Vite + React + Python

`Weather Analyzer` now uses a Vite + React frontend and a Python backend. The frontend gives you the normal `npm run dev` workflow, while the Python backend still handles weather fetching, history storage, and typo-based city suggestions.

## Stack

- Frontend: Vite + React
- Backend: Python standard-library HTTP server
- Storage: SQLite
- API source: OpenWeather

## Features

- Real-time weather search by city name
- `npm run dev` developer workflow
- Search history stored in `weather_history.db`
- Smart city suggestions for misspellings like `Mumbay` -> `Mumbai`
- React dashboard with live result cards and history sidebar
- Python backend can serve the production build after `npm run build`

## Setup

1. Open [.env](/D:/Weather Analyzer — API-Based Application/.env)
2. Paste your OpenWeather API key after `OPENWEATHER_API_KEY=`

Example:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

## Install Frontend Dependencies

Use `npm.cmd` in PowerShell because `npm` may be blocked by script execution policy on Windows:

```powershell
npm.cmd install
```

## Run In Development

```powershell
npm.cmd run dev
```

That starts:

- Vite frontend at [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Python backend API at [http://127.0.0.1:8000](http://127.0.0.1:8000)

Vite proxies `/api` requests to the Python backend automatically.

## Build The Frontend

```powershell
npm.cmd run build
```

## Serve The Production Build With Python

```powershell
py -3 main.py
```

After a build, the Python server serves the compiled frontend from `dist` and continues exposing the same `/api` endpoints.

## CLI Still Available

```powershell
py -3 -m weather_analyzer.cli "New Delhi"
```

## Run Python Tests

```powershell
py -3 -m unittest discover -s tests -v
```
