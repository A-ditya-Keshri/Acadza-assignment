"""
Data loading and normalization layer.
Loads student_performance.json, question_bank.json, and dost_config.json.
"""

import json
import os
from pathlib import Path
from .utils import normalize_question_id, parse_marks, strip_html

DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str):
    """Load a JSON file from the data directory."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_students() -> list[dict]:
    """Load and parse student performance data with normalized marks."""
    students = load_json("student_performance.json")
    for student in students:
        for attempt in student.get("attempts", []):
            attempt["parsed_marks"] = parse_marks(attempt.get("marks"))
    return students


def load_questions() -> dict:
    """
    Load question bank, normalize IDs, flag data quality issues.
    Returns dict keyed by qid for fast lookup.
    """
    raw_questions = load_json("question_bank.json")
    questions = {}
    seen_oids = set()
    
    for q in raw_questions:
        # Normalize _id
        q["_id_normalized"] = normalize_question_id(q.get("_id"))
        
        # Track duplicates
        oid = q["_id_normalized"]
        if oid in seen_oids:
            q["_data_issue"] = q.get("_data_issue", [])
            q["_data_issue"].append("duplicate_id")
        seen_oids.add(oid)
        
        # Check for missing answer
        qtype = q.get("questionType", "")
        type_data = q.get(qtype, {})
        if type_data and type_data.get("answer") is None:
            q["_data_issue"] = q.get("_data_issue", [])
            q["_data_issue"].append("missing_answer")
        
        # Check for null difficulty
        if q.get("difficulty") is None:
            q["_data_issue"] = q.get("_data_issue", [])
            q["_data_issue"].append("null_difficulty")
            q["difficulty"] = 3  # Default to medium
        
        # Build plaintext preview
        if type_data and isinstance(type_data, dict):
            q["_plaintext_question"] = strip_html(type_data.get("question", ""))
            q["_plaintext_solution"] = strip_html(type_data.get("solution", ""))
        
        qid = q.get("qid", oid)
        questions[qid] = q
    
    return questions


def load_dost_config() -> dict:
    """Load DOST type configuration."""
    return load_json("dost_config.json")


def get_student_by_id(students: list[dict], student_id: str) -> dict | None:
    """Find a student by their student_id."""
    for s in students:
        if s["student_id"] == student_id:
            return s
    return None


# Singleton-style data store
class DataStore:
    """Global data store loaded once at startup."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance
    
    def load(self):
        if not self._loaded:
            self.students = load_students()
            self.questions = load_questions()
            self.dost_config = load_dost_config()
            self._loaded = True
    
    def get_student(self, student_id: str) -> dict | None:
        return get_student_by_id(self.students, student_id)


data_store = DataStore()
