"""Thin VictoriaMetrics/PromQL client for the Monitor station.

Real container telemetry comes from VictoriaMetrics (``PANTHEOS_VM_URL``, default
the host-local ``http://127.0.0.1:8428`` the compose stack exposes). When VM is
unreachable — dev, CI, the E2E box — ``available()`` is False and the monitor
endpoints fall back to the deterministic mock in ``metrics.py``, so the suite
stays hermetic without a TSDB running. Only stdlib (urllib) is used; no new dep.
"""
import json
import os
import time
import urllib.parse
import urllib.request

_DEFAULT_URL = "http://127.0.0.1:8428"
_TIMEOUT = 1.5
_PROBE_TTL = 10.0  # seconds to cache the reachability probe

# (ok, monotonic_deadline) — module-level cache so we don't probe VM every request.
_probe_cache = (False, 0.0)


def base_url():
    return os.environ.get("PANTHEOS_VM_URL", _DEFAULT_URL).rstrip("/")


def _get(path, params):
    url = f"{base_url()}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def available():
    """True when VictoriaMetrics answers its health check (probe cached briefly)."""
    global _probe_cache
    ok, deadline = _probe_cache
    now = time.monotonic()
    if now < deadline:
        return ok
    try:
        with urllib.request.urlopen(f"{base_url()}/health", timeout=_TIMEOUT):
            ok = True
    except Exception:
        ok = False
    _probe_cache = (ok, now + _PROBE_TTL)
    return ok


def query(promql):
    """Instant query → the first sample's float value, or None on any failure."""
    try:
        data = _get("/api/v1/query", {"query": promql})
        result = data["data"]["result"]
        if not result:
            return None
        return float(result[0]["value"][1])
    except Exception:
        return None


def query_range(promql, minutes=20, points=20):
    """Range query → a list of ``points`` floats over the last ``minutes``.

    Anchored to VM's own ``time`` (server clock), bucketed evenly. Missing
    buckets read 0. Returns None on any failure so the caller can fall back.
    """
    try:
        now = query("time()")
        if now is None:
            return None
        start = now - minutes * 60
        step = max(1, int((now - start) / points))
        data = _get("/api/v1/query_range",
                    {"query": promql, "start": start, "end": now, "step": step})
        result = data["data"]["result"]
        values = result[0]["values"] if result else []
        buckets = [0.0] * points
        for ts, val in values:
            idx = int((float(ts) - start) / step)
            if 0 <= idx < points:
                buckets[idx] = float(val)
        return buckets
    except Exception:
        return None
