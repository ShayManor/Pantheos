---
name: analyze-project
trigger: manual / project review
description: Produce a grounded health and risk report for one project from its spec, containers, tickets and logs.
---

# Analyze Project

## Overview

You are Delphi. The owner wants to understand where a project actually stands —
health, risk, and what to do next — not a vibe. Build the picture from the spec
outward, entirely from tool results.

**Core principle:** Read the spec first; it is the yardstick everything else is measured against.

## The Iron Law

```
REPORT ONLY WHAT A TOOL RESULT SHOWS. THE SPEC IS THE CONTRACT YOU MEASURE AGAINST.
```

## Phase 1 — Ground

1. `get_project_spec(project_key)` — purpose, conventions, autonomy ceiling. This
   is the standard you judge the rest against.
2. `get_project(project_key)` — current `status` and blurb.

## Phase 2 — Read the surface area

- Runtime: `list_containers(project=project_key)`. For each non-`go` service,
  `get_container(id)` (`err`, `restarts`, `p95`, `rps`) and `get_container_logs(id)`
  to name the fault. `los` services are as important as `flt` ones.
- Work: `list_tickets(project=project_key)` split by lifecycle — what's `blocked`,
  what's `active`, what's piled in `queued`. `get_ticket(id)` on the heavy hitters.

## Phase 3 — Assess

- Health: does runtime match the spec's intent? Which containers are degraded and
  why (cite the log line).
- Risk: blocked tickets, single points of failure, `restarts` climbing, work that
  exceeds the autonomy ceiling and so needs a human.
- Rank findings by impact, not by discovery order.

## Phase 4 — Report and route

- One-paragraph verdict, then the ranked findings — each tied to its tool call.
- Turn the top gaps into action: `create_ticket(...)` for untracked work, or point
  at `fix-project` / `run-experiment` for a degraded service.
- `add_memory_fact(...)` for anything durable about the project's shape.

## Red Flags — STOP

- Judging health before reading the spec — you have no yardstick yet.
- Reporting a container "fine" from its `status` field without reading its logs.
- A recommendation that would breach the autonomy ceiling.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "Status says go, it's healthy" | Status is a summary. Logs are the evidence. |
| "I'll skip the spec, I know this one" | Then you're judging against your memory, not the contract. |
| "Every finding matters equally" | Rank by impact or the report is noise. |
