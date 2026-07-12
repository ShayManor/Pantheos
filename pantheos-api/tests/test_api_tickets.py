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
