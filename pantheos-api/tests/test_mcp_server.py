import asyncio

from app.mcp import server
from app.mcp import session as msession


def test_instructions_enforce_grounding():
    assert server.mcp.instructions
    text = server.mcp.instructions.lower()
    assert "get_project_spec" in text and "autonomy" in text and "ground" in text


def test_tool_count_matches_registry():
    listed = asyncio.run(server.mcp.list_tools())
    assert server.TOOL_COUNT == len(listed)
    assert server.TOOL_COUNT >= 20


def test_wrapper_delegates_through_session_scope(session, monkeypatch):
    # wrappers open their own scope — point it at the test session
    monkeypatch.setattr(msession, "_factory", lambda: session)
    out = server.get_project_spec("merlin")
    assert out["key"] == "merlin"
    created = server.create_ticket(title="Via wrapper", project_key="merlin")
    assert created["title"] == "Via wrapper"
