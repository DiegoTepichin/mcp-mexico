from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from mcp_mexico.tools.fiscal import get_isr_table, get_uma

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)
_OFFLINE = _READ_ONLY.model_copy(update={"open_world_hint": False})


def build_server() -> MCPServer:
    server = MCPServer(
        name="mcp-mexico",
        instructions=(
            "Official Mexican public data. Every result includes its official source; "
            "cite it when you use a figure."
        ),
    )
    server.add_tool(get_uma, title="UMA (Unidad de Medida y Actualización)", annotations=_OFFLINE)
    server.add_tool(get_isr_table, title="ISR rate table (personas físicas)", annotations=_OFFLINE)
    return server


def main() -> None:
    build_server().run()
