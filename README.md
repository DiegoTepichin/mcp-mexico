# mcp-mexico

MCP server that gives AI agents access to official Mexican public data.

> Work in progress toward v0.1. See [docs/PLAN.md](docs/PLAN.md).

## Tools available today

| Tool | Description | Source |
|---|---|---|
| `get_uma` | UMA (Unidad de Medida y Actualización) daily, monthly and annual values, 2020–2026. | [INEGI](https://www.inegi.org.mx/temas/uma/) |
| `get_fix_rate` | FIX USD/MXN exchange rate, latest or for a date (falls back to the previous business day). | [Banxico SIE](https://www.banxico.org.mx/SieAPIRest/service/v1/) |
| `get_fix_rate_range` | Daily FIX series between two dates (max 366 days). | Banxico SIE |
| `get_interest_rate` | Target rate, 28-day TIIE, overnight TIIE de Fondeo or 28-day CETES; latest or for a date. | Banxico SIE |
| `get_interest_rate_range` | Series of one of those rates between two dates (max 366 days). | Banxico SIE |
| `get_isr_table` | ISR rate tables for individuals, 2020–2026: monthly (LISR Art. 96) and annual (LISR Art. 152). | Anexo 8 of the RMF ([SAT](https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/index.html) / DOF), cited per table |

Banxico tools need a free token from [Banxico SIE](https://www.banxico.org.mx/SieAPIRest/service/v1/token) in the `BANXICO_TOKEN` environment variable. Offline tools (`get_uma`, `get_isr_table`) need no configuration.

## Development

```bash
uv sync
uv run mcp-mexico      # starts the server over stdio
uv run pytest
uv run --env-file .env python scripts/record_fixtures.py   # refresh recorded API responses (needs tokens)
```

## License

MIT
