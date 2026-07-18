"""Deterministic, ticket-scoped agent run for the mocked Launch Delphi flow.

Yields the same normalized event vocabulary as app.acp_mock (reasoning / tool /
text / done) but tailored to a specific ticket. A pure function of its inputs —
no randomness, no wall-clock — so the 20x E2E gate stays green.
"""

# Keyword family -> (tool keys, a short action phrase). Tool keys must exist in
# the frontend TOOLMAP so the chips render.
_ROUTES = [
    (("test", "flaky", "ci"), ["claude", "github"],
     "reproduced the failing test and traced the root cause"),
    (("deploy", "release", "ship", "rollout"), ["claude", "github", "queue"],
     "prepared the rollout and checked the pipeline"),
    (("metric", "alert", "latency", "error", "rate", "breach"), ["vm", "claude", "github"],
     "queried metrics and isolated the regression"),
    (("doc", "readme", "revision", "camera"), ["claude", "github"],
     "drafted the revisions and updated the docs"),
]
_DEFAULT = (["claude", "github"], "investigated the ticket and implemented a fix")


def _route(title):
    low = (title or "").lower()
    for keys, tools, action in _ROUTES:
        if any(k in low for k in keys):
            return tools, action
    return _DEFAULT


def _chunks(s, n=24):
    return [s[i:i + n] for i in range(0, len(s), n)] or [""]


def run_ticket(tid, title, area, autonomy):
    tools, action = _route(title)

    reasoning = (
        f"Picking up {tid} — '{title}' in {area}. "
        f"Plan: read the relevant code, {action}, then verify and prepare a PR."
    )

    if autonomy == "full":
        landing = "Opened and merged the PR; the change is live."
        result = f"Shipped a fix for {tid}."
    elif autonomy == "auto_pr":
        landing = "Opened a PR with auto-merge armed once checks pass."
        result = f"PR opened for {tid}, auto-merge armed."
    else:  # propose / unknown -> stop for review
        landing = "Opened a pull request and stopped for your review."
        result = f"Fix ready for {tid}; PR awaiting review."

    output = (
        f"**Run summary for {tid}**\n\n"
        f"I {action}. {landing}\n\n"
        "```diff\n- # before\n+ # after (patched)\n```"
    )
    report = f"Delphi {action}. {landing}"
    cost = "$0.04"

    yield {"type": "reasoning", "delta": reasoning}
    for i, name in enumerate(tools):
        yield {"type": "tool", "id": f"t{i}", "name": name,
               "status": "done", "title": name}
    for c in _chunks(output):
        yield {"type": "text", "delta": c}
    yield {"type": "done", "text": output, "reasoning": reasoning, "tools": tools,
           "result": result, "report": report, "cost": cost}
