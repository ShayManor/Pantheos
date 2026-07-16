from app.mcp import tools


def test_list_hosts_and_containers(session):
    hosts = tools.list_hosts(session)["hosts"]
    assert hosts and "id" in hosts[0]
    all_c = tools.list_containers(session)["containers"]
    assert all_c
    merlin = tools.list_containers(session, project="merlin")["containers"]
    assert all(c["proj"] == "merlin" for c in merlin)
    losers = tools.list_containers(session, status="los")["containers"]
    assert all(c["status"] == "los" for c in losers)


def test_get_container_and_logs(session):
    cid = tools.list_containers(session)["containers"][0]["id"]
    assert tools.get_container(session, cid)["id"] == cid
    logs = tools.get_container_logs(session, cid)["lines"]
    assert logs and "msg" in logs[0]
    assert tools.get_container(session, "NOPE") == {"error": "unknown container", "id": "NOPE"}
    assert tools.get_container_logs(session, "NOPE") == {"error": "unknown container", "id": "NOPE"}


def test_restart_container(session):
    # pick a degraded container so the reset is observable
    flt = next(c for c in tools.list_containers(session)["containers"] if c["status"] == "flt")
    out = tools.restart_container(session, flt["id"])
    assert out["status"] == "go" and out["up"] == "AOS" and out["err"] == "—"
    assert out["restarts"] == flt["restarts"] + 1
    assert tools.restart_container(session, "NOPE") == {"error": "unknown container", "id": "NOPE"}


def test_list_containers_by_host(session):
    cid = tools.list_containers(session)["containers"][0]["id"]
    host = tools.get_container(session, cid)["host"]
    by_host = tools.list_containers(session, host=host)["containers"]
    assert by_host and all(c["host"] == host for c in by_host)


def test_host_crud_and_get(session):
    made = tools.create_host(session, "edge", "Edge Box", kind="intermittent",
                             icon="Cpu", tag="EDGE", loc="lab")
    assert made == {"id": "edge", "name": "Edge Box", "kind": "intermittent",
                    "icon": "Cpu", "tag": "EDGE", "loc": "lab"}
    assert tools.get_host(session, "edge")["name"] == "Edge Box"
    up = tools.update_host(session, "edge", name="Edge2", loc="apt")
    assert up["name"] == "Edge2" and up["loc"] == "apt"
    assert tools.delete_host(session, "edge") == {"deleted": "edge"}
    assert tools.get_host(session, "edge")["error"] == "unknown host"
    # validation + not-found + exists
    assert tools.create_host(session, " ", "x")["error"] == "id and name required"
    assert tools.create_host(session, "minipc", "dup")["error"] == "host exists"
    assert tools.update_host(session, "nope")["error"] == "unknown host"
    assert tools.delete_host(session, "nope")["error"] == "unknown host"


def test_delete_host_guarded_by_containers(session):
    out = tools.delete_host(session, "minipc")
    assert out["error"] == "host has containers" and out["containers"] > 0


def test_container_crud(session):
    made = tools.create_container(session, "edge-api", "ghstats", "minipc", "api",
                                  status="cau", image="ghstats/edge")
    assert made["id"] == "edge-api" and made["status"] == "cau"
    assert made["proj"] == "ghstats" and made["host"] == "minipc"
    up = tools.update_container(session, "edge-api", status="go", cpu="9%", cpu_n=9)
    assert up["status"] == "go" and up["cpu"] == "9%" and up["cpuN"] == 9
    assert tools.delete_container(session, "edge-api") == {"deleted": "edge-api"}
    assert tools.get_container(session, "edge-api")["error"] == "unknown container"


def test_container_create_validation(session):
    assert tools.create_container(session, " ", "ghstats", "minipc", "api")["error"] == "id required"
    assert tools.create_container(session, "gh-stats-api", "ghstats", "minipc", "api")["error"] == "container exists"
    assert tools.create_container(session, "c1", "nope", "minipc", "api")["error"] == "unknown project"
    assert tools.create_container(session, "c1", "ghstats", "nope", "api")["error"] == "unknown host"
    assert tools.create_container(session, "c1", "ghstats", "minipc", "api", status="bad")["error"] == "invalid status"


def test_container_update_validation_and_missing(session):
    assert tools.update_container(session, "nope") == {"error": "unknown container", "id": "nope"}
    assert tools.update_container(session, "gh-stats-api", status="bad")["error"] == "invalid status"
    assert tools.update_container(session, "gh-stats-api", project_key="nope")["error"] == "unknown project"
    assert tools.update_container(session, "gh-stats-api", host_id="nope")["error"] == "unknown host"
    assert tools.delete_container(session, "nope") == {"error": "unknown container", "id": "nope"}
