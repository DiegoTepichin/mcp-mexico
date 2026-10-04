from typing import Any

import pytest
from mcp import Client

from mcp_mexico.server import build_server
from mcp_mexico.sources.inegi import InegiClient
from tests.conftest import banxico_client, inegi_client

pytestmark = pytest.mark.anyio


async def _call(tool: str, arguments: dict[str, Any], inegi: InegiClient) -> Any:
    banxico, _ = banxico_client()
    async with Client(build_server(banxico, inegi)) as client:
        return await client.call_tool(tool, arguments)


@pytest.mark.parametrize(
    ("arguments", "period", "inpc", "monthly", "annual"),
    [
        ({}, "2026-08", 145.462, 0.20, 3.26),
        ({"year": 2024, "month": 12}, "2024-12", 137.949, 0.38, 4.21),
        ({"year": 2023, "month": 6}, "2023-06", 128.214, 0.10, 5.06),
    ],
)
async def test_inflation_matches_inegi_publications(
    arguments: dict[str, int],
    period: str,
    inpc: float,
    monthly: float,
    annual: float,
    inegi: InegiClient,
) -> None:
    result = await _call("get_inflation", arguments, inegi)

    content = result.structured_content
    assert content["period"] == period
    assert content["inpc"] == inpc
    assert content["monthly_inflation_percent"] == monthly
    assert content["annual_inflation_percent"] == annual
    assert "910392" in content["source"]["name"]


async def test_year_to_date_inflation_matches_inegi(inegi: InegiClient) -> None:
    result = await _call("get_inflation", {"year": 2026, "month": 8}, inegi)

    assert result.structured_content["year_to_date_inflation_percent"] == 1.69


async def test_first_month_has_no_previous_values(inegi: InegiClient) -> None:
    result = await _call("get_inflation", {"year": 1969, "month": 1}, inegi)

    assert result.structured_content["monthly_inflation_percent"] is None
    assert result.structured_content["annual_inflation_percent"] is None


async def test_month_without_year_is_rejected(inegi: InegiClient) -> None:
    result = await _call("get_inflation", {"month": 5}, inegi)

    assert result.is_error
    assert "both year and month" in str(result.content)


async def test_unpublished_month_names_latest_available(inegi: InegiClient) -> None:
    result = await _call("get_inflation", {"year": 2026, "month": 12}, inegi)

    assert result.is_error
    assert "latest published month is 2026-08" in str(result.content)


async def test_invalid_month_is_rejected(inegi: InegiClient) -> None:
    result = await _call("get_inflation", {"year": 2026, "month": 13}, inegi)

    assert result.is_error


async def test_inflation_range(inegi: InegiClient) -> None:
    result = await _call("get_inflation_range", {"start": "2025-12", "end": "2026-08"}, inegi)

    periods = result.structured_content["periods"]
    assert [p["period"] for p in periods][0::8] == ["2025-12", "2026-08"]
    assert len(periods) == 9


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-08", "2026-01", "must be on or before"),
        ("2000-01", "2026-08", "limited to 240 months"),
    ],
)
async def test_invalid_ranges_are_rejected_without_calling_inegi(
    start: str, end: str, message: str
) -> None:
    client, transport = inegi_client()

    result = await _call("get_inflation_range", {"start": start, "end": end}, client)

    assert result.is_error
    assert message in str(result.content)
    assert transport.requests == []


async def test_malformed_month_is_rejected(inegi: InegiClient) -> None:
    result = await _call("get_inflation_range", {"start": "2026-8", "end": "2026-09"}, inegi)

    assert result.is_error


async def test_missing_token_explains_how_to_get_one() -> None:
    client, _ = inegi_client(token=None)

    result = await _call("get_inflation", {}, client)

    assert result.is_error
    assert "INEGI_TOKEN is not set" in str(result.content)
