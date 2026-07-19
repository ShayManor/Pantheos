"""Static monitoring inventory — explicit, not label auto-discovery.

The spec's original design registered containers by Docker labels (Alloy reading
``pantheos.*`` off each container). We deliberately do NOT do that: this module
is the single, explicit map from a seeded container id to the real telemetry
sources for it — the cAdvisor container name, the Caddy vhost(s) fronting it, and
the public URL blackbox probes. Only containers listed here get real metrics;
every other container stays on the deterministic mock. Adding a service is a
one-line edit here, on purpose.

An entry always carries ``cadvisor`` (cAdvisor scrapes every container by name,
so CPU / memory / restarts are always available). ``hosts`` / ``site`` / ``probe``
are optional and only present for containers a public Caddy vhost fronts: with
them a container also gets request rate / 5xx / p95 / uptime and access-log
lines; without them it's a cAdvisor-only entry (internal sidecars — db, mcp,
workers, crons — that have no vhost). ``gpu-api`` is deliberately absent: it runs
on Cloud Run, invisible to the minipc's cAdvisor, so it stays on the mock.
"""
from . import caddy_logs

# container id -> telemetry sources
INVENTORY = {
    "pantheos-app-1": {
        "cadvisor": "pantheos-app-1",
        "hosts": caddy_logs.PANTHEOS_HOSTS,
        "site": "pantheos.app",          # the caddy-exporter `host` label
        "probe": "https://pantheos.app",
    },
    "researchviewer": {
        "cadvisor": "researchviewer",
        "hosts": caddy_logs.RESEARCHVIEWER_HOSTS,
        "site": "researchviewer.org",
        "probe": "https://researchviewer.org",
    },
    # gh-stats.com is served by the generator (:5002), so it's a full site entry;
    # the rest of the gh-stats stack is internal (cAdvisor-only).
    "ghstats-generator": {
        "cadvisor": "ghstats-generator",
        "hosts": caddy_logs.GHSTATS_HOSTS,
        "site": "gh-stats.com",
        "probe": "https://gh-stats.com",
    },
    "ghstats-edge": {"cadvisor": "ghstats-edge"},
    "ghstats-generator-worker": {"cadvisor": "ghstats-generator-worker"},
    "ghstats-generator-cron": {"cadvisor": "ghstats-generator-cron"},
    "ghstats-fetcher": {"cadvisor": "ghstats-fetcher"},
    "ghstats-fetcher-cron": {"cadvisor": "ghstats-fetcher-cron"},
    # The pantheos stack watching itself — internal sidecars, no public vhost.
    "pantheos-mcp-1": {"cadvisor": "pantheos-mcp-1"},
    "pantheos-db-1": {"cadvisor": "pantheos-db-1"},
    "pantheos-caddy-log-exporter-1": {"cadvisor": "pantheos-caddy-log-exporter-1"},
}

# project key -> Caddy vhost(s) whose distinct visitors back its "users" count.
PROJECT_HOSTS = {
    "rviewer": caddy_logs.RESEARCHVIEWER_HOSTS,
}


def entry(container_id):
    return INVENTORY.get(container_id)
