---
name: triage-ticket
trigger: on new ticket
description: Enrich and route an incoming ticket so it is ready to execute.
---

# Triage Ticket

## Overview

A raw ticket arrived. Turn it into something executable: grounded summary, clear
problem statement, correct priority, real dependencies — using the tools.

**Core principle:** Enrich from sources and the project spec, not from assumption.

## The Iron Law

```
NO PRIORITY OR ROUTING WITHOUT READING THE TICKET AND ITS PROJECT SPEC.
```

## Phase 1 — Ground

1. `get_ticket(id)` — read title, body, source, existing links/deps.
2. If it names a project, `get_project_spec(project_key)` for conventions and the
   autonomy ceiling. If it doesn't, infer the area from `list_areas()` /
   `list_projects()` and pick the best fit; state your reasoning.

## Phase 2 — Enrich

- Write a crisp one-line `summary` and a problem statement in `body`: what is
  wrong, where, and what "done" means. Ground every claim — cite a log line
  (`get_container_logs`) or a spec section, never a guess.
- Set importance honestly with `pri` (0 = drop-everything … 3 = someday) and a
  realistic `effort_hours` / `deadline_hours` so scoring is meaningful.

## Phase 3 — Link and route

- `add_dep(id, dep_id, title)` for anything that must land first (find blockers
  with `list_tickets`).
- `add_ticket_link(id, kind, label, url)` for the PR/issue/doc it relates to.
- Apply the enrichment with a single `update_ticket(id, summary=..., body=...,
  pri=..., deadline_hours=..., effort_hours=...)`.
- Move it into the queue: `move_ticket(id, "queued")` and
  `set_agent_state(id, "idle")` (or `"enriching"` while you work).

## Phase 4 — Handoff

- If it's ready to execute and autonomy allows, note that the next step is
  `run_claude_code`. If autonomy is `propose`, say so — a human gates the launch.

## Red Flags — STOP

- Setting `pri=0` because the reporter sounded urgent — verify against the spec.
- Writing a summary you can't tie to a source.
- Routing to a project you never called `get_project_spec` on.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "The title says it all" | Titles lie. Read the body and the spec. |
| "I'll estimate effort later" | No estimate = no score = wrong queue order. |
| "Any project will do" | Wrong routing wastes a whole enrich+execute cycle. |
