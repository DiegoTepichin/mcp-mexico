from datetime import date

import pytest
from mcp import Client

from mcp_mexico.fiscal.uma import uma_in_force
from mcp_mexico.server import build_server

pytestmark = pytest.mark.anyio


async def test_lists_tools_as_read_only() -> None:
    async with Client(build_server()) as client:
        result = await client.list_tools()

    tools = {tool.name: tool for tool in result.tools}
    assert set(tools) == {"get_uma"}
    annotations = tools["get_uma"].annotations
    assert annotations is not None
    assert annotations.read_only_hint is True


async def test_get_uma_by_year() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("get_uma", {"year": 2024})

    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["daily"] == 108.57
    assert result.structured_content["source"]["name"].startswith("INEGI")


async def test_get_uma_defaults_to_value_in_force_today() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("get_uma", {})

    assert result.structured_content is not None
    assert result.structured_content["year"] == uma_in_force(date.today()).year


async def test_get_uma_unknown_year_is_a_tool_error() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("get_uma", {"year": 2019})

    assert result.is_error
    assert "Available years: 2020-2026" in str(result.content)
