from app import acp
import app.acp_client as acp_client


def test_run_turn_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("DELPHI_ACP_MODE", raising=False)
    events = list(acp.run_turn("what is due this week", None))
    assert events[-1]["type"] == "done"
    assert events[-1]["tools"] == ["calendar", "brightspace", "queue"]


def test_run_turn_selects_real_client(monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "acp")
    called = {}

    def fake(text, hsid, model=None, history=None):
        called["args"] = (text, hsid, model)
        yield {"type": "done", "text": "ok", "reasoning": "",
               "tools": [], "hermes_session_id": "hs1"}

    monkeypatch.setattr("app.acp_client.run_turn", fake)
    out = list(acp.run_turn("hello", "hs1", "gpt-5.6-luna"))
    assert called["args"] == ("hello", "hs1", "gpt-5.6-luna")
    assert out[-1]["text"] == "ok"


def test_run_turn_normalizes_events(monkeypatch):
    # Replace the async driver with one that emits through the same queue path.
    def fake_drive(text, hsid, on_event):
        on_event({"type": "reasoning", "delta": "thinking"})
        on_event({"type": "text", "delta": "hello "})
        on_event({"type": "text", "delta": "world"})
        on_event({"type": "tool", "id": "1", "name": "queue", "status": "done", "title": "queue"})
        on_event({"type": "done", "text": "hello world", "reasoning": "thinking",
                  "tools": ["queue"], "hermes_session_id": hsid or "hs-new"})

    monkeypatch.setattr(acp_client, "_drive", fake_drive)
    events = list(acp_client.run_turn("hi", None))
    assert [e["type"] for e in events] == ["reasoning", "text", "text", "tool", "done"]
    assert events[-1]["hermes_session_id"] == "hs-new"


def test_run_turn_reports_errors(monkeypatch):
    def boom(text, hsid, on_event):
        raise RuntimeError("ssh down")
    monkeypatch.setattr(acp_client, "_drive", boom)
    events = list(acp_client.run_turn("hi", "hs1"))
    assert events[-1] == {"type": "error", "message": "ssh down"}


# ---------------------------------------------------------------------------
# _drive/_drive_async: exercised against the REAL installed `acp` package and
# schema classes, faking only the transport boundary (acp.spawn_agent_process)
# so no subprocess/ssh/minipc is involved. Session updates/permission requests
# are dispatched through acp's own `build_client_router` with raw wire-shaped
# dicts (exactly the bytes `hermes acp` sends over the wire) rather than
# calling `_Bridge` methods directly, so these tests exercise the SAME
# kwargs-based dispatch convention the real router uses -- a prior version of
# this test called `_Bridge.session_update(SessionNotification(...))` with a
# single positional object directly, which passed even though the real router
# calls Client overrides with `session_id=`/`update=` keyword args (confirmed
# against the installed acp 0.11.0), silently missing every live update.
# ---------------------------------------------------------------------------

class _FakeCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn, None

    async def __aexit__(self, *exc_info):
        return False


def _install_fake_spawn(monkeypatch, conn_factory):
    import acp

    def fake_spawn(to_client, command, *args, **kwargs):
        bridge = to_client(None)
        return _FakeCtx(conn_factory(bridge))

    monkeypatch.setattr(acp, "spawn_agent_process", fake_spawn)


def test_drive_async_new_session_streams_reasoning_text_and_tool(monkeypatch):
    from acp.client.router import build_client_router

    class FakeConn:
        def __init__(self, bridge):
            self._router = build_client_router(bridge, use_unstable_protocol=True)

        async def initialize(self, **kw):
            return None

        async def new_session(self, **kw):
            class R:
                session_id = "hs-live"
            return R()

        async def prompt(self, session_id, prompt, **kw):
            # Raw dicts, shaped exactly like the JSON-RPC `session/update`
            # notifications and `session/request_permission` request observed
            # from a live `hermes acp` process.
            await self._router("session/update", {
                "sessionId": session_id,
                "update": {"sessionUpdate": "agent_thought_chunk",
                           "content": {"type": "text", "text": "thinking"}}}, True)
            await self._router("session/update", {
                "sessionId": session_id,
                "update": {"sessionUpdate": "agent_message_chunk",
                           "content": {"type": "text", "text": "hi"}}}, True)
            await self._router("session/update", {
                "sessionId": session_id,
                "update": {"sessionUpdate": "tool_call", "toolCallId": "1",
                           "title": "queue", "status": "completed"}}, True)
            resp = await self._router("session/request_permission", {
                "sessionId": session_id,
                "toolCall": {"toolCallId": "1"},
                "options": [{"optionId": "opt-reject", "name": "Reject", "kind": "reject_once"},
                            {"optionId": "opt-allow", "name": "Allow", "kind": "allow_once"}]}, False)
            assert resp.outcome.option_id == "opt-allow"

    _install_fake_spawn(monkeypatch, FakeConn)

    events = []
    acp_client._drive("hi", None, events.append)

    assert [e["type"] for e in events] == ["reasoning", "text", "tool", "done"]
    done = events[-1]
    assert done["text"] == "hi"
    assert done["reasoning"] == "thinking"
    assert done["tools"] == ["queue"]
    assert done["hermes_session_id"] == "hs-live"


def test_drive_async_ignores_non_tool_update_with_title(monkeypatch):
    # A SessionInfoUpdate carries a `title` but is NOT a tool call -- it must not
    # be emitted as a `tool` event nor pollute done.tools.
    from acp.client.router import build_client_router

    class FakeConn:
        def __init__(self, bridge):
            self._router = build_client_router(bridge, use_unstable_protocol=True)

        async def initialize(self, **kw):
            return None

        async def new_session(self, **kw):
            class R:
                session_id = "hs-live"
            return R()

        async def prompt(self, session_id, prompt, **kw):
            await self._router("session/update", {
                "sessionId": session_id,
                "update": {"sessionUpdate": "session_info_update",
                           "title": "My chat session"}}, True)
            await self._router("session/update", {
                "sessionId": session_id,
                "update": {"sessionUpdate": "agent_message_chunk",
                           "content": {"type": "text", "text": "hi"}}}, True)

    _install_fake_spawn(monkeypatch, FakeConn)

    events = []
    acp_client._drive("hi", None, events.append)

    assert [e["type"] for e in events] == ["text", "done"]
    assert events[-1]["tools"] == []


def test_drive_async_timeout_produces_nonempty_error(monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_TIMEOUT", "0.01")

    class FakeConn:
        def __init__(self, bridge):
            self.bridge = bridge

        async def initialize(self, **kw):
            return None

        async def new_session(self, **kw):
            class R:
                session_id = "hs-live"
            return R()

        async def prompt(self, session_id, prompt, **kw):
            import asyncio
            await asyncio.sleep(1)

    _install_fake_spawn(monkeypatch, FakeConn)

    events = list(acp_client.run_turn("hi", None))
    assert events[-1]["type"] == "error"
    assert events[-1]["message"] == "ACP turn timed out after 0.01s"


def test_drive_async_loads_existing_session(monkeypatch):
    class FakeConn:
        def __init__(self, bridge):
            self.bridge = bridge

        async def initialize(self, **kw):
            return None

        async def load_session(self, **kw):
            assert kw["session_id"] == "hs1"
            return None

        async def prompt(self, session_id, prompt, **kw):
            return None

    _install_fake_spawn(monkeypatch, FakeConn)

    events = []
    acp_client._drive("hi", "hs1", events.append)

    assert events[-1]["hermes_session_id"] == "hs1"


def test_content_text_handles_none_single_and_list():
    class Block:
        def __init__(self, text):
            self.text = text

    assert acp_client._content_text(None) == ""
    assert acp_client._content_text(Block("hi")) == "hi"
    assert acp_client._content_text([Block("a"), Block("b")]) == "ab"


def test_tool_name_prefers_title_then_falls_back_to_none():
    class Named:
        title = "Search"

    class Unnamed:
        pass

    assert acp_client._tool_name(Named()) == "Search"
    assert acp_client._tool_name(Unnamed()) is None


def test_mcp_servers_from_env(monkeypatch):
    from app import acp_client
    monkeypatch.delenv("PANTHEOS_MCP_URL", raising=False)
    assert acp_client._mcp_servers() == []
    monkeypatch.setenv("PANTHEOS_MCP_URL", "http://mac.tailnet:8001/mcp")
    cfgs = acp_client._mcp_servers()
    assert len(cfgs) == 1
    assert cfgs[0]["name"] == "pantheos"
    assert cfgs[0]["url"] == "http://mac.tailnet:8001/mcp"
