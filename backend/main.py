from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(dotenv_path="config/.env", override=False)

# Add agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from agents.coordinator_agent import citations, review, search, summarize
from tools.custom_tools import save_to_blob, load_from_blob

app = FastAPI(title="ScholarAI Backend", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

class SummarizeRequest(BaseModel):
    paper_id: str
    abstract: str = ""

class CitationRequest(BaseModel):
    papers: list[dict] = Field(default_factory=list)
    style: str = "apa"

class ReviewRequest(BaseModel):
    papers: list[dict] = Field(default_factory=list)
    query: str
    review_type: str = "narrative"

class CollectionSaveRequest(BaseModel):
    collection: list[dict]
    container_name: str = "scholarai"
    blob_name: str = "collection.json"

class CollectionLoadRequest(BaseModel):
    container_name: str = "scholarai"
    blob_name: str = "collection.json"

@app.get("/")
async def root():
    return {"message": "ScholarAI Backend Running", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Search Agent Endpoint
@app.post("/search")
async def search_papers(request: SearchRequest):
    try:
        result = await search(request.query, request.max_results)
        if result.get("status") != "success":
            raise HTTPException(status_code=502, detail=result.get("message", "Search failed"))
        return {"status": "success", "results": result.get("papers", [])}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Summarize Paper Endpoint (calls remote Summary Agent via A2A)
@app.post("/summarize")
async def summarize_paper(request: SummarizeRequest):
    try:
        result = await summarize(request.paper_id, request.abstract)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Citation Endpoint
@app.post("/citations")
async def generate_citations(request: CitationRequest):
    try:
        result = await citations(request.papers, request.style)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generate Review Endpoint
@app.post("/review")
async def generate_review(request: ReviewRequest):
    try:
        result = await review(request.query, request.review_type, request.papers)
        return {"status": "success", "review": result}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Save collection directly to Azure Blob Storage
@app.post("/collection/save")
async def save_collection(request: CollectionSaveRequest):
    try:
        result = await save_to_blob(
            {"collection": request.collection},
            request.container_name,
            request.blob_name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Load collection from Azure Blob Storage
@app.post("/collection/load")
async def load_collection(request: CollectionLoadRequest):
    try:
        result = await load_from_blob(request.container_name, request.blob_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
