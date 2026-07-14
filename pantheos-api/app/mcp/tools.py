"""Pure MCP tool functions: ``fn(session, ...) -> dict``.

No FastMCP imports here — every function is directly unit-testable against a DB
session. ``server.py`` wraps these for the wire. Mutating tools reuse
``scoring``/``metrics`` and emit the same shapes as the models' ``to_dict()``.
"""
import os
import re
import subprocess

from sqlalchemy import func

from .. import metrics, scoring
from ..models import (AgentRun, Area, Container, Host, MemoryFact, Project,
                      Skill, Ticket, TicketDep, TicketLink)


# --------------------------------------------------------------- grounding
def get_project_spec(session, key):
    """The agent's grounding entry point: a project's spec + autonomy ceiling."""
    p = session.get(Project, key)
    if p is None:
        return {"error": "unknown project", "key": key}
    return {
        "key": p.key, "name": p.name, "area": p.area.name, "autonomy": p.autonomy,
        "status": p.status, "repo": p.repo, "blurb": p.blurb,
        "context": p.context, "area_context": p.area.context,
    }


def list_projects(session):
    rows = session.query(Project).order_by(Project.position).all()
    return {"projects": [{"key": p.key, **p.to_dict()} for p in rows]}


def get_project(session, key):
    p = session.get(Project, key)
    if p is None:
        return {"error": "unknown project", "key": key}
    return {"key": p.key, **p.to_dict(), "context": p.context}


def list_areas(session):
    rows = session.query(Area).order_by(Area.position).all()
    return {"areas": [{**a.to_dict(), "context": a.context} for a in rows]}


def get_area(session, area_id):
    a = session.get(Area, area_id)
    if a is None:
        return {"error": "unknown area", "id": area_id}
    return {**a.to_dict(), "context": a.context}


_LIFECYCLES = {"backburner", "queued", "active", "blocked", "archived"}
_AGENT_STATES = {"idle", "enriching", "executing", "needs_review"}
_PRIORITIES = {0, 1, 2, 3}


# ----------------------------------------------------------------- tickets
def list_tickets(session, project=None, life=None, agent=None, area=None, hot=None):
    q = session.query(Ticket).order_by(Ticket.position)
    if project is not None:
        q = q.filter(Ticket.project_key == project)
    if life is not None:
        q = q.filter(Ticket.life == life)
    if agent is not None:
        q = q.filter(Ticket.agent == agent)
    if area is not None:
        q = q.filter(Ticket.area_id == area)
    if hot is not None:
        q = q.filter(Ticket.hot == bool(hot))
    return {"tickets": [t.to_dict() for t in q.all()]}


def get_ticket(session, tid):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    return t.to_dict()


def _rescore(t):
    """Recompute derived score/due/hot from the ticket's own urgency."""
    urg = scoring.own_urgency(t.deadline_hours, t.effort_hours)
    t.score = scoring.compute_score(t.pri, urg)
    t.due = scoring.due_display(t.deadline_hours)
    t.hot = scoring.is_hot(t.deadline_hours)


def create_ticket(session, title, area_id=None, project_key=None, pri=2,
                  summary=None, body=None, deadline_hours=None, effort_hours=None,
                  source="delphi"):
    title = (title or "").strip()
    if not title:
        return {"error": "title required"}
    if project_key:
        project = session.get(Project, project_key)
        if project is None:
            return {"error": "unknown project", "key": project_key}
        area_id = project.area_id
    if area_id is None:
        return {"error": "area or project required"}
    if session.get(Area, area_id) is None:
        return {"error": "unknown area", "id": area_id}
    if pri not in _PRIORITIES:
        return {"error": "invalid priority", "pri": pri}

    summary = (summary or "").strip() or title
    body = (body or "").strip() or summary
    prefix = re.sub(r"[^A-Za-z]", "", project_key or area_id)[:3].upper() or "TKT"
    nums = [int(re.sub(r"\D", "", tid) or 0) for (tid,) in session.query(Ticket.id).all()]
    number = (max(nums) + 1) if nums else 1
    tid = f"{prefix}-{number:04d}"
    max_pos = session.query(func.max(Ticket.position)).scalar() or 0
    t = Ticket(
        id=tid, project_key=project_key, area_id=area_id, title=title, pri=pri,
        deadline_hours=deadline_hours, effort_hours=effort_hours,
        score=scoring.compute_score(pri, scoring.own_urgency(deadline_hours, effort_hours)),
        due=scoring.due_display(deadline_hours), hot=scoring.is_hot(deadline_hours),
        life="queued", agent="idle", source=source, summary=summary, body=body,
        report=None, result=None, position=max_pos + 1)
    session.add(t)
    session.flush()
    return t.to_dict()


_EDITABLE = ("title", "pri", "summary", "body", "report", "result",
             "deadline_hours", "effort_hours")
_SCORING_INPUTS = ("pri", "deadline_hours", "effort_hours")


def update_ticket(session, tid, **fields):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    if fields.get("pri", t.pri) not in _PRIORITIES:
        return {"error": "invalid priority", "pri": fields["pri"]}
    for k in _EDITABLE:
        if k in fields and fields[k] is not None:
            setattr(t, k, fields[k])
    # Only rescore when a scoring input actually changed. A text-only edit must
    # not overwrite the ticket's stored score (which may carry seed-time
    # dependency propagation that own-urgency alone would discard).
    if any(fields.get(k) is not None for k in _SCORING_INPUTS):
        _rescore(t)
    session.flush()
    return t.to_dict()


def move_ticket(session, tid, life):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    if life not in _LIFECYCLES:
        return {"error": "invalid lifecycle", "life": life}
    t.life = life
    session.flush()
    return t.to_dict()


def set_agent_state(session, tid, agent):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    if agent not in _AGENT_STATES:
        return {"error": "invalid agent state", "agent": agent}
    t.agent = agent
    session.flush()
    return t.to_dict()


def _tail(session, model, ticket_id):
    return (session.query(func.max(model.position))
            .filter(model.ticket_id == ticket_id).scalar() or 0) + 1


def add_ticket_link(session, tid, kind, label, url):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    session.add(TicketLink(ticket_id=tid, kind=kind, label=label, url=url,
                           position=_tail(session, TicketLink, tid)))
    session.flush()
    session.refresh(t)
    return t.to_dict()


def add_dep(session, tid, dep_id, title, done=False):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    session.add(TicketDep(ticket_id=tid, dep_id=dep_id, title=title, done=done,
                          position=_tail(session, TicketDep, tid)))
    session.flush()
    session.refresh(t)
    return t.to_dict()


# ----------------------------------------------------------------- monitor
def list_hosts(session):
    rows = session.query(Host).order_by(Host.position).all()
    return {"hosts": [h.to_dict() for h in rows]}


def list_containers(session, project=None, host=None, status=None):
    q = session.query(Container).order_by(Container.position)
    if project is not None:
        q = q.filter(Container.project_key == project)
    if host is not None:
        q = q.filter(Container.host_id == host)
    if status is not None:
        q = q.filter(Container.status == status)
    return {"containers": [c.to_dict() for c in q.all()]}


def get_container(session, cid):
    c = session.get(Container, cid)
    if c is None:
        return {"error": "unknown container", "id": cid}
    return c.to_dict()


def get_container_logs(session, cid):
    c = session.get(Container, cid)
    if c is None:
        return {"error": "unknown container", "id": cid}
    return {"lines": metrics.container_logs(c)}


def restart_container(session, cid):
    """Mocked fleet action: clear the fault, bump the restart counter."""
    c = session.get(Container, cid)
    if c is None:
        return {"error": "unknown container", "id": cid}
    c.status = "go"
    c.up = "AOS"
    c.err = "—"
    c.restarts += 1
    session.flush()
    return c.to_dict()


# ------------------------------------------------------- memory / runs / skills
def list_memory(session):
    rows = session.query(MemoryFact).order_by(MemoryFact.position).all()
    return {"memory": [f.text for f in rows]}


def add_memory_fact(session, text):
    text = (text or "").strip()
    if not text:
        return {"error": "text required"}
    pos = (session.query(func.max(MemoryFact.position)).scalar() or 0) + 1
    session.add(MemoryFact(text=text, position=pos))
    session.flush()
    return {"memory": list_memory(session)["memory"], "added": text}


def list_recent_runs(session):
    rows = session.query(AgentRun).order_by(AgentRun.position).all()
    return {"runs": [r.to_dict() for r in rows]}


def list_skills(session):
    rows = session.query(Skill).order_by(Skill.position).all()
    return {"skills": [s.to_dict() for s in rows]}


def get_skill(session, name):
    from . import skills as skill_files      # lazy: skill loader (Task 7)
    return skill_files.load_skill(name)


# --------------------------------------------------------------- real work
def _workspace_for(project_key):
    root = os.environ.get("PANTHEOS_WORKSPACE_ROOT", "/tmp/pantheos-workspaces")
    return os.path.join(root, project_key)


def run_claude_code(session, project_key, task, dry_run=False):
    """Delegate real code work to Claude Code, gated by the project's autonomy.

    ``propose`` (or ``dry_run``) returns a plan without executing. ``auto_pr`` /
    ``full`` shell out to ``claude -p`` in the project workspace.
    """
    p = session.get(Project, project_key)
    if p is None:
        return {"error": "unknown project", "key": project_key}

    prompt = (
        f"You are Delphi working in project {p.name} ({project_key}).\n\n"
        f"Read and obey this project spec before acting:\n{p.context}\n\n"
        f"Autonomy ceiling: {p.autonomy}\n\nTask:\n{task}\n"
    )
    workspace = _workspace_for(project_key)
    if dry_run or p.autonomy == "propose":
        return {"project_key": project_key, "autonomy": p.autonomy, "mode": "plan",
                "workspace": workspace, "prompt": prompt,
                "note": "propose/dry_run — plan only, no execution",
                "would_run": ["claude", "-p", prompt]}

    if not os.path.isdir(workspace):
        return {"project_key": project_key, "mode": "error",
                "error": f"workspace not found: {workspace}"}
    timeout = float(os.environ.get("PANTHEOS_CLAUDE_TIMEOUT", "300"))
    try:
        proc = subprocess.run(["claude", "-p", prompt], cwd=workspace,
                              capture_output=True, text=True, timeout=timeout,
                              check=False)
    except FileNotFoundError:
        return {"project_key": project_key, "mode": "error",
                "error": "claude binary not found on PATH"}
    return {"project_key": project_key, "autonomy": p.autonomy, "mode": "executed",
            "workspace": workspace, "exit_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr}
