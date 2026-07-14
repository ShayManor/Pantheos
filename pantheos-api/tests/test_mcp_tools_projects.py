from app.mcp import tools


def test_get_project_spec_includes_context_and_autonomy(session):
    spec = tools.get_project_spec(session, "merlin")
    assert spec["key"] == "merlin"
    assert spec["autonomy"] in {"propose", "auto_pr", "full"}
    assert "# " in spec["context"]           # per-project CLAUDE.md body
    assert spec["area_context"]              # owning area context present
    assert "repo" in spec


def test_get_project_spec_unknown(session):
    assert tools.get_project_spec(session, "nope") == {"error": "unknown project", "key": "nope"}


def test_list_and_get_project(session):
    listed = tools.list_projects(session)["projects"]
    assert any(p["key"] == "merlin" for p in listed)
    one = tools.get_project(session, "merlin")
    assert one["key"] == "merlin" and one["name"]
    assert tools.get_project(session, "nope") == {"error": "unknown project", "key": "nope"}


def test_list_and_get_area(session):
    areas = tools.list_areas(session)["areas"]
    aid = areas[0]["id"]
    got = tools.get_area(session, aid)
    assert got["id"] == aid and "context" in got
    assert tools.get_area(session, "nope") == {"error": "unknown area", "id": "nope"}
