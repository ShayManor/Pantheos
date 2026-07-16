"""FastMCP wiring: register every tool, carry the grounding system prompt.

Thin wrappers open a ``session_scope()`` and delegate to ``tools.py``. Keeping
them one-liners means importing this module (which runs registration) covers
them; a test exercises each through a scoped test session.
"""
import os

from mcp.server.fastmcp import FastMCP

from . import skills, tools
from .session import session_scope

INSTRUCTIONS = """\
You are Delphi, operating the Pantheos "Life OS" through these tools.

Grounding rules — non-negotiable:
- Before acting on any project, call get_project_spec(project_key) and obey the
  project's spec and autonomy ceiling (propose = PR-only; auto_pr = PR + green-CI
  self-merge; full = commit to main). Autonomy is a hard ceiling, not a hint.
- Ground every factual claim in a tool result. Never answer about a ticket,
  container, or project from memory — call the tool and read the result.
- For code changes, delegate to run_claude_code; never claim work merged when the
  project's autonomy only allows a proposal.
- When stuck, read the matching skill (get_skill: debug-issue, fix-project,
  triage-ticket, research, dispatch-agents, analyze-project, run-experiment) and
  follow it.
- You have full create/update/delete over every dashboard entity — areas,
  projects, tickets, hosts, containers, connectors, skills, memory, models,
  runs, and sessions. This data free rein does NOT lift the autonomy ceiling:
  shipping code still goes through run_claude_code, gated by the project's
  autonomy. A delete that would orphan children (e.g. an area with projects) is
  refused — remove the children first.
"""

# host/port only matter for the streamable-http transport (the compose `mcp`
# service); stdio ignores them.
mcp = FastMCP("Pantheos", instructions=INSTRUCTIONS,
              host=os.environ.get("PANTHEOS_MCP_HOST", "127.0.0.1"),
              port=int(os.environ.get("PANTHEOS_MCP_PORT", "8001")))


# --- grounding / projects
@mcp.tool()
def get_project_spec(project_key: str) -> dict:
    """Read a project's spec + autonomy ceiling. Call this before acting."""
    with session_scope() as s:
        return tools.get_project_spec(s, project_key)


@mcp.tool()
def list_projects() -> dict:
    """List every project with status and autonomy."""
    with session_scope() as s:
        return tools.list_projects(s)


@mcp.tool()
def get_project(project_key: str) -> dict:
    """One project's details, including its spec context."""
    with session_scope() as s:
        return tools.get_project(s, project_key)


@mcp.tool()
def list_areas() -> dict:
    """List life areas with their shared context."""
    with session_scope() as s:
        return tools.list_areas(s)


@mcp.tool()
def get_area(area_id: str) -> dict:
    """One area's details and context."""
    with session_scope() as s:
        return tools.get_area(s, area_id)


# --- tickets
@mcp.tool()
def list_tickets(project: str = None, life: str = None, agent: str = None,
                 area: str = None, hot: bool = None) -> dict:
    """List tickets, optionally filtered by project/life/agent/area/hot."""
    with session_scope() as s:
        return tools.list_tickets(s, project, life, agent, area, hot)


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Full ticket detail: body, report, result, deps, links."""
    with session_scope() as s:
        return tools.get_ticket(s, ticket_id)


@mcp.tool()
def create_ticket(title: str, area_id: str = None, project_key: str = None,
                  pri: int = 2, summary: str = None, body: str = None,
                  deadline_hours: float = None, effort_hours: float = None,
                  source: str = "delphi") -> dict:
    """Create a ticket (derived score computed). Give area_id or project_key."""
    with session_scope() as s:
        return tools.create_ticket(s, title, area_id, project_key, pri, summary,
                                    body, deadline_hours, effort_hours, source)


@mcp.tool()
def update_ticket(ticket_id: str, title: str = None, pri: int = None,
                  summary: str = None, body: str = None, report: str = None,
                  result: str = None, deadline_hours: float = None,
                  effort_hours: float = None) -> dict:
    """Edit a ticket; score/due/hot are recomputed."""
    with session_scope() as s:
        return tools.update_ticket(
            s, ticket_id, title=title, pri=pri, summary=summary, body=body,
            report=report, result=result, deadline_hours=deadline_hours,
            effort_hours=effort_hours)


@mcp.tool()
def move_ticket(ticket_id: str, life: str) -> dict:
    """Set lifecycle: backburner|queued|active|blocked|archived."""
    with session_scope() as s:
        return tools.move_ticket(s, ticket_id, life)


@mcp.tool()
def set_agent_state(ticket_id: str, agent: str) -> dict:
    """Set agent state: idle|enriching|executing|needs_review."""
    with session_scope() as s:
        return tools.set_agent_state(s, ticket_id, agent)


@mcp.tool()
def add_ticket_link(ticket_id: str, kind: str, label: str, url: str) -> dict:
    """Attach a link (PR/issue/doc) to a ticket."""
    with session_scope() as s:
        return tools.add_ticket_link(s, ticket_id, kind, label, url)


@mcp.tool()
def add_dep(ticket_id: str, dep_id: str, title: str, done: bool = False) -> dict:
    """Add a dependency (blocker) to a ticket."""
    with session_scope() as s:
        return tools.add_dep(s, ticket_id, dep_id, title, done)


# --- monitor
@mcp.tool()
def list_hosts() -> dict:
    """List fleet hosts."""
    with session_scope() as s:
        return tools.list_hosts(s)


@mcp.tool()
def list_containers(project: str = None, host: str = None, status: str = None) -> dict:
    """List containers, optionally filtered by project/host/status."""
    with session_scope() as s:
        return tools.list_containers(s, project, host, status)


@mcp.tool()
def get_container(container_id: str) -> dict:
    """One container's current stats."""
    with session_scope() as s:
        return tools.get_container(s, container_id)


@mcp.tool()
def get_container_logs(container_id: str) -> dict:
    """Recent log lines for a container (read these before fixing)."""
    with session_scope() as s:
        return tools.get_container_logs(s, container_id)


@mcp.tool()
def restart_container(container_id: str) -> dict:
    """Restart a container: clear the fault, bump the restart counter."""
    with session_scope() as s:
        return tools.restart_container(s, container_id)


# --- memory / runs / skills
@mcp.tool()
def list_memory() -> dict:
    """Delphi's learned facts about the owner and the fleet."""
    with session_scope() as s:
        return tools.list_memory(s)


@mcp.tool()
def add_memory_fact(text: str) -> dict:
    """Record a durable fact worth remembering across sessions."""
    with session_scope() as s:
        return tools.add_memory_fact(s, text)


@mcp.tool()
def list_recent_runs() -> dict:
    """Recent agent runs (enrich/execute) with status and cost."""
    with session_scope() as s:
        return tools.list_recent_runs(s)


@mcp.tool()
def list_skills() -> dict:
    """List the agent's skills."""
    with session_scope() as s:
        return tools.list_skills(s)


@mcp.tool()
def get_skill(name: str) -> dict:
    """Read a skill's full playbook: debug-issue | fix-project | triage-ticket |
    research | dispatch-agents | analyze-project | run-experiment."""
    with session_scope() as s:
        return tools.get_skill(s, name)


# --- real work
@mcp.tool()
def run_claude_code(project_key: str, task: str, dry_run: bool = False) -> dict:
    """Delegate real code work to Claude Code, gated by project autonomy."""
    with session_scope() as s:
        return tools.run_claude_code(s, project_key, task, dry_run)


# ============================================================ full CRUD
# Free rein over site data. Deletes guard against orphaning children; the
# autonomy ceiling on run_claude_code is untouched. Bodies stay one-liners so a
# single import + one wrapper-coverage test exercises them all.

# --- areas
@mcp.tool()
def create_area(area_id: str, name: str, kind: str = "", active: bool = True,
                context: str = None) -> dict:
    """Create a life area."""
    with session_scope() as s:
        return tools.create_area(s, area_id, name, kind, active, context)


@mcp.tool()
def update_area(area_id: str, name: str = None, kind: str = None,
                active: bool = None, context: str = None) -> dict:
    """Edit an area's fields or its agent context."""
    with session_scope() as s:
        return tools.update_area(s, area_id, name=name, kind=kind, active=active,
                                 context=context)


@mcp.tool()
def delete_area(area_id: str) -> dict:
    """Delete an area (refused if it still has projects or tickets)."""
    with session_scope() as s:
        return tools.delete_area(s, area_id)


# --- projects
@mcp.tool()
def create_project(key: str, area_id: str, name: str, autonomy: str, status: str,
                   blurb: str = "", users: int = None, repo: str = None,
                   context: str = None) -> dict:
    """Create a project. autonomy=propose|auto_pr|full, status=go|cau|flt|los."""
    with session_scope() as s:
        return tools.create_project(s, key, area_id, name, autonomy, status, blurb,
                                     users, repo, context)


@mcp.tool()
def update_project(key: str, name: str = None, area_id: str = None,
                   autonomy: str = None, status: str = None, blurb: str = None,
                   users: int = None, repo: str = None, context: str = None) -> dict:
    """Edit a project, including its autonomy ceiling, status, or spec context."""
    with session_scope() as s:
        return tools.update_project(s, key, name=name, area_id=area_id,
                                    autonomy=autonomy, status=status, blurb=blurb,
                                    users=users, repo=repo, context=context)


@mcp.tool()
def delete_project(key: str) -> dict:
    """Delete a project (refused if it still has containers or tickets)."""
    with session_scope() as s:
        return tools.delete_project(s, key)


# --- tickets: delete + dep/link edits
@mcp.tool()
def delete_ticket(ticket_id: str) -> dict:
    """Delete a ticket and its deps/links."""
    with session_scope() as s:
        return tools.delete_ticket(s, ticket_id)


@mcp.tool()
def update_dep(ticket_id: str, dep_id: str, title: str = None,
               done: bool = None) -> dict:
    """Edit a ticket dependency (matched by dep_id)."""
    with session_scope() as s:
        return tools.update_dep(s, ticket_id, dep_id, title=title, done=done)


@mcp.tool()
def remove_dep(ticket_id: str, dep_id: str) -> dict:
    """Remove a dependency from a ticket."""
    with session_scope() as s:
        return tools.remove_dep(s, ticket_id, dep_id)


@mcp.tool()
def update_ticket_link(ticket_id: str, url: str, kind: str = None,
                       label: str = None, new_url: str = None) -> dict:
    """Edit a ticket link (matched by url)."""
    with session_scope() as s:
        return tools.update_ticket_link(s, ticket_id, url, kind=kind, label=label,
                                        new_url=new_url)


@mcp.tool()
def remove_ticket_link(ticket_id: str, url: str) -> dict:
    """Remove a link from a ticket."""
    with session_scope() as s:
        return tools.remove_ticket_link(s, ticket_id, url)


# --- hosts
@mcp.tool()
def get_host(host_id: str) -> dict:
    """One host's details."""
    with session_scope() as s:
        return tools.get_host(s, host_id)


@mcp.tool()
def create_host(host_id: str, name: str, kind: str = "", icon: str = "",
                tag: str = "", loc: str = "") -> dict:
    """Add a fleet host."""
    with session_scope() as s:
        return tools.create_host(s, host_id, name, kind, icon, tag, loc)


@mcp.tool()
def update_host(host_id: str, name: str = None, kind: str = None, icon: str = None,
                tag: str = None, loc: str = None) -> dict:
    """Edit a host."""
    with session_scope() as s:
        return tools.update_host(s, host_id, name=name, kind=kind, icon=icon,
                                 tag=tag, loc=loc)


@mcp.tool()
def delete_host(host_id: str) -> dict:
    """Delete a host (refused if it still has containers)."""
    with session_scope() as s:
        return tools.delete_host(s, host_id)


# --- containers
@mcp.tool()
def create_container(container_id: str, project_key: str, host_id: str, role: str,
                     status: str = "go", image: str = "", cpu: str = "0%",
                     cpu_n: int = 0, mem: str = "0M", err: str = "—",
                     rps: str = "0/s", p95: str = "0 ms", restarts: int = 0,
                     up: str = "AOS") -> dict:
    """Create a container on a host for a project."""
    with session_scope() as s:
        return tools.create_container(s, container_id, project_key, host_id, role,
                                      status, image, cpu, cpu_n, mem, err, rps, p95,
                                      restarts, up)


@mcp.tool()
def update_container(container_id: str, project_key: str = None, host_id: str = None,
                     role: str = None, status: str = None, cpu: str = None,
                     cpu_n: int = None, mem: str = None, err: str = None,
                     rps: str = None, p95: str = None, restarts: int = None,
                     up: str = None, image: str = None) -> dict:
    """Edit any of a container's fields."""
    with session_scope() as s:
        return tools.update_container(
            s, container_id, project_key=project_key, host_id=host_id, role=role,
            status=status, cpu=cpu, cpu_n=cpu_n, mem=mem, err=err, rps=rps, p95=p95,
            restarts=restarts, up=up, image=image)


@mcp.tool()
def delete_container(container_id: str) -> dict:
    """Delete a container."""
    with session_scope() as s:
        return tools.delete_container(s, container_id)


# --- memory
@mcp.tool()
def update_memory_fact(text: str, new_text: str) -> dict:
    """Rewrite a memory fact (matched by exact text)."""
    with session_scope() as s:
        return tools.update_memory_fact(s, text, new_text)


@mcp.tool()
def remove_memory_fact(text: str) -> dict:
    """Forget a memory fact (matched by exact text)."""
    with session_scope() as s:
        return tools.remove_memory_fact(s, text)


# --- agent runs
@mcp.tool()
def create_agent_run(ticket: str, kind: str, status: str, cost: str,
                     when: str) -> dict:
    """Log an agent run."""
    with session_scope() as s:
        return tools.create_agent_run(s, ticket, kind, status, cost, when)


@mcp.tool()
def update_agent_run(run_id: int, ticket: str = None, kind: str = None,
                     status: str = None, cost: str = None, when: str = None) -> dict:
    """Edit a logged run (id from list_recent_runs)."""
    with session_scope() as s:
        return tools.update_agent_run(s, run_id, ticket=ticket, kind=kind,
                                      status=status, cost=cost, when=when)


@mcp.tool()
def delete_agent_run(run_id: int) -> dict:
    """Delete a logged run (id from list_recent_runs)."""
    with session_scope() as s:
        return tools.delete_agent_run(s, run_id)


# --- skills (DB rows)
@mcp.tool()
def create_skill(skill_id: str, name: str, trigger: str = "", desc: str = "",
                 on: bool = True) -> dict:
    """Register a skill row."""
    with session_scope() as s:
        return tools.create_skill(s, skill_id, name, trigger, desc, on)


@mcp.tool()
def update_skill(skill_id: str, name: str = None, trigger: str = None,
                 desc: str = None, on: bool = None) -> dict:
    """Edit or toggle a skill."""
    with session_scope() as s:
        return tools.update_skill(s, skill_id, name=name, trigger=trigger,
                                  desc=desc, on=on)


@mcp.tool()
def delete_skill(skill_id: str) -> dict:
    """Delete a skill row."""
    with session_scope() as s:
        return tools.delete_skill(s, skill_id)


# --- connectors (MCP servers)
@mcp.tool()
def list_mcp_servers() -> dict:
    """List configured MCP connectors."""
    with session_scope() as s:
        return tools.list_mcp_servers(s)


@mcp.tool()
def get_mcp_server(server_id: str) -> dict:
    """One connector's details."""
    with session_scope() as s:
        return tools.get_mcp_server(s, server_id)


@mcp.tool()
def create_mcp_server(server_id: str, name: str, url: str = "", tools_desc: str = "—",
                      desc: str = "", on: bool = True) -> dict:
    """Add an MCP connector."""
    with session_scope() as s:
        return tools.create_mcp_server(s, server_id, name, url, tools_desc, desc, on)


@mcp.tool()
def update_mcp_server(server_id: str, name: str = None, url: str = None,
                      tools_desc: str = None, desc: str = None,
                      on: bool = None) -> dict:
    """Edit or toggle a connector."""
    with session_scope() as s:
        return tools.update_mcp_server(s, server_id, name=name, url=url,
                                       tools=tools_desc, desc=desc, on=on)


@mcp.tool()
def delete_mcp_server(server_id: str) -> dict:
    """Delete a connector."""
    with session_scope() as s:
        return tools.delete_mcp_server(s, server_id)


# --- models
@mcp.tool()
def list_agent_models() -> dict:
    """List the agent models the UI can choose."""
    with session_scope() as s:
        return tools.list_agent_models(s)


@mcp.tool()
def get_agent_model(model_id: str) -> dict:
    """One model's details."""
    with session_scope() as s:
        return tools.get_agent_model(s, model_id)


@mcp.tool()
def create_agent_model(model_id: str, name: str, tag: str = "") -> dict:
    """Add a selectable agent model."""
    with session_scope() as s:
        return tools.create_agent_model(s, model_id, name, tag)


@mcp.tool()
def update_agent_model(model_id: str, name: str = None, tag: str = None) -> dict:
    """Edit a model."""
    with session_scope() as s:
        return tools.update_agent_model(s, model_id, name=name, tag=tag)


@mcp.tool()
def delete_agent_model(model_id: str) -> dict:
    """Delete a model."""
    with session_scope() as s:
        return tools.delete_agent_model(s, model_id)


# --- sessions / messages
@mcp.tool()
def list_sessions() -> dict:
    """List Delphi chat sessions."""
    with session_scope() as s:
        return tools.list_sessions(s)


@mcp.tool()
def get_session(session_id: str) -> dict:
    """One session with its messages (message ids included)."""
    with session_scope() as s:
        return tools.get_session(s, session_id)


@mcp.tool()
def create_session(session_id: str, title: str, ts: str = "",
                   hermes_session_id: str = None) -> dict:
    """Create a chat session."""
    with session_scope() as s:
        return tools.create_session(s, session_id, title, ts, hermes_session_id)


@mcp.tool()
def update_session(session_id: str, title: str = None, ts: str = None,
                   hermes_session_id: str = None) -> dict:
    """Edit a session's title, timestamp, or Hermes id."""
    with session_scope() as s:
        return tools.update_session(s, session_id, title=title, ts=ts,
                                    hermes_session_id=hermes_session_id)


@mcp.tool()
def delete_session(session_id: str) -> dict:
    """Delete a session and its messages."""
    with session_scope() as s:
        return tools.delete_session(s, session_id)


@mcp.tool()
def add_message(session_id: str, who: str, text: str, reasoning: str = None,
                tools_used: list = None) -> dict:
    """Append a message to a session (who = me | flight)."""
    with session_scope() as s:
        return tools.add_message(s, session_id, who, text, reasoning, tools_used)


@mcp.tool()
def update_message(message_id: int, who: str = None, text: str = None,
                   reasoning: str = None, tools_used: list = None) -> dict:
    """Edit a message (id from get_session)."""
    with session_scope() as s:
        return tools.update_message(s, message_id, who=who, text=text,
                                    reasoning=reasoning, tools=tools_used)


@mcp.tool()
def delete_message(message_id: int) -> dict:
    """Delete a message (id from get_session)."""
    with session_scope() as s:
        return tools.delete_message(s, message_id)


# Count registered tools once, at import, for the frontend connector seed.
TOOL_COUNT = len(mcp._tool_manager.list_tools())


def serve(transport="stdio"):  # pragma: no cover - transport loop
    mcp.run(transport=transport)
