import { Check, Terminal, Wrench } from "lucide-react";
import Thinking from "./Thinking.jsx";
import Markdown from "./Markdown.jsx";
import { TOOLMAP } from "../lib/helpers.js";

// Renders a Delphi ticket run — live (streaming) or a persisted transcript.
export default function DelphiActivity({ run }) {
  if (!run) return null;
  const live = run.status === "running";
  return (
    <div className="gs-section">
      <div className="gs-section-h">
        <Terminal size={12} />DELPHI ACTIVITY · {live ? "running…" : "completed"}
      </div>
      {(run.reasoning || live) && <Thinking reasoning={run.reasoning} live={live && !run.output} />}
      {run.tools && run.tools.length > 0 && (
        <div className="gs-tools">
          {run.tools.map((tk) => {
            const [I, label] = TOOLMAP[tk] || [Wrench, tk];
            return (
              <span key={tk} className="gs-toolchip">
                <span className="ck"><Check size={10} /></span><I size={11} />{label}
              </span>
            );
          })}
        </div>
      )}
      {run.output && <div className="gs-bub"><Markdown text={run.output} /></div>}
    </div>
  );
}
