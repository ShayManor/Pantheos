import io
import json
import urllib.error

import pytest

import app.openai_client as oc
from app import acp


class FakeResp:
    """Stand-in for an httplib response: iterable over byte lines + context mgr."""
    def __init__(self, lines):
        self._lines = lines

    def __iter__(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _sse(obj):
    return f"data: {json.dumps(obj)}\n".encode()


def test_streams_reasoning_text_and_done(monkeypatch):
    monkeypatch.setenv("DELPHI_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DELPHI_MODEL", "gpt-5.6-terra")
    captured = {}
    lines = [
        b": keepalive\n",                                                  # non-data line -> skipped
        _sse({"choices": [{"delta": {"reasoning_content": "thinking "}}]}),
        _sse({"choices": [{"delta": {"content": "Your name is "}}]}),
        _sse({"choices": [{"delta": {"content": "Shay."}}]}),
        _sse({"choices": [{"delta": {}}]}),                                # empty delta
        b"data: [DONE]\n",
        _sse({"choices": [{"delta": {"content": "ignored after done"}}]}),
    ]

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data)
        captured["headers"] = dict(req.header_items())
        return FakeResp(lines)

    monkeypatch.setattr("app.openai_client.urllib.request.urlopen", fake_urlopen)

    events = list(oc.run_turn("What is my name?", "hs1"))

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["body"]["model"] == "gpt-5.6-terra"
    assert captured["body"]["stream"] is True
    assert "Bearer sk-test" in captured["headers"].values()
    assert "Shay" in captured["body"]["messages"][0]["content"]        # system prompt has user facts
    assert captured["body"]["messages"][1] == {"role": "user", "content": "What is my name?"}

    assert [e["type"] for e in events] == ["reasoning", "text", "text", "done"]
    assert events[-1]["text"] == "Your name is Shay."
    assert events[-1]["reasoning"] == "thinking "
    assert events[-1]["tools"] == [] and events[-1]["hermes_session_id"] == "hs1"
    assert events[-1]["model"] == "gpt-5.6-terra"          # resolved model reported back


def test_reasoning_field_fallback_and_base_url_and_key_fallback(monkeypatch):
    monkeypatch.delenv("DELPHI_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "k")                            # fallback key env
    monkeypatch.setenv("DELPHI_OPENAI_BASE_URL", "http://host:9/v1/")    # trailing slash trimmed
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        return FakeResp([_sse({"choices": [{"delta": {"reasoning": "r"}}]}), b"data: [DONE]\n"])

    monkeypatch.setattr("app.openai_client.urllib.request.urlopen", fake_urlopen)
    events = list(oc.run_turn("hi", None))
    assert seen["url"] == "http://host:9/v1/chat/completions"
    assert events[0] == {"type": "reasoning", "delta": "r"}
    assert events[-1]["hermes_session_id"] is None


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("DELPHI_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="no OpenAI API key"):
        list(oc.run_turn("hi", None))


def test_wraps_http_error_with_body(monkeypatch):
    monkeypatch.setenv("DELPHI_OPENAI_API_KEY", "k")

    def boom(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 404, "Not Found", {}, io.BytesIO(b'{"error":"model not found"}'))

    monkeypatch.setattr("app.openai_client.urllib.request.urlopen", boom)
    with pytest.raises(RuntimeError, match=r"model request failed \(HTTP 404\).*model not found"):
        list(oc.run_turn("hi", None))


def test_explicit_model_overrides_env(monkeypatch):
    monkeypatch.setenv("DELPHI_OPENAI_API_KEY", "k")
    monkeypatch.setenv("DELPHI_MODEL", "gpt-5.6-terra")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["model"] = json.loads(req.data)["model"]
        return FakeResp([b"data: [DONE]\n"])

    monkeypatch.setattr("app.openai_client.urllib.request.urlopen", fake_urlopen)
    list(oc.run_turn("hi", None, "gpt-5.6-luna"))     # UI-selected model wins over env
    assert seen["model"] == "gpt-5.6-luna"


def test_dispatcher_selects_openai_and_passes_model(monkeypatch):
    monkeypatch.setenv("DELPHI_ACP_MODE", "openai")
    got = {}

    def fake(text, hsid, model=None):
        got["model"] = model
        yield {"type": "done", "text": "hi", "reasoning": "", "tools": [], "hermes_session_id": hsid}

    monkeypatch.setattr("app.openai_client.run_turn", fake)
    out = list(acp.run_turn("q", "hs", "gpt-5.6-luna"))
    assert out[-1]["text"] == "hi"
    assert got["model"] == "gpt-5.6-luna"
