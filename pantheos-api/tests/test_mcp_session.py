import pytest

from app.mcp import session as msession


def test_session_scope_commits(session, monkeypatch):
    monkeypatch.setattr(msession, "_factory", lambda: session)
    with msession.session_scope() as s:
        from app.models import MemoryFact
        s.add(MemoryFact(text="scope-commit", position=999))
    # committed + visible after the scope closed
    from app.models import MemoryFact
    assert session.query(MemoryFact).filter_by(text="scope-commit").count() == 1


def test_session_scope_rolls_back(session, monkeypatch):
    monkeypatch.setattr(msession, "_factory", lambda: session)
    with pytest.raises(RuntimeError):
        with msession.session_scope() as s:
            from app.models import MemoryFact
            s.add(MemoryFact(text="scope-rollback", position=998))
            raise RuntimeError("boom")
    from app.models import MemoryFact
    assert session.query(MemoryFact).filter_by(text="scope-rollback").count() == 0


def test_factory_is_lazy_singleton(monkeypatch):
    monkeypatch.setattr(msession, "_engine", None)
    monkeypatch.setattr(msession, "_Session", None)
    first = msession._factory()
    assert msession._factory() is first
