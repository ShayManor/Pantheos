"""Baseline seed data, mapped onto the real schema from docs/spec.md.

Seeds the real, stable scaffolding — areas, projects, the deployed containers,
the model catalog, MCP server, and memory facts. Live content (tickets, Delphi
sessions, agent runs) is created at runtime, not seeded.
"""

# ---------------------------------------------------------------- areas
# kind: lab | club | class | personal
AREAS = [
    {"id": "ideas_lab", "name": "IDEAS LAB", "kind": "lab"},
    {"id": "side", "name": "SIDE PROJECTS", "kind": "personal"},
    {"id": "evc", "name": "EVC", "kind": "club"},
    {"id": "stat511", "name": "STAT 511", "kind": "class"},
]

# ---------------------------------------------------------------- projects
# status is a denormalized health indicator (go|cau|flt|los) for the UI.
PROJECTS = [
    {"key": "merlin", "area_id": "ideas_lab", "name": "MERLIN", "autonomy": "auto_pr",
     "status": "go", "users": None, "repo": "ideas-lab/merlin",
     "blurb": "Metric edge reconstruction for lightweight indoor nav"},
    {"key": "guardrail", "area_id": "ideas_lab", "name": "Guardrail", "autonomy": "auto_pr",
     "status": "go", "users": None, "repo": "ideas-lab/guardrail",
     "blurb": "Teacher-supervised failure detection under domain shift"},
    {"key": "ghstats", "area_id": "side", "name": "gh-stats", "autonomy": "full",
     "status": "flt", "users": 3820, "repo": "shaymanor/gh-stats",
     "blurb": "GitHub profile analytics"},
    {"key": "gpufindr", "area_id": "side", "name": "GPUFindr", "autonomy": "full",
     "status": "cau", "users": 1140, "repo": "shaymanor/gpufindr",
     "blurb": "GPU availability + price aggregator"},
    {"key": "rviewer", "area_id": "side", "name": "ResearchViewer", "autonomy": "full",
     "status": "go", "users": None, "repo": "shaymanor/researchviewer",
     "blurb": "Explore & analyze 2.9M arXiv papers — search, topics, and recommendations"},
    {"key": "evc", "area_id": "evc", "name": "Autonomy Stack", "autonomy": "propose",
     "status": "go", "users": None, "repo": "evc-purdue/autonomy",
     "blurb": "Autonomous kart control + perception"},
    {"key": "groundstation", "area_id": "side", "name": "Pantheos", "autonomy": "full",
     "status": "go", "users": None, "repo": "shaymanor/pantheos",
     "blurb": "This platform — tickets, monitoring, and Delphi"},
]

# ---------------------------------------------------------------- tickets
# deadline_hours: hours from the seed anchor (None = no deadline).
# effort_hours:   estimated work. Both feed the derived score (spec 1.5).
# Real tickets arrive at runtime (Alertmanager webhook, the New-ticket modal,
# Delphi); none are seeded.
TICKETS = []

# ---------------------------------------------------------------- hosts
# expectation: always_on | intermittent
HOSTS = [
    {"id": "minipc", "name": "minipc", "kind": "always_on", "icon": "Server",
     "tag": "ALWAYS-ON · local", "loc": "Purdue apt"},
]

# ---------------------------------------------------------------- containers
# A container belongs to exactly one project and runs on exactly one host.
# Only the real, deployed containers are seeded; live metrics come from the
# monitor (VictoriaMetrics/Caddy) for the instrumented ones.
CONTAINERS = [
    {"id": "gh-stats-api", "proj": "ghstats", "host": "minipc", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghstats/api"},
    {"id": "gh-stats-web", "proj": "ghstats", "host": "minipc", "role": "web", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghstats/web"},
    {"id": "gpufindr-api", "proj": "gpufindr", "host": "minipc", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "gpufindr/api"},
    {"id": "gpufindr-scraper", "proj": "gpufindr", "host": "minipc", "role": "worker", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "gpufindr/scraper"},
    {"id": "gs-platform", "proj": "groundstation", "host": "minipc", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "pantheos/platform"},
    {"id": "rviewer", "proj": "rviewer", "host": "minipc", "role": "web", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "researchviewerapi"},
]

# ---------------------------------------------------------------- Delphi config
MCP_SERVERS = [
    {"id": "pantheos", "name": "Pantheos", "url": "mcp.pantheos.local", "tools": "—",
     "on": True, "desc": "Tickets, monitor, memory & Claude Code — grounded in each project's spec"},
]

SKILLS = []

MEMORY_FACTS = [
    "Acts through the Pantheos MCP server — 24 live tools over tickets, monitor, memory and Claude Code",
    "Reads a project's spec and autonomy ceiling before acting; grounds every claim in a tool call",
    "Autonomy is a hard ceiling — propose is PR-only and never touches main",
    "Runs on Hermes over ACP; delegates real code changes to Claude Code",
]

AGENT_RUNS = []

MODELS = [
    # id = the model string sent to the OpenAI-compatible API (chosen in the UI).
    {"id": "gpt-5.6-terra", "name": "GPT Terra", "tag": "openai · gpt-5.6"},
    {"id": "gpt-5.6-luna", "name": "GPT Luna", "tag": "openai · gpt-5.6"},
    {"id": "zai/glm-5.2", "name": "GLM 5.2", "tag": "z.ai · glm-5.2"},
]

SESSIONS = []

GREETING = "Delphi online. Ask me about your tickets, projects, or fleet."
