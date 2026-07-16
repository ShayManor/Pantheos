---
name: dispatch-agents
trigger: manual / batch work
description: Fan independent code work across projects into parallel Claude Code runs, each within its own ceiling.
---

# Dispatch Agents

## Overview

You are Delphi. Several pieces of work are ready and independent — different
projects, or unrelated tickets in one project. Running them one at a time wastes
wall-clock. Dispatch them in parallel through `run_claude_code`, one worker per
unit, each gated by its own project's autonomy.

**Core principle:** Parallelize only what is genuinely independent. Shared state is a serializer.

## The Iron Law

```
EACH RUN IS GATED BY ITS OWN PROJECT'S AUTONOMY. NEVER DISPATCH DEPENDENT WORK IN PARALLEL.
```

## Phase 1 — Partition

- List the candidate work: `list_tickets(life="queued")` or the tickets the owner
  named. Read each with `get_ticket(id)`.
- Split into units that touch **disjoint** projects/files with no ordering between
  them. If A must land before B (`add_dep` / a blocker), they are one serial chain,
  not two parallel units — do not split them.

## Phase 2 — Ground each unit

- For every unit's project, `get_project_spec(project_key)` — read its autonomy
  ceiling and conventions. Ceilings differ per project; a full-autonomy dispatch on
  a `propose` project is the classic mistake.
- Make sure a ticket tracks each unit; if not, `create_ticket(...)`.

## Phase 3 — Dispatch

- For each unit, `run_claude_code(project_key, task, dry_run=<autonomy=='propose'>)`
  with a precise, self-contained task string (the worker shares no context with the
  others). `set_agent_state(id, "executing")`.
- Keep the fan-out to genuinely independent units — a large batch of unrelated,
  well-scoped tasks is the sweet spot.

## Phase 4 — Collect

- Read every result: `exit_code` / `stderr`, or the returned plan for `propose`.
- Per unit: `set_agent_state(id, "needs_review")` for `propose` plans;
  `update_ticket(id, result=...)` when it shipped. Report per-unit outcomes — one
  failure does not fail the batch.

## Red Flags — STOP

- Dispatching two units that touch the same service or where one blocks the other.
- One `task` string that assumes another worker's output — they run blind to each
  other.
- Applying one project's autonomy to every unit in the batch.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "They're all basically the same task" | Same ceiling? Read each spec and confirm. |
| "This one depends a little on that one" | "A little" dependent = serial. Chain them. |
| "One failed, call the batch failed" | Report per unit; the rest may have shipped. |
