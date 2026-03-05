"""Pytest configuration and shared fixtures."""
import io
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure backend package is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """Return a synchronous TestClient for the FastAPI app."""
    # Patch neo4j_service before importing main so it never tries to connect
    with patch("services.neo4j_service.Neo4jService._connect"):
        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def make_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
        b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
        b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<</Size 4 /Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    return make_pdf_bytes()


@pytest.fixture
def sample_analyze_response() -> dict:
    return {
        "illegal_clauses": [
            {
                "clause_text": "Tenant waives right to habitability.",
                "violation_type": "Habitability waiver",
                "legal_citation": "CA Civil Code §1941",
                "severity": "high",
                "remedy": "Clause is void. Tenant retains full habitability rights.",
                "explanation": "Landlords cannot waive the implied warranty of habitability.",
            }
        ],
        "total_clauses_scanned": 15,
        "risk_score": 75,
        "summary": "This lease contains a high-severity illegal clause.",
    }
