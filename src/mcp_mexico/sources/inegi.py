from typing import Any

import httpx

from mcp_mexico.cache import TtlCache
from mcp_mexico.config import INEGI_TOKEN_VAR, read_token, require_token
from mcp_mexico.errors import UpstreamError
from mcp_mexico.models import Source
from mcp_mexico.sources.http import get_with_retry
from mcp_mexico.sources.numbers import parse_finite

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
UNEXPECTED_FORMAT_MESSAGE = "INEGI API returned an unexpected response format."

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
        token = require_token(self._token, INEGI_TOKEN_VAR, TOKEN_URL)
        try:
            response = await get_with_retry(
                self._http, f"{BASE_URL}/{path}/{token}", params={"type": "json"}
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
    if response.status_code == 429:
        raise UpstreamError("INEGI API rate limit reached. Wait a minute and try again.")
    if response.is_error or not isinstance(payload, dict) or "Series" not in payload:
        raise UpstreamError(f"INEGI API returned an unexpected HTTP {response.status_code}.")
    return payload


def _parse_monthly_series(payload: _Payload) -> dict[Month, float]:
    try:
        observations = payload["Series"][0]["OBSERVATIONS"]
        series = {
            _parse_month(point["TIME_PERIOD"]): parse_finite(point["OBS_VALUE"])
            for point in observations
            if point["OBS_VALUE"]
        }
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise UpstreamError(UNEXPECTED_FORMAT_MESSAGE) from error
    if not series or min(series.values()) <= 0:
        raise UpstreamError(UNEXPECTED_FORMAT_MESSAGE)
    return series


def _parse_month(raw: str) -> Month:
    year, month = raw.split("/")
    return int(year), int(month)
