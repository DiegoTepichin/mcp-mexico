from collections.abc import Callable
from typing import Any

import httpx
import pytest
from mcp import Client

from mcp_mexico.server import build_server
from tests.conftest import banxico_client, inegi_client

pytestmark = pytest.mark.anyio


async def _call(tool: str, arguments: dict[str, Any], handler: Any, token: str = "t") -> Any:
    banxico, _ = banxico_client(handler, token)
    inegi, _ = inegi_client(handler, token)
    async with Client(build_server(banxico, inegi)) as client:
        return await client.call_tool(tool, arguments)


def _answer(body: object) -> Callable[[httpx.Request], httpx.Response]:
    return lambda _: httpx.Response(200, json=body)


def _banxico(value: str) -> dict[str, Any]:
    return {"bmx": {"series": [{"datos": [{"fecha": "02/01/2026", "dato": value}]}]}}


def _inegi(*values: str) -> dict[str, Any]:
    observations = [
        {"TIME_PERIOD": f"2026/{month:02d}", "OBS_VALUE": value}
        for month, value in enumerate(values, start=1)
    ]
    return {"Series": [{"OBSERVATIONS": observations}]}


@pytest.mark.parametrize("value", ["NaN", "inf", "-Infinity"])
async def test_non_finite_banxico_values_are_an_error(value: str) -> None:
    result = await _call("get_fix_rate", {}, _answer(_banxico(value)))

    assert result.is_error
    assert "unexpected response format" in str(result.content)


@pytest.mark.parametrize(
    "body", [_inegi("NaN"), _inegi("inf"), _inegi("0", "5"), _inegi("-1"), _inegi()]
)
async def test_unusable_inegi_series_are_an_error(body: dict[str, Any]) -> None:
    result = await _call("get_inflation", {}, _answer(body))

    assert result.is_error
    assert "unexpected response format" in str(result.content)


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("get_fix_rate", {"date": "0001-01-01"}),
        ("get_interest_rate", {"rate": "target", "date": "0001-01-05"}),
    ],
)
async def test_dates_at_the_calendar_limit_are_an_error(
    tool: str, arguments: dict[str, Any]
) -> None:
    result = await _call(tool, arguments, _answer(_banxico("1")))

    assert result.is_error
    assert "No Banxico series goes back to" in str(result.content)


@pytest.mark.parametrize("token", ["abc\ndef-secret", "sécret", "abc def", "abc/../def?x=1"])
@pytest.mark.parametrize(
    ("tool", "variable"), [("get_fix_rate", "BANXICO_TOKEN"), ("get_inflation", "INEGI_TOKEN")]
)
async def test_malformed_tokens_are_named_and_never_sent(
    tool: str, variable: str, token: str
) -> None:
    def refuse(_: httpx.Request) -> httpx.Response:
        raise AssertionError("a malformed token must not reach the network")

    result = await _call(tool, {}, refuse, token)

    assert result.is_error
    assert f"{variable} is not a valid token" in str(result.content)
    assert token not in str(result.content)
