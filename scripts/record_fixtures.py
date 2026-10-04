"""Record live API responses used as test fixtures.

Run manually with real tokens; never in CI:

    uv run --env-file .env python scripts/record_fixtures.py
"""

import json
import sys
from pathlib import Path

import httpx

from mcp_mexico.config import BANXICO_TOKEN_VAR, INEGI_TOKEN_VAR, read_token
from mcp_mexico.sources.banxico import BASE_URL as BANXICO_BASE_URL
from mcp_mexico.sources.inegi import BASE_URL as INEGI_BASE_URL
from mcp_mexico.sources.inegi import INPC_PATH

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

INEGI_PATHS = [INPC_PATH]


def fixture_name(path: str) -> str:
    return path.replace("/", "_") + ".json"


def save(source: str, path: str, response: httpx.Response) -> None:
    response.raise_for_status()
    target = FIXTURES_DIR / source / fixture_name(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(response.json(), ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"recorded {source}/{target.name}")


def record_banxico(client: httpx.Client, token: str) -> None:
    for path in BANXICO_PATHS:
        response = client.get(f"{BANXICO_BASE_URL}/{path}", headers={"Bmx-Token": token})
        save("banxico", path, response)


def record_inegi(client: httpx.Client, token: str) -> None:
    for path in INEGI_PATHS:
        response = client.get(f"{INEGI_BASE_URL}/{path}/{token}", params={"type": "json"})
        save("inegi", path, response)


def main() -> int:
    banxico_token = read_token(BANXICO_TOKEN_VAR)
    inegi_token = read_token(INEGI_TOKEN_VAR)
    if banxico_token is None or inegi_token is None:
        print(f"Both {BANXICO_TOKEN_VAR} and {INEGI_TOKEN_VAR} must be set.", file=sys.stderr)
        return 1
    with httpx.Client(timeout=30) as client:
        record_banxico(client, banxico_token)
        record_inegi(client, inegi_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
