from app.mcp import tools


def test_list_tickets_filters(session):
    all_t = tools.list_tickets(session)["tickets"]
    assert all_t
    merlin = tools.list_tickets(session, project="merlin")["tickets"]
    assert merlin and all(t["proj"] == "merlin" for t in merlin)
    queued = tools.list_tickets(session, life="queued")["tickets"]
    assert all(t["life"] == "queued" for t in queued)
    hot = tools.list_tickets(session, hot=True)["tickets"]
    assert all(t["hot"] for t in hot)


def test_get_ticket_and_missing(session):
    tid = tools.list_tickets(session)["tickets"][0]["id"]
    assert tools.get_ticket(session, tid)["id"] == tid
    assert tools.get_ticket(session, "NOPE") == {"error": "unknown ticket", "id": "NOPE"}


def test_create_ticket_scores_and_ids(session):
    t = tools.create_ticket(session, title="Port to Rubik Pi", project_key="merlin",
                            pri=1, deadline_hours=24, effort_hours=4)
    assert t["proj"] == "merlin" and t["title"] == "Port to Rubik Pi"
    assert t["life"] == "queued" and t["agent"] == "idle" and t["source"] == "delphi"
    assert float(t["score"]) > 0 and t["due"] == "in 1d"
    # unknown project / missing area / bad pri / no title
    assert tools.create_ticket(session, title="x", project_key="nope")["error"] == "unknown project"
    assert tools.create_ticket(session, title="x")["error"] == "area or project required"
    assert tools.create_ticket(session, title="x", area_id="nope")["error"] == "unknown area"
    assert tools.create_ticket(session, title="x", project_key="merlin", pri=9)["error"] == "invalid priority"
    assert tools.create_ticket(session, title="  ", project_key="merlin")["error"] == "title required"


def test_update_ticket_recomputes_score(session):
    t = tools.create_ticket(session, title="Rescore me", project_key="merlin", pri=3)
    before = float(t["score"])
    up = tools.update_ticket(session, t["id"], pri=0, deadline_hours=6, effort_hours=1)
    assert float(up["score"]) > before and up["due"] == "now" and up["hot"] is True
    # a text-only edit must NOT rescore (would clobber a propagated score)
    edited = tools.update_ticket(session, t["id"], summary="s", body="b")
    assert edited["summary"] == "s" and float(edited["score"]) == float(up["score"])
    assert tools.update_ticket(session, "NOPE", pri=0) == {"error": "unknown ticket", "id": "NOPE"}


def test_move_and_agent_state(session):
    tid = tools.create_ticket(session, title="Move me", project_key="merlin")["id"]
    assert tools.move_ticket(session, tid, "active")["life"] == "active"
    assert tools.move_ticket(session, tid, "bogus")["error"] == "invalid lifecycle"
    assert tools.set_agent_state(session, tid, "executing")["agent"] == "executing"
    assert tools.set_agent_state(session, tid, "bogus")["error"] == "invalid agent state"
    assert tools.move_ticket(session, "NOPE", "active")["error"] == "unknown ticket"
    assert tools.set_agent_state(session, "NOPE", "idle")["error"] == "unknown ticket"


def test_add_link_and_dep(session):
    tid = tools.create_ticket(session, title="Link me", project_key="merlin")["id"]
    linked = tools.add_ticket_link(session, tid, "pr", "PR #1", "https://x/1")
    assert linked["links"][-1] == {"kind": "pr", "label": "PR #1", "url": "https://x/1"}
    depped = tools.add_dep(session, tid, "MER-0001", "upstream fix")
    assert depped["deps"][-1] == {"id": "MER-0001", "title": "upstream fix", "done": False}
    assert tools.add_ticket_link(session, "NOPE", "pr", "l", "u")["error"] == "unknown ticket"
    assert tools.add_dep(session, "NOPE", "d", "t")["error"] == "unknown ticket"


def test_list_tickets_more_filters(session):
    # agent + area filters (branch coverage)
    from app.models import Ticket
    idle = tools.list_tickets(session, agent="idle")["tickets"]
    assert all(x["agent"] == "idle" for x in idle)
    first = tools.list_tickets(session)["tickets"][0]["id"]
    a_id = session.get(Ticket, first).area_id
    by_area = tools.list_tickets(session, area=a_id)["tickets"]
    assert by_area and all(x["area"] for x in by_area)


def test_update_ticket_rejects_invalid_pri(session):
    tid = tools.create_ticket(session, title="Bad pri", project_key="merlin")["id"]
    assert tools.update_ticket(session, tid, pri=9)["error"] == "invalid priority"
