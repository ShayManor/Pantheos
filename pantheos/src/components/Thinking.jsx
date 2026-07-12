import { useState } from "react";
import { Brain, ChevronDown, ChevronRight } from "lucide-react";
import Markdown from "./Markdown.jsx";

// Collapsible chain-of-thought. `live` = still streaming (no text yet).
export default function Thinking({ reasoning, live }) {
  const [open, setOpen] = useState(false);
  if (!reasoning && !live) return null;
  return (
    <div className={`gs-cot ${open ? "open" : ""}`}>
      <button className="gs-cot-head" onClick={() => setOpen((v) => !v)}>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        <Brain size={13} />
        <span>{live ? "Thinking…" : "Thought process"}</span>
      </button>
      {open && reasoning && (
        <div className="gs-cot-body"><Markdown text={reasoning} /></div>
      )}
    </div>
  );
}
