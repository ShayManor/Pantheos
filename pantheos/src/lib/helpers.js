import {
  Activity, Boxes, Calendar, Cpu, FileText, GitBranch, GitPullRequest,
  HardDrive, Hash, Link2, ListChecks, MessageSquare, Server, Terminal,
} from "lucide-react";

// host.icon is stored as a lucide component name; resolve it here.
export const HOST_ICONS = { Server, Boxes, Cpu, HardDrive };

export const LINK_ICON = {
  github_issue: GitBranch, github_pr: GitPullRequest, slack_message: MessageSquare,
  discord_message: MessageSquare, brightspace: Calendar, file: Hash, url: Link2,
};
export const LINK_KIND = {
  github_issue: "info", github_pr: "go", slack_message: "neu",
  brightspace: "cau", file: "neu", url: "neu",
};
export const TOOLMAP = {
  github: [GitBranch, "GitHub"], vm: [Activity, "VictoriaMetrics"], calendar: [Calendar, "Calendar"],
  brightspace: [FileText, "Brightspace"], queue: [ListChecks, "Queue"], claude: [Terminal, "Claude Code"],
};

export const autoLabel = (a) => ({ propose: "propose", auto_pr: "auto-pr", full: "full" }[a] || a);
export const registryUrl = (img) =>
  img.startsWith("gcr.io/") ? `https://${img}` : `https://ghcr.io/shaymanor/${img.split(":")[0]}`;
export const repoUrl = (r) => `https://github.com/${r}`;

export const rollup = (cs) => {
  if (!cs.length) return null;
  if (cs.some((c) => c.status === "flt")) return "flt";
  if (cs.some((c) => c.status === "cau")) return "cau";
  if (cs.every((c) => c.status === "los")) return "los";
  return "go";
};

// Resolve a ticket link to a real external URL, or null if it has no live target.
export const linkHref = (link, ticket, projects) => {
  const repo = ticket && ticket.proj ? projects[ticket.proj]?.repo : null;
  if ((link.kind === "github_issue" || link.kind === "github_pr") && repo && link.url?.startsWith("/"))
    return `https://github.com/${repo}${link.url}`;
  if (link.kind === "url" && /^https?:\/\//.test(link.url || "")) return link.url;
  return null;
};

export const openExternal = (url) => window.open(url, "_blank", "noopener,noreferrer");
