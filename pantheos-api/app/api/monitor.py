from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import db, get_or_404
from .. import caddy_logs, logview, metrics, scoring, victoria
from ..models import Area, Container, Host, LogLine, Project, Ticket
from ..monitor_inventory import INVENTORY, PROJECT_HOSTS, entry

bp = Blueprint("monitor", __name__, url_prefix="/api")

_DAYS = 14


@bp.get("/areas")
def list_areas():
    rows = db().query(Area).order_by(Area.position).all()
    return jsonify([a.to_dict() for a in rows])


@bp.get("/projects")
def list_projects():
    rows = db().query(Project).order_by(Project.position).all()
    out = {p.key: p.to_dict() for p in rows}
    # Real recent-visitor count (distinct client IPs) from the Caddy access log;
    # VictoriaMetrics stores metrics, not per-visitor identity, so this stays log-derived.
    if caddy_logs.available():
        for key, hosts in PROJECT_HOSTS.items():
            if key in out:
                out[key]["users"] = caddy_logs.visitors(hosts)
    return jsonify(out)


@bp.get("/hosts")
def list_hosts():
    rows = db().query(Host).order_by(Host.position).all()
    return jsonify({h.id: h.to_dict() for h in rows})


@bp.get("/containers")
def list_containers():
    rows = db().query(Container).order_by(Container.position).all()
    out = [c.to_dict() for c in rows]
    if victoria.available():
        by_id = {c.id: c for c in rows}
        for d in out:
            inv = entry(d["id"])
            if inv:
                _apply_real(d, inv)
    return jsonify(out)


@bp.get("/containers/<cid>/metrics")
def container_metrics(cid):
    c = get_or_404(Container, cid)
    inv = entry(cid)
    if inv and victoria.available():
        name = inv["cadvisor"]
        vals = victoria.query_range(
            f'sum(rate(container_cpu_usage_seconds_total{{name="{name}"}}[2m])) * 100')
        if vals is not None:
            series = [{"d": i, "v": round(v, 1)} for i, v in enumerate(vals)]
            return jsonify({"series": series, "off": c.up == "LOS"})
    elif victoria.available():
        # Real monitoring is up but this container isn't in the inventory: show
        # nothing rather than a fabricated series.
        return jsonify({"series": [], "off": c.up == "LOS", "monitored": False})
    return jsonify(metrics.container_metrics(c))


def _log_sources(cid, inv):
    """Which stored sources back this container's logs — mirrors _apply_real's split."""
    if not caddy_logs.available():
        return ["mock"]
    if not inv:
        return []                       # not in the monitoring inventory
    srcs = ["docker"]                   # every inventory container serves its stdout
    if inv.get("hosts"):
        srcs.append("caddy")            # vhost containers also show HTTP access lines
    return srcs


@bp.get("/containers/<cid>/logs")
def container_logs(cid):
    get_or_404(Container, cid)
    srcs = _log_sources(cid, entry(cid))
    if not srcs:
        return jsonify({"items": [], "next": None, "monitored": False})
    before = request.args.get("before", type=int)
    limit = min(request.args.get("limit", default=200, type=int), 500)
    q = db().query(LogLine).filter(LogLine.container_id == cid, LogLine.source.in_(srcs))
    if before is not None:
        q = q.filter(LogLine.id < before)
    rows = q.order_by(LogLine.id.desc()).limit(limit).all()
    nxt = rows[-1].id if len(rows) == limit else None
    if request.args.get("mode") == "raw":
        items = [{"type": "line", **logview.line(r)} for r in rows]
    else:
        items = logview.collapse(rows)
    return jsonify({"items": items, "next": nxt, "monitored": True})


@bp.get("/containers/<cid>/logs/range")
def container_log_range(cid):
    get_or_404(Container, cid)
    srcs = _log_sources(cid, entry(cid))
    if not srcs:
        return jsonify({"lines": []})
    lo = request.args.get("from", type=int)
    hi = request.args.get("to", type=int)
    rows = (db().query(LogLine).filter(LogLine.container_id == cid, LogLine.source.in_(srcs))
            .filter(LogLine.id >= lo, LogLine.id <= hi)
            .order_by(LogLine.id.desc()).all())
    return jsonify({"lines": [logview.line(r) for r in rows]})


@bp.get("/monitor/usage")
def usage():
    if victoria.available():
        vals = victoria.query_range(
            "sum(rate(caddy_http_requests_total[1h]))", minutes=_DAYS * 24 * 60, points=_DAYS)
        if vals is not None:
            return jsonify([{"d": i, "v": round(v)} for i, v in enumerate(vals)])
    return jsonify(metrics.usage_series())


@bp.get("/monitor/errseries")
def errseries():
    if victoria.available():
        vals = victoria.query_range(
            'sum(rate(caddy_http_requests_total{code=~"5.."}[1h]))',
            minutes=_DAYS * 24 * 60, points=_DAYS)
        if vals is not None:
            return jsonify([{"d": i, "v": round(v)} for i, v in enumerate(vals)])
    return jsonify(metrics.error_series())


@bp.post("/monitor/alerts")
def alerts_webhook():
    """Alertmanager webhook → P0 tickets (spec §4.8).

    Each firing alert becomes a top-of-queue P0 ticket on the matching project,
    deduped by the alert fingerprint (id ``ALR-<fp>``) so re-fires don't pile up.
    A ``resolved`` alert archives its auto-ticket if it was never touched.
    """
    payload = request.get_json(silent=True) or {}
    created, archived = [], []
    for alert in payload.get("alerts", []):
        labels = alert.get("labels", {})
        fp = alert.get("fingerprint") or ""
        tid = f"ALR-{fp[:10].upper()}" if fp else None
        if not tid:
            continue
        existing = db().get(Ticket, tid)
        if alert.get("status") == "resolved":
            if existing and existing.agent == "idle" and existing.life == "queued":
                existing.life = "archived"
                archived.append(tid)
            continue
        if existing:
            continue  # already open — dedupe
        _create_alert_ticket(tid, labels, alert.get("annotations", {}))
        created.append(tid)
    db().commit()
    return jsonify({"created": created, "archived": archived})


def _create_alert_ticket(tid, labels, annotations):
    project = db().get(Project, labels.get("project")) if labels.get("project") else None
    if project is not None:
        area_id = project.area_id
    else:
        area_id = db().query(Area.id).order_by(Area.position).limit(1).scalar()
    title = annotations.get("summary") or labels.get("alertname") or "monitoring alert"
    detail = [f"{k}: {v}" for k, v in (
        ("rule", labels.get("alertname")), ("host", labels.get("host")),
        ("route", labels.get("route")), ("restarts", labels.get("restarts")),
        ("severity", labels.get("severity"))) if v]
    body = annotations.get("description") or title
    if detail:
        body = body + "\n\n" + "\n".join(detail)
    score = scoring.compute_score(0, scoring.own_urgency(0, None))
    max_pos = db().query(func.max(Ticket.position)).scalar() or 0
    db().add(Ticket(
        id=tid, project_key=project.key if project else None, area_id=area_id,
        title=title, pri=0, deadline_hours=0, effort_hours=None, score=score,
        due=scoring.due_display(0), hot=scoring.is_hot(0), life="queued",
        agent="idle", source="monitor", summary=title, body=body,
        report=None, result=None, position=max_pos + 1))


def _parse_pct(s):
    try:
        return float(str(s).rstrip("%").strip())
    except ValueError:
        return 0.0


def _fmt_bytes(v):
    if v >= 2 ** 30:
        return f"{v / 2 ** 30:.1f}G"
    return f"{round(v / 2 ** 20)}M"


def _derive_status(err_pct, p95_ms, restarts, up):
    if up == "LOS":
        return "los"
    if err_pct > 2.0 or (p95_ms is not None and p95_ms > 1000) or restarts > 3:
        return "flt"
    if err_pct > 0.5 or (p95_ms is not None and p95_ms > 400):
        return "cau"
    return "go"


def _apply_real(d, inv):
    """Overlay live VictoriaMetrics values onto a container's serialized dict.

    Each field is overridden only when its query returns a value, so partial VM
    data (e.g. exporter down) degrades field-by-field to the seeded mock rather
    than blanking the card.
    """
    name = inv["cadvisor"]
    site, probe = inv.get("site"), inv.get("probe")
    cpu = victoria.query(f'sum(rate(container_cpu_usage_seconds_total{{name="{name}"}}[2m])) * 100')
    mem = victoria.query(f'sum(container_memory_working_set_bytes{{name="{name}"}})')
    restarts = victoria.query(f'sum(changes(container_start_time_seconds{{name="{name}"}}[1h]))')
    # Request telemetry / uptime only exist for containers a public Caddy vhost
    # fronts; internal sidecars (no site/probe) keep their seeded request fields.
    rps = victoria.query(f'pantheos_caddy_rps{{site="{site}"}}') if site else None
    err = victoria.query(f'pantheos_caddy_err_ratio{{site="{site}"}}') if site else None
    p95 = victoria.query(f'pantheos_caddy_p95_ms{{site="{site}"}}') if site else None
    up_probe = victoria.query(f'probe_success{{instance="{probe}"}}') if probe else None

    if cpu is not None:
        d["cpu"], d["cpuN"] = f"{round(cpu)}%", round(cpu)
    if mem is not None:
        d["mem"] = _fmt_bytes(mem)
    if restarts is not None:
        d["restarts"] = int(restarts)
    if rps is not None:
        d["rps"] = f"{round(rps, 1)}/s"
    if err is not None:
        d["err"] = f"{err * 100:.1f}%"
    if p95 is not None:
        d["p95"] = f"{round(p95)} ms"
    if up_probe is not None:
        d["up"] = "AOS" if up_probe >= 1 else "LOS"

    if err is not None or p95 is not None or up_probe is not None or restarts is not None:
        err_pct = err * 100 if err is not None else _parse_pct(d["err"])
        d["status"] = _derive_status(err_pct, p95, d["restarts"], d["up"])
