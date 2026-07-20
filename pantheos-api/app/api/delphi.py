import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import db, get_or_404
from .. import delphi as delphi_logic
from .. import hermes_connectors
from ..models import (AgentModel, AgentRun, Area, DelphiMessage, DelphiSession,
                      McpServer, MemoryFact, Project, Skill)
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


@bp.post("/chat")
def chat():
    """Enqueue a user turn. Persists the user row plus a queued assistant
    placeholder (both position-reserved in one commit, guaranteeing me→flight
    ordering) and returns immediately; the background worker fills the reply."""
    data = request.get_json(silent=True) or {}
    sess = get_or_404(DelphiSession, data.get("session_id"))
    text = (data.get("text") or "").strip()
    base = _tail_position(DelphiMessage)
    db().add(DelphiMessage(session_id=sess.id, who="me", text=text,
                           status="done", position=base))
    db().add(DelphiMessage(session_id=sess.id, who="flight", text="",
                           status="queued", position=base + 1))
    db().commit()
    return jsonify(get_or_404(DelphiSession, sess.id).to_dict()), 201


@bp.delete("/messages/<int:mid>")
def cancel_message(mid):
    """Cancel a still-queued turn: remove the assistant placeholder and its
    paired user row. Rejected (409) once the turn is running or done."""
    msg = get_or_404(DelphiMessage, mid)
    if msg.who != "flight" or (msg.status or "done") != "queued":
        return jsonify({"error": "only queued messages can be cancelled"}), 409
    user_row = (db().query(DelphiMessage)
                .filter(DelphiMessage.session_id == msg.session_id,
                        DelphiMessage.position < msg.position,
                        DelphiMessage.who == "me")
                .order_by(DelphiMessage.position.desc()).first())
    if user_row is not None:
        db().delete(user_row)
    db().delete(msg)
    db().commit()
    return jsonify({"status": "cancelled"})


@bp.post("/draft_ticket")
def draft_ticket():
    import os
    data = request.get_json(silent=True) or {}
    if os.environ.get("DELPHI_ACP_MODE", "mock") != "mock":
        s = db()
        projects = {p.key: p.name for p in s.query(Project)}
        areas = {a.id: a.name for a in s.query(Area)}
        try:
            from .. import openai_client
            return jsonify(openai_client.draft(data, projects=projects, areas=areas))
        except Exception:
            pass   # any model/network failure falls back to the canned draft
    return jsonify(delphi_logic.draft_ticket(data))


# ------------------------------------------------------------- connectors
@bp.post("/connectors")
def add_connector():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    url = (data.get("url") or "").strip() or "custom"
    if hermes_connectors.enabled():
        try:
            srv = hermes_connectors.add(db(), name, url,
                                        (data.get("token") or "").strip() or None)
        except hermes_connectors.HermesError as e:
            return jsonify({"error": str(e)}), 502
        return jsonify(srv.to_dict()), 201
    srv = McpServer(id=_new_id(), name=name, url=url, tools="—", on=True,
                    desc="Custom connector", position=_front_position(McpServer))
    db().add(srv)
    db().commit()
    return jsonify(srv.to_dict()), 201


@bp.patch("/connectors/<sid>")
def toggle_connector(sid):
    srv = get_or_404(McpServer, sid)
    data = request.get_json(silent=True) or {}
    if "on" not in data:
        return jsonify(srv.to_dict())
    on = bool(data["on"])
    if hermes_connectors.enabled():
        try:
            srv = hermes_connectors.set_enabled(db(), sid, on)
        except hermes_connectors.HermesError as e:
            return jsonify({"error": str(e)}), 502
        return jsonify(srv.to_dict())
    srv.on = on
    db().commit()
    return jsonify(srv.to_dict())


@bp.delete("/connectors/<sid>")
def delete_connector(sid):
    srv = get_or_404(McpServer, sid)
    if hermes_connectors.enabled():
        try:
            hermes_connectors.remove(db(), sid)
        except hermes_connectors.HermesError as e:
            return jsonify({"error": str(e)}), 502
        return jsonify({"status": "deleted"})
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
