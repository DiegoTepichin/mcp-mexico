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


class Observation(BaseModel):
    date: date
    value: float


class IndicatorValue(BaseModel):
    indicator: str
    description: str
    unit: str
    date: date
    value: float
    source: Source


class IndicatorSeries(BaseModel):
    indicator: str
    description: str
    unit: str
    start: date
    end: date
    observations: list[Observation]
    source: Source


class InflationPeriod(BaseModel):
    period: str = Field(description="Month as YYYY-MM.")
    inpc: float = Field(description="INPC general index, 2nd fortnight of July 2018 = 100.")
    monthly_inflation_percent: float | None = Field(
        description="Change vs the previous month. None when that month is not available."
    )
    annual_inflation_percent: float | None = Field(
        description="Change vs the same month of the previous year. None when not available."
    )
    year_to_date_inflation_percent: float | None = Field(
        description="Change vs December of the previous year. None when not available."
    )


class Inflation(InflationPeriod):
    source: Source


class InflationSeries(BaseModel):
    start: str
    end: str
    periods: list[InflationPeriod]
    source: Source
