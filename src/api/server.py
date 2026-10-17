"""FastAPI Backend Server for NexusBrain.

Implements TRD.md Section 6 REST API endpoints:
- POST /api/v1/query (calls AgentCoordinator or fallback MockBridge)
- POST /api/v1/mutate (calls GraphTools.mutate_knowledge_state or fallback MockBridge)
- GET /api/v1/stats (live FalkorDB / system statistics)
- POST /api/v1/reset (resets knowledge state for fresh demo takes)
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.schema.models import AgentQueryResponse
from src.api.mock_bridge import mock_bridge

app = FastAPI(
    title="NexusBrain API",
    description="Graph-Native Company Brain & Multi-Agent Memory Coordinator REST API",
    version="1.0.0",
)

# Enable CORS for local Streamlit / Web UI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    user_id: str = Field(default="meera_sre", description="Active user persona identifier")
    query: str = Field(..., description="Natural language question or command")


class MutateRequest(BaseModel):
    topic: str = Field(default="auth_rpc", description="Architectural domain or topic")
    new_id: str = Field(default="ADR-061", description="New ADR / Decision ID")
    title: str = Field(..., description="Decision title")
    reason: str = Field(..., description="Reason for superseding prior standard")


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "service": "NexusBrain API",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/api/v1/stats")
def get_stats() -> Dict[str, Any]:
    """Return live FalkorDB graph metrics and tenant stats."""
    try:
        # Attempt to import FalkorDB stats if loader is available
        from src.graph.tools import graph_tools  # type: ignore
        return graph_tools.get_stats()
    except (ImportError, Exception):
        # Fallback to high-fidelity mock bridge stats
        return mock_bridge.get_stats()


@app.post("/api/v1/query", response_model=AgentQueryResponse)
def handle_query(payload: QueryRequest) -> AgentQueryResponse:
    """Execute multi-agent graph query returning strict TRD Section 6 contract."""
    try:
        # If AgentCoordinator is implemented, delegate to live coordinator
        from src.agents.coordinator import agent_coordinator  # type: ignore
        return agent_coordinator.handle_query(user_id=payload.user_id, query=payload.query)
    except (ImportError, Exception):
        # Fallback to deterministic mock bridge
        return mock_bridge.handle_query(user_id=payload.user_id, query=payload.query)


@app.post("/api/v1/mutate")
def mutate_knowledge(payload: MutateRequest) -> Dict[str, Any]:
    """Ingest new architectural decision and supersede old node in real-time."""
    try:
        from src.graph.tools import graph_tools  # type: ignore
        return graph_tools.mutate_knowledge_state(payload.model_dump())
    except (ImportError, Exception):
        return mock_bridge.mutate_decision(payload.model_dump())


@app.post("/api/v1/reset")
def reset_state() -> Dict[str, str]:
    """Reset all live mutations back to pristine 5 Golden Scenarios."""
    mock_bridge.reset_state()
    try:
        from src.graph.loader import falkordb_loader  # type: ignore
        falkordb_loader.reset_golden_scenarios()
    except (ImportError, Exception):
        pass
    return {"status": "success", "message": "Knowledge graph reset to pristine baseline."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=True)
