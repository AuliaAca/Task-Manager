import pytest

from validation import (
    MAX_TASK_ID,
    ValidationError,
    validate_due_date,
    validate_priority,
    validate_status,
    validate_task_id,
    validate_title,
)


# --- title ---------------------------------------------------------------

def test_title_is_returned_without_surrounding_spaces():
    assert validate_title("  Buy milk  ") == "Buy milk"


def test_title_of_one_and_two_hundred_characters_is_accepted():
    assert validate_title("a") == "a"
    assert validate_title("a" * 200) == "a" * 200


@pytest.mark.parametrize("title", ["", " ", "   \t\n "])
def test_empty_or_blank_title_is_rejected(title):
    with pytest.raises(ValidationError, match="must not be empty"):
        validate_title(title)


def test_title_longer_than_two_hundred_characters_is_rejected():
    with pytest.raises(ValidationError, match=r"at most 200 characters \(got 201\)"):
        validate_title("a" * 201)


@pytest.mark.parametrize("title", [None, 123, ["Buy milk"]])
def test_title_that_is_not_text_is_rejected(title):
    with pytest.raises(ValidationError, match="must be text"):
        validate_title(title)


# --- due_date ------------------------------------------------------------

def test_missing_due_date_is_allowed():
    assert validate_due_date(None) is None


@pytest.mark.parametrize("due_date", ["2026-10-31", "2024-02-29", "1999-01-01"])
def test_valid_due_date_is_accepted(due_date):
    assert validate_due_date(due_date) == due_date


@pytest.mark.parametrize(
    "due_date",
    ["31-10-2026", "2026/10/31", "20261031", "2026-1-5", "2026-10-31T10:00", "tomorrow", "", 20261031],
)
def test_due_date_in_wrong_format_is_rejected(due_date):
    with pytest.raises(ValidationError, match="format YYYY-MM-DD"):
        validate_due_date(due_date)


@pytest.mark.parametrize("due_date", ["2026-02-30", "2025-02-29", "2026-13-01", "2026-00-10"])
def test_impossible_calendar_date_is_rejected(due_date):
    with pytest.raises(ValidationError, match="not a real calendar date"):
        validate_due_date(due_date)


# --- priority ------------------------------------------------------------

@pytest.mark.parametrize("priority", [1, 2, 3])
def test_priority_one_to_three_is_accepted(priority):
    assert validate_priority(priority) == priority


@pytest.mark.parametrize("priority", [0, 4, -1, 2.0, "2", True, None])
def test_other_priority_is_rejected(priority):
    with pytest.raises(ValidationError, match="priority must be 1, 2, or 3"):
        validate_priority(priority)


# --- status --------------------------------------------------------------

@pytest.mark.parametrize("status", ["open", "done", "all"])
def test_known_status_is_accepted(status):
    assert validate_status(status) == status


@pytest.mark.parametrize("status", ["OPEN", "closed", "", None])
def test_unknown_status_is_rejected(status):
    with pytest.raises(ValidationError, match="status must be one of"):
        validate_status(status)


# --- task_id -------------------------------------------------------------

@pytest.mark.parametrize("task_id", [1, 42, MAX_TASK_ID])
def test_positive_task_id_is_accepted(task_id):
    assert validate_task_id(task_id) == task_id


@pytest.mark.parametrize("task_id", [0, -5, 1.5, "3", True, None])
def test_task_id_that_is_not_a_positive_whole_number_is_rejected(task_id):
    with pytest.raises(ValidationError, match="positive whole number"):
        validate_task_id(task_id)


def test_task_id_larger_than_sqlite_can_store_is_rejected():
    with pytest.raises(ValidationError, match="too large"):
        validate_task_id(MAX_TASK_ID + 1)
