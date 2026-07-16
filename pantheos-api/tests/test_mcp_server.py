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


def test_every_crud_wrapper_runs_through_scope(session, monkeypatch):
    # Exercise every full-CRUD wrapper once (self-provisioning, so it holds
    # against the baseline seed) to cover its session_scope body.
    monkeypatch.setattr(msession, "_factory", lambda: session)

    tid = server.create_ticket(title="wrap", project_key="merlin")["id"]
    server.add_dep(tid, "MER-9", "d")
    server.add_ticket_link(tid, "pr", "l", "https://x/9")
    run_id = server.create_agent_run("MER-9", "enrich", "done", "$0", "now")["id"]
    server.create_session("wsess", "T", ts="now")
    msg_id = server.add_message("wsess", "me", "hi", tools_used=[{"name": "x"}])["id"]

    calls = [
        server.create_area("warea", "WA", kind="lab"),
        server.update_area("warea", name="WA2", active=False),
        server.delete_area("warea"),
        server.create_project("wproj", "ideas_lab", "WP", "propose", "go"),
        server.update_project("wproj", status="cau"),
        server.delete_project("wproj"),
        server.update_dep(tid, "MER-9", done=True),
        server.remove_dep(tid, "MER-9"),
        server.update_ticket_link(tid, "https://x/9", label="l2"),
        server.remove_ticket_link(tid, "https://x/9"),
        server.delete_ticket(tid),
        server.get_host("minipc"),
        server.create_host("whost", "WH"),
        server.update_host("whost", loc="apt"),
        server.delete_host("whost"),
        server.create_container("wcont", "ghstats", "minipc", "api"),
        server.update_container("wcont", status="cau"),
        server.delete_container("wcont"),
        server.update_memory_fact("f", "f2") if server.add_memory_fact("f") else None,
        server.remove_memory_fact("f2"),
        server.update_agent_run(run_id, status="needs review"),
        server.delete_agent_run(run_id),
        server.create_skill("wskill", "WS"),
        server.update_skill("wskill", on=False),
        server.delete_skill("wskill"),
        server.list_mcp_servers(),
        server.get_mcp_server("pantheos"),
        server.create_mcp_server("wmcp", "WM"),
        server.update_mcp_server("wmcp", desc="d"),
        server.delete_mcp_server("wmcp"),
        server.list_agent_models(),
        server.get_agent_model("gpt-5.6-terra"),
        server.create_agent_model("wmodel", "WMo"),
        server.update_agent_model("wmodel", tag="t"),
        server.delete_agent_model("wmodel"),
        server.list_sessions(),
        server.get_session("wsess"),
        server.update_session("wsess", title="T2"),
        server.update_message(msg_id, text="hey"),
        server.delete_message(msg_id),
        server.delete_session("wsess"),
    ]
    assert all(c is not None for c in calls)
