"""
Citation Agent for ScholarAI.
"""
import os
from dotenv import load_dotenv
from tools.custom_tools import generate_citations

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"), override=False)


async def run(papers: list[dict], style: str = "apa") -> dict:
    """Generate citations from available papers."""
    return await generate_citations(papers, style)
