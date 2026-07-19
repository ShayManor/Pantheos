"""Build the mock DB from seed_data, computing derived scores at seed time."""
from . import scoring
from . import seed_data as S
from .models import (
    AgentModel, AgentRun, Area, Base, Container, DelphiMessage, DelphiSession,
    Host, LogLine, McpServer, MemoryFact, Project, Skill, Ticket, TicketDep, TicketLink,
)


_CEILINGS = {
    "propose": "Branch + PR only — never touch main; hard-stop at needs_review.",
    "auto_pr": "Commit + PR; self-merge only on green CI.",
    "full": "Commit to main; self-archive on completion.",
}


def _project_context(p):
    return (
        f"# {p['name']}\n\n{p['blurb']}\n\n"
        f"## Autonomy\n{p['autonomy']} — {_CEILINGS[p['autonomy']]}\n\n"
        f"## Repo\n{p['repo'] or '—'}\n\n"
        f"## Notes\n" + "".join(f"- {n}\n" for n in p["notes"])
    )


def _area_context(a):
    return (
        f"# {a['name']}\n\n"
        f"Working context for the {a['name']} area ({a['kind']}).\n\n"
        f"## Notes\n- Shared conventions across every project and ticket in this area.\n"
    )


def sync_models(session):
    """Refresh the agent-model catalog to match the code.

    Models are a fixed, non-user-editable catalog (the UI only *selects* one),
    so replace ``agent_models`` on every boot. On an existing DB — where the
    full seed is skipped — this keeps the selector, and the model ids sent to
    the API, in step with the current MODELS list, instead of offering stale
    ids the backend can no longer serve.
    """
    session.query(AgentModel).delete()
    for i, mo in enumerate(S.MODELS):
        session.add(AgentModel(id=mo["id"], name=mo["name"], tag=mo["tag"], position=i))
    session.commit()


def seed_container_logs(session):
    """Insert deterministic mock log history for any container lacking it.

    Idempotent across seed + seed_sample: each pass only fills containers that
    have no rows yet, so seed() covers the base set and seed_sample() covers the
    demo set. Source is 'mock'; real 'caddy' rows come only from log_ingest.
    """
    from . import metrics
    have = {cid for (cid,) in session.query(LogLine.container_id).distinct()}
    for c in session.query(Container).all():
        if c.id in have:
            continue
        session.add_all([
            LogLine(container_id=c.id, source="mock", ts=ts, lvl=lvl, msg=msg)
            for ts, lvl, msg in metrics.container_log_stream(c)])
    session.commit()


def reset_db(engine):
    """Drop and recreate every table atomically — one transaction, so a
    concurrent reader (e.g. a lingering request from a just-closed page) never
    sees a half-dropped schema (`relation "x" does not exist`)."""
    with engine.begin() as conn:
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)


def seed(session):
    """Insert the real, stable scaffolding into empty tables.

    Live content (tickets, Delphi sessions, agent runs) is created at runtime,
    not seeded. Tests and the E2E reseed layer demo content on top via
    ``seed_sample``.
    """
    for i, a in enumerate(S.AREAS):
        session.add(Area(id=a["id"], name=a["name"], kind=a["kind"], active=True,
                        context=_area_context(a), position=i))
    session.flush()

    for i, p in enumerate(S.PROJECTS):
        session.add(Project(key=p["key"], area_id=p["area_id"], name=p["name"],
                            autonomy=p["autonomy"], status=p["status"], users=p["users"],
                            blurb=p["blurb"], repo=p["repo"], context=_project_context(p), position=i))
    session.flush()

    for i, h in enumerate(S.HOSTS):
        session.add(Host(id=h["id"], name=h["name"], kind=h["kind"], icon=h["icon"],
                        tag=h["tag"], loc=h["loc"], position=i))
    session.flush()
    for i, c in enumerate(S.CONTAINERS):
        session.add(Container(id=c["id"], project_key=c["proj"], host_id=c["host"], role=c["role"],
                             status=c["status"], cpu=c["cpu"], cpu_n=c["cpu_n"], mem=c["mem"],
                             err=c["err"], rps=c["rps"], p95=c["p95"], restarts=c["restarts"],
                             up=c["up"], image=c["image"], position=i))

    from .mcp.server import TOOL_COUNT
    for i, m in enumerate(S.MCP_SERVERS):
        tools = str(TOOL_COUNT) if m["id"] == "pantheos" else m["tools"]
        session.add(McpServer(id=m["id"], name=m["name"], url=m["url"], tools=tools,
                             on=m["on"], desc=m["desc"], position=i))
    for i, f in enumerate(S.MEMORY_FACTS):
        session.add(MemoryFact(text=f, position=i))
    for i, mo in enumerate(S.MODELS):
        session.add(AgentModel(id=mo["id"], name=mo["name"], tag=mo["tag"], position=i))

    session.commit()
    seed_container_logs(session)


def seed_sample(session):
    """Layer demo content (tickets, extra hosts/containers, Delphi history) on
    top of ``seed``. For tests and the ALLOW_RESEED-gated reseed endpoint only —
    never the production/dev DB, so the shipped app stays free of mock data."""
    from . import sample_data as SS

    rows = [{"id": t["id"], "pri": t["pri"], "deadline_hours": t["deadline_hours"],
             "effort_hours": t["effort_hours"], "dep_ids": [d["id"] for d in t["deps"]]}
            for t in SS.SAMPLE_TICKETS]
    scores = scoring.score_tickets(rows)
    for i, t in enumerate(SS.SAMPLE_TICKETS):
        session.add(Ticket(
            id=t["id"], project_key=t["proj"], area_id=t["area_id"], title=t["title"],
            pri=t["pri"], deadline_hours=t["deadline_hours"], effort_hours=t["effort_hours"],
            score=scores[t["id"]], due=scoring.due_display(t["deadline_hours"]),
            hot=scoring.is_hot(t["deadline_hours"]), life=t["life"], agent=t["agent"],
            source=t["source"], summary=t["summary"], body=t["body"], report=t["report"],
            result=t["result"], position=i))
    session.flush()
    for t in SS.SAMPLE_TICKETS:
        for j, d in enumerate(t["deps"]):
            session.add(TicketDep(ticket_id=t["id"], dep_id=d["id"], title=d["title"],
                                  done=d["done"], position=j))
        for j, l in enumerate(t["links"]):
            session.add(TicketLink(ticket_id=t["id"], kind=l["kind"], label=l["label"],
                                   url=l["url"], position=j))

    base_h = len(S.HOSTS)
    for i, h in enumerate(SS.SAMPLE_HOSTS):
        session.add(Host(id=h["id"], name=h["name"], kind=h["kind"], icon=h["icon"],
                        tag=h["tag"], loc=h["loc"], position=base_h + i))
    session.flush()
    base_c = len(S.CONTAINERS)
    for i, c in enumerate(SS.SAMPLE_CONTAINERS):
        session.add(Container(id=c["id"], project_key=c["proj"], host_id=c["host"], role=c["role"],
                             status=c["status"], cpu=c["cpu"], cpu_n=c["cpu_n"], mem=c["mem"],
                             err=c["err"], rps=c["rps"], p95=c["p95"], restarts=c["restarts"],
                             up=c["up"], image=c["image"], position=base_c + i))

    for i, sk in enumerate(SS.SAMPLE_SKILLS):
        session.add(Skill(id=sk["id"], name=sk["name"], on=sk["on"], trigger=sk["trigger"],
                         desc=sk["desc"], position=i))
    for i, r in enumerate(SS.SAMPLE_RUNS):
        session.add(AgentRun(ticket=r["ticket"], kind=r["kind"], status=r["status"],
                            cost=r["cost"], when=r["when"], position=i))
    for i, sess in enumerate(SS.SAMPLE_SESSIONS):
        session.add(DelphiSession(id=sess["id"], title=sess["title"], ts=sess["ts"], position=i))
    session.flush()
    for sess in SS.SAMPLE_SESSIONS:
        for j, msg in enumerate(sess["msgs"]):
            session.add(DelphiMessage(session_id=sess["id"], who=msg["who"], text=msg["text"],
                                      tools=msg.get("tools"), position=j))

    session.commit()
    seed_container_logs(session)
