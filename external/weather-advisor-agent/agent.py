"""
Weather Advisor Agent — External A2A Agent
Uses Open-Meteo (free, no API key) for weather data.
Uses LangChain + Claude for activity and packing recommendations.
Exposes Google A2A protocol endpoints for SAM integration.
"""
import os
import re
import json
import logging
import httpx
import uvicorn
from datetime import date, timedelta
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("weather-agent")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://lite-llm.mymaas.net")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
PORT = int(os.environ.get("PORT", "10000"))

# --- Open-Meteo Integration (completely free, no API key) ---

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm",
}


async def get_coordinates(city: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(GEOCODING_URL, params={"name": city, "count": 1})
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    return {
        "lat": results[0]["latitude"],
        "lon": results[0]["longitude"],
        "name": results[0].get("name", city),
        "country": results[0].get("country", ""),
    }


async def get_weather_forecast(lat: float, lon: float, days: int = 7):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": min(days, 16),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(FORECAST_URL, params=params)
    return resp.json()


def generate_recommendations(weather_data: dict) -> str:
    daily = weather_data.get("daily", {})
    weather_codes = daily.get("weathercode", [])
    temps_max = daily.get("temperature_2m_max", [])
    precip = daily.get("precipitation_sum", [])

    rainy_days = sum(1 for c in weather_codes[:7] if c in {51,53,55,61,63,65,71,73,75,80,81,82,95,96,99})
    hot_days = sum(1 for t in temps_max[:7] if t and t >= 28)
    heavy_rain = any(p and p >= 10 for p in precip[:7])

    packing = ["comfortable walking shoes", "reusable water bottle"]
    activities_out = ["explore local markets and parks on clear days"]
    activities_in = ["visit museums and indoor attractions on rainy days"]

    if rainy_days >= 3:
        packing.append("compact umbrella (essential)")
        if heavy_rain:
            packing.append("light rain jacket or poncho")
    if hot_days >= 3:
        packing += ["lightweight breathable clothing", "sunscreen SPF 50+"]
        activities_out.append("morning sightseeing before peak heat")
        activities_in.append("air-conditioned shopping malls and galleries")

    summary_parts = []
    if hot_days >= 3:
        summary_parts.append(f"hot and humid ({int(max(t for t in temps_max[:7] if t))}°C peak)")
    if rainy_days >= 4:
        summary_parts.append("mostly wet — carry an umbrella daily")
    elif rainy_days >= 2:
        summary_parts.append(f"mixed — {rainy_days} rainy days expected")
    else:
        summary_parts.append("generally clear")

    summary = "Conditions: " + ", ".join(summary_parts) + "."
    return (
        summary + "\n"
        "Outdoor: " + "; ".join(activities_out) + ".\n"
        "Indoor: " + "; ".join(activities_in) + ".\n"
        "Pack: " + ", ".join(packing) + "."
    )


# --- A2A Protocol Handler ---

async def handle_task(request_data: dict, use_message_format: bool = False) -> dict:
    req_id = request_data.get("id")
    params = request_data.get("params", {})
    message = params.get("message", {})
    task_id = params.get("taskId") or message.get("taskId")
    context_id = params.get("contextId") or message.get("contextId")

    def respond(rid, text):
        if use_message_format:
            return _message_response(rid, text, task_id=task_id, context_id=context_id)
        return _task_response(rid, text)

    parts = message.get("parts", [])

    query = ""
    for part in parts:
        if part.get("type") == "text" or part.get("kind") == "text":
            query = part.get("text", "")
            break

    if not query:
        return _error_response(req_id, "No query text provided")

    city = extract_city(query)
    if not city:
        city = query.strip()

    coords = await get_coordinates(city)
    if not coords:
        return respond(req_id, json.dumps({"error": f"Could not find location: {city}"}))

    start_date, end_date = extract_dates(query)
    today = date.today()
    forecast_window_end = today + timedelta(days=15)  # Open-Meteo max: 16 days (0-indexed)

    weather_data = await get_weather_forecast(coords["lat"], coords["lon"])
    daily = weather_data.get("daily", {})
    dates = daily.get("time", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    weather_codes = daily.get("weathercode", [])
    precip = daily.get("precipitation_sum", [])

    # Determine which rows to show
    forecast_lines = []
    date_note = ""

    if start_date and start_date > forecast_window_end:
        # Requested dates entirely outside the forecast window
        date_note = (
            f"\n> **Note**: Open-Meteo only provides forecasts up to 16 days ahead "
            f"(through {forecast_window_end.strftime('%b %d')}). "
            f"The requested dates ({start_date.strftime('%b %d')} – {end_date.strftime('%b %d')}) "
            f"are outside the forecast window. Showing the nearest available forecast instead.\n"
        )
        rows = range(min(len(dates), 7))
    elif start_date:
        # Filter to rows that fall within the requested date range
        rows = [
            i for i, d in enumerate(dates)
            if start_date <= date.fromisoformat(d) <= end_date
        ]
        if not rows:
            date_note = (
                f"\n> **Note**: No forecast data available for "
                f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d')} "
                f"(beyond the 16-day window). Showing nearest available forecast.\n"
            )
            rows = range(min(len(dates), 7))
        elif end_date > forecast_window_end:
            date_note = (
                f"\n> **Note**: Forecast only available through {forecast_window_end.strftime('%b %d')}. "
                f"Dates beyond that are outside the 16-day Open-Meteo window.\n"
            )
    else:
        rows = range(min(len(dates), 7))

    for i in rows:
        forecast_lines.append(
            f"- {dates[i]}: {WMO_CODES.get(weather_codes[i], 'Unknown')}, "
            f"{temps_min[i]}°C – {temps_max[i]}°C, precipitation: {precip[i]}mm"
        )

    location = f"{coords['name']}, {coords['country']}"
    forecast_text = (
        f"**Weather Forecast for {location}**"
        + (f" ({start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')})" if start_date else "")
        + date_note + "\n\n"
        + "\n".join(forecast_lines)
    )

    recommendations = generate_recommendations(weather_data)
    output = forecast_text + "\n\n" + recommendations

    return respond(req_id, output)


_MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def extract_dates(query: str):
    """Return (start_date, end_date) parsed from the query, or (None, None)."""
    found = []
    current_year = date.today().year

    # "September 15, 2026" / "Sep 15 2026" / "September 15"
    for m in re.finditer(
        r'(january|february|march|april|may|june|july|august|september|october|november|december'
        r'|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:[,\s]+(\d{4}))?',
        query.lower()
    ):
        month, day, year = _MONTHS[m.group(1)], int(m.group(2)), int(m.group(3) or current_year)
        try:
            found.append(date(year, month, day))
        except ValueError:
            pass

    # "2026-09-15"
    for m in re.finditer(r'(\d{4})-(\d{2})-(\d{2})', query):
        try:
            found.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass

    found.sort()
    if len(found) >= 2:
        return found[0], found[-1]
    if len(found) == 1:
        return found[0], found[0] + timedelta(days=6)
    return None, None


def extract_city(query: str) -> str:
    # Strip SAM orchestrator wrapper if present
    if "Now please execute this task that was given to you:" in query:
        query = query.split("Now please execute this task that was given to you:")[-1].strip()

    lower = query.lower()
    stoppers = [
        " for ", " for next", " for the ", " next week", " this week", " in the coming",
        " from ", ". ", "?\n", "!\n", "\n", ". include", ", include",
    ]
    for prefix in [
        "weather forecast for ", "weather in ", "weather for ",
        "forecast for ", "forecast in ", "what's the weather in ",
        "weather at ", "plan trip to ", "what will the weather be like in ",
    ]:
        if prefix in lower:
            idx = lower.index(prefix) + len(prefix)
            candidate = query[idx:].strip()
            for stopper in stoppers:
                stop_idx = candidate.lower().find(stopper)
                if 0 < stop_idx:
                    candidate = candidate[:stop_idx]
            # Strip parenthetical content (e.g. "(Denpasar)" or "(latitude -8.67, longitude 115.2)")
            paren_idx = candidate.find(" (")
            if paren_idx > 0:
                candidate = candidate[:paren_idx]
            return candidate.strip().rstrip(",.?!)")
    return ""


def _task_response(req_id, text: str) -> dict:
    """Response format for old tasks/send spec."""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "id": str(req_id) if req_id else "task-1",
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "text", "text": text}]}]
        }
    }


def _message_response(req_id, text: str, task_id: str = None, context_id: str = None) -> dict:
    """Response format for message/send — Task with completed status (SAM proxy expects this)."""
    result = {
        "id": task_id or str(req_id) or "task-1",
        "status": {
            "state": "completed",
            "message": {
                "role": "agent",
                "parts": [{"kind": "text", "text": text}]
            }
        }
    }
    if context_id:
        result["contextId"] = context_id
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error_response(req_id, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32600, "message": message}
    }


# --- A2A Agent Card ---

AGENT_CARD = {
    "name": "WeatherAdvisorAgent",
    "description": (
        "Provides weather forecasts and activity recommendations for travel "
        "destinations. Uses Open-Meteo for accurate weather data and Claude AI "
        "for personalized activity and packing suggestions."
    ),
    "url": os.environ.get("AGENT_BASE_URL", f"http://localhost:{PORT}"),
    "version": "1.0.0",
    "protocolVersion": "0.2.1",
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False,
    },
    "skills": [{
        "id": "weather-forecast",
        "name": "Weather Forecast & Activity Advisor",
        "description": (
            "Get weather forecast and activity recommendations for any city. "
            "Send the city name or a natural language question."
        ),
        "tags": ["weather", "travel", "activities", "packing"],
        "inputModes": ["text/plain"],
        "outputModes": ["text/plain"],
        "examples": [
            "What's the weather like in Tokyo?",
            "Weather forecast for Barcelona",
            "Will it rain in London next week?",
        ]
    }]
}


# --- HTTP Routes ---

async def agent_card(request: Request):
    return JSONResponse(AGENT_CARD)


async def handle_a2a(request: Request):
    body = await request.json()
    method = body.get("method", "")
    req_id = body.get("id")
    log.info("A2A request — method=%s id=%s body=%s", method, req_id, json.dumps(body))
    if method in ("tasks/send", "message/send"):
        result = await handle_task(body, use_message_format=(method == "message/send"))
        log.info("A2A response — %s", json.dumps(result))
        return JSONResponse(result)
    log.warning("Unknown method: %s", method)
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    })


async def health(request: Request):
    return JSONResponse({"status": "healthy", "agent": "WeatherAdvisorAgent"})


app = Starlette(routes=[
    Route("/.well-known/agent.json", agent_card),
    Route("/.well-known/agent-card.json", agent_card),  # SAM Desktop tries this path first
    Route("/", handle_a2a, methods=["POST"]),
    Route("/health", health),
])

if __name__ == "__main__":
    print(f"WeatherAdvisorAgent (A2A) starting on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
