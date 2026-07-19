import { useState } from "react";
import { ChevronDown, Check } from "lucide-react";

export default function Dropdown({ label, value, options, onChange }) {
  const [open, setOpen] = useState(false);
  const cur = options.find((o) => o.value === value);
  return (
    <div style={{ position: "relative" }}>
      <button className="gs-model" onClick={() => setOpen((v) => !v)}>
        {label && <span style={{ color: "var(--ink-3)", fontFamily: "var(--mono)", fontSize: 11 }}>{label}</span>}
        {cur?.label ?? value}
        <ChevronDown size={14} color="var(--ink-3)" />
      </button>
      {open && (
        <>
          <div className="gs-menu-catch" onClick={() => setOpen(false)} />
          <div className="gs-menu">
            {options.map((o) => (
              <button key={o.value} className="gs-menu-item" onClick={() => { onChange(o.value); setOpen(false); }}>
                <div><div className="t">{o.label}</div></div>
                {o.value === value && <span className="chk"><Check size={15} /></span>}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
