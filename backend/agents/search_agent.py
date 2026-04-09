"""
Search Agent helper for ScholarAI.
"""
import os
from dotenv import load_dotenv
from mcp.client import mcp_client
from tools import custom_tools  # Ensures shared MCP tools are registered on import.

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"), override=False)

async def run(query: str, max_results: int = 5) -> dict:
    """Search for papers through a shared MCP tool."""
    return await mcp_client.call_tool(
        "shared_paper_search",
        query=query,
        max_results=max_results,
    )
