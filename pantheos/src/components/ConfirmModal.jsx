import { AlertTriangle } from "lucide-react";

// A small in-app confirmation used for irreversible actions (Playwright
// auto-dismisses native window.confirm, which would break the E2E gate).
export default function ConfirmModal({ title, body, confirmLabel, onConfirm, onClose }) {
  return (
    <div className="gs-overlay" onClick={onClose}>
      <div className="gs-pal" style={{ maxWidth: 420, maxHeight: "none" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ padding: "18px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <span style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "var(--disp)", fontWeight: 600, fontSize: 15 }}>
            <AlertTriangle size={16} color="var(--fault)" />{title}
          </span>
          <p className="gs-sub" style={{ margin: 0 }}>{body}</p>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
            <button className="gs-btn ghost" onClick={onClose}>Cancel</button>
            <button className="gs-btn danger" onClick={onConfirm}>{confirmLabel}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
