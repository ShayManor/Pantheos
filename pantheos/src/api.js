async function req(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`${method} ${url} → ${res.status}`);
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export const api = {
  tickets: () => req("GET", "/api/tickets"),
  createTicket: (data) => req("POST", "/api/tickets", data),
  areas: () => req("GET", "/api/areas"),
  projects: () => req("GET", "/api/projects"),
  hosts: () => req("GET", "/api/hosts"),
  containers: () => req("GET", "/api/containers"),
  containerMetrics: (id) => req("GET", `/api/containers/${id}/metrics`),
  containerLogs: (id) => req("GET", `/api/containers/${id}/logs`),
  usage: () => req("GET", "/api/monitor/usage"),
  errseries: () => req("GET", "/api/monitor/errseries"),

  launch: (id) => req("POST", `/api/tickets/${id}/launch`),
  setLife: (id, life) => req("PATCH", `/api/tickets/${id}`, { life }),
  deleteTicket: (id) => req("DELETE", `/api/tickets/${id}`),

  getAreaContext: (id) => req("GET", `/api/areas/${id}/context`),
  setAreaContext: (id, context) => req("PUT", `/api/areas/${id}/context`, { context }),
  getProjectContext: (key) => req("GET", `/api/projects/${key}/context`),
  setProjectContext: (key, context) => req("PUT", `/api/projects/${key}/context`, { context }),

  delphiContext: () => req("GET", "/api/delphi/context"),
  createSession: (title) => req("POST", "/api/delphi/sessions", { title }),
  listSessions: () => req("GET", "/api/delphi/sessions"),
  getSession: (id) => req("GET", `/api/delphi/sessions/${id}`),
  deleteSession: (id) => req("DELETE", `/api/delphi/sessions/${id}`),
  chatStream: async (sessionId, text, h, model) => {
    const res = await fetch("/api/delphi/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, text, model }),
    });
    if (!res.ok || !res.body) { h.onError?.({ message: `HTTP ${res.status}` }); return; }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let sep;
      while ((sep = buf.indexOf("\n\n")) !== -1) {
        const frame = buf.slice(0, sep); buf = buf.slice(sep + 2);
        let ev = null, data = null;
        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) ev = line.slice(6).trim();
          else if (line.startsWith("data:")) data = line.slice(5).trim();
        }
        if (!data) continue;
        const p = JSON.parse(data);
        if (ev === "reasoning") h.onReasoning?.(p.delta);
        else if (ev === "text") h.onText?.(p.delta);
        else if (ev === "tool") h.onTool?.(p);
        else if (ev === "done") h.onDone?.(p);
        else if (ev === "error") h.onError?.(p);
      }
    }
  },
  draftTicket: (ctx) => req("POST", "/api/delphi/draft_ticket", ctx),
  addConnector: (name, url, token) => req("POST", "/api/delphi/connectors", { name, url, token }),
  toggleConnector: (id, on) => req("PATCH", `/api/delphi/connectors/${id}`, { on }),
  deleteConnector: (id) => req("DELETE", `/api/delphi/connectors/${id}`),
  addSkill: (name) => req("POST", "/api/delphi/skills", { name }),
  toggleSkill: (id, on) => req("PATCH", `/api/delphi/skills/${id}`, { on }),
  deleteSkill: (id) => req("DELETE", `/api/delphi/skills/${id}`),
};
