"""REST API blueprint for CodePulse."""

import json
from flask import Blueprint, jsonify, request

from models.database import db
from models.schemas import CodeAnalysis
from services.analyzer import analyze_code
from services.data_service import (
    save_analysis,
    get_recent_analyses,
    get_analysis_by_id,
    get_aggregate_stats,
    delete_analysis,
    get_sample_code,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Return service health status."""
    return jsonify({"status": "healthy", "service": "CodePulse", "version": "1.0.0"})


@api_bp.route("/analyze", methods=["POST"])
def analyze():
    """Analyze submitted Python source code.

    Expects JSON body with:
        code (str): Python source code to analyze.
        filename (str, optional): Name for the file, default 'untitled.py'.

    Returns full analysis result as JSON.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("code", "").strip():
        return jsonify({"error": "No code provided"}), 400

    code = data["code"]
    if len(code) > 500_000:
        return jsonify({"error": "Code exceeds maximum length of 500,000 characters"}), 400

    filename = data.get("filename", "untitled.py")

    result = analyze_code(code, filename)

    # Persist to database
    try:
        record = save_analysis(db.session, result, filename)
        result["id"] = record.id
    except Exception:
        db.session.rollback()

    return jsonify(result)


@api_bp.route("/analyses", methods=["GET"])
def list_analyses():
    """Return recent analysis records."""
    limit = request.args.get("limit", 20, type=int)
    analyses = get_recent_analyses(db.session, limit=min(limit, 100))
    return jsonify([a.to_dict() for a in analyses])


@api_bp.route("/analyses/<int:analysis_id>", methods=["GET"])
def get_analysis(analysis_id):
    """Return a single analysis by ID with full details."""
    record = get_analysis_by_id(db.session, analysis_id)
    if not record:
        return jsonify({"error": "Analysis not found"}), 404
    result = record.to_dict()
    if record.raw_json:
        try:
            result["details"] = json.loads(record.raw_json)
        except (json.JSONDecodeError, TypeError):
            pass
    return jsonify(result)


@api_bp.route("/analyses/<int:analysis_id>", methods=["DELETE"])
def remove_analysis(analysis_id):
    """Delete a single analysis by ID."""
    deleted = delete_analysis(db.session, analysis_id)
    if not deleted:
        return jsonify({"error": "Analysis not found"}), 404
    return jsonify({"status": "deleted", "id": analysis_id})


@api_bp.route("/stats", methods=["GET"])
def stats():
    """Return aggregate statistics across all analyses."""
    return jsonify(get_aggregate_stats(db.session))


@api_bp.route("/sample", methods=["GET"])
def sample():
    """Return the sample code snippet."""
    return jsonify({"code": get_sample_code(), "filename": "sample.py"})
