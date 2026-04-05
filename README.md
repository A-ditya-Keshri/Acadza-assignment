# Acadza AI Intern Assignment — Student Performance Recommender

## Overview

This project is a **FastAPI-based recommendation engine** for Acadza, an EdTech platform helping students prepare for JEE and NEET. The system analyzes student performance data across multiple test and assignment sessions — tracking marks scored, time spent, questions attempted, chapters covered, and completion status — and then generates **personalized step-by-step study plans** using DOST (Dynamic Optimized Study Task) activities.

The core idea is simple: students who struggle with specific chapters should receive targeted interventions, starting from conceptual understanding and progressing through formula revision, practice sets, mock tests, and speed drills. The recommendation engine doesn't just say "study more Physics" — it gives a concrete sequence: *first* understand the concept, *then* review formulas, *then* practice easy problems without a timer, *then* take a timed test, and *finally* do speed drills to improve response time.

---

## Approach

### Data Analysis

The student performance data (`student_performance.json`) includes 10 students with 5-8 sessions each. Each session records the subject, chapters tested, marks obtained, time taken, questions attempted vs skipped, and outlier question IDs (slowest/fastest).

The **analyzer** computes:
- **Overall statistics**: completion rate, average marks, attempt rate, trend direction
- **Subject-wise breakdown**: marks, time, and completion per subject (Physics, Chemistry, Mathematics)
- **Chapter-wise breakdown**: how each chapter performs across all sessions where it appeared
- **Strengths and weaknesses**: chapters ranked by average marks contribution — bottom 3 are weaknesses, top 3 are strengths
- **Time management analysis**: average solving speed, identifying students who spend too long or too little per question
- **Question type analysis**: how well students handle SCQ vs MCQ vs Integer questions
- **Session trends**: whether performance is improving, declining, or stable over time (comparing first-half vs second-half averages)

### Handling Messy Marks

The marks field is intentionally inconsistent across attempts — formats include `"68/100"`, `"28"`, `"+52 -12"`, `"34/75 (45.3%)"`, and raw integers like `72`. I built a regex-based parser (`parse_marks`) that handles all these formats:
- Fraction format (`68/100`) → extracts numerator as net marks, denominator as total, computes percentage
- Plus-minus format (`+52 -12`) → computes net as positive minus negative (40 in this case)
- Percentage format (`34/75 (45.3%)`) → extracts all three values
- Plain numbers → used directly as net marks

The assumption is that **net marks is the most comparable metric** across formats, even though absolute values depend on different total marks across tests. For the leaderboard, I normalize marks against an assumed maximum of 80 to produce a percentage score.

### DOST Recommendation Strategy

The recommender follows a **progressive difficulty model**:

1. **Very weak chapters (avg marks < 25)**: Start with `concept` (theory understanding) → `formula` (revision) → `practiceAssignment` (easy, untimed)
2. **Moderately weak chapters**: Skip concept, go directly to `formula` → `practiceAssignment`
3. **All weak areas combined**: `revision` (3-day structured plan)
4. **Assessment**: `practiceTest` (timed mock under exam conditions)
5. **Speed issues (avg time > 150s/question)**: `clickingPower` (rapid-fire drill)
6. **Low attempt rate (<85%)**: `pickingPower` (MCQ elimination practice)
7. **Motivation/confidence**: `speedRace` in a strong chapter to end on a positive note

Each step includes specific question IDs from the question bank, matched by topic and difficulty range.

---

## Debug Task

The `debug/recommender_buggy.py` file contains a cosine-similarity-based recommender that runs without errors but produces identical recommendations for all students.

### The Bug

Located on **lines 54-55** of the `recommend()` function:

```python
# BUGGY:
profile_norm = np.linalg.norm(cohort_baseline)           # Bug 1
student_profile = cohort_baseline / (profile_norm + 1e-10)  # Bug 2
```

**Bug 1**: Computes the norm of `cohort_baseline` instead of `student_profile`. The student's individual adjusted profile (computed on line 51) is ignored for normalization.

**Bug 2**: Overwrites `student_profile` with the normalized `cohort_baseline`. This means every student's profile becomes the same normalized cohort average, completely discarding individual weakness patterns.

The fix is straightforward:
```python
# FIXED:
profile_norm = np.linalg.norm(student_profile)
student_profile = student_profile / (profile_norm + 1e-10)
```

### How I Found It

I traced the data flow through `recommend()`. Line 51 correctly computes `student_profile = student_matrix[student_idx] - cohort_baseline` (the individual gap from the average). But then lines 54-55 throw away this computation by using `cohort_baseline` in both the norm calculation and the assignment. This is a variable name swap bug — the kind that passes all syntax checks and produces valid output, but the output is semantically wrong because personalization is lost.

### What AI Suggested

AI tools correctly identified the variable substitution on lines 54-55. The bug is designed to be subtle (no crash, valid output), but the mismatch between the comment ("normalize the adjusted profile") and the actual code (normalizing the cohort baseline) makes it identifiable through careful code reading.

---

## Improvements Given More Time

1. **Machine learning model**: Train a collaborative filtering or matrix factorization model on the student-question data to predict which questions a student would find most beneficial.
2. **Adaptive difficulty**: Track performance on recommended questions and dynamically adjust the difficulty of subsequent recommendations.
3. **Spaced repetition**: Integrate a spaced repetition algorithm so students revisit weak topics at optimal intervals.
4. **Detailed question-level analytics**: Track individual question performance (not just chapter-level) to identify specific misconception patterns.
5. **Frontend dashboard**: Build a React dashboard showing analytics visualizations and the study plan timeline.
6. **Database backend**: Replace JSON files with MongoDB for scalability and real-time updates.
7. **A/B testing framework**: Test different recommendation strategies against each other to measure which produces the best student outcomes.

---

## Project Structure

```
acadza-assignment/
├── app/
│   ├── main.py              # FastAPI app with 4 endpoints
│   ├── data_loader.py        # Data loading & normalization
│   ├── analyzer.py           # Student analysis logic
│   ├── recommender.py        # DOST recommendation engine
│   └── utils.py              # Marks parser, HTML stripper
├── data/                     # Input data files
├── debug/
│   ├── recommender_buggy.py  # Original buggy file
│   └── recommender_fixed.py  # Fixed with explanation
├── sample_outputs/           # Generated outputs for all students
├── generate_outputs.py       # Script to generate sample outputs
├── requirements.txt
├── README.md
└── run.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/{student_id}` | Analyze student performance |
| POST | `/recommend/{student_id}` | Get personalized study plan |
| GET | `/question/{question_id}` | Look up a question |
| GET | `/leaderboard` | Rank all students |

## Leaderboard Scoring Formula

`Score = 0.40 × marks% + 0.25 × completion_rate + 0.20 × attempt_rate + 0.15 × time_efficiency`

This weights actual performance highest, followed by consistency (completion), effort (attempt rate), and speed (time management).
