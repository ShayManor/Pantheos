import { useEffect, useRef, useState } from "react";
import {
  Brain, Check, ChevronDown, Copy, FileText, Hash, History, Mic, Paperclip,
  Plug, Plus, Radio, Rocket, Send, Settings, Sparkles, Square, SquarePen,
  Terminal, Trash2, Wrench, X, Zap,
} from "lucide-react";
import { useNav } from "../nav.jsx";
import Markdown from "../components/Markdown.jsx";
import Thinking from "../components/Thinking.jsx";
import { TOOLMAP } from "../lib/helpers.js";
import { api } from "../api.js";

function RunRow({ r }) {
  const { go } = useNav();
  return (
    <div className="gs-svc" style={{ gridTemplateColumns: "1fr auto auto auto", gap: 14 }} onClick={() => go({ view: "queue", ticketId: r.ticket })}>
      <div className="gs-svc-nm">
        {r.kind === "execute" ? <Rocket size={14} color="var(--go)" /> : <Zap size={14} color="var(--info)" />}
        <div><div className="id" style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{r.ticket}</div><div className="sub">{r.kind}</div></div>
      </div>
      <span className={`pill ${r.status === "needs review" ? "cau" : "go"}`}>{r.status}</span>
      <span className="gs-svc-val" style={{ color: "var(--ink-2)" }}>{r.cost}</span>
      <span className="gs-svc-val" style={{ color: "var(--ink-3)" }}>{r.when}</span>
    </div>
  );
}

export default function FlightView() {
  const { toast } = useNav();
  const [ctx, setCtx] = useState(null);
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [atts, setAtts] = useState([]);
  const [thinking, setThinking] = useState(false);
  const [recording, setRecording] = useState(false);
  const [drawer, setDrawer] = useState(null); // null | connectors | skills | memory
  const [histOpen, setHistOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [activeSess, setActiveSess] = useState(null);
  const [model, setModel] = useState(null);
  const [modelOpen, setModelOpen] = useState(false);
  const [servers, setServers] = useState([]);
  const [skills, setSkills] = useState([]);
  const [newSrv, setNewSrv] = useState({ name: "", url: "" });
  const [newSkill, setNewSkill] = useState("");
  const fileRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.delphiContext().then((d) => {
      setCtx(d);
      setMsgs([{ who: "flight", text: d.greeting }]);
      setSessions(d.sessions);
      setServers(d.connectors);
      setSkills(d.skills);
      setModel(d.models[0]);
    });
  }, []);
  useEffect(() => { scrollRef.current?.scrollTo(0, 1e6); }, [msgs, thinking]);

  const suggestions = [
    ["What's due this week?", "Deadlines, ranked by urgency"],
    ["What's on fire?", "Containers needing attention"],
    ["Re-rank my queue", "Recompute importance × urgency"],
    ["Summarize my projects", "Health across the fleet"],
  ];

  const send = async (q) => {
    const text = q ?? input.trim();
    if (!text && atts.length === 0) return;
    const sent = atts;
    setMsgs((m) => [...m, { who: "me", text: text || "(attachment)", atts: sent },
                          { who: "flight", text: "", reasoning: "", tools: [], live: true }]);
    setInput(""); setAtts([]); setThinking(true);
    const patchLast = (fn) => setMsgs((m) => m.map((x, i) => (i === m.length - 1 ? fn(x) : x)));
    let sess = activeSess;
    if (!sess) {
      const s = await api.createSession(text.slice(0, 42));
      sess = s.id;
      setActiveSess(s.id);
      setSessions((x) => [s, ...x]);
    }
    api.chatStream(sess, text, {
      onReasoning: (d) => patchLast((x) => ({ ...x, reasoning: x.reasoning + d })),
      onText: (d) => { setThinking(false); patchLast((x) => ({ ...x, text: x.text + d, live: false })); },
      onTool: (t) => patchLast((x) => x.tools.includes(t.name) ? x : ({ ...x, tools: [...x.tools, t.name] })),
      onDone: (p) => { setThinking(false); patchLast((x) => ({ ...x, text: p.text, reasoning: p.reasoning, tools: p.tools, live: false })); },
      onError: (e) => { setThinking(false); patchLast((x) => ({ ...x, text: x.text || "⚠️ Delphi is unreachable.", live: false })); toast(e.message || "Stream error"); },
    }, model?.id);
  };
  const onFiles = (e) => {
    const picked = Array.from(e.target.files || []).map((f) => ({ name: f.name, img: f.type.startsWith("image/") }));
    setAtts((a) => [...a, ...picked]); e.target.value = "";
  };
  const stopRec = () => { setRecording(false); };
  const addServer = () => {
    if (!newSrv.name.trim()) return;
    api.addConnector(newSrv.name.trim(), newSrv.url.trim()).then((srv) => {
      setServers((s) => [srv, ...s]); toast(`Connected ${srv.name}`);
    });
    setNewSrv({ name: "", url: "" });
  };
  const toggleServer = (s) => {
    api.toggleConnector(s.id, !s.on).then((u) => setServers((list) => list.map((x) => (x.id === u.id ? u : x))));
  };
  const removeServer = (s) => {
    api.deleteConnector(s.id).then(() => setServers((list) => list.filter((x) => x.id !== s.id)));
  };
  const addSkill = () => {
    if (!newSkill.trim()) return;
    api.addSkill(newSkill.trim()).then((sk) => { setSkills((s) => [sk, ...s]); toast(`Added ${sk.name}`); });
    setNewSkill("");
  };
  const toggleSkill = (s) => {
    api.toggleSkill(s.id, !s.on).then((u) => setSkills((list) => list.map((x) => (x.id === u.id ? u : x))));
  };
  const removeSkill = (s) => {
    api.deleteSkill(s.id).then(() => setSkills((list) => list.filter((x) => x.id !== s.id)));
  };
  const copy = (t) => { try { navigator.clipboard?.writeText(t); } catch (e) { /* noop */ } toast("Copied to clipboard"); };

  const newChat = () => {
    setActiveSess(null);
    setMsgs([{ who: "flight", text: ctx.greeting }]);
    toast("Started a new chat");
  };
  const loadSession = (sess) => {
    api.getSession(sess.id).then((full) => {
      setActiveSess(full.id);
      setMsgs(full.msgs.length ? full.msgs : [{ who: "flight", text: ctx.greeting }]);
      setHistOpen(false);
    });
  };
  const welcome = msgs.length <= 1;

  if (!ctx) return <div className="gs-empty">Connecting to Delphi…</div>;

  return (
    <div className="gs-flight-wrap">
      <div className="gs-fl-head">
        <div className="gs-fl-id">
          <div className="gs-fl-av"><Radio size={17} /></div>
          <div>
            <div className="gs-fl-nm">Delphi</div>
            <div className="gs-fl-st"><span className="dot go" style={{ boxShadow: "none", width: 6, height: 6 }} />ONLINE · {servers.filter((s) => s.on).length} CONNECTORS</div>
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, position: "relative" }}>
          <button className="gs-model" onClick={() => setModelOpen((v) => !v)}>
            <Sparkles size={14} color="var(--go)" />{model?.name}<ChevronDown size={14} color="var(--ink-3)" />
          </button>
          {modelOpen && (
            <>
              <div className="gs-menu-catch" onClick={() => setModelOpen(false)} />
              <div className="gs-menu">
                <div className="gs-menu-lbl">Agent model</div>
                {ctx.models.map((mo) => (
                  <button key={mo.id} className="gs-menu-item" onClick={() => { setModel(mo); setModelOpen(false); toast(`Switched to ${mo.name}`); }}>
                    <div><div className="t">{mo.name}</div><div className="g">{mo.tag}</div></div>
                    {model?.id === mo.id && <span className="chk"><Check size={15} /></span>}
                  </button>
                ))}
              </div>
            </>
          )}
          <button className="gs-hbtn icon" onClick={() => { api.listSessions().then(setSessions); setHistOpen(true); }} title="Chat history"><History size={16} /></button>
          <button className="gs-hbtn" onClick={newChat}><SquarePen size={15} />New</button>
          <button className="gs-hbtn icon" onClick={() => setDrawer("connectors")} title="Connectors, skills & memory"><Settings size={16} /></button>
        </div>
      </div>

      <div className="gs-flight-content">
        <div className="gs-msgs" ref={scrollRef}>
          {welcome ? (
            <div className="gs-welcome">
              <div className="gs-fl-av" style={{ width: 44, height: 44, borderRadius: 12 }}><Radio size={22} /></div>
              <h2>Talk to Delphi</h2>
              <p>It knows every ticket, project, and container you own.</p>
              <div className="gs-sugg">
                {suggestions.map(([t, d]) => (
                  <button key={t} onClick={() => send(t)}><span className="t">{t}</span><span className="d">{d}</span></button>
                ))}
              </div>
            </div>
          ) : msgs.map((m, i) => (
            <div key={i} className={`gs-msg ${m.who}`}>
              <div className={`gs-msg-av ${m.who === "flight" ? "flight" : "me"}`}>
                {m.who === "flight" ? <Radio size={15} /> : <span style={{ fontFamily: "var(--mono)", fontSize: 11 }}>S</span>}
              </div>
              <div style={{ minWidth: 0 }}>
                {m.who === "flight" && (m.reasoning || m.live) && (
                  <Thinking reasoning={m.reasoning} live={m.live && !m.text} />
                )}
                {m.tools && m.tools.length > 0 && (
                  <div className="gs-tools">
                    {m.tools.map((tk) => { const [I, label] = TOOLMAP[tk] || [Wrench, tk]; return (
                      <span key={tk} className="gs-toolchip"><span className="ck"><Check size={10} /></span><I size={11} />{label}</span>
                    ); })}
                  </div>
                )}
                <div className="gs-bub">{m.who === "flight" ? <Markdown text={m.text} /> : m.text}</div>
                {m.atts && m.atts.length > 0 && (
                  <div className="gs-atts" style={{ marginTop: 7, marginBottom: 0 }}>
                    {m.atts.map((a, j) => <span key={j} className="gs-att">{a.img ? <Hash size={12} /> : <FileText size={12} />}<span className="nm">{a.name}</span></span>)}
                  </div>
                )}
                {m.who === "flight" && (
                  <div className="gs-msg-copy">
                    <button onClick={() => copy(m.text)}><Copy size={11} />Copy</button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {!welcome && (
          <div className="gs-chips">
            {suggestions.slice(0, 4).map(([c]) => <button key={c} className="gs-chip" onClick={() => send(c)}>{c}</button>)}
          </div>
        )}

        {atts.length > 0 && (
          <div className="gs-atts">
            {atts.map((a, i) => (
              <span key={i} className="gs-att">{a.img ? <Hash size={12} /> : <FileText size={12} />}<span className="nm">{a.name}</span>
                <span className="rm" onClick={() => setAtts(atts.filter((_, j) => j !== i))}><X size={13} /></span></span>
            ))}
          </div>
        )}

        <div className="gs-composer">
          <input ref={fileRef} type="file" multiple hidden onChange={onFiles} />
          {recording ? (
            <div className="gs-recbar">
              <span className="dot flt" style={{ boxShadow: "none" }} />
              <span className="gs-rec-label">Listening…</span>
              <div className="gs-wave">{Array.from({ length: 7 }).map((_, i) => <i key={i} />)}</div>
              <div style={{ flex: 1 }} />
              <button className="gs-btn ghost" onClick={stopRec}><Square size={13} />Stop</button>
            </div>
          ) : (
            <>
              <button className="gs-attach-btn" onClick={() => fileRef.current?.click()} title="Attach files or images"><Paperclip size={17} /></button>
              <button className="gs-mic" onClick={() => setRecording(true)} title="Dictate"><Mic size={17} /></button>
              <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask Delphi, attach a file, or dictate…" />
              <button className="gs-btn primary" onClick={() => send()}><Send size={15} /></button>
            </>
          )}
        </div>
      </div>

      {histOpen && (
        <>
          <div className="gs-drawer-bg" onClick={() => setHistOpen(false)} />
          <div className="gs-drawer left">
            <div className="gs-drawer-head">
              <History size={16} color="var(--ink-2)" />
              <span className="ttl">Chats</span>
              <button className="gs-hbtn" style={{ marginLeft: "auto" }} onClick={() => { newChat(); setHistOpen(false); }}><SquarePen size={14} />New</button>
              <button className="gs-hbtn icon" onClick={() => setHistOpen(false)}><X size={16} /></button>
            </div>
            <div className="gs-drawer-body">
              {!welcome && (
                <div className="gs-sess active">
                  <span className="t">{(msgs.find((m) => m.who === "me")?.text || "Current chat").slice(0, 42)}</span>
                  <span className="m"><span>Current</span><span>{msgs.filter((m) => m.who === "me").length} messages</span></span>
                </div>
              )}
              {sessions.filter((s) => s.id !== activeSess).length === 0
                ? (welcome ? <div className="gs-empty">No past chats yet.</div> : null)
                : sessions.filter((s) => s.id !== activeSess).map((s) => (
                  <div key={s.id} className="gs-sess" onClick={() => loadSession(s)}>
                    <span className="t">{s.title}</span>
                    <span className="m"><span>{s.ts}</span><span>{s.msgs.filter((m) => m.who === "me").length} messages</span></span>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}

      {drawer && (
        <>
          <div className="gs-drawer-bg" onClick={() => setDrawer(null)} />
          <div className="gs-drawer">
            <div className="gs-drawer-head">
              <Sparkles size={16} color="var(--go)" />
              <span className="ttl">Agent context</span>
              <button className="gs-hbtn icon" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><X size={16} /></button>
            </div>
            <div style={{ padding: "12px 18px 0" }}>
              <div className="gs-toggle" style={{ marginBottom: 4, width: "100%" }}>
                {[["connectors", "Connectors", Plug], ["skills", "Skills", Wrench], ["memory", "Memory", Brain]].map(([k, label, I]) => (
                  <button key={k} className={drawer === k ? "on" : ""} onClick={() => setDrawer(k)} style={{ flex: 1, justifyContent: "center" }}><I size={13} />{label}</button>
                ))}
              </div>
            </div>
            <div className="gs-drawer-body">
              {drawer === "connectors" && (
                <>
                  {servers.map((s) => (
                    <div key={s.id} className={`gs-conn ${s.on ? "" : "off"}`}>
                      <div className="gs-conn-ic"><Plug size={16} /></div>
                      <div style={{ minWidth: 0 }}>
                        <div className="gs-conn-nm">{s.name}<span className="pill neu" style={{ fontSize: 9 }}>{s.tools} tools</span></div>
                        <div className="gs-conn-meta">{s.url}</div>
                      </div>
                      <div className="gs-conn-act">
                        <div className={`gs-switch ${s.on ? "on" : ""}`} onClick={() => toggleServer(s)} />
                        <button className="gs-icon-btn" title="Delete connector" onClick={() => removeServer(s)}><Trash2 size={15} /></button>
                      </div>
                    </div>
                  ))}
                  <div className="gs-addrow" style={{ flexDirection: "column" }}>
                    <input className="gs-input" placeholder="Connector name" value={newSrv.name} onChange={(e) => setNewSrv({ ...newSrv, name: e.target.value })} />
                    <div style={{ display: "flex", gap: 8 }}>
                      <input className="gs-input" placeholder="server URL" value={newSrv.url} onChange={(e) => setNewSrv({ ...newSrv, url: e.target.value })} onKeyDown={(e) => e.key === "Enter" && addServer()} />
                      <button className="gs-btn primary" onClick={addServer}><Plus size={15} />Add</button>
                    </div>
                  </div>
                </>
              )}
              {drawer === "skills" && (
                <>
                  {skills.map((s) => (
                    <div key={s.id} className={`gs-conn ${s.on ? "" : "off"}`}>
                      <div className="gs-conn-ic"><Wrench size={15} /></div>
                      <div style={{ minWidth: 0 }}>
                        <div className="gs-conn-nm" style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{s.name}<span className="pill neu" style={{ fontSize: 9, fontFamily: "var(--sans)" }}>{s.trigger}</span></div>
                        <div className="gs-conn-meta" style={{ fontFamily: "var(--sans)", fontSize: 11.5, whiteSpace: "normal" }}>{s.desc}</div>
                      </div>
                      <div className="gs-conn-act">
                        <div className={`gs-switch ${s.on ? "on" : ""}`} onClick={() => toggleSkill(s)} />
                        <button className="gs-icon-btn" onClick={() => removeSkill(s)}><Trash2 size={15} /></button>
                      </div>
                    </div>
                  ))}
                  <div className="gs-addrow">
                    <input className="gs-input" placeholder="skill-name" value={newSkill} onChange={(e) => setNewSkill(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addSkill()} />
                    <button className="gs-btn primary" onClick={addSkill}><Plus size={15} />Add</button>
                  </div>
                </>
              )}
              {drawer === "memory" && (
                <>
                  <div className="gs-section-h" style={{ marginBottom: 6 }}><Brain size={12} />LEARNED FACTS</div>
                  <div className="gs-card" style={{ padding: "6px 16px", marginBottom: 22 }}>
                    {ctx.memory.map((f, i) => <div key={i} className="gs-fact"><Check size={15} color="var(--go)" style={{ flexShrink: 0, marginTop: 1 }} />{f}</div>)}
                  </div>
                  <div className="gs-section-h" style={{ marginBottom: 10 }}><Terminal size={12} />RECENT RUNS</div>
                  <div className="gs-card">{ctx.runs.map((r, i) => <RunRow key={i} r={r} />)}</div>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
