import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useNav } from "../nav.jsx";
import DelphiActivity from "../components/DelphiActivity.jsx";
import { api } from "../api.js";

// Full-page transcript for a ticket's Delphi run. Prefers the live run from
// App state; falls back to the persisted transcript on direct load / reload.
export default function TicketRunView({ id }) {
  const { tickets, runsByTicket, back } = useNav();
  const live = runsByTicket[id];
  const [persisted, setPersisted] = useState(null);
  const t = tickets.find((x) => x.id === id);

  useEffect(() => {
    if (!live) api.ticketRuns(id).then((rs) => setPersisted(rs[0] || null));
  }, [id, live]);

  const run = live || persisted;
  return (
    <div>
      <div className="gs-eyebrow">
        <button className="gs-btn ghost" onClick={back}><ArrowLeft size={14} />Back to ticket</button>
        <span style={{ fontFamily: "var(--mono)" }}>{id}</span>
      </div>
      <h1 className="gs-h1">Delphi run · {t ? t.title : id}</h1>
      {run ? <DelphiActivity run={run} /> : <div className="gs-empty">No run yet. Launch Delphi from the ticket.</div>}
    </div>
  );
}
