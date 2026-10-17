"""Pydantic v2 Graph Schemas for NexusBrain.

Defines all 8 Node types, GraphEdge schema with validated relation types,
and the unified GraphBundle container for "7bit Cloud Technologies".
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class NodeType(str, Enum):
    """Supported Graph Node Labels."""
    TEAM = "Team"
    PERSON = "Person"
    SYSTEM = "System"
    TICKET = "Ticket"
    PULL_REQUEST = "PullRequest"
    SLACK_THREAD = "SlackThread"
    DOCUMENT = "Document"
    DECISION = "Decision"


class RelationType(str, Enum):
    """Supported Graph Edge Relationship Types."""
    # Organization & Ownership
    MEMBER_OF = "MEMBER_OF"
    LEADS = "LEADS"
    OWNS = "OWNS"
    MAINTAINS = "MAINTAINS"
    DEPENDS_ON = "DEPENDS_ON"

    # Incidents & Tickets
    REPORTED = "REPORTED"
    ASSIGNED_TO = "ASSIGNED_TO"
    AFFECTS = "AFFECTS"
    CAUSED_BY = "CAUSED_BY"

    # Development & Code
    AUTHORED = "AUTHORED"
    REVIEWED = "REVIEWED"
    IMPLEMENTS = "IMPLEMENTS"
    RESOLVES = "RESOLVES"
    MODIFIES = "MODIFIES"

    # Discussions & Decision Dynamics
    PARTICIPATED_IN = "PARTICIPATED_IN"
    DISCUSSES = "DISCUSSES"
    TRIGGERED_DECISION = "TRIGGERED_DECISION"

    # Knowledge Evolution & Conflict Resolution
    SUPERSEDES = "SUPERSEDES"
    CONTRADICTS = "CONTRADICTS"
    GUIDES_RESOLUTION_OF = "GUIDES_RESOLUTION_OF"


class SystemTier(str, Enum):
    TIER_0 = "Tier-0"  # Critical Core (e.g. Auth, Redis, Kafka)
    TIER_1 = "Tier-1"  # Business Core (e.g. Billing, Gateway, ML Inference)
    TIER_2 = "Tier-2"  # Supporting Services (e.g. Admin Console, Ingest)
    TIER_3 = "Tier-3"  # Utility / Internal Tools (e.g. Cost Optimizer)


class TicketType(str, Enum):
    INCIDENT = "incident"
    BUG = "bug"
    FEATURE = "feature"
    TECH_DEBT = "tech_debt"


class TicketSeverity(str, Enum):
    SEV_1 = "SEV-1"  # Outage / Critical
    SEV_2 = "SEV-2"  # Major Degraded
    SEV_3 = "SEV-3"  # Moderate Impact
    SEV_4 = "SEV-4"  # Low / Minor


class DocType(str, Enum):
    RUNBOOK = "runbook"
    RFC = "rfc"
    POSTMORTEM = "postmortem"
    ONBOARDING = "onboarding"


class DocStatus(str, Enum):
    ACTIVE = "active"
    OUTDATED = "outdated"


class DecisionStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Node Models
# ---------------------------------------------------------------------------

class Team(BaseModel):
    """Team entity representing organizational units."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique team identifier, e.g. team-core-platform")
    name: str = Field(..., description="Human readable team name")
    department: str = Field(..., description="Parent department")
    lead_id: str = Field(..., description="Person ID of the team lead")
    slack_channel: str = Field(..., description="Team Slack channel handle, e.g. #core-platform")


class Person(BaseModel):
    """Person entity representing engineers, leads, and staff."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique person identifier, e.g. person-01")
    name: str = Field(..., description="Full name")
    role: str = Field(..., description="Job role, e.g. Senior Software Engineer")
    seniority: str = Field(..., description="Seniority level, e.g. Staff, Senior, Mid, Junior")
    team_id: str = Field(..., description="Primary team ID")
    skills: List[str] = Field(default_factory=list, description="Core technical competencies")
    joined_date: str = Field(..., description="ISO date of joining")
    active: bool = Field(default=True, description="Whether currently active at company")


class System(BaseModel):
    """System entity representing microservices, infrastructure, and core data stores."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique system identifier, e.g. auth-service")
    name: str = Field(..., description="Human readable service name")
    tier: str = Field(..., description="Service criticality tier (Tier-0 to Tier-3)")
    language: str = Field(..., description="Primary implementation language/runtime")
    repo_url: str = Field(..., description="Git repository URL")
    owner_team_id: str = Field(..., description="Owning team ID")
    primary_maintainer_id: str = Field(..., description="Person ID of primary maintainer")


class Ticket(BaseModel):
    """Ticket entity representing Jira/Linear incidents, bugs, features, and tech debt."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique ticket identifier, e.g. INC-108 or TICKET-205")
    title: str = Field(..., description="Summary headline")
    type: str = Field(..., description="incident, bug, feature, or tech_debt")
    severity: str = Field(..., description="SEV-1, SEV-2, SEV-3, or SEV-4")
    status: str = Field(..., description="resolved, in_progress, open, closed")
    created_at: str = Field(..., description="ISO timestamp of creation")
    resolved_at: Optional[str] = Field(None, description="ISO timestamp of resolution")
    reporter_id: str = Field(..., description="Person ID who filed the ticket")
    assignee_id: str = Field(..., description="Person ID assigned to resolve")
    affected_system_id: str = Field(..., description="System ID directly experiencing symptoms")
    root_cause_system_id: Optional[str] = Field(None, description="System ID identifying root cause failure")
    summary: str = Field(..., description="Detailed technical summary of ticket/incident")


class PullRequest(BaseModel):
    """PullRequest entity representing GitHub/GitLab pull requests."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique PR identifier, e.g. PR-398")
    title: str = Field(..., description="PR title")
    author_id: str = Field(..., description="Person ID of the PR author")
    reviewer_ids: List[str] = Field(default_factory=list, description="Person IDs of code reviewers")
    system_id: str = Field(..., description="Target System ID being modified")
    linked_ticket_id: Optional[str] = Field(None, description="Associated Ticket ID if any")
    merged_at: Optional[str] = Field(None, description="ISO timestamp when merged")
    files_changed: List[str] = Field(default_factory=list, description="List of file paths changed")
    commit_summary: str = Field(..., description="Technical overview of changes introduced")


class SlackMessage(BaseModel):
    """Sub-message within an unstructured Slack thread."""
    sender_id: str
    timestamp: str
    text: str


class SlackThread(BaseModel):
    """SlackThread entity representing unstructured conversations, war-rooms, and design debates."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique thread identifier, e.g. SLACK-088")
    channel: str = Field(..., description="Slack channel name, e.g. #incident-war-room")
    started_at: str = Field(..., description="ISO timestamp thread started")
    participant_ids: List[str] = Field(default_factory=list, description="List of Person IDs in discussion")
    messages: List[SlackMessage] = Field(default_factory=list, description="Chronological messages in thread")
    transcript: Optional[str] = Field(None, description="Concatenated conversation transcript")
    linked_ticket_id: Optional[str] = Field(None, description="Associated Ticket ID if discussed")
    linked_decision_id: Optional[str] = Field(None, description="Associated ADR ID if discussed")


class Document(BaseModel):
    """Document entity representing Runbooks, RFCs, Postmortems, and Onboarding Guides."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique document identifier, e.g. DOC-012")
    title: str = Field(..., description="Document title")
    doc_type: str = Field(..., description="runbook, rfc, postmortem, or onboarding")
    author_id: str = Field(..., description="Person ID of the primary document author")
    system_id: Optional[str] = Field(None, description="Associated System ID")
    last_updated: str = Field(..., description="ISO date or timestamp last edited")
    status: str = Field(..., description="active or outdated")
    content: str = Field(..., description="Full text technical content or instructions")


class Decision(BaseModel):
    """Decision entity representing Architecture Decision Records (ADRs)."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique ADR identifier, e.g. ADR-051")
    title: str = Field(..., description="ADR title")
    topic: str = Field(..., description="Domain/topic, e.g. Inter-Service RPC Protocol")
    status: str = Field(..., description="active or superseded")
    decided_at: str = Field(..., description="ISO timestamp when decision took effect")
    invalidated_at: Optional[str] = Field(None, description="ISO timestamp when superseded/invalidated")
    author_id: str = Field(..., description="Person ID of the ADR architect/author")
    system_id: str = Field(..., description="Target System ID governed by this decision")
    source_slack_id: Optional[str] = Field(None, description="Linked Slack thread ID that spawned decision")
    source_ticket_id: Optional[str] = Field(None, description="Linked Ticket ID that catalyzed decision")
    supersedes_decision_id: Optional[str] = Field(None, description="Previous ADR ID that this decision invalidates")
    rationale: str = Field(..., description="Architectural reasoning and trade-off analysis")


# ---------------------------------------------------------------------------
# Edge Model & Unified Bundle
# ---------------------------------------------------------------------------

class GraphEdge(BaseModel):
    """GraphEdge entity representing directed relationships between nodes."""
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Identifier of source node")
    source_label: str = Field(..., description="Label/Type of source node")
    target_id: str = Field(..., description="Identifier of target node")
    target_label: str = Field(..., description="Label/Type of target node")
    relation_type: str = Field(..., description="Relationship type enum value")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Attributes e.g. timestamp, status, weight, source_ref",
    )


class GraphBundle(BaseModel):
    """Unified container containing all nodes and edges in the enterprise knowledge graph."""
    teams: List[Team] = Field(default_factory=list)
    people: List[Person] = Field(default_factory=list)
    systems: List[System] = Field(default_factory=list)
    tickets: List[Ticket] = Field(default_factory=list)
    pull_requests: List[PullRequest] = Field(default_factory=list)
    slack_threads: List[SlackThread] = Field(default_factory=list)
    documents: List[Document] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tenant Memory Models (TRD.md Section 4.2)
# ---------------------------------------------------------------------------

class Session(BaseModel):
    """Episodic Session entity representing interactive user interactions."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique session identifier, e.g. session-001")
    user_id: str = Field(..., description="Tenant user persona ID, e.g. user-kabir")
    started_at: str = Field(..., description="ISO timestamp of session initiation")


class Turn(BaseModel):
    """Conversation turn stored in tenant episodic memory."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique turn identifier, e.g. turn-001")
    session_id: str = Field(..., description="Parent session ID")
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message text")
    timestamp: str = Field(..., description="ISO timestamp")
    referenced_node_ids: List[str] = Field(default_factory=list, description="IDs of graph nodes cited in turn")


class Playbook(BaseModel):
    """Procedural troubleshooting playbook learned by agents."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique playbook identifier, e.g. playbook-001")
    trigger_signature: str = Field(..., description="Pattern/signature of issue")
    resolution_steps: List[str] = Field(default_factory=list, description="Ordered mitigation actions")
    verified_by_ticket_id: Optional[str] = Field(None, description="Ticket ID verifying playbook effectiveness")
    success_count: int = Field(default=1, description="Times successfully applied")


# ---------------------------------------------------------------------------
# Strict API Contract Models (TRD.md Section 6)
# ---------------------------------------------------------------------------

class AgentTrace(BaseModel):
    """Telemetry trace for a single agent tool execution step."""
    model_config = ConfigDict(extra="forbid")

    agent: str = Field(..., description="Agent name (e.g. RouterAgent, GraphNavigator)")
    tool: str = Field(..., description="Deterministic tool name invoked")
    cypher_executed: str = Field(..., description="Exact Cypher query executed against FalkorDB")
    latency_ms: float = Field(..., description="Query latency in milliseconds")


class Citation(BaseModel):
    """Reference citation for graph entity backing an agent response."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Entity ID")
    label: str = Field(..., description="Entity node type (e.g. Decision, Document, System)")
    title: str = Field(..., description="Entity title or headline")
    status: Optional[str] = Field(None, description="active, superseded, outdated, etc.")
    source_ref: Optional[str] = Field(None, description="Linked incident or thread reference")


class SubgraphNode(BaseModel):
    """Node visualization datum for force-directed visualizer."""
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    type: str
    status: Optional[str] = None


class SubgraphEdge(BaseModel):
    """Edge visualization datum for force-directed visualizer."""
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    relationship: str


class Subgraph(BaseModel):
    """Exploration subgraph containing traversed nodes and edges."""
    model_config = ConfigDict(extra="forbid")

    nodes: List[SubgraphNode] = Field(default_factory=list)
    edges: List[SubgraphEdge] = Field(default_factory=list)


class AgentQueryResponse(BaseModel):
    """Strict API response model matching TRD.md Section 6."""
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(..., description="Markdown-formatted answer with inline [ID] citations")
    tenant_graph: str = Field(..., description="FalkorDB tenant graph identifier")
    agent_trace: List[AgentTrace] = Field(default_factory=list, description="Execution traces")
    citations: List[Citation] = Field(default_factory=list, description="Inline citations")
    subgraph: Subgraph = Field(default_factory=Subgraph, description="Visual subgraph")
