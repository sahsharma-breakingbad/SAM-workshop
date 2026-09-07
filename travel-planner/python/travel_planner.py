#!/usr/bin/env python3
"""
travel_planner.py — Platform-independent Python implementation of the travel-planner toolset.

Tools:
  compile_itinerary  — Compiles flights, hotels, activities and weather into a day-by-day plan.
  calculate_budget   — Calculates a full trip budget breakdown.

SAM STR protocol (same for Python and Go tools):
  --schema              → print JSON schema for all tools, then exit
  <runner_args.json>    → read args, execute tool, write result to result_file path
"""

import json
import sys
import os
from datetime import date, timedelta, datetime


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = {
    "tools": {
        "compile_itinerary": {
            "description": "Compile all travel data (flights, hotels, activities, weather) into a structured day-by-day itinerary document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination":   {"type": "string",  "description": "Travel destination city"},
                    "travel_dates":  {"type": "string",  "description": "Travel dates (e.g. 2025-03-15 to 2025-03-20)"},
                    "flights":       {"type": "string",  "description": "JSON string of selected flight information"},
                    "hotels":        {"type": "string",  "description": "JSON string of selected hotel information"},
                    "activities":    {"type": "string",  "description": "JSON string of recommended activities"},
                    "weather":       {"type": "string",  "description": "JSON string of weather forecast"},
                    "travelers":     {"type": "integer", "description": "Number of travelers (default 1)"},
                },
                "required": ["destination", "travel_dates", "flights", "hotels"],
            },
            "artifact_params": {},
            "instructions": "",
        },
        "calculate_budget": {
            "description": "Calculate a complete trip budget breakdown including flights, hotels, meals, and activities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_cost":        {"type": "number",  "description": "Total flight cost per person"},
                    "hotel_cost":         {"type": "number",  "description": "Total hotel cost (all nights)"},
                    "num_days":           {"type": "integer", "description": "Number of trip days"},
                    "travelers":          {"type": "integer", "description": "Number of travelers (default 1)"},
                    "currency":           {"type": "string",  "description": "Currency code (default USD)"},
                    "daily_meals":        {"type": "number",  "description": "Estimated daily meals budget per person (default 50)"},
                    "daily_activities":   {"type": "number",  "description": "Estimated daily activities budget per person (default 30)"},
                },
                "required": ["flight_cost", "hotel_cost", "num_days"],
            },
            "artifact_params": {},
            "instructions": "",
        },
    }
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_date_range(date_str: str) -> list[str]:
    """Parse 'YYYY-MM-DD to YYYY-MM-DD' or 'YYYY-MM-DD - YYYY-MM-DD' into a list of date strings."""
    for sep in (" to ", " - "):
        if sep in date_str:
            parts = date_str.split(sep, 1)
            break
    else:
        return []
    try:
        start = date.fromisoformat(parts[0].strip())
        end   = date.fromisoformat(parts[1].strip())
    except ValueError:
        return []
    dates = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def try_parse_json(value):
    """Return parsed JSON if value is a non-empty string, else return the value as-is."""
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def ok(message: str, data=None) -> dict:
    result = {"message": message, "status": "success"}
    if data is not None:
        result["data"] = data
    return {"result": result, "error": ""}


def error(message: str) -> dict:
    return {"result": None, "error": message}


# ── Tool implementations ──────────────────────────────────────────────────────

def compile_itinerary(args: dict) -> dict:
    destination  = args.get("destination", "")
    travel_dates = args.get("travel_dates", "")
    travelers    = int(args.get("travelers") or 1)
    if travelers < 1:
        travelers = 1

    itinerary = {
        "destination":  destination,
        "travel_dates": travel_dates,
        "travelers":    travelers,
        "compiled_at":  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    for key, field in [("flights", "flights"), ("hotels", "accommodation"),
                        ("activities", "activities"), ("weather", "weather_forecast")]:
        val = args.get(key)
        if val:
            itinerary[field] = try_parse_json(val)

    dates = parse_date_range(travel_dates)
    if dates:
        days = []
        for i, d in enumerate(dates):
            if i == 0:
                note = "Arrival day"
            elif i == len(dates) - 1:
                note = "Departure day"
            else:
                note = "Exploration day"
            days.append({"day": i + 1, "date": d, "note": note})
        itinerary["day_by_day"] = days
        itinerary["total_days"] = len(dates)

    return ok("Itinerary compiled successfully", itinerary)


def calculate_budget(args: dict) -> dict:
    try:
        flight_cost = float(args.get("flight_cost", 0))
        hotel_cost  = float(args.get("hotel_cost", 0))
        num_days    = int(args.get("num_days", 0))
    except (TypeError, ValueError) as e:
        return error(f"Invalid numeric argument: {e}")

    travelers        = int(args.get("travelers") or 1)
    currency         = str(args.get("currency") or "USD")
    daily_meals      = float(args.get("daily_meals") or 50.0)
    daily_activities = float(args.get("daily_activities") or 30.0)

    if travelers < 1:
        travelers = 1

    total_flights    = flight_cost * travelers
    total_hotel      = hotel_cost
    total_meals      = daily_meals * num_days * travelers
    total_activities = daily_activities * num_days * travelers
    grand_total      = total_flights + total_hotel + total_meals + total_activities

    result = {
        "currency":  currency,
        "travelers": travelers,
        "days":      num_days,
        "breakdown": {
            "flights":    f"{total_flights:.2f}",
            "hotel":      f"{total_hotel:.2f}",
            "meals":      f"{total_meals:.2f}",
            "activities": f"{total_activities:.2f}",
        },
        "grand_total": f"{grand_total:.2f} {currency}",
        "per_person":  f"{grand_total / travelers:.2f} {currency}",
    }

    return ok("Budget calculated successfully", result)


# ── STR dispatch ──────────────────────────────────────────────────────────────

TOOLS = {
    "compile_itinerary": compile_itinerary,
    "calculate_budget":  calculate_budget,
}


def main():
    args = sys.argv[1:]

    # --schema mode: print tool schemas and exit
    if args and args[0] == "--schema":
        print(json.dumps(SCHEMA))
        sys.exit(0)

    # Normal execution: first arg is path to runner_args.json
    if not args:
        print("usage: travel_planner.py --schema | <runner_args.json>", file=sys.stderr)
        sys.exit(1)

    runner_args_path = args[0]
    try:
        with open(runner_args_path) as f:
            runner_args = json.load(f)
    except Exception as e:
        print(f"ERROR: could not read runner_args: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name   = runner_args.get("tool_name", "")
    tool_args   = runner_args.get("args", {})
    result_file = runner_args.get("result_file", "")
    status_pipe = runner_args.get("status_pipe", "")

    # Optional: write a status update to the status pipe
    if status_pipe:
        try:
            with open(status_pipe, "w") as sp:
                sp.write(json.dumps({"message": f"Running {tool_name}..."}) + "\n")
        except Exception:
            pass

    handler = TOOLS.get(tool_name)
    if handler is None:
        result = error(f"tool '{tool_name}' not found in travel_planner.py")
    else:
        try:
            result = handler(tool_args)
        except Exception as e:
            result = error(f"tool '{tool_name}' raised an exception: {e}")

    if result_file:
        try:
            with open(result_file, "w") as f:
                json.dump(result, f)
        except Exception as e:
            print(f"ERROR: could not write result_file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # No result_file — print to stdout (useful for local testing)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
