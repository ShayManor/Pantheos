import asyncio

from app.mcp import server
from app.mcp import session as msession


def test_instructions_enforce_grounding():
    assert server.mcp.instructions
    text = server.mcp.instructions.lower()
    assert "get_project_spec" in text and "autonomy" in text and "ground" in text


def test_tool_count_matches_registry():
    listed = asyncio.run(server.mcp.list_tools())
    assert server.TOOL_COUNT == len(listed)
    assert server.TOOL_COUNT >= 20


def test_wrapper_delegates_through_session_scope(session, monkeypatch):
    # wrappers open their own scope — point it at the test session
    monkeypatch.setattr(msession, "_factory", lambda: session)
    out = server.get_project_spec("merlin")
    assert out["key"] == "merlin"
    created = server.create_ticket(title="Via wrapper", project_key="merlin")
    assert created["title"] == "Via wrapper"


def test_every_wrapper_runs_through_scope(session, monkeypatch):
    # Exercise every registered wrapper once so its session_scope body executes.
    monkeypatch.setattr(msession, "_factory", lambda: session)
    tid = server.list_tickets()["tickets"][0]["id"]
    cid = server.list_containers()["containers"][0]["id"]
    aid = server.list_areas()["areas"][0]["id"]

    calls = [
        server.list_projects(),
        server.get_project("merlin"),
        server.get_area(aid),
        server.get_ticket(tid),
        server.update_ticket(tid, summary="s"),
        server.move_ticket(tid, "active"),
        server.set_agent_state(tid, "idle"),
        server.add_ticket_link(tid, "pr", "l", "https://x/1"),
        server.add_dep(tid, "MER-9999", "dep"),
        server.list_hosts(),
        server.get_container(cid),
        server.get_container_logs(cid),
        server.restart_container(cid),
        server.list_memory(),
        server.add_memory_fact("wrapper fact"),
        server.list_recent_runs(),
        server.list_skills(),
        server.get_skill("debug-issue"),
        server.run_claude_code("merlin", "noop", dry_run=True),
    ]
    assert all(c is not None for c in calls)
    assert server.get_skill("debug-issue")["name"] == "debug-issue"
