"""
ClarityFlow v1 - db stuff (SQLite)

Notes:
- Striving for a rough but WORKING v1, not perfect architecture
- tasks table holds the schema fields (title, due date, load,etc)
- dependencies table is just edges: task -> prerequisite
- insights are deterministic (no additional AI API, like AURA), based on rules

If something is missing (like due_date), I just report it in missing_data_report().

"""
# DB + rule logic for ClarityFlow v1.

# This file intentionally keeps things "boring":
# - SQLite (file-based)
# - Tiny CRUD helpers
# - A few deterministic insights (blocked + missing-data)

# Folder layout expected:
# ClarityFlow_V1/
#   app/
#     __init__.py
#     db.py
#     main.py
#   run_db_test.py
#   venv/

# NOTE:
# - I will store dates as TEXT (ISO-ish) because v1 is about structure + logic, not perfect date parsing.
# - Dependencies are directed edges: (task_id -> depends_on_task_id)

from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# DB location + connection

# Put the DB file in the project root folder (same level as "app/").
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "clarityflow_v1.db")


def get_conn() -> sqlite3.Connection:
    """
    Open a SQLite connection with dict-ish rows.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # This makes FK constraints actually apply in SQLite.
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """
    Creates tables if they do not exist yet.
    Safe to call repeatedly.
    """

    conn = get_conn()
    cur = conn.cursor()

    # Tasks: keep schema fields close to the Figma schema.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'todo',
            due_date TEXT,
            estimate_minutes INTEGER,
            cognitive_load TEXT,
            flexibility TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Dependencies: task_id depends on depends_on_task_id.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            depends_on_task_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY(depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            UNIQUE(task_id, depends_on_task_id)
        );
        """
    )

    conn.commit()
    conn.close()



# Models 

class TaskCreate(BaseModel):
    """
    What we return to user.
    """
    title: str = Field(..., min_length=1)
    notes: Optional[str] = None
    status: str = Field(default="todo")  # todo / doing / done
    due_date: Optional[str] = None       # store as string for v1
    estimate_minutes: Optional[int] = Field(default=None, ge=0)
    cognitive_load: Optional[str] = None  # low / med / high (string for v1)
    flexibility: Optional[str] = None     # fixed / flexible (string for v1)


class TaskOut(TaskCreate):
    """
    What we return to the client.
    """
    id: int


class DependencyCreate(BaseModel):
    """
    task_id depends on depends_on_task_id.
    """
    task_id: int
    depends_on_task_id: int


class DependencyOut(DependencyCreate):
    id: int




# ___ row helpers__

def _row_to_task(row: sqlite3.Row) -> TaskOut:
    return TaskOut(
        id=row["id"],
        title=row["title"],
        notes=row["notes"],
        status=row["status"],
        due_date=row["due_date"],
        estimate_minutes=row["estimate_minutes"],
        cognitive_load=row["cognitive_load"],
        flexibility=row["flexibility"],
    )


def _row_to_dependency(row: sqlite3.Row) -> DependencyOut:
    return DependencyOut(
        id=row["id"],
        task_id=row["task_id"],
        depends_on_task_id=row["depends_on_task_id"],
    )



# __CRUD: Tasks___

def list_tasks() -> List[TaskOut]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC;").fetchall()
    conn.close()
    return [_row_to_task(r) for r in rows]


def get_task(task_id: int) -> Optional[TaskOut]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
    conn.close()
    return _row_to_task(row) if row else None


def create_task(payload: TaskCreate) -> TaskOut:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tasks (title, notes, status, due_date, estimate_minutes, cognitive_load, flexibility)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            payload.title,
            payload.notes,
            payload.status,
            payload.due_date,
            payload.estimate_minutes,
            payload.cognitive_load,
            payload.flexibility,
        ),
    )
    task_id = cur.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
    conn.close()
    return _row_to_task(row)


def update_task(task_id: int, payload: TaskCreate) -> Optional[TaskOut]:
    conn = get_conn()
    cur = conn.cursor()

    # Testing if the task exists before trying to update (could also just try to update and check affected rows).
    exists = conn.execute("SELECT 1 FROM tasks WHERE id = ?;", (task_id,)).fetchone()
    if not exists:
        conn.close()
        return None

    cur.execute(
        """
        UPDATE tasks
        SET title = ?,
            notes = ?,
            status = ?,
            due_date = ?,
            estimate_minutes = ?,
            cognitive_load = ?,
            flexibility = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?;
        """,
        (
            payload.title,
            payload.notes,
            payload.status,
            payload.due_date,
            payload.estimate_minutes,
            payload.cognitive_load,
            payload.flexibility,
            task_id,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,)).fetchone()
    conn.close()
    return _row_to_task(row)


def delete_task(task_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


# Dependencies

def list_dependencies() -> List[DependencyOut]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM dependencies ORDER BY id DESC;").fetchall()
    conn.close()
    return [_row_to_dependency(r) for r in rows]


def add_dependency(payload: DependencyCreate) -> DependencyOut:
    """
 guardrails: no self-deps, both tasks must exist, UNIQUE enforced by db
    """
    if payload.task_id == payload.depends_on_task_id:
        raise ValueError("Task cannot depend on itself.")

    conn = get_conn()

    # Check that both task_id and depends_on_task_id exist before trying to insert the edge.
    a = conn.execute("SELECT 1 FROM tasks WHERE id = ?;", (payload.task_id,)).fetchone()
    b = conn.execute("SELECT 1 FROM tasks WHERE id = ?;", (payload.depends_on_task_id,)).fetchone()
    if not a or not b:
        conn.close()
        raise ValueError("One or both tasks not found. Both must exist to create a dependency.")

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO dependencies (task_id, depends_on_task_id)
            VALUES (?, ?);
            """,
            (payload.task_id, payload.depends_on_task_id),
        )
        dep_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        # Most common: UNIQUE(task_id, depends_on_task_id) triggered.
        raise ValueError("dependency already exists.") from e

    row = conn.execute("SELECT * FROM dependencies WHERE id = ?;", (dep_id,)).fetchone()
    conn.close()
    return _row_to_dependency(row)




# Insights: deterministic

def blocked_tasks() -> Dict[str, Any]:
    """
    Blocked = task has at least one prerequisite not marked 'done'.

    Returns:
      {
        "blocked": [
          {"task": <TaskOut>, "missing_prereqs": [<TaskOut>, ...]},
          ...
        ]
      }
    """

    conn = get_conn()

    # Find tasks that have prereqs not done
    # We'll also collect which prereqs are causing the block.
    blocked_rows = conn.execute(
        """
        SELECT DISTINCT t.*
        FROM tasks t
        WHERE EXISTS (
            SELECT 1
            FROM dependencies d
            JOIN tasks prereq ON prereq.id = d.depends_on_task_id
            WHERE d.task_id = t.id
              AND prereq.status != 'done'
        )
        ORDER BY t.id DESC;
        """
    ).fetchall()

    results: List[Dict[str, Any]] = []
    for trow in blocked_rows:
        task = _row_to_task(trow)

        prereq_rows = conn.execute(
            """
            SELECT prereq.*
            FROM dependencies d
            JOIN tasks prereq ON prereq.id = d.depends_on_task_id
            WHERE d.task_id = ?
              AND prereq.status != 'done'
            ORDER BY prereq.id DESC;
            """,
            (task.id,),
        ).fetchall()

        missing = [_row_to_task(r) for r in prereq_rows]
        results.append({"task": task, "missing_prereqs": missing})

    conn.close()
    return {"blocked": results}


def missing_data_report() -> Dict[str, Any]:
    """
    Basic diagnostics for v1.
    If fields are missing, some insights can not be computed.
    """
    tasks = list_tasks()

    missing_due = [t.id for t in tasks if not t.due_date]
    missing_est = [t.id for t in tasks if t.estimate_minutes is None]
    missing_load = [t.id for t in tasks if not t.cognitive_load]

    return {
        "missing_due_date": {"count": len(missing_due), "examples": missing_due[:5]},
        "missing_estimate_minutes": {"count": len(missing_est), "examples": missing_est[:5]},
        "missing_cognitive_load": {"count": len(missing_load), "examples": missing_load[:5]},
        "note": "Missing fields limit some insights",
    }
