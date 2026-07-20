from app import delphi_worker
from app.models import DelphiMessage, DelphiSession


def _queue_turn(session, sid="w1", user="hello", pos=0, hermes=None):
    """Insert a session (if new) plus a done user row + a queued flight reply."""
    if session.get(DelphiSession, sid) is None:
        session.add(DelphiSession(id=sid, title="T", ts="Now", position=-1,
                                  hermes_session_id=hermes))
    session.add(DelphiMessage(session_id=sid, who="me", text=user,
                              status="done", position=pos))
    flight = DelphiMessage(session_id=sid, who="flight", text="",
                           status="queued", position=pos + 1)
    session.add(flight)
    session.commit()
    return flight


def test_process_one_fills_reply_and_marks_done(session):
    flight = _queue_turn(session, user="what is due this week")
    fid = flight.id
    assert delphi_worker.process_one(session) is True
    row = session.get(DelphiMessage, fid)
    assert row.status == "done"
    assert "Priority math" in row.text          # the deterministic mock answer
    assert row.reasoning and row.tools
    # a fresh session gets Hermes' returned id threaded onto it
    assert session.get(DelphiSession, "w1").hermes_session_id == "mock-session"


def test_process_one_returns_false_on_empty_queue(session):
    assert delphi_worker.process_one(session) is False


def test_process_one_claims_lowest_position_first(session, monkeypatch):
    seen = []

    def spy(text, hermes_session_id, model=None, history=None):
        seen.append(text)
        yield {"type": "done", "text": "ok", "reasoning": "", "tools": [],
               "hermes_session_id": "s"}

    monkeypatch.setattr("app.acp.run_turn", spy)
    session.add(DelphiSession(id="c1", title="T", ts="Now", position=-1))
    session.add(DelphiMessage(session_id="c1", who="me", text="first",
                              status="done", position=0))
    session.add(DelphiMessage(session_id="c1", who="flight", text="",
                              status="queued", position=1))
    session.add(DelphiMessage(session_id="c1", who="me", text="second",
                              status="done", position=2))
    session.add(DelphiMessage(session_id="c1", who="flight", text="",
                              status="queued", position=3))
    session.commit()
    delphi_worker.process_one(session)
    assert seen == ["first"]                     # lowest-position turn drained first


def test_process_one_flushes_partial_text(session, monkeypatch):
    # A zero interval forces a mid-stream flush so the growing text is committed.
    monkeypatch.setattr(delphi_worker, "_FLUSH_INTERVAL", 0)
    flight = _queue_turn(session)
    assert delphi_worker.process_one(session) is True
    row = session.get(DelphiMessage, flight.id)
    assert row.status == "done" and row.text


def test_process_one_error_event_marks_error_and_continues(session, monkeypatch):
    def gen(text, hermes_session_id, model=None, history=None):
        yield {"type": "error", "message": "boom"}

    monkeypatch.setattr("app.acp.run_turn", gen)
    flight = _queue_turn(session)
    assert delphi_worker.process_one(session) is True
    row = session.get(DelphiMessage, flight.id)
    assert row.status == "error" and "boom" in row.text


def test_process_one_exception_marks_error(session, monkeypatch):
    def boom(text, hermes_session_id, model=None, history=None):
        raise RuntimeError("transport down")

    monkeypatch.setattr("app.acp.run_turn", boom)
    flight = _queue_turn(session)
    assert delphi_worker.process_one(session) is True
    row = session.get(DelphiMessage, flight.id)
    assert row.status == "error" and "transport down" in row.text


def test_history_threads_prior_done_turns(session, monkeypatch):
    captured = {}

    def spy(text, hermes_session_id, model=None, history=None):
        captured["text"] = text
        captured["history"] = history
        yield {"type": "done", "text": "ok", "reasoning": "", "tools": [],
               "hermes_session_id": hermes_session_id or "s"}

    monkeypatch.setattr("app.acp.run_turn", spy)

    # Turn 1: no prior context; the paired prompt is passed as text.
    _queue_turn(session, sid="h1", user="my name is Shay", pos=0)
    delphi_worker.process_one(session)
    assert captured["text"] == "my name is Shay" and captured["history"] == []

    # Turn 2: the first turn replays as oldest-first history; the current turn is
    # excluded (passed as text).
    session.add(DelphiMessage(session_id="h1", who="me", text="what is my name",
                              status="done", position=2))
    session.add(DelphiMessage(session_id="h1", who="flight", text="",
                              status="queued", position=3))
    session.commit()
    delphi_worker.process_one(session)
    assert captured["text"] == "what is my name"
    assert captured["history"] == [
        {"role": "user", "content": "my name is Shay"},
        {"role": "assistant", "content": "ok"},
    ]


def test_resume_interrupted_requeues_running(session):
    session.add(DelphiSession(id="r1", title="T", ts="Now", position=-1))
    session.add(DelphiMessage(session_id="r1", who="flight", text="x",
                              status="running", position=1))
    session.commit()
    assert delphi_worker.resume_interrupted(session) == 1
    row = session.query(DelphiMessage).filter_by(session_id="r1").one()
    assert row.status == "queued"
