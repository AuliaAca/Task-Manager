"""End-to-end tests that call the tools through a real MCP client."""

import asyncio
import json

from mcp import Client

from server import mcp


def call(tool: str, **arguments):
    async def run():
        async with Client(mcp) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(run())


def list_tools():
    async def run():
        async with Client(mcp) as client:
            return (await client.list_tools()).tools

    return {tool.name: tool for tool in asyncio.run(run())}


def add(title="Buy milk", due_date=None, priority=2):
    return call("add_task", title=title, due_date=due_date, priority=priority)


# --- tool list and typed inputs ------------------------------------------

def test_server_exposes_exactly_the_four_task_tools():
    assert set(list_tools()) == {"add_task", "list_tasks", "complete_task", "delete_task"}


def test_tool_inputs_are_typed():
    tools = list_tools()

    add_task_inputs = tools["add_task"].input_schema["properties"]
    assert add_task_inputs["title"]["type"] == "string"
    assert add_task_inputs["priority"]["type"] == "integer"
    assert tools["list_tasks"].input_schema["properties"]["status"]["enum"] == ["open", "done", "all"]
    assert tools["delete_task"].input_schema["properties"]["task_id"]["type"] == "integer"


# --- response format ------------------------------------------------------

def test_success_uses_ok_data_format():
    result = add(title="Buy milk", due_date="2026-10-31", priority=1)

    expected = {
        "ok": True,
        "data": {"id": 1, "title": "Buy milk", "due_date": "2026-10-31", "priority": 1, "status": "open"},
    }
    assert result.structured_content == expected
    assert json.loads(result.content[0].text) == expected
    assert result.is_error is False


def test_failure_uses_ok_error_format_and_is_flagged_as_error():
    result = add(title="   ")

    assert result.structured_content == {"ok": False, "error": "title must not be empty or only spaces."}
    assert json.loads(result.content[0].text) == result.structured_content
    assert result.is_error is True


# --- each tool ------------------------------------------------------------

def test_add_then_list_tasks():
    add(title="First")
    add(title="Second")

    result = call("list_tasks", status="all")

    assert [task["title"] for task in result.structured_content["data"]] == ["First", "Second"]


def test_complete_task_moves_task_from_open_to_done():
    task_id = add().structured_content["data"]["id"]

    result = call("complete_task", task_id=task_id)

    assert result.structured_content["data"]["status"] == "done"
    assert call("list_tasks", status="open").structured_content["data"] == []
    assert len(call("list_tasks", status="done").structured_content["data"]) == 1


def test_delete_task_removes_exactly_one_task():
    keep_id = add(title="Keep").structured_content["data"]["id"]
    remove_id = add(title="Remove").structured_content["data"]["id"]

    result = call("delete_task", task_id=remove_id)

    assert result.structured_content["data"]["id"] == remove_id
    remaining = call("list_tasks", status="all").structured_content["data"]
    assert [task["id"] for task in remaining] == [keep_id]


# --- rejected input -------------------------------------------------------

def test_missing_task_gives_clear_error_not_a_crash():
    for tool in ("complete_task", "delete_task"):
        result = call(tool, task_id=999)

        assert result.structured_content == {"ok": False, "error": "Task with ID 999 not found."}
        assert result.is_error is True


def test_invalid_values_are_rejected_and_nothing_is_stored():
    assert "real calendar date" in add(due_date="2026-02-30").structured_content["error"]
    assert "priority must be 1, 2, or 3" in add(priority=5).structured_content["error"]
    assert "positive whole number" in call("delete_task", task_id=0).structured_content["error"]

    assert call("list_tasks", status="all").structured_content["data"] == []


def test_wrong_argument_types_are_rejected_before_reaching_the_tool():
    rejected = [
        add(priority=True),
        add(priority="2"),
        call("complete_task", task_id="1"),
        call("list_tasks", status="everything"),
        call("add_task", title="No priority", due_date=None),
    ]

    assert all(result.is_error for result in rejected)
    assert call("list_tasks", status="all").structured_content["data"] == []


def test_database_problem_is_reported_as_error(monkeypatch, tmp_path):
    monkeypatch.setenv("TASKS_DB_PATH", str(tmp_path / "missing-folder" / "tasks.db"))

    result = call("list_tasks", status="all")

    assert result.structured_content["ok"] is False
    assert result.structured_content["error"].startswith("Database error:")
    assert result.is_error is True
