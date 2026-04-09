# ScholarAI

ScholarAI is a simple research paper assistant with a React frontend and a FastAPI backend. It searches arXiv, summarizes selected papers through a remote summary agent, generates a lightweight literature review draft, creates citations from the current paper list, and can save or load paper collections from Azure Blob Storage.

## Project Overview

- Azure Blob Storage is used to save and load paper collections as JSON.
- The Summary Agent runs remotely on a separate server for A2A practice.
- The app stays intentionally lightweight and local-first.

## Agents

- Coordinator Agent handles the remote summary call and shared backend flow coordination.
- Search Agent queries arXiv through a shared MCP tool.
- Summary Agent runs remotely and returns paper summaries.
- Review Agent generates a lightweight literature review draft and can also use the shared MCP tool.
- Citation Agent creates citations from the current search results.

## MCP Integration

- The project includes one minimal shared MCP tool: `shared_paper_search`.
- That MCP tool is registered in [`backend/tools/custom_tools.py`]
- It is used by two agents:
  Search Agent in [`backend/agents/search_agent.py`]
  Review Agent in [`backend/agents/review_agent.py`]
- The MCP layer is intentionally simple and local, using:
  [`backend/mcp/server.py`]
  [`backend/mcp/client.py`]

## Project Structure

ScholarAI/
|-- backend/
| |-- agents/
| | |-- **init**.py
| | |-- citation_agent.py
| | |-- coordinator_agent.py
| | |-- review_agent.py
| | |-- search_agent.py
| | `-- summary_agent_remote.py
|   |-- tools/
|   |   |-- __init__.py
|   |   `-- custom_tools.py
| |-- main.py
| `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- App.css
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
| |-- package.json
| `-- vite.config.js
`-- README.md

## Backend Setup

```powershell
cd backend
python -m pip install -r requirements.txt
```

```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```

Optional: start the remote summary service used by `/summarize` before fallback kicks in:

```powershell
cd backend
python -m agents.summary_agent_remote
```

## Backend Setup

```powershell
cd frontend
npm run dev
```

App URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Remote summary service: `http://localhost:8001`

## Steps Walkthrough

1. Set up the project structure and install dependencies for FastAPI, React, and Azure Blob Storage.
2. Run the FastAPI backend in `backend/main.py`.
3. Run the remote Summary Agent in `backend/agents/summary_agent_remote.py`.
4. Use the React frontend to search, summarize, draft a review, generate citations, and manage a saved collection.
5. Optionally refine the app later with Foundry-hosted models or richer MCP integrations.
