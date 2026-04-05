"""
Student performance analyzer.
Analyzes patterns, trends, strengths, weaknesses across all sessions.
"""

from collections import defaultdict


def analyze_student(student: dict, questions: dict) -> dict:
    """
    Analyze a student's performance across all sessions.
    Returns detailed breakdown with patterns, trends, and insights.
    """
    attempts = student.get("attempts", [])
    if not attempts:
        return {"error": "No attempts found for this student"}

    # --- Overall Stats ---
    total_attempts = len(attempts)
    completed = sum(1 for a in attempts if a.get("completed", False))
    completion_rate = round(completed / total_attempts * 100, 1) if total_attempts > 0 else 0

    net_marks_list = [a["parsed_marks"]["net_marks"] for a in attempts if "parsed_marks" in a]
    avg_marks = round(sum(net_marks_list) / len(net_marks_list), 2) if net_marks_list else 0

    total_questions_attempted = sum(a.get("attempted", 0) for a in attempts)
    total_questions_total = sum(a.get("total_questions", 0) for a in attempts)
    total_skipped = sum(a.get("skipped", 0) for a in attempts)

    # --- Subject-wise Breakdown ---
    subject_stats = defaultdict(lambda: {
        "attempts": 0, "net_marks_sum": 0, "questions_attempted": 0,
        "questions_total": 0, "time_sum": 0, "completed": 0
    })
    for a in attempts:
        subj = a.get("subject", "Unknown")
        s = subject_stats[subj]
        s["attempts"] += 1
        s["net_marks_sum"] += a.get("parsed_marks", {}).get("net_marks", 0)
        s["questions_attempted"] += a.get("attempted", 0)
        s["questions_total"] += a.get("total_questions", 0)
        s["time_sum"] += a.get("time_taken_minutes", 0)
        if a.get("completed"):
            s["completed"] += 1

    subject_breakdown = {}
    for subj, s in subject_stats.items():
        attempt_rate = round(s["questions_attempted"] / s["questions_total"] * 100, 1) if s["questions_total"] > 0 else 0
        avg_m = round(s["net_marks_sum"] / s["attempts"], 2) if s["attempts"] > 0 else 0
        subject_breakdown[subj] = {
            "total_attempts": s["attempts"],
            "avg_marks": avg_m,
            "attempt_rate": attempt_rate,
            "total_questions_attempted": s["questions_attempted"],
            "total_questions": s["questions_total"],
            "avg_time_minutes": round(s["time_sum"] / s["attempts"], 1) if s["attempts"] > 0 else 0,
            "completion_rate": round(s["completed"] / s["attempts"] * 100, 1) if s["attempts"] > 0 else 0,
        }

    # --- Chapter-wise Breakdown ---
    chapter_stats = defaultdict(lambda: {
        "attempts": 0, "net_marks_sum": 0, "subject": "", "avg_times": []
    })
    for a in attempts:
        for ch in a.get("chapters", []):
            c = chapter_stats[ch]
            c["attempts"] += 1
            # Distribute marks equally across chapters in the attempt
            n_chapters = len(a.get("chapters", [1]))
            c["net_marks_sum"] += a.get("parsed_marks", {}).get("net_marks", 0) / max(n_chapters, 1)
            c["subject"] = a.get("subject", "Unknown")
            c["avg_times"].append(a.get("avg_time_per_question_seconds", 0))

    chapter_breakdown = {}
    for ch, c in chapter_stats.items():
        avg_m = round(c["net_marks_sum"] / c["attempts"], 2) if c["attempts"] > 0 else 0
        avg_t = round(sum(c["avg_times"]) / len(c["avg_times"]), 1) if c["avg_times"] else 0
        chapter_breakdown[ch] = {
            "subject": c["subject"],
            "times_appeared": c["attempts"],
            "avg_marks_contribution": avg_m,
            "avg_time_per_question_seconds": avg_t,
        }

    # --- Strengths & Weaknesses ---
    sorted_chapters = sorted(chapter_breakdown.items(), key=lambda x: x[1]["avg_marks_contribution"])
    weakest = [{"chapter": ch, **data} for ch, data in sorted_chapters[:3]] if len(sorted_chapters) >= 3 else [{"chapter": ch, **data} for ch, data in sorted_chapters]
    strongest = [{"chapter": ch, **data} for ch, data in sorted_chapters[-3:][::-1]] if len(sorted_chapters) >= 3 else [{"chapter": ch, **data} for ch, data in sorted_chapters[::-1]]

    # --- Trends Over Time ---
    sorted_attempts = sorted(attempts, key=lambda a: a.get("date", ""))
    trends = []
    for a in sorted_attempts:
        trends.append({
            "date": a.get("date"),
            "subject": a.get("subject"),
            "chapters": a.get("chapters"),
            "net_marks": a.get("parsed_marks", {}).get("net_marks", 0),
            "attempted": a.get("attempted", 0),
            "total": a.get("total_questions", 0),
            "completed": a.get("completed", False),
            "time_taken_minutes": a.get("time_taken_minutes", 0),
        })

    # Trend direction
    if len(net_marks_list) >= 3:
        first_half = net_marks_list[:len(net_marks_list)//2]
        second_half = net_marks_list[len(net_marks_list)//2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        if avg_second > avg_first * 1.1:
            trend_direction = "improving"
        elif avg_second < avg_first * 0.9:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "insufficient_data"

    # --- Time Management ---
    avg_times = [a.get("avg_time_per_question_seconds", 0) for a in attempts if a.get("avg_time_per_question_seconds")]
    avg_time_overall = round(sum(avg_times) / len(avg_times), 1) if avg_times else 0
    
    slowest_questions = []
    fastest_questions = []
    for a in attempts:
        if a.get("slowest_question_id"):
            slowest_questions.append({
                "question_id": a["slowest_question_id"],
                "time_seconds": a.get("slowest_question_time_seconds", 0),
                "date": a.get("date"),
                "subject": a.get("subject"),
            })
        if a.get("fastest_question_id"):
            fastest_questions.append({
                "question_id": a["fastest_question_id"],
                "time_seconds": a.get("fastest_question_time_seconds", 0),
                "date": a.get("date"),
                "subject": a.get("subject"),
            })

    # --- Question Type Analysis ---
    type_stats = defaultdict(lambda: {"total": 0, "attempted": 0})
    for a in attempts:
        for qtype, count in a.get("question_type_split", {}).items():
            type_stats[qtype]["total"] += count
        for qtype, count in a.get("attempted_type_split", {}).items():
            type_stats[qtype]["attempted"] += count

    question_type_analysis = {}
    for qtype, ts in type_stats.items():
        rate = round(ts["attempted"] / ts["total"] * 100, 1) if ts["total"] > 0 else 0
        question_type_analysis[qtype] = {
            "total": ts["total"],
            "attempted": ts["attempted"],
            "attempt_rate": rate,
        }

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "class": student.get("class"),
        "stream": student.get("stream"),
        "overall": {
            "total_sessions": total_attempts,
            "completed_sessions": completed,
            "completion_rate": completion_rate,
            "avg_net_marks": avg_marks,
            "total_questions_seen": total_questions_total,
            "total_questions_attempted": total_questions_attempted,
            "total_skipped": total_skipped,
            "attempt_rate": round(total_questions_attempted / total_questions_total * 100, 1) if total_questions_total > 0 else 0,
            "trend": trend_direction,
        },
        "subject_breakdown": subject_breakdown,
        "chapter_breakdown": chapter_breakdown,
        "strengths": strongest,
        "weaknesses": weakest,
        "time_management": {
            "avg_time_per_question_seconds": avg_time_overall,
            "slowest_questions": sorted(slowest_questions, key=lambda x: -x["time_seconds"])[:5],
            "fastest_questions": sorted(fastest_questions, key=lambda x: x["time_seconds"])[:5],
        },
        "question_type_analysis": question_type_analysis,
        "session_trends": trends,
    }
