"""Task Manager MCP server.

This file only defines MCP tools. Stage 1: a single "hello" tool to check
that the server starts and can be reached from MCP Inspector.
"""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("task-manager")


@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone. Used only to check that the server works."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="stdio")
