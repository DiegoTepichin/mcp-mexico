from datetime import date

import httpx
import pytest

from mcp_mexico.errors import MissingTokenError, UpstreamError
from mcp_mexico.models import Observation
from mcp_mexico.sources.banxico import FIX, INTEREST_RATES
from tests.conftest import FAKE_TOKEN, banxico_client

pytestmark = pytest.mark.anyio

INVALID_TOKEN_BODY = {
    "error": {
        "url": "https://www.banxico.org.mx/SieAPIRest/service/v1/token",
        "mensaje": "Token inválido",
        "detalle": "El token enviado no es válido, favor de verificar.",
    }
}


async def test_latest_fix() -> None:
    client, transport = banxico_client()

    observation = await client.latest(FIX)

    assert observation == Observation(date=date(2026, 10, 2), value=18.1903)
    assert transport.requests[0].headers["Bmx-Token"] == FAKE_TOKEN


async def test_range_returns_business_days_in_order() -> None:
    client, _ = banxico_client()

    observations = await client.observations(FIX, date(2026, 9, 24), date(2026, 10, 2))

    assert [o.date.day for o in observations] == [24, 25, 28, 29, 30, 1, 2]
    assert observations[0].value == 17.6425


async def test_empty_range_returns_no_observations() -> None:
    client, _ = banxico_client()

    assert await client.observations(FIX, date(2026, 10, 3), date(2026, 10, 4)) == []


async def test_repeated_requests_are_served_from_cache() -> None:
    client, transport = banxico_client()

    await client.latest(INTEREST_RATES["target"])
    await client.latest(INTEREST_RATES["target"])

    assert len(transport.requests) == 1


async def test_missing_token_fails_without_calling_the_api() -> None:
    client, transport = banxico_client(token=None)

    with pytest.raises(MissingTokenError, match="BANXICO_TOKEN"):
        await client.latest(FIX)
    assert transport.requests == []


async def test_invalid_token_reports_banxico_message() -> None:
    client, _ = banxico_client(lambda _: httpx.Response(400, json=INVALID_TOKEN_BODY))

    with pytest.raises(UpstreamError, match="Token inválido"):
        await client.latest(FIX)


async def test_server_error_without_json() -> None:
    client, _ = banxico_client(lambda _: httpx.Response(503, text="<html>down</html>"))

    with pytest.raises(UpstreamError, match="HTTP 503"):
        await client.latest(FIX)


async def test_network_failure() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client, _ = banxico_client(fail)

    with pytest.raises(UpstreamError, match="Could not reach"):
        await client.latest(FIX)


async def test_skips_values_marked_not_available() -> None:
    body = {
        "bmx": {
            "series": [
                {
                    "idSerie": "SF43718",
                    "datos": [
                        {"fecha": "01/10/2026", "dato": "N/E"},
                        {"fecha": "02/10/2026", "dato": "1,018.19"},
                    ],
                }
            ]
        }
    }
    client, _ = banxico_client(lambda _: httpx.Response(200, json=body))

    assert await client.latest(FIX) == Observation(date=date(2026, 10, 2), value=1018.19)
