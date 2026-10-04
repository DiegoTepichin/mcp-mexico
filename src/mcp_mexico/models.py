from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    name: str
    url: str


class VerifiedSource(Source):
    verified_on: date = Field(description="Date the packaged data was checked against the source.")


class Uma(BaseModel):
    year: int
    daily: float
    monthly: float
    annual: float
    valid_from: date
    valid_until: date | None
    source: VerifiedSource


IsrPeriod = Literal["monthly", "annual"]


class IsrBracket(BaseModel):
    lower_limit: float
    upper_limit: float | None = Field(description="None for the last, open-ended bracket.")
    fixed_fee: float
    rate_percent: float = Field(description="Rate applied to the excess over lower_limit.")


class IsrTable(BaseModel):
    year: int
    period: IsrPeriod
    legal_basis: str
    brackets: list[IsrBracket]
    source: VerifiedSource
