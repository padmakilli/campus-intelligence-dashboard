"""FastAPI orchestrator. The single web backend the frontend talks to.

Endpoints:
  GET  /api/health       basic status + which router mode is active
  GET  /api/tools        aggregated MCP tools across all servers
  POST /api/chat         {message} -> answer + which sources were used
  GET  /api/dashboard    live cards pulled straight from the MCP servers

Run:  uvicorn orchestrator.main:app --reload --port 8000  (from backend/)
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import SERVER_SPECS
from .mcp_host import MCPHost
from .llm import answer, _unwrap


@asynccontextmanager
async def lifespan(app: FastAPI):
    host = await MCPHost(SERVER_SPECS).start()
    app.state.host = host
    try:
        yield
    finally:
        await host.close()


app = FastAPI(title="Campus Intelligence Dashboard", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class ChatIn(BaseModel):
    message: str


@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": "llm" if os.getenv("ANTHROPIC_API_KEY") else "fallback"}


@app.get("/api/tools")
async def tools():
    return {"tools": app.state.host.list_tools()}


@app.post("/api/chat")
async def chat(body: ChatIn):
    return await answer(app.state.host, body.message)


@app.get("/api/dashboard")
async def dashboard():
    """One view, many live sources — fetched from the MCP servers on each call."""
    host = app.state.host
    menu, _ = await host.call_tool("get_menu", {"day": "today"})
    events, _ = await host.call_tool("list_events", {"upcoming_only": True})
    deadlines, _ = await host.call_tool("get_deadlines", {})
    new_books, _ = await host.call_tool("search_catalog", {"query": "a"})
    return {
        "menu_today": _unwrap(menu),
        "upcoming_events": (_unwrap(events) or [])[:4],
        "deadlines": (_unwrap(deadlines) or [])[:4],
        "library_sample": (_unwrap(new_books) or [])[:4],
    }
