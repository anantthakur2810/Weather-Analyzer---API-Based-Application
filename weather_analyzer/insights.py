from __future__ import annotations

from weather_analyzer.models import WeatherReport


def build_insights(report: WeatherReport) -> list[str]:
    insights: list[str] = []
    summary = report.weather_summary.lower()

    apparent = report.apparent_temperature_c
    if apparent >= 35:
        insights.append("Heat stress is possible outdoors. Hydration and shade will matter today.")
    elif apparent >= 28:
        insights.append("Warm conditions are building. Light clothing and hydration are a good idea.")
    elif apparent <= 5:
        insights.append("Cold air is dominating, so a warm layer is recommended.")
    elif 18 <= apparent <= 26:
        insights.append("Conditions look comfortable for most outdoor plans.")
    else:
        insights.append("Temperatures are moderate, with no major comfort concerns right now.")

    if report.humidity_pct >= 80:
        insights.append("Humidity is high, so it may feel muggy even without extreme temperatures.")
    elif report.humidity_pct <= 35:
        insights.append("The air feels fairly dry, so outdoor conditions should feel more comfortable.")

    if report.rain_chance_pct >= 70 or report.precipitation_mm >= 2:
        insights.append("Rain looks likely, so carrying an umbrella would be sensible.")
    elif report.rain_chance_pct <= 20 and report.precipitation_mm == 0:
        if "clear" in summary or "partly cloudy" in summary:
            insights.append("Clear conditions and low rain probability make this a good window for travel or errands.")
        else:
            insights.append("Rain risk looks low, so travel and outdoor errands should be easier to plan.")

    if report.wind_speed_kmh >= 40:
        insights.append("Strong winds could affect driving comfort, cycling, or outdoor setups.")
    elif report.wind_speed_kmh >= 20:
        insights.append("A steady breeze is present, which can make temperatures feel a little cooler.")

    if report.pressure_hpa < 1005:
        insights.append("Lower pressure suggests unsettled weather may continue through the day.")

    if not report.is_day:
        insights.append("It is currently nighttime at this location, so visibility conditions may change quickly.")

    return insights
