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

None yet. Add each command here once it exists and has been run.

## Structure

Not defined yet. Decided in `docs/PLAN.md`.
