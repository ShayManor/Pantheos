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
