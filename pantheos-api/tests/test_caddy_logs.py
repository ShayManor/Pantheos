import json

import pytest

from app import caddy_logs

T = 1_000_000_000.0  # fixed "newest" timestamp so windowing is deterministic
PANTH = caddy_logs.PANTHEOS_HOSTS
RV = caddy_logs.RESEARCHVIEWER_HOSTS


def _line(host, method, uri, status, dur, ts, ip="1.2.3.4"):
    return json.dumps({
        "ts": ts,
        "request": {"method": method, "host": host, "uri": uri,
                    "client_ip": "127.0.0.1",
                    "headers": {"Cf-Connecting-Ip": [ip]}},
        "duration": dur,
        "status": status,
    })


# pantheos: 6 matched entries across 3 client IPs; researchviewer: 2 across 2 IPs.
FIXTURE_LINES = [
    _line("pantheos.app", "GET", "/", 200, 0.010, T - 10, "10.0.0.1"),
    _line("pantheos.app", "GET", "/api/tickets", 200, 0.020, T - 8, "10.0.0.1"),
    _line("pantheos.app", "POST", "/api/tickets", 500, 0.030, T - 6, "10.0.0.2"),
    _line("pantheos.app:8443", "GET", "/healthz", 404, 0.005, T - 4, "10.0.0.1"),
    _line("www.pantheos.app", "GET", "/", 301, 0.002, T - 2, "10.0.0.3"),
    _line("researchviewer.org", "GET", "/", 200, 0.100, T - 5, "20.0.0.1"),
    _line("researchviewer.org", "GET", "/paper/1", 200, 0.050, T - 3, "20.0.0.2"),
    _line("gh-stats.com", "GET", "/", 200, 0.030, T - 1, "30.0.0.1"),   # neither set
    _line("pantheos.app", "GET", "/favicon.ico", 200, 0.040, T, "10.0.0.2"),  # newest
    "this is not json",                                                  # skipped
    json.dumps({"ts": T - 3, "request": {"host": "pantheos.app"}}),      # missing fields
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


def test_logs_filter_pantheos(logfile):
    lines = caddy_logs.logs(PANTH)
    assert len(lines) == 6  # www + :port in; researchviewer, gh-stats, junk out
    assert lines[2]["msg"] == "POST /api/tickets 500 30ms" and lines[2]["lvl"] == "err"
    assert lines[3]["msg"] == "GET /healthz 404 5ms" and lines[3]["lvl"] == "warn"
    assert lines[4]["lvl"] == "info"  # 3xx
    assert lines[-1]["msg"] == "GET /favicon.ico 200 40ms"


def test_logs_filter_researchviewer_isolated(logfile):
    lines = caddy_logs.logs(RV)
    assert len(lines) == 2
    assert lines[-1]["msg"] == "GET /paper/1 200 50ms"
    assert all("pantheos" not in l["msg"] for l in lines)


def test_logs_respects_limit(logfile):
    assert len(caddy_logs.logs(PANTH, limit=2)) == 2
    assert caddy_logs.logs(PANTH, limit=2)[-1]["msg"] == "GET /favicon.ico 200 40ms"


def test_rollup_pantheos(logfile):
    r = caddy_logs.rollup(PANTH)
    assert r["err"] == "16.7%"    # 1 of 6 is 5xx
    assert r["rps"] == "0.6/s"    # 6 reqs over a 10s span
    assert r["p95"] == "40 ms"


def test_metrics_pantheos(logfile):
    m = caddy_logs.metrics(PANTH)
    assert m["off"] is False and len(m["series"]) == 20
    assert sum(p["v"] for p in m["series"]) == 6
    assert m["series"][-1]["v"] == 6


def test_visitors_counts_distinct_client_ips(logfile):
    assert caddy_logs.visitors(PANTH) == 3   # 10.0.0.1/.2/.3
    assert caddy_logs.visitors(RV) == 2      # 20.0.0.1/.2


def test_visitors_falls_back_to_client_ip_without_header(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    rec = {"ts": T, "duration": 0.01, "status": 200,
           "request": {"method": "GET", "host": "researchviewer.org", "uri": "/",
                       "client_ip": "9.9.9.9", "headers": {}}}
    p.write_text(json.dumps(rec) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    assert caddy_logs.visitors(RV) == 1


def test_logs_empty_when_unset(monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert caddy_logs.logs(PANTH) == []


def test_tail_read_bounds_to_recent_lines(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    lines = [_line("pantheos.app", "GET", "/OLDEST", 200, 0.01, T - 5000)]
    lines += [_line("pantheos.app", "GET", f"/p{i}", 200, 0.01, T - 3000 + i)
              for i in range(3000)]
    lines += [_line("pantheos.app", "GET", "/NEWEST", 200, 0.01, T)]
    p.write_text("\n".join(lines) + "\n")
    assert p.stat().st_size > 262_144
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    rows = caddy_logs.logs(PANTH)
    assert rows[-1]["msg"] == "GET /NEWEST 200 10ms"
    assert not any("/OLDEST" in r["msg"] for r in rows)


def test_empty_when_no_matching_entries(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    p.write_text(_line("pantheos.app", "GET", "/", 200, 0.1, T) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    assert caddy_logs.logs(RV) == []
    assert caddy_logs.rollup(RV) == {"rps": "0/s", "err": "0.0%", "p95": "—"}
    assert caddy_logs.visitors(RV) == 0
    m = caddy_logs.metrics(RV)
    assert len(m["series"]) == 20 and sum(p["v"] for p in m["series"]) == 0
