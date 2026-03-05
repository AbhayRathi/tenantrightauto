import logging
from typing import Any
from tavily import AsyncTavilyClient  # type: ignore[import]
import os

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS = [
    "sfrb.org",
    "tenantstogether.org",
    "leginfo.legislature.ca.gov",
    "sfgov.org",
]


async def search_tenant_law(question: str) -> tuple[str, list[str]]:
    """Search for SF tenant law information.

    Returns (answer_text, list_of_source_urls).
    On any failure returns ("", []) so the chat endpoint is never blocked.
    """
    try:
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            return ("", [])

        client = AsyncTavilyClient(api_key=api_key)
        query = f"San Francisco tenant rights {question} California law 2025"

        # Primary: targeted trusted domains
        response: dict[str, Any] = await client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
            include_domains=TRUSTED_DOMAINS,
        )

        results = response.get("results") or []
        answer = response.get("answer") or ""

        if not results:
            # Fallback: broader search
            response = await client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )
            results = response.get("results") or []
            answer = response.get("answer") or ""

        sources = [r["url"] for r in results if r.get("url")]
        context_parts: list[str] = []
        if answer:
            context_parts.append(answer)
        for r in results:
            content = r.get("content", "")
            if content:
                context_parts.append(f"[{r.get('url', '')}]\n{content[:500]}")

        context = "\n\n".join(context_parts)
        return (context, sources)

    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily search failed: %s", exc)
        return ("", [])
