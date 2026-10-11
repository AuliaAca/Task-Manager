# Task Manager MCP Server

A small [Model Context Protocol](https://modelcontextprotocol.io) server that lets an AI assistant manage a to-do list stored in SQLite.

It is built with the official MCP Python SDK (`mcp` 2.3.0, `MCPServer`, formerly called `FastMCP`) and talks over **stdio**. It is designed to be strict and predictable, so it can also serve as a reliable target for agent tests.

## Requirements

- Python 3.10 or newer
- Node.js (only needed for MCP Inspector)

## Installation

```bash
git clone https://github.com/AuliaAca/Task-Manager.git
cd Task-Manager

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

| Environment variable | Default      | Meaning                          |
| -------------------- | ------------ | -------------------------------- |
| `TASKS_DB_PATH`      | `./tasks.db` | Path of the SQLite database file |

The database file and its table are created automatically on first use. The default path is relative to the directory the server is started from, so set an absolute path whenever another program launches the server.

## Running the tests

```bash
pytest
```

Every test uses its own temporary database, so your real `tasks.db` is never touched.

## Testing with MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the official tool for trying an MCP server by hand.

**Web UI** (run from the project folder with the virtualenv active):

```bash
npx @modelcontextprotocol/inspector python server.py
```

Open the URL it prints, click **Connect**, open the **Tools** tab, click **List Tools**, pick a tool, fill in the arguments and click **Run Tool**.

**Command line** (no browser needed). Put the server command first, then the options. Use `-e` to pass environment variables, because Inspector does not forward your shell's variables to the server:

```bash
npx @modelcontextprotocol/inspector --cli python server.py -e TASKS_DB_PATH=/tmp/tasks.db \
  --method tools/list

npx @modelcontextprotocol/inspector --cli python server.py -e TASKS_DB_PATH=/tmp/tasks.db \
  --method tools/call --tool-name add_task --tool-arg title="Write report" due_date=2026-10-31 priority=1
```

## Connecting to Claude Desktop

Open the Claude Desktop config file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add the server under `mcpServers`. Use **absolute paths**, pointing `command` at the Python inside the virtualenv:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "/absolute/path/to/Task-Manager/.venv/bin/python",
      "args": ["/absolute/path/to/Task-Manager/server.py"],
      "env": {
        "TASKS_DB_PATH": "/absolute/path/to/Task-Manager/tasks.db"
      }
    }
  }
}
```

On Windows, use `C:\\path\\to\\Task-Manager\\.venv\\Scripts\\python.exe` as the command (backslashes must be doubled in JSON). Restart Claude Desktop after saving the file.

## Tools

| Tool            | Inputs                                                  | What it does                                   |
| --------------- | ------------------------------------------------------- | ---------------------------------------------- |
| `add_task`      | `title: string`, `due_date: string \| null`, `priority: integer` | Creates a new open task                        |
| `list_tasks`    | `status: "open" \| "done" \| "all"`                     | Lists matching tasks, ordered by ID            |
| `complete_task` | `task_id: integer`                                      | Marks one task as done                         |
| `delete_task`   | `task_id: integer`                                      | Permanently deletes exactly one task           |

Input rules:

- `title`: 1–200 characters after surrounding spaces are removed; empty or whitespace-only titles are rejected.
- `due_date`: `null`, or a real calendar date written exactly as `YYYY-MM-DD` (`2026-02-30` is rejected).
- `priority`: exactly `1`, `2` or `3`.
- `task_id`: a positive whole number that belongs to an existing task.

A task looks like this:

```json
{"id": 1, "title": "Write report", "due_date": "2026-10-31", "priority": 1, "status": "open"}
```

### Response format

Every tool returns the same shape, both as JSON text and as structured content:

```json
{"ok": true, "data": {"id": 1, "title": "Write report", "due_date": "2026-10-31", "priority": 1, "status": "open"}}
```

```json
{"ok": false, "error": "Task with ID 999 not found."}
```

Failed calls are also marked with the MCP `isError: true` flag, so a client cannot mistake a failure for a success.

Arguments with the wrong JSON type (for example a string where an integer is expected) or a missing argument are rejected by the MCP SDK's schema check before the tool runs. Those calls also come back with `isError: true`, with the SDK's own validation message instead of the `ok`/`error` object.

## What this server refuses to do

- **No bulk deletes.** There is no "delete all" or "delete many" tool. `delete_task` takes a single ID and removes at most one row, matched by primary key.
- **No raw SQL.** No tool accepts SQL. Every query is a fixed statement with `?` placeholders, so input such as `x'); DROP TABLE tasks; --` is stored as plain text.
- **No unknown IDs.** Completing or deleting an ID that does not exist returns `Task with ID <id> not found.` and changes nothing.
- **No reused IDs.** The ID of a deleted task is never given to a new task, so an old ID cannot silently point at a different task.
- **No loose types.** Integers must be real integers: `true`, `"2"` and `2.0` are rejected instead of being converted.
- **No invalid data.** Empty, whitespace-only or overlong titles, badly formatted or impossible dates, priorities other than 1–3, and non-positive task IDs are rejected. The database also enforces the title, priority and status rules with `CHECK` constraints as a second line of defence.
- **No unexpected crashes.** Validation, missing-task and database errors are always returned as `{"ok": false, "error": ...}`.
- **Out of scope:** editing a task's title, date or priority, reopening a done task, and searching. There are no tools for these.

## Project structure

```
server.py        MCP tool definitions only (thin layer)
validation.py    All input validation rules
db.py            All SQLite access
tests/           pytest tests for validation, the database and the tools
requirements.txt Python dependencies
```
