import sqlite3

import pytest

import db
from db import TaskNotFoundError


def test_database_is_created_at_tasks_db_path(temporary_database):
    db.add_task("Buy milk", None, 2)

    assert temporary_database.exists()


def test_add_task_returns_the_stored_task():
    task = db.add_task("Buy milk", "2026-10-31", 1)

    assert task == {
        "id": 1,
        "title": "Buy milk",
        "due_date": "2026-10-31",
        "priority": 1,
        "status": "open",
    }


def test_list_tasks_filters_by_status():
    first = db.add_task("First", None, 1)
    second = db.add_task("Second", None, 2)
    db.complete_task(first["id"])

    assert [task["id"] for task in db.list_tasks("open")] == [second["id"]]
    assert [task["id"] for task in db.list_tasks("done")] == [first["id"]]
    assert [task["id"] for task in db.list_tasks("all")] == [first["id"], second["id"]]


def test_list_tasks_on_empty_database_returns_empty_list():
    assert db.list_tasks("all") == []


def test_complete_task_marks_task_as_done():
    task = db.add_task("Write report", None, 3)

    completed = db.complete_task(task["id"])

    assert completed["status"] == "done"


def test_complete_task_twice_keeps_task_done():
    task = db.add_task("Write report", None, 3)
    db.complete_task(task["id"])

    assert db.complete_task(task["id"])["status"] == "done"


def test_complete_missing_task_raises_clear_error():
    with pytest.raises(TaskNotFoundError, match="Task with ID 999 not found."):
        db.complete_task(999)


def test_delete_task_removes_only_that_task():
    keep = db.add_task("Keep me", None, 1)
    remove = db.add_task("Remove me", None, 1)

    deleted = db.delete_task(remove["id"])

    assert deleted == remove
    assert db.list_tasks("all") == [keep]


def test_delete_missing_task_raises_clear_error_and_deletes_nothing():
    task = db.add_task("Keep me", None, 1)

    with pytest.raises(TaskNotFoundError, match="Task with ID 999 not found."):
        db.delete_task(999)

    assert db.list_tasks("all") == [task]


def test_deleted_id_is_not_reused():
    old = db.add_task("Old", None, 1)
    db.delete_task(old["id"])

    new = db.add_task("New", None, 1)

    assert new["id"] != old["id"]


def test_sql_in_title_is_stored_as_plain_text():
    title = "x'); DROP TABLE tasks; --"

    task = db.add_task(title, None, 1)

    assert task["title"] == title
    assert db.list_tasks("all") == [task]


def test_database_rejects_invalid_priority_even_without_validation():
    with pytest.raises(sqlite3.IntegrityError):
        db.add_task("Bad priority", None, 7)

    assert db.list_tasks("all") == []
