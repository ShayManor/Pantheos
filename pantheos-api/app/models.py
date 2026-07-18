"""SQLAlchemy models — the real schema from docs/spec.md section 1.

``to_dict`` methods emit exactly the shapes the React frontend (code.jsx)
consumes, so the UI is fed by the API without reshaping on the client.
"""
from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from . import scoring


class Base(DeclarativeBase):
    pass


class Area(Base):
    __tablename__ = "areas"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)          # lab | club | class | personal
    active = Column(Boolean, nullable=False, default=True)
    context = Column(Text, nullable=True)          # per-area CLAUDE.md (agent context)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "kind": self.kind, "active": self.active}


class Project(Base):
    __tablename__ = "projects"
    key = Column(String, primary_key=True)
    area_id = Column(String, ForeignKey("areas.id"), nullable=False)
    name = Column(String, nullable=False)
    autonomy = Column(String, nullable=False)      # propose | auto_pr | full
    status = Column(String, nullable=False)        # go | cau | flt | los
    users = Column(Integer, nullable=True)
    blurb = Column(Text, nullable=False)
    repo = Column(String, nullable=True)
    context = Column(Text, nullable=True)          # per-project CLAUDE.md (agent context)
    position = Column(Integer, nullable=False, default=0)

    area = relationship("Area")

    def to_dict(self):
        return {
            "name": self.name,
            "area": self.area.name,
            "autonomy": self.autonomy,
            "status": self.status,
            "users": self.users,
            "blurb": self.blurb,
            "repo": self.repo,
        }


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True)
    project_key = Column(String, ForeignKey("projects.key"), nullable=True)
    area_id = Column(String, ForeignKey("areas.id"), nullable=False)
    title = Column(String, nullable=False)
    pri = Column(Integer, nullable=False)          # importance 0..3
    deadline_hours = Column(Float, nullable=True)  # hours from seed anchor
    effort_hours = Column(Float, nullable=True)
    score = Column(Float, nullable=False)          # derived (spec 1.5)
    due = Column(String, nullable=True)            # derived display label
    hot = Column(Boolean, nullable=False, default=False)
    life = Column(String, nullable=False)          # backburner|queued|active|blocked|archived
    agent = Column(String, nullable=False)         # idle|enriching|executing|needs_review
    source = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    report = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    area = relationship("Area")
    deps = relationship("TicketDep", cascade="all, delete-orphan",
                        order_by="TicketDep.position", backref="ticket")
    links = relationship("TicketLink", cascade="all, delete-orphan",
                        order_by="TicketLink.position", backref="ticket")

    def to_dict(self):
        return {
            "id": self.id,
            "proj": self.project_key,
            "title": self.title,
            "pri": self.pri,
            "due": self.due,
            "hot": self.hot,
            "score": scoring.format_score(self.score),
            "life": self.life,
            "agent": self.agent,
            "source": self.source,
            "summary": self.summary,
            "body": self.body,
            "report": self.report,
            "result": self.result,
            "effort": f"{int(self.effort_hours)}h" if self.effort_hours else None,
            "area": self.area.name,
            "deps": [d.to_dict() for d in self.deps],
            "links": [l.to_dict() for l in self.links],
        }


class TicketDep(Base):
    __tablename__ = "ticket_deps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    dep_id = Column(String, nullable=False)        # referenced ticket id (may not exist)
    title = Column(String, nullable=False)
    done = Column(Boolean, nullable=False, default=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.dep_id, "title": self.title, "done": self.done}


class TicketLink(Base):
    __tablename__ = "ticket_links"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    kind = Column(String, nullable=False)
    label = Column(String, nullable=False)
    url = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"kind": self.kind, "label": self.label, "url": self.url}


class Host(Base):
    __tablename__ = "hosts"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)          # always_on | intermittent
    icon = Column(String, nullable=False)          # lucide component name
    tag = Column(String, nullable=False)
    loc = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "kind": self.kind,
                "icon": self.icon, "tag": self.tag, "loc": self.loc}


class Container(Base):
    __tablename__ = "containers"
    id = Column(String, primary_key=True)
    project_key = Column(String, ForeignKey("projects.key"), nullable=False)
    host_id = Column(String, ForeignKey("hosts.id"), nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)        # go | cau | flt | los
    cpu = Column(String, nullable=False)
    cpu_n = Column(Integer, nullable=False)
    mem = Column(String, nullable=False)
    err = Column(String, nullable=False)
    rps = Column(String, nullable=False)
    p95 = Column(String, nullable=False)
    restarts = Column(Integer, nullable=False)
    up = Column(String, nullable=False)            # AOS | LOS
    image = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id, "proj": self.project_key, "host": self.host_id,
            "role": self.role, "status": self.status, "cpu": self.cpu,
            "cpuN": self.cpu_n, "mem": self.mem, "err": self.err, "rps": self.rps,
            "p95": self.p95, "restarts": self.restarts, "up": self.up, "image": self.image,
        }


class McpServer(Base):
    __tablename__ = "mcp_servers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    tools = Column(String, nullable=False)
    on = Column(Boolean, nullable=False, default=True)
    desc = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "url": self.url,
                "tools": self.tools, "on": self.on, "desc": self.desc}


class Skill(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    on = Column(Boolean, nullable=False, default=True)
    trigger = Column(String, nullable=False)
    desc = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "on": self.on,
                "trigger": self.trigger, "desc": self.desc}


class MemoryFact(Base):
    __tablename__ = "memory_facts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False, default=0)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket = Column(String, nullable=False)
    kind = Column(String, nullable=False)          # enrich | execute
    status = Column(String, nullable=False)
    cost = Column(String, nullable=False)
    when = Column(String, nullable=False)
    reasoning = Column(Text, nullable=True)
    tools = Column(JSON, nullable=True)
    output = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        d = {"ticket": self.ticket, "kind": self.kind,
             "status": self.status, "cost": self.cost, "when": self.when}
        if self.reasoning:
            d["reasoning"] = self.reasoning
        if self.tools:
            d["tools"] = self.tools
        if self.output:
            d["output"] = self.output
        return d


class AgentModel(Base):
    __tablename__ = "agent_models"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "tag": self.tag}


class DelphiSession(Base):
    __tablename__ = "delphi_sessions"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    ts = Column(String, nullable=False)
    hermes_session_id = Column(String, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    messages = relationship("DelphiMessage", cascade="all, delete-orphan",
                            order_by="DelphiMessage.position", backref="session")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "ts": self.ts,
                "hermes_session_id": self.hermes_session_id,
                "msgs": [m.to_dict() for m in self.messages]}


class DelphiMessage(Base):
    __tablename__ = "delphi_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("delphi_sessions.id"), nullable=False)
    who = Column(String, nullable=False)           # me | flight
    text = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    tools = Column(JSON, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        d = {"who": self.who, "text": self.text}
        if self.reasoning:
            d["reasoning"] = self.reasoning
        if self.tools:
            d["tools"] = self.tools
        return d
