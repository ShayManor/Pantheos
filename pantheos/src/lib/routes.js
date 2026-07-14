// Bijection between a navigation node (the shape App.jsx pushes onto `stack`)
// and a URL path, so the browser History API can back the in-app nav stack.
// Keep this in sync with App.jsx's `body` dispatch — same nodes, same order.

export function pathForNode(node) {
  if (!node) return "/queue";
  if (node.ticketId) return `/tickets/${node.ticketId}`;
  if (node.containerId) return `/monitor/containers/${node.containerId}${node.logs ? "/logs" : ""}`;
  const v = node.view || "queue";
  if (v === "monitor") {
    if (node.projectId) return `/monitor/projects/${node.projectId}`;
    if (node.hostId) return `/monitor/hosts/${node.hostId}`;
    return "/monitor";
  }
  if (v === "projects") return node.projectId ? `/projects/${node.projectId}` : "/projects";
  if (v === "flight") return "/delphi";
  return "/queue";
}

export function nodeFromPath(pathname) {
  const [a, b, c, d] = pathname.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean);
  if (a === "tickets" && b) return { view: "queue", ticketId: b };
  if (a === "projects") return b ? { view: "projects", projectId: b } : { view: "projects" };
  if (a === "monitor") {
    if (b === "projects" && c) return { view: "monitor", projectId: c };
    if (b === "hosts" && c) return { view: "monitor", hostId: c };
    if (b === "containers" && c) return d === "logs"
      ? { view: "monitor", containerId: c, logs: true }
      : { view: "monitor", containerId: c };
    return { view: "monitor" };
  }
  if (a === "delphi") return { view: "flight" };
  return { view: "queue" };
}

// Expand a deep-linked path into a full nav stack, so a refresh at e.g.
// /tickets/X lands with the queue underneath it and "back" returns there
// instead of leaving the app.
export function stackFromPath(pathname) {
  const leaf = nodeFromPath(pathname);
  if (leaf.ticketId) return [{ view: "queue" }, leaf];
  if (leaf.containerId && leaf.logs) return [{ view: "monitor" }, { view: "monitor", containerId: leaf.containerId }, leaf];
  if (leaf.containerId) return [{ view: "monitor" }, leaf];
  if (leaf.view === "monitor" && (leaf.projectId || leaf.hostId)) return [{ view: "monitor" }, leaf];
  if (leaf.view === "projects" && leaf.projectId) return [{ view: "projects" }, leaf];
  return [leaf];
}
