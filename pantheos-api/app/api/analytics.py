from flask import Blueprint, abort, jsonify, request

from . import db
from .. import analytics

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("/<site>")
def report(site):
    if site not in analytics.REPORTS:
        abort(404)
    return jsonify(analytics.REPORTS[site](db(), analytics._range_arg(request.args.get("range"))))


@bp.get("/<site>/users/<uid>")
def user(site, uid):
    out = analytics.USERS[site](db(), uid) if site in analytics.USERS else None
    if out is None:
        abort(404)
    return jsonify(out)
