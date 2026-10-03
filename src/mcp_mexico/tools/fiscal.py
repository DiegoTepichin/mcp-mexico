from datetime import date

from mcp.server.mcpserver.exceptions import ToolError

from mcp_mexico.errors import DataNotAvailableError
from mcp_mexico.fiscal.uma import uma_for_year, uma_in_force
from mcp_mexico.models import Uma


def get_uma(year: int | None = None) -> Uma:
    """Get the official UMA (Unidad de Medida y Actualización) in Mexican pesos.

    Returns the daily, monthly and annual values, the validity period and the
    official source. Without `year`, returns the UMA in force today. Each year's
    UMA takes effect on February 1, so in January the previous year's value applies.
    """
    try:
        return uma_in_force(date.today()) if year is None else uma_for_year(year)
    except DataNotAvailableError as error:
        raise ToolError(str(error)) from error
