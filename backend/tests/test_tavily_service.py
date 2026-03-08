"""Service-level unit tests for tavily_service.search_tenant_law."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_search_response(answer: str, urls: list[str]) -> dict:
    return {
        "answer": answer,
        "results": [{"url": u, "content": f"Content from {u}"} for u in urls],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tavily_normal_search_returns_answer_and_sources(monkeypatch):
    """Normal search with trusted domains returns (answer_str, [source_urls])."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    mock_client = AsyncMock()
    mock_client.search.return_value = _make_search_response(
        answer="SF tenants are protected by Rent Ordinance §37.9.",
        urls=["https://sfrb.org/page1", "https://sfgov.org/page2"],
    )

    with patch("services.tavily_service.AsyncTavilyClient", return_value=mock_client):
        from services.tavily_service import search_tenant_law
        context, sources = await search_tenant_law("What are my eviction protections?")

    assert isinstance(context, str)
    assert len(context) > 0
    assert isinstance(sources, list)
    # Parse the URL and check the netloc to avoid substring-position ambiguity
    assert any(urlparse(s).netloc in ("sfrb.org", "www.sfrb.org") for s in sources)


@pytest.mark.asyncio
async def test_tavily_no_results_from_trusted_domains_falls_back_to_broader_search(monkeypatch):
    """Empty results from trusted domains triggers a second broader search."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    empty_response = {"answer": "", "results": []}
    broader_response = _make_search_response(
        answer="General info about tenant rights.",
        urls=["https://example.com/tenant-rights"],
    )

    mock_client = AsyncMock()
    # First call (trusted domains) returns empty; second call (broad) returns results
    mock_client.search.side_effect = [empty_response, broader_response]

    with patch("services.tavily_service.AsyncTavilyClient", return_value=mock_client):
        from services.tavily_service import search_tenant_law
        context, sources = await search_tenant_law("deposit return")

    assert mock_client.search.call_count == 2
    assert len(sources) > 0


@pytest.mark.asyncio
async def test_tavily_any_exception_returns_empty_tuple(monkeypatch):
    """Any exception during search returns ("", []) and never raises."""
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    mock_client = AsyncMock()
    mock_client.search.side_effect = Exception("Network failure")

    with patch("services.tavily_service.AsyncTavilyClient", return_value=mock_client):
        from services.tavily_service import search_tenant_law
        context, sources = await search_tenant_law("entry notice")

    assert context == ""
    assert sources == []


@pytest.mark.asyncio
async def test_tavily_missing_api_key_returns_empty_tuple(monkeypatch):
    """Missing TAVILY_API_KEY returns ("", []) without attempting any search."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with patch("services.tavily_service.AsyncTavilyClient") as mock_cls:
        from services.tavily_service import search_tenant_law
        context, sources = await search_tenant_law("rent increase")

    mock_cls.assert_not_called()
    assert context == ""
    assert sources == []
