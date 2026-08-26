"""
Places MCP Server — Exposes restaurant and attraction search tools
via the Model Context Protocol (MCP) over legacy SSE transport.

SAM Desktop uses the legacy SSE transport:
  GET  /mcp          opens SSE stream, server sends endpoint event
  POST /messages/    SAM posts JSON-RPC messages here

Uses Foursquare Legacy Places API v2 (client_id + client_secret auth).
"""
import os
import json
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp import types
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

FSQ_CLIENT_ID = os.environ.get("FOURSQUARE_CLIENT_ID", "")
FSQ_CLIENT_SECRET = os.environ.get("FOURSQUARE_CLIENT_SECRET", "")
FSQ_BASE_URL = "https://api.foursquare.com/v2/venues/search"
FSQ_VERSION = "20231001"

# v2 category IDs
RESTAURANT_CATEGORY = "4d4b7105d754a06374d81259"
CATEGORY_MAP = {
    "museums":   "4bf58dd8d48988d181941735",
    "parks":     "4bf58dd8d48988d163941735",
    "landmarks": "4bf58dd8d48988d12d941735",
    "nightlife": "4d4b7105d754a06376d81259",
    "shopping":  "4d4b7105d754a06378d81259",
}

TOOLS = [
    types.Tool(
        name="find_restaurants",
        description="Find restaurants near a location. Returns name, cuisine type, and address.",
        inputSchema={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or place name (e.g. 'Paris, France')"},
                "cuisine": {"type": "string", "description": "Optional cuisine filter (e.g. 'italian', 'japanese')"},
                "limit": {"type": "integer", "description": "Max results (default 8)", "default": 8},
            },
            "required": ["location"],
        },
    ),
    types.Tool(
        name="find_attractions",
        description="Find tourist attractions and points of interest near a location.",
        inputSchema={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or place name (e.g. 'Tokyo, Japan')"},
                "category": {"type": "string", "description": "Category: museums, parks, landmarks, nightlife, shopping"},
                "limit": {"type": "integer", "description": "Max results (default 8)", "default": 8},
            },
            "required": ["location"],
        },
    ),
]


async def foursquare_search(params: dict) -> list:
    params.update({
        "client_id": FSQ_CLIENT_ID,
        "client_secret": FSQ_CLIENT_SECRET,
        "v": FSQ_VERSION,
    })
    async with httpx.AsyncClient() as client:
        resp = await client.get(FSQ_BASE_URL, params=params)
    if resp.status_code != 200:
        return [{"error": f"Foursquare API error: {resp.status_code}", "detail": resp.text}]
    places = []
    for venue in resp.json().get("response", {}).get("venues", []):
        loc = venue.get("location", {})
        cats = venue.get("categories", [])
        formatted = loc.get("formattedAddress", [])
        places.append({
            "name": venue.get("name"),
            "category": cats[0].get("name", "Unknown") if cats else "Unknown",
            "address": ", ".join(formatted) if formatted else "N/A",
            "city": loc.get("city"),
            "country": loc.get("country"),
        })
    return places


async def handle_list_tools(ctx, params):
    return types.ListToolsResult(tools=TOOLS)


async def handle_call_tool(ctx, params: types.CallToolRequestParams):
    name = params.name
    args = params.arguments or {}

    if name == "find_restaurants":
        search_params = {
            "near": args.get("location", ""),
            "categoryId": RESTAURANT_CATEGORY,
            "limit": args.get("limit", 8),
            "intent": "browse",
        }
        if args.get("cuisine"):
            search_params["query"] = args["cuisine"]
        results = await foursquare_search(search_params)

    elif name == "find_attractions":
        cat_id = CATEGORY_MAP.get(args.get("category", ""), "4d4b7105d754a06372d81259")
        search_params = {
            "near": args.get("location", ""),
            "categoryId": cat_id,
            "limit": args.get("limit", 8),
            "intent": "browse",
        }
        results = await foursquare_search(search_params)

    else:
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Unknown tool: {name}")]
        )

    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(results, indent=2))]
    )


# MCP server
mcp_server = Server(
    "places-mcp-server",
    on_list_tools=handle_list_tools,
    on_call_tool=handle_call_tool,
)

# Legacy SSE transport — SAM Desktop uses GET for SSE stream, POST for messages
sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    """SAM Desktop connects here with GET, receives SSE stream + endpoint event."""
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read, write):
        await mcp_server.run(read, write, mcp_server.create_initialization_options())


async def health(request: Request):
    return JSONResponse({"status": "healthy", "server": "places-mcp-server", "endpoint": "/mcp"})


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/mcp", handle_sse),                          # SAM connects here (GET)
        Mount("/messages/", app=sse.handle_post_message),   # SAM posts here
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3010"))
    host = os.environ.get("HOST", "::")  # dual-stack for localhost on macOS
    print(f"Places MCP Server starting on port {port}")
    print(f"MCP endpoint: http://localhost:{port}/mcp")
    uvicorn.run("server:app", host=host, port=port, timeout_keep_alive=120)
