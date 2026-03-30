# clarityflow
ClarityFlow: a schema-driven productivity prototype focused on transparent task sensemaking and inspectable rule-based insights.

# ClarityFlow v1

**Course:** CTS*4020 - University of Guelph  
**Project Type:** Schema-Driven Productivity & Sensemaking Tool  
**Stack:** Python 3.11+, FastAPI, Pydantic, SQLite, Uvicorn  

## What It Is

ClarityFlow is a task sensemaking tool. Unlike productivity apps that rely on auto-scheduling, it uses deterministic logic and schema enforcement to expose what is unclear about a workload, including blocked tasks, missing metadata, and dependency bottlenecks.

The core insight is simple: most productivity tools tell users what to do. ClarityFlow instead shows what is wrong with the plan before work begins.

## Architecture

ClarityFlow/
├── app/
│   ├── main.py          # FastAPI routes and core application logic
│   └── db.py            # SQLite connection, schema initialization, helpers
├── requirements.txt
├── README.md
├── project_log.md
└── test_log.md

## Setup and Run

### 1. Create and activate a virtual environment

python -m venv venv  
source venv/bin/activate  

On Windows:  
venv\Scripts\activate

### 2. Install dependencies

pip install -r requirements.txt

### 3. Start the server

uvicorn app.main:app --reload

### 4. Open interactive docs

http://127.0.0.1:8000/docs

## API Reference

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /tasks | Create a task |
| GET | /tasks | List all tasks |
| PUT | /tasks/{id} | Update a task (partial update supported) |
| DELETE | /tasks/{id} | Delete a task |

### Task Schema

{
  "title": "string (required)",
  "status": "todo | in_progress | done",
  "due_date": "YYYY-MM-DD (optional)",
  "estimate_minutes": "integer (optional)",
  "cognitive_load": "low | medium | high (optional)",
  "notes": "string (optional)"
}

### Dependencies

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /dependencies | Declare that task A depends on task B |
| GET | /dependencies | List all dependency pairs |

### Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /insights/blocked | Tasks blocked by incomplete prerequisites |
| GET | /insights/missing-data | Schema completeness audit |

## How the Insight Routes Work

### /insights/blocked

For each task, the system checks its dependency list. If any upstream task has a status other than done, the downstream task is flagged as blocked. This is pure graph traversal with no machine learning or heuristic ranking.

### /insights/missing-data

This route counts tasks missing due_date, estimate_minutes, or cognitive_load, and returns both totals and example task IDs. It is a deterministic field-presence check.

## Design Decisions
- **SQLite over PostgreSQL:** Appropriate for a single-user v1 prototype. Migration to a larger database is straightforward through changes in db.py and schema setup.
- **Pydantic for validation:** Schema enforcement happens at the API boundary rather than through scattered manual checks.
- **No authentication in v1:** Out of scope for this prototype. A future version could add JWT-based authentication.

## Known Limitations

- No cycle detection in the dependency graph
- Single-user only
- No pagination on GET /tasks
- SQLite write contention under concurrent load, though this is not a major concern for v1
