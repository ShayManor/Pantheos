import json
import re

from flask import Blueprint, Response, jsonify, request, stream_with_context
from sqlalchemy import func

from . import db, get_or_404
from .. import scoring
from ..models import AgentRun, Area, Project, Ticket
from ..ticket_run import run_ticket

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


@bp.get("/tickets/<tid>/run/stream")
def ticket_run_stream(tid):
    t = get_or_404(Ticket, tid)
    # Capture primitives before streaming: stream_with_context resumes the
    # generator after the request context is torn down and re-pushed, by which
    # point lazy ORM access on `t` would raise DetachedInstanceError.
    title, area = t.title, t.area.name
    project = db().get(Project, t.project_key) if t.project_key else None
    autonomy = project.autonomy if project else None

    run = (db().query(AgentRun)
           .filter(AgentRun.ticket == tid, AgentRun.kind == "execute",
                   AgentRun.status == "running")
           .order_by(AgentRun.position.desc()).first())
    if run is None:
        pos = (db().query(func.max(AgentRun.position)).scalar() or 0) + 1
        run = AgentRun(ticket=tid, kind="execute", status="running",
                       cost="—", when="Just now", position=pos)
        db().add(run)
        db().commit()
    run_id = run.id

    def generate():
        final = None
        try:
            for ev in run_ticket(tid, title, area, autonomy):
                if ev["type"] == "done":
                    final = ev
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        except Exception as exc:  # surface run failures to the UI
            err = {"type": "error", "message": str(exc)}
            yield f"event: error\ndata: {json.dumps(err)}\n\n"
            r = db().get(AgentRun, run_id)
            r.status = "error"
            tk = db().get(Ticket, tid)
            tk.agent = "idle"
            db().commit()
        if final is not None:
            r = db().get(AgentRun, run_id)
            r.reasoning = final["reasoning"]
            r.tools = final["tools"]
            r.output = final["text"]
            r.cost = final["cost"]
            r.status = "done"
            tk = db().get(Ticket, tid)
            tk.agent = "needs_review"
            tk.report = final["report"]
            tk.result = final["result"]
            db().commit()

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@bp.get("/tickets/<tid>/runs")
def ticket_runs(tid):
    get_or_404(Ticket, tid)
    rows = (db().query(AgentRun)
            .filter(AgentRun.ticket == tid)
            .order_by(AgentRun.position.desc()).all())
    return jsonify([r.to_dict() for r in rows])


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
