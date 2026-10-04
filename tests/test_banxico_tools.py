from typing import Any

import pytest
from mcp import Client

from mcp_mexico.server import build_server
from mcp_mexico.sources.banxico import BanxicoClient
from tests.conftest import banxico_client

pytestmark = pytest.mark.anyio


async def _call(tool: str, arguments: dict[str, Any], banxico: BanxicoClient) -> Any:
    async with Client(build_server(banxico)) as client:
        return await client.call_tool(tool, arguments)


async def test_latest_fix_rate(banxico: BanxicoClient) -> None:
    result = await _call("get_fix_rate", {}, banxico)

    assert result.structured_content["date"] == "2026-10-02"
    assert result.structured_content["value"] == 18.1903
    assert result.structured_content["unit"] == "MXN per USD"
    assert "SF43718" in result.structured_content["source"]["name"]


async def test_fix_rate_on_sunday_returns_previous_business_day(banxico: BanxicoClient) -> None:
    result = await _call("get_fix_rate", {"date": "2026-09-27"}, banxico)

    assert result.structured_content["date"] == "2026-09-25"
    assert result.structured_content["value"] == 17.71


async def test_fix_rate_range(banxico: BanxicoClient) -> None:
    result = await _call(
        "get_fix_rate_range", {"start": "2026-09-24", "end": "2026-10-02"}, banxico
    )

    assert len(result.structured_content["observations"]) == 7


async def test_fix_rate_range_without_business_days_is_an_error(banxico: BanxicoClient) -> None:
    result = await _call(
        "get_fix_rate_range", {"start": "2026-10-03", "end": "2026-10-04"}, banxico
    )

    assert result.is_error
    assert "no fix values" in str(result.content)


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-10-02", "2026-09-24", "must be on or before"),
        ("2024-01-01", "2026-01-01", "limited to 366 days"),
    ],
)
async def test_invalid_ranges_are_rejected_without_calling_banxico(
    start: str, end: str, message: str
) -> None:
    client, transport = banxico_client()

    result = await _call("get_fix_rate_range", {"start": start, "end": end}, client)

    assert result.is_error
    assert message in str(result.content)
    assert transport.requests == []


@pytest.mark.parametrize(
    ("rate", "date", "value"),
    [
        ("target", "2026-10-04", 6.5),
        ("tiie_28", "2026-10-05", 6.7559),
        ("tiie_funding", "2026-10-02", 6.48),
        ("cetes_28", "2026-10-01", 6.01),
    ],
)
async def test_latest_interest_rates(
    rate: str, date: str, value: float, banxico: BanxicoClient
) -> None:
    result = await _call("get_interest_rate", {"rate": rate}, banxico)

    assert result.structured_content["indicator"] == rate
    assert result.structured_content["date"] == date
    assert result.structured_content["value"] == value
    assert result.structured_content["unit"] == "percent per year"


async def test_weekly_cetes_series(banxico: BanxicoClient) -> None:
    result = await _call(
        "get_interest_rate_range",
        {"rate": "cetes_28", "start": "2026-07-01", "end": "2026-09-30"},
        banxico,
    )

    assert len(result.structured_content["observations"]) == 13


async def test_unknown_rate_is_rejected(banxico: BanxicoClient) -> None:
    result = await _call("get_interest_rate", {"rate": "libor"}, banxico)

    assert result.is_error


async def test_missing_token_explains_how_to_get_one() -> None:
    client, _ = banxico_client(token=None)

    result = await _call("get_fix_rate", {}, client)

    assert result.is_error
    assert "BANXICO_TOKEN is not set" in str(result.content)
    assert "SieAPIRest/service/v1/token" in str(result.content)
