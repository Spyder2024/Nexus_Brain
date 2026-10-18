"""API Request & Response Schemas for NexusBrain.

Strictly adheres to DEV_B_SPEC_v2.md and TRD.md Section 6.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.schema.models import AgentQueryResponse, Subgraph


class HealthResponse(BaseModel):
    status: str = Field(default="awake")
    falkordb_connected: bool
    seeded: bool
    mode: str = Field(description="'live' or 'mock'")
    timestamp: str


class StatsResponse(BaseModel):
    mode: str = Field(description="'live' or 'mock'")
    nodes: int
    edges: int
    graphs: List[str]
    active_tenant_graph: str
    avg_query_ms: float


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., description="Active user persona: meera | kabir | riya")
    query: str = Field(..., min_length=1, description="Question or task for the Company Brain")
    session_id: Optional[str] = Field(default="sess_01", description="Session identifier")


class MutateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(default="meera", description="User initiating the architectural change")
    source_type: str = Field(default="SlackThread", description="SlackThread, Ticket, or PullRequest")
    channel: str = Field(default="#arch-sync", description="Originating channel")
    system_name: str = Field(default="auth-service", description="Governed system")
    new_decision_title: str = Field(..., min_length=1, description="Title for the new active ADR")
    supersedes_decision_id: str = Field(default="ADR-051", description="Prior ADR ID being invalidated")
    rationale: str = Field(..., min_length=1, description="Architectural reasoning and trade-offs")


class MutateResponse(BaseModel):
    new_decision: Dict[str, Any]
    superseded_decision: Dict[str, Any]
    subgraph: Subgraph
    latency_ms: float
    cypher_executed: str


class MemoryResponse(BaseModel):
    tenant_graph: str
    turns: List[Dict[str, Any]]
    playbooks: List[Dict[str, Any]]
    shared_playbooks: List[Dict[str, Any]]


class ResetResponse(BaseModel):
    reseeded: bool
    nodes: int
    edges: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
