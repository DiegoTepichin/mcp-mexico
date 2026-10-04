import logging

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from mcp_mexico.sources.banxico import BanxicoClient
from mcp_mexico.sources.inegi import InegiClient
from mcp_mexico.tools.banxico import BanxicoTools
from mcp_mexico.tools.fiscal import get_isr_table, get_uma
from mcp_mexico.tools.inegi import InegiTools

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)
_OFFLINE = _READ_ONLY.model_copy(update={"open_world_hint": False})
_ONLINE = _READ_ONLY.model_copy(update={"open_world_hint": True})


def build_server(
    banxico: BanxicoClient | None = None, inegi: InegiClient | None = None
) -> MCPServer:
    server = MCPServer(
        name="mcp-mexico",
        instructions=(
            "Official Mexican public data. Every result includes its official source; "
            "cite it when you use a figure."
        ),
    )
    server.add_tool(get_uma, title="UMA (Unidad de Medida y Actualización)", annotations=_OFFLINE)
    server.add_tool(get_isr_table, title="ISR rate table (personas físicas)", annotations=_OFFLINE)
    _add_banxico_tools(server, BanxicoTools(banxico or BanxicoClient.from_env()))
    _add_inegi_tools(server, InegiTools(inegi or InegiClient.from_env()))
    return server


def _add_banxico_tools(server: MCPServer, tools: BanxicoTools) -> None:
    server.add_tool(tools.get_fix_rate, title="FIX exchange rate", annotations=_ONLINE)
    server.add_tool(tools.get_fix_rate_range, title="FIX exchange rate series", annotations=_ONLINE)
    server.add_tool(tools.get_interest_rate, title="Interest rate", annotations=_ONLINE)
    server.add_tool(
        tools.get_interest_rate_range, title="Interest rate series", annotations=_ONLINE
    )


def _add_inegi_tools(server: MCPServer, tools: InegiTools) -> None:
    server.add_tool(tools.get_inflation, title="Inflation (INPC)", annotations=_ONLINE)
    server.add_tool(tools.get_inflation_range, title="Inflation series (INPC)", annotations=_ONLINE)


def main() -> None:
    # httpx logs every request URL at INFO, and INEGI requires the token in the URL.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    build_server().run()
