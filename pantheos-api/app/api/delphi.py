import json
import uuid

from flask import Blueprint, Response, jsonify, request, stream_with_context
from sqlalchemy import func

from . import db, get_or_404
from .. import acp
from .. import delphi as delphi_logic
from ..models import (AgentModel, AgentRun, DelphiMessage, DelphiSession,
                      McpServer, MemoryFact, Skill)
from ..seed_data import GREETING

bp = Blueprint("delphi", __name__, url_prefix="/api/delphi")


def _new_id():
    return uuid.uuid4().hex[:8]


def _front_position(model):
    """One below the current minimum, so new rows sort to the front."""
    return (db().query(func.min(model.position)).scalar() or 0) - 1


@bp.get("/context")
def context():
    s = db()
    return jsonify({
        "greeting": GREETING,
        "models": [m.to_dict() for m in s.query(AgentModel).order_by(AgentModel.position)],
        "sessions": [x.to_dict() for x in s.query(DelphiSession).order_by(DelphiSession.position)],
        "connectors": [c.to_dict() for c in s.query(McpServer).order_by(McpServer.position)],
        "skills": [k.to_dict() for k in s.query(Skill).order_by(Skill.position)],
        "memory": [f.text for f in s.query(MemoryFact).order_by(MemoryFact.position)],
        "runs": [r.to_dict() for r in s.query(AgentRun).order_by(AgentRun.position)],
    })


def _tail_position(model):
    """One above the current maximum, so a row sorts to the end."""
    return (db().query(func.max(model.position)).scalar() or 0) + 1


@bp.get("/health")
def health():
    import os
    return jsonify({"mode": os.environ.get("DELPHI_ACP_MODE", "mock"), "ok": True})


@bp.post("/sessions")
def create_session():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "New chat").strip() or "New chat"
    sess = DelphiSession(id=_new_id(), title=title, ts="Just now",
                         position=_front_position(DelphiSession))
    db().add(sess)
    db().commit()
    return jsonify(sess.to_dict()), 201


@bp.get("/sessions")
def list_sessions():
    rows = db().query(DelphiSession).order_by(DelphiSession.position)
    return jsonify([s.to_dict() for s in rows])


@bp.get("/sessions/<sid>")
def get_session(sid):
    return jsonify(get_or_404(DelphiSession, sid).to_dict())


@bp.delete("/sessions/<sid>")
def delete_session(sid):
    sess = get_or_404(DelphiSession, sid)
    db().delete(sess)
    db().commit()
    return jsonify({"status": "deleted"})


@bp.post("/chat/stream")
def chat_stream():
    data = request.get_json(silent=True) or {}
    sess = get_or_404(DelphiSession, data.get("session_id"))
    text = (data.get("text") or "").strip()
    # Captured before the commit below expires `sess`: the streaming generator
    # resumes after the request context has been torn down and re-pushed by
    # stream_with_context, by which point ORM attribute access on `sess`
    # would raise DetachedInstanceError.
    sess_id = sess.id
    hermes_session_id = sess.hermes_session_id

    # Persist the user turn immediately.
    db().add(DelphiMessage(session_id=sess_id, who="me", text=text,
                           position=_tail_position(DelphiMessage)))
    db().commit()

    def generate():
        final = None
        try:
            for ev in acp.run_turn(text, hermes_session_id):
                if ev["type"] == "done":
                    final = ev
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        except Exception as exc:  # surface transport failures to the UI
            err = {"type": "error", "message": str(exc)}
            yield f"event: error\ndata: {json.dumps(err)}\n\n"
        # Persist the assistant turn (whatever completed).
        if final is not None:
            if final.get("hermes_session_id"):
                db().get(DelphiSession, sess_id).hermes_session_id = final["hermes_session_id"]
            db().add(DelphiMessage(
                session_id=sess_id, who="flight", text=final["text"],
                reasoning=final.get("reasoning") or None,
                tools=final.get("tools") or None,
                position=_tail_position(DelphiMessage)))
            db().commit()

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@bp.post("/draft_ticket")
def draft_ticket():
    data = request.get_json(silent=True) or {}
    return jsonify(delphi_logic.draft_ticket(data))


# ------------------------------------------------------------- connectors
@bp.post("/connectors")
def add_connector():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    url = (data.get("url") or "").strip() or "custom"
    srv = McpServer(id=_new_id(), name=name, url=url, tools="—", on=True,
                    desc="Custom connector", position=_front_position(McpServer))
    db().add(srv)
    db().commit()
    return jsonify(srv.to_dict()), 201


@bp.patch("/connectors/<sid>")
def toggle_connector(sid):
    srv = get_or_404(McpServer, sid)
    data = request.get_json(silent=True) or {}
    if "on" in data:
        srv.on = bool(data["on"])
    db().commit()
    return jsonify(srv.to_dict())


@bp.delete("/connectors/<sid>")
def delete_connector(sid):
    srv = get_or_404(McpServer, sid)
    db().delete(srv)
    db().commit()
    return jsonify({"status": "deleted"})


# ------------------------------------------------------------- skills
@bp.post("/skills")
def add_skill():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    skill = Skill(id=_new_id(), name=name, on=True, trigger="manual",
                  desc="Custom skill", position=_front_position(Skill))
    db().add(skill)
    db().commit()
    return jsonify(skill.to_dict()), 201


@bp.patch("/skills/<sid>")
def toggle_skill(sid):
    skill = get_or_404(Skill, sid)
    data = request.get_json(silent=True) or {}
    if "on" in data:
        skill.on = bool(data["on"])
    db().commit()
    return jsonify(skill.to_dict())


@bp.delete("/skills/<sid>")
def delete_skill(sid):
    skill = get_or_404(Skill, sid)
    db().delete(skill)
    db().commit()
    return jsonify({"status": "deleted"})
