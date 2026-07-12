from flask import Blueprint, jsonify

from . import db, get_or_404
from .. import metrics
from ..models import Area, Container, Host, Project

bp = Blueprint("monitor", __name__, url_prefix="/api")


@bp.get("/areas")
def list_areas():
    rows = db().query(Area).order_by(Area.position).all()
    return jsonify([a.to_dict() for a in rows])


@bp.get("/projects")
def list_projects():
    rows = db().query(Project).order_by(Project.position).all()
    return jsonify({p.key: p.to_dict() for p in rows})


@bp.get("/hosts")
def list_hosts():
    rows = db().query(Host).order_by(Host.position).all()
    return jsonify({h.id: h.to_dict() for h in rows})


@bp.get("/containers")
def list_containers():
    rows = db().query(Container).order_by(Container.position).all()
    return jsonify([c.to_dict() for c in rows])


@bp.get("/containers/<cid>/metrics")
def container_metrics(cid):
    c = get_or_404(Container, cid)
    return jsonify(metrics.container_metrics(c))


@bp.get("/containers/<cid>/logs")
def container_logs(cid):
    c = get_or_404(Container, cid)
    return jsonify({"lines": metrics.container_logs(c)})


@bp.get("/monitor/usage")
def usage():
    return jsonify(metrics.usage_series())


@bp.get("/monitor/errseries")
def errseries():
    return jsonify(metrics.error_series())
