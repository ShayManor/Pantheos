from flask import Blueprint, jsonify, request

from . import db, get_or_404
from ..models import Project, Ticket

bp = Blueprint("tickets", __name__, url_prefix="/api")

_LIFECYCLES = {"backburner", "queued", "active", "blocked", "archived"}


@bp.get("/tickets")
def list_tickets():
    rows = db().query(Ticket).order_by(Ticket.position).all()
    return jsonify([t.to_dict() for t in rows])


@bp.get("/tickets/<tid>")
def get_ticket(tid):
    return jsonify(get_or_404(Ticket, tid).to_dict())


@bp.post("/tickets/<tid>/launch")
def launch_ticket(tid):
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
