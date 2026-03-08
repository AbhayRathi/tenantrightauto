import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request

from models.schemas import DemandLetterRequest, DemandLetterResponse
from services import claude_service
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/letter", response_model=DemandLetterResponse)
@limiter.limit("20/minute")
async def generate_letter(request: Request, body: DemandLetterRequest):
    if not body.illegal_clauses:
        raise HTTPException(status_code=400, detail="At least one illegal clause must be provided.")

    try:
        letter_text = await claude_service.generate_demand_letter(
            tenant_name=body.tenant_name,
            tenant_address=body.tenant_address,
            landlord_name=body.landlord_name,
            landlord_address=body.landlord_address,
            clauses=[c.model_dump() for c in body.illegal_clauses],
            remedy_requested=body.remedy_requested,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in claude_service.generate_demand_letter: %s", exc)
        raise HTTPException(status_code=503, detail="AI service is unavailable. Please try again.")

    return DemandLetterResponse(
        letter_text=letter_text,
        generated_at=datetime.now(timezone.utc),
    )
