import logging
from fastapi import APIRouter, Request

from models.schemas import GraphResponse
from services.neo4j_service import neo4j_service
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph/{session_id}", response_model=GraphResponse)
@limiter.limit("20/minute")
async def get_graph(request: Request, session_id: str):
    data = neo4j_service.get_graph(session_id)
    return GraphResponse(nodes=data["nodes"], edges=data["edges"])
