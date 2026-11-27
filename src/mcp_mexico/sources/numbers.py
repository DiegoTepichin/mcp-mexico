import math


def parse_finite(raw: str) -> float:
    """Like `float`, but rejects NaN and infinity, which cannot be serialised as JSON."""
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"{raw!r} is not a finite number")
    return value
