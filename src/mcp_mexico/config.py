import os
import re

from mcp_mexico.errors import MalformedTokenError, MissingTokenError

BANXICO_TOKEN_VAR = "BANXICO_TOKEN"
INEGI_TOKEN_VAR = "INEGI_TOKEN"


def read_token(variable: str) -> str | None:
    value = os.environ.get(variable, "").strip()
    return value or None


def require_token(token: str | None, variable: str, signup_url: str) -> str:
    """Return a token that is safe to put in a header or URL, or explain how to fix it.

    Messages never include the token itself.
    """
    if token is None:
        raise MissingTokenError(
            f"{variable} is not set. Get a free token at {signup_url} and add it "
            "to the MCP server's environment."
        )
    if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        raise MalformedTokenError(
            f"{variable} is not a valid token: it has spaces or other characters a token "
            "cannot have. Copy it again."
        )
    return token
