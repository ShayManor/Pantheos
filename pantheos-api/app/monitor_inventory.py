"""Static monitoring inventory — explicit, not label auto-discovery.

The spec's original design registered containers by Docker labels (Alloy reading
``pantheos.*`` off each container). We deliberately do NOT do that: this module
is the single, explicit map from a seeded container id to the real telemetry
sources for it — the cAdvisor container name, the Caddy vhost(s) fronting it, and
the public URL blackbox probes. Only containers listed here get real metrics;
every other container stays on the deterministic mock. Adding a service is a
one-line edit here, on purpose.
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
}

# project key -> Caddy vhost(s) whose distinct visitors back its "users" count.
PROJECT_HOSTS = {
    "rviewer": caddy_logs.RESEARCHVIEWER_HOSTS,
}


def entry(container_id):
    return INVENTORY.get(container_id)
