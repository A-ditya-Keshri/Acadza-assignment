"""
Acadza AI Intern Assignment — FastAPI Application
Student performance analysis and DOST-based recommendations.
"""

from fastapi import FastAPI, HTTPException
from .data_loader import data_store
from .analyzer import analyze_student
from .recommender import recommend_for_student
from .utils import strip_html, normalize_question_id

app = FastAPI(
    title="Acadza Student Recommender",
    description="Analyze student performance and recommend personalized study plans using DOST activities.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    """Load all data at startup."""
    data_store.load()


@app.post("/analyze/{student_id}")
def analyze(student_id: str):
    """
    Analyze a student's performance across all sessions.
    Returns patterns, trends, chapter-wise breakdown, strengths, weaknesses.
    """
    student = data_store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return analyze_student(student, data_store.questions)


@app.post("/recommend/{student_id}")
def recommend(student_id: str):
    """
    Return a step-by-step personalized study plan.
    Each step includes DOST type, target chapter, parameters, question IDs, and reasoning.
    """
    student = data_store.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    return recommend_for_student(student, data_store.questions, data_store.dost_config)


@app.get("/question/{question_id}")
def get_question(question_id: str):
    """
    Look up a question by its qid. Returns clean data with plaintext preview.
    """
    q = data_store.questions.get(question_id)
    if not q:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    qtype = q.get("questionType", "")
    type_data = q.get(qtype, {})

    result = {
        "qid": q.get("qid"),
        "_id": q.get("_id_normalized"),
        "questionType": qtype,
        "subject": q.get("subject"),
        "topic": q.get("topic"),
        "subtopic": q.get("subtopic"),
        "difficulty": q.get("difficulty"),
        "question_preview": q.get("_plaintext_question", ""),
        "solution_preview": q.get("_plaintext_solution", ""),
        "answer": type_data.get("answer") if isinstance(type_data, dict) else None,
        "data_issues": q.get("_data_issue", []),
    }
    return result


@app.get("/leaderboard")
def leaderboard():
    """
    Rank all students using a composite scoring formula.
    Score = 0.4 * avg_marks_pct + 0.25 * completion_rate + 0.20 * attempt_rate + 0.15 * time_efficiency
    """
    rankings = []

    for student in data_store.students:
        analysis = analyze_student(student, data_store.questions)
        overall = analysis.get("overall", {})

        # Compute normalized scores
        avg_marks = overall.get("avg_net_marks", 0)
        # Normalize marks to 0-100 scale (assuming max possible ~120)
        marks_pct = min(avg_marks / 80 * 100, 100) if avg_marks > 0 else 0

        completion_rate = overall.get("completion_rate", 0)
        attempt_rate = overall.get("attempt_rate", 0)

        # Time efficiency: ideal is ~120s/question, penalize extremes
        time_mgmt = analysis.get("time_management", {})
        avg_time = time_mgmt.get("avg_time_per_question_seconds", 120)
        # Score higher for times closer to 90-120s range
        if avg_time <= 0:
            time_eff = 0
        elif avg_time < 30:
            time_eff = 40  # Too fast = probably guessing
        elif avg_time <= 120:
            time_eff = 100
        elif avg_time <= 200:
            time_eff = max(0, 100 - (avg_time - 120) * 0.8)
        else:
            time_eff = max(0, 100 - (avg_time - 120) * 1.0)

        # Composite score
        score = round(
            0.40 * marks_pct +
            0.25 * completion_rate +
            0.20 * attempt_rate +
            0.15 * time_eff,
            2
        )

        # Strengths and weaknesses
        strengths = analysis.get("strengths", [])
        weaknesses = analysis.get("weaknesses", [])

        rankings.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "score": score,
            "avg_marks": avg_marks,
            "completion_rate": completion_rate,
            "attempt_rate": attempt_rate,
            "time_efficiency_score": round(time_eff, 1),
            "strongest_chapter": strengths[0]["chapter"] if strengths else "N/A",
            "weakest_chapter": weaknesses[0]["chapter"] if weaknesses else "N/A",
            "focus_area": weaknesses[0]["chapter"] if weaknesses else "General Practice",
        })

    # Sort by score descending
    rankings.sort(key=lambda x: -x["score"])
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return {
        "total_students": len(rankings),
        "scoring_formula": "0.40 * marks% + 0.25 * completion_rate + 0.20 * attempt_rate + 0.15 * time_efficiency",
        "leaderboard": rankings,
    }
