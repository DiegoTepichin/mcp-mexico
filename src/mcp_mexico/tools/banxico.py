from datetime import date, timedelta

from mcp_mexico.errors import DataNotAvailableError, InvalidRequestError
from mcp_mexico.models import IndicatorSeries, IndicatorValue, Observation
from mcp_mexico.sources.banxico import (
    FIX,
    INTEREST_RATES,
    BanxicoClient,
    BanxicoSeries,
    InterestRateName,
)
from mcp_mexico.tools._errors import as_tool_error

MAX_RANGE_DAYS = 366
LOOKBACK_DAYS = 10


class BanxicoTools:
    """MCP tools backed by the Banxico SIE API."""

    def __init__(self, client: BanxicoClient) -> None:
        self._client = client

    async def get_fix_rate(self, date: date | None = None) -> IndicatorValue:
        """Get the FIX USD/MXN exchange rate published by Banco de México.

        Without `date`, returns the latest FIX. With `date`, returns the FIX for that
        day; on weekends and holidays there is no FIX, so it returns the most recent
        one before that day. Check the `date` field of the result.
        """
        with as_tool_error():
            return await self._value_on_or_before(FIX, date)

    async def get_fix_rate_range(self, start: date, end: date) -> IndicatorSeries:
        """Get the daily FIX USD/MXN exchange rate between two dates (inclusive, max 366 days).

        Only business days have a value.
        """
        with as_tool_error():
            return await self._series(FIX, start, end)

    async def get_interest_rate(
        self, rate: InterestRateName, date: date | None = None
    ) -> IndicatorValue:
        """Get a key Mexican interest rate from Banco de México, in percent per year.

        Rates: `target` (Banxico policy rate), `tiie_28` (28-day TIIE), `tiie_funding`
        (overnight TIIE de Fondeo) and `cetes_28` (28-day CETES, weekly auction).
        Without `date`, returns the latest value. With `date`, returns the value for
        that day or the most recent one before it. Check the `date` field of the result.
        """
        with as_tool_error():
            return await self._value_on_or_before(INTEREST_RATES[rate], date)

    async def get_interest_rate_range(
        self, rate: InterestRateName, start: date, end: date
    ) -> IndicatorSeries:
        """Get a key Mexican interest rate between two dates (inclusive, max 366 days).

        Rates: `target`, `tiie_28`, `tiie_funding` and `cetes_28` (weekly). Values are
        in percent per year.
        """
        with as_tool_error():
            return await self._series(INTEREST_RATES[rate], start, end)

    async def _value_on_or_before(self, series: BanxicoSeries, day: date | None) -> IndicatorValue:
        observation = await self._observation_on_or_before(series, day)
        return IndicatorValue(
            indicator=series.indicator,
            description=series.description,
            unit=series.unit,
            date=observation.date,
            value=observation.value,
            source=series.source,
        )

    async def _observation_on_or_before(
        self, series: BanxicoSeries, day: date | None
    ) -> Observation:
        if day is None:
            return await self._client.latest(series)
        observations = await self._client.observations(
            series, day - timedelta(days=LOOKBACK_DAYS), day
        )
        if not observations:
            raise DataNotAvailableError(
                f"Banxico has no {series.indicator} value on or in the "
                f"{LOOKBACK_DAYS} days before {day.isoformat()}."
            )
        return observations[-1]

    async def _series(self, series: BanxicoSeries, start: date, end: date) -> IndicatorSeries:
        _validate_range(start, end)
        observations = await self._client.observations(series, start, end)
        if not observations:
            raise DataNotAvailableError(
                f"Banxico has no {series.indicator} values between "
                f"{start.isoformat()} and {end.isoformat()}."
            )
        return IndicatorSeries(
            indicator=series.indicator,
            description=series.description,
            unit=series.unit,
            start=start,
            end=end,
            observations=observations,
            source=series.source,
        )


def _validate_range(start: date, end: date) -> None:
    if start > end:
        raise InvalidRequestError(f"start ({start}) must be on or before end ({end}).")
    if (end - start).days > MAX_RANGE_DAYS:
        raise InvalidRequestError(
            f"The range is limited to {MAX_RANGE_DAYS} days; split longer periods."
        )
