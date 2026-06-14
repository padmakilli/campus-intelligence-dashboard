"""Cafeteria MCP server. Owns the weekly menu; exposes menu tools over MCP."""
import json
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA = json.loads((Path(__file__).parent / "data" / "cafeteria.json").read_text())
MENU = DATA["menu"]

mcp = FastMCP("cafeteria")


def _resolve_day(day: str) -> str:
    day = (day or "today").strip().lower()
    if day in ("today", ""):
        return datetime.now().strftime("%A")
    if day == "tomorrow":
        idx = (datetime.now().weekday() + 1) % 7
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][idx]
    return day.capitalize()


@mcp.tool()
def get_menu(day: str = "today") -> dict:
    """Get the cafeteria menu for a day. 'day' can be today, tomorrow, or a
    weekday name (e.g. Monday). Returns breakfast, lunch and dinner."""
    d = _resolve_day(day)
    if d not in MENU:
        return {"error": f"No menu for '{day}'. Valid days: {', '.join(MENU)}."}
    return {"day": d, **MENU[d]}


@mcp.tool()
def find_dish(dish: str) -> list[dict]:
    """Find which days and meals a given dish is served."""
    q = dish.lower().strip()
    hits = []
    for day, meals in MENU.items():
        for meal, items in meals.items():
            if q in items.lower():
                hits.append({"day": day, "meal": meal, "served": items})
    return hits or [{"note": f"'{dish}' is not on this week's menu."}]


if __name__ == "__main__":
    mcp.run(transport="stdio")
