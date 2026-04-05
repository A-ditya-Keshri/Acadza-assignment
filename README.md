# Acadza AI Intern Assignment — Student Performance Recommender

## Data Analysis

The dataset consists of 10 students with 5-8 sessions, noting the subject, chapters, marks, time spent, attempted versus skipped questions, and outliers in question IDs.

The analyzer determines completion rate, average marks, attempt rate, and trend direction. Moreover, it categorizes performances based on the subject (Physics, Chemistry, Math), chapter, and question type (SCQ, MCQ, Integer). Trends are assessed within the session in terms of comparing the first half and second half averages to determine improvement or decline.

Marks in inconsistent forms were the annoying part. Marks were recorded in five ways: 68/100, 28, +52 -12, 34/75 (45.3%), and simply integers. I developed a regular expression parser to accommodate all five. The net marks are the common denominator but aren't consistent across various total marks; hence, they aren't always the most comparable values. However, marks are normalized with respect to the maximum assumed value of 80 for the leaderboard.

## DOST Recommendation Strategy

The recommendation follows the progressively challenging strategy based on weaknesses:

- Very weak chapters (average mark < 25): concept -> formula -> practiceAssignment
- Weak chapters: formula -> practiceAssignment (skip concept)
- Overall weaknesses: 3-day revision of all weak areas
- Evaluation: timed practiceTest under simulated exam conditions
- Slow problem solvers (average time > 150 seconds): clickingPower drill
- Low attempt rates (<85%): pickingPower MCQ elimination practice
- Confidence booster: speedRace in a strong chapter to end on a high note

Each recommendation uses a set of question IDs selected from the bank based on topic and difficulty.

## Debug Task

`debug/recommender_buggy.py` works fine but provides the same recommendations to all the students. The error occurs in lines 54-55:

```python
# BUGGY:
profile_norm = np.linalg.norm(cohort_baseline)           # wrong variable
student_profile = cohort_baseline / (profile_norm + 1e-10)  # overwrites student data
```

Line 51 already correctly computes the student_profile as `student_matrix[student_idx] - cohort_baseline`, which is the difference between the individual and average. Lines 54-55 then overwrite `student_profile` with the normalization of `cohort_baseline` instead. All the students then get the normalized cohort average as the recommended profile.

```python
# FIXED:
profile_norm = np.linalg.norm(student_profile)
student_profile = student_profile / (profile_norm + 1e-10)
```

It is just a variable name swap. The result will be the same, i.e., no crash and valid output; however, it removes any personalization. The code comments that "normalize the adjusted profile"; however, it instead normalizes `cohort_baseline`.

## What I'd Add With More Time

- I would like to add more collaborative filtering or matrix factorization methods to predict benefits from individual questions.
- Moreover, the difficulty could be adjusted adaptively based on performance on previously recommended questions.
- Spaced repetition of weak topics would also help improve retention.
- Additionally, I would like to incorporate React dashboard with analytics and study plan timeline.
- Finally, I would migrate to MongoDB from JSON files and conduct A/B testing on recommendations.

## Leaderboard Formula

`Score = 0.40 × marks% + 0.25 × completion_rate + 0.20 × attempt_rate + 0.15 × time_efficiency`
