"""
Summary Agent - lightweight remote HTTP service for paper summaries.
"""
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from tools.custom_tools import summarize_paper_content

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"), override=False)

app = FastAPI(title="ScholarAI Summary Agent", version="1.0.0")


@app.post("/run")
async def run_summary(request: dict):
    return await summarize_paper_content(
        request.get("paper_id", ""),
        request.get("abstract", ""),
    )


async def main():
    """Start the Summary Agent as an HTTP server."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Run the remote agent server
    asyncio.run(main())
