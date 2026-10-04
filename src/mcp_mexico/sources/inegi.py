from typing import Any

import httpx

from mcp_mexico.cache import TtlCache
from mcp_mexico.config import INEGI_TOKEN_VAR, read_token
from mcp_mexico.errors import MissingTokenError, UpstreamError
from mcp_mexico.models import Source

BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"
TOKEN_URL = "https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify"
INPC_INDICATOR = "910392"
INPC_PATH = f"INDICATOR/{INPC_INDICATOR}/es/00/false/BIE-BISE/2.0"
INPC_SOURCE = Source(
    name=f"INEGI, Índice Nacional de Precios al Consumidor (INPC), indicator {INPC_INDICATOR}",
    url="https://www.inegi.org.mx/temas/inpc/",
)
CACHE_TTL_SECONDS = 6 * 60 * 60
TIMEOUT_SECONDS = 20.0

Month = tuple[int, int]
_Payload = dict[str, Any]


class InegiClient:
    """Async client for the INEGI Indicators API."""

    def __init__(self, token: str | None, http: httpx.AsyncClient) -> None:
        self._token = token
        self._http = http
        self._cache: TtlCache[str, dict[Month, float]] = TtlCache()

    @classmethod
    def from_env(cls) -> "InegiClient":
        return cls(read_token(INEGI_TOKEN_VAR), httpx.AsyncClient(timeout=TIMEOUT_SECONDS))

    async def inpc(self) -> dict[Month, float]:
        """Return the full monthly INPC series keyed by (year, month)."""
        cached = self._cache.get(INPC_PATH)
        if cached is not None:
            return cached
        series = _parse_monthly_series(await self._get(INPC_PATH))
        self._cache.set(INPC_PATH, series, CACHE_TTL_SECONDS)
        return series

    async def _get(self, path: str) -> _Payload:
        if self._token is None:
            raise MissingTokenError(
                f"{INEGI_TOKEN_VAR} is not set. Get a free token at {TOKEN_URL} and add it "
                "to the MCP server's environment."
            )
        try:
            response = await self._http.get(
                f"{BASE_URL}/{path}/{self._token}", params={"type": "json"}
            )
        except httpx.HTTPError as error:
            # The token is part of the URL, so the exception text is not echoed back.
            raise UpstreamError(
                f"Could not reach the INEGI API ({type(error).__name__})."
            ) from error
        return _payload_or_raise(response)


def _payload_or_raise(response: httpx.Response) -> _Payload:
    try:
        payload: object = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, list):
        details = "; ".join(str(item) for item in payload)
        raise UpstreamError(
            f"INEGI API error (HTTP {response.status_code}): {details}. INEGI also answers "
            f"this way when {INEGI_TOKEN_VAR} is invalid or not yet activated."
        )
    if response.is_error or not isinstance(payload, dict) or "Series" not in payload:
        raise UpstreamError(f"INEGI API returned an unexpected HTTP {response.status_code}.")
    return payload


def _parse_monthly_series(payload: _Payload) -> dict[Month, float]:
    observations = payload["Series"][0]["OBSERVATIONS"]
    return {
        _parse_month(point["TIME_PERIOD"]): float(point["OBS_VALUE"])
        for point in observations
        if point["OBS_VALUE"]
    }


def _parse_month(raw: str) -> Month:
    year, month = raw.split("/")
    return int(year), int(month)
