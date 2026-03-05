import logging
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded  # type: ignore[import]
from slowapi import _rate_limit_exceeded_handler  # type: ignore[import]

from middleware.rate_limit import limiter
from routers import analyze, chat, letter, graph
from services.neo4j_service import neo4j_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up.")
    yield
    logger.info("Application shutting down — closing Neo4j driver.")
    neo4j_service.close()


app = FastAPI(title="Tenant Rights Autopilot API", version="1.0.0", lifespan=lifespan)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Routers
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(letter.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception for %s %s:\n%s", request.method, request.url, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "An internal server error occurred."})


@app.get("/health")
async def health():
    neo4j_ok = neo4j_service.is_connected()
    return {"status": "ok", "neo4j": neo4j_ok}
