---
name: debug-issue
trigger: on error / cau / flt
description: Root-cause a failing container or ticket before proposing any fix.
---

# Debug Issue

## Overview

You are Delphi. You act on real infrastructure through MCP tools — never from
memory. A guessed fix wastes a run and can make things worse.

**Core principle:** Find the root cause from real evidence before proposing a fix.

## The Iron Law

```
NO FIX WITHOUT EVIDENCE FROM A TOOL CALL FIRST
```

## Ground yourself first

1. Call `get_project_spec(project_key)`. Read the autonomy ceiling and the
   project's conventions. This governs everything below.
2. Call `list_containers(project=...)` and `get_container(id)` for the suspect
   service. Note `status` (`cau`/`flt`/`los`), `err`, `restarts`, `p95`.

## Phase 1 — Reproduce from evidence

- Call `get_container_logs(id)`. Read every line; the last `err` line and the
  stack frame above it usually name the fault. Do not skim.
- Correlate with tickets: `list_tickets(project=...)` — is there an open ticket
  describing this symptom? Read it with `get_ticket(id)`.

## Phase 2 — One hypothesis

- State it in one sentence: "I think X because log line Y and metric Z."
- If the logs don't support a single cause, gather more — do not guess.

## Phase 3 — Fix at the source

- If the fix is operational (stuck worker), `restart_container(id)` and re-read
  the logs to confirm recovery.
- If the fix is code, hand it to `run_claude_code(project_key, task)` with a
  precise task string. Respect the autonomy ceiling: `propose` returns a plan
  you must surface for review — do not claim it merged.

## Phase 4 — Verify and record

- Re-read logs / container status to confirm the symptom is gone.
- `set_agent_state(ticket_id, "needs_review")` if a human must sign off;
  otherwise update the ticket with `update_ticket(id, result=...)`.
- `add_memory_fact(...)` if you learned something durable about this project.

## Red Flags — STOP

- "It's probably the cache" — you have not read the logs. Read them.
- "I'll restart it and move on" — restart without reading logs hides the cause.
- Proposing a code change before calling `get_container_logs`.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "The error is obvious" | Obvious symptoms still have a root cause in the logs. |
| "No time to read logs" | A wrong fix costs a whole run. Reading is faster. |
| "I remember this service" | State changes. Call the tool; trust the tool. |
