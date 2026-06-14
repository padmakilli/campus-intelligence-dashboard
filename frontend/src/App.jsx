import React, { useEffect, useState } from "react";
import Chat from "./components/Chat.jsx";
import Dashboard from "./components/Dashboard.jsx";
import { api } from "./api.js";

export default function App() {
  const [activeSources, setActiveSources] = useState([]);
  const [mode, setMode] = useState(null);

  useEffect(() => {
    api.health().then((h) => setMode(h.mode)).catch(() => setMode("offline"));
  }, []);

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" />
          <span className="brand__name">Campus<em>Intelligence</em></span>
        </div>
        <div className={`mode mode--${mode || "loading"}`}>
          {mode === "llm" ? "AI router: LLM" : mode === "fallback" ? "AI router: rules" : mode === "offline" ? "backend offline" : "…"}
        </div>
      </header>

      <main className="layout">
        <div className="layout__chat">
          <p className="eyebrow">Ask</p>
          <h1 className="hero">One question.<br />The whole campus answers.</h1>
          <Chat onSources={setActiveSources} />
        </div>
        <aside className="layout__dash">
          <p className="eyebrow">Today on campus</p>
          <Dashboard activeSources={activeSources} />
        </aside>
      </main>

      <footer className="foot">
        Live data is fetched from independent MCP servers — no shared database.
      </footer>
    </div>
  );
}
