"""Model and schema tests for CodePulse."""

from models.schemas import CodeAnalysis, AnalysisRequest, AnalysisResponse


def test_code_analysis_creation(db_session):
    """Create a CodeAnalysis record and verify fields persist."""
    record = CodeAnalysis(
        filename="test.py",
        language="python",
        total_lines=42,
        code_lines=35,
        complexity_score=5,
        maintainability_index=72.5,
        halstead_volume=150.0,
        smell_count=1,
        functions_count=3,
        classes_count=1,
        grade="B",
    )
    db_session.add(record)
    db_session.commit()

    fetched = db_session.get(CodeAnalysis, record.id)
    assert fetched is not None
    assert fetched.filename == "test.py"
    assert fetched.total_lines == 42
    assert fetched.code_lines == 35
    assert fetched.grade == "B"
    assert fetched.maintainability_index == 72.5


def test_code_analysis_to_dict(db_session):
    """to_dict() returns a dictionary with expected keys."""
    record = CodeAnalysis(filename="x.py", total_lines=10, grade="A")
    db_session.add(record)
    db_session.commit()

    d = record.to_dict()
    assert d["filename"] == "x.py"
    assert "id" in d
    assert "created_at" in d
    assert "maintainability_index" in d
    assert "halstead_volume" in d


def test_analysis_request_validation():
    """AnalysisRequest validates required fields."""
    req = AnalysisRequest(code="print('hi')")
    assert req.code == "print('hi')"
    assert req.filename == "untitled.py"


def test_analysis_response_fields():
    """AnalysisResponse includes all expected fields including Halstead."""
    resp = AnalysisResponse(
        filename="test.py",
        total_lines=50,
        complexity_score=8,
        grade="B",
        functions_count=3,
        classes_count=1,
        smell_count=2,
        maintainability_index=65.0,
        halstead_volume=200.0,
    )
    assert resp.filename == "test.py"
    assert resp.grade == "B"
    assert resp.functions == []
    assert resp.smells == []
    assert resp.maintainability_index == 65.0
    assert resp.halstead_volume == 200.0
    assert resp.halstead_bugs == 0.0
