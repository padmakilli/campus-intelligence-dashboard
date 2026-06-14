"""MCP host. Connects to every configured MCP server over stdio, aggregates
their tools, and routes a tool call to whichever server owns that tool.

This is the 'no giant database' core: the host holds no campus data itself — it
asks the live servers each time. Sessions are opened once at startup and kept
open for the app's lifetime via a single AsyncExitStack.
"""
from __future__ import annotations

import json
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPHost:
    def __init__(self, server_specs: list[dict]):
        self.specs = server_specs
        self._stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.tool_owner: dict[str, str] = {}      # tool name -> server name
        self._tools_cache: list[dict] = []

    async def start(self):
        for spec in self.specs:
            params = StdioServerParameters(command=spec["command"], args=spec["args"])
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[spec["name"]] = session
            listed = await session.list_tools()
            for t in listed.tools:
                self.tool_owner[t.name] = spec["name"]
                self._tools_cache.append({
                    "name": t.name,
                    "server": spec["name"],
                    "description": t.description or "",
                    "input_schema": t.inputSchema,
                })
        return self

    def list_tools(self) -> list[dict]:
        """Aggregated tool schemas across all servers (tagged with owner)."""
        return list(self._tools_cache)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> tuple[Any, str]:
        """Call a tool by name. Returns (parsed_result, owning_server)."""
        server = self.tool_owner.get(name)
        if server is None:
            return ({"error": f"Unknown tool '{name}'"}, "unknown")
        result = await self.sessions[server].call_tool(name, arguments)
        return (self._parse(result), server)

    @staticmethod
    def _parse(result) -> Any:
        """FastMCP returns content blocks; pull out the (JSON) text payload."""
        if getattr(result, "structuredContent", None):
            return result.structuredContent
        texts = [b.text for b in result.content if getattr(b, "type", None) == "text"]
        joined = "\n".join(texts)
        try:
            return json.loads(joined)
        except (json.JSONDecodeError, ValueError):
            return joined

    async def close(self):
        await self._stack.aclose()
