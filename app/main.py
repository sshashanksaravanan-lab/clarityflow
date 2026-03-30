"""
Adding comments to main.py to explain that this is the API layer for ClarityFlow v1, and it connects to the db logic in db.py.

The API is built using FastAPI and defines endpoints for:
- CRUD operations on tasks
- Managing dependencies between tasks 
- Insights like blocked tasks and missing data

"""


from fastapi import FastAPI, HTTPException
from typing import Any, Dict, List

#Import database setup, CRUD functions, schemas, and insight functions

from app.db import (
    init_db,
    list_tasks, get_task, create_task, update_task, delete_task,
    list_dependencies, add_dependency,
    TaskCreate, TaskOut,
    DependencyCreate, DependencyOut,
    blocked_tasks, missing_data_report,
)

# Create the FastAPI application instance
app = FastAPI(title="ClarityFlow v1", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()

# Basic health-check route to confirm the API is running
@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok", "app": "ClarityFlow v1"}



# TASKS 

# Return all tasks in the database
@app.get("/tasks", response_model=List[TaskOut])
def api_list_tasks() -> List[TaskOut]:
    return list_tasks()


# Return one task by ID, or raise 404 if it does not exist
@app.get("/tasks/{task_id}", response_model=TaskOut)
def api_get_task(task_id: int) -> TaskOut:
    t = get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


#create a new task with the provided data, and return the created task
@app.post("/tasks", response_model=TaskOut)
def api_create_task(payload: TaskCreate) -> TaskOut:
    return create_task(payload)


# Update an existing task by ID, or raise 404 if not found

@app.put("/tasks/{task_id}", response_model=TaskOut)
def api_update_task(task_id: int, payload: TaskCreate) -> TaskOut:
    t = update_task(task_id, payload)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


# Delete as task ID, or raise 404 if not found
@app.delete("/tasks/{task_id}")
def api_delete_task(task_id: int) -> Dict[str, Any]:
    ok = delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "id": task_id}



# DEPENDENCIES

# Return all dependencies in the database
@app.get("/dependencies", response_model=List[DependencyOut])
def api_list_dependencies() -> List[DependencyOut]:
    return list_dependencies()


# Create a new dependency (task -> prerequisite), and return the created 
@app.post("/dependencies", response_model=DependencyOut)
def api_add_dependency(payload: DependencyCreate) -> DependencyOut:
    try:
        return add_dependency(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# INSIGHTS


#return insights about blocked tasks
@app.get("/insights/blocked")
def api_blocked() -> Dict[str, Any]:
    return blocked_tasks()

#Return insights about missing data in tasks
@app.get("/insights/missing-data")
def api_missing_data() -> Dict[str, Any]:
    return missing_data_report()
