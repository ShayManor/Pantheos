import { ChevronRight } from "lucide-react";
import { useNav } from "../nav.jsx";
import { LifePill } from "./pills.jsx";

// Ticket rows, reused in queue + project detail.
export default function TicketRow({ t }) {
  const { go } = useNav();
  return (
    <div className="gs-trow" onClick={() => go({ view: "queue", ticketId: t.id })}>
      <span className={`pri p${t.pri}`}>P{t.pri}</span>
      <div className="gs-trow-main">
        <div className="gs-trow-top">
          <span className="gs-trow-id">{t.id}</span>
          <span className="gs-trow-title">{t.title}</span>
          <LifePill life={t.life} agent={t.agent} />
        </div>
        <div className="gs-trow-sum">{t.summary}</div>
      </div>
      <div className="gs-trow-right">
        <span className={`gs-due ${t.hot ? "hot" : ""}`}>{t.due || "no deadline"}</span>
        <span className="gs-score">{t.score}</span>
        <ChevronRight size={15} color="var(--ink-3)" />
      </div>
    </div>
  );
}
