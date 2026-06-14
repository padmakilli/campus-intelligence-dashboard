"""The AI assistant's brain: turn a natural-language question into MCP tool
calls and a final answer.

Two modes:
  * LLM mode (when ANTHROPIC_API_KEY is set): the model sees every server's
    tools and decides which to call, in a normal tool-calling loop.
  * Fallback mode (no key): a keyword router picks the relevant server(s) and
    calls sensible default tools. Keeps the whole app demoable with no key.
"""
from __future__ import annotations

import os
import re
from typing import Any

from .mcp_host import MCPHost

SYSTEM = (
    "You are the Campus Intelligence assistant. Answer student questions about "
    "the library, cafeteria menu, campus events, and academic handbook using ONLY "
    "the provided tools. Call the tools you need, then answer concisely. If a tool "
    "returns nothing useful, say so plainly. Never invent data."
)

KEYWORDS = {
    "library":   ["book", "books", "library", "borrow", "catalog", "available", "author", "copy", "copies", "issue", "read"],
    "cafeteria": ["menu", "food", "eat", "lunch", "dinner", "breakfast", "cafeteria", "mess", "dish", "meal", "serving", "served"],
    "events":    ["event", "events", "fest", "workshop", "club", "talk", "seminar", "competition", "happening", "hackathon", "schedule", "when is"],
    "academics": ["handbook", "policy", "deadline", "deadlines", "exam", "exams", "attendance", "credit", "registration", "register", "academic", "rule", "rules", "grade", "grading", "fee", "fees"],
}


def _unwrap(x: Any) -> Any:
    """FastMCP wraps list returns as {'result': [...]}. Unwrap for display."""
    if isinstance(x, dict) and set(x.keys()) == {"result"}:
        return x["result"]
    return x


def _route(message: str) -> list[str]:
    m = message.lower()
    scores = {s: sum(1 for k in kws if k in m) for s, kws in KEYWORDS.items()}
    best = max(scores.values())
    if best == 0:
        return ["events", "cafeteria"]  # sensible default for vague questions
    return [s for s, sc in scores.items() if sc == best or sc >= max(1, best - 1)]


# ---------------------------------------------------------------- fallback mode
async def deterministic_answer(host: MCPHost, message: str) -> dict:
    servers = _route(message)
    sources, calls, findings = [], [], []

    for server in servers:
        if server == "cafeteria":
            res, _ = await host.call_tool("get_menu", {"day": "today"})
            calls.append({"tool": "get_menu", "args": {"day": "today"}})
            findings.append(("Cafeteria (today)", _unwrap(res)))
            sources.append("cafeteria")
        elif server == "events":
            res, _ = await host.call_tool("list_events", {"upcoming_only": True})
            calls.append({"tool": "list_events", "args": {"upcoming_only": True}})
            findings.append(("Upcoming events", _unwrap(res)))
            sources.append("events")
        elif server == "academics":
            res, _ = await host.call_tool("search_handbook", {"query": message})
            calls.append({"tool": "search_handbook", "args": {"query": message}})
            findings.append(("Handbook", _unwrap(res)))
            sources.append("academics")
        elif server == "library":
            hits, seen = [], set()
            for word in re.findall(r"[a-zA-Z]{3,}", message):
                res, _ = await host.call_tool("search_catalog", {"query": word})
                for b in _unwrap(res) or []:
                    if isinstance(b, dict) and b.get("title") not in seen:
                        seen.add(b.get("title")); hits.append(b)
                calls.append({"tool": "search_catalog", "args": {"query": word}})
            findings.append(("Library", hits or [{"note": "No matching book."}]))
            sources.append("library")

    answer = _render(findings)
    return {"answer": answer, "sources": sorted(set(sources)), "tool_calls": calls, "mode": "fallback"}


def _render(findings: list[tuple[str, Any]]) -> str:
    lines = []
    for label, data in findings:
        lines.append(f"**{label}:**")
        if isinstance(data, list):
            for item in data[:5]:
                lines.append("  - " + _one_line(item))
        elif isinstance(data, dict):
            lines.append("  - " + _one_line(data))
        else:
            lines.append("  - " + str(data))
    return "\n".join(lines)


def _one_line(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item)
    if "title" in item and "available" in item:
        return f"{item['title']} — {item['available']}/{item['copies']} available ({item['location']})"
    if "title" in item and "date" in item:
        return f"{item['title']} ({item['club']}) on {item['date']} {item.get('time','')} @ {item.get('venue','')}"
    if "section" in item:
        return f"{item['section']}: {item['text']}"
    if "day" in item and "lunch" in item:
        return f"{item['day']} — Breakfast: {item['breakfast']}; Lunch: {item['lunch']}; Dinner: {item['dinner']}"
    if "note" in item:
        return item["note"]
    return ", ".join(f"{k}: {v}" for k, v in item.items())


# --------------------------------------------------------------------- llm mode
async def llm_answer(host: MCPHost, message: str) -> dict:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    tools = [{"name": t["name"], "description": t["description"],
              "input_schema": t["input_schema"]} for t in host.list_tools()]

    messages = [{"role": "user", "content": message}]
    sources, calls = set(), []
    for _ in range(6):  # cap tool-calling rounds
        resp = await client.messages.create(
            model=model, max_tokens=1024, system=SYSTEM, tools=tools, messages=messages)
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": text, "sources": sorted(sources), "tool_calls": calls, "mode": "llm"}
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out, server = await host.call_tool(block.name, dict(block.input))
                sources.add(server)
                calls.append({"tool": block.name, "args": dict(block.input), "server": server})
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": str(_unwrap(out))})
        messages.append({"role": "user", "content": results})
    return {"answer": "Stopped after too many tool calls.", "sources": sorted(sources),
            "tool_calls": calls, "mode": "llm"}


async def answer(host: MCPHost, message: str) -> dict:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return await llm_answer(host, message)
        except Exception as e:  # fall back rather than fail the request
            res = await deterministic_answer(host, message)
            res["note"] = f"LLM error, used fallback: {e}"
            return res
    return await deterministic_answer(host, message)
