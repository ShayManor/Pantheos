from app.mcp import tools


def test_memory_list_and_add(session):
    before = tools.list_memory(session)["memory"]
    out = tools.add_memory_fact(session, "Delphi learned a new thing")
    assert out["added"] == "Delphi learned a new thing"
    assert len(out["memory"]) == len(before) + 1
    assert "Delphi learned a new thing" in tools.list_memory(session)["memory"]
    assert tools.add_memory_fact(session, "  ") == {"error": "text required"}


def test_recent_runs(session):
    runs = tools.list_recent_runs(session)["runs"]
    assert runs and "ticket" in runs[0]


def test_list_skills(session):
    skills = tools.list_skills(session)["skills"]
    assert skills and "name" in skills[0]


def test_memory_update_and_remove(session):
    tools.add_memory_fact(session, "fact to edit")
    up = tools.update_memory_fact(session, "fact to edit", "edited fact")
    assert "edited fact" in up["memory"] and "fact to edit" not in up["memory"]
    rm = tools.remove_memory_fact(session, "edited fact")
    assert "edited fact" not in rm["memory"] and rm["removed"] == "edited fact"
    assert tools.update_memory_fact(session, "gone", "x")["error"] == "unknown memory fact"
    assert tools.update_memory_fact(session, "edited fact", "  ")["error"] == "new_text required"
    assert tools.remove_memory_fact(session, "gone")["error"] == "unknown memory fact"


def test_agent_run_crud(session):
    made = tools.create_agent_run(session, "MER-0001", "enrich", "done", "$0.02", "now")
    assert made["ticket"] == "MER-0001" and "id" in made
    rid = made["id"]
    assert any(r["id"] == rid for r in tools.list_recent_runs(session)["runs"])
    up = tools.update_agent_run(session, rid, status="needs review", cost="$0.10")
    assert up["status"] == "needs review" and up["cost"] == "$0.10"
    assert tools.delete_agent_run(session, rid) == {"deleted": rid}
    assert tools.create_agent_run(session, " ", "k", "s", "c", "w")["error"] == "ticket required"
    assert tools.update_agent_run(session, 999999)["error"] == "unknown run"
    assert tools.delete_agent_run(session, 999999)["error"] == "unknown run"


def test_skill_crud(session):
    made = tools.create_skill(session, "sk1", "My Skill", trigger="manual", desc="d")
    assert made == {"id": "sk1", "name": "My Skill", "on": True,
                    "trigger": "manual", "desc": "d"}
    up = tools.update_skill(session, "sk1", desc="d2", on=False)
    assert up["desc"] == "d2" and up["on"] is False
    assert tools.delete_skill(session, "sk1") == {"deleted": "sk1"}
    assert tools.create_skill(session, " ", "x")["error"] == "id and name required"
    assert tools.create_skill(session, "sk2", "x")["id"] == "sk2"
    assert tools.create_skill(session, "sk2", "dup")["error"] == "skill exists"
    assert tools.update_skill(session, "nope")["error"] == "unknown skill"
    assert tools.delete_skill(session, "nope")["error"] == "unknown skill"
