import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import db, get_or_404
from .. import delphi as delphi_logic
from ..models import AgentModel, AgentRun, DelphiSession, McpServer, MemoryFact, Skill
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


@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    return jsonify(delphi_logic.reply(data.get("text", "")))


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
