import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Boxes, ChevronRight, SignalZero, Terminal } from "lucide-react";
import { useNav } from "../nav.jsx";
import { StatusPill } from "../components/pills.jsx";
import AreaSpark from "../components/AreaSpark.jsx";
import { openExternal, registryUrl } from "../lib/helpers.js";
import { api } from "../api.js";

export default function ContainerDetail({ id }) {
  const { go, toast, projects, hosts, containers, tickets } = useNav();
  const c = containers.find((x) => x.id === id);
  const p = projects[c.proj], h = hosts[c.host];
  const [series, setSeries] = useState([]);
  useEffect(() => { api.containerMetrics(id).then((d) => setSeries(d.series)); }, [id]);
  const off = c.up === "LOS";
  const relTicket = tickets.find((t) => t.proj === c.proj && t.source === "alert");
  const tiles = [
    ["CPU", c.cpu, c.status === "flt"], ["MEMORY", c.mem, false], ["5XX RATE", c.err, c.status === "flt"],
    ["REQ/S", c.rps, false], ["P95 LATENCY", c.p95, false], ["RESTARTS · 1H", String(c.restarts), c.restarts > 2],
  ];
  return (
    <>
      <div className="gs-eyebrow">
        <span className="gs-linkable" onClick={() => go({ view: "monitor", projectId: c.proj })} style={{ fontFamily: "var(--mono)" }}>{p.name}</span><span>·</span>
        <span className="gs-linkable" onClick={() => go({ view: "monitor", hostId: c.host })}>{h.name}</span><span>·</span><span>{c.role}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 4 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{c.id}</h1><StatusPill s={c.status} />
      </div>
      <p className="gs-sub" style={{ fontFamily: "var(--mono)", fontSize: 12 }}>
        <span className="gs-ref" onClick={() => openExternal(registryUrl(c.image))}>{c.image}</span>
      </p>

      {c.status === "flt" && relTicket && (
        <div className="gs-card" style={{ padding: "12px 15px", marginBottom: 20, background: "var(--fault-soft)", borderColor: "var(--fault-line)", cursor: "pointer" }}
          onClick={() => go({ view: "queue", ticketId: relTicket.id })}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", color: "var(--fault)", fontSize: 13 }}>
            <AlertTriangle size={15} /><span>Fault filed as <b>{relTicket.id}</b> — {relTicket.title}</span>
            <ChevronRight size={15} style={{ marginLeft: "auto" }} />
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(120px,1fr))", gap: 12, marginBottom: 22 }}>
        {tiles.map(([l, v, hot]) => (
          <div key={l} className="gs-card" style={{ padding: "14px 15px" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em",
              color: hot ? "var(--fault)" : off ? "var(--ink-3)" : "var(--ink)" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>

      {off ? (
        <div className="gs-card" style={{ padding: "14px 16px", marginBottom: 22, background: "var(--surface-2)" }}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", color: "var(--ink-2)", fontSize: 13 }}>
            <SignalZero size={16} /><span>Loss of signal · last reported 3h ago. Intermittent host, no alert.</span>
          </div>
        </div>
      ) : (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div className="gs-section-h" style={{ marginBottom: 14 }}><Activity size={12} />{["gs-platform", "rviewer"].includes(c.id) ? "REQ/MIN · LAST 20 MIN" : "CPU · LAST 20 MIN"}</div>
          <AreaSpark data={series} color={c.status === "flt" ? "#BF3A3A" : "#0F7A4B"} height={120} yWidth={40} gid="gc" />
        </div>
      )}

      <div className="gs-card gs-meta-card">
        <div className="gs-meta-row"><span className="gs-meta-k">project</span>
          <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "monitor", projectId: c.proj })}>{p.name} ›</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">host</span>
          <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "monitor", hostId: c.host })}>{h.name} ›</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">role</span><span className="gs-meta-v">{c.role}</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">image</span>
          <span className="gs-meta-v gs-linkable" onClick={() => openExternal(registryUrl(c.image))}>{c.image} ↗</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">restart policy</span><span className="gs-meta-v">always</span></div>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button className="gs-btn ghost" onClick={() => go({ view: "monitor", containerId: c.id, logs: true })}><Terminal size={15} />View logs</button>
        <button className="gs-btn ghost" onClick={() => openExternal(registryUrl(c.image))}><Boxes size={15} />Registry</button>
      </div>
    </>
  );
}
