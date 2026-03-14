"""Data access helpers -- sample data, persistence, queries."""

import hashlib
import json
from typing import Any

from sqlalchemy import func

from models.database import db
from models.schemas import CodeAnalysis


def get_sample_code() -> str:
    """Return a non-trivial sample Python snippet for the demo textarea."""
    return '''\
import os
import sys
from collections import defaultdict


class DataProcessor:
    """Process and aggregate data records."""

    def __init__(self, source_path, delimiter=",", encoding="utf-8"):
        self.source_path = source_path
        self.delimiter = delimiter
        self.encoding = encoding
        self.records = []
        self._cache = {}

    def load(self):
        """Load records from the source file."""
        if not os.path.exists(self.source_path):
            raise FileNotFoundError(f"Source not found: {self.source_path}")
        with open(self.source_path, encoding=self.encoding) as fh:
            for line in fh:
                parts = line.strip().split(self.delimiter)
                if len(parts) >= 2:
                    self.records.append({"key": parts[0], "value": parts[1]})

    def aggregate(self, group_field="key"):
        """Group records by a field and count occurrences."""
        groups = defaultdict(list)
        for record in self.records:
            if group_field in record:
                groups[record[group_field]].append(record)
        return dict(groups)

    def filter_records(self, predicate):
        """Return records matching the predicate function."""
        return [r for r in self.records if predicate(r)]

    def transform(self, field, func):
        """Apply a transformation function to a field in all records."""
        for record in self.records:
            if field in record:
                record[field] = func(record[field])
        return self.records

    def export_json(self, output_path):
        """Export records to a JSON file."""
        with open(output_path, "w") as fh:
            json.dump(self.records, fh, indent=2)
        return len(self.records)


def calculate_statistics(numbers):
    """Return basic statistics for a list of numbers."""
    if not numbers:
        return {"mean": 0, "median": 0, "std_dev": 0, "min": 0, "max": 0}

    n = len(numbers)
    mean = sum(numbers) / n
    sorted_nums = sorted(numbers)

    if n % 2 == 0:
        median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
    else:
        median = sorted_nums[n // 2]

    variance = sum((x - mean) ** 2 for x in numbers) / n
    std_dev = variance ** 0.5

    return {
        "mean": round(mean, 2),
        "median": median,
        "std_dev": round(std_dev, 2),
        "min": min(numbers),
        "max": max(numbers),
    }


if __name__ == "__main__":
    import json
    proc = DataProcessor("data.csv")
    proc.load()
    groups = proc.aggregate()
    print(f"Found {len(groups)} groups")
'''


def save_analysis(
    db_session, analysis_result: dict[str, Any], filename: str
) -> CodeAnalysis:
    """Persist an analysis result to the database and return the ORM object."""
    source_hash = hashlib.sha256(
        json.dumps(analysis_result, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    record = CodeAnalysis(
        filename=filename,
        language=analysis_result.get("language", "python"),
        total_lines=analysis_result.get("total_lines", 0),
        code_lines=analysis_result.get("code_lines", 0),
        blank_lines=analysis_result.get("blank_lines", 0),
        comment_lines=analysis_result.get("comment_lines", 0),
        complexity_score=analysis_result.get("complexity_score", 0),
        maintainability_index=analysis_result.get("maintainability_index", 100.0),
        halstead_volume=analysis_result.get("halstead_volume", 0.0),
        halstead_difficulty=analysis_result.get("halstead_difficulty", 0.0),
        halstead_effort=analysis_result.get("halstead_effort", 0.0),
        smell_count=analysis_result.get("smell_count", 0),
        functions_count=analysis_result.get("functions_count", 0),
        classes_count=analysis_result.get("classes_count", 0),
        grade=analysis_result.get("grade", "A"),
        raw_json=json.dumps(analysis_result, default=str),
        source_hash=source_hash,
    )
    db_session.add(record)
    db_session.commit()
    return record


def get_recent_analyses(db_session, limit: int = 10) -> list[CodeAnalysis]:
    """Return the most recent analyses ordered by creation date."""
    return (
        db_session.query(CodeAnalysis)
        .order_by(CodeAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )


def get_analysis_by_id(db_session, analysis_id: int):
    """Return a single analysis record by ID or None."""
    return db_session.get(CodeAnalysis, analysis_id)


def get_aggregate_stats(db_session) -> dict[str, Any]:
    """Return aggregate statistics across all analyses."""
    result = db_session.query(
        func.count(CodeAnalysis.id).label("total_analyses"),
        func.avg(CodeAnalysis.complexity_score).label("avg_complexity"),
        func.avg(CodeAnalysis.maintainability_index).label("avg_mi"),
        func.avg(CodeAnalysis.smell_count).label("avg_smells"),
        func.sum(CodeAnalysis.total_lines).label("total_lines_analyzed"),
        func.avg(CodeAnalysis.total_lines).label("avg_lines"),
    ).first()

    if not result or not result.total_analyses:
        return {
            "total_analyses": 0,
            "avg_complexity": 0,
            "avg_mi": 0,
            "avg_smells": 0,
            "total_lines_analyzed": 0,
            "avg_lines": 0,
            "grade_distribution": {},
        }

    # Grade distribution
    grade_rows = (
        db_session.query(CodeAnalysis.grade, func.count(CodeAnalysis.id))
        .group_by(CodeAnalysis.grade)
        .all()
    )
    grade_distribution = {row[0]: row[1] for row in grade_rows}

    return {
        "total_analyses": result.total_analyses or 0,
        "avg_complexity": round(float(result.avg_complexity or 0), 1),
        "avg_mi": round(float(result.avg_mi or 0), 1),
        "avg_smells": round(float(result.avg_smells or 0), 1),
        "total_lines_analyzed": result.total_lines_analyzed or 0,
        "avg_lines": round(float(result.avg_lines or 0), 1),
        "grade_distribution": grade_distribution,
    }


def delete_analysis(db_session, analysis_id: int) -> bool:
    """Delete an analysis record by ID. Returns True if deleted."""
    record = db_session.get(CodeAnalysis, analysis_id)
    if record:
        db_session.delete(record)
        db_session.commit()
        return True
    return False
