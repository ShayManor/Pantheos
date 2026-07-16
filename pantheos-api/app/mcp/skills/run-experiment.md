---
name: run-experiment
trigger: manual / perf regression
description: Test one hypothesis with a single controlled change, measure before and after, then keep or revert.
---

# Run Experiment

## Overview

You are Delphi, acting as a scientist. A metric moved (p95 up, err rate up, rps
down) and you have an idea why. Don't ship the idea — test it. One variable, a
measured baseline, an honest verdict.

**Core principle:** Change one thing, measure it, and let the numbers decide — not your prior.

## The Iron Law

```
ONE VARIABLE PER EXPERIMENT. RECORD THE BASELINE BEFORE YOU TOUCH ANYTHING.
```

## Phase 1 — Hypothesis

- State it falsifiably in one sentence: "restarting `X` clears the p95 spike
  because the worker is wedged (log line Y)." If you can't say what result would
  prove it *wrong*, it isn't a hypothesis yet.
- Ground it: `get_project_spec(project_key)` for the ceiling, `get_container_logs`
  for the evidence that motivated it.

## Phase 2 — Baseline

- Record the numbers you expect to move, before changing anything:
  `get_container(id)` → note `p95`, `err`, `rps`, `restarts`. Write them down; they
  are the comparison point. No baseline = no experiment.

## Phase 3 — One change

- Make exactly one intervention:
  - operational: `restart_container(id)`.
  - code: `run_claude_code(project_key, task, dry_run=<autonomy=='propose'>)` with a
    task that changes one thing. Respect the ceiling — a `propose` project returns a
    plan to review, not a shipped change.
- Do not bundle a second "while I'm here" tweak — it destroys the measurement.

## Phase 4 — Measure and decide

- Re-read `get_container(id)` / `get_container_logs(id)`. Compare to the baseline.
- Verdict: confirmed (kept, `update_ticket(id, result=...)`), refuted (revert or
  open a ticket for the real cause), or inconclusive (state why, plan the next
  single variable).
- `add_memory_fact(...)` with the result — a refuted hypothesis is worth recording
  so it isn't retried.

## Red Flags — STOP

- Changing two things so you can't tell which one worked.
- Declaring success from the change you made, not from a re-measured metric.
- No baseline — then "better" is just a feeling.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll fix both while I'm in here" | Two variables, zero signal. One change. |
| "It's obviously better now" | Re-measure. "Obviously" is not a number. |
| "The hypothesis was wrong, delete it" | Record the refutation so no one retries it. |
