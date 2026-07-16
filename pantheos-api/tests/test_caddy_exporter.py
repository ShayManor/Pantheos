import json

from app import caddy_exporter, caddy_logs


def _log(tmp_path, monkeypatch):
    p = tmp_path / "access.log"
    p.write_text("\n".join(
        json.dumps({"ts": 1e9 + i, "duration": 0.02,
                    "status": 500 if i == 0 else 200,
                    "request": {"method": "GET", "host": "pantheos.app",
                                "uri": "/", "client_ip": f"9.9.9.{i}"}})
        for i in range(4)) + "\n")
    monkeypatch.setenv("CADDY_ACCESS_LOG", str(p))


def test_render_metrics_exposes_per_site_gauges(tmp_path, monkeypatch):
    _log(tmp_path, monkeypatch)
    body = caddy_exporter.render_metrics()
    assert "# TYPE pantheos_caddy_rps gauge" in body
    assert 'pantheos_caddy_rps{host="pantheos.app"}' in body
    # researchviewer has no entries → zeroed series still present
    assert 'pantheos_caddy_requests{host="researchviewer.org"} 0' in body
    # pantheos.app: 1 of 4 requests is 5xx
    assert 'pantheos_caddy_requests{host="pantheos.app"} 4' in body
    assert 'pantheos_caddy_err_ratio{host="pantheos.app"} 0.25' in body


def test_stats_empty(monkeypatch):
    monkeypatch.delenv("CADDY_ACCESS_LOG", raising=False)
    assert caddy_logs.stats(caddy_logs.PANTHEOS_HOSTS) == {
        "rps": 0.0, "err_ratio": 0.0, "p95_ms": 0.0, "visitors": 0, "requests": 0}
