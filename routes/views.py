"""HTML view blueprint for CodePulse."""

import json
from flask import Blueprint, render_template

from models.database import db
from models.schemas import CodeAnalysis
from services.data_service import get_recent_analyses, get_analysis_by_id, get_aggregate_stats

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Render the dashboard / main page."""
    recent = get_recent_analyses(db.session, limit=5)
    stats = get_aggregate_stats(db.session)
    return render_template("index.html", recent=recent, stats=stats)


@views_bp.route("/analyze")
def analyze_page():
    """Render the code analysis input page."""
    return render_template("analyze.html")


@views_bp.route("/history")
def history():
    """Render the analysis history page."""
    analyses = get_recent_analyses(db.session, limit=50)
    return render_template("history.html", analyses=analyses)


@views_bp.route("/analysis/<int:analysis_id>")
def detail(analysis_id):
    """Render the detail page for a single analysis."""
    record = get_analysis_by_id(db.session, analysis_id)
    if not record:
        return render_template("analyze.html", error="Analysis not found")
    details = None
    if record.raw_json:
        try:
            details = json.loads(record.raw_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return render_template("analyze.html", analysis=record, details=details)


@views_bp.route("/about")
def about():
    """Render the about page."""
    return render_template("about.html")
