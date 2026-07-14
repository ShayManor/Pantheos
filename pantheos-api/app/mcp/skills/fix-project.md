---
name: fix-project
trigger: manual / project cau|flt
description: Bring a degraded project back to green, within its autonomy ceiling.
---

# Fix Project

## Overview

A project is `cau` (caution) or `flt` (fault). Your job is to return it to `go`
using the MCP tools, never exceeding what the project's autonomy allows.

**Core principle:** The project spec is the contract. Read it first; obey it.

## The Iron Law

```
READ get_project_spec BEFORE TOUCHING ANYTHING. NEVER EXCEED THE AUTONOMY CEILING.
```

`propose` → branch + PR only, hard-stop at `needs_review`.
`auto_pr` → commit + PR, self-merge only on green CI.
`full` → commit to main.

## Phase 1 — Ground

1. `get_project_spec(project_key)` — name, repo, autonomy, conventions.
2. `get_project(project_key)` — current `status` and blurb.
3. `list_containers(project=project_key)` — which service is degraded.

## Phase 2 — Diagnose

- For each non-`go` container, follow the **debug-issue** skill: read
  `get_container_logs(id)`, form one hypothesis.
- Check open work: `list_tickets(project=project_key, life="blocked")` and
  `list_tickets(project=project_key, agent="needs_review")`.

## Phase 3 — Act within the ceiling

- Operational fix → `restart_container(id)`.
- Code fix → `run_claude_code(project_key, task, dry_run=<autonomy=='propose'>)`.
  - `propose`: the tool returns a **plan**. Create/annotate a ticket and set
    `set_agent_state(ticket_id, "needs_review")`. Do not claim it shipped.
  - `auto_pr` / `full`: the tool executes. Read `exit_code`/`stderr`.
- If no ticket tracks this work, open one: `create_ticket(title=..., project_key=...,
  pri=1, summary=..., body=...)`.

## Phase 4 — Verify

- Re-check `get_project`/`list_containers` — is it `go`?
- Record the outcome: `update_ticket(id, result=...)` and, if durable,
  `add_memory_fact(...)`.
- Never report "fixed" without a tool result confirming it.

## Red Flags — STOP

- Editing anything before reading the spec.
- Running `run_claude_code` in `full` mode on a `propose` project.
- Reporting success from intent rather than from a container/status re-check.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "Autonomy is just a label" | It is a hard ceiling. Propose means PR-only. |
| "I'll skip the spec, it's a small fix" | Small fixes break conventions too. |
| "It should be fine now" | Re-read the status. "Should" is not evidence. |
