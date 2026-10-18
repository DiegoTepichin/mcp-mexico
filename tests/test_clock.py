from datetime import UTC, date, datetime

import pytest

from mcp_mexico.clock import mexico_date, today_mx


@pytest.mark.parametrize(
    ("utc_moment", "expected"),
    [
        (datetime(2026, 10, 18, 5, 59, tzinfo=UTC), date(2026, 10, 17)),
        (datetime(2026, 10, 18, 6, 0, tzinfo=UTC), date(2026, 10, 18)),
        (datetime(2027, 1, 1, 3, 0, tzinfo=UTC), date(2026, 12, 31)),
        (datetime(2027, 2, 1, 5, 59, tzinfo=UTC), date(2027, 1, 31)),
    ],
)
def test_mexico_date_uses_mexico_city_offset(utc_moment: datetime, expected: date) -> None:
    assert mexico_date(utc_moment) == expected


def test_today_mx_returns_a_date() -> None:
    assert isinstance(today_mx(), date)
