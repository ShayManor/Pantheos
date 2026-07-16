import json

from app import victoria
from app.api import monitor


def test_areas(client):
    names = [a["name"] for a in client.get("/api/areas").get_json()]
    assert "IDEAS LAB" in names and "STAT 511" in names


def test_projects(client):
    d = client.get("/api/projects").get_json()
    assert "ghstats" in d
    assert d["ghstats"]["status"] == "flt"
    assert d["ghstats"]["area"] == "SIDE PROJECTS"
    assert d["ghstats"]["users"] == 146


def test_hosts(client):
    d = client.get("/api/hosts").get_json()
    assert d["minipc"]["kind"] == "always_on"
    assert d["jetson"]["icon"] == "Cpu"


def test_containers(client):
    d = client.get("/api/containers").get_json()
    assert len(d) == 15
    api = next(c for c in d if c["id"] == "ghstats-generator")
    assert api["cpuN"] == 0                            # seeded neutral; live metrics come from the monitor
    assert api["proj"] == "ghstats"


def test_container_metrics(client):
    d = client.get("/api/containers/ghstats-generator/metrics").get_json()
    assert d["off"] is False and len(d["series"]) == 20
    assert client.get("/api/containers/NOPE/metrics").status_code == 404


def test_container_logs(client):
    d = client.get("/api/containers/ghstats-generator/logs").get_json()
    assert len(d["lines"]) > 0
    assert client.get("/api/containers/NOPE/logs").status_code == 404


def test_monitor_series(client):
    assert len(client.get("/api/monitor/usage").get_json()) == 14
    assert len(client.get("/api/monitor/errseries").get_json()) == 14


# --------------------------------------------------------------- VictoriaMetrics
# Container current-values, per-container series, and the overview charts come
# from VictoriaMetrics when it's reachable. We monkeypatch the victoria client so
# tests stay hermetic (no TSDB running); absent VM, everything falls back to mock.

def _use_vm(monkeypatch, values=None, range_vals=None, available=True):
    values = values or {}
    monkeypatch.setattr(victoria, "available", lambda: available)

    def q(promql):
        for sub, val in values.items():
            if sub in promql:
                return val
        return None

    monkeypatch.setattr(victoria, "query", q)
    monkeypatch.setattr(victoria, "query_range", lambda promql, **kw: range_vals)


_HEALTHY = {
    "container_cpu_usage": 17.4,
    "container_memory_working_set": 340 * 2 ** 20,
    "changes(container_start_time": 0,
    "pantheos_caddy_rps": 12.3,
    "pantheos_caddy_err_ratio": 0.001,
    "pantheos_caddy_p95_ms": 205.0,
    "probe_success": 1,
}


def _gs(client):
    return next(c for c in client.get("/api/containers").get_json() if c["id"] == "pantheos-app-1")


def test_container_values_from_victoria(client, monkeypatch):
    _use_vm(monkeypatch, _HEALTHY)
    gs = _gs(client)
    assert gs["cpu"] == "17%" and gs["cpuN"] == 17
    assert gs["mem"] == "340M"
    assert gs["restarts"] == 0
    assert gs["rps"] == "12.3/s"
    assert gs["err"] == "0.1%"
    assert gs["p95"] == "205 ms"
    assert gs["up"] == "AOS" and gs["status"] == "go"


def test_container_status_caution(client, monkeypatch):
    _use_vm(monkeypatch, {**_HEALTHY, "pantheos_caddy_p95_ms": 500.0})
    assert _gs(client)["status"] == "cau"


def test_container_status_fault_by_errors(client, monkeypatch):
    _use_vm(monkeypatch, {**_HEALTHY, "pantheos_caddy_err_ratio": 0.03})
    gs = _gs(client)
    assert gs["err"] == "3.0%" and gs["status"] == "flt"


def test_container_status_fault_by_restarts(client, monkeypatch):
    _use_vm(monkeypatch, {**_HEALTHY, "changes(container_start_time": 5})
    assert _gs(client)["status"] == "flt"


def test_container_down_from_blackbox(client, monkeypatch):
    _use_vm(monkeypatch, {**_HEALTHY, "probe_success": 0})
    gs = _gs(client)
    assert gs["up"] == "LOS" and gs["status"] == "los"


def test_container_memory_gigabytes(client, monkeypatch):
    _use_vm(monkeypatch, {**_HEALTHY, "container_memory_working_set": 2 * 2 ** 30})
    assert _gs(client)["mem"] == "2.0G"


def test_container_partial_vm_keeps_seeded(client, monkeypatch):
    # Only resource metrics present (exporter/blackbox down): request fields and
    # status stay at their seeded mock values rather than blanking.
    _use_vm(monkeypatch, {
        "container_cpu_usage": 5.0,
        "container_memory_working_set": 96 * 2 ** 20,
    })
    gs = _gs(client)
    assert gs["cpu"] == "5%" and gs["mem"] == "96M"
    assert gs["rps"] == "—"           # seeded (neutral), untouched
    assert gs["status"] == "go"       # seeded, not recomputed


def test_noninventory_container_stays_mock_under_vm(client, monkeypatch):
    _use_vm(monkeypatch, _HEALTHY)
    api = next(c for c in client.get("/api/containers").get_json() if c["id"] == "ghstats-generator")
    assert api["cpuN"] == 0 and api["rps"] == "—"     # seeded (neutral), non-inventory stays as-is


def test_container_metrics_from_victoria(client, monkeypatch):
    _use_vm(monkeypatch, range_vals=[3.0] * 20)
    d = client.get("/api/containers/pantheos-app-1/metrics").get_json()
    assert len(d["series"]) == 20 and d["series"][0] == {"d": 0, "v": 3.0}


def test_container_metrics_falls_back_when_query_fails(client, monkeypatch):
    _use_vm(monkeypatch, range_vals=None)  # VM up but query returns nothing
    d = client.get("/api/containers/pantheos-app-1/metrics").get_json()
    assert len(d["series"]) == 20


def test_usage_and_errseries_from_victoria(client, monkeypatch):
    _use_vm(monkeypatch, range_vals=[2.0] * 14)
    assert client.get("/api/monitor/usage").get_json()[0] == {"d": 0, "v": 2}
    assert client.get("/api/monitor/errseries").get_json()[0] == {"d": 0, "v": 2}


def test_usage_and_errseries_fall_back(client, monkeypatch):
    _use_vm(monkeypatch, range_vals=None)
    assert len(client.get("/api/monitor/usage").get_json()) == 14
    assert len(client.get("/api/monitor/errseries").get_json()) == 14


def test_parse_pct_helper():
    assert monitor._parse_pct("6.1%") == 6.1
    assert monitor._parse_pct("—") == 0.0


# ----------------------------------------------------------------- Caddy access log
# The access log still drives per-container LOG LINES and the project visitor
# count (VictoriaMetrics stores metrics, not log lines or per-visitor identity).

def _caddy_log(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    p.write_text("\n".join(
        json.dumps({"ts": 1e9 + i, "duration": 0.01 * (i + 1),
                    "status": 500 if i == 2 else 200,
                    "request": {"method": "GET", "host": "pantheos.app",
                                "uri": f"/api/tickets?p={i}"}})
        for i in range(5)) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    return p


def test_pantheos_logs_from_caddy(client, tmp_path, monkeypatch):
    _caddy_log(tmp_path, monkeypatch)
    logs = client.get("/api/containers/pantheos-app-1/logs").get_json()["lines"]
    assert any("/api/tickets" in l["msg"] for l in logs)
    assert any(l["lvl"] == "err" for l in logs)  # the 5xx line


def test_pantheos_logs_fall_back_to_mock(client, monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert len(client.get("/api/containers/pantheos-app-1/logs").get_json()["lines"]) > 0


def _rv_caddy_log(tmp_path, monkeypatch):
    ips = ["1.1.1.1", "1.1.1.1", "2.2.2.2", "3.3.3.3"]  # 3 distinct visitors
    p = tmp_path / "access.log"
    p.write_text("\n".join(
        json.dumps({"ts": 1e9 + i, "duration": 0.05, "status": 200,
                    "request": {"method": "GET", "host": "researchviewer.org",
                                "uri": f"/paper/{i}", "client_ip": "127.0.0.1",
                                "headers": {"Cf-Connecting-Ip": [ip]}}})
        for i, ip in enumerate(ips)) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))
    return p


def test_rviewer_logs_from_caddy(client, tmp_path, monkeypatch):
    _rv_caddy_log(tmp_path, monkeypatch)
    logs = client.get("/api/containers/researchviewer/logs").get_json()["lines"]
    assert logs and all("/paper/" in l["msg"] for l in logs)


def test_rviewer_project_users_are_real_visitor_count(client, tmp_path, monkeypatch):
    _rv_caddy_log(tmp_path, monkeypatch)
    projects = client.get("/api/projects").get_json()
    assert projects["rviewer"]["users"] == 3  # distinct Cf-Connecting-Ip count


def test_rviewer_project_users_none_without_log(client, monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert client.get("/api/projects").get_json()["rviewer"]["users"] is None
