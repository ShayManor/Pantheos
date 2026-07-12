def test_context(client):
    d = client.get("/api/delphi/context").get_json()
    assert len(d["models"]) == 5
    assert len(d["connectors"]) == 7
    assert len(d["skills"]) == 5
    assert len(d["memory"]) == 4
    assert len(d["runs"]) == 4
    assert len(d["sessions"]) == 3
    assert d["greeting"].startswith("Delphi online")
    s1 = next(s for s in d["sessions"] if s["id"] == "s1")
    assert any("tools" in m for m in s1["msgs"])       # flight message carries tools
    assert any("tools" not in m for m in s1["msgs"])   # user message does not


def test_chat(client):
    r = client.post("/api/delphi/chat", json={"text": "what is due this week"})
    assert "calendar" in r.get_json()["tools"]
    assert client.post("/api/delphi/chat", json={}).get_json()["tools"] == []


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
