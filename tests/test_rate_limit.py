"""Unit test rate limiter dasar."""
import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.rate_limit import rate_limit_dependency, reset_rate_limit_state_for_tests


def build_request(path="/api/test", client="198.51.100.7"):
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": (client, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_rate_limiter_returns_429_after_limit():
    reset_rate_limit_state_for_tests()
    dependency = rate_limit_dependency(scope="test", limit=1)
    asyncio.run(dependency(build_request()))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dependency(build_request()))
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers
    reset_rate_limit_state_for_tests()
