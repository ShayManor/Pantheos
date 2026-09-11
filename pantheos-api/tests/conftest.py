import os

import pytest

from app import create_app
from app.seed import reset_db, seed, seed_sample

TEST_DB = os.environ.get(
    "PANTHEOS_TEST_DATABASE_URL",
    "postgresql+psycopg://shay@localhost:5432/pantheos_test",
)


@pytest.fixture(autouse=True)
def no_agent_host(monkeypatch):
    """Keep the run prompt's host probe off the network.

    Without an ssh transport the probe short-circuits, which is how a dev box
    behaves anyway. Left unset, the default transport points at the real minipc
    and the suite would reach it on every acp-mode test.
    """
    monkeypatch.setenv("DELPHI_ACP_CMD", "hermes acp")


@pytest.fixture()
def app():
    application = create_app({"DATABASE_URL": TEST_DB, "ALLOW_RESEED": True})
    reset_db(application.db_engine)
    seed(application.db_session)
    seed_sample(application.db_session)
    application.db_session.remove()
    yield application
    application.db_session.remove()
    application.db_engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    """A DB session inside an app context (for direct model tests)."""
    with app.app_context():
        yield app.db_session


@pytest.fixture()
def auth_app():
    """An app with the Firebase gate switched on. The default `app` fixture
    leaves it off so the rest of the suite is unaffected."""
    application = create_app({
        "DATABASE_URL": TEST_DB,
        "FIREBASE_PROJECT_ID": "pantheos-8d962",
        "FIREBASE_API_KEY": "test-api-key",
        "FIREBASE_AUTH_DOMAIN": "pantheos-8d962.firebaseapp.com",
        "ALLOWED_EMAILS": "shay.manor@gmail.com",
        "SERVICE_TOKEN": "svc-secret",
        "AUTH_DISABLED": False,
    })
    reset_db(application.db_engine)
    seed(application.db_session)
    application.db_session.remove()
    yield application
    application.db_session.remove()
    application.db_engine.dispose()
