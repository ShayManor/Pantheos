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
