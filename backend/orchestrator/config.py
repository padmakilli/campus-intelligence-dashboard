"""Which MCP servers the host launches. Each is an independent process with its
own code and data — there is no shared database."""
import sys
from pathlib import Path

SERVERS_DIR = Path(__file__).resolve().parent.parent / "mcp_servers"

SERVER_SPECS = [
    {"name": "library",   "command": sys.executable, "args": [str(SERVERS_DIR / "library_server.py")]},
    {"name": "cafeteria", "command": sys.executable, "args": [str(SERVERS_DIR / "cafeteria_server.py")]},
    {"name": "events",    "command": sys.executable, "args": [str(SERVERS_DIR / "events_server.py")]},
    {"name": "academics", "command": sys.executable, "args": [str(SERVERS_DIR / "academics_server.py")]},
]
