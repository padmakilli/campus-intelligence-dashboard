"""Generates docs/architecture.svg (3D layered) and docs/sequence.svg.
Run: python docs/_gen_diagrams.py   (pure-string SVG, no dependencies)
"""
from pathlib import Path
HERE = Path(__file__).parent

SOURCE_COLORS = {
    "Library": ("#e0a43b", "#a9741d"),
    "Cafeteria": ("#3aa66b", "#1f6e44"),
    "Events": ("#e5688a", "#b13a5e"),
    "Academics": ("#4f86e0", "#2f5bb0"),
}


def _defs(grads):
    out = ['<defs>']
    for gid, (c1, c2) in grads.items():
        out.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                   f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
    out.append('<filter id="soft" x="-20%" y="-20%" width="140%" height="170%">'
               '<feDropShadow dx="0" dy="7" stdDeviation="9" flood-color="#05081e" flood-opacity="0.35"/></filter>')
    out.append('<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               '<path d="M0 0 L10 5 L0 10 z" fill="#94a3b8"/></marker>')
    out.append('</defs>')
    return "\n".join(out)


def architecture_svg() -> str:
    W, H = 1180, 940
    x, w, h, gap, depth = 300, 720, 74, 24, 12
    top = 96
    layers = [
        ("STUDENT", "asks a question in plain language", "#64748b", "#334155"),
        ("FRONTEND — React + Vite  (Vercel)", "chat assistant  •  live 'today on campus' dashboard", "#7c5cff", "#4c34b8"),
        ("ORCHESTRATOR — FastAPI  (Render)", "/api/chat   •   /api/tools   •   /api/dashboard", "#0ea5a4", "#0f766e"),
        ("AI ROUTER", "LLM tool-calling (Anthropic)  —or—  rule-based fallback (no key needed)", "#f59e0b", "#b45309"),
        ("MCP HOST", "opens a session per server  •  aggregates all tools  •  routes each call to its owner", "#22c55e", "#15803d"),
    ]
    grads = {f"g{i}": (c1, c2) for i, (_, _, c1, c2) in enumerate(layers)}
    grads.update({f"s{k}": v for k, v in SOURCE_COLORS.items()})

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">']
    parts.append(f'<rect width="{W}" height="{H}" fill="#0b1024"/>')
    parts.append(_defs(grads))
    parts.append(f'<text x="{W/2}" y="46" fill="#e2e8f0" font-size="29" font-weight="700" text-anchor="middle">Unified Campus Intelligence — Layered Architecture</text>')
    parts.append(f'<text x="{W/2}" y="73" fill="#94a3b8" font-size="14" text-anchor="middle">the assistant queries independent MCP servers live — there is no shared database</text>')

    ys = [top + i * (h + gap) for i in range(len(layers))]
    for i, (title, sub, c1, c2) in enumerate(layers):
        y = ys[i]
        parts.append(f'<rect x="{x+depth}" y="{y+depth}" width="{w}" height="{h}" rx="13" fill="{c2}" opacity="0.55"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="13" fill="url(#g{i})" filter="url(#soft)"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="#fff" opacity="0.85"/>')
        parts.append(f'<text x="{x+24}" y="{y+30}" fill="#fff" font-size="17" font-weight="700">{title}</text>')
        parts.append(f'<text x="{x+24}" y="{y+54}" fill="#f1f5f9" font-size="12.5" opacity="0.95">{sub}</text>')
        ax = x + w / 2
        parts.append(f'<line x1="{ax}" y1="{y+h+depth}" x2="{ax}" y2="{ys[i+1] if i+1 < len(layers) else y+h+gap+depth}" stroke="#94a3b8" stroke-width="2.5" marker-end="url(#arr)"/>')

    # bottom layer: 4 independent MCP servers, side by side
    by = ys[-1] + h + gap + depth + 14
    parts.append(f'<text x="{x}" y="{by-6}" fill="#cbd5e1" font-size="13" font-weight="700">INDEPENDENT MCP SERVERS — each owns its data</text>')
    names = list(SOURCE_COLORS.keys())
    tools = ["search_catalog\ncheck_availability", "get_menu\nfind_dish", "list_events\nnext_event", "search_handbook\nget_deadlines"]
    bw = (w - 3 * 16) / 4
    for j, (name, toolset) in enumerate(zip(names, tools)):
        bx = x + j * (bw + 16)
        parts.append(f'<rect x="{bx+8}" y="{by+8+depth}" width="{bw}" height="118" rx="12" fill="{SOURCE_COLORS[name][1]}" opacity="0.5"/>')
        parts.append(f'<rect x="{bx}" y="{by+8}" width="{bw}" height="118" rx="12" fill="url(#s{name})" filter="url(#soft)"/>')
        parts.append(f'<text x="{bx+bw/2}" y="{by+34}" fill="#fff" font-size="14" font-weight="700" text-anchor="middle">{name}</text>')
        for k, t in enumerate(toolset.split("\n")):
            parts.append(f'<text x="{bx+bw/2}" y="{by+58+k*16}" fill="#fff" font-size="10.5" opacity="0.92" text-anchor="middle" font-family="monospace">{t}</text>')
        parts.append(f'<rect x="{bx+bw/2-32}" y="{by+92}" width="64" height="20" rx="6" fill="rgba(0,0,0,0.28)"/>')
        parts.append(f'<text x="{bx+bw/2}" y="{by+106}" fill="#fff" font-size="9.5" text-anchor="middle" font-family="monospace">own data</text>')
        parts.append(f'<line x1="{x+w/2}" y1="{by-2}" x2="{bx+bw/2}" y2="{by+6}" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#arr)"/>')

    return "\n".join(parts) + "\n</svg>"


def sequence_svg() -> str:
    W, H = 1180, 760
    actors = ["Student", "Frontend\n(React)", "Orchestrator\n(FastAPI)", "AI Router", "MCP Host", "MCP Server\n(e.g. library)"]
    palette = ["#64748b", "#7c5cff", "#0ea5a4", "#f59e0b", "#22c55e", "#e0a43b"]
    n = len(actors); margin, top = 95, 150
    xs = [margin + i * ((W - 2 * margin) / (n - 1)) for i in range(n)]
    msgs = [
        (0, 1, "\"is Clean Code available?\"", False),
        (1, 2, "POST /api/chat", False),
        (2, 3, "answer(message)", False),
        (3, 4, "list_tools()  — 8 tools, 4 servers", False),
        (3, 4, "call_tool(search_catalog, {...})", False),
        (4, 5, "MCP tools/call (JSON-RPC over stdio)", False),
        (5, 4, "live result from its own data", True),
        (4, 3, "parsed result + source = library", True),
        (3, 2, "answer + sources", True),
        (2, 1, "{ answer, sources:[library] }", True),
        (1, 0, "answer + 'Library' station lights up", True),
    ]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">']
    parts.append(f'<rect width="{W}" height="{H}" fill="#0b1024"/>')
    parts.append('<defs><marker id="sa" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#cbd5e1"/></marker></defs>')
    parts.append(f'<text x="{W/2}" y="44" fill="#e2e8f0" font-size="28" font-weight="700" text-anchor="middle">Campus Assistant — Request Sequence</text>')
    parts.append(f'<text x="{W/2}" y="72" fill="#94a3b8" font-size="13" text-anchor="middle">one chat question, routed live to the right MCP server</text>')
    bottom = H - 36
    for i, name in enumerate(actors):
        x = xs[i]
        parts.append(f'<line x1="{x}" y1="{top+36}" x2="{x}" y2="{bottom}" stroke="#334155" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x-68}" y="{top-14}" width="136" height="50" rx="10" fill="{palette[i]}" opacity="0.96"/>')
        for j, line in enumerate(name.split("\n")):
            parts.append(f'<text x="{x}" y="{top+(8 if j==0 else 23)}" fill="#fff" font-size="{13 if j==0 else 11}" font-weight="600" text-anchor="middle">{line}</text>')
    y = top + 78
    step = (bottom - y - 16) / len(msgs)
    for a, b, label, dashed in msgs:
        xa, xb = xs[a], xs[b]
        dash = 'stroke-dasharray="6 4"' if dashed else ''
        parts.append(f'<line x1="{xa}" y1="{y}" x2="{xb}" y2="{y}" stroke="#cbd5e1" stroke-width="1.7" {dash} marker-end="url(#sa)"/>')
        parts.append(f'<text x="{(xa+xb)/2}" y="{y-7}" fill="#e2e8f0" font-size="11.5" text-anchor="middle">{label}</text>')
        y += step
    return "\n".join(parts) + "\n</svg>"


if __name__ == "__main__":
    (HERE / "architecture.svg").write_text(architecture_svg())
    (HERE / "sequence.svg").write_text(sequence_svg())
    print("wrote architecture.svg and sequence.svg")
