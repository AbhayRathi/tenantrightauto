import logging
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi import status

from models.schemas import AnalyzeResponse, IllegalClause
from services import pdf_service, claude_service
from services.neo4j_service import neo4j_service
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("20/minute")
async def analyze_lease(request: Request, file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())

    # Extract text from PDF
    try:
        text = await pdf_service.extract_text_from_pdf(file)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in pdf_service: %s", exc)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PDF.")

    # Analyze with Claude
    try:
        result = await claude_service.analyze_lease(text, session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in claude_service.analyze_lease: %s", exc)
        raise HTTPException(status_code=503, detail="AI analysis service is unavailable. Please try again.")

    # Parse clauses
    raw_clauses = result.get("illegal_clauses", [])
    clauses: list[IllegalClause] = []
    for c in raw_clauses:
        try:
            clauses.append(IllegalClause(**c))
        except Exception as exc:
            logger.warning("Skipping malformed clause: %s — %s", c, exc)

    # Clamp risk_score 0-100
    risk_score = max(0.0, min(100.0, float(result.get("risk_score", 0))))

    response = AnalyzeResponse(
        session_id=session_id,
        illegal_clauses=clauses,
        total_clauses_scanned=int(result.get("total_clauses_scanned", len(clauses))),
        risk_score=risk_score,
        summary=result.get("summary", ""),
    )

    # Store in Neo4j (non-blocking)
    try:
        neo4j_service.store_analysis(session_id, [c.model_dump() for c in clauses])
    except Exception as exc:
        logger.warning("Neo4j store_analysis non-blocking failure: %s", exc)

    return response
