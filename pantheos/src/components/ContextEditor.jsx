import { useEffect, useState } from "react";
import { FileText, X } from "lucide-react";
import { useNav } from "../nav.jsx";
import { api } from "../api.js";

// View / edit the CLAUDE.md-style context for an area or project.
export default function ContextEditor({ target, onClose }) {
  const { toast } = useNav();
  const { kind, id, name } = target;
  const [text, setText] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const get = kind === "area" ? api.getAreaContext(id) : api.getProjectContext(id);
    get.then((d) => { setText(d.context); setLoaded(true); });
  }, [kind, id]);

  const save = () => {
    if (busy) return;
    setBusy(true);
    const put = kind === "area" ? api.setAreaContext(id, text) : api.setProjectContext(id, text);
    put.then(() => { toast(`Saved context for ${name}`); onClose(); }).catch(() => setBusy(false));
  };

  return (
    <div className="gs-overlay" onClick={onClose}>
      <div className="gs-pal" style={{ width: "min(720px,92%)", maxHeight: "82%" }} onClick={(e) => e.stopPropagation()}>
        <div className="gs-pal-in" style={{ justifyContent: "space-between" }}>
          <span style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "var(--disp)", fontWeight: 600, fontSize: 15 }}>
            <FileText size={16} color="var(--go)" />{name} · context
          </span>
          <button className="gs-hbtn icon" onClick={onClose}><X size={16} /></button>
        </div>
        <div style={{ padding: "16px 18px" }}>
          <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, letterSpacing: "0.1em", color: "var(--ink-3)", textTransform: "uppercase", marginBottom: 8 }}>
            {kind} CLAUDE.md — injected as agent context
          </div>
          <textarea
            value={loaded ? text : "Loading…"} readOnly={!loaded} spellCheck={false}
            onChange={(e) => setText(e.target.value)}
            style={{ width: "100%", minHeight: 320, resize: "vertical", fontFamily: "var(--mono)", fontSize: 12.5,
              lineHeight: 1.6, color: "var(--ink)", background: "var(--surface-2)", border: "1px solid var(--line-2)",
              borderRadius: 10, padding: "12px 14px", outline: "none" }} />
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 14 }}>
            <button className="gs-btn ghost" onClick={onClose}>Cancel</button>
            <button className="gs-btn primary" onClick={save} disabled={!loaded || busy}>Save context</button>
          </div>
        </div>
      </div>
    </div>
  );
}
