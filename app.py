"""CodePulse -- Flask application factory and entry point.

A Python code analysis tool with AST parsing, complexity scoring,
Halstead metrics, maintainability index, and code smell detection.
"""

import os
import logging

from flask import Flask, jsonify, render_template

from config import HOST, PORT, DEBUG
from models.database import init_db
from routes.api import api_bp
from routes.views import views_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Updated for clarity
def create_app(testing: bool = False) -> Flask:
    """Application factory for CodePulse.

    Args:
        testing: If True, uses an in-memory SQLite database.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "codepulse-dev-secret")
    app.config["TESTING"] = testing

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Database
    init_db(app)

    # Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Template context processor
    @app.context_processor
    def inject_globals():
        return {"app_name": "CodePulse", "app_version": "1.0.1"}

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if _wants_json():
            return jsonify({"error": "Not found"}), 404
        return render_template("base.html", error="Page not found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        if _wants_json():
            return jsonify({"error": "Internal server error"}), 500
        return render_template("base.html", error="Internal server error"), 500

    @app.errorhandler(413)
    def too_large(error):
        if _wants_json():
            return jsonify({"error": "Request too large"}), 413
        return render_template("base.html", error="Request too large"), 413

    logger.info("CodePulse application created (testing=%s)", testing)
    return app


def _wants_json() -> bool:
    """Check if the client prefers JSON responses."""
    from flask import request
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


app = create_app()

if __name__ == "__main__":
    logger.info("Starting CodePulse on %s:%d", HOST, PORT)
    app.run(host="0.0.0.0", port=8000, debug=DEBUG)
