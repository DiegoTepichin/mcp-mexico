from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

MEXICO_CITY = ZoneInfo("America/Mexico_City")


def mexico_date(moment: datetime) -> date:
    return moment.astimezone(MEXICO_CITY).date()


def today_mx() -> date:
    return mexico_date(datetime.now(UTC))
