"""
Review Agent helper for ScholarAI.
"""
import os
from dotenv import load_dotenv
from mcp.client import mcp_client
from tools.custom_tools import generate_literature_review

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"), override=False)

async def run(topic: str, review_type: str = "narrative", papers: list[dict] | None = None) -> str:
    """Generate a literature review for a topic."""
    if papers:
        selected_papers = papers
    else:
        search_results = await mcp_client.call_tool(
            "shared_paper_search",
            query=topic,
            max_results=5,
        )
        selected_papers = search_results.get("papers", []) if search_results.get("status") == "success" else []
    review = await generate_literature_review(topic, selected_papers, review_type)
    if review.get("status") != "success":
        return review.get("message", "Unable to generate review.")
    return review["review"]
