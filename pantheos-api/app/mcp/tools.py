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
from ..models import (AgentModel, AgentRun, Area, Container, DelphiMessage,
                      DelphiSession, Host, McpServer, MemoryFact, Project,
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
    body = (body or "").strip()
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
    # ``id`` is surfaced (additive, MCP-only) so update/delete_agent_run can
    # target a specific run; the REST/frontend shape is unaffected.
    return {"runs": [{"id": r.id, **r.to_dict()} for r in rows]}


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


# ============================================================ full CRUD
# Free rein over site data: create/update/delete for every entity. Deletes that
# would orphan children are refused with a blocker count (guard, not cascade);
# tickets/sessions cascade their own children via relationship config. Writes
# validate required fields, foreign keys, and the documented vocabularies only.
_AUTONOMY = {"propose", "auto_pr", "full"}
_STATUSES = {"go", "cau", "flt", "los"}


def _next_pos(session, model):
    return (session.query(func.max(model.position)).scalar() or 0) + 1


# ------------------------------------------------------------------- areas
def create_area(session, area_id, name, kind, active=True, context=None):
    area_id = (area_id or "").strip()
    name = (name or "").strip()
    if not area_id or not name:
        return {"error": "id and name required"}
    if session.get(Area, area_id) is not None:
        return {"error": "area exists", "id": area_id}
    a = Area(id=area_id, name=name, kind=(kind or "").strip(), active=bool(active),
             context=context, position=_next_pos(session, Area))
    session.add(a)
    session.flush()
    return {**a.to_dict(), "context": a.context}


def update_area(session, area_id, name=None, kind=None, active=None, context=None):
    a = session.get(Area, area_id)
    if a is None:
        return {"error": "unknown area", "id": area_id}
    for field, val in (("name", name), ("kind", kind), ("context", context)):
        if val is not None:
            setattr(a, field, val)
    if active is not None:
        a.active = bool(active)
    session.flush()
    return {**a.to_dict(), "context": a.context}


def delete_area(session, area_id):
    a = session.get(Area, area_id)
    if a is None:
        return {"error": "unknown area", "id": area_id}
    projects = session.query(func.count(Project.key)).filter(Project.area_id == area_id).scalar()
    tickets = session.query(func.count(Ticket.id)).filter(Ticket.area_id == area_id).scalar()
    if projects or tickets:
        return {"error": "area has dependents", "id": area_id,
                "projects": projects, "tickets": tickets}
    session.delete(a)
    session.flush()
    return {"deleted": area_id}


# ---------------------------------------------------------------- projects
def create_project(session, key, area_id, name, autonomy, status, blurb="",
                   users=None, repo=None, context=None):
    key = (key or "").strip()
    name = (name or "").strip()
    if not key or not name:
        return {"error": "key and name required"}
    if session.get(Project, key) is not None:
        return {"error": "project exists", "key": key}
    if session.get(Area, area_id) is None:
        return {"error": "unknown area", "id": area_id}
    if autonomy not in _AUTONOMY:
        return {"error": "invalid autonomy", "autonomy": autonomy}
    if status not in _STATUSES:
        return {"error": "invalid status", "status": status}
    p = Project(key=key, area_id=area_id, name=name, autonomy=autonomy, status=status,
                blurb=(blurb or ""), users=users, repo=repo, context=context,
                position=_next_pos(session, Project))
    session.add(p)
    session.flush()
    return {"key": p.key, **p.to_dict(), "context": p.context}


def update_project(session, key, name=None, area_id=None, autonomy=None, status=None,
                   blurb=None, users=None, repo=None, context=None):
    p = session.get(Project, key)
    if p is None:
        return {"error": "unknown project", "key": key}
    if autonomy is not None and autonomy not in _AUTONOMY:
        return {"error": "invalid autonomy", "autonomy": autonomy}
    if status is not None and status not in _STATUSES:
        return {"error": "invalid status", "status": status}
    if area_id is not None:
        if session.get(Area, area_id) is None:
            return {"error": "unknown area", "id": area_id}
        p.area_id = area_id
    for field, val in (("name", name), ("autonomy", autonomy), ("status", status),
                       ("blurb", blurb), ("users", users), ("repo", repo),
                       ("context", context)):
        if val is not None:
            setattr(p, field, val)
    session.flush()
    return {"key": p.key, **p.to_dict(), "context": p.context}


def delete_project(session, key):
    p = session.get(Project, key)
    if p is None:
        return {"error": "unknown project", "key": key}
    containers = session.query(func.count(Container.id)).filter(Container.project_key == key).scalar()
    tickets = session.query(func.count(Ticket.id)).filter(Ticket.project_key == key).scalar()
    if containers or tickets:
        return {"error": "project has dependents", "key": key,
                "containers": containers, "tickets": tickets}
    session.delete(p)
    session.flush()
    return {"deleted": key}


# ------------------------------------------------------- tickets: delete + kids
def delete_ticket(session, tid):
    t = session.get(Ticket, tid)
    if t is None:
        return {"error": "unknown ticket", "id": tid}
    session.delete(t)              # deps/links cascade via relationship config
    session.flush()
    return {"deleted": tid}


def _ticket_after_kid_edit(session, tid):
    t = session.get(Ticket, tid)
    session.refresh(t)
    return t.to_dict()


def update_dep(session, tid, dep_id, title=None, done=None):
    d = (session.query(TicketDep)
         .filter(TicketDep.ticket_id == tid, TicketDep.dep_id == dep_id).first())
    if d is None:
        return {"error": "unknown dep", "id": tid, "dep_id": dep_id}
    if title is not None:
        d.title = title
    if done is not None:
        d.done = bool(done)
    session.flush()
    return _ticket_after_kid_edit(session, tid)


def remove_dep(session, tid, dep_id):
    d = (session.query(TicketDep)
         .filter(TicketDep.ticket_id == tid, TicketDep.dep_id == dep_id).first())
    if d is None:
        return {"error": "unknown dep", "id": tid, "dep_id": dep_id}
    session.delete(d)
    session.flush()
    return _ticket_after_kid_edit(session, tid)


def update_ticket_link(session, tid, url, kind=None, label=None, new_url=None):
    link = (session.query(TicketLink)
            .filter(TicketLink.ticket_id == tid, TicketLink.url == url).first())
    if link is None:
        return {"error": "unknown link", "id": tid, "url": url}
    for field, val in (("kind", kind), ("label", label), ("url", new_url)):
        if val is not None:
            setattr(link, field, val)
    session.flush()
    return _ticket_after_kid_edit(session, tid)


def remove_ticket_link(session, tid, url):
    link = (session.query(TicketLink)
            .filter(TicketLink.ticket_id == tid, TicketLink.url == url).first())
    if link is None:
        return {"error": "unknown link", "id": tid, "url": url}
    session.delete(link)
    session.flush()
    return _ticket_after_kid_edit(session, tid)


# ------------------------------------------------------------------- hosts
def get_host(session, host_id):
    h = session.get(Host, host_id)
    if h is None:
        return {"error": "unknown host", "id": host_id}
    return h.to_dict()


def create_host(session, host_id, name, kind="", icon="", tag="", loc=""):
    host_id = (host_id or "").strip()
    name = (name or "").strip()
    if not host_id or not name:
        return {"error": "id and name required"}
    if session.get(Host, host_id) is not None:
        return {"error": "host exists", "id": host_id}
    h = Host(id=host_id, name=name, kind=kind or "", icon=icon or "", tag=tag or "",
             loc=loc or "", position=_next_pos(session, Host))
    session.add(h)
    session.flush()
    return h.to_dict()


def update_host(session, host_id, name=None, kind=None, icon=None, tag=None, loc=None):
    h = session.get(Host, host_id)
    if h is None:
        return {"error": "unknown host", "id": host_id}
    for field, val in (("name", name), ("kind", kind), ("icon", icon),
                       ("tag", tag), ("loc", loc)):
        if val is not None:
            setattr(h, field, val)
    session.flush()
    return h.to_dict()


def delete_host(session, host_id):
    h = session.get(Host, host_id)
    if h is None:
        return {"error": "unknown host", "id": host_id}
    containers = session.query(func.count(Container.id)).filter(Container.host_id == host_id).scalar()
    if containers:
        return {"error": "host has containers", "id": host_id, "containers": containers}
    session.delete(h)
    session.flush()
    return {"deleted": host_id}


# -------------------------------------------------------------- containers
_CONTAINER_FIELDS = ("project_key", "host_id", "role", "status", "cpu", "cpu_n",
                     "mem", "err", "rps", "p95", "restarts", "up", "image")


def create_container(session, container_id, project_key, host_id, role, status="go",
                     image="", cpu="0%", cpu_n=0, mem="0M", err="—", rps="0/s",
                     p95="0 ms", restarts=0, up="AOS"):
    container_id = (container_id or "").strip()
    if not container_id:
        return {"error": "id required"}
    if session.get(Container, container_id) is not None:
        return {"error": "container exists", "id": container_id}
    if session.get(Project, project_key) is None:
        return {"error": "unknown project", "key": project_key}
    if session.get(Host, host_id) is None:
        return {"error": "unknown host", "id": host_id}
    if status not in _STATUSES:
        return {"error": "invalid status", "status": status}
    c = Container(id=container_id, project_key=project_key, host_id=host_id,
                  role=role or "", status=status, cpu=cpu, cpu_n=cpu_n, mem=mem,
                  err=err, rps=rps, p95=p95, restarts=restarts, up=up,
                  image=image or "", position=_next_pos(session, Container))
    session.add(c)
    session.flush()
    return c.to_dict()


def update_container(session, container_id, **fields):
    c = session.get(Container, container_id)
    if c is None:
        return {"error": "unknown container", "id": container_id}
    if fields.get("status") is not None and fields["status"] not in _STATUSES:
        return {"error": "invalid status", "status": fields["status"]}
    if fields.get("project_key") is not None and session.get(Project, fields["project_key"]) is None:
        return {"error": "unknown project", "key": fields["project_key"]}
    if fields.get("host_id") is not None and session.get(Host, fields["host_id"]) is None:
        return {"error": "unknown host", "id": fields["host_id"]}
    for k in _CONTAINER_FIELDS:
        if fields.get(k) is not None:
            setattr(c, k, fields[k])
    session.flush()
    return c.to_dict()


def delete_container(session, container_id):
    c = session.get(Container, container_id)
    if c is None:
        return {"error": "unknown container", "id": container_id}
    session.delete(c)
    session.flush()
    return {"deleted": container_id}


# ------------------------------------------------------------------ memory
def update_memory_fact(session, text, new_text):
    new_text = (new_text or "").strip()
    if not new_text:
        return {"error": "new_text required"}
    f = session.query(MemoryFact).filter(MemoryFact.text == text).first()
    if f is None:
        return {"error": "unknown memory fact", "text": text}
    f.text = new_text
    session.flush()
    return {"memory": list_memory(session)["memory"], "updated": new_text}


def remove_memory_fact(session, text):
    f = session.query(MemoryFact).filter(MemoryFact.text == text).first()
    if f is None:
        return {"error": "unknown memory fact", "text": text}
    session.delete(f)
    session.flush()
    return {"memory": list_memory(session)["memory"], "removed": text}


# ---------------------------------------------------------- agent runs (logs)
def create_agent_run(session, ticket, kind, status, cost, when):
    ticket = (ticket or "").strip()
    if not ticket:
        return {"error": "ticket required"}
    r = AgentRun(ticket=ticket, kind=kind or "", status=status or "", cost=cost or "",
                 when=when or "", position=_next_pos(session, AgentRun))
    session.add(r)
    session.flush()
    return {"id": r.id, **r.to_dict()}


def update_agent_run(session, run_id, ticket=None, kind=None, status=None,
                     cost=None, when=None):
    r = session.get(AgentRun, run_id)
    if r is None:
        return {"error": "unknown run", "id": run_id}
    for field, val in (("ticket", ticket), ("kind", kind), ("status", status),
                       ("cost", cost), ("when", when)):
        if val is not None:
            setattr(r, field, val)
    session.flush()
    return {"id": r.id, **r.to_dict()}


def delete_agent_run(session, run_id):
    r = session.get(AgentRun, run_id)
    if r is None:
        return {"error": "unknown run", "id": run_id}
    session.delete(r)
    session.flush()
    return {"deleted": run_id}


# ---------------------------------------------------------- skills (DB rows)
def create_skill(session, skill_id, name, trigger="", desc="", on=True):
    skill_id = (skill_id or "").strip()
    name = (name or "").strip()
    if not skill_id or not name:
        return {"error": "id and name required"}
    if session.get(Skill, skill_id) is not None:
        return {"error": "skill exists", "id": skill_id}
    sk = Skill(id=skill_id, name=name, on=bool(on), trigger=trigger or "",
               desc=desc or "", position=_next_pos(session, Skill))
    session.add(sk)
    session.flush()
    return sk.to_dict()


def update_skill(session, skill_id, name=None, trigger=None, desc=None, on=None):
    sk = session.get(Skill, skill_id)
    if sk is None:
        return {"error": "unknown skill", "id": skill_id}
    for field, val in (("name", name), ("trigger", trigger), ("desc", desc)):
        if val is not None:
            setattr(sk, field, val)
    if on is not None:
        sk.on = bool(on)
    session.flush()
    return sk.to_dict()


def delete_skill(session, skill_id):
    sk = session.get(Skill, skill_id)
    if sk is None:
        return {"error": "unknown skill", "id": skill_id}
    session.delete(sk)
    session.flush()
    return {"deleted": skill_id}


# ---------------------------------------------------- connectors (McpServer)
def list_mcp_servers(session):
    rows = session.query(McpServer).order_by(McpServer.position).all()
    return {"mcp_servers": [m.to_dict() for m in rows]}


def get_mcp_server(session, server_id):
    m = session.get(McpServer, server_id)
    if m is None:
        return {"error": "unknown mcp server", "id": server_id}
    return m.to_dict()


def create_mcp_server(session, server_id, name, url="", tools="—", desc="", on=True):
    server_id = (server_id or "").strip()
    name = (name or "").strip()
    if not server_id or not name:
        return {"error": "id and name required"}
    if session.get(McpServer, server_id) is not None:
        return {"error": "mcp server exists", "id": server_id}
    m = McpServer(id=server_id, name=name, url=url or "", tools=tools or "—",
                  on=bool(on), desc=desc or "", position=_next_pos(session, McpServer))
    session.add(m)
    session.flush()
    return m.to_dict()


def update_mcp_server(session, server_id, name=None, url=None, tools=None,
                      desc=None, on=None):
    m = session.get(McpServer, server_id)
    if m is None:
        return {"error": "unknown mcp server", "id": server_id}
    for field, val in (("name", name), ("url", url), ("tools", tools), ("desc", desc)):
        if val is not None:
            setattr(m, field, val)
    if on is not None:
        m.on = bool(on)
    session.flush()
    return m.to_dict()


def delete_mcp_server(session, server_id):
    m = session.get(McpServer, server_id)
    if m is None:
        return {"error": "unknown mcp server", "id": server_id}
    session.delete(m)
    session.flush()
    return {"deleted": server_id}


# ------------------------------------------------------- models (AgentModel)
def list_agent_models(session):
    rows = session.query(AgentModel).order_by(AgentModel.position).all()
    return {"models": [m.to_dict() for m in rows]}


def get_agent_model(session, model_id):
    m = session.get(AgentModel, model_id)
    if m is None:
        return {"error": "unknown model", "id": model_id}
    return m.to_dict()


def create_agent_model(session, model_id, name, tag=""):
    model_id = (model_id or "").strip()
    name = (name or "").strip()
    if not model_id or not name:
        return {"error": "id and name required"}
    if session.get(AgentModel, model_id) is not None:
        return {"error": "model exists", "id": model_id}
    m = AgentModel(id=model_id, name=name, tag=tag or "",
                   position=_next_pos(session, AgentModel))
    session.add(m)
    session.flush()
    return m.to_dict()


def update_agent_model(session, model_id, name=None, tag=None):
    m = session.get(AgentModel, model_id)
    if m is None:
        return {"error": "unknown model", "id": model_id}
    if name is not None:
        m.name = name
    if tag is not None:
        m.tag = tag
    session.flush()
    return m.to_dict()


def delete_agent_model(session, model_id):
    m = session.get(AgentModel, model_id)
    if m is None:
        return {"error": "unknown model", "id": model_id}
    session.delete(m)
    session.flush()
    return {"deleted": model_id}


# ------------------------------------------------------ sessions / messages
def list_sessions(session):
    rows = session.query(DelphiSession).order_by(DelphiSession.position).all()
    return {"sessions": [{"id": s.id, "title": s.title, "ts": s.ts,
                          "hermes_session_id": s.hermes_session_id} for s in rows]}


def get_session(session, session_id):
    s = session.get(DelphiSession, session_id)
    if s is None:
        return {"error": "unknown session", "id": session_id}
    d = s.to_dict()
    # override with id-bearing messages so update/delete_message can target them
    d["msgs"] = [{"id": m.id, **m.to_dict()} for m in s.messages]
    return d


def create_session(session, session_id, title, ts="", hermes_session_id=None):
    session_id = (session_id or "").strip()
    title = (title or "").strip()
    if not session_id or not title:
        return {"error": "id and title required"}
    if session.get(DelphiSession, session_id) is not None:
        return {"error": "session exists", "id": session_id}
    s = DelphiSession(id=session_id, title=title, ts=ts or "",
                      hermes_session_id=hermes_session_id,
                      position=_next_pos(session, DelphiSession))
    session.add(s)
    session.flush()
    return s.to_dict()


def update_session(session, session_id, title=None, ts=None, hermes_session_id=None):
    s = session.get(DelphiSession, session_id)
    if s is None:
        return {"error": "unknown session", "id": session_id}
    for field, val in (("title", title), ("ts", ts),
                       ("hermes_session_id", hermes_session_id)):
        if val is not None:
            setattr(s, field, val)
    session.flush()
    return s.to_dict()


def delete_session(session, session_id):
    s = session.get(DelphiSession, session_id)
    if s is None:
        return {"error": "unknown session", "id": session_id}
    session.delete(s)             # messages cascade via relationship config
    session.flush()
    return {"deleted": session_id}


def add_message(session, session_id, who, text, reasoning=None, tools=None):
    s = session.get(DelphiSession, session_id)
    if s is None:
        return {"error": "unknown session", "id": session_id}
    text = (text or "").strip()
    if not text:
        return {"error": "text required"}
    pos = (session.query(func.max(DelphiMessage.position))
           .filter(DelphiMessage.session_id == session_id).scalar() or 0) + 1
    m = DelphiMessage(session_id=session_id, who=who or "", text=text,
                      reasoning=reasoning, tools=tools, position=pos)
    session.add(m)
    session.flush()
    return {"id": m.id, **m.to_dict()}


def update_message(session, message_id, who=None, text=None, reasoning=None, tools=None):
    m = session.get(DelphiMessage, message_id)
    if m is None:
        return {"error": "unknown message", "id": message_id}
    for field, val in (("who", who), ("text", text), ("reasoning", reasoning),
                       ("tools", tools)):
        if val is not None:
            setattr(m, field, val)
    session.flush()
    return {"id": m.id, **m.to_dict()}


def delete_message(session, message_id):
    m = session.get(DelphiMessage, message_id)
    if m is None:
        return {"error": "unknown message", "id": message_id}
    session.delete(m)
    session.flush()
    return {"deleted": message_id}
