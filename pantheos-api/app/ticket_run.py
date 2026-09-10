"""Ticket-scoped agent run behind the Launch Delphi button.

Yields the same normalized event vocabulary as app.acp_mock (reasoning / tool /
text / done) but tailored to a specific ticket. DELPHI_ACP_MODE picks the
backend, mirroring app.acp: 'mock' (default) replays a deterministic canned run,
a pure function of its inputs with no randomness or wall-clock, so the 20x E2E
gate stays green; any other mode drives the real agent through app.acp.run_turn.
"""
import os
import re

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


def _run_mock(tid, title, area, autonomy):
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


def run_ticket(tid, title, area, autonomy, ctx=None):
    """Dispatch one ticket run to the backend named by DELPHI_ACP_MODE."""
    if os.environ.get("DELPHI_ACP_MODE", "mock") == "mock":
        yield from _run_mock(tid, title, area, autonomy)
    else:
        yield from _run_real(tid, title, area, autonomy, ctx or {})


def _run_real(tid, title, area, autonomy, ctx):
    """Drive the real agent for one ticket, then close the normalized `done`.

    app.acp.run_turn reports what the agent said (text / reasoning / tools); the
    ticket columns it does not carry (result, report, cost) are derived from that
    output here, never templated from the ticket, so a run can only claim what
    the agent actually reported.
    """
    from . import acp                      # imported lazily, mirroring app.acp

    prompt = _prompt(tid, title, area, autonomy, ctx)
    # The ceiling is a real gate, not just prompt text. It fails closed: only an
    # explicit auto_pr/full ceiling auto-approves a tool call, so propose — and a
    # ticket with no project, which declares no ceiling at all — does not.
    for ev in acp.run_turn(prompt, None,
                           auto_approve=autonomy in ("auto_pr", "full")):
        if ev["type"] == "done":
            text = ev.get("text") or ""
            result, report = _summarize(text)
            yield {**ev, "result": result, "report": report, "cost": "—"}
        else:
            yield ev


def _prompt(tid, title, area, autonomy, ctx):
    """Ground the turn the way mcp.tools.run_claude_code does: project spec first,
    autonomy ceiling as a hard gate, then the ticket."""
    name, key = ctx.get("project_name"), ctx.get("project_key")
    where = f"project {name} ({key}), area {area}" if name else f"area {area}"
    lines = [f"You are Delphi working ticket {tid} in {where}.", ""]
    if ctx.get("project_context"):
        lines += ["Read and obey this project spec before acting:",
                  ctx["project_context"], ""]
    lines += [f"Autonomy ceiling: {autonomy}",
              "(propose = plan and PR only, stop for review; auto_pr = PR plus "
              "green-CI self-merge; full = may commit to main.)", "",
              f"Ticket: {title}"]
    lines += [v for v in (ctx.get("summary"), ctx.get("body")) if v]
    lines += ["", "Work the ticket. Close with one line starting 'RESULT:' stating "
              "what actually changed, then one paragraph starting 'REPORT:'."]
    return "\n".join(lines)


# RESULT is the one-line banner; REPORT runs to the end of the turn (DOTALL) so a
# wrapped closing paragraph survives intact.
_RESULT = re.compile(r"^[ \t]*RESULT[ \t]*:[ \t]*(.*)", re.MULTILINE)
_REPORT = re.compile(r"^[ \t]*REPORT[ \t]*:[ \t]*(.*)", re.MULTILINE | re.DOTALL)


def _summarize(text):
    """Pull (result, report) out of the agent's own closing markers.

    Falls back to the first line and first paragraph when the agent skipped them,
    so the UI shows real output rather than an invented success line.
    """
    result = _RESULT.search(text)
    report = _REPORT.search(text)
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    first_para = paras[0] if paras else ""
    return (result.group(1).strip() if result else first_para.split("\n")[0].strip(),
            report.group(1).strip() if report else first_para)
