from app.mcp import tools


# --------------------------------------------------------------- connectors
def test_mcp_server_crud(session):
    listed = tools.list_mcp_servers(session)["mcp_servers"]
    assert any(m["id"] == "pantheos" for m in listed)
    assert tools.get_mcp_server(session, "pantheos")["name"] == "Pantheos"
    made = tools.create_mcp_server(session, "gh", "GitHub", url="mcp.gh.local",
                                   tools="8", desc="repos")
    assert made == {"id": "gh", "name": "GitHub", "url": "mcp.gh.local",
                    "tools": "8", "on": True, "desc": "repos"}
    up = tools.update_mcp_server(session, "gh", desc="repos+issues", on=False)
    assert up["desc"] == "repos+issues" and up["on"] is False
    assert tools.delete_mcp_server(session, "gh") == {"deleted": "gh"}
    assert tools.get_mcp_server(session, "gh")["error"] == "unknown mcp server"


def test_mcp_server_validation(session):
    assert tools.create_mcp_server(session, " ", "x")["error"] == "id and name required"
    assert tools.create_mcp_server(session, "pantheos", "dup")["error"] == "mcp server exists"
    assert tools.update_mcp_server(session, "nope")["error"] == "unknown mcp server"
    assert tools.delete_mcp_server(session, "nope")["error"] == "unknown mcp server"


# ------------------------------------------------------------------- models
def test_agent_model_crud(session):
    listed = tools.list_agent_models(session)["models"]
    assert any(m["id"] == "gpt-5.6-terra" for m in listed)
    assert tools.get_agent_model(session, "gpt-5.6-terra")["name"] == "GPT Terra"
    made = tools.create_agent_model(session, "claude-x", "Claude X", tag="anthropic")
    assert made == {"id": "claude-x", "name": "Claude X", "tag": "anthropic"}
    up = tools.update_agent_model(session, "claude-x", name="Claude Y", tag="ant")
    assert up["name"] == "Claude Y" and up["tag"] == "ant"
    assert tools.delete_agent_model(session, "claude-x") == {"deleted": "claude-x"}
    assert tools.get_agent_model(session, "claude-x")["error"] == "unknown model"


def test_agent_model_validation(session):
    assert tools.create_agent_model(session, " ", "x")["error"] == "id and name required"
    assert tools.create_agent_model(session, "gpt-5.6-terra", "dup")["error"] == "model exists"
    assert tools.update_agent_model(session, "nope")["error"] == "unknown model"
    assert tools.delete_agent_model(session, "nope")["error"] == "unknown model"


# ------------------------------------------------------- sessions / messages
def test_session_and_message_crud(session):
    s = tools.create_session(session, "sx", "New chat", ts="now")
    assert s["id"] == "sx" and s["title"] == "New chat" and s["msgs"] == []
    up = tools.update_session(session, "sx", title="Renamed", hermes_session_id="h1")
    assert up["title"] == "Renamed" and up["hermes_session_id"] == "h1"
    assert any(x["id"] == "sx" for x in tools.list_sessions(session)["sessions"])

    m = tools.add_message(session, "sx", "me", "hello", reasoning="r",
                          tools=[{"name": "get_ticket"}])
    assert m["who"] == "me" and m["text"] == "hello" and "id" in m
    got = tools.get_session(session, "sx")
    assert got["msgs"][-1]["id"] == m["id"] and got["msgs"][-1]["text"] == "hello"

    mu = tools.update_message(session, m["id"], text="hi", who="flight")
    assert mu["text"] == "hi" and mu["who"] == "flight"
    assert tools.delete_message(session, m["id"]) == {"deleted": m["id"]}

    assert tools.delete_session(session, "sx") == {"deleted": "sx"}
    assert tools.get_session(session, "sx")["error"] == "unknown session"


def test_session_and_message_validation(session):
    assert tools.create_session(session, " ", "t")["error"] == "id and title required"
    tools.create_session(session, "dup", "T")
    assert tools.create_session(session, "dup", "T2")["error"] == "session exists"
    assert tools.update_session(session, "nope")["error"] == "unknown session"
    assert tools.delete_session(session, "nope")["error"] == "unknown session"
    assert tools.add_message(session, "nope", "me", "x")["error"] == "unknown session"
    assert tools.add_message(session, "dup", "me", "  ")["error"] == "text required"
    assert tools.update_message(session, 999999)["error"] == "unknown message"
    assert tools.delete_message(session, 999999)["error"] == "unknown message"
