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
     "status": "go", "users": None, "repo": "ShayManor/Merlin",
     "blurb": "Metric edge reconstruction for lightweight indoor nav",
     "notes": [
         "1.23B metric-3D teacher distilled to a 230M student; 0.178 abs_rel vs the teacher.",
         "Deploys at 16-17 FPS TRT-INT8 @378px, ~9.8 W, 0.68 GB on a $249 Jetson Orin Nano 8GB.",
         "Metric scale (0.4-1.3% err) comes from a decoupled VI front end — the student is a poor ego-motion estimator.",
         "A 9-axis IMU bounds drift to ~1.5-2%, but indoors needs a visual yaw reference, not the magnetometer.",
         "Nav is planner-bound, not perception-bound: a perfect-depth oracle navigates worse, so run the cheapest op point.",
         "Model + ONNX: huggingface.co/ShayManor/merlin-mapanything-student.",
         "Runs on-device (Jetson), not as a container in the fleet.",
     ]},
    {"key": "guardrail", "area_id": "ideas_lab", "name": "Guardrail", "autonomy": "auto_pr",
     "status": "go", "users": None, "repo": "ShayManor/Guardrail-Distillation",
     "blurb": "Teacher-supervised failure detection under domain shift",
     "notes": [
         "A compact SegFormer student pairs with a lightweight guardrail head that predicts student failure without calling the teacher at test time.",
         "Trained on dense teacher-derived targets; the key comparison is teacher-supervised vs GT-supervised vs post-hoc (MSP, temp-scaled MSP, entropy, MaxLogit, MC-Dropout).",
         "Pipeline: Cityscapes -> student_sup.ckpt -> student_kd/student_skd.ckpt -> frozen student + teacher -> guardrail.ckpt. Shift eval on ACDC.",
         "Under anonymous review — keep author/institution identifiers and public release links out of the repo.",
     ]},
    {"key": "ghstats", "area_id": "side", "name": "gh-stats", "autonomy": "full",
     "status": "go", "users": 146, "repo": "ShayManor/github-readme-stats",
     "blurb": "GitHub README widgets — editable, cached, drop-in profile stats",
     "notes": [
         "Live at gh-stats.com; a single SVG widget dropped into a profile README via /api/<username>.",
         "Monorepo of three independent Python services plus a Vite+React frontend.",
         "fetcher:5001 — owns the GitHub PAT and fetcher.db; serves /data/<u> to internal callers only.",
         "generator:5002 — owns the settings + widgets SQLite DBs; renders SVGs, serves the SPA and /api/*.",
         "edge:5003 — cache-first SVG proxy in front of the generator (Flask-Caching + Flask-Compress, optional Redis).",
         "Don't cross-import across services — they talk over HTTP. Each has its own requirements.txt, pytest.ini and Dockerfile.",
         "146 enrolled users (generator settings.db). daily_stats usernames include scanner noise — don't count them.",
     ]},
    {"key": "gpufindr", "area_id": "side", "name": "GPUFindr", "autonomy": "full",
     "status": "cau", "users": 1140, "repo": "ShayManor/GpuScanner",
     "blurb": "GPU availability + price aggregator",
     "notes": [
         "Live at gpufindr.com — a Go app scanning GPU price/availability across RunPod, TensorDock, Vast.ai and AWS Lambda.",
         "cmd/api — web API + frontend; cmd/blog — automated GPU-market blog generation.",
         "Exposes an MCP server so an agent can find and rent the best instance from a text prompt.",
         "Deployed on Google Cloud Run (project gpuscanner, us-central1, service gpu-api) — NOT the minipc.",
         "Image lives in Artifact Registry, not GHCR. gpufindr.com is a Cloud Run domain mapping onto gpu-api.",
     ]},
    {"key": "rviewer", "area_id": "side", "name": "ResearchViewer", "autonomy": "full",
     "status": "go", "users": None, "repo": "ShayManor/ResearchViewer",
     "blurb": "Explore & analyze 2.9M arXiv papers — search, topics, and recommendations",
     "notes": [
         "Live at researchviewer.org (API at /api). Self-hosted on the minipc.",
         "Backend: Flask + Gunicorn, DuckDB (2.9M papers, 1.7M authors, 11K microtopics), Firebase Auth, Redis caching.",
         "Frontend: React + TypeScript, Vite, TailwindCSS, Recharts.",
         "Dataset is huggingface-native: huggingface.co/datasets/ShayManor/Labeled-arXiv.",
         "Alerting already covers this site — pantheos_caddy_err_ratio{site=\"researchviewer.org\"} and a blackbox probe.",
     ]},
    {"key": "evc", "area_id": "evc", "name": "Autonomy Stack", "autonomy": "propose",
     "status": "go", "users": None, "repo": "EVC-Purdue/AutonomousKart",
     "blurb": "Autonomous kart control + perception",
     "notes": [
         "Full ROS2 self-driving stack for Purdue EVC's racing kart: 3DGS localization, EKF + RTK GPS, online param optimization.",
         "1st place International Autonomous Karting Series as a rookie team; Shay is the autonomous team lead.",
         "Club-owned org repo — autonomy is propose (branch + PR only), never commit to main.",
         "Sibling repos: EVC-Purdue/3DGS_Scene, global_racetrajectory_optimization, Autonomous_UI, RideBot.",
     ]},
    {"key": "horizon", "area_id": "ideas_lab", "name": "Horizon-Reduction", "autonomy": "auto_pr",
     "status": "go", "users": None, "repo": "ShayManor/horizon-reduction",
     "blurb": "Physics-informed horizon reduction for offline goal-conditioned RL",
     "notes": [
         "Fork of the official 'Horizon Reduction Makes RL Scalable' implementation (arXiv 2506.04168).",
         "IDEAS Lab work: improving SARSA / offline GCRL with physics-informed learning.",
         "Upstream ships five horizon-reduction techniques and five baselines; supports the 1B-sized OGBench datasets and oraclerep envs.",
         "Research code — no deployed container.",
     ]},
    {"key": "groundstation", "area_id": "side", "name": "Pantheos", "autonomy": "full",
     "status": "go", "users": None, "repo": "ShayManor/Pantheos",
     "blurb": "This platform — tickets, monitoring, and Delphi",
     "notes": [
         "Live at pantheos.app. Flask + React + Postgres; one image (ghcr.io/shaymanor/pantheos) runs the app, the MCP server and the Caddy log exporter.",
         "Deploys to the minipc via a self-hosted runner: docker.yml builds/pushes to GHCR, deploy.sh pulls and recreates the stack in ~/pantheos.",
         "Traffic path: cloudflared -> Caddy:8080 -> backends. Monitoring overlay is VictoriaMetrics + vmagent + vmalert + Alertmanager + cAdvisor + node/blackbox exporters.",
         "Alerts fire on pantheos_caddy_err_ratio > 0.05, probe_success == 0, container crash-looping and low host disk.",
     ]},
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
    {"id": "gcr", "name": "Google Cloud Run", "kind": "always_on", "icon": "Boxes",
     "tag": "ALWAYS-ON · managed", "loc": "us-central1"},
]

# ---------------------------------------------------------------- containers
# A container belongs to exactly one project and runs on exactly one host.
# Only the real, deployed containers are seeded; live metrics come from the
# monitor (VictoriaMetrics/Caddy) for the instrumented ones.
CONTAINERS = [
    {"id": "ghstats-edge", "proj": "ghstats", "host": "minipc", "role": "edge", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-edge"},
    {"id": "ghstats-generator", "proj": "ghstats", "host": "minipc", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-generator"},
    {"id": "ghstats-generator-worker", "proj": "ghstats", "host": "minipc", "role": "worker", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-generator"},
    {"id": "ghstats-generator-cron", "proj": "ghstats", "host": "minipc", "role": "cron", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-generator"},
    {"id": "ghstats-fetcher", "proj": "ghstats", "host": "minipc", "role": "fetcher", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-fetcher"},
    {"id": "ghstats-fetcher-cron", "proj": "ghstats", "host": "minipc", "role": "cron", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/ghstats-fetcher"},
    {"id": "gpu-api", "proj": "gpufindr", "host": "gcr", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "us-central1-docker.pkg.dev/gpuscanner/containers/gpu-api"},
    {"id": "pantheos-app-1", "proj": "groundstation", "host": "minipc", "role": "api", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/pantheos"},
    {"id": "pantheos-mcp-1", "proj": "groundstation", "host": "minipc", "role": "mcp", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/pantheos"},
    {"id": "pantheos-caddy-log-exporter-1", "proj": "groundstation", "host": "minipc", "role": "exporter", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/pantheos"},
    {"id": "pantheos-db-1", "proj": "groundstation", "host": "minipc", "role": "db", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "postgres:16-alpine"},
    {"id": "researchviewer", "proj": "rviewer", "host": "minipc", "role": "web", "status": "go",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "ghcr.io/shaymanor/researchviewerapi"},
]

# ---------------------------------------------------------------- Delphi config
MCP_SERVERS = [
    {"id": "pantheos", "name": "Pantheos", "url": "mcp.pantheos.local", "tools": "—",
     "on": True, "desc": "Tickets, monitor, memory & Claude Code — grounded in each project's spec"},
    {"id": "github", "name": "GitHub", "url": "api.githubcopilot.com/mcp", "tools": "47",
     "on": True, "desc": "Issues, PRs, code search & repo ops across your GitHub"},
    {"id": "huggingface", "name": "Hugging Face", "url": "huggingface.co/mcp", "tools": "9",
     "on": True, "desc": "Hub search, models, datasets, papers & Spaces"},
    {"id": "exa", "name": "Exa", "url": "mcp.exa.ai/mcp", "tools": "2",
     "on": True, "desc": "Neural web search & clean page fetch"},
    {"id": "wandb", "name": "Weights & Biases", "url": "mcp.withwandb.com/mcp", "tools": "30",
     "on": True, "desc": "Runs, sweeps, artifacts & Weave traces"},
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
