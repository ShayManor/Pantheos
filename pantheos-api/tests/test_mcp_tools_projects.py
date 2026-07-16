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


def test_area_crud(session):
    made = tools.create_area(session, "robotics", "ROBOTICS", "lab", context="# ctx")
    assert made["id"] == "robotics" and made["name"] == "ROBOTICS" and made["context"] == "# ctx"
    up = tools.update_area(session, "robotics", name="ROBO", active=False, kind="club")
    assert up["name"] == "ROBO" and up["active"] is False and up["kind"] == "club"
    assert tools.delete_area(session, "robotics") == {"deleted": "robotics"}
    assert tools.get_area(session, "robotics")["error"] == "unknown area"
    # validation + not-found + exists
    assert tools.create_area(session, " ", "x", "lab")["error"] == "id and name required"
    assert tools.create_area(session, "ideas_lab", "dup", "lab")["error"] == "area exists"
    assert tools.update_area(session, "nope")["error"] == "unknown area"
    assert tools.delete_area(session, "nope")["error"] == "unknown area"


def test_delete_area_guarded_by_dependents(session):
    # ideas_lab owns projects/tickets in the seed → refuse, name the blockers
    out = tools.delete_area(session, "ideas_lab")
    assert out["error"] == "area has dependents"
    assert out["projects"] > 0 or out["tickets"] > 0


def test_project_crud(session):
    made = tools.create_project(session, "robo", "ideas_lab", "Robo", "propose",
                                "go", blurb="b", context="# spec")
    assert made["key"] == "robo" and made["autonomy"] == "propose" and made["context"] == "# spec"
    up = tools.update_project(session, "robo", status="cau", autonomy="full",
                              area_id="side", name="Robo2")
    assert up["status"] == "cau" and up["autonomy"] == "full" and up["area"]
    assert tools.delete_project(session, "robo") == {"deleted": "robo"}
    assert tools.get_project(session, "robo")["error"] == "unknown project"


def test_project_create_validation(session):
    assert tools.create_project(session, " ", "ideas_lab", "n", "propose", "go")["error"] == "key and name required"
    assert tools.create_project(session, "merlin", "ideas_lab", "n", "propose", "go")["error"] == "project exists"
    assert tools.create_project(session, "x", "nope", "n", "propose", "go")["error"] == "unknown area"
    assert tools.create_project(session, "x", "ideas_lab", "n", "bogus", "go")["error"] == "invalid autonomy"
    assert tools.create_project(session, "x", "ideas_lab", "n", "propose", "bad")["error"] == "invalid status"


def test_project_update_validation_and_missing(session):
    assert tools.update_project(session, "nope")["error"] == "unknown project"
    assert tools.update_project(session, "merlin", autonomy="bogus")["error"] == "invalid autonomy"
    assert tools.update_project(session, "merlin", status="bad")["error"] == "invalid status"
    assert tools.update_project(session, "merlin", area_id="nope")["error"] == "unknown area"


def test_delete_project_guarded_by_dependents(session):
    # a container blocks the delete (ghstats runs containers in the seed)
    out = tools.delete_project(session, "ghstats")
    assert out["error"] == "project has dependents"
    assert out["containers"] > 0
    # a ticket blocks it too (provision one so the branch is exercised)
    tools.create_ticket(session, title="blocker", project_key="merlin")
    blocked = tools.delete_project(session, "merlin")
    assert blocked["error"] == "project has dependents" and blocked["tickets"] > 0
    assert tools.delete_project(session, "nope")["error"] == "unknown project"
