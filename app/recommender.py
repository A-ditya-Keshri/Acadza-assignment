"""
DOST-based recommendation engine.
Builds a step-by-step study plan based on student performance analysis.
"""

from collections import defaultdict
from .analyzer import analyze_student


def _map_chapter_to_topic(chapter: str) -> str:
    """Map chapter names from student data to question bank topic slugs."""
    mapping = {
        "Thermodynamics": "thermodynamics",
        "Electrostatics": "electrostatics",
        "Kinematics": "kinematics",
        "Optics": "optics",
        "Laws of Motion": "laws_of_motion",
        "Rotational Mechanics": "rotational_mechanics",
        "Heat Transfer": "heat_transfer",
        "Organic Chemistry": "organic_chemistry",
        "Chemical Bonding": "chemical_bonding",
        "Physical Chemistry": "physical_chemistry",
        "Coordinate Geometry": "coordinate_geometry",
        "Algebra": "algebra",
        "Calculus": "calculus",
        "Trigonometry": "trigonometry",
        "Probability": "probability",
    }
    return mapping.get(chapter, chapter.lower().replace(" ", "_"))


def _get_questions_for_topic(questions: dict, topic: str, difficulty_range: tuple = None, limit: int = 5) -> list[str]:
    """Find question IDs matching a topic and optional difficulty range."""
    matches = []
    for qid, q in questions.items():
        if q.get("topic") == topic:
            if difficulty_range:
                diff = q.get("difficulty", 3)
                if diff is not None and difficulty_range[0] <= diff <= difficulty_range[1]:
                    matches.append(qid)
            else:
                matches.append(qid)
        if len(matches) >= limit:
            break
    return matches


def _get_questions_for_subject(questions: dict, subject: str, limit: int = 5) -> list[str]:
    """Find question IDs matching a subject."""
    matches = []
    for qid, q in questions.items():
        if q.get("subject", "").lower() == subject.lower():
            matches.append(qid)
            if len(matches) >= limit:
                break
    return matches


def recommend_for_student(student: dict, questions: dict, dost_config: dict) -> dict:
    """
    Generate a step-by-step study plan for a student.
    
    Strategy:
    1. Analyze the student's performance
    2. Identify weakest chapters and subjects
    3. Build a progression: concept → formula → practice → test → speed drills
    4. Each step has DOST type, parameters, target chapters, question IDs, and reasoning
    """
    analysis = analyze_student(student, questions)
    
    weaknesses = analysis.get("weaknesses", [])
    strengths = analysis.get("strengths", [])
    overall = analysis.get("overall", {})
    time_mgmt = analysis.get("time_management", {})
    qtype_analysis = analysis.get("question_type_analysis", {})
    
    steps = []
    step_num = 1

    # --- Step 1-3: Address weakest chapters with concept → formula → practice ---
    for weakness in weaknesses[:3]:
        chapter = weakness["chapter"]
        subject = weakness.get("subject", "Unknown")
        topic = _map_chapter_to_topic(chapter)
        avg_marks = weakness.get("avg_marks_contribution", 0)

        # Step A: Concept understanding for very weak topics
        if avg_marks < 25:
            concept_config = dost_config.get("concept", {})
            steps.append({
                "step": step_num,
                "dost_type": "concept",
                "description": concept_config.get("description", "Theory explanation and conceptual understanding"),
                "target_chapter": chapter,
                "target_subject": subject,
                "parameters": concept_config.get("params", {}),
                "question_ids": [],
                "reasoning": f"{chapter} has very low average marks ({avg_marks}). Start with conceptual understanding before attempting problems.",
                "message_to_student": f"Let's begin by strengthening your fundamentals in {chapter}. We'll go through the key concepts and theory so you have a solid foundation before practice."
            })
            step_num += 1

        # Step B: Formula revision
        formula_config = dost_config.get("formula", {})
        steps.append({
            "step": step_num,
            "dost_type": "formula",
            "description": formula_config.get("description", "Formula revision sheet"),
            "target_chapter": chapter,
            "target_subject": subject,
            "parameters": formula_config.get("params", {}),
            "question_ids": [],
            "reasoning": f"Revise key formulas for {chapter} before practice to ensure quick recall during problem-solving.",
            "message_to_student": f"Time to review the important formulas for {chapter}. Having these at your fingertips will help you solve problems faster."
        })
        step_num += 1

        # Step C: Practice assignment (untimed, targeted)
        pa_config = dost_config.get("practiceAssignment", {})
        topic_questions = _get_questions_for_topic(questions, topic, difficulty_range=(1, 3), limit=10)
        if not topic_questions:
            topic_questions = _get_questions_for_subject(questions, subject, limit=10)
        
        steps.append({
            "step": step_num,
            "dost_type": "practiceAssignment",
            "description": pa_config.get("description", "Targeted practice set, no timer"),
            "target_chapter": chapter,
            "target_subject": subject,
            "parameters": {
                "difficulty": "easy",
                "type_split": pa_config.get("params", {}).get("type_split", {}).get("default", {"scq": 20, "mcq": 10, "integer": 5})
            },
            "question_ids": topic_questions,
            "reasoning": f"Start with easier problems in {chapter} to build confidence. No timer to reduce pressure.",
            "message_to_student": f"Now let's practice {chapter} with some problems. Take your time — there's no timer. Focus on understanding each solution."
        })
        step_num += 1

    # --- Step 4: Revision plan for all weak areas ---
    if weaknesses:
        rev_config = dost_config.get("revision", {})
        weak_chapters = [w["chapter"] for w in weaknesses[:3]]
        steps.append({
            "step": step_num,
            "dost_type": "revision",
            "description": rev_config.get("description", "Multi-day structured revision plan"),
            "target_chapter": ", ".join(weak_chapters),
            "target_subject": "Mixed",
            "parameters": {
                "alloted_days": 3,
                "strategy": 1,
                "daily_time_minutes": 60,
            },
            "question_ids": [],
            "reasoning": f"A structured 3-day revision plan covering all weak areas ({', '.join(weak_chapters)}) for systematic improvement.",
            "message_to_student": f"Here's a 3-day revision plan covering {', '.join(weak_chapters)}. Follow it daily for consistent improvement."
        })
        step_num += 1

    # --- Step 5: Practice test to assess improvement ---
    pt_config = dost_config.get("practiceTest", {})
    test_questions = []
    for w in weaknesses[:3]:
        topic = _map_chapter_to_topic(w["chapter"])
        test_questions.extend(_get_questions_for_topic(questions, topic, difficulty_range=(2, 4), limit=5))
    
    steps.append({
        "step": step_num,
        "dost_type": "practiceTest",
        "description": pt_config.get("description", "Full timed mock test"),
        "target_chapter": "Mixed (weak chapters)",
        "target_subject": "Mixed",
        "parameters": {
            "difficulty": "medium",
            "duration_minutes": 60,
            "paperPattern": student.get("stream", "Mains"),
        },
        "question_ids": test_questions[:25],
        "reasoning": "A timed mock test to assess improvement on weak chapters under exam conditions.",
        "message_to_student": "Time to test yourself! This timed mock will show how much you've improved on your weak areas. Treat it like a real exam."
    })
    step_num += 1

    # --- Step 6: Speed drill if time management is an issue ---
    avg_time = time_mgmt.get("avg_time_per_question_seconds", 0)
    if avg_time > 150:  # More than 2.5 minutes per question is slow
        cp_config = dost_config.get("clickingPower", {})
        speed_questions = []
        for w in weaknesses[:2]:
            topic = _map_chapter_to_topic(w["chapter"])
            speed_questions.extend(_get_questions_for_topic(questions, topic, difficulty_range=(1, 2), limit=5))
        
        steps.append({
            "step": step_num,
            "dost_type": "clickingPower",
            "description": cp_config.get("description", "Speed drill — 10 rapid questions"),
            "target_chapter": "Mixed",
            "target_subject": "Mixed",
            "parameters": {
                "total_questions": 10,
            },
            "question_ids": speed_questions[:10],
            "reasoning": f"Average time per question is {avg_time}s (above 150s threshold). Speed drills will help improve response time.",
            "message_to_student": "Your solving speed needs work! Let's do a rapid-fire round — 10 quick questions to sharpen your reflexes."
        })
        step_num += 1

    # --- Step 7: MCQ option elimination if attempt rate is low ---
    overall_attempt_rate = overall.get("attempt_rate", 100)
    if overall_attempt_rate < 85:
        pp_config = dost_config.get("pickingPower", {})
        steps.append({
            "step": step_num,
            "dost_type": "pickingPower",
            "description": pp_config.get("description", "MCQ option elimination practice"),
            "target_chapter": "General",
            "target_subject": "Mixed",
            "parameters": pp_config.get("params", {}),
            "question_ids": _get_questions_for_subject(questions, "Physics", limit=5) + _get_questions_for_subject(questions, "Chemistry", limit=5),
            "reasoning": f"Attempt rate is {overall_attempt_rate}% — too many questions are being skipped. Option elimination practice will help attempt more questions confidently.",
            "message_to_student": "You're skipping too many questions. Let's practice eliminating wrong options — this will help you attempt more questions even when unsure."
        })
        step_num += 1

    # --- Step 8: Speed race for competitive motivation ---
    if strengths:
        sr_config = dost_config.get("speedRace", {})
        strong_chapter = strengths[0]["chapter"]
        topic = _map_chapter_to_topic(strong_chapter)
        race_questions = _get_questions_for_topic(questions, topic, limit=10)
        
        steps.append({
            "step": step_num,
            "dost_type": "speedRace",
            "description": sr_config.get("description", "Competitive timed race against bot"),
            "target_chapter": strong_chapter,
            "target_subject": strengths[0].get("subject", "Mixed"),
            "parameters": {
                "rank": 100,
                "opponent_type": "bot",
            },
            "question_ids": race_questions,
            "reasoning": f"End with a confidence-building speed race in {strong_chapter} — a strong area — to maintain motivation.",
            "message_to_student": f"Great work! Let's end with a fun challenge — race against a bot in {strong_chapter}, one of your strongest topics!"
        })
        step_num += 1

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "total_steps": len(steps),
        "summary": f"Personalized {len(steps)}-step study plan targeting {len(weaknesses)} weak areas with progressive difficulty.",
        "steps": steps,
    }
