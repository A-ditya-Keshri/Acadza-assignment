# How to Run

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd acadza-assignment
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the FastAPI Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`. You can access the interactive API docs at `http://localhost:8000/docs`.

## API Endpoints

### 1. Analyze a Student
```bash
curl -X POST http://localhost:8000/analyze/STU_001
```

### 2. Get Recommendations for a Student
```bash
curl -X POST http://localhost:8000/recommend/STU_001
```

### 3. Look Up a Question
```bash
curl http://localhost:8000/question/Q_PHY_0018
```

### 4. View Leaderboard
```bash
curl http://localhost:8000/leaderboard
```

## Generating Sample Outputs

To generate analysis and recommendation outputs for all 10 students:

```bash
python generate_outputs.py
```

This creates JSON files in the `sample_outputs/` directory:
- `STU_001_analyze.json` through `STU_010_analyze.json`
- `STU_001_recommend.json` through `STU_010_recommend.json`
- `leaderboard.json`

## Running the Debug Fix

To verify the bug fix in the recommender:

```bash
# Run the buggy version (all students get same recommendations):
python debug/recommender_buggy.py

# Run the fixed version (each student gets personalized recommendations):
python debug/recommender_fixed.py
```

## Student IDs

Available student IDs: `STU_001` through `STU_010`
