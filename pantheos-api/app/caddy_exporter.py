"""Prometheus exporter for per-site Caddy telemetry.

Caddy's native Prometheus metrics carry no per-vhost label (every site shares
``server="srv0"``), so per-site request rate / 5xx / p95 can't come from them.
This exporter reuses the Caddy JSON access-log parsing in ``caddy_logs`` and
republishes the numbers as per-``site`` gauges that vmagent scrapes into
VictoriaMetrics (``site`` avoids colliding with the ``host`` machine label that
vmagent's external_labels add). It runs from the app image (``python -m app.caddy_exporter``)
with the access log mounted read-only; stdlib only, no prometheus_client dep.
"""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import caddy_logs

# (label, host set) — the canonical ``host`` label is the primary vhost.
SITES = [
    ("pantheos.app", caddy_logs.PANTHEOS_HOSTS),
    ("researchviewer.org", caddy_logs.RESEARCHVIEWER_HOSTS),
    ("gh-stats.com", caddy_logs.GHSTATS_HOSTS),
]

_GAUGES = [
    ("pantheos_caddy_rps", "rps", "Requests per second over the access-log tail window"),
    ("pantheos_caddy_err_ratio", "err_ratio", "5xx responses as a fraction of requests"),
    ("pantheos_caddy_p95_ms", "p95_ms", "p95 request latency in milliseconds"),
    ("pantheos_caddy_visitors", "visitors", "Distinct client IPs over the window"),
    ("pantheos_caddy_requests", "requests", "Request count over the window"),
]


def render_metrics():
    """The Prometheus text exposition body for all configured sites."""
    stats = {label: caddy_logs.stats(hosts) for label, hosts in SITES}
    lines = []
    for metric, key, help_text in _GAUGES:
        lines.append(f"# HELP {metric} {help_text}")
        lines.append(f"# TYPE {metric} gauge")
        for label, _hosts in SITES:
            lines.append(f'{metric}{{site="{label}"}} {stats[label][key]}')
    return "\n".join(lines) + "\n"


class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - HTTP transport
    def do_GET(self):
        body = render_metrics().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def serve(port=None):  # pragma: no cover - server loop
    port = port or int(os.environ.get("CADDY_EXPORTER_PORT", "9109"))
    HTTPServer(("0.0.0.0", port), _Handler).serve_forever()


if __name__ == "__main__":  # pragma: no cover
    serve()
