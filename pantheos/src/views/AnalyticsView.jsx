import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, BarChart3, CalendarDays, ChevronDown, ChevronRight, Clock, Search, Users,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";

const GO = "#0F7A4B", INFO = "#2563A6", FAULT = "#BF3A3A", MUTED = "#8E99A4", GRID = "#E4E8ED";
const TICK = { fontFamily: "var(--mono)", fontSize: 10, fill: MUTED };
const TIP = { fontFamily: "var(--mono)", fontSize: 11, borderRadius: 8, border: `1px solid ${GRID}` };
const RANGES = [["7d", "7D"], ["30d", "30D"], ["90d", "90D"], ["all", "ALL"]];
const SITES = { ghstats: "gh-stats", gpufindr: "GPUFindr" };
const STATUS = {
  ghstats: { live: ["go", "Live"], stopped: ["flt", "Stopped"], tried: ["neu", "Tried once"] },
  gpufindr: { live: ["go", "Active"], stopped: ["neu", "Lapsed"] },
};
const FILTERS = {
  ghstats: [["all", "All"], ["live", "Live"], ["stopped", "Stopped"], ["tried", "Tried once"], ["oauth", "OAuth"]],
  gpufindr: [["all", "All"], ["live", "Active"], ["stopped", "Lapsed"], ["searched", "Searched"]],
};

export const fmtDur = (s) => {
  if (!s) return "0s";
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, "0")}s`;
  return `${Math.floor(s / 3600)}h ${String(Math.floor(s / 60) % 60).padStart(2, "0")}m`;
};
const fmtDay = (d) => d && new Date(`${d}T12:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" });
const tileVal = (t) => (t.unit === "s" ? fmtDur(t.v) : t.v.toLocaleString());

function Section({ icon: I, title, legend, note, children }) {
  return (
    <div className="gs-card gs-an-card">
      <div className="gs-an-card-h">
        <div className="gs-section-h" style={{ margin: 0 }}><I size={12} />{title}</div>
        {note && <span className="gs-an-dim">{note}</span>}
        {legend && (
          <div className="gs-an-legend">
            {legend.map(([c, l, dash]) => (
              <span key={l}><i style={{ background: dash ? "none" : c, borderTop: dash ? `2px dashed ${c}` : "none" }} />{l}</span>
            ))}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

function Lines({ data, x, series, height = 200, xFmt }) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 6, right: 6, left: -18, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey={x} tick={TICK} axisLine={false} tickLine={false} tickFormatter={xFmt} minTickGap={24} />
          <YAxis tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip contentStyle={TIP} labelFormatter={xFmt} />
          {series.map(([k, c, name, dash]) => (
            <Line key={k} type="monotone" dataKey={k} name={name} stroke={c} strokeWidth={dash ? 1.5 : 2}
              strokeDasharray={dash ? "4 4" : undefined} dot={false} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function Bars({ data, x = "k", series = [["v", GO, "count"]], height = 180, layout, xFmt, stack }) {
  const vertical = layout === "vertical";
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout={layout} stackOffset={stack ? "sign" : undefined}
          margin={{ top: 6, right: 6, left: vertical ? 4 : -18, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={vertical} horizontal={!vertical} />
          {vertical ? (
            <>
              <XAxis type="number" tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey={x} tick={TICK} axisLine={false} tickLine={false} width={110} />
            </>
          ) : (
            <>
              <XAxis dataKey={x} tick={TICK} axisLine={false} tickLine={false} tickFormatter={xFmt} />
              <YAxis tick={TICK} axisLine={false} tickLine={false} allowDecimals={false}
                tickFormatter={stack ? (v) => Math.abs(v) : undefined} />
            </>
          )}
          <Tooltip contentStyle={TIP} labelFormatter={xFmt} cursor={{ fill: "#F4F6F8" }}
            formatter={stack ? (v, n) => [Math.abs(v), n] : undefined} />
          {series.map(([k, c, name]) => (
            <Bar key={k} dataKey={k} name={name} fill={c} stackId={stack ? "s" : undefined}
              radius={vertical ? [0, 3, 3, 0] : [3, 3, 0, 0]} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function Spark({ data }) {
  const pts = data.map((v, i) => ({ i, v }));
  return (
    <div style={{ height: 34, marginTop: 8 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={pts} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
          <YAxis hide domain={["dataMin", "dataMax"]} />
          <Line type="monotone" dataKey="v" stroke={GO} strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function UserDetail({ site, id }) {
  const [d, setD] = useState(null);
  useEffect(() => { api.analyticsUser(site, id).then(setD).catch(() => setD({ error: true })); }, [site, id]);
  if (!d) return <div className="gs-an-detail gs-an-dim">Loading timeline…</div>;
  if (d.error) return <div className="gs-an-detail gs-an-dim">No activity recorded.</div>;
  const unit = site === "ghstats" ? "embed loads" : "requests";
  // Days from the gh-stats rollup were active but their load counts weren't kept.
  const timeline = d.timeline.map((t) => ({ ...t, seen: t.on && !t.v ? 1 : 0 }));
  const hasSeen = timeline.some((t) => t.seen);
  return (
    <div className="gs-an-detail">
      <div className="gs-an-detail-grid">
        <div>
          <div className="gs-an-k">{unit.toUpperCase()} PER DAY · {fmtDay(d.timeline[0].d)} → {fmtDay(d.timeline[d.timeline.length - 1].d)}</div>
          <Bars data={timeline} x="d" xFmt={fmtDay} height={120} stack
            series={[["v", GO, unit], ...(hasSeen ? [["seen", "#BFE0CE", "active, count not kept"]] : [])]} />
          {hasSeen && <div className="gs-an-dim" style={{ marginTop: 6 }}>Light bars: active days from before per-day counts were saved.</div>}
        </div>
        <div>
          <div className="gs-an-k">{site === "ghstats" ? "WIDGETS" : "SEARCHES"}</div>
          {d.top.length === 0 ? <div className="gs-an-dim">None recorded.</div> : d.top.map((t) => (
            <div key={t.k} className="gs-an-top"><span>{t.k}</span><b>{t.v.toLocaleString()}</b></div>
          ))}
          {d.enrolled && <div className="gs-an-dim" style={{ marginTop: 10 }}>Enrolled {fmtDay(d.enrolled)}{d.oauth ? " · GitHub OAuth" : ""}</div>}
        </div>
      </div>
    </div>
  );
}

function UsersTable({ site, users }) {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(null);
  const [limit, setLimit] = useState(50);
  useEffect(() => { setFilter("all"); setOpen(null); setLimit(50); }, [site]);
  const counts = useMemo(() => {
    const c = { all: users.length, oauth: users.filter((u) => u.oauth).length, searched: users.filter((u) => u.searches).length };
    users.forEach((u) => { c[u.status] = (c[u.status] || 0) + 1; });
    return c;
  }, [users]);
  const rows = users.filter((u) =>
    (filter === "all" || u.status === filter || (filter === "oauth" && u.oauth) || (filter === "searched" && u.searches))
    && u.id.toLowerCase().includes(q.toLowerCase()));
  const gh = site === "ghstats";
  const cols = gh ? ["User", "Status", "Embedded", "Loads", "Site time", "Last seen"]
    : ["Visitor", "Status", "Visits", "Searches", "Most searched", "Site time", "Last seen"];
  return (
    <>
      <div className="gs-an-tools">
        <div className="gs-filters" style={{ margin: 0 }}>
          {FILTERS[site].map(([k, l]) => (
            <button key={k} className={`gs-filter ${filter === k ? "on" : ""}`} onClick={() => { setFilter(k); setLimit(50); }}>
              {l} <span className="gs-an-num">{counts[k] || 0}</span>
            </button>
          ))}
        </div>
        <div className="gs-an-search"><Search size={13} /><input className="gs-input" placeholder={gh ? "Find a user" : "Find a visitor"}
          value={q} onChange={(e) => setQ(e.target.value)} /></div>
      </div>
      <div className="gs-card" style={{ overflow: "hidden" }}>
        <div className={`gs-an-row head ${site}`}>{cols.map((c) => <span key={c}>{c}</span>)}<span /></div>
        {rows.length === 0 && <div className="gs-empty" style={{ padding: 22 }}>No {gh ? "users" : "visitors"} match.</div>}
        {rows.slice(0, limit).map((u) => {
          const [tone, label] = STATUS[site][u.status];
          const isOpen = open === u.id;
          return (
            <React.Fragment key={u.id}>
              <div className={`gs-an-row ${site} ${isOpen ? "open" : ""}`} onClick={() => setOpen(isOpen ? null : u.id)}>
                <span className="nm">{u.id}{u.oauth && <span className="pill info">OAuth</span>}</span>
                <span><span className={`pill ${tone}`}>{label}</span></span>
                {gh ? (
                  <>
                    <span>{u.embedded_days}d</span>
                    <span>{u.loads.toLocaleString()}</span>
                  </>
                ) : (
                  <>
                    <span>{u.visits}</span>
                    <span>{u.searches}</span>
                    <span className="gs-an-trunc">{[u.gpu, u.provider].filter(Boolean).join(" · ") || "—"}</span>
                  </>
                )}
                <span>{u.site_s ? fmtDur(u.site_s) : "—"}</span>
                <span>{fmtDay(u.last)}</span>
                <span className="chev">{isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</span>
              </div>
              {isOpen && <UserDetail site={site} id={u.id} />}
            </React.Fragment>
          );
        })}
      </div>
      {rows.length > limit && (
        <button className="gs-btn ghost" style={{ marginTop: 12 }} onClick={() => setLimit(rows.length)}>
          Show all {rows.length.toLocaleString()}
        </button>
      )}
    </>
  );
}

export default function AnalyticsView() {
  const [site, setSite] = useState("ghstats");
  const [range, setRange] = useState("30d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    setLoading(true);
    api.analytics(site, range)
      .then((d) => { if (live) setData(d); })
      .catch(() => { if (live) setData({ error: true }); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [site, range]);

  const shown = data && data.site === site ? data : null;
  const gh = site === "ghstats";
  return (
    <>
      <div className="gs-eyebrow"><BarChart3 size={13} />STATION · ANALYTICS</div>
      <h1 className="gs-h1">{SITES[site]} analytics</h1>
      <div className="gs-an-bar">
        <div className="gs-toggle" style={{ margin: 0 }}>
          {Object.entries(SITES).map(([k, l]) => (
            <button key={k} className={site === k ? "on" : ""} onClick={() => setSite(k)}>{l}</button>
          ))}
        </div>
        <div className="gs-toggle" style={{ margin: 0 }}>
          {RANGES.map(([k, l]) => (
            <button key={k} className={range === k ? "on" : ""} onClick={() => setRange(k)}>{l}</button>
          ))}
        </div>
        {shown && !shown.empty && !shown.error && <span className="gs-an-dim">{fmtDay(shown.start)} → {fmtDay(shown.now)}</span>}
        {loading && <span className="gs-an-spin" aria-label="Loading" />}
      </div>

      {!shown && <div className="gs-card gs-empty gs-an-loading">Loading {SITES[site]} analytics…</div>}
      {shown?.error && <div className="gs-card gs-empty" style={{ padding: 28 }}>Couldn't load analytics. Is the API reachable?</div>}
      {shown?.empty && <div className="gs-card gs-empty" style={{ padding: 28 }}>No {SITES[site]} traffic recorded yet.</div>}
      {shown && !shown.empty && !shown.error && (
        <div className={`gs-an ${loading ? "stale" : ""}`}>
          <div className="gs-an-tiles">
            {shown.tiles.map((t) => (
              <div key={t.k} className="gs-card gs-an-tile">
                <div className="v">{tileVal(t)}</div>
                <div className="l">{t.label}</div>
                <Spark data={t.spark} />
              </div>
            ))}
          </div>

          <Section icon={CalendarDays} title="HISTORY · PER DAY"
            legend={gh ? [[GO, "Active users"], [INFO, "Live embeds"]] : [[GO, "Visitors"], [INFO, "Searches"]]}>
            <Lines data={shown.history} x="d" xFmt={fmtDay} height={230}
              series={gh ? [["users", GO, "Active users"], ["live", INFO, "Live embeds"]]
                : [["visitors", GO, "Visitors"], ["searches", INFO, "Searches"]]} />
          </Section>

          <div className="gs-an-two">
            <Section icon={Clock} title={`${gh ? "EMBED LOADS" : "REQUESTS"} BY HOUR`}
              legend={[[GO, "Last 24 hours"], [MUTED, "Average day", true]]}>
              <Lines data={shown.hourly} x="h" series={[["last", GO, "Last 24 hours"], ["avg", MUTED, "Average day", true]]} />
            </Section>
            <Section icon={CalendarDays} title="AVERAGE WEEK">
              <Bars data={shown.weekly} x="d" height={200} series={[["v", GO, "per day"]]} />
            </Section>
          </div>

          {gh ? (
            <div className="gs-an-two">
              <Section icon={Activity} title="EMBEDS STARTED VS STOPPED · PER WEEK"
                legend={[[GO, "Started"], [FAULT, "Stopped"]]}>
                <Bars data={shown.embeds.map((e) => ({ ...e, stopped: -e.stopped }))} x="w" xFmt={fmtDay} stack
                  series={[["started", GO, "Started"], ["stopped", FAULT, "Stopped"]]} />
              </Section>
              <Section icon={Clock} title="HOW LONG EMBEDS LAST">
                <Bars data={shown.lifetime} series={[["v", GO, "embeds"]]} />
              </Section>
            </div>
          ) : (
            <div className="gs-an-two">
              <Section icon={Search} title="MOST SEARCHED GPUS">
                {shown.gpus.length ? <Bars data={shown.gpus} layout="vertical" series={[["v", GO, "searches"]]} />
                  : <div className="gs-empty gs-an-none">No searches in this range.</div>}
              </Section>
              <Section icon={Search} title="MOST SEARCHED PROVIDERS">
                {shown.providers.length ? <Bars data={shown.providers} layout="vertical" series={[["v", INFO, "searches"]]} />
                  : <div className="gs-empty gs-an-none">No provider filters in this range.</div>}
              </Section>
            </div>
          )}

          <Section icon={Clock} title={`TIME ON ${gh ? "GH-STATS.COM" : "GPUFINDR.COM"} · PER VISIT`}
            note={`${shown.sessions.bounce}% of visits bounced after one request and are left out`}>
            <Bars data={shown.sessions.hist} height={160} series={[["v", GO, "visits"]]} />
          </Section>

          <div className="gs-eyebrow" style={{ margin: "26px 0 12px" }}><Users size={12} />{gh ? "USERS" : "VISITORS"} · {shown.users.length.toLocaleString()}</div>
          <UsersTable site={site} users={shown.users} />
        </div>
      )}
    </>
  );
}
