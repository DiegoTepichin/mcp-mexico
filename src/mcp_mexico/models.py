from datetime import date

from pydantic import BaseModel


class Source(BaseModel):
    name: str
    url: str
    verified_on: date


class Uma(BaseModel):
    year: int
    daily: float
    monthly: float
    annual: float
    valid_from: date
    valid_until: date | None
    source: Source
