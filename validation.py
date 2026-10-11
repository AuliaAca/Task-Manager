"""All input validation rules.

Each function either returns a clean value or raises ValidationError with a
message that tells the caller exactly what was wrong.
"""

import re
from datetime import date

TITLE_MAX_LENGTH = 200
PRIORITIES = (1, 2, 3)
STATUSES = ("open", "done", "all")
# Largest integer SQLite can store. Bigger IDs cannot exist and would crash sqlite3.
MAX_TASK_ID = 2**63 - 1

# [0-9] instead of \d, because \d also matches non-ASCII digits such as "٢".
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class ValidationError(ValueError):
    """Raised when a tool argument breaks one of the rules."""


def validate_title(title: str) -> str:
    """Return the title without surrounding spaces."""
    if not isinstance(title, str):
        raise ValidationError("title must be text.")
    title = title.strip()
    if not title:
        raise ValidationError("title must not be empty or only spaces.")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError(
            f"title must be at most {TITLE_MAX_LENGTH} characters (got {len(title)})."
        )
    return title


def validate_due_date(due_date: str | None) -> str | None:
    """Accept None (no due date) or a real calendar date written as YYYY-MM-DD."""
    if due_date is None:
        return None
    if not isinstance(due_date, str) or not DATE_PATTERN.fullmatch(due_date):
        raise ValidationError(
            f"due_date must use the format YYYY-MM-DD, for example 2026-12-31 (got {due_date!r})."
        )
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError(f"due_date {due_date!r} is not a real calendar date.") from None
    return due_date


def validate_priority(priority: int) -> int:
    if not _is_integer(priority) or priority not in PRIORITIES:
        raise ValidationError(f"priority must be 1, 2, or 3 (got {priority!r}).")
    return priority


def validate_status(status: str) -> str:
    if status not in STATUSES:
        raise ValidationError(f"status must be one of: open, done, all (got {status!r}).")
    return status


def validate_task_id(task_id: int) -> int:
    if not _is_integer(task_id) or task_id < 1:
        raise ValidationError(f"task_id must be a positive whole number (got {task_id!r}).")
    if task_id > MAX_TASK_ID:
        raise ValidationError(f"task_id is too large (maximum is {MAX_TASK_ID}).")
    return task_id


def _is_integer(value) -> bool:
    # bool is a subclass of int in Python, so True would otherwise count as 1.
    return isinstance(value, int) and not isinstance(value, bool)
