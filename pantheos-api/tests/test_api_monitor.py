def test_areas(client):
    names = [a["name"] for a in client.get("/api/areas").get_json()]
    assert "IDEAS LAB" in names and "STAT 511" in names


def test_projects(client):
    d = client.get("/api/projects").get_json()
    assert "ghstats" in d
    assert d["ghstats"]["status"] == "flt"
    assert d["ghstats"]["area"] == "SIDE PROJECTS"
    assert d["ghstats"]["users"] == 3820


def test_hosts(client):
    d = client.get("/api/hosts").get_json()
    assert d["minipc"]["kind"] == "always_on"
    assert d["jetson"]["icon"] == "Cpu"


def test_containers(client):
    d = client.get("/api/containers").get_json()
    assert len(d) == 9
    api = next(c for c in d if c["id"] == "gh-stats-api")
    assert api["cpuN"] == 38
    assert api["proj"] == "ghstats"


def test_container_metrics(client):
    d = client.get("/api/containers/gh-stats-api/metrics").get_json()
    assert d["off"] is False and len(d["series"]) == 20
    assert client.get("/api/containers/NOPE/metrics").status_code == 404


def test_container_logs(client):
    d = client.get("/api/containers/gh-stats-api/logs").get_json()
    assert len(d["lines"]) > 0
    assert client.get("/api/containers/NOPE/logs").status_code == 404


def test_monitor_series(client):
    assert len(client.get("/api/monitor/usage").get_json()) == 14
    assert len(client.get("/api/monitor/errseries").get_json()) == 14


import json


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


def test_pantheos_container_uses_caddy_log(client, tmp_path, monkeypatch):
    _caddy_log(tmp_path, monkeypatch)
    m = client.get("/api/containers/gs-platform/metrics").get_json()
    assert m["off"] is False and len(m["series"]) == 20
    logs = client.get("/api/containers/gs-platform/logs").get_json()["lines"]
    assert any("/api/tickets" in l["msg"] for l in logs)
    assert any(l["lvl"] == "err" for l in logs)  # the 5xx line
    gs = next(c for c in client.get("/api/containers").get_json() if c["id"] == "gs-platform")
    assert gs["rps"].endswith("/s") and gs["err"] == "20.0%"  # 1 of 5 is 5xx


def test_pantheos_container_falls_back_to_mock_without_log(client, monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert len(client.get("/api/containers/gs-platform/metrics").get_json()["series"]) == 20
    assert len(client.get("/api/containers/gs-platform/logs").get_json()["lines"]) > 0
    gs = next(c for c in client.get("/api/containers").get_json() if c["id"] == "gs-platform")
    assert gs["rps"] == "12/s"  # seeded mock value, untouched
