from datetime import date

import pytest

from mcp_mexico.errors import DataNotAvailableError
from mcp_mexico.fiscal.uma import available_years, uma_for_year, uma_in_force


def test_covers_2020_through_2026() -> None:
    assert available_years() == list(range(2020, 2027))


@pytest.mark.parametrize("year", available_years())
def test_monthly_and_annual_follow_the_legal_formula(year: int) -> None:
    uma = uma_for_year(year)

    assert uma.monthly == pytest.approx(uma.daily * 30.4, abs=0.01)
    assert uma.annual == pytest.approx(uma.monthly * 12, abs=0.01)


@pytest.mark.parametrize("year", available_years())
def test_takes_effect_on_february_first(year: int) -> None:
    assert uma_for_year(year).valid_from == date(year, 2, 1)


def test_known_value_2025() -> None:
    uma = uma_for_year(2025)

    assert (uma.daily, uma.monthly, uma.annual) == (113.14, 3439.46, 41273.52)
    assert uma.valid_until == date(2026, 1, 31)
    assert uma.source.url == "https://www.inegi.org.mx/temas/uma/"


def test_latest_year_has_open_validity() -> None:
    assert uma_for_year(available_years()[-1]).valid_until is None


def test_previous_year_applies_in_january() -> None:
    assert uma_in_force(date(2026, 1, 31)).year == 2025
    assert uma_in_force(date(2026, 2, 1)).year == 2026


def test_unknown_year_raises() -> None:
    with pytest.raises(DataNotAvailableError, match="2019"):
        uma_for_year(2019)


def test_date_before_coverage_raises() -> None:
    with pytest.raises(DataNotAvailableError):
        uma_in_force(date(2020, 1, 31))
