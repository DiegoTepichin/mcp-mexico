from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

import httpx

from mcp_mexico.cache import TtlCache
from mcp_mexico.config import BANXICO_TOKEN_VAR, read_token
from mcp_mexico.errors import DataNotAvailableError, MissingTokenError, UpstreamError
from mcp_mexico.models import Observation, Source

BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
TOKEN_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/token"
LATEST_TTL_SECONDS = 60 * 60
HISTORICAL_TTL_SECONDS = 24 * 60 * 60
TIMEOUT_SECONDS = 15.0

InterestRateName = Literal["target", "tiie_28", "tiie_funding", "cetes_28"]


@dataclass(frozen=True)
class BanxicoSeries:
    series_id: str
    indicator: str
    description: str
    unit: str

    @property
    def source(self) -> Source:
        return Source(
            name=f"Banco de México, SIE series {self.series_id}",
            url="https://www.banxico.org.mx/SieAPIRest/service/v1/",
        )


FIX = BanxicoSeries(
    "SF43718",
    "fix",
    "FIX exchange rate determined by Banco de México, used to settle USD obligations in Mexico.",
    "MXN per USD",
)

INTEREST_RATES: dict[InterestRateName, BanxicoSeries] = {
    "target": BanxicoSeries(
        "SF61745", "target", "Banco de México monetary policy target rate.", "percent per year"
    ),
    "tiie_28": BanxicoSeries(
        "SF43783", "tiie_28", "28-day TIIE interbank equilibrium rate.", "percent per year"
    ),
    "tiie_funding": BanxicoSeries(
        "SF331451",
        "tiie_funding",
        "Overnight TIIE funding rate (TIIE de Fondeo), volume-weighted median.",
        "percent per year",
    ),
    "cetes_28": BanxicoSeries(
        "SF43936",
        "cetes_28",
        "28-day CETES yield from the weekly primary auction.",
        "percent per year",
    ),
}

_Payload = dict[str, Any]


class BanxicoClient:
    """Async client for the Banxico SIE time-series API."""

    def __init__(
        self,
        token: str | None,
        http: httpx.AsyncClient,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._token = token
        self._http = http
        self._today = today
        self._cache: TtlCache[str, list[Observation]] = TtlCache()

    @classmethod
    def from_env(cls) -> "BanxicoClient":
        return cls(read_token(BANXICO_TOKEN_VAR), httpx.AsyncClient(timeout=TIMEOUT_SECONDS))

    async def latest(self, series: BanxicoSeries) -> Observation:
        observations = await self._observations(
            f"{series.series_id}/datos/oportuno", LATEST_TTL_SECONDS
        )
        if not observations:
            raise DataNotAvailableError(f"Banxico has no data for {series.indicator}.")
        return observations[-1]

    async def observations(
        self, series: BanxicoSeries, start: date, end: date
    ) -> list[Observation]:
        ttl = HISTORICAL_TTL_SECONDS if end < self._today() else LATEST_TTL_SECONDS
        path = f"{series.series_id}/datos/{start.isoformat()}/{end.isoformat()}"
        return await self._observations(path, ttl)

    async def _observations(self, path: str, ttl_seconds: float) -> list[Observation]:
        cached = self._cache.get(path)
        if cached is not None:
            return cached
        observations = _parse_observations(await self._get(path))
        self._cache.set(path, observations, ttl_seconds)
        return observations

    async def _get(self, path: str) -> _Payload:
        if self._token is None:
            raise MissingTokenError(
                f"{BANXICO_TOKEN_VAR} is not set. Get a free token at {TOKEN_URL} and add it "
                "to the MCP server's environment."
            )
        try:
            response = await self._http.get(
                f"{BASE_URL}/{path}", headers={"Bmx-Token": self._token}
            )
        except httpx.HTTPError as error:
            raise UpstreamError(f"Could not reach the Banxico SIE API: {error!r}") from error
        return _payload_or_raise(response)


def _payload_or_raise(response: httpx.Response) -> _Payload:
    try:
        payload: _Payload = response.json()
    except ValueError:
        payload = {}
    error = payload.get("error")
    if isinstance(error, dict):
        message = " ".join(str(error.get(key, "")) for key in ("mensaje", "detalle")).strip()
        raise UpstreamError(f"Banxico SIE API error (HTTP {response.status_code}): {message}")
    if response.is_error or "bmx" not in payload:
        raise UpstreamError(f"Banxico SIE API returned an unexpected HTTP {response.status_code}.")
    return payload


def _parse_observations(payload: _Payload) -> list[Observation]:
    series = payload["bmx"]["series"][0]
    return [
        Observation(date=_parse_date(point["fecha"]), value=float(point["dato"].replace(",", "")))
        for point in series.get("datos", [])
        if point["dato"] != "N/E"
    ]


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%d/%m/%Y").date()
