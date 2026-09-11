"""Alertmanager webhook → P0 tickets (spec §4.8)."""


def _fire(client, fingerprint="abc123def456", status="firing", labels=None, annotations=None):
    payload = {"alerts": [{
        "status": status,
        "fingerprint": fingerprint,
        "labels": labels if labels is not None else {"alertname": "HighErrorRate",
                                                     "project": "ghstats", "severity": "critical"},
        "annotations": annotations if annotations is not None else {
            "summary": "ghstats 5xx over 5%", "description": "error budget burning"},
    }]}
    return client.post("/api/monitor/alerts", json=payload)


def _ticket(client, tid):
    return next((t for t in client.get("/api/tickets").get_json() if t["id"] == tid), None)


def test_firing_creates_p0_ticket(client):
    r = _fire(client, labels={"alertname": "HighErrorRate", "project": "ghstats",
                              "host": "minipc", "route": "/api/stats", "restarts": "4"})
    assert r.get_json()["created"] == ["ALR-ABC123DEF4"]
    t = _ticket(client, "ALR-ABC123DEF4")
    assert t is not None
    assert t["pri"] == 0 and t["score"] == "8.0" and t["hot"] is True and t["due"] == "now"
    assert t["proj"] == "ghstats" and t["source"] == "monitor"
    assert "route: /api/stats" in t["body"] and "restarts: 4" in t["body"]


def test_firing_ticket_body_carries_the_whole_alert(client):
    """Delphi reads the ticket body, so the alert's own query, start time and
    labels have to survive the webhook instead of being rebuilt by hand."""
    payload = {"alerts": [{
        "status": "firing", "fingerprint": "abc123def456",
        "labels": {"alertname": "HighErrorRate", "project": "groundstation",
                   "severity": "critical", "site": "pantheos.app",
                   "container": "pantheos-mcp-1"},
        "annotations": {"summary": "pantheos.app 5xx rate above 5%",
                        "description": "over 5% for 2m",
                        "runbook_url": "https://example.test/runbook"},
        "startsAt": "2026-09-11T14:49:00Z",
        "generatorURL": "http://vmalert:8880/vmalert/alert?expr=err_ratio",
    }]}
    client.post("/api/monitor/alerts", json=payload)
    body = _ticket(client, "ALR-ABC123DEF4")["body"]
    assert "site: pantheos.app" in body          # a label the fixed list dropped
    assert "container: pantheos-mcp-1" in body   # names the culprit outright
    assert "started: 2026-09-11T14:49:00Z" in body
    assert "vmalert:8880" in body                # the query behind the alert
    assert "https://example.test/runbook" in body


def test_refire_is_deduped(client):
    _fire(client)
    r = _fire(client)  # same fingerprint
    assert r.get_json()["created"] == []
    tickets = [t for t in client.get("/api/tickets").get_json() if t["id"] == "ALR-ABC123DEF4"]
    assert len(tickets) == 1


def test_unknown_project_falls_back_to_first_area(client):
    r = _fire(client, labels={"alertname": "HostDown", "project": "nope"})
    assert r.get_json()["created"] == ["ALR-ABC123DEF4"]
    t = _ticket(client, "ALR-ABC123DEF4")
    assert t["proj"] is None and t["area"]  # attached to an area


def test_no_project_label(client):
    r = _fire(client, labels={"alertname": "DiskFull"}, annotations={})
    assert r.get_json()["created"] == ["ALR-ABC123DEF4"]
    t = _ticket(client, "ALR-ABC123DEF4")
    assert t["title"] == "DiskFull"  # falls back to alertname


def test_resolved_archives_untouched_ticket(client):
    _fire(client)
    r = _fire(client, status="resolved")
    assert r.get_json()["archived"] == ["ALR-ABC123DEF4"]
    assert _ticket(client, "ALR-ABC123DEF4")["life"] == "archived"


def test_resolved_leaves_touched_ticket(client):
    _fire(client)
    client.post("/api/tickets/ALR-ABC123DEF4/launch")  # sets agent=executing
    r = _fire(client, status="resolved")
    assert r.get_json()["archived"] == []
    assert _ticket(client, "ALR-ABC123DEF4")["life"] != "archived"


def test_resolved_unknown_ticket_noop(client):
    r = _fire(client, fingerprint="zzz999", status="resolved")
    assert r.get_json() == {"created": [], "archived": []}


def test_alert_without_fingerprint_skipped(client):
    r = client.post("/api/monitor/alerts", json={"alerts": [{"status": "firing", "labels": {}}]})
    assert r.get_json() == {"created": [], "archived": []}


def test_empty_payload(client):
    r = client.post("/api/monitor/alerts", json={})
    assert r.get_json() == {"created": [], "archived": []}
