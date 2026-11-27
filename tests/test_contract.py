"""The 1.x promise: tool names, arguments and result shapes only grow in compatible ways.

If a change here is intentional and compatible, regenerate the snapshot with
`UPDATE_CONTRACT=1 uv run pytest tests/test_contract.py` and review the diff.
A removed or renamed tool, argument or result field needs a new major version.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_mexico.server import build_server

pytestmark = pytest.mark.anyio

SNAPSHOT = Path(__file__).parent / "contract" / "tools.json"


def _without_prose(schema: Any) -> Any:
    """Drop descriptions and titles: rewording them does not break a client."""
    if isinstance(schema, dict):
        return {
            key: _without_prose(value)
            for key, value in schema.items()
            if not (key in {"description", "title"} and isinstance(value, str))
        }
    if isinstance(schema, list):
        return [_without_prose(item) for item in schema]
    return schema


async def test_tool_contract_matches_the_snapshot() -> None:
    async with Client(build_server()) as client:
        listed = await client.list_tools()
    contract = {
        tool.name: {
            "input": _without_prose(tool.input_schema),
            "output": _without_prose(tool.output_schema),
        }
        for tool in listed.tools
    }
    rendered = json.dumps(contract, indent=2, sort_keys=True) + "\n"
    if os.environ.get("UPDATE_CONTRACT"):
        SNAPSHOT.write_text(rendered, encoding="utf-8")

    assert rendered == SNAPSHOT.read_text(encoding="utf-8")


async def test_the_server_answers_over_stdio() -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from mcp_mexico.server import main; main()"],
    )

    async with Client(stdio_client(server)) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}
        result = await client.call_tool("get_uma", {"year": 2026})

    assert names == set(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    assert result.structured_content is not None
    assert result.structured_content["daily"] == 117.31
