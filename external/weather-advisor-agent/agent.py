"""
Weather Advisor Agent — External A2A Agent
Uses Open-Meteo (free, no API key) for weather data.
Uses LangChain + Claude for activity and packing recommendations.
Exposes Google A2A protocol endpoints for SAM integration.
"""
import os
import json
import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", "10010"))

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


async def generate_recommendations(city: str, weather_data: dict) -> str:
    daily = weather_data.get("daily", {})
    dates = daily.get("time", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    weather_codes = daily.get("weathercode", [])
    precip = daily.get("precipitation_sum", [])

    weather_lines = []
    for i in range(min(len(dates), 7)):
        weather_lines.append(
            f"  {dates[i]}: {WMO_CODES.get(weather_codes[i], 'Unknown')}, "
            f"{temps_min[i]}C to {temps_max[i]}C, precipitation: {precip[i]}mm"
        )

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1024,
    )

    messages = [
        SystemMessage(content=(
            "You are a travel activity advisor. Based on the weather forecast, provide:\n"
            "1) A brief weather summary (2-3 sentences)\n"
            "2) Recommended outdoor activities for good weather days\n"
            "3) Recommended indoor activities for rainy/bad weather days\n"
            "4) A packing checklist based on the weather\n"
            "Be concise and practical. Format with clear sections."
        )),
        HumanMessage(content=(
            f"I'm traveling to {city}. Here's the 7-day weather forecast:\n"
            + "\n".join(weather_lines)
            + "\n\nProvide activity recommendations and packing list."
        )),
    ]

    response = await llm.ainvoke(messages)
    return response.content


# --- A2A Protocol Handler ---

async def handle_task(request_data: dict) -> dict:
    req_id = request_data.get("id")
    params = request_data.get("params", {})
    message = params.get("message", {})
    parts = message.get("parts", [])

    query = ""
    for part in parts:
        if part.get("type") == "text":
            query = part.get("text", "")
            break

    if not query:
        return _error_response(req_id, "No query text provided")

    city = extract_city(query)
    if not city:
        # No known prefix - treat the query as the city itself, still
        # stripping punctuation and trailing time expressions
        city = _strip_time_suffix(query.strip().rstrip("?.!").strip())

    coords = await get_coordinates(city)
    if not coords:
        return _task_response(req_id, json.dumps({"error": f"Could not find location: {city}"}))

    weather_data = await get_weather_forecast(coords["lat"], coords["lon"])
    daily = weather_data.get("daily", {})
    dates = daily.get("time", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    weather_codes = daily.get("weathercode", [])
    precip = daily.get("precipitation_sum", [])

    forecast = []
    for i in range(min(len(dates), 7)):
        forecast.append({
            "date": dates[i],
            "condition": WMO_CODES.get(weather_codes[i], "Unknown"),
            "temp_high_c": temps_max[i],
            "temp_low_c": temps_min[i],
            "precipitation_mm": precip[i],
        })

    recommendations = ""
    if ANTHROPIC_API_KEY:
        try:
            recommendations = await generate_recommendations(
                f"{coords['name']}, {coords['country']}", weather_data
            )
        except Exception as e:
            recommendations = f"(Could not generate recommendations: {e})"
    else:
        recommendations = "(No ANTHROPIC_API_KEY set — skipping AI recommendations)"

    result = {
        "location": f"{coords['name']}, {coords['country']}",
        "forecast": forecast,
        "recommendations": recommendations,
    }

    return _task_response(req_id, json.dumps(result, indent=2))


# Trailing time expressions users naturally append ("Weather in Tokyo this week")
# that would otherwise be sent to the geocoder as part of the city name.
_TIME_SUFFIXES = [
    "this week", "next week", "this weekend", "next weekend",
    "this month", "next month", "today", "tomorrow", "tonight",
    "right now", "now",
]


def _strip_time_suffix(city: str) -> str:
    lowered = city.lower()
    for suffix in _TIME_SUFFIXES:
        if lowered.endswith(suffix):
            return city[: len(city) - len(suffix)].strip().rstrip(",")
    return city


def extract_city(query: str) -> str:
    lower = query.lower()
    for prefix in ["weather in ", "weather for ", "forecast for ", "forecast in ",
                   "what's the weather in ", "weather at ", "plan trip to ",
                   "what will the weather be like in ", "rain in ", "snow in "]:
        if prefix in lower:
            city = query[lower.index(prefix) + len(prefix):].strip().rstrip("?.!").strip()
            return _strip_time_suffix(city)
    return ""


def _task_response(req_id, text: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "id": str(req_id) if req_id else "task-1",
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "text", "text": text}]}]
        }
    }


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
    "capabilities": {"streaming": False, "pushNotifications": False},
    "skills": [{
        "id": "weather-forecast",
        "name": "Weather Forecast & Activity Advisor",
        "description": (
            "Get weather forecast and activity recommendations for any city. "
            "Send the city name or a natural language question."
        ),
        "tags": ["weather", "travel", "activities", "packing"],
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
    if method == "tasks/send":
        result = await handle_task(body)
        return JSONResponse(result)
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": body.get("id"),
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
