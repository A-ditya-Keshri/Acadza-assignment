"""
Generate sample outputs for all 10 students.
Calls the analyze and recommend logic and saves results to sample_outputs/.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data_loader import data_store
from app.analyzer import analyze_student
from app.recommender import recommend_for_student

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_outputs")


def main():
    # Load data
    data_store.load()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating sample outputs for {len(data_store.students)} students...")

    for student in data_store.students:
        sid = student["student_id"]
        name = student["name"]

        # Analyze
        analysis = analyze_student(student, data_store.questions)
        with open(os.path.join(OUTPUT_DIR, f"{sid}_analyze.json"), "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        # Recommend
        recommendation = recommend_for_student(student, data_store.questions, data_store.dost_config)
        with open(os.path.join(OUTPUT_DIR, f"{sid}_recommend.json"), "w", encoding="utf-8") as f:
            json.dump(recommendation, f, indent=2, ensure_ascii=False)

        print(f"  ✓ {sid} ({name}) — analyze + recommend")

    # Leaderboard
    print("\nGenerating leaderboard...")
    from app.main import app
    # Import leaderboard logic directly
    rankings = []
    for student in data_store.students:
        analysis = analyze_student(student, data_store.questions)
        overall = analysis.get("overall", {})

        avg_marks = overall.get("avg_net_marks", 0)
        marks_pct = min(avg_marks / 80 * 100, 100) if avg_marks > 0 else 0
        completion_rate = overall.get("completion_rate", 0)
        attempt_rate = overall.get("attempt_rate", 0)

        time_mgmt = analysis.get("time_management", {})
        avg_time = time_mgmt.get("avg_time_per_question_seconds", 120)
        if avg_time <= 0:
            time_eff = 0
        elif avg_time < 30:
            time_eff = 40
        elif avg_time <= 120:
            time_eff = 100
        elif avg_time <= 200:
            time_eff = max(0, 100 - (avg_time - 120) * 0.8)
        else:
            time_eff = max(0, 100 - (avg_time - 120) * 1.0)

        score = round(0.40 * marks_pct + 0.25 * completion_rate + 0.20 * attempt_rate + 0.15 * time_eff, 2)

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

    rankings.sort(key=lambda x: -x["score"])
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    leaderboard = {
        "total_students": len(rankings),
        "scoring_formula": "0.40 * marks% + 0.25 * completion_rate + 0.20 * attempt_rate + 0.15 * time_efficiency",
        "leaderboard": rankings,
    }

    with open(os.path.join(OUTPUT_DIR, "leaderboard.json"), "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, indent=2, ensure_ascii=False)

    print("  ✓ leaderboard.json")
    print(f"\nDone! All outputs saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
