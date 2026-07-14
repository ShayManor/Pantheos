"""A standalone SQLAlchemy session for the MCP process.

The MCP server runs outside Flask's request lifecycle, so it owns its own
engine/session bound to the same database as the API.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from ..config import Config

_engine = None
_Session = None


def _factory():
    """Lazily build (once) a scoped session bound to the configured database."""
    global _engine, _Session
    if _Session is None:
        _engine = create_engine(Config.DATABASE_URL, future=True)
        _Session = scoped_session(
            sessionmaker(bind=_engine, autoflush=False, future=True))
    return _Session


@contextmanager
def session_scope():
    """Yield a session; commit on success, roll back on error, always release."""
    s = _factory()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.remove()
