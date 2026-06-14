"""Academics MCP server. Owns the handbook + deadlines; exposes lookup tools.

This replaces the giant handbook PDF: sections are indexed as text chunks and a
simple keyword search returns the relevant ones (a real build could swap in an
embedding search behind the same tool signature)."""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA = json.loads((Path(__file__).parent / "data" / "handbook.json").read_text())
SECTIONS = DATA["sections"]
DEADLINES = DATA["deadlines"]

mcp = FastMCP("academics")


@mcp.tool()
def search_handbook(query: str, top_k: int = 3) -> list[dict]:
    """Search the academic handbook and return the most relevant sections.
    Use for questions about attendance, grading, registration, exam rules, etc."""
    q = set(query.lower().split())
    scored = []
    for s in SECTIONS:
        words = set((s["section"] + " " + s["text"]).lower().split())
        overlap = len(q & words)
        if overlap:
            scored.append((overlap, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]] or [{"note": "No matching handbook section."}]


@mcp.tool()
def get_deadlines() -> list[dict]:
    """List important upcoming academic deadlines (registration, fees, exams)."""
    return sorted(DEADLINES, key=lambda d: d["date"])


if __name__ == "__main__":
    mcp.run(transport="stdio")
