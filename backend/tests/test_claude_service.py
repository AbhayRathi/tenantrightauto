"""Service-level unit tests for claude_service."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import anthropic
import httpx

from services.claude_service import analyze_lease, generate_demand_letter, chat_rights


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_message(text: str) -> MagicMock:
    """Return a mock anthropic message with a single text content block."""
    content_block = MagicMock()
    content_block.text = text
    msg = MagicMock()
    msg.content = [content_block]
    return msg


def _valid_analyze_json() -> str:
    return json.dumps({
        "illegal_clauses": [
            {
                "clause_text": "Tenant waives all habitability rights.",
                "violation_type": "Habitability waiver",
                "legal_citation": "CA Civil Code §1941",
                "severity": "high",
                "remedy": "Clause is void.",
                "explanation": "Cannot waive habitability.",
            }
        ],
        "total_clauses_scanned": 10,
        "risk_score": 80,
        "summary": "High-risk lease.",
    })


def _conn_error() -> anthropic.APIConnectionError:
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APIConnectionError(request=req)


def _rate_error() -> anthropic.RateLimitError:
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(429, request=req)
    return anthropic.RateLimitError("Rate limit exceeded", response=resp, body={})


def _status_error() -> anthropic.APIStatusError:
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(500, request=req)
    return anthropic.APIStatusError("Internal server error", response=resp, body={})


# ── analyze_lease ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_lease_happy_path_returns_parsed_dict():
    """analyze_lease() returns a dict parsed from valid JSON response."""
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _make_message(_valid_analyze_json())
        result = await analyze_lease("Sample lease text", "session-001")

    assert isinstance(result, dict)
    assert "illegal_clauses" in result
    assert result["risk_score"] == 80


@pytest.mark.asyncio
async def test_analyze_lease_preamble_before_json_uses_regex_fallback():
    """analyze_lease() uses regex fallback when response has preamble text before JSON."""
    preamble = "Here is my analysis:\n" + _valid_analyze_json()
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _make_message(preamble)
        result = await analyze_lease("Sample lease text", "session-001")

    assert isinstance(result, dict)
    assert "illegal_clauses" in result


@pytest.mark.asyncio
async def test_analyze_lease_connection_error_raises_503():
    """analyze_lease() raises HTTPException(503) on APIConnectionError."""
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = _conn_error()
        with pytest.raises(HTTPException) as exc_info:
            await analyze_lease("text", "session-001")
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_analyze_lease_rate_limit_error_raises_503():
    """analyze_lease() raises HTTPException(503) on RateLimitError."""
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = _rate_error()
        with pytest.raises(HTTPException) as exc_info:
            await analyze_lease("text", "session-001")
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_analyze_lease_api_status_error_raises_503():
    """analyze_lease() raises HTTPException(503) on APIStatusError."""
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = _status_error()
        with pytest.raises(HTTPException) as exc_info:
            await analyze_lease("text", "session-001")
    assert exc_info.value.status_code == 503


# ── generate_demand_letter ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_demand_letter_contains_landlord_tenant_and_statute():
    """generate_demand_letter() returns letter text with landlord name, tenant name, statute citation."""
    letter_text = (
        "Dear Mr. Landlord Smith,\n"
        "I, Jane Doe, write regarding illegal lease clauses.\n"
        "CA Civil Code §1941 voids clause 3.\n"
        "Please respond within 10 business days."
    )
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _make_message(letter_text)
        result = await generate_demand_letter(
            tenant_name="Jane Doe",
            tenant_address="123 Main St",
            landlord_name="Landlord Smith",
            landlord_address="456 Oak Ave",
            clauses=[{
                "clause_text": "Tenant waives habitability.",
                "violation_type": "Habitability waiver",
                "legal_citation": "CA Civil Code §1941",
                "remedy": "Clause is void.",
            }],
            remedy_requested="Remove illegal clauses.",
        )

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Landlord Smith" in result or "Jane Doe" in result or "§1941" in result


# ── chat_rights ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_rights_returns_string_answer():
    """chat_rights() returns a non-empty string answer."""
    answer = "Under CA Civil Code §1954, landlords must give 24-hour notice. Not legal advice."
    with patch("services.claude_service._client.messages.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = _make_message(answer)
        result = await chat_rights("Can my landlord enter without notice?", "")

    assert isinstance(result, str)
    assert len(result) > 0
    assert "§1954" in result or "24-hour" in result or "notice" in result.lower()
