import { startTransition, useEffect, useState } from 'react'

const initialWeather = null

function formatDateTime(value) {
  return String(value).replace('T', ' ')
}

function formatTime(value) {
  return String(value).slice(11, 16)
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function HistoryItem({ entry, onSelect }) {
  return (
    <button type="button" className="history-button" onClick={() => onSelect(entry.query)}>
      <strong>{entry.display_name}</strong>
      <div className="history-meta">
        <span>{entry.weather_summary}</span>
        <span>{Number(entry.temperature_c).toFixed(1)} C</span>
      </div>
      <div className="history-meta">
        <span>Searched as: {entry.query}</span>
        <span>{formatDateTime(entry.checked_at)}</span>
      </div>
    </button>
  )
}

export default function App() {
  const [city, setCity] = useState('')
  const [status, setStatus] = useState({ text: 'Enter a city to load live weather data.', error: false })
  const [weather, setWeather] = useState(initialWeather)
  const [insights, setInsights] = useState([])
  const [history, setHistory] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadHistory() {
      try {
        const response = await fetch('/api/history?limit=12')
        const data = await response.json()
        startTransition(() => {
          setHistory(data.history || [])
        })
      } catch {
        startTransition(() => {
          setStatus({ text: 'Unable to load search history right now.', error: true })
        })
      }
    }

    loadHistory()
  }, [])

  async function runSearch(nextCity) {
    const trimmedCity = nextCity.trim()
    if (!trimmedCity) {
      setStatus({ text: 'Please enter a city name.', error: true })
      return
    }

    setCity(trimmedCity)
    setLoading(true)
    setSuggestions([])
    setStatus({ text: `Loading live weather for ${trimmedCity}...`, error: false })

    try {
      const response = await fetch(`/api/weather?city=${encodeURIComponent(trimmedCity)}`)
      const data = await response.json()

      if (!response.ok) {
        startTransition(() => {
          setLoading(false)
          setStatus({ text: data.error || 'Unable to fetch weather right now.', error: true })
          setSuggestions(data.suggestions || [])
        })
        return
      }

      startTransition(() => {
        setLoading(false)
        setWeather(data.report)
        setInsights(data.insights || [])
        setHistory(data.history || [])
        setSuggestions([])
        setStatus({ text: `Showing latest weather for ${data.report.location.display_name}.`, error: false })
      })
    } catch {
      startTransition(() => {
        setLoading(false)
        setStatus({ text: 'Network error while fetching weather data.', error: true })
      })
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    runSearch(city)
  }

  return (
    <>
      <div className="background-orb orb-one" />
      <div className="background-orb orb-two" />
      <main className="page-shell">
        <section className="hero-card">
          <p className="eyebrow">Live Weather Dashboard</p>
          <h1>Weather Analyzer</h1>
          <p className="hero-copy">
            Check real-time weather, keep a searchable history, and recover quickly from spelling mistakes with smart city suggestions.
          </p>
          <form className="search-bar" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="city-input">Search city</label>
            <input
              id="city-input"
              name="city"
              type="text"
              placeholder="Search for a city like Mumbai or London"
              autoComplete="off"
              required
              value={city}
              onChange={(event) => setCity(event.target.value)}
            />
            <button type="submit" disabled={loading}>{loading ? 'Loading...' : 'Check Weather'}</button>
          </form>
          <div className={`status-line${status.error ? ' error' : ''}`}>{status.text}</div>
          <div className="suggestions">
            {suggestions.length > 0 && <span>Did you mean:</span>}
            {suggestions.map((suggestion) => (
              <button key={suggestion} type="button" className="suggestion-button" onClick={() => runSearch(suggestion)}>
                {suggestion}
              </button>
            ))}
          </div>
        </section>

        <section className="content-grid">
          <article className="panel result-panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Current Result</p>
                <h2>{weather ? weather.location.display_name : 'No city selected'}</h2>
              </div>
              {weather && <span className="day-pill">{weather.is_day ? 'Day' : 'Night'}</span>}
            </div>

            {!weather && <div className="empty-state">Weather details will appear here after your first search.</div>}

            {weather && (
              <div>
                <div className="temperature-row">
                  <div>
                    <p className="metric-label">Temperature</p>
                    <p className="temperature-value">{weather.temperature_c.toFixed(1)} C</p>
                  </div>
                  <div className="summary-chip">{weather.weather_summary}</div>
                </div>

                <div className="metrics-grid">
                  <MetricCard label="Feels like" value={`${weather.apparent_temperature_c.toFixed(1)} C`} />
                  <MetricCard label="Humidity" value={`${weather.humidity_pct}%`} />
                  <MetricCard label="Wind" value={`${weather.wind_speed_kmh.toFixed(1)} km/h at ${weather.wind_direction_deg} deg`} />
                  <MetricCard label="Pressure" value={`${weather.pressure_hpa.toFixed(1)} hPa`} />
                  <MetricCard label="Precipitation" value={`${weather.precipitation_mm.toFixed(1)} mm`} />
                  <MetricCard label="Observed" value={formatDateTime(weather.observed_at)} />
                </div>

                <div className="outlook-grid">
                  <MetricCard label="High / Low" value={`${weather.daily_high_c.toFixed(1)} C / ${weather.daily_low_c.toFixed(1)} C`} />
                  <MetricCard label="Rain chance" value={`${weather.rain_chance_pct}%`} />
                  <MetricCard label="Sunrise" value={formatTime(weather.sunrise)} />
                  <MetricCard label="Sunset" value={formatTime(weather.sunset)} />
                </div>

                <div>
                  <p className="panel-kicker">Insights</p>
                  <ul className="insight-list">
                    {insights.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </article>

          <aside className="panel history-panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Saved Activity</p>
                <h2>Recent Checks</h2>
              </div>
            </div>
            <p className="history-copy">Each successful search is stored locally so you can revisit it quickly.</p>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="history-empty">No searches saved yet.</div>
              ) : (
                history.map((entry) => <HistoryItem key={entry.id} entry={entry} onSelect={runSearch} />)
              )}
            </div>
          </aside>
        </section>
      </main>
    </>
  )
}
