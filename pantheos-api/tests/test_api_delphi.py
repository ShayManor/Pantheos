def test_context(client):
    d = client.get("/api/delphi/context").get_json()
    assert len(d["models"]) == 3
    assert len(d["connectors"]) == 5
    assert d["connectors"][0]["name"] == "Pantheos"
    assert int(d["connectors"][0]["tools"]) >= 20
    assert len(d["skills"]) == 7
    assert {s["name"] for s in d["skills"]} == {"debug-issue", "fix-project",
        "triage-ticket", "research", "dispatch-agents", "analyze-project",
        "run-experiment"}
    assert len(d["memory"]) == 4
    assert len(d["runs"]) == 4
    assert len(d["sessions"]) == 3
    assert d["greeting"].startswith("Delphi online")
    s1 = next(s for s in d["sessions"] if s["id"] == "s1")
    assert any("tools" in m for m in s1["msgs"])       # flight message carries tools
    assert any("tools" not in m for m in s1["msgs"])   # user message does not


def test_draft_ticket(client):
    r = client.post("/api/delphi/draft_ticket", json={"title": "port to rubik pi"})
    assert r.status_code == 200
    d = r.get_json()
    assert d["project_key"] == "merlin"
    assert d["summary"]
    # empty body still returns a usable draft
    assert client.post("/api/delphi/draft_ticket", json={}).get_json()["title"]


def test_connector_crud(client):
    r = client.post("/api/delphi/connectors", json={"name": "MyConn"})
    assert r.status_code == 201
    body = r.get_json()
    cid, = (body["id"],)
    assert body["url"] == "custom"
    # new connector sorts to the front of the context list
    conns = client.get("/api/delphi/context").get_json()["connectors"]
    assert conns[0]["id"] == cid
    # blank name rejected
    assert client.post("/api/delphi/connectors", json={"name": "  "}).status_code == 400
    # toggle off, then a no-op patch (no 'on' key)
    assert client.patch(f"/api/delphi/connectors/{cid}", json={"on": False}).get_json()["on"] is False
    assert client.patch(f"/api/delphi/connectors/{cid}", json={}).status_code == 200
    # delete, then operations on a missing id 404
    assert client.delete(f"/api/delphi/connectors/{cid}").status_code == 200
    assert client.patch(f"/api/delphi/connectors/{cid}", json={"on": True}).status_code == 404
    assert client.delete("/api/delphi/connectors/NOPE").status_code == 404


def test_add_connector_with_url(client):
    r = client.post("/api/delphi/connectors", json={"name": "X", "url": "host:1"})
    assert r.get_json()["url"] == "host:1"


def test_connector_bridge_enabled(client, monkeypatch):
    """With the Hermes bridge on, connector edits route through it, not the DB."""
    from app import hermes_connectors as hc
    from app.models import McpServer
    monkeypatch.setattr(hc, "enabled", lambda: True)

    added = McpServer(id="exa", name="Exa", url="u", tools="—", on=True, desc="")
    monkeypatch.setattr(hc, "add", lambda *a, **k: added)
    r = client.post("/api/delphi/connectors", json={"name": "Exa", "url": "u", "token": "t"})
    assert r.status_code == 201 and r.get_json()["id"] == "exa"

    toggled = McpServer(id="github", name="GitHub", url="u", tools="47", on=False, desc="")
    monkeypatch.setattr(hc, "set_enabled", lambda *a, **k: toggled)
    r = client.patch("/api/delphi/connectors/github", json={"on": False})
    assert r.status_code == 200 and r.get_json()["on"] is False

    monkeypatch.setattr(hc, "remove", lambda *a, **k: None)
    assert client.delete("/api/delphi/connectors/github").status_code == 200


def test_connector_bridge_errors(client, monkeypatch):
    """A bridge SSH failure surfaces as 502 on add/toggle/delete."""
    from app import hermes_connectors as hc
    monkeypatch.setattr(hc, "enabled", lambda: True)

    def boom(*a, **k):
        raise hc.HermesError("ssh down")

    monkeypatch.setattr(hc, "add", boom)
    monkeypatch.setattr(hc, "set_enabled", boom)
    monkeypatch.setattr(hc, "remove", boom)
    assert client.post("/api/delphi/connectors", json={"name": "Z"}).status_code == 502
    assert client.patch("/api/delphi/connectors/github", json={"on": False}).status_code == 502
    assert client.delete("/api/delphi/connectors/github").status_code == 502


def test_skill_crud(client):
    r = client.post("/api/delphi/skills", json={"name": "my-skill"})
    assert r.status_code == 201
    sid = r.get_json()["id"]
    assert client.post("/api/delphi/skills", json={"name": ""}).status_code == 400
    assert client.patch(f"/api/delphi/skills/{sid}", json={"on": False}).get_json()["on"] is False
    assert client.patch(f"/api/delphi/skills/{sid}", json={}).status_code == 200
    assert client.delete(f"/api/delphi/skills/{sid}").status_code == 200
    assert client.patch(f"/api/delphi/skills/{sid}", json={"on": True}).status_code == 404
    assert client.delete("/api/delphi/skills/NOPE").status_code == 404


def test_message_reasoning_and_session_link(session):
    from app.models import DelphiSession, DelphiMessage
    s = DelphiSession(id="zz01", title="T", ts="Now", position=-1,
                      hermes_session_id="hs-abc")
    session.add(s)
    session.add(DelphiMessage(session_id="zz01", who="flight", text="hi",
                              reasoning="because", tools=["queue"], position=0))
    session.add(DelphiMessage(session_id="zz01", who="me", text="yo", position=1))
    session.commit()
    d = session.get(DelphiSession, "zz01").to_dict()
    assert d["hermes_session_id"] == "hs-abc"
    flight, me = d["msgs"]
    assert flight["reasoning"] == "because" and flight["tools"] == ["queue"]
    assert "reasoning" not in me  # unset reasoning is omitted


def test_session_crud(client):
    created = client.post("/api/delphi/sessions", json={"title": "My chat"})
    assert created.status_code == 201
    sid = created.get_json()["id"]
    # sorts to the front of the list
    assert client.get("/api/delphi/sessions").get_json()[0]["id"] == sid
    assert client.get(f"/api/delphi/sessions/{sid}").get_json()["title"] == "My chat"
    assert client.delete(f"/api/delphi/sessions/{sid}").status_code == 200
    assert client.get(f"/api/delphi/sessions/{sid}").status_code == 404
    assert client.delete(f"/api/delphi/sessions/{sid}").status_code == 404


def test_session_default_title(client):
    r = client.post("/api/delphi/sessions", json={})
    assert r.get_json()["title"] == "New chat"


def test_chat_enqueues_user_and_queued_placeholder(client):
    sid = client.post("/api/delphi/sessions", json={}).get_json()["id"]
    r = client.post("/api/delphi/chat",
                    json={"session_id": sid, "text": "what is due this week"})
    assert r.status_code == 201
    msgs = r.get_json()["msgs"]
    # a reserved me→flight pair; the reply is queued (empty) for the worker
    assert [m["who"] for m in msgs] == ["me", "flight"]
    assert msgs[0]["text"] == "what is due this week"
    assert msgs[1]["status"] == "queued" and msgs[1]["text"] == ""
    assert isinstance(msgs[1]["id"], int)
    # user rows carry no status/id in the served shape
    assert "status" not in msgs[0] and "id" not in msgs[0]


def test_chat_missing_session_404(client):
    assert client.post("/api/delphi/chat",
                       json={"session_id": "nope", "text": "hi"}).status_code == 404


def test_cancel_queued_message_removes_pair(client):
    sid = client.post("/api/delphi/sessions", json={}).get_json()["id"]
    fid = client.post("/api/delphi/chat",
                      json={"session_id": sid, "text": "one"}).get_json()["msgs"][1]["id"]
    assert client.delete(f"/api/delphi/messages/{fid}").status_code == 200
    # both the placeholder and its paired user row are gone
    assert client.get(f"/api/delphi/sessions/{sid}").get_json()["msgs"] == []
    # the row no longer exists
    assert client.delete(f"/api/delphi/messages/{fid}").status_code == 404


def test_cancel_rejects_non_queued(client, app):
    sid = client.post("/api/delphi/sessions", json={}).get_json()["id"]
    fid = client.post("/api/delphi/chat",
                      json={"session_id": sid, "text": "x"}).get_json()["msgs"][1]["id"]
    with app.app_context():
        from app.models import DelphiMessage
        app.db_session.get(DelphiMessage, fid).status = "running"
        app.db_session.commit()
    assert client.delete(f"/api/delphi/messages/{fid}").status_code == 409


def test_health(client):
    d = client.get("/api/delphi/health").get_json()
    assert d == {"mode": "mock", "ok": True}


def test_sync_models_refreshes_stale_catalog(session):
    from app.models import AgentModel
    from app.seed import sync_models

    # Simulate an existing DB that still holds the old model catalog.
    session.query(AgentModel).delete()
    session.add(AgentModel(id="hermes4", name="Hermes 4 70B", tag="old", position=0))
    session.commit()

    sync_models(session)

    ids = [m.id for m in session.query(AgentModel).order_by(AgentModel.position)]
    assert ids == ["gpt-5.6-terra", "gpt-5.6-luna", "zai/glm-5.2"]


def test_draft_ticket_uses_model_when_configured(client, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "openai")
    seen = {}

    def fake_draft(data, projects, areas):
        seen["projects"] = projects
        seen["areas"] = areas
        return {"title": "Modelled draft", "project_key": "merlin"}

    monkeypatch.setattr("app.openai_client.draft", fake_draft)
    d = client.post("/api/delphi/draft_ticket", json={"title": "port"}).get_json()
    assert d["title"] == "Modelled draft" and d["project_key"] == "merlin"
    assert "merlin" in seen["projects"] and seen["areas"]     # real DB options passed in


def test_draft_ticket_falls_back_on_model_error(client, monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "openai")

    def boom(data, projects, areas):
        raise RuntimeError("model down")

    monkeypatch.setattr("app.openai_client.draft", boom)
    d = client.post("/api/delphi/draft_ticket", json={"title": "port to rubik pi"}).get_json()
    assert d["project_key"] == "merlin"     # canned draft on failure
