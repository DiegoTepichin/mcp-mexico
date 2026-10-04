from collections.abc import Iterator
from contextlib import contextmanager

from mcp.server.mcpserver.exceptions import ToolError

from mcp_mexico.errors import McpMexicoError


@contextmanager
def as_tool_error() -> Iterator[None]:
    try:
        yield
    except McpMexicoError as error:
        raise ToolError(str(error)) from error
