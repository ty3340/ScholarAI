"""
Custom tools for ScholarAI agents.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import requests
from mcp.server import mcp_server


def _trim_text(value: str, length: int) -> str:
    text = " ".join((value or "").split())
    return f"{text[:length]}..." if len(text) > length else text

# Tool 1: ArXiv Search
async def search_arxiv(query: str, max_results: int = 5) -> dict:
    """
    Search for research papers on ArXiv
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with search results containing paper metadata
    """
    base_urls = [
        "https://export.arxiv.org/api/query?",
        "https://arxiv.org/api/query?",
    ]
    encoded_query = quote_plus(query)
    search_query = (
        f"search_query=all:{encoded_query}&start=0&max_results={max_results}"
        "&sortBy=relevance&sortOrder=descending"
    )

    headers = {
        "User-Agent": "ScholarAI/1.0 (local development app)",
        "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    }
    try:
        response = None
        last_error = None
        for base_url in base_urls:
            request_url = base_url + search_query
            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(
                        requests.get,
                        request_url,
                        headers=headers,
                        timeout=(5, 25),
                    )
                    if response.status_code != 429:
                        break
                    last_error = requests.HTTPError(
                        "arXiv rate limit",
                        response=response,
                    )
                    if attempt < 2:
                        await asyncio.sleep(1.5 * (attempt + 1))
                except requests.Timeout as exc:
                    last_error = exc
                    if attempt < 2:
                        await asyncio.sleep(1.5 * (attempt + 1))
                except requests.RequestException as exc:
                    last_error = exc
                    break

            if response is not None and response.ok:
                break

        if response is None:
            if isinstance(last_error, requests.Timeout):
                return {
                    "status": "error",
                    "message": "arXiv took too long to respond. Please try again in a moment.",
                }
            return {"status": "error", "message": "No response received from arXiv."}

        response.raise_for_status()
        
        # Parse XML response (simplified)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            paper = {
                "title": (entry.find("{http://www.w3.org/2005/Atom}title").text or "").strip(),
                "authors": [author.find("{http://www.w3.org/2005/Atom}name").text 
                           for author in entry.findall("{http://www.w3.org/2005/Atom}author")],
                "summary": (entry.find("{http://www.w3.org/2005/Atom}summary").text or "").strip(),
                "published": entry.find("{http://www.w3.org/2005/Atom}published").text,
                "arxiv_id": entry.find("{http://www.w3.org/2005/Atom}id").text.split("/abs/")[-1],
            }
            papers.append(paper)
        
        return {"status": "success", "count": len(papers), "papers": papers}
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return {
                "status": "error",
                "message": "arXiv is rate-limiting requests right now. Wait a moment and try again.",
            }
        return {"status": "error", "message": str(e)}
    except requests.Timeout:
        return {
            "status": "error",
            "message": "arXiv took too long to respond. Please try again in a moment.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Tool 2: Blob Storage Upload
async def save_to_blob(data: dict, container_name: str = "scholarai", blob_name: Optional[str] = None) -> dict:
    """
    Save data to Azure Blob Storage
    
    Args:
        data: Dictionary to save (will be converted to JSON)
        container_name: Name of the blob container
        blob_name: Name for the blob file (auto-generated if None)
        
    Returns:
        Dictionary with status and blob info
    """
    from azure.storage.blob import BlobServiceClient
    
    try:
        if not blob_name:
            blob_name = f"scholarai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            return {
                "status": "error",
                "message": "AZURE_STORAGE_CONNECTION_STRING is not configured.",
            }

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(blob_name)
        payload = json.dumps(data, indent=2)
        blob_client.upload_blob(payload, overwrite=True)

        return {
            "status": "success",
            "blob_name": blob_name,
            "container": container_name,
            "message": f"Data saved to {container_name}/{blob_name}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def load_from_blob(container_name: str = "scholarai", blob_name: str = "collection.json") -> dict:
    """
    Load JSON content from Azure Blob Storage.
    """
    from azure.storage.blob import BlobServiceClient

    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection_string:
            return {
                "status": "error",
                "message": "AZURE_STORAGE_CONNECTION_STRING is not configured.",
            }

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            return {
                "status": "error",
                "message": f"Container '{container_name}' does not exist.",
            }

        blob_client = container_client.get_blob_client(blob_name)
        if not blob_client.exists():
            return {
                "status": "error",
                "message": f"Blob '{blob_name}' does not exist in container '{container_name}'.",
            }

        content = blob_client.download_blob().readall()
        data = json.loads(content)
        return {
            "status": "success",
            "blob_name": blob_name,
            "container": container_name,
            "data": data,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Tool 3: Generate Paper Summary
async def summarize_paper_content(paper_id: str, abstract: str) -> dict:
    """
    Generate a summary of paper content
    
    Args:
        paper_id: ArXiv paper ID
        abstract: Paper abstract from ArXiv
        
    Returns:
        Summary data
    """
    return {
        "status": "success",
        "paper_id": paper_id,
        "summary": (
            f"Paper {paper_id} focuses on: {abstract[:300]}{'...' if len(abstract) > 300 else ''}"
            if abstract.strip()
            else f"No abstract was provided for {paper_id}."
        ),
        "abstract_length": len(abstract)
    }


async def generate_literature_review(topic: str, papers: list[dict], review_type: str = "narrative") -> dict:
    """
    Generate a more structured literature review from the provided paper summaries.
    """
    if not papers:
        return {
            "status": "error",
            "message": "No papers were provided to build a literature review.",
        }

    publication_years = [paper.get("published", "")[:4] for paper in papers if paper.get("published")]
    year_span = ""
    if publication_years:
        year_span = f" The sampled papers span {min(publication_years)} to {max(publication_years)}."

    def classify_theme(summary: str) -> str:
        text = (summary or "").lower()
        if any(keyword in text for keyword in ["transformer", "attention", "bert", "gpt", "llm"]):
            return "Large language models and transformers"
        if any(keyword in text for keyword in ["deep learning", "neural network", "cnn", "rnn", "lstm"]):
            return "Deep learning architectures"
        if any(keyword in text for keyword in ["reinforcement", "policy", "agent", "reward"]):
            return "Reinforcement learning"
        if any(keyword in text for keyword in ["optimization", "gradient", "loss", "training"]):
            return "Optimization and training methods"
        if any(keyword in text for keyword in ["survey", "review", "meta-analysis"]):
            return "Surveys and review articles"
        return "Application and evaluation"

    themes = {}
    for paper in papers:
        theme = classify_theme(paper.get("summary", ""))
        themes[theme] = themes.get(theme, 0) + 1

    theme_lines = [f"- {theme}: {count} paper(s)" for theme, count in sorted(themes.items(), key=lambda item: -item[1])]

    sorted_by_year = sorted(
        [paper for paper in papers if paper.get("published")],
        key=lambda paper: paper.get("published", ""),
    )
    timeline_lines = []
    for paper in sorted_by_year[:5]:
        year = paper.get("published", "")[:4]
        title = paper.get("title", "Untitled paper")
        timeline_lines.append(f"- {year}: {title}")

    review_lines = [
        f"This {review_type} literature review surveys {len(papers)} papers related to {topic}.{year_span}",
        "",
        "Development timeline:",
    ]
    review_lines.extend(timeline_lines or ["- No publication dates available."])
    review_lines.extend([
        "",
        "Key themes identified:",
    ])
    review_lines.extend(theme_lines)
    review_lines.extend([
        "",
        "Representative papers:",
    ])

    for paper in papers[:5]:
        title = paper.get("title", "Untitled paper")
        summary = _trim_text(paper.get("summary", ""), 180)
        year = paper.get("published", "")[:4]
        review_lines.append(f"- ({year}) {title}: {summary}")

    review_lines.extend([
        "",
        "Synthesis:",
        f"The literature on {topic} shows that research has evolved over time, with emerging themes focused on the highest-frequency topics above.",
        "Recent work tends to emphasize applied evaluation scenarios and model performance, while earlier papers often focus on foundational methods and architecture design.",
        "",
        "Current gaps and opportunities:",
        "- Comparative evaluation is often limited by varying datasets and metrics.",
        "- Reproducibility details are frequently incomplete, especially for newer model variants.",
        "- Few papers combine longitudinal perspectives with systematic comparison across study designs.",
        "",
        "Suggested next step:",
        "Construct a structured review table listing each paper's research question, method, dataset, metrics, and limitations; then use that table to write a cohesive narrative of how the topic has developed.",
    ])

    return {"status": "success", "review": "\n".join(review_lines)}


async def generate_citations(papers: list[dict], style: str = "apa") -> dict:
    """
    Generate simple citations from the current paper list.
    """
    if not papers:
        return {"status": "error", "message": "No papers were provided to cite."}

    normalized_style = (style or "apa").lower()
    citations = []
    for paper in papers[:10]:
        authors = paper.get("authors", [])
        year = (paper.get("published", "") or "n.d.")[:4]
        title = (paper.get("title", "Untitled paper") or "Untitled paper").strip()
        arxiv_id = paper.get("arxiv_id", "")
        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

        if authors:
            if len(authors) == 1:
                author_text = authors[0]
            elif len(authors) == 2:
                author_text = f"{authors[0]} & {authors[1]}"
            else:
                author_text = f"{authors[0]} et al."
        else:
            author_text = "Unknown author"

        if normalized_style == "mla":
            citation = f'{author_text}. "{title}." arXiv, {year}, {url}'.strip()
        else:
            citation = f"{author_text} ({year}). {title}. arXiv. {url}".strip()

        citations.append(citation)

    return {
        "status": "success",
        "style": normalized_style,
        "citations": citations,
        "formatted": "\n".join(f"{index + 1}. {citation}" for index, citation in enumerate(citations)),
    }


mcp_server.register_tool("shared_paper_search", search_arxiv)
