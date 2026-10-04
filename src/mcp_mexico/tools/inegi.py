from typing import Annotated

from pydantic import Field

from mcp_mexico.errors import DataNotAvailableError, InvalidRequestError
from mcp_mexico.models import Inflation, InflationPeriod, InflationSeries
from mcp_mexico.sources.inegi import INPC_SOURCE, InegiClient, Month
from mcp_mexico.tools._errors import as_tool_error

MAX_RANGE_MONTHS = 240

YearMonth = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM")]
MonthNumber = Annotated[int, Field(ge=1, le=12)]


class InegiTools:
    """MCP tools backed by the INEGI Indicators API."""

    def __init__(self, client: InegiClient) -> None:
        self._client = client

    async def get_inflation(
        self, year: int | None = None, month: MonthNumber | None = None
    ) -> Inflation:
        """Get Mexican consumer price inflation (INPC, INEGI) for a month.

        Returns the INPC index plus monthly, annual and year-to-date inflation in
        percent. Without `year` and `month`, returns the latest published month.
        Pass both to get a specific month.
        """
        with as_tool_error():
            series = await self._client.inpc()
            target = _requested_month(series, year, month)
            return Inflation(**_period(series, target).model_dump(), source=INPC_SOURCE)

    async def get_inflation_range(self, start: YearMonth, end: YearMonth) -> InflationSeries:
        """Get Mexican consumer price inflation (INPC, INEGI) for each month in a range.

        `start` and `end` are inclusive, as YYYY-MM, at most 240 months apart.
        """
        with as_tool_error():
            first, last = _parse_year_month(start), _parse_year_month(end)
            _validate_range(first, last)
            series = await self._client.inpc()
            months = [m for m in sorted(series) if first <= m <= last]
            if not months:
                raise DataNotAvailableError(f"INEGI has no INPC values between {start} and {end}.")
            return InflationSeries(
                start=start,
                end=end,
                periods=[_period(series, m) for m in months],
                source=INPC_SOURCE,
            )


def _requested_month(series: dict[Month, float], year: int | None, month: int | None) -> Month:
    if year is None and month is None:
        return max(series)
    if year is None or month is None:
        raise InvalidRequestError("Pass both year and month, or neither for the latest month.")
    if (year, month) not in series:
        latest_year, latest_month = max(series)
        raise DataNotAvailableError(
            f"INEGI has no INPC value for {year}-{month:02d}. "
            f"The latest published month is {latest_year}-{latest_month:02d}."
        )
    return year, month


def _period(series: dict[Month, float], month: Month) -> InflationPeriod:
    year, number = month
    previous_month = (year, number - 1) if number > 1 else (year - 1, 12)
    return InflationPeriod(
        period=f"{year}-{number:02d}",
        inpc=series[month],
        monthly_inflation_percent=_change(series, month, previous_month),
        annual_inflation_percent=_change(series, month, (year - 1, number)),
        year_to_date_inflation_percent=_change(series, month, (year - 1, 12)),
    )


def _change(series: dict[Month, float], month: Month, base: Month) -> float | None:
    if base not in series:
        return None
    return round((series[month] / series[base] - 1) * 100, 2)


def _parse_year_month(raw: str) -> Month:
    year, month = raw.split("-")
    return int(year), int(month)


def _validate_range(first: Month, last: Month) -> None:
    if first > last:
        raise InvalidRequestError("start must be on or before end.")
    months = (last[0] - first[0]) * 12 + last[1] - first[1] + 1
    if months > MAX_RANGE_MONTHS:
        raise InvalidRequestError(
            f"The range is limited to {MAX_RANGE_MONTHS} months; split longer periods."
        )
