"""Tests for /api/v1/analyze endpoint."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx


def test_analyze_missing_file(client):
    """Should return 422 when no file is uploaded."""
    response = client.post("/api/v1/analyze")
    assert response.status_code == 422


def test_analyze_non_pdf(client):
    """Should return 400 when a non-PDF file is uploaded."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_analyze_bad_magic_bytes(client):
    """Should return 400 when file has PDF MIME but wrong magic bytes."""
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.pdf", io.BytesIO(b"This is not a PDF"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "magic bytes" in response.json()["detail"].lower()


def test_analyze_success(client, sample_pdf_bytes, sample_analyze_response):
    """Should return AnalyzeResponse when pdf_service, claude_service, and neo4j succeed."""
    with (
        patch("routers.analyze.pdf_service.extract_text_from_pdf", new_callable=AsyncMock) as mock_pdf,
        patch("routers.analyze.claude_service.analyze_lease", new_callable=AsyncMock) as mock_claude,
        patch("routers.analyze.neo4j_service.store_analysis", return_value=True),
    ):
        mock_pdf.return_value = "LEASE TEXT: tenant waives all rights."
        mock_claude.return_value = sample_analyze_response

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["risk_score"] == 75
    assert len(data["illegal_clauses"]) == 1
    assert data["illegal_clauses"][0]["severity"] == "high"


def test_analyze_risk_score_clamped(client, sample_pdf_bytes, sample_analyze_response):
    """Risk score should be clamped to 0-100."""
    out_of_range = dict(sample_analyze_response, risk_score=999)

    with (
        patch("routers.analyze.pdf_service.extract_text_from_pdf", new_callable=AsyncMock) as mock_pdf,
        patch("routers.analyze.claude_service.analyze_lease", new_callable=AsyncMock) as mock_claude,
        patch("routers.analyze.neo4j_service.store_analysis", return_value=True),
    ):
        mock_pdf.return_value = "lease text"
        mock_claude.return_value = out_of_range

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["risk_score"] == 100.0


def test_analyze_neo4j_failure_non_blocking(client, sample_pdf_bytes, sample_analyze_response):
    """Neo4j failure should not cause analyze to fail."""
    with (
        patch("routers.analyze.pdf_service.extract_text_from_pdf", new_callable=AsyncMock) as mock_pdf,
        patch("routers.analyze.claude_service.analyze_lease", new_callable=AsyncMock) as mock_claude,
        patch("routers.analyze.neo4j_service.store_analysis", side_effect=Exception("DB down")),
    ):
        mock_pdf.return_value = "lease text"
        mock_claude.return_value = sample_analyze_response

        response = client.post(
            "/api/v1/analyze",
            files={"file": ("lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        )

    assert response.status_code == 200


# ── Async variants ──────────────────────────────────────────────────────────


def _get_app():
    from main import app  # noqa: PLC0415
    return app


@pytest.mark.asyncio
async def test_analyze_missing_file_async():
    """Async: should return 422 when no file is uploaded."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/v1/analyze")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_non_pdf_async():
    """Async: should return 400 when a non-PDF file is uploaded."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/analyze",
            files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
        )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_bad_magic_bytes_async():
    """Async: should return 400 when file has PDF MIME but wrong magic bytes."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/analyze",
            files={"file": ("test.pdf", io.BytesIO(b"Not a PDF"), "application/pdf")},
        )
    assert response.status_code == 400
    assert "magic bytes" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_analyze_success_async(minimal_pdf, mock_pdf_service, mock_claude_service, mock_neo4j_service):
    """Async: should return AnalyzeResponse when all services succeed."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/analyze",
            files={"file": ("lease.pdf", io.BytesIO(minimal_pdf), "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["risk_score"] == 75
    assert len(data["illegal_clauses"]) == 1


@pytest.mark.asyncio
async def test_analyze_risk_score_clamped_async(minimal_pdf, mock_neo4j_service, sample_analyze_response):
    """Async: risk score should be clamped to 0-100."""
    out_of_range = dict(sample_analyze_response, risk_score=999)
    with (
        patch("routers.analyze.pdf_service.extract_text_from_pdf", new_callable=AsyncMock) as mock_pdf,
        patch("routers.analyze.claude_service.analyze_lease", new_callable=AsyncMock) as mock_claude,
    ):
        mock_pdf.return_value = "lease text"
        mock_claude.return_value = out_of_range
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/analyze",
                files={"file": ("lease.pdf", io.BytesIO(minimal_pdf), "application/pdf")},
            )
    assert response.status_code == 200
    assert response.json()["risk_score"] == 100.0


@pytest.mark.asyncio
async def test_analyze_neo4j_failure_non_blocking_async(minimal_pdf, mock_pdf_service, mock_claude_service):
    """Async: Neo4j failure should not cause analyze to fail."""
    with patch("routers.analyze.neo4j_service.store_analysis", side_effect=Exception("DB down")):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=_get_app()), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/analyze",
                files={"file": ("lease.pdf", io.BytesIO(minimal_pdf), "application/pdf")},
            )
    assert response.status_code == 200

