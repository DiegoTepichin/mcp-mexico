from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from mcp_mexico.sources.banxico import BASE_URL as BANXICO_BASE_URL
from mcp_mexico.sources.banxico import BanxicoClient
from mcp_mexico.sources.inegi import BASE_URL as INEGI_BASE_URL
from mcp_mexico.sources.inegi import InegiClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FAKE_TOKEN = "test-token"

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class RecordingTransport(httpx.MockTransport):
    def __init__(self, handler: Handler) -> None:
        self.requests: list[httpx.Request] = []

        def record(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        super().__init__(record)


def serve_banxico_fixtures(request: httpx.Request) -> httpx.Response:
    path = str(request.url).removeprefix(BANXICO_BASE_URL + "/")
    fixture = FIXTURES_DIR / "banxico" / (path.replace("/", "_") + ".json")
    if not fixture.exists():
        return httpx.Response(404, json={"missing_fixture": fixture.name})
    return httpx.Response(200, content=fixture.read_bytes())


def serve_inegi_fixtures(request: httpx.Request) -> httpx.Response:
    path = request.url.path.removeprefix(httpx.URL(INEGI_BASE_URL).path + "/")
    path_without_token = path.rsplit("/", 1)[0]
    if path.rsplit("/", 1)[1] != FAKE_TOKEN:
        return httpx.Response(400, json=["ErrorInfo:No se encontraron resultados", "ErrorCode:100"])
    fixture = FIXTURES_DIR / "inegi" / (path_without_token.replace("/", "_") + ".json")
    return httpx.Response(200, content=fixture.read_bytes())


def banxico_client(
    handler: Handler = serve_banxico_fixtures, token: str | None = FAKE_TOKEN
) -> tuple[BanxicoClient, RecordingTransport]:
    transport = RecordingTransport(handler)
    return BanxicoClient(token, httpx.AsyncClient(transport=transport)), transport


@pytest.fixture
def banxico() -> BanxicoClient:
    client, _ = banxico_client()
    return client


def inegi_client(
    handler: Handler = serve_inegi_fixtures, token: str | None = FAKE_TOKEN
) -> tuple[InegiClient, RecordingTransport]:
    transport = RecordingTransport(handler)
    return InegiClient(token, httpx.AsyncClient(transport=transport)), transport


@pytest.fixture
def inegi() -> InegiClient:
    client, _ = inegi_client()
    return client
