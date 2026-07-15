"""Deterministic ACP stand-in used for tests and the default (mock) mode.

Emits the same normalized event vocabulary as the real client (app.acp_client)
but is a pure function of the input text — no randomness, no wall-clock — so the
20x E2E gate stays green. Reuses app.delphi.reply() for the answer + tools.
"""
from . import delphi as delphi_logic


def _chunks(s, n=24):
    """Split a string into <=n-char pieces, deterministically."""
    return [s[i:i + n] for i in range(0, len(s), n)] or [""]


def run_turn(text, hermes_session_id, model=None, history=None):  # model/history ignored: deterministic mock
    base = delphi_logic.reply(text)          # {"text": str, "tools": [str]}
    tools = base["tools"]

    reasoning = (
        f"The user asked: {text!r}. I'll check the queue and deadlines, "
        "then summarize the highest-leverage item."
    )
    # Rich answer so the UI exercises markdown, LaTeX, code, and a ticket ref.
    answer = (
        f"{base['text']}\n\n"
        "**Priority math:** score $s = w_d \\cdot \\frac{1}{t} + w_e$ favors "
        "`GRD-0182` today.\n\n"
        "```py\nscore = w_d / hours_left + w_e\n```"
    )

    yield {"type": "reasoning", "delta": reasoning}
    for i, name in enumerate(tools):
        yield {"type": "tool", "id": f"t{i}", "name": name,
               "status": "done", "title": name}
    for c in _chunks(answer):
        yield {"type": "text", "delta": c}
    yield {"type": "done", "text": answer, "reasoning": reasoning,
           "tools": tools, "hermes_session_id": hermes_session_id or "mock-session"}
