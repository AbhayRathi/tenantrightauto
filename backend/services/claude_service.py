import json
import re
import logging
from typing import Any
import anthropic
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic()

MODEL = "claude-sonnet-4-20250514"

_ANALYZE_SYSTEM = """You are an expert California and San Francisco tenant rights attorney.
You analyze residential lease agreements to identify illegal, void, or unenforceable clauses under:
- California Civil Code §1941 (implied warranty of habitability)
- California Civil Code §1942.5 (anti-retaliation)
- California Civil Code §1950.5 (security deposits)
- California Civil Code §1954 (landlord right of entry — 24-hr notice required)
- San Francisco Rent Ordinance §37.9 (just cause eviction)
- SF Just Cause for Eviction Ordinance (Prop M / Ordinance §37.9)
- SF Administrative Code §49 (tenant protections)

Clause types that are automatically void under California law:
- Waiver of the implied warranty of habitability
- Waiver of right to repair-and-deduct
- Waiver of anti-retaliation protections
- Security deposit exceeding 2 months' rent (unfurnished) or 3 months' (furnished)
- Entry without required notice
- Waiver of just cause eviction protections (SF covered units)
- Any provision imposing fees/penalties prohibited by statute
- Clauses requiring tenant to waive any statutory right

You MUST respond with ONLY valid JSON (no prose, no markdown fences) matching this exact shape:
{
  "illegal_clauses": [
    {
      "clause_text": "<exact text from lease, max 2000 chars>",
      "violation_type": "<short label>",
      "legal_citation": "<statute/ordinance citation>",
      "severity": "high" | "medium" | "low",
      "remedy": "<what the tenant can do>",
      "explanation": "<clear plain-English explanation>"
    }
  ],
  "total_clauses_scanned": <integer>,
  "risk_score": <0-100 integer>,
  "summary": "<2-3 sentence plain-English summary>"
}

If no illegal clauses are found, return an empty illegal_clauses array.
"""

_CHAT_SYSTEM = """You are an expert San Francisco tenant rights advisor.
Answer questions using specific California and San Francisco laws.
Give concise 3-5 sentence answers.
Always cite specific statutes or ordinances when relevant.
End every answer with: "Note: This is general information, not formal legal advice. Consult a licensed attorney for your specific situation."
"""


async def analyze_lease(text: str, session_id: str) -> dict[str, Any]:
    """Send lease text to Claude and return parsed JSON analysis."""
    prompt = f"Session ID: {session_id}\n\nLEASE TEXT:\n{text}"
    try:
        message = await _client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=_ANALYZE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIConnectionError as exc:
        logger.error("Claude connection error: %s", exc)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")
    except anthropic.RateLimitError as exc:
        logger.error("Claude rate limit: %s", exc)
        raise HTTPException(status_code=503, detail="AI service rate limit reached. Please try again shortly.")
    except anthropic.APIStatusError as exc:
        logger.error("Claude API status error %s: %s", exc.status_code, exc.message)
        raise HTTPException(status_code=503, detail="AI service returned an error. Please try again.")

    raw = message.content[0].text.strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: extract JSON block with regex
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.error("Could not parse Claude response as JSON: %s", raw[:500])
    raise HTTPException(status_code=503, detail="AI service returned an unexpected response format.")


async def generate_demand_letter(
    tenant_name: str,
    tenant_address: str,
    landlord_name: str,
    landlord_address: str,
    clauses: list[dict[str, Any]],
    remedy_requested: str,
) -> str:
    """Generate a formal demand letter."""
    violations_text = "\n".join(
        f"- Clause: \"{c['clause_text'][:300]}...\"\n"
        f"  Violation: {c['violation_type']}\n"
        f"  Citation: {c['legal_citation']}\n"
        f"  Remedy: {c['remedy']}"
        for c in clauses
    )

    prompt = f"""Draft a formal legal demand letter with the following information:

Tenant: {tenant_name}
Tenant Address: {tenant_address}
Landlord: {landlord_name}
Landlord Address: {landlord_address}

ILLEGAL LEASE CLAUSES IDENTIFIED:
{violations_text}

REMEDY REQUESTED: {remedy_requested}

Requirements:
- Professional legal tone, firm but not aggressive
- State that identified clauses are void and unenforceable under California law
- Cite the specific statutes for each violation
- Give landlord 10 business days to respond
- Mention SF Rent Board (sfrb.org, 415-252-4602) as escalation path
- Include a clear statement of what action will be taken if no response is received
"""
    try:
        message = await _client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system="You are an expert tenant rights attorney drafting formal demand letters. Return only the letter text, no commentary.",
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIConnectionError as exc:
        logger.error("Claude connection error: %s", exc)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")
    except anthropic.RateLimitError as exc:
        logger.error("Claude rate limit: %s", exc)
        raise HTTPException(status_code=503, detail="AI service rate limit reached. Please try again shortly.")
    except anthropic.APIStatusError as exc:
        logger.error("Claude API status error %s: %s", exc.status_code, exc.message)
        raise HTTPException(status_code=503, detail="AI service returned an error. Please try again.")

    return message.content[0].text.strip()


async def chat_rights(question: str, search_context: str) -> str:
    """Answer a tenant rights question, optionally augmented with Tavily search context."""
    context_block = f"\nRELEVANT LEGAL CONTEXT FROM CURRENT SOURCES:\n{search_context}\n" if search_context else ""
    prompt = f"{context_block}\nTENANT QUESTION: {question}"

    try:
        message = await _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=_CHAT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIConnectionError as exc:
        logger.error("Claude connection error: %s", exc)
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")
    except anthropic.RateLimitError as exc:
        logger.error("Claude rate limit: %s", exc)
        raise HTTPException(status_code=503, detail="AI service rate limit reached. Please try again shortly.")
    except anthropic.APIStatusError as exc:
        logger.error("Claude API status error %s: %s", exc.status_code, exc.message)
        raise HTTPException(status_code=503, detail="AI service returned an error. Please try again.")

    return message.content[0].text.strip()
