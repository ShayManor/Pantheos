"""Delphi's canned conversational replies.

The real agent runtime is out of scope; this keyword-routes a question to a
fixed answer + the tools it "used", mirroring the prototype's reply().
"""

_ROUTES = [
    (("due", "friday", "week"),
     "This week: GRD-0182 TMLR revisions (2d, P0), STA-0044 STAT 511 PS4 (3d, P1), "
     "EVC-0074 motor sync (4d, P1). The TMLR one is the only P0 with real slack risk — "
     "6h of work, 2 days out. I'd start it today.",
     ["calendar", "brightspace", "queue"]),
    (("merlin", "rubik"),
     "MERLIN is nominal. 2 open tickets: MER-0093 (Rubik Pi port), blocked-ish on "
     "MER-0088 (INT8 quant, backburner). Both onboard containers are LOS — the Jetson's "
     "been off ~3h, expected, not an incident.",
     ["queue", "vm"]),
    (("gh-stats", "500", "canary"),
     "Alert at t-11m: 5XX hit 6.1% on gh-stats-api. I traced a cold-cache null-deref in "
     "the rate-limit middleware, added a guard + fallback, and opened the fix under "
     "GHS-0311. Canary 5XX back to 0.3%, waiting on your merge.",
     ["vm", "github", "claude"]),
    (("rank", "queue"),
     "Re-ranked. Top: GHS-0311 (9.1, executing), GRD-0182 (9.4), EVC-0074 (6.8), "
     "STA-0044 (6.1). Nothing else moved.",
     ["queue"]),
]

_DEFAULT = (
    "I can pull ticket status, project health, run history, or metrics — or launch on "
    "any ticket. Try a suggestion, attach a file, or dictate.",
    [],
)


def reply(text):
    lower = (text or "").lower()
    for keywords, answer, tools in _ROUTES:
        if any(k in lower for k in keywords):
            return {"text": answer, "tools": tools}
    return {"text": _DEFAULT[0], "tools": _DEFAULT[1]}


# --------------------------------------------------------------- ticket drafts
# Delphi "enriches" a half-filled ticket into a full one. Keyword-routed and
# deterministic (no random / clock) so the E2E gate stays green. Each route is a
# complete field draft matching the New-ticket modal's payload keys.
_DRAFT_ROUTES = [
    (("merlin", "rubik", "jetson", "inference"),
     {"title": "Port MERLIN inference to Rubik Pi",
      "summary": "Cross-compile the runtime and validate INT8 parity on the Rubik Pi 5.",
      "pri": 1, "effort_hours": 8, "deadline_hours": 168, "project_key": "merlin"}),
    (("gh-stats", "ghstats", "canary", "5xx", "rate-limit", "middleware"),
     {"title": "Harden gh-stats rate-limit middleware",
      "summary": "Add the cold-cache null guard + fallback and roll the canary to 100%.",
      "pri": 0, "effort_hours": 3, "deadline_hours": 72, "project_key": "ghstats"}),
    (("tmlr", "grad", "guardrail", "revision", "camera", "paper"),
     {"title": "TMLR camera-ready revisions",
      "summary": "Address reviewer comments and submit the Guardrail camera-ready.",
      "pri": 0, "effort_hours": 6, "deadline_hours": 72, "project_key": "guardrail"}),
    (("evc", "motor", "can bus", "can-bus", "sync"),
     {"title": "EVC motor-sync integration",
      "summary": "Wire the CAN-bus motor-sync loop into the autonomy stack and bench-test it.",
      "pri": 1, "effort_hours": 4, "deadline_hours": 168, "project_key": "evc"}),
    (("stat", "511", "homework", "problem set", "ps4", "pset"),
     {"title": "STAT 511 problem set",
      "summary": "Work the current STAT 511 problem set and write up the solutions.",
      "pri": 1, "effort_hours": 3, "deadline_hours": 72, "area_id": "stat511"}),
]


def draft_ticket(context):
    """Return a full ticket-field draft from whatever the user has filled in.

    ``context`` may carry any of ``title``, ``summary``, ``pri``, ``effort_hours``,
    ``deadline_hours``, ``project_key``, ``area_id``. A keyword match on the
    title+summary yields a canned draft; otherwise Delphi scopes the given title
    and keeps the project/area the user already picked.
    """
    context = context or {}
    title = (context.get("title") or "").strip()
    lower = f"{title} {context.get('summary') or ''}".lower()
    for keywords, draft in _DRAFT_ROUTES:
        if any(k in lower for k in keywords):
            return dict(draft)
    draft = {
        "title": title or "New ticket",
        "summary": f"Scope and complete: {title}" if title else "Scope and complete this ticket.",
        "pri": 1, "effort_hours": 4, "deadline_hours": 72,
    }
    if context.get("project_key"):
        draft["project_key"] = context["project_key"]
    elif context.get("area_id"):
        draft["area_id"] = context["area_id"]
    return draft
