"""Per-area and per-project context (a CLAUDE.md for each area / project).

Stored as text on the entity (mock DB — the design spec's `claude_md_path`
becomes inline content here). View with GET, edit with PUT.
"""
from flask import Blueprint, jsonify, request

from . import db, get_or_404
from ..models import Area, Project

bp = Blueprint("context", __name__, url_prefix="/api")


def _get(obj):
    return jsonify({"context": obj.context or ""})


def _set(obj):
    data = request.get_json(silent=True) or {}
    ctx = data.get("context")
    if not isinstance(ctx, str):
        return jsonify({"error": "context must be a string"}), 400
    obj.context = ctx
    db().commit()
    return jsonify({"context": obj.context})


@bp.get("/areas/<aid>/context")
def get_area_context(aid):
    return _get(get_or_404(Area, aid))


@bp.put("/areas/<aid>/context")
def set_area_context(aid):
    return _set(get_or_404(Area, aid))


@bp.get("/projects/<key>/context")
def get_project_context(key):
    return _get(get_or_404(Project, key))


@bp.put("/projects/<key>/context")
def set_project_context(key):
    return _set(get_or_404(Project, key))
