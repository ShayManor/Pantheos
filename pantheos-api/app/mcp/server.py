"""FastMCP wiring: register every tool, carry the grounding system prompt.

Thin wrappers open a ``session_scope()`` and delegate to ``tools.py``. Keeping
them one-liners means importing this module (which runs registration) covers
them; a test exercises each through a scoped test session.
"""
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
  triage-ticket) and follow it.
"""

mcp = FastMCP("Pantheos", instructions=INSTRUCTIONS)


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
    """Read a skill's full playbook: debug-issue | fix-project | triage-ticket."""
    with session_scope() as s:
        return tools.get_skill(s, name)


# --- real work
@mcp.tool()
def run_claude_code(project_key: str, task: str, dry_run: bool = False) -> dict:
    """Delegate real code work to Claude Code, gated by project autonomy."""
    with session_scope() as s:
        return tools.run_claude_code(s, project_key, task, dry_run)


# Count registered tools once, at import, for the frontend connector seed.
TOOL_COUNT = len(mcp._tool_manager.list_tools())


def serve(transport="stdio"):  # pragma: no cover - transport loop
    mcp.run(transport=transport)
