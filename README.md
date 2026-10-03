# mcp-mexico

MCP server that gives AI agents access to official Mexican public data.

> Work in progress toward v0.1. See [docs/PLAN.md](docs/PLAN.md).

## Tools available today

| Tool | Description | Source |
|---|---|---|
| `get_uma` | UMA (Unidad de Medida y Actualización) daily, monthly and annual values, 2020–2026. | [INEGI](https://www.inegi.org.mx/temas/uma/) |

## Development

```bash
uv sync
uv run mcp-mexico      # starts the server over stdio
uv run pytest
```

## License

MIT
