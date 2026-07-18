import { useState } from "react";
import {
  AlertTriangle, CheckCircle2, ChevronRight, Clock, GitBranch, Layers,
  Link2, PauseCircle, Rocket, Terminal, Trash2, Zap,
} from "lucide-react";
import { useNav } from "../nav.jsx";
import { LifePill } from "../components/pills.jsx";
import ConfirmModal from "../components/ConfirmModal.jsx";
import { autoLabel, linkHref, LINK_ICON, LINK_KIND, openExternal } from "../lib/helpers.js";

export default function TicketDetail({ id }) {
  const { go, tickets, launchTicket, setLifecycle, deleteTicket, setFilter, toast, projects } = useNav();
  const [confirmDel, setConfirmDel] = useState(false);
  const t = tickets.find((x) => x.id === id);
  if (!t) return <div className="gs-empty">Ticket not found.</div>;
  const p = t.proj ? projects[t.proj] : null;

  return (
    <div className="gs-detail-grid">
      <div>
        <div className="gs-eyebrow">
          <span className={`pri p${t.pri}`}>P{t.pri}</span>
          <span style={{ fontFamily: "var(--mono)" }}>{t.id}</span>
          <span>·</span>
          <span className="gs-linkable" onClick={() => { setFilter({ kind: "area", val: t.area }); go({ view: "queue" }); }}>{t.area}</span>
        </div>
        <h1 className="gs-h1">{t.title}</h1>
        <p className="gs-sub">{t.summary}</p>

        {t.result && (
          <div className="gs-section">
            <div className="gs-section-h"><CheckCircle2 size={12} />RESULT</div>
            <div className="gs-result"><Zap size={16} color="var(--go)" style={{ flexShrink: 0, marginTop: 1 }} />{t.result}</div>
          </div>
        )}
        {t.report && (
          <div className="gs-section">
            <div className="gs-section-h"><Terminal size={12} />REPORT · latest run</div>
            <div className="gs-body-text muted">{t.report}</div>
          </div>
        )}
        <div className="gs-section">
          <div className="gs-section-h"><Layers size={12} />PROBLEM STATEMENT · agent-written</div>
          <div className="gs-body-text">{t.body}</div>
        </div>
        {t.deps.length > 0 && (
          <div className="gs-section">
            <div className="gs-section-h"><GitBranch size={12} />DEPENDENCIES · non-blocking</div>
            {t.deps.map((d) => {
              const exists = tickets.some((x) => x.id === d.id);
              return (
                <div key={d.id} className={`gs-dep ${exists ? "gs-linkable" : ""}`} onClick={() => exists && go({ view: "queue", ticketId: d.id })}>
                  <span className={`dot ${d.done ? "go" : "cau"}`} style={{ boxShadow: "none" }} />
                  <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--ink-3)" }}>{d.id}</span>
                  {d.title}
                  <span style={{ marginLeft: "auto", fontFamily: "var(--mono)", fontSize: 10, color: d.done ? "var(--go)" : "var(--caution)" }}>
                    {d.done ? "DONE" : "OPEN"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div>
        <div className="gs-card gs-meta-card" style={{ marginBottom: 14 }}>
          <button className="gs-btn primary" style={{ width: "100%", justifyContent: "center", marginBottom: 10 }}
            onClick={() => launchTicket(t.id)} disabled={t.agent === "executing"}>
            <Rocket size={15} />{t.agent === "executing" ? "Delphi is running…" : "Launch Delphi"}
          </button>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            {t.life === "backburner" ? (
              <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "queued"); toast(`${t.id} → queued`); }}><Clock size={14} />Activate</button>
            ) : (
              <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "backburner"); toast(`${t.id} → backburner`); }}><PauseCircle size={14} />Backburner</button>
            )}
            {t.life !== "archived" && (
              <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "archived"); toast(`${t.id} archived`); }}><CheckCircle2 size={14} />Done</button>
            )}
          </div>
          <div className="gs-meta-row"><span className="gs-meta-k">status</span><LifePill life={t.life} agent={t.agent} /></div>
          <div className="gs-meta-row"><span className="gs-meta-k">deadline</span>
            <span className="gs-meta-v" style={{ color: t.hot ? "var(--fault)" : "var(--ink)" }}>{t.due || "none"}</span></div>
          <div className="gs-meta-row"><span className="gs-meta-k">est. effort</span><span className="gs-meta-v">{t.effort}</span></div>
          <div className="gs-meta-row"><span className="gs-meta-k">score</span><span className="gs-meta-v">{t.score}</span></div>
          <div className="gs-meta-row"><span className="gs-meta-k">source</span>
            <span className="gs-meta-v gs-linkable" onClick={() => { setFilter({ kind: "source", val: t.source }); go({ view: "queue" }); }}>{t.source}</span></div>
          {p && <div className="gs-meta-row"><span className="gs-meta-k">project</span>
            <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "projects", projectId: t.proj })}>{p.name} ›</span></div>}
          {p && <div className="gs-meta-row"><span className="gs-meta-k">autonomy</span>
            <span className="pill neu" style={{ textTransform: "none" }}>{autoLabel(p.autonomy)}</span></div>}
          <button className="gs-btn danger" style={{ width: "100%", justifyContent: "center", marginTop: 12 }}
            onClick={() => setConfirmDel(true)}><Trash2 size={14} />Delete ticket</button>
        </div>

        {p && p.autonomy === "propose" && (
          <div className="gs-card" style={{ padding: "12px 14px", marginBottom: 14, background: "var(--caution-soft)", borderColor: "var(--caution-line)" }}>
            <div style={{ display: "flex", gap: 9, fontSize: 12, color: "var(--caution)", lineHeight: 1.5 }}>
              <AlertTriangle size={15} style={{ flexShrink: 0 }} />
              <span><b>PR-only.</b> Opens a pull request and stops for your review.</span>
            </div>
          </div>
        )}

        {t.links.length > 0 && (
          <div className="gs-card gs-meta-card">
            <div className="gs-section-h" style={{ marginBottom: 11 }}><Link2 size={12} />LINKS</div>
            {t.links.map((l, i) => {
              const I = LINK_ICON[l.kind] || Link2;
              const href = linkHref(l, t, projects);
              const inner = (
                <>
                  <span className={`pill ${LINK_KIND[l.kind] || "neu"}`} style={{ padding: 4, borderRadius: 6 }}><I size={12} /></span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.label}</span>
                  <ChevronRight size={14} color="var(--ink-3)" style={{ marginLeft: "auto" }} />
                </>
              );
              return href ? (
                <a key={i} className="gs-link" href={href} target="_blank" rel="noopener noreferrer"
                   style={{ textDecoration: "none", color: "inherit" }}>{inner}</a>
              ) : (
                <div key={i} className="gs-link" onClick={() => toast(`Opening ${l.label}`)}>{inner}</div>
              );
            })}
          </div>
        )}
      </div>

      {confirmDel && (
        <ConfirmModal
          title={`Delete ${t.id}?`}
          body="This permanently deletes the ticket and can't be undone."
          confirmLabel="Delete ticket"
          onConfirm={() => { setConfirmDel(false); deleteTicket(t.id); }}
          onClose={() => setConfirmDel(false)} />
      )}
    </div>
  );
}
