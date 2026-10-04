import httpx
import pytest

from mcp_mexico.errors import MissingTokenError, UpstreamError
from tests.conftest import inegi_client

pytestmark = pytest.mark.anyio


async def test_inpc_full_series() -> None:
    client, transport = inegi_client()

    series = await client.inpc()

    assert series[(2026, 8)] == 145.462
    assert series[(2024, 12)] == 137.949
    assert min(series) == (1969, 1)
    assert transport.requests[0].url.params["type"] == "json"


async def test_series_is_cached() -> None:
    client, transport = inegi_client()

    await client.inpc()
    await client.inpc()

    assert len(transport.requests) == 1


async def test_missing_token_fails_without_calling_the_api() -> None:
    client, transport = inegi_client(token=None)

    with pytest.raises(MissingTokenError, match="INEGI_TOKEN"):
        await client.inpc()
    assert transport.requests == []


async def test_error_list_mentions_possible_token_problem() -> None:
    client, _ = inegi_client(token="wrong-token")

    with pytest.raises(UpstreamError, match=r"ErrorCode:100.*INEGI_TOKEN is invalid"):
        await client.inpc()


async def test_network_failure_does_not_leak_the_url() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed {request.url}", request=request)

    client, _ = inegi_client(fail, token="secret-token")

    with pytest.raises(UpstreamError) as raised:
        await client.inpc()
    assert "secret-token" not in str(raised.value)
