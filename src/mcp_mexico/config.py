import os

BANXICO_TOKEN_VAR = "BANXICO_TOKEN"
INEGI_TOKEN_VAR = "INEGI_TOKEN"


def read_token(variable: str) -> str | None:
    value = os.environ.get(variable, "").strip()
    return value or None
