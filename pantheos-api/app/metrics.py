"""Deterministic mock telemetry — chart series and container logs.

Real monitoring is out of scope (see the goal). These generators are seeded and
free of randomness so the UI is stable and the E2E suite never flakes.
"""
import math


def _seed_of(value):
    if isinstance(value, str):
        return sum(ord(c) for c in value)
    return int(value)


def _noise(seed, i):
    """Deterministic pseudo-noise in [0, 1)."""
    x = math.sin((seed * 97 + i * 31) * 12.9898) * 43758.5453
    return x - math.floor(x)


def spark(base, n=14, amp=0.25, seed=0):
    """Deterministic analogue of the prototype's ``spark`` helper."""
    out = []
    for i in range(n):
        wobble = math.sin(i / 2.3) * amp * 0.5 + (_noise(seed, i) - 0.5) * amp
        out.append({"d": i, "v": max(0, round(base * (1 + wobble)))})
    return out


def container_metrics(container):
    """CPU-over-last-20-min series for a container, plus its off (LOS) flag."""
    off = container.up == "LOS"
    series = spark(container.cpu_n or 5, 20, 0.5, _seed_of(container.id))
    return {"series": series, "off": off}


def usage_series():
    """Daily-active users, last 14 days (the prototype's USAGE)."""
    return spark(3820, 14, 0.18, _seed_of("usage"))


def error_series():
    """gh-stats 5xx spike series (the prototype's ERRSERIES)."""
    base = spark(2, 14, 0.9, _seed_of("errors"))
    return [{"d": p["d"], "v": p["v"] + 5 if p["d"] > 10 else round(p["v"] * 0.4)} for p in base]


def log_timestamps(seed, n):
    """Deterministic, monotonically increasing HH:MM:SS stamps."""
    hh, mm = 14, 2
    out = []
    for i in range(1, n + 1):
        mm += 1 + int(_noise(seed, i) * 3)
        if mm >= 60:
            mm -= 60
            hh += 1
        ss = int(_noise(seed, i + 500) * 60)
        out.append(f"{hh:02d}:{mm:02d}:{ss:02d}")
    return out


def container_logs(container):
    """Deterministic log lines, mirroring the prototype's genLogs by status."""
    routes = ["/api/stats", "/api/user/shaymanor", "/healthz", "/api/repos", "/metrics"]
    seed = _seed_of(container.id)

    base = [
        ("info", f"starting {container.id} ({container.image})"),
        ("info", "connected to postgres · pool=10"),
    ]
    if container.up == "LOS":
        base += [
            ("info", "heartbeat ok"),
            ("warn", "no telemetry ack from collector"),
            ("err", "signal lost — host unreachable, entering intermittent mode"),
        ]
        ts = log_timestamps(seed, len(base))
        return [{"t": ts[i], "lvl": lvl, "msg": msg} for i, (lvl, msg) in enumerate(base)]

    for i in range(6):
        lat = 8 + int(_noise(seed, i + 100) * 40)
        base.append(("info", f"GET {routes[i % len(routes)]} 200 {lat}ms"))
    if container.status == "flt":
        base += [
            ("info", "GET /api/stats 200 42ms"),
            ("warn", "redis cache miss — falling through to cold path"),
            ("err", "TypeError: cannot read properties of undefined (reading 'window')"),
            ("err", "  at rateLimit (middleware/ratelimit.js:41:18)"),
            ("err", "GET /api/stats 500 3ms"),
            ("warn", "restarting worker (restart #4)"),
            ("info", "hotfix c8a91f applied · guard added, in-memory fallback active"),
            ("info", "GET /api/stats 200 39ms"),
        ]
    elif container.status == "cau":
        base += [
            ("warn", "upstream selector drift — 2 fields missing"),
            ("info", "scrape complete · 18/20 providers fresh"),
        ]
    else:
        base.append(("info", "GET /healthz 200 2ms"))
    ts = log_timestamps(seed, len(base))
    return [{"t": ts[i], "lvl": lvl, "msg": msg} for i, (lvl, msg) in enumerate(base)]
