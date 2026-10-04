"""Record live API responses used as test fixtures.

Run manually with real tokens; never in CI:

    uv run --env-file .env python scripts/record_fixtures.py
"""

import json
import sys
from pathlib import Path

import httpx

from mcp_mexico.config import BANXICO_TOKEN_VAR, read_token
from mcp_mexico.sources.banxico import BASE_URL as BANXICO_BASE_URL

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

BANXICO_PATHS = [
    "SF43718/datos/oportuno",
    "SF43718/datos/2026-09-24/2026-10-02",
    "SF43718/datos/2026-09-17/2026-09-27",
    "SF43718/datos/2026-10-03/2026-10-04",
    "SF61745/datos/oportuno",
    "SF43783/datos/oportuno",
    "SF331451/datos/oportuno",
    "SF43936/datos/oportuno",
    "SF43936/datos/2026-07-01/2026-09-30",
]


def fixture_name(path: str) -> str:
    return path.replace("/", "_") + ".json"


def record_banxico(token: str) -> None:
    target = FIXTURES_DIR / "banxico"
    target.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=30) as client:
        for path in BANXICO_PATHS:
            response = client.get(f"{BANXICO_BASE_URL}/{path}", headers={"Bmx-Token": token})
            response.raise_for_status()
            content = json.dumps(response.json(), ensure_ascii=False, indent=2) + "\n"
            (target / fixture_name(path)).write_text(content, encoding="utf-8")
            print(f"recorded banxico/{fixture_name(path)}")


def main() -> int:
    token = read_token(BANXICO_TOKEN_VAR)
    if token is None:
        print(f"{BANXICO_TOKEN_VAR} is not set.", file=sys.stderr)
        return 1
    record_banxico(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
