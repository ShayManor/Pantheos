import shutil
import subprocess

from app import ticket_run
from app.ticket_run import run_ticket


def _collect(gen):
    events = list(gen)
    types = [e["type"] for e in events]
    done = events[-1]
    return events, types, done


def test_run_ticket_event_sequence_and_tools():
    events, types, done = _collect(run_ticket("GRD-0182", "Fix flaky auth test", "Research", "propose"))
    # reasoning first, at least one tool, text chunks, done last
    assert types[0] == "reasoning"
    assert "tool" in types
    assert "text" in types
    assert types[-1] == "done"
    # tool names are TOOLMAP keys
    tool_names = [e["name"] for e in events if e["type"] == "tool"]
    assert tool_names and set(tool_names) <= {"github", "vm", "calendar", "brightspace", "queue", "claude"}
    assert done["tools"] == tool_names
    # streamed text reconstructs the final output
    streamed = "".join(e["delta"] for e in events if e["type"] == "text")
    assert streamed == done["text"]
    assert "GRD-0182" in done["reasoning"]


def test_run_ticket_is_deterministic():
    a = list(run_ticket("T-1", "Deploy the service", "Infra", "auto_pr"))
    b = list(run_ticket("T-1", "Deploy the service", "Infra", "auto_pr"))
    assert a == b


def test_run_ticket_autonomy_variants():
    propose = list(run_ticket("T-1", "x", "A", "propose"))[-1]
    autopr = list(run_ticket("T-1", "x", "A", "auto_pr"))[-1]
    full = list(run_ticket("T-1", "x", "A", "full"))[-1]
    assert "review" in propose["report"].lower()
    assert "auto-merge" in autopr["report"].lower()
    assert "live" in full["report"].lower()
    # unknown autonomy falls back to the propose/stop-for-review path
    unknown = list(run_ticket("T-1", "x", "A", None))[-1]
    assert "review" in unknown["report"].lower()


def test_run_ticket_keyword_routing_covers_all_routes():
    # each keyword family plus the default path
    assert "vm" in list(run_ticket("T", "latency alert on api", "A", "full"))[-1]["tools"]
    assert "queue" in list(run_ticket("T", "release rollout", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "update the readme", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "fix flaky ci test", "A", "full"))[-1]["tools"]
    assert list(run_ticket("T", "something unrelated", "A", "full"))[-1]["tools"]


# ------------------------------------------------- real-backend run context
def _ctx(**over):
    ctx = {"summary": "5xx over 5%", "body": "rule: HighErrorRate\nsite: pantheos.app",
           "project_name": "Pantheos", "project_key": "groundstation",
           "project_context": "# Pantheos\n\n## Ops\n- ssh minipc\n",
           "project_repo": "ShayManor/Pantheos", "project_status": "flt",
           "area_context": "# SIDE PROJECTS\n", "source": "monitor",
           "containers": [{"id": "pantheos-mcp-1", "role": "mcp", "status": "flt",
                           "restarts": 45605, "err": "0.0%", "p95": "—",
                           "image": "ghcr.io/shaymanor/pantheos:main"}],
           "runtime": "agent host: shay@127.0.0.1"}
    ctx.update(over)
    return ctx


def test_prompt_inlines_the_whole_project_spec():
    """get_project_spec is the documented grounding call, but it lives behind the
    MCP server, which is exactly what is down during an infra ticket. Inline it."""
    p = ticket_run._prompt("ALR-1", "5xx spike", "SIDE", "full", _ctx())
    assert "ShayManor/Pantheos" in p          # repo, previously never reached
    assert "flt" in p                         # project status
    assert "SIDE PROJECTS" in p               # owning area context


def test_prompt_routes_a_monitor_ticket_to_the_debug_skill():
    p = ticket_run._prompt("ALR-1", "5xx spike", "SIDE", "full", _ctx())
    assert "debug-issue" in p


def test_prompt_leaves_a_manual_ticket_unrouted():
    p = ticket_run._prompt("GRD-1", "Add a flag", "SIDE", "full", _ctx(source="manual"))
    assert "debug-issue" not in p


def test_prompt_spells_out_what_the_ceiling_permits():
    """'full = may commit to main' never told the agent that a commit to main is
    a production deploy, so it stalled asking whether it had approval."""
    p = ticket_run._prompt("ALR-1", "5xx", "SIDE", "full", _ctx())
    assert "deploy" in p.lower()
    assert "force-push" in p.lower()          # the never-list


def test_prompt_lists_the_project_fleet():
    p = ticket_run._prompt("ALR-1", "5xx", "SIDE", "full", _ctx())
    assert "pantheos-mcp-1" in p
    assert "45605" in p                       # the restart count naming the culprit


def test_prompt_carries_the_runtime_block():
    p = ticket_run._prompt("ALR-1", "5xx", "SIDE", "full", _ctx())
    assert "shay@127.0.0.1" in p


def test_prompt_survives_a_ticket_with_no_project():
    p = ticket_run._prompt("GRD-1", "x", "SIDE", None, {})
    assert "GRD-1" in p and "RESULT:" in p


# ------------------------------------------------------ agent-host handles
def test_ssh_argv_reuses_the_configured_acp_transport(monkeypatch):
    """The probe must ride the same flags and identity as the ACP session, or it
    reports a reachability the real turn does not have."""
    monkeypatch.setenv("DELPHI_ACP_CMD",
                       "ssh -F /dev/null -i /root/.ssh/id_ed25519 shay@127.0.0.1"
                       " \"bash -lc 'hermes acp'\"")
    argv = ticket_run._ssh_argv()
    assert argv[0] == "ssh" and argv[-1] == "shay@127.0.0.1"
    assert "bash -lc 'hermes acp'" not in argv      # remote command dropped
    assert "-F" in argv and "/root/.ssh/id_ed25519" in argv


def test_ssh_argv_is_none_when_hermes_runs_locally(monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_CMD", "hermes acp")
    assert ticket_run._ssh_argv() is None


def test_probe_is_skipped_without_a_transport():
    assert ticket_run._probe(None, "/ws") is None


def test_probe_reports_what_the_host_answered(monkeypatch):
    seen = {}

    def fake_run(argv, **kw):
        seen["argv"] = argv
        return type("P", (), {"stdout": "git docker <- on PATH\ngh auth: INVALID"})()

    monkeypatch.setattr("subprocess.run", fake_run)
    out = ticket_run._probe(["ssh", "host"], "/ws/groundstation")
    assert "gh auth: INVALID" in out
    assert "/ws/groundstation" in seen["argv"][-1]   # workspace check is included


def test_probe_degrades_to_none_when_the_host_cannot_be_reached(monkeypatch):
    def boom(argv, **kw):
        raise OSError("no route to host")

    monkeypatch.setattr("subprocess.run", boom)
    assert ticket_run._probe(["ssh", "host"], "/ws") is None


def test_probe_degrades_to_none_on_empty_output(monkeypatch):
    monkeypatch.setattr("subprocess.run",
                        lambda argv, **kw: type("P", (), {"stdout": "  \n"})())
    assert ticket_run._probe(["ssh", "host"], "/ws") is None


def test_runtime_block_names_host_workspace_and_mcp(monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_CMD", "ssh -F /dev/null shay@127.0.0.1 \"bash -lc 'x'\"")
    monkeypatch.setenv("PANTHEOS_WORKSPACE_ROOT", "/srv/ws")
    monkeypatch.setenv("PANTHEOS_MCP_URL", "http://127.0.0.1:8001/mcp")
    monkeypatch.setattr(ticket_run, "_probe", lambda argv, ws: "gh auth: ok")
    block = ticket_run._runtime({"project_key": "groundstation"})
    assert "agent host: shay@127.0.0.1" in block
    assert "workspace: /srv/ws/groundstation" in block
    assert "http://127.0.0.1:8001/mcp" in block
    assert "gh auth: ok" in block


def test_runtime_block_says_so_when_the_probe_failed(monkeypatch):
    """Silence would read as 'the tooling is fine'; the run has to know it is
    acting on unverified ground."""
    monkeypatch.delenv("PANTHEOS_MCP_URL", raising=False)
    monkeypatch.setattr(ticket_run, "_probe", lambda argv, ws: None)
    block = ticket_run._runtime({"project_key": "groundstation"})
    assert "probe unavailable" in block
    assert "not configured" in block                # MCP URL absent, said plainly


def test_runtime_block_without_a_project(monkeypatch):
    monkeypatch.setattr(ticket_run, "_probe", lambda argv, ws: None)
    assert "no workspace" in ticket_run._runtime({})


def test_prompt_does_not_repeat_the_title_as_summary():
    """An alert ticket sets summary = title, and printing both spends the
    agent's attention re-reading a line it already has."""
    p = ticket_run._prompt("ALR-1", "5xx over 5%", "SIDE", "full",
                           _ctx(summary="5xx over 5%"))
    assert p.count("5xx over 5%") == 1


def test_prompt_marks_a_fleet_it_could_not_refresh():
    """restarts=0 / status=go reads as healthy. With the metrics store down
    during an outage that is a confident falsehood, so label which it is."""
    live = ticket_run._prompt("ALR-1", "x", "SIDE", "full", _ctx(fleet_live=True))
    stale = ticket_run._prompt("ALR-1", "x", "SIDE", "full", _ctx(fleet_live=False))
    assert "## Fleet (live)" in live
    assert "## Fleet (live)" not in stale and "not refreshed" in stale


def _run_probe(tmp_path, **fakes):
    """Run the probe script with PATH holding only the stand-ins a test supplies.

    Inheriting the real PATH made the outcome depend on what the host happened
    to have installed: CI runners ship gh in /usr/bin, so an "absent" case
    passed locally and failed there.
    """
    for name, body in fakes.items():
        f = tmp_path / name
        f.write_text(body)
        f.chmod(0o755)
    # `head` is the one external binary the script itself pipes through.
    (tmp_path / "head").symlink_to(shutil.which("head"))
    return subprocess.run([shutil.which("bash"), "-c", ticket_run._PROBE],
                          env={"PATH": str(tmp_path)},
                          capture_output=True, text=True).stdout


def test_probe_calls_a_dead_gh_token_invalid(tmp_path):
    """`gh auth status` exits 0 with an unusable token, so an exit-code check
    reports a credential the run does not actually have."""
    out = _run_probe(tmp_path, gh="#!/bin/sh\n"
                     "echo 'X Failed to log in to github.com account ShayManor'\n"
                     "exit 0\n")
    assert "gh auth: INVALID" in out


def test_probe_calls_a_live_gh_token_ok(tmp_path):
    out = _run_probe(tmp_path, gh="#!/bin/sh\necho 'Logged in to github.com'\n")
    assert "gh auth: ok" in out


def test_probe_says_so_when_gh_is_absent(tmp_path):
    """No gh at all is a different answer from a bad credential, and it changes
    what the run should try next."""
    assert "gh auth: no gh binary" in _run_probe(tmp_path)


def test_probe_reports_container_uptime(tmp_path):
    """restarts=N says a container is looping. Uptime says whether a restart was
    a deploy a minute ago or a crash loop, which is the distinction a run needs
    before it decides the alert is its own fault."""
    out = _run_probe(tmp_path, docker="#!/bin/sh\n"
                     "echo 'pantheos-mcp-1  Restarting (1) 56 seconds ago'\n")
    assert "pantheos-mcp-1" in out and "Restarting" in out
