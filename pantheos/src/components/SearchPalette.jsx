import { useEffect, useRef, useState } from "react";
import { Cpu, ListChecks, Radio, Satellite, Server } from "lucide-react";
import { useNav } from "../nav.jsx";

export default function SearchPalette({ onClose }) {
  const { go, tickets, projects, containers, hosts } = useNav();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const inRef = useRef(null);
  useEffect(() => { inRef.current?.focus(); }, []);

  const s = q.toLowerCase();
  const tRes = (q ? tickets.filter((t) => (t.id + t.title + t.summary).toLowerCase().includes(s)) : tickets).slice(0, 6)
    .map((t) => ({ kind: "Ticket", icon: ListChecks, t: t.title, sub: `${t.id} · ${t.area}`, k: `P${t.pri}`, go: { view: "queue", ticketId: t.id } }));
  const pRes = Object.entries(projects).filter(([, p]) => !q || p.name.toLowerCase().includes(s)).slice(0, 4)
    .map(([k, p]) => ({ kind: "Project", icon: Satellite, t: p.name, sub: p.area, k: "", go: { view: "projects", projectId: k } }));
  const cRes = containers.filter((c) => !q || c.id.toLowerCase().includes(s)).slice(0, 4)
    .map((c) => ({ kind: "Container", icon: Server, t: c.id, sub: `${projects[c.proj].name} · ${hosts[c.host].name}`, k: c.up, go: { view: "monitor", containerId: c.id } }));
  const hRes = Object.values(hosts).filter((h) => !q || h.name.toLowerCase().includes(s)).slice(0, 3)
    .map((h) => ({ kind: "Host", icon: Cpu, t: h.name, sub: h.loc, k: "", go: { view: "monitor", hostId: h.id } }));
  const groups = [["Tickets", tRes], ["Projects", pRes], ["Containers", cRes], ["Hosts", hRes]].filter(([, r]) => r.length);
  const flat = groups.flatMap(([, r]) => r);
  const pick = (i) => { const r = flat[i]; if (r) { go(r.go); onClose(); } };

  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSel((x) => Math.min(x + 1, flat.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSel((x) => Math.max(x - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); pick(sel); }
    else if (e.key === "Escape") onClose();
  };

  let idx = -1;
  return (
    <div className="gs-overlay" onClick={onClose}>
      <div className="gs-pal" onClick={(e) => e.stopPropagation()}>
        <div className="gs-pal-in">
          <Radio size={17} color="var(--ink-3)" />
          <input ref={inRef} value={q} onChange={(e) => { setQ(e.target.value); setSel(0); }} onKeyDown={onKey}
            placeholder="Search tickets, projects, containers, hosts…" />
          <kbd style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--ink-3)", border: "1px solid var(--line)", borderRadius: 4, padding: "2px 6px" }}>esc</kbd>
        </div>
        <div className="gs-pal-res">
          {flat.length === 0 ? <div className="gs-pal-empty">No matches for "{q}"</div> : groups.map(([label, rows]) => (
            <div key={label}>
              <div className="gs-pal-grp">{label}</div>
              {rows.map((r) => { idx++; const my = idx; const I = r.icon; return (
                <div key={r.t + my} className={`gs-pal-item ${sel === my ? "sel" : ""}`} onMouseEnter={() => setSel(my)} onClick={() => pick(my)}>
                  <div className="ic"><I size={15} /></div>
                  <div style={{ minWidth: 0 }}><div className="t">{r.t}</div><div className="s">{r.sub}</div></div>
                  {r.k && <span className="k">{r.k}</span>}
                </div>
              ); })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
