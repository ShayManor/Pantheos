import { ChevronRight } from "lucide-react";
import { useNav } from "../nav.jsx";

// Container list, reused everywhere. sub = "host" | "proj".
export default function ContainerTable({ containers, sub }) {
  const { go, hosts, projects } = useNav();
  return (
    <div className="gs-card" style={{ overflow: "hidden" }}>
      <div className="gs-svc-head">
        <span>Container</span><span>CPU</span><span>Mem</span><span>5xx</span><span>Signal</span><span />
      </div>
      {containers.map((c) => (
        <div key={c.id} className="gs-svc" onClick={() => go({ view: "monitor", containerId: c.id })}>
          <div className="gs-svc-nm">
            <span className={`dot ${c.status}`} style={{ boxShadow: "none" }} />
            <div style={{ minWidth: 0 }}>
              <div className="id">{c.id}</div>
              <div className="sub">{sub === "host" ? hosts[c.host].name : projects[c.proj].name} · {c.role}</div>
            </div>
          </div>
          <div className="gs-svc-val">{c.cpu}</div>
          <div className="gs-svc-val">{c.mem}</div>
          <div className="gs-svc-val" style={{ color: c.status === "flt" ? "var(--fault)" : "var(--ink-2)" }}>{c.err}</div>
          <div className="gs-svc-val" style={{ color: c.up === "LOS" ? "var(--ink-3)" : "var(--go)" }}>{c.up}</div>
          <div className="gs-svc-chev"><ChevronRight size={15} /></div>
        </div>
      ))}
    </div>
  );
}
