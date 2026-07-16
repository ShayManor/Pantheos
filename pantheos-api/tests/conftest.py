import os

import pytest

from app import create_app
from app.seed import reset_db, seed, seed_sample

TEST_DB = os.environ.get(
    "PANTHEOS_TEST_DATABASE_URL",
    "postgresql+psycopg://shay@localhost:5432/pantheos_test",
)


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
