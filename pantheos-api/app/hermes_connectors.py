"""Bridge between the Pantheos connectors panel and Hermes' MCP config.

Hermes (the Delphi runtime on the minipc) owns the real MCP connectors in
``~/.hermes/config.yaml``. This module makes Hermes the source of truth: it
mirrors that file into the ``mcp_servers`` table (so the UI always reflects what
Delphi can actually call) and pushes UI edits back out to Hermes over the same
SSH channel ACP uses. A pure mirror — a connector Hermes no longer has is
removed from the panel.

Secrets never touch Postgres: a connector's Bearer token is written to Hermes'
``~/.hermes/.env`` as ``MCP_<NAME>_API_KEY`` (the deploy-mcp-connectors
convention), and the config references it as ``Bearer ${MCP_<NAME>_API_KEY}``.

Everything is gated on ``PANTHEOS_HERMES_SSH`` (an ssh host alias). Unset — dev,
test, E2E — and the panel stays pure-DB, exactly as before. All file
transformation is pure; the only side effects are three thin ssh primitives
(``_read``/``_write``/``_restart``) that tests monkeypatch.
"""
import os
import re
import subprocess
import threading
import time

import yaml
from sqlalchemy import func

from .models import McpServer

_CONFIG = "~/.hermes/config.yaml"
_ENV = "~/.hermes/.env"
_UNIT = "hermes-serve.service"

# Display names for the known connectors; new UI-added rows get their typed name
# (set by the add endpoint), and any other id falls back to a title-cased slug.
_NAMES = {"pantheos": "Pantheos", "github": "GitHub", "huggingface": "Hugging Face",
          "exa": "Exa", "wandb": "Weights & Biases"}


class HermesError(RuntimeError):
    """A Hermes SSH bridge operation failed."""


def _host():
    return os.environ.get("PANTHEOS_HERMES_SSH")


def enabled():
    """True when the SSH bridge is configured (prod); False in dev/test/E2E."""
    return bool(_host())


# --------------------------------------------------------------- ssh primitives
def _run(remote_cmd, stdin=None):
    timeout = float(os.environ.get("PANTHEOS_HERMES_TIMEOUT", "30"))
    try:
        p = subprocess.run(["ssh", _host(), remote_cmd], input=stdin,
                           capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        raise HermesError(f"ssh failed: {e}") from e
    if p.returncode != 0:
        raise HermesError(f"ssh {remote_cmd!r} exited {p.returncode}: {p.stderr.strip()}")
    return p.stdout


def _read(path):
    return _run(f"cat {path}")


def _write(path, content):
    # tmp + mv so a dropped connection never leaves a half-written config.
    _run(f"cat > {path}.tmp && mv {path}.tmp {path}", stdin=content)


def _restart():
    _run(f"bash -lc 'export XDG_RUNTIME_DIR=/run/user/$(id -u); "
         f"systemctl --user restart {_UNIT}'")


# --------------------------------------------------------------- pure transforms
def parse_connectors(text):
    """Extract ``[{id, url, on}]`` from a config.yaml's ``mcp_servers`` block."""
    servers = (yaml.safe_load(text) or {}).get("mcp_servers") or {}
    return [{"id": key, "url": (val or {}).get("url") or "",
             "on": bool((val or {}).get("enabled", True))}
            for key, val in servers.items()]


def _load_servers(text):
    return dict((yaml.safe_load(text) or {}).get("mcp_servers") or {})


def _splice(text, servers):
    """Replace the ``mcp_servers`` block in ``text`` with a dump of ``servers``,
    leaving every other line (header comments, other config) untouched."""
    lines = text.splitlines(keepends=True)
    start = end = None
    for i, line in enumerate(lines):
        if start is None:
            if re.match(r"^mcp_servers\s*:", line):
                start = i
        elif line.strip() and not line[0].isspace():
            end = i
            break
    block = yaml.safe_dump({"mcp_servers": servers}, sort_keys=False,
                           default_flow_style=False)
    if start is None:
        return text + ("\n" if text and not text.endswith("\n") else "") + block
    if end is None:
        end = len(lines)
    return "".join(lines[:start]) + block + "".join(lines[end:])


def _add_to_config(text, key, url, header_auth):
    servers = _load_servers(text)
    entry = {"url": url}
    if header_auth:
        entry["headers"] = {"Authorization": f"Bearer ${{MCP_{key.upper()}_API_KEY}}"}
    entry["enabled"] = True
    servers[key] = entry
    return _splice(text, servers)


def _remove_from_config(text, key):
    servers = _load_servers(text)
    servers.pop(key, None)
    return _splice(text, servers)


def _set_enabled_in_config(text, key, on):
    servers = _load_servers(text)
    if key in servers:
        servers[key] = {**(servers[key] or {}), "enabled": bool(on)}
    return _splice(text, servers)


def _upsert_env(text, key, value):
    out, found = [], False
    for ln in text.splitlines():
        if ln.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"{key}={value}")
    return "\n".join(out) + "\n"


def _slug(name):
    """Slugify a display name into a config key (lowercase alnum + underscore)."""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_") or "connector"


def _display(key):
    return _NAMES.get(key, key.replace("_", " ").replace("-", " ").title())


# --------------------------------------------------------------- mirror (inbound)
def mirror(session):
    """Reconcile the ``mcp_servers`` table to match Hermes exactly (pure mirror).

    No-op when the bridge is off. On any read/parse failure it returns without
    touching the table, so a transient SSH hiccup never wipes the panel.
    """
    if not enabled():
        return
    try:
        conns = parse_connectors(_read(_CONFIG))
    except (HermesError, yaml.YAMLError):
        return
    ids = {c["id"] for c in conns}
    existing = {r.id: r for r in session.query(McpServer).all()}
    pos = session.query(func.max(McpServer.position)).scalar() or 0
    for c in conns:
        row = existing.get(c["id"])
        if row is None:
            pos += 1
            session.add(McpServer(id=c["id"], name=_display(c["id"]), url=c["url"],
                                  tools="—", on=c["on"], desc="", position=pos))
        else:
            row.url, row.on = c["url"], c["on"]
    for rid, row in existing.items():
        if rid not in ids:
            session.delete(row)
    session.commit()


# --------------------------------------------------------------- outbound edits
def add(session, name, url, token=None):
    """Register a connector in Hermes, then mirror it back. Returns the row."""
    key = _slug(name)
    if token:
        if re.search(r"[\r\n\x00]", token):
            raise HermesError("invalid token")
        env = _run(f"cat {_ENV} 2>/dev/null || true")
        _write(_ENV, _upsert_env(env, f"MCP_{key.upper()}_API_KEY", token))
    _write(_CONFIG, _add_to_config(_read(_CONFIG), key, url, header_auth=bool(token)))
    _restart()
    mirror(session)
    row = session.get(McpServer, key)
    if row is None:
        raise HermesError("connector written to Hermes but sync did not return it")
    row.name = name.strip()
    session.commit()
    return row


def set_enabled(session, key, on):
    """Flip a connector's ``enabled`` flag in Hermes, then mirror. Returns the row."""
    _write(_CONFIG, _set_enabled_in_config(_read(_CONFIG), key, on))
    _restart()
    mirror(session)
    return session.get(McpServer, key)


def remove(session, key):
    """Delete a connector from Hermes, then mirror it out of the table."""
    _write(_CONFIG, _remove_from_config(_read(_CONFIG), key))
    _restart()
    mirror(session)


# --------------------------------------------------------------- periodic sync
def _sync_once(app):
    with app.app_context():
        try:
            mirror(app.db_session)
        finally:
            app.db_session.remove()


def start_background_sync(app):  # pragma: no cover - background thread wiring
    """Mirror Hermes into the DB on a timer so out-of-band CLI edits surface."""
    if not enabled():
        return None
    interval = float(os.environ.get("PANTHEOS_HERMES_SYNC_INTERVAL", "60"))

    def loop():
        while True:
            time.sleep(interval)
            try:
                _sync_once(app)
            except Exception:
                pass

    t = threading.Thread(target=loop, name="hermes-sync", daemon=True)
    t.start()
    return t
