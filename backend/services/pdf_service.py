import re
import io
import logging
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 100
MAX_TEXT_CHARS = 50_000
PDF_MAGIC = b"%PDF"


async def extract_text_from_pdf(file: UploadFile) -> str:
    """Validate and extract text from a PDF upload."""
    import fitz  # PyMuPDF

    # Validate MIME type
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted (invalid MIME type).")

    # Read file content
    content = await file.read()

    # Validate magic bytes
    if not content.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF (bad magic bytes).")

    # Validate size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 10 MB size limit.")

    # Open with PyMuPDF
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        logger.warning("PyMuPDF could not open PDF: %s", exc)
        raise HTTPException(status_code=422, detail="Could not open PDF file. It may be corrupted.")

    # Reject encrypted / password-protected PDFs
    if doc.is_encrypted:
        doc.close()
        raise HTTPException(status_code=422, detail="Password-protected or encrypted PDFs are not supported.")

    page_count = doc.page_count

    # Reject empty or oversized documents
    if page_count == 0:
        doc.close()
        raise HTTPException(status_code=422, detail="PDF contains no pages.")
    if page_count > MAX_PAGES:
        doc.close()
        raise HTTPException(status_code=422, detail=f"PDF exceeds the {MAX_PAGES}-page limit ({page_count} pages).")

    # Extract text page by page
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()

    full_text = "\n".join(parts)

    # Sanitize: strip null bytes and control characters (keep newline \n and tab \t)
    full_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", full_text)

    # Truncate if necessary
    if len(full_text) > MAX_TEXT_CHARS:
        full_text = full_text[:MAX_TEXT_CHARS] + "\n\n[Document truncated]"

    return full_text
