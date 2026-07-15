"""Real ACP client: drives `hermes acp` over stdio and yields normalized events.

ACP (agent-client-protocol) is async; Flask's SSE generator is sync. We run the
async driver on a private event loop in a background thread and hand events back
through a thread-safe queue, exposing a plain sync generator to the API layer.
"""
import asyncio
import os
import queue
import shlex
import threading

# The remote host has no interactive shell (ssh runs bash non-interactively, so
# ~/.bashrc's early-return skips PATH setup) -- wrap the remote command in a
# login shell so `hermes` resolves. Keep this as ONE shlex token (nested quotes)
# so ssh sends it to the remote shell intact instead of splitting it into
# positional args (`bash -c` only treats its first arg as the command string).
_DEFAULT_ACP_CMD = "ssh minipc \"bash -lc 'hermes acp'\""

_SENTINEL = object()


def _mcp_servers():
	"""MCP server configs to expose to Hermes, from PANTHEOS_MCP_URL (env-gated)."""
	url = os.environ.get("PANTHEOS_MCP_URL")
	if not url:
		return []
	# ACP's HttpMcpServer requires `headers` (Hermes rejects the whole session
	# request otherwise, leaving the agent with no Pantheos tools).
	return [{"name": "pantheos", "url": url, "type": "http", "headers": []}]


def run_turn(text, hermes_session_id, model=None, history=None):  # model/history ignored: Hermes threads its own session
    """Yield normalized event dicts for one user turn."""
    q = queue.Queue()

    def on_event(ev):
        q.put(ev)

    def worker():
        try:
            _drive(text, hermes_session_id, on_event)
        except Exception as exc:  # transport / spawn / protocol failure
            q.put({"type": "error", "message": str(exc)})
        finally:
            q.put(_SENTINEL)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        ev = q.get()
        if ev is _SENTINEL:
            break
        yield ev


def _drive(text, hermes_session_id, on_event):
    """Blocking: run the async ACP turn to completion, calling on_event per event."""
    asyncio.run(_drive_async(text, hermes_session_id, on_event))


async def _drive_async(text, hermes_session_id, on_event):
    import acp
    from acp.schema import (AgentMessageChunk, AgentThoughtChunk,
                            AllowedOutcome, RequestPermissionResponse,
                            ToolCallProgress, ToolCallStart, ToolCallUpdate)

    cmd = shlex.split(os.environ.get("DELPHI_ACP_CMD", _DEFAULT_ACP_CMD))
    timeout = float(os.environ.get("DELPHI_ACP_TIMEOUT", "180"))

    acc = {"text": "", "reasoning": "", "tools": [], "sid": hermes_session_id}

    class _Bridge(acp.Client):
        # NOTE: acp's MessageRouter dispatches Client overrides by keyword args
        # matching the request/notification model fields (session_id, update,
        # options, ...) -- NOT a single positional `params` object -- for any
        # method whose name contains an underscore (confirmed against the
        # installed acp 0.11.0 by tracing acp.router._resolve_handler /
        # _make_func against a live `hermes acp` session; a single-`params`
        # signature is silently never invoked, since MessageRouter's
        # `contextlib.suppress(Exception)` around notification dispatch
        # swallows the resulting TypeError).
        async def session_update(self, session_id, update, **kwargs):
            if isinstance(update, AgentThoughtChunk):
                delta = _content_text(update.content)
                acc["reasoning"] += delta
                on_event({"type": "reasoning", "delta": delta})
            elif isinstance(update, AgentMessageChunk):
                delta = _content_text(update.content)
                acc["text"] += delta
                on_event({"type": "text", "delta": delta})
            elif isinstance(update, (ToolCallStart, ToolCallProgress, ToolCallUpdate)):
                # Only genuine tool-call variants; other update kinds (e.g.
                # SessionInfoUpdate, which also carries a `title`) are dropped so
                # they don't masquerade as tools and pollute `done.tools`.
                name = _tool_name(update)
                if name:
                    if name not in acc["tools"]:
                        acc["tools"].append(name)
                    on_event({"type": "tool", "id": getattr(update, "tool_call_id", name),
                              "name": name, "status": getattr(update, "status", "done"),
                              "title": getattr(update, "title", name)})

        async def request_permission(self, session_id, tool_call, options, **kwargs):
            # Full-autonomy: auto-approve. Prefer an allow-once option.
            chosen = next((o for o in options if "allow" in (o.kind or "").lower()), options[0])
            return RequestPermissionResponse(
                outcome=AllowedOutcome(outcome="selected", option_id=chosen.option_id))

        async def write_text_file(self, session_id, path, content, **kwargs):  # pragma: no cover - not used by chat
            return None

        async def read_text_file(self, session_id, path, line=None, limit=None, **kwargs):  # pragma: no cover - not used by chat
            from acp.schema import ReadTextFileResponse
            return ReadTextFileResponse(content="")

    async with acp.spawn_agent_process(
            lambda agent: _Bridge(), cmd[0], *cmd[1:],
            use_unstable_protocol=True) as (conn, proc):
        await conn.initialize(protocol_version=acp.PROTOCOL_VERSION, client_capabilities=None)
        if hermes_session_id:
            await conn.load_session(cwd=os.getcwd(), session_id=hermes_session_id, mcp_servers=_mcp_servers())
            sid = hermes_session_id
        else:
            resp = await conn.new_session(cwd=os.getcwd(), mcp_servers=_mcp_servers())
            sid = resp.session_id
        acc["sid"] = sid
        try:
            await asyncio.wait_for(
                conn.prompt(session_id=sid, prompt=[{"type": "text", "text": text}]),
                timeout=timeout)
        except asyncio.TimeoutError:
            # builtin TimeoutError stringifies to "" -- give the UI a real message.
            raise RuntimeError(f"ACP turn timed out after {timeout}s")

    on_event({"type": "done", "text": acc["text"], "reasoning": acc["reasoning"],
              "tools": acc["tools"], "hermes_session_id": acc["sid"]})


def _content_text(content):
    """Extract text from an ACP content block (or list of them)."""
    if content is None:
        return ""
    if isinstance(content, list):
        return "".join(_content_text(c) for c in content)
    return getattr(content, "text", "") or ""


def _tool_name(update):
    """Best-effort human tool name from a tool-call update."""
    for attr in ("title", "kind", "name", "tool_name"):
        v = getattr(update, attr, None)
        if v:
            return str(v)
    return None
