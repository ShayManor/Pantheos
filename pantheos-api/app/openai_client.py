"""OpenAI-compatible streaming backend for Delphi.

Streams a chat completion from an OpenAI-compatible endpoint (default the real
OpenAI API) and yields the same normalized event vocabulary as app.acp_client /
app.acp_mock, so the SSE layer (api/delphi.py) stays backend-agnostic.

Config (env):
  DELPHI_OPENAI_BASE_URL   default https://api.openai.com/v1
  DELPHI_MODEL             default gpt-5.6-terra
  DELPHI_OPENAI_API_KEY    (or OPENAI_API_KEY) — required
  DELPHI_OPENAI_TIMEOUT    seconds, default 120
"""
import json
import os
import urllib.error
import urllib.request

from . import seed_data

_DEFAULT_BASE = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-5.6-terra"


def _system_prompt():
    facts = "\n".join(f"- {f}" for f in seed_data.MEMORY_FACTS)
    return (
        "You are Delphi, the AI agent inside Pantheos — Shay Manor's personal "
        '"Life OS" for managing tickets, projects, infrastructure, and research. '
        "You are talking to Shay. Be terse and technically precise.\n\n"
        f"What you know about Shay:\n{facts}"
    )


def _api_key():
    return os.environ.get("DELPHI_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")


def run_turn(text, hermes_session_id, model=None, history=None):
    """Yield normalized event dicts for one user turn, streamed from the model.

    ``model`` (from the UI selector) overrides the DELPHI_MODEL env default.
    ``history`` is the prior turns of the session as OpenAI-style
    {"role", "content"} dicts (oldest-first); replaying it gives the model memory.
    """
    key = _api_key()
    if not key:
        raise RuntimeError("no OpenAI API key set (DELPHI_OPENAI_API_KEY / OPENAI_API_KEY)")
    base = os.environ.get("DELPHI_OPENAI_BASE_URL", _DEFAULT_BASE).rstrip("/")
    model = model or os.environ.get("DELPHI_MODEL", _DEFAULT_MODEL)
    timeout = float(os.environ.get("DELPHI_OPENAI_TIMEOUT", "120"))

    payload = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            *(history or []),
            {"role": "user", "content": text},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    full_text, full_reasoning = "", ""
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"model request failed (HTTP {exc.code}): {body}") from exc

    with resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            delta = (json.loads(data).get("choices") or [{}])[0].get("delta") or {}
            reasoning = delta.get("reasoning_content") or delta.get("reasoning")
            if reasoning:
                full_reasoning += reasoning
                yield {"type": "reasoning", "delta": reasoning}
            content = delta.get("content")
            if content:
                full_text += content
                yield {"type": "text", "delta": content}

    yield {"type": "done", "text": full_text, "reasoning": full_reasoning,
           "tools": [], "model": model, "hermes_session_id": hermes_session_id}
