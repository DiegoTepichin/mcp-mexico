from datetime import date, timedelta
from functools import cache
from importlib.resources import files

from pydantic import BaseModel

from mcp_mexico.errors import DataNotAvailableError
from mcp_mexico.models import Source, Uma


class _UmaRecord(BaseModel):
    year: int
    daily: float
    monthly: float
    annual: float
    valid_from: date


class _UmaFile(BaseModel):
    source: Source
    values: list[_UmaRecord]


@cache
def _load() -> _UmaFile:
    raw = files("mcp_mexico.fiscal.data").joinpath("uma.json").read_text(encoding="utf-8")
    table = _UmaFile.model_validate_json(raw)
    table.values.sort(key=lambda record: record.year)
    return table


def available_years() -> list[int]:
    return [record.year for record in _load().values]


def uma_for_year(year: int) -> Uma:
    table = _load()
    for index, record in enumerate(table.values):
        if record.year == year:
            successor = table.values[index + 1] if index + 1 < len(table.values) else None
            return _to_uma(record, successor, table.source)
    years = available_years()
    raise DataNotAvailableError(f"No UMA data for {year}. Available years: {years[0]}-{years[-1]}.")


def uma_in_force(on: date) -> Uma:
    in_force = [record for record in _load().values if record.valid_from <= on]
    if not in_force:
        raise DataNotAvailableError(f"No UMA data in force on {on.isoformat()}.")
    return uma_for_year(in_force[-1].year)


def _to_uma(record: _UmaRecord, successor: _UmaRecord | None, source: Source) -> Uma:
    valid_until = successor.valid_from - timedelta(days=1) if successor else None
    return Uma(
        year=record.year,
        daily=record.daily,
        monthly=record.monthly,
        annual=record.annual,
        valid_from=record.valid_from,
        valid_until=valid_until,
        source=source,
    )
