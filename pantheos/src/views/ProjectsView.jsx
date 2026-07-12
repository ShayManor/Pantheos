import { useEffect, useState } from "react";
import { Activity, GitBranch, Gauge, ListChecks, Satellite, Server } from "lucide-react";
import { useNav } from "../nav.jsx";
import { StatusPill } from "../components/pills.jsx";
import TicketRow from "../components/TicketRow.jsx";
import ContainerTable from "../components/ContainerTable.jsx";
import AreaSpark from "../components/AreaSpark.jsx";
import { autoLabel, openExternal, repoUrl } from "../lib/helpers.js";
import { api } from "../api.js";

export function UsersChart() {
  const [data, setData] = useState([]);
  useEffect(() => { api.usage().then(setData); }, []);
  return <AreaSpark data={data} color="#0F7A4B" height={150} yWidth={44} gid="gu" />;
}

export default function ProjectsView() {
  const { go, tickets, projects } = useNav();
  const entries = Object.entries(projects);
  const areas = [...new Set(entries.map(([, p]) => p.area))];
  return (
    <>
      <div className="gs-eyebrow"><Satellite size={13} />STATION · PROJECTS</div>
      <h1 className="gs-h1">Projects</h1>
      {areas.map((area) => (
        <div key={area} style={{ marginBottom: 26 }}>
          <div className="gs-eyebrow" style={{ marginBottom: 12 }}>{area}</div>
          <div className="gs-grid">
            {entries.filter(([, p]) => p.area === area).map(([k, p]) => {
              const open = tickets.filter((t) => t.proj === k && t.life !== "archived").length;
              return (
                <div key={k} className="gs-card gs-pcard" onClick={() => go({ view: "projects", projectId: k })}>
                  <div className="gs-pcard-top">
                    <div><div className="gs-pcard-nm">{p.name}</div><div className="gs-pcard-area">{autoLabel(p.autonomy).toUpperCase()}</div></div>
                    <StatusPill s={p.status} />
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5 }}>{p.blurb}</div>
                  <div className="gs-pcard-metrics">
                    <div className="gs-metric"><div className="v">{open}</div><div className="l">OPEN TICKETS</div></div>
                    {p.users != null ? (
                      <div className="gs-metric"><div className="v">{p.users.toLocaleString()}</div><div className="l">USERS · 7D</div></div>
                    ) : (
                      <div className="gs-metric"><div className="v" style={{ color: "var(--ink-3)" }}>—</div><div className="l">NO ANALYTICS</div></div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </>
  );
}

export function ProjectDetail({ pk }) {
  const { go, tickets, toast, projects, containers } = useNav();
  const p = projects[pk];
  const tix = tickets.filter((t) => t.proj === pk);
  const conts = containers.filter((c) => c.proj === pk);
  return (
    <>
      <div className="gs-eyebrow">{p.area} · <span className="pill neu" style={{ textTransform: "none" }}>{autoLabel(p.autonomy)}</span></div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 6 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{p.name}</h1><StatusPill s={p.status} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {p.repo && <button className="gs-btn ghost" onClick={() => openExternal(repoUrl(p.repo))}><GitBranch size={14} />Repo</button>}
          {conts.length > 0 && <button className="gs-btn ghost" onClick={() => go({ view: "monitor", projectId: pk })}><Gauge size={14} />Monitor</button>}
        </div>
      </div>
      <p className="gs-sub">{p.blurb}</p>

      {p.users != null && (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
            <div className="gs-section-h" style={{ margin: 0 }}><Activity size={12} />DAILY ACTIVE · LAST 14 DAYS</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--ink-2)" }}><b style={{ color: "var(--ink)" }}>{p.users.toLocaleString()}</b> active</div>
          </div>
          <UsersChart />
        </div>
      )}

      {conts.length > 0 && (
        <>
          <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
          <div style={{ marginBottom: 22 }}><ContainerTable containers={conts} sub="host" /></div>
        </>
      )}

      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><ListChecks size={12} />TICKETS · {tix.length}</div>
      {tix.length === 0 ? (
        <div className="gs-card gs-empty">No tickets yet.</div>
      ) : (
        <div className="gs-card">{tix.map((t) => <TicketRow key={t.id} t={t} />)}</div>
      )}
    </>
  );
}
