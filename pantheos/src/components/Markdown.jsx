import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import { useNav } from "../nav.jsx";

// Wrap known ticket ids in a plain string into clickable refs.
function linkTickets(text, ids, go) {
  if (!ids.length || typeof text !== "string") return text;
  const re = new RegExp(`\\b(${ids.join("|")})\\b`, "g");
  const parts = text.split(re);
  return parts.map((p, i) =>
    ids.includes(p) ? (
      <span key={i} className="gs-ref" onClick={() => go({ view: "queue", ticketId: p })}>{p}</span>
    ) : (
      <React.Fragment key={i}>{p}</React.Fragment>
    )
  );
}

export default function Markdown({ text }) {
  const { go, tickets } = useNav();
  const ids = tickets.map((t) => t.id);
  const withRefs = (children) =>
    React.Children.map(children, (c) =>
      typeof c === "string" ? linkTickets(c, ids, go) : c
    );
  return (
    <div className="gs-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
          p: ({ children }) => <p>{withRefs(children)}</p>,
          li: ({ children }) => <li>{withRefs(children)}</li>,
        }}
      >
        {text || ""}
      </ReactMarkdown>
    </div>
  );
}
