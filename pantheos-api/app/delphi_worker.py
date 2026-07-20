"""Background worker that drains the Delphi message queue.

A chat turn is processed out-of-band from the request that enqueued it, so a
closed tab (or a process restart) never loses or corrupts a turn. One daemon
thread claims queued assistant rows one at a time (global FIFO by position) and
fills them via ``acp.run_turn`` -- the same backend the synchronous endpoint used
to call inline. Claiming is atomic (``FOR UPDATE SKIP LOCKED``) so several
gunicorn workers can each run a drainer without double-processing a row.
"""
import threading
import time

from sqlalchemy import text as sql_text

from . import acp
from .models import DelphiMessage, DelphiSession

_FLUSH_INTERVAL = 0.5   # seconds between partial-text flushes while a turn runs
_IDLE_SLEEP = 1.0       # seconds to wait when the queue is empty


def _claim_next(session):
    """Atomically move the lowest-position queued assistant row to 'running'.

    Returns the claimed row, or None if the queue is empty. SKIP LOCKED keeps
    concurrent drainers from grabbing the same row.
    """
    row_id = session.execute(sql_text(
        "UPDATE delphi_messages SET status='running' "
        "WHERE id = (SELECT id FROM delphi_messages WHERE status='queued' "
        "ORDER BY position LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING id"
    )).scalar()
    session.commit()
    if row_id is None:
        return None
    return session.get(DelphiMessage, row_id)


def resume_interrupted(session):
    """Requeue rows left 'running' by a crash/restart. Returns the count reset."""
    n = (session.query(DelphiMessage)
         .filter(DelphiMessage.status == "running")
         .update({"status": "queued"}))
    session.commit()
    return n


def process_one(session):
    """Claim and fully process one queued turn. Returns True if one ran."""
    msg = _claim_next(session)
    if msg is None:
        return False

    sess = session.get(DelphiSession, msg.session_id)
    # The paired prompt is the nearest 'me' row just before this reply; history
    # is the prior *done* turns of the session, oldest-first (the current turn is
    # excluded -- it is passed as `text`, matching the old inline behavior).
    user_row = (session.query(DelphiMessage)
                .filter(DelphiMessage.session_id == msg.session_id,
                        DelphiMessage.position < msg.position,
                        DelphiMessage.who == "me")
                .order_by(DelphiMessage.position.desc()).first())
    text = user_row.text if user_row is not None else ""
    cutoff = user_row.position if user_row is not None else msg.position
    history = [
        {"role": "assistant" if m.who == "flight" else "user", "content": m.text}
        for m in session.query(DelphiMessage)
        .filter(DelphiMessage.session_id == msg.session_id,
                DelphiMessage.position < cutoff,
                DelphiMessage.status == "done")
        .order_by(DelphiMessage.position)
    ]

    final = None
    acc = ""
    last_flush = time.monotonic()
    try:
        for ev in acp.run_turn(text, sess.hermes_session_id, None, history):
            if ev["type"] == "text":
                acc += ev["delta"]
                now = time.monotonic()
                if now - last_flush >= _FLUSH_INTERVAL:
                    msg.text = acc
                    session.commit()
                    last_flush = now
            elif ev["type"] == "error":
                msg.text = f"⚠️ {ev.get('message') or 'Delphi error'}"
                msg.status = "error"
                session.commit()
                return True
            elif ev["type"] == "done":
                final = ev
    except Exception as exc:      # transport / spawn / protocol failure
        msg.text = f"⚠️ {exc}"
        msg.status = "error"
        session.commit()
        return True

    if final is not None:
        msg.reasoning = final.get("reasoning") or None
        msg.tools = final.get("tools") or None
        if final.get("hermes_session_id"):
            sess.hermes_session_id = final["hermes_session_id"]
    msg.text = final["text"] if final is not None else acc
    msg.status = "done"
    session.commit()
    return True


def start(app):  # pragma: no cover - background thread wiring
    """Spawn the daemon drain loop for this process."""
    def loop():
        with app.app_context():
            session = app.db_session
            try:
                resume_interrupted(session)
            except Exception:
                session.rollback()
            finally:
                session.remove()
        while True:
            ran = False
            with app.app_context():
                session = app.db_session
                try:
                    ran = process_one(session)
                except Exception:
                    session.rollback()
                finally:
                    session.remove()
            if not ran:
                time.sleep(_IDLE_SLEEP)

    t = threading.Thread(target=loop, name="delphi-worker", daemon=True)
    t.start()
    return t
