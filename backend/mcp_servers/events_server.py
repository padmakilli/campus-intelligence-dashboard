"""Events MCP server. Owns club/campus events; exposes event tools over MCP."""
import json
from datetime import date
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA = json.loads((Path(__file__).parent / "data" / "events.json").read_text())
EVENTS = sorted(DATA["events"], key=lambda e: (e["date"], e["time"]))

mcp = FastMCP("events")


@mcp.tool()
def list_events(club: str = "", upcoming_only: bool = True) -> list[dict]:
    """List campus events. Optionally filter by club name. By default only
    events today or later are returned."""
    today = date.today().isoformat()
    out = EVENTS
    if upcoming_only:
        out = [e for e in out if e["date"] >= today]
    if club.strip():
        c = club.lower().strip()
        out = [e for e in out if c in e["club"].lower()]
    return out


@mcp.tool()
def next_event(query: str = "") -> dict:
    """Get the soonest upcoming event, optionally matching a keyword in the
    title or club (e.g. 'robotics', 'music', 'placement')."""
    today = date.today().isoformat()
    q = query.lower().strip()
    for e in EVENTS:
        if e["date"] < today:
            continue
        if not q or q in e["title"].lower() or q in e["club"].lower():
            return e
    return {"note": f"No upcoming events matching '{query}'."}


if __name__ == "__main__":
    mcp.run(transport="stdio")
