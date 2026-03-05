from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class SeverityLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class IllegalClause(BaseModel):
    clause_text: str = Field(..., max_length=2000)
    violation_type: str
    legal_citation: str
    severity: SeverityLevel
    remedy: str
    explanation: str


class AnalyzeResponse(BaseModel):
    session_id: str
    illegal_clauses: list[IllegalClause]
    total_clauses_scanned: int
    risk_score: float = Field(..., ge=0, le=100)
    summary: str


class ChatRequest(BaseModel):
    question: str = Field(..., max_length=1000)
    session_id: Optional[str] = None

    @field_validator("question", mode="before")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("question must be a string")
        v = v.strip()
        # Remove null bytes and control characters except newline/tab
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
        return v


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    citations: list[str]


class DemandLetterRequest(BaseModel):
    session_id: str
    tenant_name: str = Field(..., max_length=200)
    tenant_address: str = Field(..., max_length=500)
    landlord_name: str = Field(..., max_length=200)
    landlord_address: str = Field(..., max_length=500)
    illegal_clauses: list[IllegalClause]
    remedy_requested: str = Field(..., max_length=2000)


class DemandLetterResponse(BaseModel):
    letter_text: str
    generated_at: datetime


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
