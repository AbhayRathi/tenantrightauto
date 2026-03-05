"""Tests for rate limiting middleware behaviour."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_app(limit: str) -> FastAPI:
    """Create a fresh FastAPI app with the given rate limit for isolation."""
    lim = Limiter(key_func=get_remote_address, default_limits=[limit])
    app = FastAPI()
    app.state.limiter = lim
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/ping")
    @lim.limit(limit)
    async def ping(request: Request):  # noqa: ARG001
        return {"ok": True}

    return app


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_rate_limit_requests_below_limit_succeed():
    """Requests up to the limit return 200."""
    app = _make_app("3/minute")
    with TestClient(app, raise_server_exceptions=False) as client:
        for _ in range(3):
            assert client.get("/ping").status_code == 200


def test_rate_limit_exceeded_returns_429():
    """The (limit + 1)th request within one minute returns HTTP 429."""
    app = _make_app("2/minute")
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/ping").status_code == 200
        assert client.get("/ping").status_code == 200
        response = client.get("/ping")
        assert response.status_code == 429


def test_rate_limit_resets_after_window():
    """Counter resets after the time window elapses (simulated with freezegun)."""
    from freezegun import freeze_time

    app = _make_app("1/minute")

    with freeze_time("2026-01-01 00:00:00"):
        with TestClient(app, raise_server_exceptions=False) as client:
            # First request in window succeeds
            assert client.get("/ping").status_code == 200
            # Second request in same window is rate-limited
            assert client.get("/ping").status_code == 429

    # Advance past the 1-minute window
    with freeze_time("2026-01-01 00:01:01"):
        with TestClient(app, raise_server_exceptions=False) as client2:
            # After the window resets, should succeed again
            assert client2.get("/ping").status_code == 200


def test_rate_limit_env_var_is_used_in_main_app():
    """The main app's limiter respects the RATE_LIMIT_PER_MINUTE env var."""
    import os
    from middleware.rate_limit import RATE_LIMIT

    # Verify the limiter reads from the env var (default is "20")
    assert RATE_LIMIT.isdigit()
    expected = os.environ.get("RATE_LIMIT_PER_MINUTE", "20")
    assert RATE_LIMIT == expected
