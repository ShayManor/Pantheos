import { useEffect, useState, useCallback } from "react";
import { Download } from "lucide-react";
import { useNav } from "../nav.jsx";
import { StatusPill } from "../components/pills.jsx";
import Dropdown from "../components/dropdown.jsx";
import { api } from "../api.js";

const LV = { info: "INFO", warn: "WARN", err: "ERROR" };

export default function ContainerLogs({ id }) {
  const { go, toast, projects, hosts, containers } = useNav();
  const c = containers.find((x) => x.id === id);
  const p = projects[c.proj], h = hosts[c.host];
  const [view, setView] = useState("smart");
  const [lvl, setLvl] = useState("all");
  const [items, setItems] = useState([]);
  const [next, setNext] = useState(null);
  const [monitored, setMonitored] = useState(true);

  useEffect(() => {
    let live = true;
    const mode = view === "raw" ? "raw" : undefined;
    api.containerLogs(id, { mode }).then((d) => {
      if (!live) return;
      setItems(d.items); setNext(d.next); setMonitored(d.monitored !== false);
    });
    return () => { live = false; };
  }, [id, view]);

  const loadOlder = useCallback(() => {
    if (next == null) return;
    const mode = view === "raw" ? "raw" : undefined;
    api.containerLogs(id, { mode, before: next }).then((d) => {
      setItems((prev) => [...prev, ...d.items]); setNext(d.next);
    });
  }, [id, view, next]);

  const expandGap = (gap) => {
    api.containerLogRange(id, gap.from, gap.to).then((d) => {
      setItems((prev) => {
        const idx = prev.indexOf(gap);
        if (idx === -1) return prev;
        const copy = prev.slice();
        copy.splice(idx, 1, ...d.lines.map((l) => ({ type: "line", ...l })));
        return copy;
      });
    });
  };

  const shown = items.filter((it) =>
    it.type === "gap" ? lvl === "all" : lvl === "all" || it.lvl === lvl);

  const download = () => {
    const text = items.filter((it) => it.type === "line")
      .map((l) => `${l.t}  ${LV[l.lvl].padEnd(5)}  ${l.msg}`).join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url; a.download = `${c.id}.log`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast("Log bundle downloaded");
  };

  return (
    <>
      <div className="gs-eyebrow">
        <span className="gs-linkable" onClick={() => go({ view: "monitor", containerId: c.id })} style={{ fontFamily: "var(--mono)" }}>{c.id}</span><span>·</span>
        <span>{p.name}</span><span>·</span><span>{h.name}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>Logs</h1>
        <StatusPill s={c.status} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {monitored && c.up !== "LOS" && <span className="gs-follow"><span className="dot go" style={{ boxShadow: "none", width: 6, height: 6 }} />following</span>}
          <Dropdown label="View" value={view} onChange={setView}
            options={[{ value: "smart", label: "Smart" }, { value: "raw", label: "Raw" }]} />
          <Dropdown label="Level" value={lvl} onChange={setLvl}
            options={[{ value: "all", label: "All" }, { value: "info", label: "Info" }, { value: "warn", label: "Warn" }, { value: "err", label: "Errors" }]} />
          <button className="gs-btn ghost" onClick={download}><Download size={15} />Download</button>
        </div>
      </div>
      <div className="gs-logbox">
        {!monitored ? (
          <div className="gs-logline"><span className="mg">Not monitored · no logs collected for this container.</span></div>
        ) : (
          <>
            {shown.map((it, i) => it.type === "gap" ? (
              <button key={`g${it.from}-${it.to}`} className="gs-loggap" onClick={() => expandGap(it)}>
                ▾ {it.count} info lines
              </button>
            ) : (
              <div key={`${it.id}-${i}`} className={`gs-logline${it.ctx ? " ctx" : ""}`}>
                <span className="ts">{it.t}</span>
                <span className={`lv ${it.lvl}`}>{LV[it.lvl]}</span>
                <span className="mg">{it.msg}</span>
              </div>
            ))}
            {next != null && (
              <button className="gs-loggap older" onClick={loadOlder}>Load older ↓</button>
            )}
          </>
        )}
      </div>
    </>
  );
}
