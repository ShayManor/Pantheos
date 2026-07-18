import os

from app import create_app

TEST_DB = os.environ.get(
    "PANTHEOS_TEST_DATABASE_URL",
    "postgresql+psycopg://shay@localhost:5432/pantheos_test",
)


def test_health(client):
    assert client.get("/api/health").get_json()["status"] == "ok"


def test_404_json(client):
    r = client.get("/api/nonexistent")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not found"


def test_reseed_allowed(client):
    r = client.post("/api/admin/reseed")
    assert r.status_code == 200
    assert r.get_json()["status"] == "reseeded"


def test_reseed_forbidden():
    app = create_app({"DATABASE_URL": TEST_DB, "ALLOW_RESEED": False})
    try:
        assert app.test_client().post("/api/admin/reseed").status_code == 403
    finally:
        app.db_engine.dispose()


def test_frontend_static_serving(tmp_path):
    """When FRONTEND_DIST is set, Flask serves the SPA at / while the API keeps
    priority (unmatched /api/* still 404s as JSON, not the index page)."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Pantheos</title>")
    (dist / "assets" / "app.js").write_text("console.log('hi')")
    app = create_app({"DATABASE_URL": TEST_DB, "FRONTEND_DIST": str(dist)})
    c = app.test_client()
    assert b"Pantheos" in c.get("/").data                       # index at /
    assert b"console.log" in c.get("/assets/app.js").data       # real asset
    assert b"Pantheos" in c.get("/unknown/route").data          # SPA fallback
    r = c.get("/api/does-not-exist")                            # API keeps priority
    assert r.status_code == 404 and r.is_json
    app.db_session.remove()
    app.db_engine.dispose()


def test_agent_run_transcript_roundtrip(session):
    from app.models import AgentRun
    r = AgentRun(ticket="GRD-0182", kind="execute", status="done",
                 cost="$0.04", when="Just now", position=99,
                 reasoning="thought", tools=["claude", "github"], output="# out")
    session.add(r)
    session.commit()
    d = r.to_dict()
    assert d["reasoning"] == "thought"
    assert d["tools"] == ["claude", "github"]
    assert d["output"] == "# out"
    # A bare run (no transcript) omits the optional keys, like DelphiMessage.
    bare = AgentRun(ticket="X", kind="execute", status="running",
                    cost="—", when="Just now", position=100)
    assert "reasoning" not in bare.to_dict()
    assert "output" not in bare.to_dict()
