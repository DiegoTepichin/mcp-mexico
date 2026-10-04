# Contributing

Thanks for your interest. Issues and pull requests are welcome, in English or Spanish.

## Before you start

- For anything bigger than a small fix, open an issue first so we can agree on the approach.
- Check the open issues to avoid duplicate work.

## Development setup

```bash
uv sync
```

## Checks

All of these must pass before a pull request is merged (CI runs them too):

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run pytest
```

## Tests and recorded API responses

Tests never call Banxico or INEGI. They replay JSON responses stored in `tests/fixtures/`. If you add a tool that needs a new request, add its path to `scripts/record_fixtures.py` and record it with your own tokens:

```bash
cp .env.example .env   # then fill in your tokens
uv run --env-file .env python scripts/record_fixtures.py
```

Check that no token ends up in a fixture before committing.

## Updating UMA and ISR tables

The offline data lives in `src/mcp_mexico/fiscal/data/`. Every entry must cite the official document it comes from (INEGI, SAT or DOF) and the date it was verified. Pull requests that change figures without a source will not be merged.

## Pull requests

- One logical change per pull request.
- Add or update tests for every behavior change.
- Update the README if you change user-facing behavior.
- Use [Conventional Commits](https://www.conventionalcommits.org/) in English, for example `feat: add INPC tool` or `fix: handle empty Banxico response`.

## Reporting bugs

Use the bug report template and include the version, your OS and the smallest input that reproduces the problem. Never paste API tokens or personal data.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
