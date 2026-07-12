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
