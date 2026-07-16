import { useEffect, useState } from "react";
import {
  Activity, AlertTriangle, Cpu, Gauge, ListChecks, Satellite, Server, Signal, SignalZero,
} from "lucide-react";
import { useNav } from "../nav.jsx";
import { StatusPill } from "../components/pills.jsx";
import ContainerTable from "../components/ContainerTable.jsx";
import AreaSpark from "../components/AreaSpark.jsx";
import { UsersChart } from "./ProjectsView.jsx";
import { HOST_ICONS, rollup } from "../lib/helpers.js";
import { api } from "../api.js";

export default function MonitorView({ mode, setMode }) {
  const { go, containers, projects, hosts } = useNav();
  const byHost = (hid) => containers.filter((c) => c.host === hid);
  const byProject = (pk) => containers.filter((c) => c.proj === pk);
  const monProjects = [...new Set(containers.map((c) => c.proj))];
  const faults = containers.filter((c) => c.status === "flt").length;
  const firstFault = containers.find((c) => c.status === "flt")?.id;
  const hostList = Object.values(hosts);
  const hostsOnline = hostList.filter((h) => h.kind === "always_on" || !byHost(h.id).every((c) => c.status === "los")).length;
  const activeUsers = Object.values(projects).reduce((s, p) => s + (p.users || 0), 0);

  return (
    <>
      <div className="gs-eyebrow"><Gauge size={13} />STATION · MONITOR</div>
      <h1 className="gs-h1">Monitor</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 14, marginBottom: 22 }}>
        {[["ACTIVE USERS · 7D", activeUsers.toLocaleString(), "go", null],
          ["FAULTS", String(faults), faults ? "flt" : "go", faults ? "faults" : null],
          ["HOSTS ONLINE", `${hostsOnline} / ${hostList.length}`, "cau", "compute"]].map(([l, v, c, act]) => (
          <div key={l} className="gs-card" style={{ padding: "15px 17px", cursor: act ? "pointer" : "default" }}
            onClick={() => act === "compute" ? setMode("compute") : act === "faults" ? go({ view: "monitor", containerId: firstFault }) : null}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em",
              color: c === "flt" ? "var(--fault)" : c === "cau" ? "var(--caution)" : "var(--ink)" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>

      <div className="gs-toggle">
        <button className={mode === "projects" ? "on" : ""} onClick={() => setMode("projects")}><Satellite size={13} />Project</button>
        <button className={mode === "compute" ? "on" : ""} onClick={() => setMode("compute")}><Cpu size={13} />Compute</button>
      </div>

      {mode === "projects" ? (
        <div className="gs-grid">
          {monProjects.map((pk) => {
            const p = projects[pk], conts = byProject(pk), st = rollup(conts);
            const worstErr = conts.map((c) => parseFloat(c.err)).filter((n) => !isNaN(n)).sort((a, b) => b - a)[0];
            return (
              <div key={pk} className="gs-card gs-pcard" onClick={() => go({ view: "monitor", projectId: pk })}>
                <div className="gs-pcard-top">
                  <div><div className="gs-pcard-nm">{p.name}</div><div className="gs-pcard-area">{p.area}</div></div>
                  <StatusPill s={st} />
                </div>
                <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5 }}>{p.blurb}</div>
                <div className="gs-pcard-metrics">
                  <div className="gs-metric"><div className="v">{conts.length}</div><div className="l">CONTAINERS</div></div>
                  {p.users != null ? (
                    <div className="gs-metric"><div className="v">{p.users.toLocaleString()}</div><div className="l">USERS · 7D</div></div>
                  ) : (
                    <div className="gs-metric"><div className="v" style={{ color: "var(--ink-3)" }}>—</div><div className="l">NO ANALYTICS</div></div>
                  )}
                  <div className="gs-metric"><div className="v" style={{ color: st === "flt" ? "var(--fault)" : "var(--ink)" }}>
                    {worstErr != null ? `${worstErr}%` : "—"}</div><div className="l">MAX 5XX</div></div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="gs-grid">
          {hostList.map((h) => {
            const conts = byHost(h.id), I = HOST_ICONS[h.icon];
            const online = h.kind === "always_on" || !conts.every((c) => c.status === "los");
            return (
              <div key={h.id} className="gs-card gs-pcard" onClick={() => go({ view: "monitor", hostId: h.id })}>
                <div className="gs-pcard-top">
                  <div style={{ display: "flex", gap: 11, alignItems: "center" }}>
                    <I size={20} color="var(--ink-2)" />
                    <div><div className="gs-pcard-nm">{h.name}</div><div className="gs-pcard-area">{h.loc}</div></div>
                  </div>
                  {online ? <span className="pill go"><Signal size={11} />AOS</span> : <span className="pill neu"><SignalZero size={11} />LOS</span>}
                </div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 10.5, color: "var(--ink-3)", letterSpacing: "0.06em" }}>{h.tag}</div>
                <div className="gs-pcard-metrics">
                  <div className="gs-metric"><div className="v">{conts.length}</div><div className="l">CONTAINERS</div></div>
                  <div className="gs-metric"><div className="v" style={{ color: conts.some((c) => c.status === "flt") ? "var(--fault)" : "var(--ink)" }}>
                    {conts.filter((c) => c.status === "flt").length}</div><div className="l">FAULTS</div></div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

export function MonProjectDetail({ pk }) {
  const { go, projects, containers } = useNav();
  const p = projects[pk];
  const conts = containers.filter((c) => c.proj === pk);
  const [errData, setErrData] = useState([]);
  useEffect(() => { if (pk === "ghstats") api.errseries().then(setErrData); }, [pk]);
  return (
    <>
      <div className="gs-eyebrow">{p.area}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 6 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{p.name}</h1><StatusPill s={rollup(conts)} />
        <button className="gs-btn ghost" style={{ marginLeft: "auto" }} onClick={() => go({ view: "projects", projectId: pk })}><ListChecks size={14} />Tickets</button>
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

      {pk === "ghstats" && (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div className="gs-section-h" style={{ marginBottom: 14 }}><AlertTriangle size={12} color="var(--fault)" />gh-stats · 5XX RATE · breach at t-11m → <span className="gs-ref" onClick={() => go({ view: "queue", ticketId: "GHS-0311" })}>GHS-0311</span></div>
          <AreaSpark data={errData} color="#BF3A3A" height={120} yWidth={44} gid="ge" />
        </div>
      )}

      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
      <ContainerTable containers={conts} sub="host" />
    </>
  );
}

export function HostDetail({ hid }) {
  const { hosts, containers } = useNav();
  const h = hosts[hid];
  const conts = containers.filter((c) => c.host === hid);
  const I = HOST_ICONS[h.icon];
  const online = h.kind === "always_on" || !conts.every((c) => c.status === "los");
  return (
    <>
      <div className="gs-eyebrow">{h.tag} · {h.loc}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
        <I size={22} color="var(--ink-2)" />
        <h1 className="gs-h1" style={{ margin: 0 }}>{h.name}</h1>
        {online ? <span className="pill go"><Signal size={11} />AOS</span> : <span className="pill neu"><SignalZero size={11} />LOS</span>}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 12, marginBottom: 22 }}>
        {[["CONTAINERS", String(conts.length)], ["FAULTS", String(conts.filter((c) => c.status === "flt").length)],
          ["CLASS", h.kind === "always_on" ? "ALWAYS-ON" : "INTERMITTENT"]].map(([l, v]) => (
          <div key={l} className="gs-card" style={{ padding: "14px 15px" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>
      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
      <ContainerTable containers={conts} sub="proj" />
    </>
  );
}
