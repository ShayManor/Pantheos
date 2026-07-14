from app.mcp import skills


def test_lists_three_real_skills():
    names = {s["name"] for s in skills.list_skills()}
    assert names == {"debug-issue", "fix-project", "triage-ticket"}
    for s in skills.list_skills():
        assert s["trigger"] and s["description"]


def test_load_skill_body_and_grounding():
    sk = skills.load_skill("debug-issue")
    assert sk["name"] == "debug-issue"
    # every skill enforces the grounding discipline + names real MCP tools
    assert "get_project_spec" in sk["body"]
    assert "run_claude_code" in skills.load_skill("fix-project")["body"]
    assert "create_ticket" in skills.load_skill("triage-ticket")["body"] or \
           "update_ticket" in skills.load_skill("triage-ticket")["body"]


def test_load_unknown():
    assert skills.load_skill("nope") == {"error": "unknown skill", "name": "nope"}


def test_load_rejects_path_traversal():
    # name is agent-controlled — anything that isn't a bare slug is rejected
    for bad in ("../../etc/passwd", "sub/dir", "", "foo.bar"):
        assert skills.load_skill(bad) == {"error": "unknown skill", "name": bad}
