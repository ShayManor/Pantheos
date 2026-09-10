def test_list_tickets(client):
    r = client.get("/api/tickets")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 9
    grd = next(t for t in data if t["id"] == "GRD-0182")
    assert grd["effort"] == "6h"
    assert grd["area"] == "IDEAS LAB"
    assert len(grd["links"]) == 2
    # score is a formatted string; queue is score-ranked (GHS-0311 is P0/now → top)
    assert data[0]["id"] in {"GRD-0182", "GHS-0311"}
    evc = next(t for t in data if t["id"] == "EVC-0074")
    assert evc["deps"][0]["id"] == "EVC-0071"


def test_create_ticket_with_project(client):
    r = client.post("/api/tickets", json={
        "title": "New investigation", "project_key": "ghstats", "pri": 1,
        "effort_hours": 4, "deadline_hours": 72, "summary": "look into it",
        "body": "## Repro\nHit `/api/foo` and it 500s."})
    assert r.status_code == 201
    t = r.get_json()
    assert t["title"] == "New investigation"
    assert t["proj"] == "ghstats"
    assert t["area"] == "SIDE PROJECTS"
    assert t["summary"] == "look into it"
    assert t["body"] == "## Repro\nHit `/api/foo` and it 500s."  # distinct longer context
    assert t["life"] == "queued" and t["agent"] == "idle" and t["source"] == "manual"
    assert t["due"] == "in 3d"           # derived from deadline_hours
    assert float(t["score"]) > 0          # derived score
    assert client.get("/api/tickets").get_json().__len__() == 10  # now 10
    assert client.get(f"/api/tickets/{t['id']}").status_code == 200


def test_create_ticket_area_only_defaults(client):
    r = client.post("/api/tickets", json={"title": "Study for midterm", "area_id": "stat511"})
    assert r.status_code == 201
    t = r.get_json()
    assert t["proj"] is None and t["area"] == "STAT 511"
    assert t["pri"] == 2                   # default priority
    assert t["due"] is None                # no deadline
    assert t["summary"] == "Study for midterm"  # summary defaults to title
    assert t["body"] == ""                 # body is NOT a copy of summary when omitted


def test_create_ticket_validation(client):
    assert client.post("/api/tickets", json={"title": "  "}).status_code == 400
    assert client.post("/api/tickets", json={"title": "x", "project_key": "nope"}).status_code == 400
    assert client.post("/api/tickets", json={"title": "x"}).status_code == 400  # no area/project
    assert client.post("/api/tickets", json={"title": "x", "area_id": "nope"}).status_code == 400
    assert client.post("/api/tickets", json={"title": "x", "area_id": "stat511", "pri": 9}).status_code == 400


def test_get_ticket_and_404(client):
    assert client.get("/api/tickets/GRD-0182").status_code == 200
    assert client.get("/api/tickets/NOPE").status_code == 404


def test_launch_propose(client):
    d = client.post("/api/tickets/EVC-0074/launch").get_json()
    assert "PR-only" in d["toast"]
    assert d["ticket"]["agent"] == "executing"


def test_launch_full_and_no_project(client):
    assert "Claude Code" in client.post("/api/tickets/GHS-0311/launch").get_json()["toast"]
    assert "Claude Code" in client.post("/api/tickets/STA-0044/launch").get_json()["toast"]


def test_launch_backburner_becomes_queued(client):
    d = client.post("/api/tickets/MER-0088/launch").get_json()["ticket"]
    assert d["life"] == "queued"
    assert d["agent"] == "executing"


def test_launch_404(client):
    assert client.post("/api/tickets/NOPE/launch").status_code == 404


def test_update_lifecycle(client):
    r = client.patch("/api/tickets/GRD-0182", json={"life": "archived"})
    assert r.get_json()["life"] == "archived"


def test_update_invalid_lifecycle(client):
    assert client.patch("/api/tickets/GRD-0182", json={"life": "bogus"}).status_code == 400


def test_update_noop(client):
    r = client.patch("/api/tickets/GRD-0182", json={})
    assert r.status_code == 200
    assert r.get_json()["life"] == "active"


def test_update_404(client):
    assert client.patch("/api/tickets/NOPE", json={"life": "queued"}).status_code == 404


def test_delete_ticket(client):
    r = client.delete("/api/tickets/GRD-0182")
    assert r.status_code == 204
    assert r.get_data() == b""
    assert client.get("/api/tickets/GRD-0182").status_code == 404
    assert len(client.get("/api/tickets").get_json()) == 8


def test_delete_ticket_404(client):
    assert client.delete("/api/tickets/NOPE").status_code == 404
    client.delete("/api/tickets/GRD-0182")
    assert client.delete("/api/tickets/GRD-0182").status_code == 404  # gone → 404


def test_delete_ticket_keeps_dependents(client):
    # MER-0093 depends on MER-0088; deleting the referenced ticket leaves the
    # dangling dep on the dependent intact (dep_id may reference a missing ticket).
    assert client.delete("/api/tickets/MER-0088").status_code == 204
    mer = client.get("/api/tickets/MER-0093").get_json()
    assert mer["deps"][0]["id"] == "MER-0088"


def test_ticket_run_stream_persists_and_completes(client, app):
    body = client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)
    assert "event: reasoning" in body
    assert "event: tool" in body
    assert "event: done" in body
    # side effects persisted
    from app.models import AgentRun, Ticket
    with app.app_context():
        s = app.db_session
        t = s.get(Ticket, "GRD-0182")
        assert t.agent == "needs_review"
        assert t.report and t.result
        run = (s.query(AgentRun)
               .filter(AgentRun.ticket == "GRD-0182", AgentRun.status == "done")
               .order_by(AgentRun.position.desc()).first())
        assert run is not None
        assert run.output and run.reasoning and run.tools


def test_ticket_run_stream_reuses_existing_running_run(client, app):
    from app.models import AgentRun

    with app.app_context():
        s = app.db_session
        existing = AgentRun(ticket="GRD-0182", kind="execute", status="running",
                             cost="—", when="Just now", position=999)
        s.add(existing)
        s.commit()
        existing_id = existing.id

    client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)

    with app.app_context():
        s = app.db_session
        execute_runs = (s.query(AgentRun)
                         .filter(AgentRun.ticket == "GRD-0182", AgentRun.kind == "execute")
                         .all())
        assert len(execute_runs) == 1
        reused = execute_runs[0]
        assert reused.id == existing_id
        assert reused.status == "done"
        assert reused.output is not None


def test_ticket_runs_endpoint_newest_first(client):
    client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)
    runs = client.get("/api/tickets/GRD-0182/runs").get_json()
    assert isinstance(runs, list) and len(runs) >= 1
    assert runs[0]["status"] == "done"
    assert "output" in runs[0]


def test_ticket_run_stream_unknown_ticket_404(client):
    assert client.get("/api/tickets/NOPE/run/stream").status_code == 404
    assert client.get("/api/tickets/NOPE/runs").status_code == 404


def test_ticket_run_stream_surfaces_errors(client, app, monkeypatch):
    from app.api import tickets as tickets_api

    def boom(*a, **k):
        raise RuntimeError("kaboom")
        yield  # pragma: no cover  (make it a generator)

    monkeypatch.setattr(tickets_api, "run_ticket", boom)
    body = client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)
    assert "event: error" in body
    assert "kaboom" in body

    from app.models import AgentRun, Ticket
    with app.app_context():
        s = app.db_session
        t = s.get(Ticket, "GRD-0182")
        assert t.agent == "idle"
        run = (s.query(AgentRun)
               .filter(AgentRun.ticket == "GRD-0182", AgentRun.kind == "execute")
               .order_by(AgentRun.position.desc()).first())
        assert run is not None
        assert run.status == "error"


def _fake_turn(output, reasoning="checked the container logs", tools=("terminal",),
               capture=None):
    """Build a stand-in for acp.run_turn that replays one real-shaped ACP turn."""
    def run_turn(text, hermes_session_id, model=None, history=None, auto_approve=True):
        if capture is not None:
            capture["text"] = text
            capture["auto_approve"] = auto_approve
        yield {"type": "reasoning", "delta": reasoning}
        for name in tools:
            yield {"type": "tool", "id": name, "name": name, "status": "done", "title": name}
        yield {"type": "text", "delta": output}
        yield {"type": "done", "text": output, "reasoning": reasoning,
               "tools": list(tools), "hermes_session_id": "sess-1"}
    return run_turn


def test_ticket_run_stream_acp_mode_persists_agent_result(client, app, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    output = ("Pulled the container logs and found the unhandled 429.\n\n"
              "RESULT: Rate-limit path now raises instead of storing 0.\n"
              "REPORT: The fetcher swallowed GitHub 429s and wrote 0 stars; it now "
              "raises GitHubTransientError and the cron retries.")
    monkeypatch.setattr("app.acp.run_turn", _fake_turn(output))

    body = client.get("/api/tickets/GHS-0311/run/stream").get_data(as_text=True)
    assert "event: done" in body

    from app.models import AgentRun, Ticket
    with app.app_context():
        s = app.db_session
        t = s.get(Ticket, "GHS-0311")
        assert t.result == "Rate-limit path now raises instead of storing 0."
        assert t.report == ("The fetcher swallowed GitHub 429s and wrote 0 stars; it now "
                            "raises GitHubTransientError and the cron retries.")
        assert t.agent == "needs_review"
        run = (s.query(AgentRun)
               .filter(AgentRun.ticket == "GHS-0311", AgentRun.kind == "execute")
               .order_by(AgentRun.position.desc()).first())
        assert run.status == "done"
        assert run.output == output
        assert run.tools == ["terminal"]
        assert run.cost == "—"


def test_ticket_run_stream_acp_mode_falls_back_when_agent_skips_markers(client, app, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    output = ("Could not reproduce the 500 locally.\nThe container is healthy.\n\n"
              "Next step is to tail the edge logs during a live spike.")
    monkeypatch.setattr("app.acp.run_turn", _fake_turn(output))

    client.get("/api/tickets/GHS-0311/run/stream").get_data(as_text=True)

    from app.models import Ticket
    with app.app_context():
        t = app.db_session.get(Ticket, "GHS-0311")
        assert t.result == "Could not reproduce the 500 locally."
        assert t.report == ("Could not reproduce the 500 locally.\n"
                            "The container is healthy.")


def test_ticket_run_stream_acp_mode_keeps_wrapped_report_paragraph(client, app, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    output = ("RESULT: Pinned the fetcher to the retrying client.\n"
              "REPORT: The 429 path stored 0 stars for every user in the batch.\n"
              "Pinning the retrying client keeps the previous value until the\n"
              "window resets.")
    monkeypatch.setattr("app.acp.run_turn", _fake_turn(output))

    client.get("/api/tickets/GHS-0311/run/stream").get_data(as_text=True)

    from app.models import Ticket
    with app.app_context():
        t = app.db_session.get(Ticket, "GHS-0311")
        assert t.result == "Pinned the fetcher to the retrying client."
        assert t.report == ("The 429 path stored 0 stars for every user in the batch.\n"
                            "Pinning the retrying client keeps the previous value until the\n"
                            "window resets.")


def test_ticket_run_stream_acp_mode_prompt_carries_project_spec(client, app, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    seen = {}
    monkeypatch.setattr("app.acp.run_turn", _fake_turn("RESULT: done\nREPORT: done", capture=seen))

    from app.models import Project, Ticket
    with app.app_context():
        s = app.db_session
        ticket = s.get(Ticket, "GHS-0311")
        project = s.get(Project, ticket.project_key)
        summary, body = ticket.summary, ticket.body
        pname, pkey, pcontext, autonomy = (project.name, project.key,
                                           project.context, project.autonomy)

    client.get("/api/tickets/GHS-0311/run/stream").get_data(as_text=True)

    prompt = seen["text"]
    assert "GHS-0311" in prompt
    assert f"{pname} ({pkey})" in prompt
    assert pcontext in prompt
    assert f"Autonomy ceiling: {autonomy}" in prompt
    assert summary in prompt
    assert body in prompt


def test_ticket_run_stream_propose_ceiling_withholds_auto_approval(client, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    seen = {}
    monkeypatch.setattr("app.acp.run_turn", _fake_turn("RESULT: x\nREPORT: y", capture=seen))

    client.get("/api/tickets/EVC-0074/run/stream").get_data(as_text=True)   # evc → propose

    assert seen["auto_approve"] is False


def test_ticket_run_stream_full_ceiling_auto_approves(client, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    seen = {}
    monkeypatch.setattr("app.acp.run_turn", _fake_turn("RESULT: x\nREPORT: y", capture=seen))

    client.get("/api/tickets/GHS-0311/run/stream").get_data(as_text=True)   # ghstats → full

    assert seen["auto_approve"] is True


def test_ticket_run_stream_error_clears_stale_result_banner(client, app, monkeypatch):
    """A failed run must not leave the previous run's success banner standing."""
    import app.api.tickets as tickets_api
    from app.models import Ticket

    with app.app_context():
        assert app.db_session.get(Ticket, "GRD-0182").result   # seeded banner

    def boom(*a, **k):
        raise RuntimeError("hermes unreachable")
        yield  # pragma: no cover  (make it a generator)

    monkeypatch.setattr(tickets_api, "run_ticket", boom)
    client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)

    with app.app_context():
        t = app.db_session.get(Ticket, "GRD-0182")
        assert t.result is None
        assert t.report is None


def test_ticket_run_stream_acp_error_event_releases_the_ticket(client, app, monkeypatch):
    """acp_client reports transport failures as an `error` event rather than
    raising, so the stream must still unstick the ticket: left 'executing', the
    Launch button stays disabled and the run can never be retried."""
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")

    def failing_turn(text, hsid, model=None, history=None, auto_approve=True):
        yield {"type": "reasoning", "delta": "connecting"}
        yield {"type": "error", "message": "ssh down"}

    monkeypatch.setattr("app.acp.run_turn", failing_turn)

    client.post("/api/tickets/GRD-0182/launch")          # arms it: agent -> executing
    body = client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)
    assert "event: error" in body

    from app.models import AgentRun, Ticket
    with app.app_context():
        s = app.db_session
        t = s.get(Ticket, "GRD-0182")
        assert t.agent == "idle"
        assert t.result is None and t.report is None
        run = (s.query(AgentRun)
               .filter(AgentRun.ticket == "GRD-0182", AgentRun.kind == "execute")
               .order_by(AgentRun.position.desc()).first())
        assert run.status == "error"


def test_ticket_run_stream_unknown_ceiling_withholds_auto_approval(client, app, monkeypatch):
    """A ticket with no project has no declared ceiling, so the run must fail
    closed the way the mock's 'propose / unknown' branch already does."""
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    seen = {}
    monkeypatch.setattr("app.acp.run_turn", _fake_turn("RESULT: x\nREPORT: y", capture=seen))

    from app.models import Ticket
    with app.app_context():
        s = app.db_session
        s.get(Ticket, "GRD-0182").project_key = None
        s.commit()

    client.get("/api/tickets/GRD-0182/run/stream").get_data(as_text=True)

    assert seen["auto_approve"] is False
