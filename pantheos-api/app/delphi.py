"""Delphi's fallback conversational reply.

The real agent runtime (Hermes over ACP) handles live chat; this is the
deterministic stand-in used by the mock backend and tests.
"""

_DEFAULT = (
    "I can pull ticket status, project health, run history, or metrics — or launch on "
    "any ticket. Try a suggestion, attach a file, or dictate.",
    [],
)


def reply(text):
    return {"text": _DEFAULT[0], "tools": _DEFAULT[1]}


# --------------------------------------------------------------- ticket drafts
# Delphi "enriches" a half-filled ticket into a full one: it scopes the given
# title and keeps the project/area the user already picked. Deterministic (no
# random / clock) so the E2E gate stays green.
def draft_ticket(context):
    """Return a full ticket-field draft from whatever the user has filled in.

    ``context`` may carry any of ``title``, ``summary``, ``pri``, ``effort_hours``,
    ``deadline_hours``, ``project_key``, ``area_id``. Delphi scopes the given
    title and keeps the project/area the user already picked.
    """
    context = context or {}
    title = (context.get("title") or "").strip()
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
