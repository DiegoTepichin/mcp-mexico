# mcp-mexico

MCP server that gives AI agents official Mexican public data: Banxico exchange and interest rates, INEGI inflation, UMA values and ISR tax tables.

[![CI](https://github.com/DiegoTepichin/mcp-mexico/actions/workflows/ci.yml/badge.svg)](https://github.com/DiegoTepichin/mcp-mexico/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Leer en español](README.es.md)

![Claude Code answering questions about the FIX exchange rate, inflation and ISR with mcp-mexico](https://raw.githubusercontent.com/DiegoTepichin/mcp-mexico/main/docs/demo.gif)

*Claude Code using `mcp-mexico`. Response wait times are cut from the recording.*

## Why

AI assistants either make up Mexican economic figures or use stale ones, so you end up looking them up by hand at Banxico, INEGI or the SAT and pasting them in. `mcp-mexico` lets any [MCP](https://modelcontextprotocol.io) client (Claude Desktop, Claude Code, Cursor) fetch them directly. Every result names its official source and the date it applies to.

## Tools

| Tool | What it returns | Source | Token |
|---|---|---|---|
| `get_fix_rate` | FIX USD/MXN exchange rate, latest or for a date. On weekends and holidays it returns the previous business day. | Banxico SIE | `BANXICO_TOKEN` |
| `get_fix_rate_range` | Daily FIX between two dates (max 366 days). | Banxico SIE | `BANXICO_TOKEN` |
| `get_interest_rate` | Banxico target rate, 28-day TIIE, overnight TIIE de Fondeo or 28-day CETES; latest or for a date. | Banxico SIE | `BANXICO_TOKEN` |
| `get_interest_rate_range` | One of those rates between two dates (max 366 days). | Banxico SIE | `BANXICO_TOKEN` |
| `get_inflation` | INPC index and monthly, annual and year-to-date inflation for a month (latest by default). | INEGI | `INEGI_TOKEN` |
| `get_inflation_range` | The same for each month in a range (max 240 months). | INEGI | `INEGI_TOKEN` |
| `get_uma` | UMA daily, monthly and annual values, 2020–2026, with validity dates. | INEGI | none |
| `get_isr_table` | ISR tables for individuals, 2020–2026: monthly (LISR Art. 96) and annual (LISR Art. 152). | Anexo 8 of the RMF (SAT / DOF) | none |

`get_uma` and `get_isr_table` work offline with no configuration. Their data ships inside the package; each table cites the document it was taken from and the date it was verified.

## Get your tokens

Both are free and take a couple of minutes.

1. **Banxico**: open the [SIE API token page](https://www.banxico.org.mx/SieAPIRest/service/v1/token), solve the captcha and click "Generar token". The 64-character token appears on the page.
2. **INEGI**: enter your email in the [INEGI token form](https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify). The token arrives by email.

You can start with only one token, or none: tools whose token is missing return a message explaining how to get it.

## Install

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). The server runs with `uvx mcp-mexico`; you don't start it yourself, your MCP client does.

### Claude Code

```bash
claude mcp add mcp-mexico -e BANXICO_TOKEN=your-token -e INEGI_TOKEN=your-token -- uvx mcp-mexico
```

### Claude Desktop

Add this to `claude_desktop_config.json` (Settings → Developer → Edit Config) and restart Claude Desktop:

```json
{
  "mcpServers": {
    "mcp-mexico": {
      "command": "uvx",
      "args": ["mcp-mexico"],
      "env": {
        "BANXICO_TOKEN": "your-token",
        "INEGI_TOKEN": "your-token"
      }
    }
  }
}
```

### Cursor

Add the same `mcpServers` block to `~/.cursor/mcp.json`.

## Try it

Ask your assistant:

- "What is today's FIX exchange rate?"
- "What was annual inflation in Mexico in December 2024?"
- "How much is 30 UMAs in pesos this year?"
- "Using the 2026 monthly ISR table, how much tax is withheld on a 25,000 peso salary?"

## Configuration

| Variable | Required | Description |
|---|---|---|
| `BANXICO_TOKEN` | For Banxico tools | Banxico SIE API token. |
| `INEGI_TOKEN` | For INEGI tools | INEGI Indicators API token. |

Responses are cached in memory only: up to 1 hour for latest values, 24 hours for past Banxico ranges and 6 hours for the INPC series. Nothing is written to disk.

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy .
uv run mcp-mexico      # starts the server over stdio
```

Tests never touch the network: they replay responses recorded from the real APIs. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

This project is not affiliated with Banco de México, INEGI or the SAT. Figures come from their public sources, but check the cited source before relying on them for tax or legal decisions.

## License

[MIT](LICENSE) © Diego Tepichin
