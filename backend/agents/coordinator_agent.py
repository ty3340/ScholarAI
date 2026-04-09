"""
Coordinator helper for ScholarAI.
"""
import os
import httpx
from dotenv import load_dotenv
from agents.citation_agent import run as citation_run
from agents.review_agent import run as review_run
from agents.search_agent import run as search_run
from tools.custom_tools import summarize_paper_content

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"), override=False)

async def search(query: str, max_results: int = 5) -> dict:
    return await search_run(query, max_results)


async def summarize(paper_id: str, abstract: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/run",
                json={"paper_id": paper_id, "abstract": abstract},
                timeout=30.0,
            )
            response.raise_for_status()
            return {
                "status": "success",
                "agent": "summary_agent_remote",
                "summary": response.json(),
            }
    except Exception as exc:
        fallback = await summarize_paper_content(paper_id, abstract)
        return {
            "status": "fallback",
            "agent": "summary_agent_remote",
            "summary": fallback,
            "message": f"Remote summary agent unavailable: {exc}",
        }


async def citations(papers: list[dict], style: str = "apa") -> dict:
    return await citation_run(papers, style)


async def review(query: str, review_type: str = "narrative", papers: list[dict] | None = None) -> str:
    return await review_run(query, review_type, papers or [])
