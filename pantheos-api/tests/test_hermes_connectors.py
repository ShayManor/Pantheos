"""Unit tests for the Hermes MCP-connector bridge.

Pure transforms are tested directly; the three ssh primitives are monkeypatched
so nothing touches a real host. DB-touching paths use the seeded test session.
"""
import subprocess
import types

import pytest
import yaml

from app import hermes_connectors as hc
from app.models import McpServer

SAMPLE = """\
# Hermes config
model:
  default: gpt

mcp_servers:
  pantheos:
    url: http://127.0.0.1:8001/mcp
    connect_timeout: 20.0
    enabled: true
  github:
    url: https://api.githubcopilot.com/mcp/
    headers:
      Authorization: Bearer ${MCP_GITHUB_API_KEY}
    enabled: true

logging:
  level: info
"""


# --------------------------------------------------------------- gating
def test_enabled_reflects_env(monkeypatch):
    monkeypatch.delenv("PANTHEOS_HERMES_SSH", raising=False)
    assert hc.enabled() is False
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "minipc")
    assert hc.enabled() is True and hc._host() == "minipc"


# --------------------------------------------------------------- ssh primitives
def test_run_ok_and_helpers(monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    calls = []

    def fake(argv, **kw):
        calls.append((argv, kw.get("input")))
        return types.SimpleNamespace(returncode=0, stdout="OUT", stderr="")

    monkeypatch.setattr(subprocess, "run", fake)
    assert hc._read("/f") == "OUT"
    hc._write("/f", "body")
    hc._restart()
    # read, write (with stdin), restart each issued one ssh call
    assert calls[0][0][:2] == ["ssh", "h"] and "cat /f" in calls[0][0][2]
    assert calls[1][1] == "body" and "mv" in calls[1][0][2]
    assert "systemctl --user restart" in calls[2][0][2]


def test_run_nonzero_raises(monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: types.SimpleNamespace(
        returncode=3, stdout="", stderr="boom"))
    with pytest.raises(hc.HermesError, match="exited 3"):
        hc._run("do")


def test_run_subprocess_exception_raises(monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")

    def boom(*a, **k):
        raise subprocess.TimeoutExpired("ssh", 30)

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(hc.HermesError, match="ssh failed"):
        hc._run("do")


# --------------------------------------------------------------- pure transforms
def test_parse_connectors():
    conns = hc.parse_connectors(SAMPLE)
    assert conns == [
        {"id": "pantheos", "url": "http://127.0.0.1:8001/mcp", "on": True},
        {"id": "github", "url": "https://api.githubcopilot.com/mcp/", "on": True},
    ]
    # empty / missing block, None value, and missing `enabled` (defaults on)
    assert hc.parse_connectors("other: 1") == []
    assert hc.parse_connectors("mcp_servers:\n  x:\n") == [
        {"id": "x", "url": "", "on": True}]


def test_splice_preserves_surrounding_lines():
    out = hc._remove_from_config(SAMPLE, "github")
    assert "model:" in out and "logging:" in out          # kept
    assert "github" not in out and "pantheos:" in out     # only the block changed


def test_splice_no_block_appends():
    out = hc._splice("foo: bar", {"a": {"url": "u", "enabled": True}})
    assert out.startswith("foo: bar\n") and "mcp_servers:" in out and "a:" in out


def test_splice_block_at_eof():
    text = "mcp_servers:\n  a:\n    url: u\n    enabled: true\n"
    out = hc._set_enabled_in_config(text, "a", False)
    assert "enabled: false" in out


def test_add_to_config_header_and_plain():
    with_auth = hc._add_to_config(SAMPLE, "exa", "https://mcp.exa.ai/mcp", True)
    servers = yaml.safe_load(with_auth)["mcp_servers"]
    assert servers["exa"]["url"] == "https://mcp.exa.ai/mcp"
    assert servers["exa"]["headers"]["Authorization"] == "Bearer ${MCP_EXA_API_KEY}"
    assert servers["exa"]["enabled"] is True
    plain = yaml.safe_load(hc._add_to_config(SAMPLE, "local", "http://x", False))
    assert "headers" not in plain["mcp_servers"]["local"]


def test_set_enabled_missing_key_is_noop():
    out = yaml.safe_load(hc._set_enabled_in_config(SAMPLE, "ghost", False))
    assert set(out["mcp_servers"]) == {"pantheos", "github"}


def test_upsert_env():
    assert hc._upsert_env("A=1\nB=2", "B", "9") == "A=1\nB=9\n"
    assert hc._upsert_env("A=1", "C", "3") == "A=1\nC=3\n"


def test_slug_and_display():
    assert hc._slug("My Cool Server!") == "my_cool_server"
    assert hc._slug("***") == "connector"
    assert hc._display("github") == "GitHub"
    assert hc._display("my_thing") == "My Thing"


# --------------------------------------------------------------- mirror (inbound)
def test_mirror_disabled_is_noop(session, monkeypatch):
    monkeypatch.delenv("PANTHEOS_HERMES_SSH", raising=False)
    monkeypatch.setattr(hc, "_read", lambda *a: pytest.fail("should not read"))
    hc.mirror(session)  # returns immediately


def test_mirror_read_failure_keeps_panel(session, monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    before = session.query(McpServer).count()

    def raise_hermes(*a):
        raise hc.HermesError("down")

    monkeypatch.setattr(hc, "_read", raise_hermes)
    hc.mirror(session)
    assert session.query(McpServer).count() == before  # nothing wiped


def test_mirror_bad_yaml_keeps_panel(session, monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    before = session.query(McpServer).count()
    monkeypatch.setattr(hc, "_read", lambda *a: "a: b: c")  # invalid yaml
    hc.mirror(session)
    assert session.query(McpServer).count() == before


def test_mirror_upserts_and_deletes(session, monkeypatch):
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    # Hermes now has only pantheos (url changed, disabled) + a brand-new "acme".
    cfg = ("mcp_servers:\n"
           "  pantheos:\n    url: http://new:9000/mcp\n    enabled: false\n"
           "  acme:\n    url: http://acme\n    enabled: true\n")
    monkeypatch.setattr(hc, "_read", lambda *a: cfg)
    hc.mirror(session)
    rows = {r.id: r for r in session.query(McpServer).all()}
    assert set(rows) == {"pantheos", "acme"}          # github/hf/exa/wandb deleted
    assert rows["pantheos"].url == "http://new:9000/mcp" and rows["pantheos"].on is False
    assert rows["acme"].name == "Acme" and rows["acme"].tools == "—"


# --------------------------------------------------------------- outbound edits
@pytest.fixture()
def bridge(monkeypatch):
    """Enable the bridge with recording stubs for the ssh primitives."""
    monkeypatch.setenv("PANTHEOS_HERMES_SSH", "h")
    writes, restarts = [], []
    monkeypatch.setattr(hc, "_write", lambda p, c: writes.append((p, c)))
    monkeypatch.setattr(hc, "_restart", lambda: restarts.append(True))
    monkeypatch.setattr(hc, "_run", lambda *a, **k: "")  # env cat
    return types.SimpleNamespace(writes=writes, restarts=restarts, monkeypatch=monkeypatch)


def test_add_with_token(session, bridge):
    cfg = ("mcp_servers:\n  exa:\n    url: https://mcp.exa.ai/mcp\n"
           "    headers:\n      Authorization: Bearer ${MCP_EXA_API_KEY}\n    enabled: true\n")
    bridge.monkeypatch.setattr(hc, "_read", lambda *a: cfg)
    row = hc.add(session, "Exa", "https://mcp.exa.ai/mcp", token="secret")
    assert row.id == "exa" and row.name == "Exa"
    env_writes = [w for w in bridge.writes if w[0] == hc._ENV]
    assert env_writes and "MCP_EXA_API_KEY=secret" in env_writes[0][1]
    assert bridge.restarts == [True]


def test_add_without_token_no_env_write(session, bridge):
    cfg = "mcp_servers:\n  plain:\n    url: http://x\n    enabled: true\n"
    bridge.monkeypatch.setattr(hc, "_read", lambda *a: cfg)
    row = hc.add(session, "plain", "http://x")
    assert row.id == "plain"
    assert not [w for w in bridge.writes if w[0] == hc._ENV]


def test_add_sync_miss_raises(session, bridge):
    # Hermes read never shows the new key, so mirror can't return it.
    bridge.monkeypatch.setattr(hc, "_read", lambda *a: "mcp_servers: {}\n")
    with pytest.raises(hc.HermesError, match="sync did not return"):
        hc.add(session, "ghost", "http://x")


def test_set_enabled_and_remove(session, bridge):
    off = ("mcp_servers:\n  github:\n    url: https://api.githubcopilot.com/mcp/\n"
           "    enabled: false\n")
    bridge.monkeypatch.setattr(hc, "_read", lambda *a: off)
    row = hc.set_enabled(session, "github", False)
    assert row.on is False

    bridge.monkeypatch.setattr(hc, "_read", lambda *a: "mcp_servers: {}\n")
    hc.remove(session, "github")
    assert session.get(McpServer, "github") is None


def test_sync_once_runs_mirror(app, monkeypatch):
    ran = []
    monkeypatch.setattr(hc, "mirror", lambda s: ran.append(s))
    hc._sync_once(app)
    assert len(ran) == 1
