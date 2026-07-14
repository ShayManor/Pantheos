import subprocess
import types

from app.mcp import tools


def _force_autonomy(session, key, autonomy):
    from app.models import Project
    session.get(Project, key).autonomy = autonomy
    session.flush()


def test_unknown_project(session):
    assert tools.run_claude_code(session, "nope", "do it")["error"] == "unknown project"


def test_propose_is_plan_only(session, monkeypatch):
    _force_autonomy(session, "merlin", "propose")
    called = {"ran": False}
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: called.__setitem__("ran", True))
    out = tools.run_claude_code(session, "merlin", "refactor planner")
    assert out["mode"] == "plan" and out["autonomy"] == "propose"
    assert "refactor planner" in out["prompt"] and called["ran"] is False


def test_dry_run_forces_plan_even_on_full(session, monkeypatch):
    _force_autonomy(session, "merlin", "full")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    out = tools.run_claude_code(session, "merlin", "x", dry_run=True)
    assert out["mode"] == "plan"


def test_full_executes(session, monkeypatch, tmp_path):
    _force_autonomy(session, "merlin", "full")
    monkeypatch.setenv("PANTHEOS_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "merlin").mkdir()
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: types.SimpleNamespace(returncode=0, stdout="done", stderr=""))
    out = tools.run_claude_code(session, "merlin", "ship it")
    assert out["mode"] == "executed" and out["exit_code"] == 0 and out["stdout"] == "done"


def test_missing_workspace(session, monkeypatch, tmp_path):
    _force_autonomy(session, "merlin", "full")
    monkeypatch.setenv("PANTHEOS_WORKSPACE_ROOT", str(tmp_path))
    out = tools.run_claude_code(session, "merlin", "x")
    assert out["mode"] == "error" and "workspace not found" in out["error"]


def test_missing_binary(session, monkeypatch, tmp_path):
    _force_autonomy(session, "merlin", "full")
    monkeypatch.setenv("PANTHEOS_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "merlin").mkdir()
    def boom(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(subprocess, "run", boom)
    out = tools.run_claude_code(session, "merlin", "x")
    assert out["mode"] == "error" and "claude binary" in out["error"]
