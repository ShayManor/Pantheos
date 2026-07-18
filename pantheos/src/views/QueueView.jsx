import { useState } from "react";
import { ArrowUpDown, Hash, ListChecks, Plus, X } from "lucide-react";
import { useNav } from "../nav.jsx";
import TicketRow from "../components/TicketRow.jsx";

export default function QueueView() {
  const { tickets, filter, setFilter, projects, openNewTicket } = useNav();
  const [hz, setHz] = useState("Queue");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("score");
  const horizons = ["Queue", "Now", "This week", "This month", "Someday", "Archived"];

  let list = tickets.filter((t) => {
    if (hz === "Archived") return t.life === "archived";
    if (t.life === "archived") return false;
    if (hz === "Now") return t.life === "active" || t.pri === 0;
    if (hz === "This week") return t.due && !t.due.includes("12d") && t.life !== "backburner";
    if (hz === "This month") return t.due;
    if (hz === "Someday") return t.life === "backburner";
    return true;
  });
  if (filter)
    list = list.filter((t) =>
      filter.kind === "area" ? t.area === filter.val
        : filter.kind === "source" ? t.source === filter.val
        : filter.kind === "project" ? t.proj === filter.val : true
    );
  if (q.trim()) {
    const s = q.toLowerCase();
    list = list.filter((t) => (t.id + t.title + t.summary).toLowerCase().includes(s));
  }
  list = [...list].sort((a, b) =>
    sort === "score" ? parseFloat(b.score) - parseFloat(a.score)
      : sort === "priority" ? a.pri - b.pri
      : (a.due ? 0 : 1) - (b.due ? 0 : 1) || 0
  );

  return (
    <>
      <div className="gs-eyebrow"><ListChecks size={13} />STATION · QUEUE</div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 3 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>Queue</h1>
        <button className="gs-btn primary" style={{ marginLeft: "auto" }} onClick={openNewTicket}>
          <Plus size={15} />New ticket
        </button>
      </div>
      <div className="gs-qtools" style={{ marginTop: 16 }}>
        <div className="gs-qsearch">
          <Hash size={14} color="var(--ink-3)" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter tickets…" />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 7, color: "var(--ink-3)" }}>
          <ArrowUpDown size={14} />
          <select className="gs-sort" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="score">Score</option>
            <option value="priority">Priority</option>
            <option value="deadline">Deadline</option>
          </select>
        </div>
      </div>
      <div className="gs-filters">
        {horizons.map((h) => (
          <button key={h} className={`gs-filter ${hz === h ? "on" : ""}`} onClick={() => setHz(h)}>{h}</button>
        ))}
        {filter && (
          <span className="gs-chip-x">
            {filter.kind}: {projects[filter.val]?.name || filter.val}
            <button onClick={() => setFilter(null)}><X size={13} /></button>
          </span>
        )}
      </div>
      {list.length === 0 ? (
        <div className="gs-card gs-empty">No tickets match.</div>
      ) : (
        <div className="gs-card">{list.map((t) => <TicketRow key={t.id} t={t} />)}</div>
      )}
    </>
  );
}
