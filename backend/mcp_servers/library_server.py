"""Library MCP server. Owns the catalog; exposes catalog tools over MCP (stdio).

Run standalone for debugging:  python mcp_servers/library_server.py
Normally the orchestrator's MCP host spawns it as a subprocess.
"""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA = json.loads((Path(__file__).parent / "data" / "library.json").read_text())
BOOKS = DATA["books"]

mcp = FastMCP("library")


@mcp.tool()
def search_catalog(query: str) -> list[dict]:
    """Search the library catalog by title or author. Returns matching books
    with how many copies are available right now and where to find them."""
    q = query.lower().strip()
    return [b for b in BOOKS if q in b["title"].lower() or q in b["author"].lower()]


@mcp.tool()
def check_availability(title: str) -> dict:
    """Check if a specific book is available and where it is shelved."""
    q = title.lower().strip()
    for b in BOOKS:
        if q in b["title"].lower():
            status = "available" if b["available"] > 0 else "all copies issued"
            return {**b, "status": status}
    return {"error": f"No book matching '{title}' found in the catalog."}


if __name__ == "__main__":
    mcp.run(transport="stdio")
