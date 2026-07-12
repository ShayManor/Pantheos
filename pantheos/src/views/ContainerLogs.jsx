import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { useNav } from "../nav.jsx";
import { StatusPill } from "../components/pills.jsx";
import { api } from "../api.js";

const LV = { info: "INFO", warn: "WARN", err: "ERROR" };

export default function ContainerLogs({ id }) {
  const { go, toast, projects, hosts, containers } = useNav();
  const c = containers.find((x) => x.id === id);
  const p = projects[c.proj], h = hosts[c.host];
  const [lvl, setLvl] = useState("all");
  const [all, setAll] = useState([]);
  useEffect(() => { api.containerLogs(id).then((d) => setAll(d.lines)); }, [id]);
  const lines = all.filter((l) => lvl === "all" || l.lvl === lvl);

  const download = () => {
    const text = all.map((l) => `${l.t}  ${LV[l.lvl].padEnd(5)}  ${l.msg}`).join("\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${c.id}.log`;
    document.body.appendChild(a);
    a.click();
    a.remove();
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
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {c.up !== "LOS" && <span className="gs-follow"><span className="dot go" style={{ boxShadow: "none", width: 6, height: 6 }} />following</span>}
          <button className="gs-btn ghost" onClick={download}><Download size={15} />Download</button>
        </div>
      </div>
      <div className="gs-filters">
        {["all", "info", "warn", "err"].map((k) => (
          <button key={k} className={`gs-filter ${lvl === k ? "on" : ""}`} onClick={() => setLvl(k)}>
            {k === "all" ? "All" : LV[k]}
          </button>
        ))}
      </div>
      <div className="gs-logbox">
        {lines.map((l, i) => (
          <div key={i} className="gs-logline">
            <span className="ts">{l.t}</span>
            <span className={`lv ${l.lvl}`}>{LV[l.lvl]}</span>
            <span className="mg">{l.msg}</span>
          </div>
        ))}
      </div>
    </>
  );
}
