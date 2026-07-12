import { useState } from "react";
import { ListChecks, Plus, Sparkles, X } from "lucide-react";
import { useNav } from "../nav.jsx";
import { api } from "../api.js";

const DEADLINES = [
  ["", "No deadline"],
  ["6", "Today"],
  ["72", "In 3 days"],
  ["168", "This week"],
  ["336", "In 2 weeks"],
];

const fieldLabel = { fontFamily: "var(--mono)", fontSize: 9.5, letterSpacing: "0.1em",
  color: "var(--ink-3)", textTransform: "uppercase", marginBottom: 6, display: "block" };

export default function NewTicketModal({ onClose }) {
  const { projects, areas, createTicket, go, toast } = useNav();
  const projectEntries = Object.entries(projects);
  const [title, setTitle] = useState("");
  const [attach, setAttach] = useState(projectEntries.length ? `project:${projectEntries[0][0]}` : "");
  const [pri, setPri] = useState(2);
  const [effort, setEffort] = useState("");
  const [deadline, setDeadline] = useState("");
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);
  const [drafting, setDrafting] = useState(false);

  // Ask Delphi to enrich whatever's filled in into a full ticket, then fill the
  // form live (field by field) so the user can edit the draft before creating.
  const callDelphi = () => {
    if (busy || drafting) return;
    const [kind, id] = attach.split(":");
    const ctx = { title: title.trim(), summary: summary.trim(), pri };
    if (kind === "project") ctx.project_key = id;
    else if (kind === "area") ctx.area_id = id;
    if (effort) ctx.effort_hours = Number(effort);
    if (deadline) ctx.deadline_hours = Number(deadline);
    setDrafting(true);
    api.draftTicket(ctx)
      .then((d) => {
        const fills = [
          () => setTitle(d.title ?? ""),
          () => {
            if (d.project_key) setAttach(`project:${d.project_key}`);
            else if (d.area_id) setAttach(`area:${d.area_id}`);
          },
          () => { if (d.pri != null) setPri(d.pri); },
          () => setDeadline(d.deadline_hours != null ? String(d.deadline_hours) : ""),
          () => setEffort(d.effort_hours != null ? String(d.effort_hours) : ""),
          () => setSummary(d.summary ?? ""),
        ];
        fills.forEach((fn, i) => setTimeout(fn, i * 120));
        setTimeout(() => setDrafting(false), fills.length * 120);
      })
      .catch(() => { toast("Delphi couldn't draft that"); setDrafting(false); });
  };

  const submit = () => {
    const t = title.trim();
    if (!t || !attach || busy) return;
    const [kind, id] = attach.split(":");
    const payload = { title: t, pri };
    if (kind === "project") payload.project_key = id;
    else payload.area_id = id;
    if (summary.trim()) payload.summary = summary.trim();
    if (effort) payload.effort_hours = Number(effort);
    if (deadline) payload.deadline_hours = Number(deadline);
    setBusy(true);
    createTicket(payload)
      .then((ticket) => { toast(`Created ${ticket.id}`); go({ view: "queue", ticketId: ticket.id }); onClose(); })
      .catch(() => setBusy(false));
  };

  return (
    <div className="gs-overlay" onClick={onClose}>
      <div className="gs-pal" style={{ maxHeight: "none" }} onClick={(e) => e.stopPropagation()}>
        <div className="gs-pal-in" style={{ justifyContent: "space-between" }}>
          <span style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "var(--disp)", fontWeight: 600, fontSize: 15 }}>
            <ListChecks size={16} color="var(--go)" />New ticket
          </span>
          <button className="gs-hbtn icon" onClick={onClose}><X size={16} /></button>
        </div>

        <div style={{ padding: "16px 18px", display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={fieldLabel}>Title</label>
            <input className="gs-input" style={{ width: "100%", fontFamily: "var(--sans)", fontSize: 14 }}
              autoFocus value={title} onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()} placeholder="What needs doing?" />
          </div>

          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={fieldLabel}>Area / Project</label>
              <select className="gs-sort" style={{ width: "100%" }} value={attach} onChange={(e) => setAttach(e.target.value)}>
                <optgroup label="Projects">
                  {projectEntries.map(([k, p]) => <option key={k} value={`project:${k}`}>{p.name}</option>)}
                </optgroup>
                <optgroup label="Areas">
                  {areas.map((a) => <option key={a.id} value={`area:${a.id}`}>{a.name}</option>)}
                </optgroup>
              </select>
            </div>
            <div style={{ width: 92 }}>
              <label style={fieldLabel}>Priority</label>
              <select className="gs-sort" style={{ width: "100%" }} value={pri} onChange={(e) => setPri(Number(e.target.value))}>
                {[0, 1, 2, 3].map((p) => <option key={p} value={p}>P{p}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={fieldLabel}>Deadline</label>
              <select className="gs-sort" style={{ width: "100%" }} value={deadline} onChange={(e) => setDeadline(e.target.value)}>
                {DEADLINES.map(([v, l]) => <option key={l} value={v}>{l}</option>)}
              </select>
            </div>
            <div style={{ width: 120 }}>
              <label style={fieldLabel}>Effort (hrs)</label>
              <input className="gs-input" style={{ width: "100%" }} type="number" min="0"
                value={effort} onChange={(e) => setEffort(e.target.value)} placeholder="—" />
            </div>
          </div>

          <div>
            <label style={fieldLabel}>Summary <span style={{ textTransform: "none", letterSpacing: 0 }}>(optional)</span></label>
            <input className="gs-input" style={{ width: "100%", fontFamily: "var(--sans)", fontSize: 13 }}
              value={summary} onChange={(e) => setSummary(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()} placeholder="One line — what this ticket is" />
          </div>

          <div style={{ display: "flex", gap: 8, justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
            <button className="gs-btn ghost" onClick={callDelphi} disabled={busy || drafting}>
              <Sparkles size={15} color="var(--go)" />{drafting ? "Delphi drafting…" : "Call Delphi"}
            </button>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="gs-btn ghost" onClick={onClose}>Cancel</button>
              <button className="gs-btn primary" onClick={submit} disabled={!title.trim() || busy}>
                <Plus size={15} />Create ticket
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
