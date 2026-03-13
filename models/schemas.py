"""SQLAlchemy models and Pydantic schemas for CodePulse."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from models.database import db


class CodeAnalysis(db.Model):
    """Persisted record of a single code analysis run."""

    __tablename__ = "code_analyses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False, default="untitled.py")
    language = db.Column(db.String(50), nullable=False, default="python")
    total_lines = db.Column(db.Integer, nullable=False, default=0)
    code_lines = db.Column(db.Integer, nullable=False, default=0)
    blank_lines = db.Column(db.Integer, nullable=False, default=0)
    comment_lines = db.Column(db.Integer, nullable=False, default=0)
    complexity_score = db.Column(db.Integer, nullable=False, default=0)
    maintainability_index = db.Column(db.Float, nullable=False, default=100.0)
    halstead_volume = db.Column(db.Float, nullable=False, default=0.0)
    halstead_difficulty = db.Column(db.Float, nullable=False, default=0.0)
    halstead_effort = db.Column(db.Float, nullable=False, default=0.0)
    smell_count = db.Column(db.Integer, nullable=False, default=0)
    functions_count = db.Column(db.Integer, nullable=False, default=0)
    classes_count = db.Column(db.Integer, nullable=False, default=0)
    grade = db.Column(db.String(2), nullable=False, default="A")
    raw_json = db.Column(db.Text, nullable=True)
    source_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<CodeAnalysis {self.id} {self.filename} grade={self.grade}>"

    def to_dict(self):
        """Serialize the record to a dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "language": self.language,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "complexity_score": self.complexity_score,
            "maintainability_index": round(self.maintainability_index, 1),
            "halstead_volume": round(self.halstead_volume, 1),
            "halstead_difficulty": round(self.halstead_difficulty, 1),
            "halstead_effort": round(self.halstead_effort, 1),
            "smell_count": self.smell_count,
            "functions_count": self.functions_count,
            "classes_count": self.classes_count,
            "grade": self.grade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisRequest(BaseModel):
    """Incoming analysis request."""

    code: str = Field(..., min_length=1, max_length=500_000)
    filename: str = Field(default="untitled.py", max_length=255)


class AnalysisResponse(BaseModel):
    """Full analysis result returned to the client."""

    filename: str
    language: str = "python"
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    complexity_score: int = 0
    maintainability_index: float = 100.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_bugs: float = 0.0
    halstead_time: float = 0.0
    grade: str = "A"
    functions: list = Field(default_factory=list)
    classes: list = Field(default_factory=list)
    imports: list = Field(default_factory=list)
    smells: list = Field(default_factory=list)
    smell_count: int = 0
    functions_count: int = 0
    classes_count: int = 0
    id: Optional[int] = None
