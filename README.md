# Weather Analyzer

Weather Analyzer is a small full-stack weather app.

It uses:
- a React frontend built with Vite
- a Python backend that talks to OpenWeather
- SQLite for local search history

You can search for a city, view current conditions and a short daily outlook, keep a history of recent searches, and get likely city suggestions when the input is misspelled.

## Local development

Use these commands in PowerShell:

```powershell
npm.cmd install
npm.cmd run dev
```

`npm` may fail in VS Code PowerShell with an execution-policy error because Windows tries to run `npm.ps1`. `npm.cmd` avoids that issue.

## Deployment

This project has two parts:

- a static React frontend
- a Python backend that serves `/api/*`

Because of that, GitHub Pages can host only the frontend. It cannot run the Python backend.

### Deploying the frontend to GitHub Pages

The workflow at `.github/workflows/deploy.yml` publishes the `dist/` folder to GitHub Pages.

Before pushing to `main`, set this repository variable in GitHub:

- `VITE_API_BASE_URL` = the public URL of your deployed backend, for example `https://your-backend.example.com`

Also make sure GitHub Pages is enabled in the repository settings.

### Deploying the backend

Deploy the Python app to a host that can run a long-lived Python process. The backend needs:

- Python 3.10+
- the `OPENWEATHER_API_KEY` environment variable
- optionally `CORS_ALLOW_ORIGIN` if you want to restrict browser access to a specific frontend origin
- a start command that builds the frontend before serving, or a deploy flow that already includes the `dist/` folder

Example backend start command:

```bash
python -m weather_analyzer.web --host 0.0.0.0 --port $PORT
```

### Important notes

- `.env` is ignored by git, so your API key is not uploaded with the repo.
- `dist/` is also ignored by git, so your deployment must run `npm run build` or publish the built frontend separately.
- The frontend now supports `VITE_API_BASE_URL`, so it can call a backend hosted on a different domain.
- If frontend and backend are on different domains, set `CORS_ALLOW_ORIGIN` on the backend to your frontend URL.
