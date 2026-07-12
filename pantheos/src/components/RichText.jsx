import React from "react";
import { useNav } from "../nav.jsx";

// Renders text with known ticket IDs turned into clickable refs.
export default function RichText({ text }) {
  const { go, tickets } = useNav();
  const ids = tickets.map((t) => t.id);
  if (ids.length === 0) return <>{text}</>;
  const re = new RegExp(`\\b(${ids.join("|")})\\b`, "g");
  const parts = text.split(re);
  return (
    <>
      {parts.map((p, i) =>
        ids.includes(p) ? (
          <span key={i} className="gs-ref" onClick={() => go({ view: "queue", ticketId: p })}>{p}</span>
        ) : (
          <React.Fragment key={i}>{p}</React.Fragment>
        )
      )}
    </>
  );
}
