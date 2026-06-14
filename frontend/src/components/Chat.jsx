import React, { useState, useRef, useEffect } from "react";
import { api, SOURCES } from "../api.js";

const SUGGESTIONS = [
  "Is Clean Code available in the library?",
  "What's for lunch today?",
  "When is the next robotics event?",
  "What's the attendance rule for exams?",
];

function SourceChip({ name }) {
  const s = SOURCES[name] || { label: name, accent: "#9aa0c8" };
  return (
    <span className="chip" style={{ "--chip": s.accent }}>
      {s.label}
    </span>
  );
}

function Message({ msg }) {
  if (msg.role === "user") {
    return <div className="msg msg--user">{msg.text}</div>;
  }
  return (
    <div className="msg msg--bot">
      <div className="msg__text">{renderAnswer(msg.text)}</div>
      {msg.sources?.length > 0 && (
        <div className="msg__sources">
          <span className="msg__sources-label">consulted</span>
          {msg.sources.map((s) => (
            <SourceChip key={s} name={s} />
          ))}
        </div>
      )}
    </div>
  );
}

// The answer text uses simple **label:** + "- item" lines; render lightly.
function renderAnswer(text) {
  return text.split("\n").map((line, i) => {
    const bold = line.match(/^\*\*(.+?)\*\*:?$/);
    if (bold) return <strong key={i} className="ans-head">{bold[1]}</strong>;
    if (line.trim().startsWith("-"))
      return <div key={i} className="ans-item">{line.replace(/^\s*-\s*/, "")}</div>;
    return <div key={i}>{line}</div>;
  });
}

export default function Chat({ onSources }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const res = await api.chat(q);
      setMessages((m) => [
        ...m,
        { role: "bot", text: res.answer, sources: res.sources, mode: res.mode },
      ]);
      onSources?.(res.sources || []);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "bot", text: `Could not reach the campus services (${e.message}). Is the backend running?`, sources: [] },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="chat" aria-label="Campus assistant">
      <div className="chat__log">
        {messages.length === 0 && (
          <div className="empty">
            <p className="empty__lead">Ask one question — it pulls live from the right campus desk.</p>
            <div className="empty__chips">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggest" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        {busy && <div className="msg msg--bot typing">checking the campus desks…</div>}
        <div ref={endRef} />
      </div>

      <div className="composer">
        <input
          className="composer__input"
          value={input}
          placeholder="Ask the campus anything…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          aria-label="Your question"
        />
        <button className="composer__send" onClick={() => send()} disabled={busy}>
          Ask
        </button>
      </div>
    </section>
  );
}
