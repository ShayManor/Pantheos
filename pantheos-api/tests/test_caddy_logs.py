import json
import os

import pytest

from app import caddy_logs

T = 1_000_000_000.0  # fixed "newest" timestamp so windowing is deterministic


def _line(host, method, uri, status, dur, ts):
    return json.dumps({
        "ts": ts,
        "request": {"method": method, "host": host, "uri": uri},
        "duration": dur,
        "status": status,
    })


# 6 pantheos-matched entries (incl. a :port host and www), 1 other host, plus junk.
FIXTURE_LINES = [
    _line("pantheos.app", "GET", "/", 200, 0.010, T - 10),
    _line("pantheos.app", "GET", "/api/tickets", 200, 0.020, T - 8),
    _line("pantheos.app", "POST", "/api/tickets", 500, 0.030, T - 6),
    _line("pantheos.app:8443", "GET", "/healthz", 404, 0.005, T - 4),
    _line("www.pantheos.app", "GET", "/", 301, 0.002, T - 2),
    _line("researchviewer.org", "GET", "/", 200, 0.100, T - 1),  # filtered out
    _line("pantheos.app", "GET", "/favicon.ico", 200, 0.040, T),  # newest
    "this is not json",                                            # skipped
    json.dumps({"ts": T - 3, "request": {"host": "pantheos.app"}}),  # missing fields → skipped
]


@pytest.fixture()
def logfile(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    p.write_text("\n".join(FIXTURE_LINES) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    return p


def test_available_true_when_readable(logfile):
    assert caddy_logs.available() is True


def test_available_false_when_unset(monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert caddy_logs.available() is False


def test_available_false_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(tmp_path / "nope.log"))
    assert caddy_logs.available() is False


def test_logs_filters_host_and_shapes_lines(logfile):
    lines = caddy_logs.logs()
    assert len(lines) == 6  # www + :port included, other host + junk excluded
    assert lines[0] == {"t": lines[0]["t"], "lvl": "info", "msg": "GET / 200 10ms"}
    assert lines[2]["msg"] == "POST /api/tickets 500 30ms" and lines[2]["lvl"] == "err"
    assert lines[3]["msg"] == "GET /healthz 404 5ms" and lines[3]["lvl"] == "warn"
    assert lines[4]["lvl"] == "info"  # 3xx
    # chronological, newest last
    assert lines[-1]["msg"] == "GET /favicon.ico 200 40ms"


def test_logs_respects_limit(logfile):
    assert len(caddy_logs.logs(limit=2)) == 2
    assert caddy_logs.logs(limit=2)[-1]["msg"] == "GET /favicon.ico 200 40ms"


def test_rollup_computes_rps_err_p95(logfile):
    r = caddy_logs.rollup()
    assert r["err"] == "16.7%"    # 1 of 6 is 5xx
    assert r["rps"] == "0.6/s"    # 6 reqs over a 10s span
    assert r["p95"] == "40 ms"    # 95th-pct of durations


def test_metrics_buckets_by_minute(logfile):
    m = caddy_logs.metrics()
    assert m["off"] is False
    assert len(m["series"]) == 20
    assert sum(p["v"] for p in m["series"]) == 6  # all matched entries counted
    assert m["series"][-1]["v"] == 6              # all within the last minute of newest ts


def test_logs_empty_when_unset(monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert caddy_logs.logs() == []


def test_tail_read_bounds_to_recent_lines(tmp_path, monkeypatch):
    # A file larger than the tail window: the oldest lines fall outside it.
    p = tmp_path / "access.log"
    lines = [_line("pantheos.app", "GET", "/OLDEST", 200, 0.01, T - 5000)]
    lines += [_line("pantheos.app", "GET", f"/p{i}", 200, 0.01, T - 3000 + i)
              for i in range(3000)]
    lines += [_line("pantheos.app", "GET", "/NEWEST", 200, 0.01, T)]
    p.write_text("\n".join(lines) + "\n")
    assert p.stat().st_size > 262_144  # exceeds the tail window
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    rows = caddy_logs.logs()
    assert rows[-1]["msg"] == "GET /NEWEST 200 10ms"
    assert not any("/OLDEST" in r["msg"] for r in rows)


def test_empty_when_no_matching_entries(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    p.write_text(_line("researchviewer.org", "GET", "/", 200, 0.1, T) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    assert caddy_logs.logs() == []
    assert caddy_logs.rollup() == {"rps": "0/s", "err": "0.0%", "p95": "—"}
    m = caddy_logs.metrics()
    assert len(m["series"]) == 20 and sum(p["v"] for p in m["series"]) == 0
