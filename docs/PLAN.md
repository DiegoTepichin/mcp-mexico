# mcp-mexico — v0.1 plan

Status: **approved** (2026-10-02). Started 2026-10-02. Target for v0.1: 2026-10-16.

## Goal

An MCP server, installable with one `uvx` command, that gives AI agents typed access to official Mexican figures: Banxico exchange and interest rates, INEGI inflation, and UMA and ISR tables. Every answer carries its official source and date.

## Architecture

```
src/mcp_mexico/
  server.py        MCP server instance, tool registration, `main()` entry point (stdio transport)
  config.py        Settings read from environment variables (BANXICO_TOKEN, INEGI_TOKEN)
  errors.py        Typed errors mapped to clear tool error messages (missing token, upstream down, no data)
  cache.py         Small in-memory TTL cache (process lifetime only)
  models.py        Pydantic models returned by tools (value + date + unit + source)
  sources/
    banxico.py     Async httpx client for Banxico SIE API
    inegi.py       Async httpx client for INEGI Indicators API
  fiscal/
    data/*.json    UMA and ISR tables per year, each with source reference
    tables.py      Loads and validates the packaged JSON
  tools/
    banxico.py     FIX and interest rate tools
    inegi.py       Inflation tools
    fiscal.py      UMA and ISR tools
tests/
  fixtures/        Recorded API responses (JSON)
scripts/
  record_fixtures.py   Refreshes fixtures from the live APIs (manual, needs tokens; never run in CI)
```

Key decisions:

- **SDK:** official `mcp` Python SDK, pinned to the 2.2.x line.
- **HTTP:** `httpx` (async). Tests mock it with `respx` and recorded fixtures; no network in tests.
- **Transport:** stdio only. No hosted server (out of scope).
- **Cache:** in-memory TTL. Historical data for 24 h, "latest" queries for 1 h. Nothing written to disk.
- **Offline data:** JSON packaged inside the wheel and validated with Pydantic on load. Each table includes `year`, `valid_from`, `source` (document name and URL) and `verified_on`.
- **Tokens:** optional. Offline tools work with no configuration. Banxico/INEGI tools return an actionable error that explains how to get the free token.
- **Package:** `mcp-mexico` on PyPI (name available as of 2026-10-02). Console script `mcp-mexico`. Build with `hatchling`.

## v0.1 tools

| Tool | Input | Returns | Source |
|---|---|---|---|
| `get_fix_rate` | optional `date` | FIX USD/MXN for that date, or the latest | Banxico SIE |
| `get_fix_rate_range` | `start`, `end` | FIX series | Banxico SIE |
| `get_interest_rate` | `rate` (`target`, `tiie_28`, `tiie_funding`, `cetes_28`), optional `date` | Latest value, or the value on/before a date | Banxico SIE |
| `get_interest_rate_range` | `rate`, `start`, `end` | Series | Banxico SIE |
| `get_inflation` | optional `year`/`month` | INPC index, monthly, annual and year-to-date inflation for the period, or the latest | INEGI |
| `get_inflation_range` | `start`, `end` (year-month) | Series of the above | INEGI |
| `get_uma` | optional `year` (2020–2026) | Daily, monthly and annual UMA and validity date | INEGI / DOF |
| `get_isr_table` | optional `year` (2020–2026), `period` (`monthly`, `annual`) | ISR rate table (Art. 96 monthly, Art. 152 annual) | RMF Annex 8 / DOF |

Banxico series IDs, confirmed against the live API on 2026-10-03: FIX `SF43718`, target rate `SF61745`, TIIE 28 `SF43783`, TIIE de Fondeo `SF331451`, CETES 28 `SF43936`. INEGI: INPC general index `910392` (monthly, 2nd fortnight of July 2018 = 100), confirmed with the INEGI catalog API on 2026-10-04; inflation is computed from the index and matches INEGI publications for 2026-08, 2024-12 and 2023-06. Nothing is hardcoded from memory without verification.

## Milestones

Each milestone gets its own branch and PR, and merges only with green CI.

### M1 — Skeleton, CI and UMA (2 days, target 2026-10-04)
- `pyproject.toml` (uv, hatchling, ruff, mypy strict, pytest), `src/` layout, `.env.example`, CI from `_templates`.
- Server starts over stdio; `uv run mcp-mexico` works.
- `get_uma` for 2020–2026, with each year verified against INEGI/DOF.
- Test that drives the server through an in-memory MCP client (list tools, call `get_uma`).
- **Done when:** CI is green on 3.11–3.14 and the server works from Claude Code locally.

### M2 — ISR tables (3 days, target 2026-10-07)
- Monthly (Art. 96) and annual (Art. 152) tables for 2020–2026. 2026 monthly is taken from `calculadoras-mx`; everything else comes from the RMF Annex 8 / DOF and gets verified.
- Validation tests: brackets are contiguous, rates go up, the last bracket is open, and every year has a source.
- **Done when:** `get_isr_table` works for every year and period with its source cited.

### M3 — Banxico (3 days, target 2026-10-10)
- SIE client, cache, error mapping (missing/invalid token, 5xx, empty series, non-business days).
- `get_fix_rate`, `get_fix_rate_range`, `get_interest_rate`.
- `scripts/record_fixtures.py` plus recorded fixtures.
- **Done when:** tools pass against fixtures and give the right answers in a manual live check.

### M4 — INEGI (2 days, target 2026-10-13)
- Indicators API client, `get_inflation` and `get_inflation_range`, with fixtures.
- **Done when:** results match INEGI's published INPC for 3 manually checked periods.

### M5 — Distribution and docs (3 days, target 2026-10-16)
- Verify `uvx --from <local wheel> mcp-mexico` works, and test the TestPyPI install (needs your OK).
- Configuration verified for Claude Desktop, Claude Code and Cursor.
- README (EN) + README.es.md, token guide, demo GIF, CONTRIBUTING, issue templates.
- **Done when:** a clean machine installs and uses it by following only the README.

## Test strategy

- **Unit:** parsers for each source, run against recorded fixtures (valid, empty, error). Includes JSON table validation.
- **Tool level:** every tool is called through an in-memory MCP client to check its schemas and outputs.
- **Errors:** missing token, HTTP 401/500, timeouts, dates with no data (weekends, future dates).
- **No network in CI.** Fixtures are refreshed by hand with `scripts/record_fixtures.py`.
- Every PR must pass `ruff check`, `ruff format --check`, `mypy --strict` and `pytest`. Coverage gets reported, with no hard gate.

## Out of scope for v0.1 (later list)

DOF, CFDI, other LATAM countries, hosted server, persistent cache, ISR calculation (computing the tax, not just returning the table), employment subsidy, other ISR periodicities (daily, weekly, biweekly), minimum wage, more Banxico/INEGI series.

## Launch checklist

- [ ] All milestones merged, CI green on `main`.
- [ ] README commands executed verbatim on a clean environment.
- [ ] Demo GIF recorded.
- [ ] Repo made public (needs your OK).
- [ ] v0.1.0 published to PyPI and GitHub release created (needs your OK).
- [ ] Listed in the MCP server registry / community lists.
- [ ] Posts: Show HN, r/mexico, r/LocalLLaMA, r/ClaudeAI, X.
- [ ] `ROADMAP.md` updated.

## 30-day success metrics (after launch)

- ≥ 100 GitHub stars.
- ≥ 500 PyPI downloads.
- ≥ 3 issues or PRs from external people.
- 100% of valid issues answered within 72 h.
- ≥ 1 maintenance release (v0.1.x).
