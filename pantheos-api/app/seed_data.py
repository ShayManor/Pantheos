"""Mock seed data, transcribed from the design prototype (code.jsx) and mapped
onto the real schema from docs/spec.md.

Tickets carry a real ``deadline_hours`` offset (hours from the seed anchor) and
``effort_hours`` so the score in spec section 1.5 can be *derived* rather than
hard-coded. Everything else mirrors the prototype's inline constants.
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
     "status": "go", "users": 640, "repo": "shaymanor/researchviewer",
     "blurb": "Research paper exploration tool"},
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
TICKETS = [
    {"id": "GRD-0182", "proj": "guardrail", "area_id": "ideas_lab",
     "title": "TMLR camera-ready revisions", "pri": 0, "deadline_hours": 48,
     "effort_hours": 6, "life": "active", "agent": "idle", "source": "manual",
     "summary": "Address reviewer 2's ablation request and re-run the OOD detection sweep before Friday.",
     "body": "Reviewers accepted with minor revisions. R2 wants an ablation isolating the teacher-confidence threshold from the entropy gate, plus a table over 3 domain-shift severities. Re-run sweep on Gautschi (8×A100), regenerate Fig 4, update related work with the two ICLR'26 citations flagged by R1.",
     "report": "Ran threshold sweep τ∈{0.5,0.7,0.9} × severity {light,med,heavy}. Cosine-gated variant held +1.2 mIoU over entropy-only at heavy shift. Fig 4 + Table 3 regenerated.",
     "result": "Ablation confirms the teacher gate is the load-bearing component; camera-ready draft ready for your review.",
     "deps": [],
     "links": [
         {"kind": "github_issue", "label": "ideas-lab/guardrail #182", "url": "/issues/182"},
         {"kind": "file", "label": "reviews_r1_r2.pdf", "url": "attach"}]},

    {"id": "GHS-0311", "proj": "ghstats", "area_id": "side",
     "title": "500-rate breach on api container", "pri": 0, "deadline_hours": 0.5,
     "effort_hours": 1, "life": "active", "agent": "executing", "source": "alert",
     "summary": "Alert: gh-stats-api 500-rate > 5% for 11m on minipc. Auto-filed, Delphi dispatched.",
     "body": "Alertmanager fired traefik_5xx_ratio{project=ghstats} = 0.061 sustained 11m. Restart count on gh-stats-api jumped to 4 in the last hour. Recent deploy c7f2a1 touched the rate-limit middleware. Likely a null-deref on the new Redis path when the cache is cold.",
     "report": "Reproduced cold-cache null deref in rate-limit middleware. Added guard + fallback to in-memory bucket. CI green. PR opened, self-merge blocked pending green canary.",
     "result": "Fix identified and PR pushed; 500-rate down to 0.3% on canary. Awaiting your merge (full-autonomy would auto-merge on green).",
     "deps": [],
     "links": [
         {"kind": "github_pr", "label": "gh-stats#94 fix(rate-limit)", "url": "/pull/94"},
         {"kind": "github_issue", "label": "auto: alert GHS-0311", "url": "/issues/x"}]},

    {"id": "EVC-0074", "proj": "evc", "area_id": "evc",
     "title": "Fix motor sync on left rear", "pri": 1, "deadline_hours": 96,
     "effort_hours": 5, "life": "queued", "agent": "idle", "source": "slack",
     "summary": "Encoder counts drift ~3% between rear motors above 20 km/h; suspect CAN timing.",
     "body": "From #autonomy Slack: left-rear encoder desyncs from right-rear under load. Reproduces above 20 km/h. Hypothesis: CAN frame jitter on the VESC bus starves the sync loop. Check bus load %, confirm frame IDs aren't colliding with the IMU stream, consider raising sync-loop rate to 200Hz.",
     "report": None, "result": None,
     "deps": [{"id": "EVC-0071", "title": "CAN bus load profiling", "done": True}],
     "links": [{"kind": "slack_message", "label": "#autonomy · thread", "url": "slack"}]},

    {"id": "MER-0093", "proj": "merlin", "area_id": "ideas_lab",
     "title": "Port edge extractor to Rubik Pi 3", "pri": 1, "deadline_hours": 144,
     "effort_hours": 8, "life": "queued", "agent": "idle", "source": "github",
     "summary": "Cross-compile the metric edge stage for the Rubik Pi NPU and benchmark vs Orin Nano.",
     "body": "Move the edge-reconstruction stage off the Jetson Orin Nano onto the Rubik Pi 3 to free the Orin for the planner. Needs INT8 quantization of the extractor, a QNN delegate path, and a latency comparison at 640×480. Target < 22ms/frame.",
     "report": None, "result": None,
     "deps": [{"id": "MER-0088", "title": "INT8 quant of extractor", "done": False}],
     "links": [{"kind": "github_issue", "label": "ideas-lab/merlin #93", "url": "/issues/93"}]},

    {"id": "STA-0044", "proj": None, "area_id": "stat511",
     "title": "STAT 511 · Problem Set 4", "pri": 1, "deadline_hours": 72,
     "effort_hours": 4, "life": "queued", "agent": "idle", "source": "brightspace",
     "summary": "MLE, sufficient statistics, and a Fisher-information derivation. PDF pulled from Brightspace.",
     "body": "Brightspace: PS4 covers maximum likelihood estimation, sufficiency + the factorization theorem, and Cramér-Rao lower bound. 6 problems. Problem 5 asks for the Fisher information of a Gamma(α, β) with known β. Due 11:59pm.",
     "report": None, "result": None, "deps": [],
     "links": [
         {"kind": "brightspace", "label": "STAT 511 · PS4", "url": "bs"},
         {"kind": "file", "label": "ps4.pdf", "url": "attach"}]},

    {"id": "GHS-0308", "proj": "ghstats", "area_id": "side",
     "title": "SEO: programmatic profile pages", "pri": 2, "deadline_hours": 288,
     "effort_hours": 6, "life": "queued", "agent": "idle", "source": "manual",
     "summary": "Generate indexable per-user stat pages to break the traffic plateau.",
     "body": "User growth flat ~3.8k/wk. Hypothesis: no long-tail SEO surface. Generate static, cacheable /u/<handle> pages with OG images, sitemap, and schema.org markup. Measure index coverage in Search Console after 2 weeks.",
     "report": None, "result": None, "deps": [],
     "links": [{"kind": "github_issue", "label": "gh-stats #308", "url": "/issues/308"}]},

    {"id": "GPU-0021", "proj": "gpufindr", "area_id": "side",
     "title": "Stale prices on 2 providers", "pri": 2, "deadline_hours": 120,
     "effort_hours": 3, "life": "queued", "agent": "idle", "source": "alert",
     "summary": "Scraper for Lambda + RunPod returning cached data > 6h old; freshness caution.",
     "body": "Freshness monitor shows lambda + runpod feeds > 6h stale. Their markup changed; selectors likely broke. Re-derive selectors, add a freshness alert at 2h, backfill.",
     "report": None, "result": None, "deps": [],
     "links": [{"kind": "github_issue", "label": "gpufindr #21", "url": "/issues/21"}]},

    {"id": "MER-0088", "proj": "merlin", "area_id": "ideas_lab",
     "title": "INT8 quantization of extractor", "pri": 2, "deadline_hours": None,
     "effort_hours": 5, "life": "backburner", "agent": "idle", "source": "manual",
     "summary": "Post-training INT8 quant with a calibration set from the lab hallway captures.",
     "body": "Prereq for the Rubik Pi port. Build a 300-frame calibration set from hallway captures, run PTQ, verify edge-F1 stays within 2% of FP16.",
     "report": None, "result": None, "deps": [], "links": []},

    {"id": "RV-0012", "proj": "rviewer", "area_id": "side",
     "title": "Add citation-graph hover cards", "pri": 3, "deadline_hours": None,
     "effort_hours": 3, "life": "backburner", "agent": "idle", "source": "manual",
     "summary": "Show a mini citation neighborhood on hover over any paper node.",
     "body": "Low stakes, full autonomy. On hover over a paper, fetch its 5 most-cited neighbors from the Semantic Scholar API and render a small card. Nice-to-have.",
     "report": None, "result": None, "deps": [], "links": []},
]

# ---------------------------------------------------------------- hosts
# expectation: always_on | intermittent
HOSTS = [
    {"id": "minipc", "name": "minipc", "kind": "always_on", "icon": "Server",
     "tag": "ALWAYS-ON · local", "loc": "Purdue apt"},
    {"id": "gcp", "name": "GCP · Cloud Run", "kind": "intermittent", "icon": "Boxes",
     "tag": "SCALE-TO-ZERO · polled", "loc": "us-central1"},
    {"id": "jetson", "name": "Jetson Orin Nano", "kind": "intermittent", "icon": "Cpu",
     "tag": "INTERMITTENT · onboard", "loc": "EVC kart"},
    {"id": "rubikpi", "name": "Rubik Pi 3", "kind": "intermittent", "icon": "HardDrive",
     "tag": "INTERMITTENT · onboard", "loc": "EVC kart"},
]

# ---------------------------------------------------------------- containers
# A container belongs to exactly one project and runs on exactly one host.
# Runtime metrics are mocked current-values (real monitoring is out of scope).
CONTAINERS = [
    {"id": "gh-stats-api", "proj": "ghstats", "host": "minipc", "role": "api", "status": "flt",
     "cpu": "38%", "cpu_n": 38, "mem": "512M", "err": "6.1%", "rps": "142/s", "p95": "890 ms", "restarts": 4, "up": "AOS", "image": "ghstats/api:c7f2a1"},
    {"id": "gh-stats-web", "proj": "ghstats", "host": "minipc", "role": "web", "status": "go",
     "cpu": "4%", "cpu_n": 4, "mem": "96M", "err": "0.0%", "rps": "38/s", "p95": "64 ms", "restarts": 0, "up": "AOS", "image": "ghstats/web:1f9d0e"},
    {"id": "gpufindr-api", "proj": "gpufindr", "host": "minipc", "role": "api", "status": "cau",
     "cpu": "12%", "cpu_n": 12, "mem": "210M", "err": "0.4%", "rps": "22/s", "p95": "120 ms", "restarts": 1, "up": "AOS", "image": "gpufindr/api:8a41c2"},
    {"id": "gpufindr-scraper", "proj": "gpufindr", "host": "minipc", "role": "worker", "status": "cau",
     "cpu": "22%", "cpu_n": 22, "mem": "180M", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "AOS", "image": "gpufindr/scraper:8a41c2"},
    {"id": "gs-platform", "proj": "groundstation", "host": "minipc", "role": "api", "status": "go",
     "cpu": "9%", "cpu_n": 9, "mem": "340M", "err": "0.0%", "rps": "12/s", "p95": "48 ms", "restarts": 0, "up": "AOS", "image": "pantheos/platform:dev"},
    {"id": "rviewer", "proj": "rviewer", "host": "gcp", "role": "web", "status": "go",
     "cpu": "—", "cpu_n": 6, "mem": "—", "err": "0.1%", "rps": "3/s", "p95": "210 ms", "restarts": 0, "up": "AOS", "image": "gcr.io/rviewer:live"},
    {"id": "merlin-planner", "proj": "merlin", "host": "jetson", "role": "planner", "status": "los",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "LOS", "image": "merlin/planner:orin"},
    {"id": "merlin-edge", "proj": "merlin", "host": "jetson", "role": "perception", "status": "los",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "LOS", "image": "merlin/edge:orin"},
    {"id": "edge-npu", "proj": "merlin", "host": "rubikpi", "role": "perception", "status": "los",
     "cpu": "—", "cpu_n": 0, "mem": "—", "err": "—", "rps": "—", "p95": "—", "restarts": 0, "up": "LOS", "image": "merlin/edge:qnn"},
]

# ---------------------------------------------------------------- Delphi config
MCP_SERVERS = [
    {"id": "github", "name": "GitHub", "url": "api.github.com", "tools": "8", "on": True, "desc": "Issues, PRs, CI, commits"},
    {"id": "gcal", "name": "Google Calendar", "url": "calendarmcp.googleapis.com", "tools": "4", "on": True, "desc": "Events, free/busy, scheduling"},
    {"id": "gmail", "name": "Gmail", "url": "gmailmcp.googleapis.com", "tools": "5", "on": True, "desc": "Starred mail → tickets"},
    {"id": "brightspace", "name": "Brightspace", "url": "browser-agent · isolated", "tools": "3", "on": True, "desc": "Assignments + PDFs via browser session"},
    {"id": "metrics", "name": "VictoriaMetrics", "url": "vm.minipc.local", "tools": "2", "on": True, "desc": "PromQL over fleet telemetry"},
    {"id": "hf", "name": "Hugging Face", "url": "huggingface.co/mcp", "tools": "10", "on": False, "desc": "Models, datasets, spaces"},
    {"id": "exa", "name": "Exa", "url": "mcp.exa.ai", "tools": "2", "on": False, "desc": "Web search + fetch"},
]

SKILLS = [
    {"id": "enrich", "name": "enrich-ticket", "on": True, "trigger": "on create", "desc": "Read sources, write summary + problem statement"},
    {"id": "exec", "name": "launch-claude-code", "on": True, "trigger": "manual / CI", "desc": "Spawn headless session under project ceiling"},
    {"id": "rerank", "name": "re-rank-queue", "on": True, "trigger": "nightly", "desc": "Score importance × urgency, propagate deadlines"},
    {"id": "bs", "name": "brightspace-pull", "on": True, "trigger": "hourly", "desc": "New assignments → enriched tickets"},
    {"id": "digest", "name": "weekly-digest", "on": False, "trigger": "Sun 6pm", "desc": "Summarize the week, flag slipping deadlines"},
]

MEMORY_FACTS = [
    "Prefers terse, technically precise replies",
    "EVC → PR-only, never touch main",
    "Does exams in one sitting — block the full window",
    "Guardrail + MERLIN under active submission; results integrity matters",
]

AGENT_RUNS = [
    {"ticket": "GHS-0311", "kind": "execute", "status": "needs review", "cost": "$0.42", "when": "12m ago"},
    {"ticket": "GRD-0182", "kind": "enrich", "status": "done", "cost": "$0.03", "when": "1h ago"},
    {"ticket": "STA-0044", "kind": "enrich", "status": "done", "cost": "$0.05", "when": "3h ago"},
    {"ticket": "EVC-0074", "kind": "enrich", "status": "done", "cost": "$0.04", "when": "5h ago"},
]

MODELS = [
    # id = the model string sent to the OpenAI-compatible API (chosen in the UI).
    {"id": "gpt-5.6-terra", "name": "GPT Terra", "tag": "openai · gpt-5.6"},
    {"id": "gpt-5.6-luna", "name": "GPT Luna", "tag": "openai · gpt-5.6"},
    {"id": "gpt-5.6-sol", "name": "GPT Sol", "tag": "openai · gpt-5.6"},
]

SESSIONS = [
    {"id": "s1", "title": "EKF drift on the kart", "ts": "Yesterday", "msgs": [
        {"who": "me", "text": "Why is the EKF drifting on the EVC kart?"},
        {"who": "flight", "text": "The GEM1305 RTK fix was dropping to float during the sweep. I correlated the covariance spikes with EVC-0071 — CAN bus load hitting 82%. Raising the IMU publish rate to 200Hz and re-timing the fusion loop settled it.", "tools": ["queue", "vm"]},
    ]},
    {"id": "s2", "title": "Guardrail rebuttal plan", "ts": "2d ago", "msgs": [
        {"who": "me", "text": "Draft a plan for the Guardrail rebuttal"},
        {"who": "flight", "text": "R2's ablation is the crux. I outlined a 3-point response and staged the sweep under GRD-0182. The teacher-gate isolation is the strongest evidence — cosine-gated held +1.2 mIoU at heavy shift.", "tools": ["brightspace", "queue"]},
    ]},
    {"id": "s3", "title": "gh-stats SEO ideas", "ts": "Mar 3", "msgs": [
        {"who": "me", "text": "How do I break the gh-stats traffic plateau?"},
        {"who": "flight", "text": "Programmatic per-profile pages are the highest-leverage move — indexable long-tail surface you don't have yet. Filed as GHS-0308 with OG images + schema.org markup.", "tools": ["github", "vm"]},
    ]},
]

GREETING = ("Delphi online. Two things want your attention: GRD-0182 (TMLR) is due in 2 days, "
            "and my fix for the gh-stats 500-rate breach is in a PR waiting on your merge.")
