"""SQLAlchemy database setup for CodePulse."""

import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask application.

    Creates the instance directory if needed, configures SQLAlchemy,
    and ensures all tables exist.
    """
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    instance_dir = os.path.join(base_dir, "instance")
    os.makedirs(instance_dir, exist_ok=True)

    db_path = os.path.join(instance_dir, "codepulse.db")

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_pre_ping": True,
    })

    db.init_app(app)

    with app.app_context():
        from models.schemas import CodeAnalysis  # noqa: F401
        db.create_all()

    return db
