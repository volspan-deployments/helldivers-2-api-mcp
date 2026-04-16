from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("Helldivers 2 Community API")

BASE_URL = "https://api.helldivers2.dev"
CLIENT_NAME = "helldivers2-fastmcp-server"


def get_headers(language: str = "en-US") -> dict:
    return {
        "Accept-Language": language,
        "X-Super-Client": CLIENT_NAME,
        "Accept": "application/json",
    }


@mcp.tool()
async def get_war_status(language: str = "en-US") -> dict:
    """Retrieve the current war status and season information for Helldivers 2.
    Use this to get the overall state of the ongoing galactic war, including
    active war season, time info, and global statistics. Good starting point
    for any war-related query."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/war",
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_planets(
    planet_index: Optional[int] = None,
    language: str = "en-US",
) -> dict:
    """Retrieve information about all planets or a specific planet in the
    Helldivers 2 galaxy. Use this to get planet details such as faction control,
    liberation percentage, player count, health, and planetary hazards. Use when
    users ask about specific planets or want to find planets under attack."""
    async with httpx.AsyncClient() as client:
        if planet_index is not None:
            url = f"{BASE_URL}/api/v1/planets/{planet_index}"
        else:
            url = f"{BASE_URL}/api/v1/planets"
        response = await client.get(
            url,
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_campaigns(language: str = "en-US") -> dict:
    """Retrieve all active campaigns currently happening in the Helldivers 2
    galactic war. Use this to find out which planets have active defense or
    liberation campaigns, including campaign type, progress, and involved
    factions. Use when users want to know where the current major battles are."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/campaigns",
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_assignments(language: str = "en-US") -> dict:
    """Retrieve current major orders and assignments in Helldivers 2. Use this
    when users want to know what the current major order is, its objectives,
    rewards, and deadline. This is the in-game 'Major Order' information that
    guides the community's collective effort."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/assignments",
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_dispatches(language: str = "en-US") -> dict:
    """Retrieve recent dispatches (in-game news and messages from Super Earth
    High Command) from Helldivers 2. Use this to get the latest lore-flavored
    news updates, announcements, and narrative messages broadcast to players.
    Useful when users want the latest in-game story updates."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/dispatches",
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_steam_news(count: int = 10) -> dict:
    """Retrieve the latest Steam news and patch notes for Helldivers 2. Use this
    when users ask about recent game updates, patch notes, events, or
    announcements posted by the developers on Steam. Good for staying up to
    date with game changes."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/steam",
            params={"count": count},
            headers=get_headers(),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_war_history(
    planet_index: Optional[int] = None,
    language: str = "en-US",
) -> dict:
    """Retrieve historical snapshot or summary data about past events in the
    Helldivers 2 galactic war. Use this to look up information about previously
    liberated or lost planets, past campaigns, and war history. Useful when
    users want context about how the war has progressed over time."""
    async with httpx.AsyncClient() as client:
        if planet_index is not None:
            url = f"{BASE_URL}/api/v1/planets/{planet_index}/history"
        else:
            url = f"{BASE_URL}/api/v1/war/history"
        response = await client.get(
            url,
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_raw_data(
    endpoint: str,
    language: str = "en-US",
) -> dict:
    """Retrieve raw unprocessed data directly from the ArrowHead API endpoints
    via the community wrapper's /raw endpoints. Use this when you need low-level
    or unformatted game data not covered by other endpoints, or when debugging
    discrepancies between community and official data. Prefer this over directly
    calling ArrowHead's API to reduce load on their servers.

    The 'endpoint' parameter should be the raw endpoint path to call
    (e.g. 'WarSeason/801/Status', 'WarSeason/801/WarInfo')."""
    endpoint = endpoint.lstrip("/")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/raw/{endpoint}",
            headers=get_headers(language),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()




_SERVER_SLUG = "helldivers-2-api"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

sse_app = mcp.http_app(transport="sse")

app = Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", sse_app),
    ],
    lifespan=sse_app.lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
