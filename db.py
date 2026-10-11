"""All SQLite access for the task manager.

Every query uses `?` placeholders, so values are never pasted into SQL text.
The database location comes from the TASKS_DB_PATH environment variable.
"""

import os
import sqlite3
from contextlib import contextmanager

DEFAULT_DB_PATH = "tasks.db"

# AUTOINCREMENT stops SQLite from reusing the ID of a deleted task, so an old
# ID can never silently point at a different task. The CHECK constraints are
# a last line of defence in case invalid data ever slips past validation.py.
SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT    NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    due_date TEXT,
    priority INTEGER NOT NULL CHECK (priority IN (1, 2, 3)),
    status   TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done'))
)
"""


class TaskNotFoundError(LookupError):
    """Raised when no task has the requested ID."""

    def __init__(self, task_id: int):
        super().__init__(f"Task with ID {task_id} not found.")


def get_db_path() -> str:
    """Read the path on every call so a changed TASKS_DB_PATH is respected."""
    return os.environ.get("TASKS_DB_PATH", DEFAULT_DB_PATH)


@contextmanager
def connect():
    """Open a connection, commit on success, roll back on error, always close."""
    connection = sqlite3.connect(get_db_path())
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(SCHEMA)
            yield connection
    finally:
        connection.close()


def add_task(title: str, due_date: str | None, priority: int) -> dict:
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, due_date, priority) VALUES (?, ?, ?)",
            (title, due_date, priority),
        )
        return _get_task(connection, cursor.lastrowid)


def list_tasks(status: str) -> list[dict]:
    """Return tasks with the given status ("open" or "done"), or all tasks for "all"."""
    with connect() as connection:
        if status == "all":
            rows = connection.execute(
                "SELECT id, title, due_date, priority, status FROM tasks ORDER BY id"
            )
        else:
            rows = connection.execute(
                "SELECT id, title, due_date, priority, status FROM tasks WHERE status = ? ORDER BY id",
                (status,),
            )
        return [dict(row) for row in rows]


def complete_task(task_id: int) -> dict:
    """Mark one task as done. Completing a task that is already done is allowed."""
    with connect() as connection:
        cursor = connection.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ?",
            (task_id,),
        )
        if cursor.rowcount == 0:
            raise TaskNotFoundError(task_id)
        return _get_task(connection, task_id)


def delete_task(task_id: int) -> dict:
    """Delete exactly one task by its primary key and return what was deleted."""
    with connect() as connection:
        task = _get_task(connection, task_id)
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return task


def _get_task(connection: sqlite3.Connection, task_id: int) -> dict:
    row = connection.execute(
        "SELECT id, title, due_date, priority, status FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        raise TaskNotFoundError(task_id)
    return dict(row)
