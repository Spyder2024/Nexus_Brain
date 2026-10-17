"""Strict Pydantic v2 Models for Multi-Agent Coordination and API Contracts.

Implements TRD.md Section 6 JSON contract:
- AgentTraceStep
- CitationItem
- SubgraphNode
- SubgraphEdge
- SubgraphPayload
- AgentQueryResponse
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AgentTraceStep(BaseModel):
    """Telemetry trace for a single agent tool execution step."""
    model_config = ConfigDict(extra="ignore")

    agent: str = Field(..., description="Agent name (e.g. RouterAgent, GraphNavigator, MemoryScribe)")
    tool: str = Field(..., description="Deterministic tool name invoked")
    cypher_executed: str = Field(..., description="Exact Cypher query executed against FalkorDB")
    latency_ms: float = Field(..., description="Query latency in milliseconds")


class CitationItem(BaseModel):
    """Reference citation for graph entity backing an agent response."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Entity ID (e.g. ADR-051, DOC-082, person-19)")
    label: str = Field(..., description="Entity node label (e.g. Decision, Document, System, Person)")
    title: str = Field(..., description="Entity title, name, or headline")
    status: Optional[str] = Field(None, description="active, superseded, outdated, etc.")
    source_ref: Optional[str] = Field(None, description="Linked incident or thread reference")


class SubgraphNode(BaseModel):
    """Node visualization datum for force-directed visualizer."""
    model_config = ConfigDict(extra="ignore")

    id: str
    label: str
    type: str
    status: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class SubgraphEdge(BaseModel):
    """Edge visualization datum for force-directed visualizer."""
    model_config = ConfigDict(extra="ignore")

    source: str
    target: str
    relationship: str


class SubgraphPayload(BaseModel):
    """Exploration subgraph containing traversed nodes and edges."""
    model_config = ConfigDict(extra="ignore")

    nodes: List[SubgraphNode] = Field(default_factory=list)
    edges: List[SubgraphEdge] = Field(default_factory=list)


class AgentQueryResponse(BaseModel):
    """Strict API response model matching TRD.md Section 6."""
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(..., description="Markdown-formatted answer with inline [ID] citations")
    tenant_graph: str = Field(..., description="FalkorDB tenant graph identifier")
    agent_trace: List[AgentTraceStep] = Field(default_factory=list, description="Execution traces")
    citations: List[CitationItem] = Field(default_factory=list, description="Inline citations")
    subgraph: SubgraphPayload = Field(default_factory=SubgraphPayload, description="Visual subgraph")
