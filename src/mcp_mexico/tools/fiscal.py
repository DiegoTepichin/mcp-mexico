from datetime import date

from mcp_mexico.fiscal.isr import isr_table
from mcp_mexico.fiscal.uma import uma_for_year, uma_in_force
from mcp_mexico.models import IsrPeriod, IsrTable, Uma
from mcp_mexico.tools._errors import as_tool_error


def get_uma(year: int | None = None) -> Uma:
    """Get the official UMA (Unidad de Medida y Actualización) in Mexican pesos.

    Returns the daily, monthly and annual values, the validity period and the
    official source. Without `year`, returns the UMA in force today. Each year's
    UMA takes effect on February 1, so in January the previous year's value applies.
    """
    with as_tool_error():
        return uma_in_force(date.today()) if year is None else uma_for_year(year)


def get_isr_table(year: int | None = None, period: IsrPeriod = "monthly") -> IsrTable:
    """Get the official ISR rate table for individuals (personas físicas) in Mexican pesos.

    `monthly` is the Art. 96 table used for monthly withholdings and provisional
    payments on wages; `annual` is the Art. 152 table used for the annual tax return.
    Without `year`, returns the current year's table. To compute the tax, find the
    bracket containing the taxable income, then: fixed_fee + (income - lower_limit)
    * rate_percent / 100.
    """
    with as_tool_error():
        return isr_table(date.today().year if year is None else year, period)
