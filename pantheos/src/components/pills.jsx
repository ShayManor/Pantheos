import {
  AlertTriangle, CheckCircle2, CircleDot, Clock, PauseCircle, Rocket, Zap,
} from "lucide-react";

export const StatusPill = ({ s }) => {
  const map = { go: ["go", "NOMINAL"], cau: ["cau", "CAUTION"], flt: ["flt", "FAULT"], los: ["neu", "LOS"] };
  const [c, t] = map[s] || map.go;
  return (
    <span className={`pill ${c}`}>
      <span className={`dot ${s}`} style={{ width: 6, height: 6, boxShadow: "none" }} />
      {t}
    </span>
  );
};

export const LifePill = ({ life, agent }) => {
  if (agent === "executing") return <span className="pill go"><Rocket size={11} />EXECUTING</span>;
  if (agent === "enriching") return <span className="pill info"><Zap size={11} />ENRICHING</span>;
  const map = {
    active: ["go", CircleDot, "ACTIVE"], queued: ["neu", Clock, "QUEUED"],
    backburner: ["neu", PauseCircle, "BACKBURNER"], blocked: ["cau", AlertTriangle, "BLOCKED"],
    archived: ["neu", CheckCircle2, "ARCHIVED"],
  };
  const [c, I, t] = map[life] || map.queued;
  return <span className={`pill ${c}`}><I size={11} />{t}</span>;
};
