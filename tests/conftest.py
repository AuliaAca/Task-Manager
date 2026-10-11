import pytest


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    """Give every test its own empty database so tests never touch tasks.db."""
    db_path = tmp_path / "test_tasks.db"
    monkeypatch.setenv("TASKS_DB_PATH", str(db_path))
    return db_path
