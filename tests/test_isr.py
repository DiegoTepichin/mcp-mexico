from itertools import pairwise

import pytest

from mcp_mexico.errors import DataNotAvailableError
from mcp_mexico.fiscal.isr import available_years, isr_table
from mcp_mexico.models import IsrPeriod, IsrTable

PERIODS: tuple[IsrPeriod, ...] = ("monthly", "annual")
ALL_TABLES = [isr_table(year, period) for year in available_years() for period in PERIODS]


def _id(table: IsrTable) -> str:
    return f"{table.year}-{table.period}"


def test_covers_2020_through_2026() -> None:
    assert available_years() == list(range(2020, 2027))


@pytest.mark.parametrize("table", ALL_TABLES, ids=_id)
def test_brackets_are_contiguous_and_open_ended(table: IsrTable) -> None:
    brackets = table.brackets

    assert brackets[0].lower_limit == 0.01
    assert brackets[-1].upper_limit is None
    for current, following in pairwise(brackets):
        assert current.upper_limit is not None
        assert following.lower_limit == pytest.approx(current.upper_limit + 0.01)


@pytest.mark.parametrize("table", ALL_TABLES, ids=_id)
def test_rates_go_from_1_92_to_35_percent(table: IsrTable) -> None:
    rates = [bracket.rate_percent for bracket in table.brackets]

    assert rates == sorted(set(rates))
    assert (rates[0], rates[-1]) == (1.92, 35.0)


@pytest.mark.parametrize("table", ALL_TABLES, ids=_id)
def test_fixed_fee_equals_tax_accumulated_by_previous_brackets(table: IsrTable) -> None:
    for current, following in pairwise(table.brackets):
        assert current.upper_limit is not None
        accumulated = current.fixed_fee + (
            (current.upper_limit - current.lower_limit) * current.rate_percent / 100
        )
        assert following.fixed_fee == pytest.approx(accumulated, abs=0.02)


@pytest.mark.parametrize("table", ALL_TABLES, ids=_id)
def test_every_table_cites_an_official_source(table: IsrTable) -> None:
    assert table.source.url.startswith(
        ("https://www.sat.gob.mx/", "https://www.dof.gob.mx/", "https://dof.gob.mx/")
    )
    assert "Anexo 8" in table.source.name


def test_monthly_2026_matches_anexo_8() -> None:
    table = isr_table(2026, "monthly")

    assert len(table.brackets) == 11
    assert table.brackets[4].upper_limit == 17533.64
    assert table.brackets[-1].lower_limit == 425642.00
    assert table.brackets[-1].fixed_fee == 133488.54
    assert table.legal_basis.startswith("Ley del ISR, artículo 96")


def test_monthly_2020_predates_2021_update() -> None:
    assert isr_table(2020, "monthly").brackets[0].upper_limit == 578.52
    assert isr_table(2021, "monthly").brackets[0].upper_limit == 644.58


def test_unknown_year_raises() -> None:
    with pytest.raises(DataNotAvailableError, match="Available years: 2020-2026"):
        isr_table(2019, "monthly")
