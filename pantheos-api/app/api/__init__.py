"""API blueprints + shared helpers."""
from flask import abort, current_app


def db():
    """The request-scoped SQLAlchemy session."""
    return current_app.db_session


def get_or_404(model, id_):
    obj = db().get(model, id_)
    if obj is None:
        abort(404)
    return obj


def register_blueprints(app):
    from .admin import bp as admin_bp
    from .context import bp as context_bp
    from .delphi import bp as delphi_bp
    from .monitor import bp as monitor_bp
    from .tickets import bp as tickets_bp

    for bp in (tickets_bp, monitor_bp, delphi_bp, context_bp, admin_bp):
        app.register_blueprint(bp)
