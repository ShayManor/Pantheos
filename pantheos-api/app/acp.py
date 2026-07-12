"""Selects the ACP backend for a Delphi turn based on DELPHI_ACP_MODE."""
import os

from . import acp_mock


def run_turn(text, hermes_session_id):
    """Yield normalized events for one user turn. Mode: 'mock' (default) | 'acp'."""
    if os.environ.get("DELPHI_ACP_MODE", "mock") == "acp":
        from . import acp_client            # imported lazily; real deps only in acp mode
        yield from acp_client.run_turn(text, hermes_session_id)
    else:
        yield from acp_mock.run_turn(text, hermes_session_id)
