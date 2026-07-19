"""Real telemetry parsed from the Caddy access log, per site.

Unlike the deterministic mocks in ``metrics.py``, these read actual request
lines from Caddy's JSON access log (path in the ``CADDY_ACCESS_LOG`` env var),
filtered to a given set of hosts. When the log is absent — dev, CI, the E2E box
— ``available()`` is False and the monitor endpoints fall back to the mock, so
the suite stays deterministic. Windows are relative to the newest log entry,
never the wall clock, for the same reason.
"""
import json
import math
import os
import time

PANTHEOS_HOSTS = {"pantheos.app", "www.pantheos.app"}
RESEARCHVIEWER_HOSTS = {"researchviewer.org", "www.researchviewer.org"}
GHSTATS_HOSTS = {"gh-stats.com", "www.gh-stats.com"}
_TAIL_BYTES = 262_144


def _log_path():
    return os.environ.get("CADDY_ACCESS_LOG")


def available():
    p = _log_path()
    return bool(p and os.path.isfile(p) and os.access(p, os.R_OK))


def _client_ip(req):
    """Real visitor IP: Cloudflare's connecting-IP header, else XFF, else the peer."""
    headers = req.get("headers", {})
    forwarded = headers.get("Cf-Connecting-Ip") or headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded[0].split(",")[0].strip()
    return req.get("client_ip", "")


def _entries(hosts):
    """Parsed request records for ``hosts`` from the tail of the log, oldest first."""
    p = _log_path()
    if not p:
        return []
    with open(p, "rb") as f:
        f.seek(0, os.SEEK_END)
        start = max(0, f.tell() - _TAIL_BYTES)
        f.seek(start)
        lines = f.read().decode("utf-8", "replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]  # first line is likely a partial record
    out = []
    for line in lines:
        try:
            rec = json.loads(line)
            req = rec["request"]
            if req["host"].split(":", 1)[0] not in hosts:
                continue
            out.append({
                "ts": float(rec["ts"]),
                "method": req["method"],
                "uri": req["uri"],
                "status": int(rec["status"]),
                "dur": float(rec["duration"]),
                "ip": _client_ip(req),
            })
        except (ValueError, KeyError, TypeError):
            continue
    return out


def _level(status):
    if status >= 500:
        return "err"
    if status >= 400:
        return "warn"
    return "info"


def _hhmmss(ts):
    lt = time.localtime(ts)
    return f"{lt.tm_hour:02d}:{lt.tm_min:02d}:{lt.tm_sec:02d}"


def logs(hosts, limit=20):
    """Recent access lines shaped like the mock's container logs, oldest first."""
    return [{
        "t": _hhmmss(e["ts"]),
        "lvl": _level(e["status"]),
        "msg": f'{e["method"]} {e["uri"]} {e["status"]} {round(e["dur"] * 1000)}ms',
    } for e in _entries(hosts)[-limit:]]


def rollup(hosts):
    """Current REQ/S, 5XX rate, and P95 latency over the tail window."""
    es = _entries(hosts)
    if not es:
        return {"rps": "0/s", "err": "0.0%", "p95": "—"}
    n = len(es)
    span = max(es[-1]["ts"] - es[0]["ts"], 1.0)
    err = round(100 * sum(1 for e in es if e["status"] >= 500) / n, 1)
    durs = sorted(e["dur"] for e in es)
    p95 = round(durs[max(0, math.ceil(0.95 * n) - 1)] * 1000)
    return {"rps": f"{round(n / span, 1)}/s", "err": f"{err}%", "p95": f"{p95} ms"}


def metrics(hosts):
    """Per-minute request counts for the last 20 minutes (chart series)."""
    es = _entries(hosts)
    series = [{"d": i, "v": 0} for i in range(20)]
    if es:
        newest = es[-1]["ts"]
        for e in es:
            bucket = 19 - int((newest - e["ts"]) // 60)
            if 0 <= bucket <= 19:
                series[bucket]["v"] += 1
    return {"series": series, "off": False}


def visitors(hosts):
    """Distinct client IPs seen for ``hosts`` over the tail window."""
    return len({e["ip"] for e in _entries(hosts) if e["ip"]})


def stats(hosts):
    """Numeric telemetry for ``hosts`` — the raw values the exporter publishes.

    Returns floats/ints (unlike ``rollup``, which formats for the UI): requests
    per second, 5xx ratio in [0, 1], p95 latency in ms, distinct visitors, and
    the request count over the tail window.
    """
    es = _entries(hosts)
    n = len(es)
    if not es:
        return {"rps": 0.0, "err_ratio": 0.0, "p95_ms": 0.0, "visitors": 0, "requests": 0}
    span = max(es[-1]["ts"] - es[0]["ts"], 1.0)
    durs = sorted(e["dur"] for e in es)
    p95 = durs[max(0, math.ceil(0.95 * n) - 1)] * 1000
    return {
        "rps": n / span,
        "err_ratio": sum(1 for e in es if e["status"] >= 500) / n,
        "p95_ms": p95,
        "visitors": len({e["ip"] for e in es if e["ip"]}),
        "requests": n,
    }
