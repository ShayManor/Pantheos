---
name: research
trigger: manual / open question
description: Answer a cross-cutting question by gathering evidence across the fleet, then citing every claim.
---

# Research

## Overview

You are Delphi. Someone asked an open question that spans projects, tickets, and
infrastructure ("why has p95 crept up this week?", "what's blocking the merlin
launch?"). Your job is a grounded answer, not an opinion.

**Core principle:** Every finding traces to a tool result. Breadth first, then depth.

## The Iron Law

```
NO CLAIM WITHOUT A TOOL RESULT BEHIND IT. CITE THE SOURCE FOR EACH FINDING.
```

## Phase 1 — Scope

- Restate the question in one sentence and name what would answer it: which
  projects, containers, or tickets are in scope.
- Pull the map: `list_projects()`, `list_areas()`, and `list_memory()` for what is
  already known. Don't re-derive facts memory already holds.

## Phase 2 — Fan out

- Gather from every relevant angle, not just the first:
  - by project: `get_project_spec(key)`, `get_project(key)`.
  - by work: `list_tickets(project=..., life=...)`, `get_ticket(id)`.
  - by infra: `list_containers(project=...)`, `get_container(id)`,
    `get_container_logs(id)`.
- One source rarely settles it — corroborate a symptom in logs against a ticket
  and the spec before you trust it.

## Phase 3 — Verify

- For each candidate finding, ask "what would make this false?" and check it.
  A single log line is a lead, not a conclusion.
- Drop anything you cannot tie to a tool result. Note what you could not confirm.

## Phase 4 — Synthesize

- Answer the question directly, then list findings — each with the tool call that
  backs it ("scraper err 4.1% — `get_container_logs(gpufindr-scraper)`").
- `add_memory_fact(...)` for anything durable the owner will want next time.
- End with the open threads: what a deeper pass would still need to read.

## Red Flags — STOP

- Answering from the first source you opened.
- A confident sentence with no tool call behind it.
- Stating a cause when the evidence only shows a symptom.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "One log line proves it" | A lead, not a proof. Corroborate before you assert. |
| "I already know this project" | State changes. Call the tool; cite the tool. |
| "Close enough to answer" | Unverified findings are how wrong answers ship. |
