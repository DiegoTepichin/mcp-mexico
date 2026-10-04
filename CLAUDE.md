@../briefs/mcp-mexico.md

# mcp-mexico

## What it is

An MCP (Model Context Protocol) server that gives AI agents such as Claude and Cursor access to Mexican public data: Banxico SIE (FIX exchange rate, interest rates), INEGI (INPC inflation and other indicators), and SAT ISR tables and UMA values.

## Who it is for

Developers, analysts, accountants and fintech teams in Mexico who use MCP clients (Claude Desktop, Claude Code, Cursor) and need reliable official figures inside their AI workflow.

## Scope (v0.1)

1. Banxico tools: FIX exchange rate (latest, by date and range) and key interest rates.
2. INEGI tools: INPC / inflation (latest and by period).
3. Offline tools: UMA values and ISR tables, each with year and official source.
4. One-line install with `uvx`; documented setup for Claude Desktop, Claude Code and Cursor. API tokens via environment variables.
5. Tests with recorded API responses and green CI.

Anything else is out of scope until v0.1 ships.

## Code standards

- Python 3.11+ (CI matrix: 3.11, 3.12, 3.13, 3.14). Dependencies and environments managed with `uv`.
- Strict typing: `mypy --strict` clean, no untyped public functions, no `Any` without a reason.
- Lint and format with `ruff`.
- Tests with `pytest`. No network calls in tests: use recorded or fixture data.
- Small functions, clear names, no dead code, no comments that restate the code.
- Configuration and secrets only through environment variables, documented in `.env.example`.
- Conventional Commits in English, one logical change per commit.
- README and docs describe only what exists and has been run.

## Commands

```bash
uv sync                      # install dependencies
uv run mcp-mexico            # start the server over stdio
uv run pytest                # tests
uv run ruff check .          # lint
uv run ruff format --check . # format check
uv run mypy .                # strict type check
uv run --env-file .env python scripts/record_fixtures.py  # re-record API fixtures (manual, needs tokens)
```

## Structure

See `docs/PLAN.md` for the full architecture.

- `src/mcp_mexico/server.py`: builds the `MCPServer` and registers tools; `main()` is the console entry point.
- `src/mcp_mexico/tools/`: tool functions exposed over MCP; they turn domain errors into `ToolError`.
- `src/mcp_mexico/fiscal/`: offline data (`data/*.json`, each with its source) and loaders.
- `src/mcp_mexico/sources/`: async API clients (Banxico SIE) with in-memory TTL cache and error mapping.
- `src/mcp_mexico/models.py`: Pydantic models returned by tools; every result carries a `Source`.
- `tests/`: unit tests plus tool tests through an in-memory `mcp.Client`. API tests use `httpx.MockTransport` serving `tests/fixtures/`, recorded by `scripts/record_fixtures.py`.
