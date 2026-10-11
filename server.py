"""MCP tool definitions for the task manager.

This file stays thin: arguments are checked by validation.py, data is stored
by db.py, and every result is wrapped in the same response format:
    success: {"ok": true, "data": ...}
    failure: {"ok": false, "error": "..."}
"""

import json
import sqlite3
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent
from pydantic import StrictInt

import db
import validation
from db import TaskNotFoundError
from validation import ValidationError

mcp = MCPServer("task-manager")


@mcp.tool()
def add_task(title: str, due_date: str | None, priority: StrictInt) -> CallToolResult:
    """Create a new open task.

    title: 1-200 characters, not only spaces.
    due_date: a date written as YYYY-MM-DD, or null for no due date.
    priority: 1, 2, or 3.
    """
    return respond(
        lambda: db.add_task(
            validation.validate_title(title),
            validation.validate_due_date(due_date),
            validation.validate_priority(priority),
        )
    )


@mcp.tool()
def list_tasks(status: Literal["open", "done", "all"]) -> CallToolResult:
    """List tasks that are "open", "done", or "all" tasks, ordered by ID."""
    return respond(lambda: db.list_tasks(validation.validate_status(status)))


@mcp.tool()
def complete_task(task_id: StrictInt) -> CallToolResult:
    """Mark the task with this ID as done. The ID must exist."""
    return respond(lambda: db.complete_task(validation.validate_task_id(task_id)))


@mcp.tool()
def delete_task(task_id: StrictInt) -> CallToolResult:
    """Permanently delete exactly one task by its ID. The ID must exist."""
    return respond(lambda: db.delete_task(validation.validate_task_id(task_id)))


def respond(action) -> CallToolResult:
    """Run a tool action and wrap its outcome in the shared response format.

    Failures are also flagged with isError, so a client cannot mistake them
    for success even if it never looks at "ok".
    """
    try:
        payload = {"ok": True, "data": action()}
    except (ValidationError, TaskNotFoundError) as error:
        payload = {"ok": False, "error": str(error)}
    except sqlite3.Error as error:
        payload = {"ok": False, "error": f"Database error: {error}"}

    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structured_content=payload,
        is_error=not payload["ok"],
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
