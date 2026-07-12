def test_project_context_get_and_edit(client):
    r = client.get("/api/projects/merlin/context")
    assert r.status_code == 200
    assert r.get_json()["context"].startswith("# MERLIN")   # seeded starter content

    upd = client.put("/api/projects/merlin/context", json={"context": "# MERLIN\n\ncustom rules"})
    assert upd.status_code == 200
    assert upd.get_json()["context"] == "# MERLIN\n\ncustom rules"
    # persisted
    assert client.get("/api/projects/merlin/context").get_json()["context"] == "# MERLIN\n\ncustom rules"


def test_area_context_get_and_edit(client):
    r = client.get("/api/areas/ideas_lab/context")
    assert r.status_code == 200
    assert "IDEAS LAB" in r.get_json()["context"]

    upd = client.put("/api/areas/ideas_lab/context", json={"context": "lab notes"})
    assert upd.status_code == 200
    assert upd.get_json()["context"] == "lab notes"


def test_context_validation_and_404(client):
    assert client.put("/api/projects/merlin/context", json={"context": 123}).status_code == 400
    assert client.put("/api/areas/ideas_lab/context", json={}).status_code == 400
    assert client.get("/api/projects/nope/context").status_code == 404
    assert client.get("/api/areas/nope/context").status_code == 404
    assert client.put("/api/projects/nope/context", json={"context": "x"}).status_code == 404
