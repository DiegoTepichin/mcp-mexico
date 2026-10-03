from functools import cache

from pydantic import BaseModel

from mcp_mexico.errors import DataNotAvailableError
from mcp_mexico.fiscal.data import read_data_file
from mcp_mexico.models import IsrBracket, IsrPeriod, IsrTable, Source

_LEGAL_BASIS: dict[IsrPeriod, str] = {
    "monthly": "Ley del ISR, artículo 96 (pagos provisionales mensuales)",
    "annual": "Ley del ISR, artículo 152 (cálculo del impuesto anual)",
}


class _IsrRecord(BaseModel):
    year: int
    period: IsrPeriod
    source: Source
    brackets: list[IsrBracket]


class _IsrFile(BaseModel):
    tables: list[_IsrRecord]


@cache
def _load() -> dict[tuple[int, IsrPeriod], _IsrRecord]:
    data = _IsrFile.model_validate_json(read_data_file("isr.json"))
    return {(record.year, record.period): record for record in data.tables}


def available_years() -> list[int]:
    return sorted({year for year, _ in _load()})


def isr_table(year: int, period: IsrPeriod) -> IsrTable:
    record = _load().get((year, period))
    if record is None:
        years = available_years()
        raise DataNotAvailableError(
            f"No {period} ISR table for {year}. Available years: {years[0]}-{years[-1]}."
        )
    return IsrTable(
        year=record.year,
        period=record.period,
        legal_basis=_LEGAL_BASIS[record.period],
        brackets=record.brackets,
        source=record.source,
    )
