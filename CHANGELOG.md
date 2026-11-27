# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - Unreleased

First stable version: from here on, tool names, arguments and result fields only change in compatible ways until 2.0. It includes everything listed under 0.2.0, which was prepared but not published to PyPI.

### Added

- A contract test pins the arguments and result schema of all eight tools, and another starts the server over stdio as an MCP client would.
- This changelog.

### Changed

- Requires the `mcp` Python SDK 2.3.

### Fixed

- Unusable data from Banxico or INEGI (`NaN` or infinite values, an empty INPC series, a zero or negative index) is reported as a tool error. Non-finite values used to break the client session.
- Dates before 1900 return a clear error instead of crashing.
- A badly pasted API token returns an error that names the variable, without echoing the value or sending it.

## 0.2.0 - 2026-11-05 (not published to PyPI)

### Added

- Truth-gap evaluation in `evals/`: 18 questions on official Mexican figures, answered by a model with and without these tools. Method and results in `docs/truth-gap.md`.

### Changed

- The Banxico range tools report as `start` and `end` the first and last days that have data.

### Fixed

- `get_fix_rate` and `get_interest_rate` reject dates after today in Mexico City instead of returning an older value.

## [0.1.3] - 2026-10-21

### Added

- `server.json` and the `mcp-name` marker, to list the server in the official MCP Registry. No code changes.

## [0.1.2] - 2026-10-20

### Fixed

- "Today" is computed in Mexico City time instead of the machine's clock. This affects the UMA in force, the default ISR table year and how long Banxico data is cached.

## [0.1.1] - 2026-10-17

### Fixed

- `get_uma` returns an error once the packaged UMA expires, instead of presenting it as current.
- Banxico and INEGI responses in an unexpected format are reported as upstream errors.
- One automatic retry on network errors and HTTP 502, 503 and 504; rate limits get a specific message.
- `get_inflation_range` reports the first and last months actually returned.

## [0.1.0] - 2026-10-05

First release.

### Added

- `get_fix_rate`, `get_fix_rate_range`, `get_interest_rate` and `get_interest_rate_range` (Banxico SIE).
- `get_inflation` and `get_inflation_range` (INEGI INPC).
- `get_uma` and `get_isr_table`, offline, for 2020–2026.
- Every result names its official source.

[1.0.0]: https://github.com/DiegoTepichin/mcp-mexico/compare/v0.1.3...main
[0.1.3]: https://github.com/DiegoTepichin/mcp-mexico/releases/tag/v0.1.3
[0.1.2]: https://github.com/DiegoTepichin/mcp-mexico/releases/tag/v0.1.2
[0.1.1]: https://github.com/DiegoTepichin/mcp-mexico/releases/tag/v0.1.1
[0.1.0]: https://github.com/DiegoTepichin/mcp-mexico/releases/tag/v0.1.0
