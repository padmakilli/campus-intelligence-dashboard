import React, { useEffect, useState } from "react";
import { api, SOURCES } from "../api.js";

function Card({ source, title, active, children }) {
  const accent = SOURCES[source]?.accent || "#9aa0c8";
  return (
    <article className={`card ${active ? "card--active" : ""}`} style={{ "--accent": accent }}>
      <header className="card__head">
        <span className="card__dot" />
        <h3>{title}</h3>
        <span className="card__src">{source}</span>
      </header>
      <div className="card__body">{children}</div>
    </article>
  );
}

export default function Dashboard({ activeSources }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  const isActive = (s) => activeSources?.includes(s);

  if (error)
    return <div className="dash dash--error">Campus services offline ({error}). Start the backend, then reload.</div>;
  if (!data) return <div className="dash dash--loading">Loading today on campus…</div>;

  const m = data.menu_today || {};
  return (
    <div className="dash">
      <Card source="cafeteria" title="Today's menu" active={isActive("cafeteria")}>
        {m.error ? (
          <p className="muted">{m.error}</p>
        ) : (
          <ul className="kv">
            <li><span>Breakfast</span>{m.breakfast}</li>
            <li><span>Lunch</span>{m.lunch}</li>
            <li><span>Dinner</span>{m.dinner}</li>
          </ul>
        )}
      </Card>

      <Card source="events" title="Upcoming events" active={isActive("events")}>
        <ul className="list">
          {(data.upcoming_events || []).map((e, i) => (
            <li key={i}>
              <strong>{e.title}</strong>
              <span className="meta">{e.club} · {e.date} {e.time} · {e.venue}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card source="academics" title="Deadlines" active={isActive("academics")}>
        <ul className="list">
          {(data.deadlines || []).map((d, i) => (
            <li key={i}>
              <strong>{d.item}</strong>
              <span className="meta">{d.date}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card source="library" title="In the library" active={isActive("library")}>
        <ul className="list">
          {(data.library_sample || []).map((b, i) => (
            <li key={i}>
              <strong>{b.title}</strong>
              <span className="meta">
                {b.available > 0 ? `${b.available}/${b.copies} available` : "all copies issued"} · {b.location}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
