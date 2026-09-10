"""Selects the Delphi model backend for a turn based on DELPHI_ACP_MODE."""
import os

from . import acp_mock


def run_turn(text, hermes_session_id, model=None, history=None, auto_approve=True):
    """Yield normalized events for one user turn.

    Mode (env DELPHI_ACP_MODE): 'mock' (default, deterministic — used by tests)
    | 'openai' (stream from an OpenAI-compatible model) | 'acp' (Hermes over ACP).
    ``model`` is the id chosen in the UI selector (used by the openai backend).
    ``history`` is the prior turns of this session as OpenAI-style
    {"role", "content"} dicts (oldest-first), giving the model memory; the acp
    backend ignores it since Hermes threads its own session by hermes_session_id.
    ``auto_approve`` reaches only the acp backend, where it decides whether the
    agent's tool calls are permitted without asking.
    """
    mode = os.environ.get("DELPHI_ACP_MODE", "mock")
    if mode == "openai":
        from . import openai_client         # imported lazily
        yield from openai_client.run_turn(text, hermes_session_id, model, history)
    elif mode == "acp":
        from . import acp_client            # imported lazily; real deps only in acp mode
        yield from acp_client.run_turn(text, hermes_session_id, model, history,
                                       auto_approve=auto_approve)
    else:
        yield from acp_mock.run_turn(text, hermes_session_id, model, history)
