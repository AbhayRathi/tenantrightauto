import re
import logging
from fastapi import APIRouter, HTTPException, Request

from models.schemas import ChatRequest, ChatResponse
from services import tavily_service, claude_service
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# Patterns for extracting citations from Claude's answer
_CITATION_PATTERNS = [
    r"Civil Code\s+§\s*\d+[\w.]*",
    r"California\s+Civil\s+Code\s+§\s*\d+[\w.]*",
    r"SF\s+Rent\s+Ordinance\s+§\s*[\d.]+",
    r"San\s+Francisco\s+Rent\s+Ordinance\s+§\s*[\d.]+",
    r"Administrative\s+Code\s+§\s*\d+[\w.]*",
]
_CITATION_RE = re.compile("|".join(_CITATION_PATTERNS), re.IGNORECASE)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(request: Request, body: ChatRequest):
    # Search for context (failure is non-blocking)
    search_context, sources = await tavily_service.search_tenant_law(body.question)

    # Get answer from Claude
    try:
        answer = await claude_service.chat_rights(body.question, search_context)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in claude_service.chat_rights: %s", exc)
        raise HTTPException(status_code=503, detail="AI service is unavailable. Please try again.")

    # Extract citations from the answer
    citations = list(dict.fromkeys(_CITATION_RE.findall(answer)))

    return ChatResponse(answer=answer, sources=sources, citations=citations)
