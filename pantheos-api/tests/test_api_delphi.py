def test_context(client):
    d = client.get("/api/delphi/context").get_json()
    assert len(d["models"]) == 3
    assert len(d["connectors"]) == 1
    assert d["connectors"][0]["name"] == "Pantheos"
    assert int(d["connectors"][0]["tools"]) >= 20
    assert len(d["skills"]) == 3
    assert {s["name"] for s in d["skills"]} == {"debug-issue", "fix-project", "triage-ticket"}
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


def _sse_events(resp):
    """Parse an SSE body into [(event, json-data-str), ...]."""
    import json
    out = []
    for frame in resp.get_data(as_text=True).split("\n\n"):
        if not frame.strip():
            continue
        ev = data = None
        for line in frame.splitlines():
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        out.append((ev, json.loads(data)))
    return out


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


def test_chat_stream_persists_and_streams(client):
    sid = client.post("/api/delphi/sessions", json={}).get_json()["id"]
    resp = client.post("/api/delphi/chat/stream",
                       json={"session_id": sid, "text": "what is due this week"})
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"
    events = _sse_events(resp)
    types = [e for e, _ in events]
    assert types[0] == "reasoning" and types[-1] == "done"
    done = events[-1][1]
    # persisted: user msg + assistant msg with reasoning + tools + hermes id
    sess = client.get(f"/api/delphi/sessions/{sid}").get_json()
    assert sess["hermes_session_id"] == done["hermes_session_id"]
    whos = [m["who"] for m in sess["msgs"]]
    assert whos == ["me", "flight"]
    assert sess["msgs"][1]["reasoning"] == done["reasoning"]
    assert sess["msgs"][1]["tools"] == ["calendar", "brightspace", "queue"]


def test_chat_stream_missing_session_404(client):
    assert client.post("/api/delphi/chat/stream",
                       json={"session_id": "nope", "text": "hi"}).status_code == 404


def test_chat_stream_transport_error(client, monkeypatch):
    sid = client.post("/api/delphi/sessions", json={}).get_json()["id"]

    def boom(text, hermes_session_id, model=None):
        raise RuntimeError("transport down")

    monkeypatch.setattr("app.acp.run_turn", boom)
    resp = client.post("/api/delphi/chat/stream",
                       json={"session_id": sid, "text": "hi"})
    events = _sse_events(resp)
    assert events[-1] == ("error", {"type": "error", "message": "transport down"})
    # nothing persisted for the assistant turn on failure
    whos = [m["who"] for m in client.get(f"/api/delphi/sessions/{sid}").get_json()["msgs"]]
    assert whos == ["me"]


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
    assert ids == ["gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6-sol"]
