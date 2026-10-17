/**
 * TypeScript mirror of TRD.md Section 6 and DEV_B_SPEC_v2.md contracts.
 */

export interface AgentTrace {
  agent: string;
  tool: string;
  cypher_executed: string;
  latency_ms: number;
}

export interface Citation {
  id: string;
  label: string;
  title: string;
  status?: string;
  source_ref?: string;
}

export interface SubgraphNode {
  id: string;
  label: string;
  type: string;
  status?: string;
  x?: number;
  y?: number;
}

export interface SubgraphEdge {
  source: string | SubgraphNode;
  target: string | SubgraphNode;
  relationship: string;
}

export interface Subgraph {
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
}

export interface QueryResponse {
  answer: string;
  tenant_graph: string;
  agent_trace: AgentTrace[];
  citations: Citation[];
  subgraph: Subgraph;
  llm_fallback?: boolean;
}

export interface HealthResponse {
  status: string;
  falkordb_connected: boolean;
  seeded: boolean;
  mode: "live" | "mock";
  timestamp: string;
}

export interface StatsResponse {
  mode: "live" | "mock";
  nodes: number;
  edges: number;
  graphs: string[];
  active_tenant_graph: string;
  avg_query_ms: number;
}

export interface MutateRequest {
  user_id: string;
  source_type: string;
  channel: string;
  system_name: string;
  new_decision_title: string;
  supersedes_decision_id: string;
  rationale: string;
}

export interface MutateResponse {
  new_decision: {
    id: string;
    title: string;
    status: string;
    system_id?: string;
    rationale?: string;
  };
  superseded_decision: {
    id: string;
    status: string;
    invalidated_at?: string;
  };
  subgraph: Subgraph;
  latency_ms: number;
  cypher_executed: string;
}

export interface MemoryTurn {
  turn_id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface Playbook {
  id: string;
  trigger_signature: string;
  resolution_steps: string[];
  verified_by?: string;
  verified_by_ticket_id?: string;
  success_count: number;
}

export interface MemoryResponse {
  tenant_graph: string;
  turns: MemoryTurn[];
  playbooks: Playbook[];
  shared_playbooks: Playbook[];
}

export interface Persona {
  id: "meera" | "kabir" | "riya";
  name: string;
  role: string;
  avatar: string;
}
