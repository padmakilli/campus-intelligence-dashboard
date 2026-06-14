const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function getJSON(path, opts) {
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  dashboard: () => getJSON("/api/dashboard"),
  health: () => getJSON("/api/health"),
  chat: (message) =>
    getJSON("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }),
};

// Source identity shared by chips and dashboard cards.
export const SOURCES = {
  library:   { label: "Library",   accent: "#e0a43b" },
  cafeteria: { label: "Cafeteria", accent: "#3aa66b" },
  events:    { label: "Events",    accent: "#e5688a" },
  academics: { label: "Academics", accent: "#4f86e0" },
};
