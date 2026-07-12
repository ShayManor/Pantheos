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

  getAreaContext: (id) => req("GET", `/api/areas/${id}/context`),
  setAreaContext: (id, context) => req("PUT", `/api/areas/${id}/context`, { context }),
  getProjectContext: (key) => req("GET", `/api/projects/${key}/context`),
  setProjectContext: (key, context) => req("PUT", `/api/projects/${key}/context`, { context }),

  delphiContext: () => req("GET", "/api/delphi/context"),
  chat: (text) => req("POST", "/api/delphi/chat", { text }),
  draftTicket: (ctx) => req("POST", "/api/delphi/draft_ticket", ctx),
  addConnector: (name, url) => req("POST", "/api/delphi/connectors", { name, url }),
  toggleConnector: (id, on) => req("PATCH", `/api/delphi/connectors/${id}`, { on }),
  deleteConnector: (id) => req("DELETE", `/api/delphi/connectors/${id}`),
  addSkill: (name) => req("POST", "/api/delphi/skills", { name }),
  toggleSkill: (id, on) => req("PATCH", `/api/delphi/skills/${id}`, { on }),
  deleteSkill: (id) => req("DELETE", `/api/delphi/skills/${id}`),
};
