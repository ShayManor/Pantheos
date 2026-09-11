"""Ticket-scoped agent run behind the Launch Delphi button.

Yields the same normalized event vocabulary as app.acp_mock (reasoning / tool /
text / done) but tailored to a specific ticket. DELPHI_ACP_MODE picks the
backend, mirroring app.acp: 'mock' (default) replays a deterministic canned run,
a pure function of its inputs with no randomness or wall-clock, so the 20x E2E
gate stays green; any other mode drives the real agent through app.acp.run_turn.
"""
import os
import re
import shlex
import subprocess

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

    prompt = _prompt(tid, title, area, autonomy, {**ctx, "runtime": _runtime(ctx)})
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


# What each ceiling permits, in operational terms. A run stalled on "am I allowed
# to commit to main?" because the old gloss named the permission without naming
# its consequence. Unknown/None falls back to the most restrictive entry, the
# same way the auto_approve gate in _run_real fails closed.
_CEILINGS = {
    "propose": "Plan and open a PR only, then stop for review. Do not push to main.",
    "auto_pr": "Open a PR and self-merge it once CI is green. Do not push to main "
               "directly.",
    "full": "You may commit straight to main. On a deployed project a push to main "
            "triggers a production deploy, so treat every push as a deploy.",
}
_NEVER = ("Never force-push, rewrite history, read or relocate secrets, drop or "
          "truncate data, or delete a container or volume.")

# Ticket source -> the skill that already describes how to work it. The skills
# are good and nothing routed to them, so a monitor ticket arrived with no method.
_SKILLS = {"monitor": "debug-issue", "alert": "debug-issue"}

_PROBE = (
    "for b in git gh claude docker psql; do command -v $b >/dev/null 2>&1 "
    "&& printf '%s ' \"$b\"; done; echo '<- on PATH'; "
    # `gh auth status` exits 0 on a dead token, so read what it prints rather
    # than what it returns. A credential wrongly called good is worse than no
    # answer: the run plans around a push it cannot make.
    "if command -v gh >/dev/null 2>&1; then case \"$(gh auth status 2>&1)\" in "
    "*'Failed to log in'*|*'not logged in'*|*invalid*) "
    "echo 'gh auth: INVALID (cannot clone, push or open a PR)';; "
    "*) echo 'gh auth: ok';; esac; "
    "else echo 'gh auth: no gh binary'; fi; "
    # Uptime separates a container recreated by a deploy from one in a crash
    # loop. Both show a raised restart count; only one is the fault.
    "if command -v docker >/dev/null 2>&1; then echo 'containers:'; "
    "docker ps --format '{{.Names}}  {{.Status}}' 2>/dev/null | head -40; fi")


def _ssh_argv():
    """The ssh argv app.acp_client uses, minus its remote command.

    Reusing the configured transport puts the probe on the same flags, identity
    and destination as the ACP session, so the two cannot disagree about whether
    the host is reachable.
    """
    from .acp_client import _DEFAULT_ACP_CMD

    argv = shlex.split(os.environ.get("DELPHI_ACP_CMD", _DEFAULT_ACP_CMD))
    return argv[:-1] if len(argv) >= 3 and argv[0] == "ssh" else None


def _probe(argv, workspace):
    """Ask the agent host what it actually has. None when it cannot be asked.

    One ssh answers which binaries exist, whether gh holds a usable credential
    and whether there is a workspace to edit in. Left to the agent, each of those
    costs a turn, and a run can spend its whole budget discovering it has no
    checkout and no credential.
    """
    if not argv:
        return None
    script = (_PROBE + f"; [ -d {shlex.quote(workspace)} ] && echo 'workspace: present'"
              " || echo 'workspace: MISSING (nothing to edit or commit from)'")
    try:
        proc = subprocess.run(
            argv + ["bash -lc " + shlex.quote(script)], capture_output=True, text=True,
            timeout=float(os.environ.get("DELPHI_PROBE_TIMEOUT", "15")), check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() or None


def _runtime(ctx):
    """The handles a run needs before it can act: host, workspace, tools, MCP."""
    from .mcp.tools import _workspace_for

    argv = _ssh_argv()
    key = ctx.get("project_key")
    workspace = _workspace_for(key) if key else "(no project, no workspace)"
    lines = [f"agent host: {argv[-1]}"] if argv else []
    lines += [f"workspace: {workspace}",
              f"pantheos MCP: {os.environ.get('PANTHEOS_MCP_URL') or 'not configured'}",
              _probe(argv, workspace) or
              "host probe unavailable: confirm tooling yourself before relying on it"]
    return "\n".join(lines)


def _fleet(containers):
    """One line per container, so a crash loop is readable without a query."""
    return "\n".join(
        f"{c.get('id')}  role={c.get('role')}  status={c.get('status')}  "
        f"restarts={c.get('restarts')}  err={c.get('err')}  p95={c.get('p95')}  "
        f"image={c.get('image')}"
        for c in containers)


def _prompt(tid, title, area, autonomy, ctx):
    """Ground the turn with what the run would otherwise rediscover by hand."""
    name, key = ctx.get("project_name"), ctx.get("project_key")
    where = f"project {name} ({key}), area {area}" if name else f"area {area}"
    lines = [f"You are Delphi working ticket {tid} in {where}.", ""]
    if ctx.get("project_context"):
        lines += ["Read and obey this project spec before acting:",
                  ctx["project_context"], ""]
    # get_project_spec is the documented grounding call, but it answers over the
    # MCP server, which is the thing most likely to be down on an infra ticket.
    # Inlining its remaining fields keeps a run grounded with no tools at all.
    lines += [f"{label}: {v}" for label, v in
              (("Repo", ctx.get("project_repo")),
               ("Project status", ctx.get("project_status"))) if v]
    if ctx.get("area_context"):
        lines += ["", "Area context:", ctx["area_context"]]
    if ctx.get("containers"):
        # Say whether these numbers were refreshed. Seeded values read as a
        # healthy fleet, which is the worst thing to assert during an outage.
        head = ("## Fleet (live)" if ctx.get("fleet_live")
                else "## Fleet (not refreshed, metrics store unreachable)")
        lines += ["", head, _fleet(ctx["containers"])]
    if ctx.get("runtime"):
        lines += ["", "## Runtime", ctx["runtime"]]
    lines += ["", f"## Autonomy ceiling: {autonomy}",
              _CEILINGS.get(autonomy, _CEILINGS["propose"]), _NEVER]
    skill = _SKILLS.get(ctx.get("source"))
    if skill:
        lines += ["", f"Follow the {skill} skill: take evidence from a tool call "
                  "before proposing any fix."]
    lines += ["", f"Ticket: {title}"]
    # An alert ticket sets summary = title; print it once.
    lines += [v for v in (ctx.get("summary"), ctx.get("body"))
              if v and v != title]
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
