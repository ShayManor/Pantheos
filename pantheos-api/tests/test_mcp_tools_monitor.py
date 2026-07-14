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
