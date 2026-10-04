from mcp_mexico.cache import TtlCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_returns_value_until_it_expires() -> None:
    clock = FakeClock()
    cache: TtlCache[str, int] = TtlCache(clock)
    cache.set("fix", 1, ttl_seconds=60)

    clock.now = 59.9
    assert cache.get("fix") == 1

    clock.now = 60
    assert cache.get("fix") is None


def test_missing_key_returns_none() -> None:
    assert TtlCache[str, int]().get("unknown") is None
