"""Service-level unit tests for pdf_service.extract_text_from_pdf."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile

from services.pdf_service import (
    extract_text_from_pdf,
    MAX_FILE_SIZE_BYTES,
    MAX_PAGES,
    MAX_TEXT_CHARS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_upload(content: bytes, content_type: str = "application/pdf") -> UploadFile:
    """Return a mock UploadFile with the given bytes and MIME type."""
    mock = MagicMock(spec=UploadFile)
    mock.content_type = content_type
    mock.read = AsyncMock(return_value=content)
    return mock


MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
    b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
    b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>>\nendobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
    b"0000000058 00000 n \n0000000115 00000 n \n"
    b"trailer\n<</Size 4 /Root 1 0 R>>\nstartxref\n190\n%%EOF"
)


# ── Valid PDF ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_valid_pdf_returns_text():
    """Valid minimal PDF passes all checks and returns extracted text string."""
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Lease agreement text."
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = 1
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        result = await extract_text_from_pdf(upload)

    assert isinstance(result, str)
    assert "Lease agreement text." in result


# ── File size ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_oversized_file_raises_400():
    """File larger than 10 MB raises HTTPException with status 400."""
    big_content = b"%PDF" + b"x" * (MAX_FILE_SIZE_BYTES + 1)
    upload = _make_upload(big_content)

    with pytest.raises(HTTPException) as exc_info:
        await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 400
    assert "10 MB" in exc_info.value.detail


# ── MIME type ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_non_pdf_mime_raises_400():
    """Non-PDF MIME type raises HTTPException with status 400 before file is read."""
    upload = _make_upload(b"Hello world", content_type="text/plain")

    with pytest.raises(HTTPException) as exc_info:
        await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 400
    assert "PDF" in exc_info.value.detail


# ── Magic bytes ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_bad_magic_bytes_raises_400():
    """File with PDF MIME but wrong magic bytes raises HTTPException with status 400."""
    upload = _make_upload(b"This is not a PDF at all", content_type="application/pdf")

    with pytest.raises(HTTPException) as exc_info:
        await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 400
    assert "magic bytes" in exc_info.value.detail.lower()


# ── Encrypted PDF ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_encrypted_pdf_raises_422():
    """Encrypted/password-protected PDF raises HTTPException with status 422."""
    mock_doc = MagicMock()
    mock_doc.is_encrypted = True

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        with pytest.raises(HTTPException) as exc_info:
            await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 422
    assert "encrypted" in exc_info.value.detail.lower() or "password" in exc_info.value.detail.lower()


# ── Page count ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_zero_pages_raises_422():
    """PDF with zero pages raises HTTPException with status 422."""
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = 0

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        with pytest.raises(HTTPException) as exc_info:
            await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 422
    assert "no pages" in exc_info.value.detail.lower() or "page" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_pdf_service_too_many_pages_raises_422():
    """PDF with more than MAX_PAGES pages raises HTTPException with status 422."""
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = MAX_PAGES + 1

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        with pytest.raises(HTTPException) as exc_info:
            await extract_text_from_pdf(upload)

    assert exc_info.value.status_code == 422
    assert str(MAX_PAGES) in exc_info.value.detail


# ── Truncation ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_long_text_is_truncated():
    """Text exceeding MAX_TEXT_CHARS is truncated and [Document truncated] is appended."""
    long_text = "A" * (MAX_TEXT_CHARS + 1000)
    mock_page = MagicMock()
    mock_page.get_text.return_value = long_text
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = 1
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        result = await extract_text_from_pdf(upload)

    assert len(result) <= MAX_TEXT_CHARS + len("\n\n[Document truncated]") + 5
    assert "[Document truncated]" in result


# ── Sanitization ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pdf_service_null_bytes_and_control_chars_stripped():
    """Null bytes and control characters are removed from extracted text."""
    dirty_text = "Hello\x00 World\x01\x07\x1f End"
    mock_page = MagicMock()
    mock_page.get_text.return_value = dirty_text
    mock_doc = MagicMock()
    mock_doc.is_encrypted = False
    mock_doc.page_count = 1
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    upload = _make_upload(MINIMAL_PDF)

    with patch("fitz.open", return_value=mock_doc):
        result = await extract_text_from_pdf(upload)

    assert "\x00" not in result
    assert "\x01" not in result
    assert "\x07" not in result
    assert "\x1f" not in result
    assert "Hello" in result
    assert "World" in result
