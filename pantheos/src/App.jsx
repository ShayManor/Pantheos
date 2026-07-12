import { useEffect, useState } from "react";
import React from "react";
import { Check, ChevronRight, Clock, Gauge, ListChecks, Radio, Satellite } from "lucide-react";
import { CSS } from "./styles.js";
import { Nav } from "./nav.jsx";
import { api } from "./api.js";
import QueueView from "./views/QueueView.jsx";
import TicketDetail from "./views/TicketDetail.jsx";
import ProjectsView, { ProjectDetail } from "./views/ProjectsView.jsx";
import MonitorView, { MonProjectDetail, HostDetail } from "./views/MonitorView.jsx";
import ContainerDetail from "./views/ContainerDetail.jsx";
import ContainerLogs from "./views/ContainerLogs.jsx";
import FlightView from "./views/FlightView.jsx";
import SearchPalette from "./components/SearchPalette.jsx";
import NewTicketModal from "./components/NewTicketModal.jsx";
import ContextEditor from "./components/ContextEditor.jsx";

export default function Pantheos() {
  const [ready, setReady] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [projects, setProjects] = useState({});
  const [hosts, setHosts] = useState({});
  const [containers, setContainers] = useState([]);
  const [areas, setAreas] = useState([]);

  const [stack, setStack] = useState([{ view: "queue" }]);
  const [monMode, setMonMode] = useState("projects");
  const [filter, setFilter] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [newTicketOpen, setNewTicketOpen] = useState(false);
  const [contextTarget, setContextTarget] = useState(null);
  const [met, setMet] = useState(15153);

  useEffect(() => {
    Promise.all([api.tickets(), api.projects(), api.hosts(), api.containers(), api.areas()]).then(
      ([t, p, h, c, a]) => { setTickets(t); setProjects(p); setHosts(h); setContainers(c); setAreas(a); setReady(true); }
    );
  }, []);

  const cur = stack[stack.length - 1];
  useEffect(() => { const t = setInterval(() => setMet((m) => m + 1), 1000); return () => clearInterval(t); }, []);
  const clock = `${String(Math.floor(met / 3600)).padStart(2, "0")}:${String(Math.floor(met / 60) % 60).padStart(2, "0")}:${String(met % 60).padStart(2, "0")}`;
  const cCount = {
    flt: containers.filter((c) => c.status === "flt").length,
    cau: containers.filter((c) => c.status === "cau").length,
    go: containers.filter((c) => c.status === "go").length,
  };

  let toastSeq = 0;
  const toast = (text, action) => {
    const id = `${met}-${toastSeq++}-${text}`;
    setToasts((t) => [...t, { id, text, action }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200);
  };
  const go = (node) => setStack((s) => [...s, node]);
  const back = () => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s));
  const root = (view) => { setStack([{ view }]); setFilter(null); };

  const launchTicket = (id) => {
    api.launch(id).then(({ ticket, toast: msg }) => {
      setTickets((ts) => ts.map((t) => (t.id === id ? ticket : t)));
      toast(msg);
    });
  };
  const setLifecycle = (id, life) => {
    api.setLife(id, life).then((updated) => setTickets((ts) => ts.map((t) => (t.id === id ? updated : t))));
  };
  const createTicket = (payload) =>
    api.createTicket(payload).then((ticket) => { setTickets((ts) => [...ts, ticket]); return ticket; });
  const openNewTicket = () => setNewTicketOpen(true);
  const openContext = (kind, id, name) => setContextTarget({ kind, id, name });

  const nav = [
    { k: "queue", label: "Queue", icon: ListChecks, cnt: tickets.filter((t) => t.life !== "archived").length },
    { k: "projects", label: "Projects", icon: Satellite, cnt: Object.keys(projects).length },
    { k: "monitor", label: "Monitor", icon: Gauge, cnt: null },
  ];

  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearchOpen(true); }
      else if (e.key === "Escape" && !searchOpen) back();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [searchOpen]);

  const apiCtx = { go, back, root, toast, tickets, launchTicket, setLifecycle, createTicket, openNewTicket,
    openContext, filter, setFilter, projects, hosts, containers, areas };

  const section = cur.ticketId ? "queue" : cur.view;
  const secName = { queue: "Queue", projects: "Projects", monitor: "Monitor", flight: "Delphi" }[section] || "Queue";
  const crumbs = [{ label: secName, node: { view: section }, mode: section === "monitor" }];
  if (cur.ticketId) crumbs.push({ label: tickets.find((t) => t.id === cur.ticketId)?.id || cur.ticketId });
  else if (cur.projectId) crumbs.push({ label: projects[cur.projectId]?.name });
  else if (cur.hostId) crumbs.push({ label: hosts[cur.hostId]?.name });
  else if (cur.containerId) { crumbs.push({ label: containers.find((c) => c.id === cur.containerId)?.id }); if (cur.logs) crumbs.push({ label: "Logs" }); }

  let body = null;
  if (!ready) body = <div className="gs-empty">Loading Pantheos…</div>;
  else if (cur.containerId && cur.logs) body = <ContainerLogs id={cur.containerId} />;
  else if (cur.containerId) body = <ContainerDetail id={cur.containerId} />;
  else if (cur.ticketId) body = <TicketDetail id={cur.ticketId} />;
  else if (cur.view === "projects" && cur.projectId) body = <ProjectDetail pk={cur.projectId} />;
  else if (cur.view === "monitor" && cur.projectId) body = <MonProjectDetail pk={cur.projectId} />;
  else if (cur.view === "monitor" && cur.hostId) body = <HostDetail hid={cur.hostId} />;
  else if (cur.view === "queue") body = <QueueView />;
  else if (cur.view === "projects") body = <ProjectsView />;
  else if (cur.view === "monitor") body = <MonitorView mode={monMode} setMode={setMonMode} />;
  else if (cur.view === "flight") body = <FlightView />;

  return (
    <div className="gs">
      <style>{CSS}</style>
      <Nav.Provider value={apiCtx}>
        <div className="gs-shell">
          <aside className="gs-rail">
            <div className="gs-brand" style={{ cursor: "pointer" }} onClick={() => root("queue")}>
              <div className="gs-brand-mark"><Satellite size={17} /></div>
              <div><div className="gs-brand-name">Pantheos</div><div className="gs-brand-sub">LIFE OS</div></div>
            </div>
            <nav className="gs-nav">
              <div className="gs-nav-label">STATIONS</div>
              {nav.map((n) => (
                <button key={n.k} className={`gs-nav-item ${section === n.k ? "active" : ""}`} onClick={() => root(n.k)}>
                  <n.icon size={16} />{n.label}{n.cnt != null && <span className="cnt">{n.cnt}</span>}
                </button>
              ))}
              <div className="gs-nav-label" style={{ marginTop: 8 }}>AGENT</div>
              <button className={`gs-nav-item ${section === "flight" ? "active" : ""}`} onClick={() => root("flight")}><Radio size={16} />Delphi</button>
            </nav>
            <div className="gs-rail-foot">
              <div className="gs-flight-card" style={{ cursor: "pointer" }} onClick={() => root("flight")}>
                <div className="row"><span className="dot go" /><span className="nm">Delphi</span><Radio size={13} color="var(--ink-3)" style={{ marginLeft: "auto" }} /></div>
                <div className="st">● ONLINE · 40 RUNS LOGGED</div>
              </div>
            </div>
          </aside>

          <main className="gs-main">
            <div className="gs-strip">
              <div className="gs-crumb">
                {crumbs.map((c, i) => (
                  <React.Fragment key={i}>
                    {i > 0 && <ChevronRight size={14} className="sep" />}
                    {i < crumbs.length - 1
                      ? <button onClick={() => { if (c.mode !== undefined) root(section); else back(); }}>{c.label}</button>
                      : <span className="cur">{c.label}</span>}
                  </React.Fragment>
                ))}
              </div>
              <div className="gs-strip-spacer" />
              <button className="gs-kbtn" onClick={() => setSearchOpen(true)}>
                <Radio size={13} />Search <kbd>⌘K</kbd>
              </button>
              <span className="gs-stat-chip" style={{ background: "var(--fault-soft)", color: "var(--fault)", cursor: "pointer" }}
                onClick={() => go({ view: "monitor", containerId: "gh-stats-api" })}>
                <span className="dot flt" style={{ boxShadow: "none" }} />{cCount.flt} fault</span>
              <span className="gs-met"><Clock size={12} />MET <b>{clock}</b></span>
            </div>

            <div className="gs-body">{body}</div>
          </main>
        </div>

        {searchOpen && <SearchPalette onClose={() => setSearchOpen(false)} />}
        {newTicketOpen && <NewTicketModal onClose={() => setNewTicketOpen(false)} />}
        {contextTarget && <ContextEditor target={contextTarget} onClose={() => setContextTarget(null)} />}
        {toasts.length > 0 && (
          <div className="gs-toasts">
            {toasts.map((t) => (
              <div key={t.id} className="gs-toast">
                <Check size={15} className="go" />{t.text}
              </div>
            ))}
          </div>
        )}
      </Nav.Provider>
    </div>
  );
}
