"""Pure parsing for Docker's per-container JSON stdout/stderr logs.

Sibling of ``caddy_logs``: where that shapes Caddy *access* lines, this shapes a
container's own stdout/stderr as written by Docker's ``json-file`` log driver
(``/var/lib/docker/containers/<hash>/<hash>-json.log``). Each line is a JSON
record ``{"log","stream","time"}``. There is no HTTP status to key a level off,
so ``level`` is a text heuristic. No I/O and no wall-clock here — the ingest loop
in ``docker_log_ingest`` owns the file tailing and cursor.
"""
import json
from datetime import datetime

_ERR_MARKERS = ("ERROR", "CRITICAL", "FATAL", "TRACEBACK")
_WARN_MARKERS = ("WARN", "WARNING")


def _epoch(tstr):
    """RFC3339 (``…Z`` or offset, up to nanoseconds) → epoch seconds."""
    if tstr.endswith("Z"):
        tstr = tstr[:-1] + "+00:00"
    return datetime.fromisoformat(tstr).timestamp()


def parse_line(line):
    """One json-file log line → ``{"ts", "msg"}``, or None if unparseable."""
    try:
        rec = json.loads(line)
        return {"ts": _epoch(rec["time"]), "msg": rec["log"].rstrip("\n")}
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def level(msg):
    """Best-effort log level from line text (stdout carries no status code)."""
    up = msg.upper()
    if any(m in up for m in _ERR_MARKERS):
        return "err"
    if any(m in up for m in _WARN_MARKERS):
        return "warn"
    return "info"


def name_from_config(config_json):
    """The container's Docker ``Name`` (leading ``/`` stripped), or None."""
    try:
        name = json.loads(config_json)["Name"]
    except (ValueError, KeyError, TypeError):
        return None
    return name.lstrip("/") if name else None
