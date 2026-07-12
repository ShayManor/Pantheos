"""Derived priority scoring — spec section 1.5.

Pure functions, no I/O. Deadlines are expressed as ``deadline_hours`` (hours
from the seed anchor) so scoring is deterministic and independent of wall-clock
time — the seeded values never drift between test runs.
"""

# weight(importance): P0=8, P1=4, P2=2, P3=1
_WEIGHT = {0: 8, 1: 4, 2: 2, 3: 1}


def weight(importance):
    return _WEIGHT.get(importance, 1)


def own_urgency(deadline_hours, effort_hours):
    """1 / (1 + max(slack,0)/24); no deadline → 0.3 baseline."""
    if deadline_hours is None:
        return 0.3
    slack = deadline_hours - (effort_hours or 0)
    return 1.0 / (1.0 + max(slack, 0) / 24.0)


def inherited_urgency(own, dependent_urgencies):
    """Deadline pressure flows upstream: max(own, 0.8 * max(dependents))."""
    best_dep = max(dependent_urgencies, default=0.0)
    return max(own, 0.8 * best_dep)


def compute_score(importance, inherited):
    return weight(importance) * (0.3 + 0.7 * inherited)


def due_display(deadline_hours):
    """Relative deadline label: None → no deadline, <12h → 'now', else 'in Nd'."""
    if deadline_hours is None:
        return None
    if deadline_hours < 12:
        return "now"
    days = round(deadline_hours / 24)
    return f"in {days}d"


def is_hot(deadline_hours):
    """A deadline within ~2 days is hot."""
    return deadline_hours is not None and deadline_hours <= 50


def format_score(score):
    """One-decimal display string, matching the prototype ('9.4')."""
    return f"{score:.1f}"


def score_tickets(rows):
    """Score a list of ticket rows, propagating urgency upstream through deps.

    Each row: {id, pri, deadline_hours, effort_hours, dep_ids:[...]}.
    Returns {id: score_float}.
    """
    own = {r["id"]: own_urgency(r["deadline_hours"], r["effort_hours"]) for r in rows}

    # dependents[x] = urgencies of tickets that depend on x
    dependents = {r["id"]: [] for r in rows}
    for r in rows:
        for dep_id in r.get("dep_ids", []):
            if dep_id in dependents:
                dependents[dep_id].append(own[r["id"]])

    scores = {}
    for r in rows:
        inh = inherited_urgency(own[r["id"]], dependents[r["id"]])
        scores[r["id"]] = compute_score(r["pri"], inh)
    return scores
