import re

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import db, get_or_404
from .. import scoring
from ..models import Area, Project, Ticket

bp = Blueprint("tickets", __name__, url_prefix="/api")

_LIFECYCLES = {"backburner", "queued", "active", "blocked", "archived"}
_PRIORITIES = {0, 1, 2, 3}


@bp.get("/tickets")
def list_tickets():
    rows = db().query(Ticket).order_by(Ticket.position).all()
    return jsonify([t.to_dict() for t in rows])


@bp.post("/tickets")
def create_ticket():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400

    project_key = data.get("project_key") or None
    area_id = data.get("area_id") or None
    if project_key:
        project = db().get(Project, project_key)
        if project is None:
            return jsonify({"error": "unknown project"}), 400
        area_id = project.area_id
    if area_id is None:
        return jsonify({"error": "area or project required"}), 400
    if db().get(Area, area_id) is None:
        return jsonify({"error": "unknown area"}), 400

    pri = data.get("pri", 2)
    if pri not in _PRIORITIES:
        return jsonify({"error": "invalid priority"}), 400

    deadline = data.get("deadline_hours")
    effort = data.get("effort_hours")
    summary = (data.get("summary") or "").strip() or title
    body = (data.get("body") or "").strip() or summary
    score = scoring.compute_score(pri, scoring.own_urgency(deadline, effort))

    # Unique id: a 3-letter prefix + a number above every existing suffix.
    prefix = re.sub(r"[^A-Za-z]", "", project_key or area_id)[:3].upper() or "TKT"
    nums = [int(re.sub(r"\D", "", t.id) or 0) for t in db().query(Ticket.id).all()]
    number = (max(nums) + 1) if nums else 1
    tid = f"{prefix}-{number:04d}"
    max_pos = db().query(func.max(Ticket.position)).scalar() or 0

    ticket = Ticket(
        id=tid, project_key=project_key, area_id=area_id, title=title, pri=pri,
        deadline_hours=deadline, effort_hours=effort, score=score,
        due=scoring.due_display(deadline), hot=scoring.is_hot(deadline),
        life="queued", agent="idle", source=data.get("source") or "manual",
        summary=summary, body=body, report=None, result=None, position=max_pos + 1)
    db().add(ticket)
    db().commit()
    return jsonify(ticket.to_dict()), 201


@bp.get("/tickets/<tid>")
def get_ticket(tid):
    return jsonify(get_or_404(Ticket, tid).to_dict())


@bp.post("/tickets/<tid>/launch")
def launch_ticket(tid):
    # TODO: real agent execution is not yet implemented. This only flips the
    # ticket to "executing" and returns a toast — nothing dispatches Delphi or
    # runs the work. Wiring this to the agent (see mcp/tools.run_claude_code) is
    # the remaining piece.
    t = get_or_404(Ticket, tid)
    t.agent = "executing"
    if t.life == "backburner":
        t.life = "queued"
    db().commit()
    project = db().get(Project, t.project_key) if t.project_key else None
    if project and project.autonomy == "propose":
        toast = f"Delphi dispatched on {tid} · PR-only, stops for review"
    else:
        toast = f"Delphi dispatched on {tid} · Claude Code session spawning"
    return jsonify({"ticket": t.to_dict(), "toast": toast})


@bp.delete("/tickets/<tid>")
def delete_ticket(tid):
    t = get_or_404(Ticket, tid)
    db().delete(t)
    db().commit()
    return "", 204


@bp.patch("/tickets/<tid>")
def update_ticket(tid):
    t = get_or_404(Ticket, tid)
    data = request.get_json(silent=True) or {}
    life = data.get("life")
    if life is not None:
        if life not in _LIFECYCLES:
            return jsonify({"error": "invalid lifecycle"}), 400
        t.life = life
    db().commit()
    return jsonify(t.to_dict())
