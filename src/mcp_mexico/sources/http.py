import asyncio

import httpx

ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.5
RETRYABLE_STATUS_CODES = frozenset({502, 503, 504})


async def get_with_retry(
    http: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> httpx.Response:
    """GET once more after a transient failure; the final attempt's errors propagate."""
    for _ in range(ATTEMPTS - 1):
        try:
            response = await http.get(url, headers=headers, params=params)
        except httpx.TransportError:
            pass
        else:
            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response
        await asyncio.sleep(RETRY_DELAY_SECONDS)
    return await http.get(url, headers=headers, params=params)
