"""Mock Contract Bridge for NexusBrain.

Provides high-fidelity, deterministic responses for all 5 Golden Demo Scenarios
and dynamic fallback queries, strictly implementing TRD.md Section 6.
Guarantees the UI and API work seamlessly regardless of whether the LLM or live
FalkorDB database is connected.
"""

from typing import Dict, Any, Optional
from src.schema.models import (
    AgentQueryResponse,
    AgentTrace,
    Citation,
    Subgraph,
    SubgraphNode,
    SubgraphEdge,
)


class MockContractBridge:
    """Provides validated responses matching TRD.md Section 6."""

    def __init__(self) -> None:
        self._current_decision_state = {
            "auth_rpc": {
                "active_id": "ADR-051",
                "active_title": "Migrate auth-service RPC to gRPC Streaming",
                "superseded_id": "ADR-019",
                "superseded_title": "Use Kafka for synchronous inter-service RPC",
                "is_mutated": False,
            }
        }

    def reset_state(self) -> None:
        """Reset mutated mock state back to pristine Golden Scenarios."""
        self._current_decision_state["auth_rpc"] = {
            "active_id": "ADR-051",
            "active_title": "Migrate auth-service RPC to gRPC Streaming",
            "superseded_id": "ADR-019",
            "superseded_title": "Use Kafka for synchronous inter-service RPC",
            "is_mutated": False,
        }

    def mutate_decision(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate real-time knowledge mutation from Slack/Incident/PR."""
        topic = event_payload.get("topic", "auth_rpc")
        new_id = event_payload.get("new_id", "ADR-061")
        new_title = event_payload.get("title", "Move auth-service RPC to HTTP/3 QUIC")
        reason = event_payload.get("reason", "Envoy proxy bug INC-299 causing gRPC stream resets")

        old_id = self._current_decision_state.get(topic, {}).get("active_id", "ADR-051")
        self._current_decision_state[topic] = {
            "active_id": new_id,
            "active_title": new_title,
            "superseded_id": old_id,
            "superseded_title": self._current_decision_state.get(topic, {}).get("active_title", "gRPC Streaming"),
            "is_mutated": True,
            "reason": reason,
        }
        return {
            "status": "success",
            "mutated_node": new_id,
            "superseded_node": old_id,
            "timestamp": "2026-10-18T00:45:00Z",
            "message": f"Successfully created {new_id} (active) and superseded {old_id} in company_brain.",
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return live/simulated graph statistics."""
        return {
            "status": "online",
            "falkordb_host": "localhost:6379",
            "graphs": {
                "company_brain": {
                    "node_count": 1077,
                    "edge_count": 4103,
                    "status": "ready",
                },
                "memory_tenant_kabir": {"turns": 14, "playbooks": 3},
                "memory_tenant_meera": {"turns": 22, "playbooks": 5},
                "memory_tenant_riya": {"turns": 4, "playbooks": 5},
            },
            "p95_latency_ms": 3.8,
        }

    def handle_query(self, user_id: str, query: str) -> AgentQueryResponse:
        """Route query to corresponding Golden Scenario or dynamic responder."""
        query_lower = query.lower()

        # Scenario 1: Shadow Expert & Ownership
        if any(k in query_lower for k in ["shadow", "knows the most", "who actually knows", "outages", "expert"]):
            return self._scenario_1_shadow_expert(user_id)

        # Scenario 2 & 4: Temporal Decision Lineage / Kafka / HTTP/3
        if any(k in query_lower for k in ["kafka", "rpc", "doc-082", "doc-004", "onboarding doc", "adr"]):
            return self._scenario_2_decision_lineage(user_id)

        # Scenario 3: Cascading Blast Radius / Redis
        if any(k in query_lower for k in ["blast", "radius", "redis", "cascade", "downstream"]):
            return self._scenario_3_blast_radius(user_id)

        # Scenario 4: CUDA Memory Leak / Cross-Agent Memory
        if any(k in query_lower for k in ["cuda", "memory leak", "ml-inference", "recurring", "playbook"]):
            return self._scenario_4_cuda_memory(user_id)

        # Scenario 5: Undocumented API Breaking Change / PR-398
        if any(k in query_lower for k in ["pr-398", "breaking", "recommendation", "deserialization", "user-profile"]):
            return self._scenario_5_breaking_change(user_id)

        # Default Dynamic Graph Response
        return self._scenario_generic(user_id, query)

    def _scenario_1_shadow_expert(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 🔍 Subject-Matter Expert & Ownership Analysis for `auth-service`\n\n"
                "- **Official Owner:** **`person-04` (Devon Vance)** is listed in the org graph as Team Lead for *Auth & Identity* ([Team: team-auth]).\n"
                "- **Shadow Expert:** **`person-19` (Kavya Rao - Staff SRE)** is the true operational domain expert. Traversal reveals `person-19` has **resolved 18 critical SEV-1 incidents** and **authored 26 PRs** touching `auth-service` over the last 90 days.\n\n"
                "#### ⚠️ Cascading Blast Radius\n"
                "If `auth-service` fails, **3 downstream tier-0/tier-1 services** are immediately impacted:\n"
                "1. `checkout-orchestrator` (Payment & Billing)\n"
                "2. `user-profile-service` (Core Platform)\n"
                "3. `gateway-proxy` (Frontend Experience)\n\n"
                "> **Recommendation:** Page `person-19` directly for live incident triage."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Intent: SHADOW_EXPERT_LOOKUP)",
                    latency_ms=0.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="find_shadow_expert",
                    cypher_executed=(
                        "MATCH (s:System {id: 'auth-service'})<-[:OWNS]-(t:Team)<-[:LEADS]-(lead:Person) "
                        "OPTIONAL MATCH (p:Person)-[:AUTHORED|RESOLVES]->(item)-[:MODIFIES|AFFECTS]->(s) "
                        "RETURN lead.id, p.id, count(item) ORDER BY count(item) DESC LIMIT 5"
                    ),
                    latency_ms=3.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="calculate_blast_radius",
                    cypher_executed=(
                        "MATCH (s:System {id: 'auth-service'})<-[:DEPENDS_ON*1..3]-(downstream:System) "
                        "RETURN downstream.id, downstream.tier"
                    ),
                    latency_ms=2.9,
                ),
            ],
            citations=[
                Citation(id="person-04", label="Person", title="Devon Vance (Official Lead)", status="active"),
                Citation(id="person-19", label="Person", title="Kavya Rao (Top Contributor: 18 SEV-1s)", status="active"),
                Citation(id="auth-service", label="System", title="Auth & Token Validation Microservice", status="active"),
                Citation(id="checkout-orchestrator", label="System", title="Checkout Orchestrator", status="active"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="auth-service", label="auth-service", type="System", status="active"),
                    SubgraphNode(id="person-04", label="Devon Vance (Lead)", type="Person", status="active"),
                    SubgraphNode(id="person-19", label="Kavya Rao (SRE Expert)", type="Person", status="active"),
                    SubgraphNode(id="team-auth", label="Auth & Identity", type="Team", status="active"),
                    SubgraphNode(id="checkout-orchestrator", label="checkout-orchestrator", type="System", status="active"),
                ],
                edges=[
                    SubgraphEdge(source="team-auth", target="auth-service", relationship="OWNS"),
                    SubgraphEdge(source="person-04", target="team-auth", relationship="LEADS"),
                    SubgraphEdge(source="person-19", target="auth-service", relationship="RESOLVED_INCIDENTS"),
                    SubgraphEdge(source="checkout-orchestrator", target="auth-service", relationship="DEPENDS_ON"),
                ],
            ),
        )

    def _scenario_2_decision_lineage(self, user_id: str) -> AgentQueryResponse:
        state = self._current_decision_state["auth_rpc"]
        if state.get("is_mutated"):
            # Post-mutation state (HTTP/3)
            return AgentQueryResponse(
                answer=(
                    f"### 🛑 Temporal Decision Alert: `DOC-082` & `{state['superseded_id']}` are SUPERSEDED\n\n"
                    f"**DO NOT follow `DOC-082` (Kafka RPC) or `{state['superseded_id']}` (gRPC Streaming).**\n\n"
                    f"- **Current Active Policy:** **`{state['active_id']}` ({state['active_title']})**.\n"
                    f"- **Invalidated Decision:** `{state['superseded_id']}` was superseded due to `{state.get('reason', 'incident INC-299')}`.\n"
                    f"- **Historical Root:** Original Kafka RPC (`ADR-019`) was superseded after deadlock incident `INC-204` discussed in `#arch-sync` ([Slack: SLACK-088]).\n\n"
                    f"> **Action Required:** Implement HTTP/3 QUIC connection pools with mTLS."
                ),
                tenant_graph=f"memory_tenant_{user_id}",
                agent_trace=[
                    AgentTrace(
                        agent="RouterAgent",
                        tool="classify_intent",
                        cypher_executed="N/A (Intent: TEMPORAL_DECISION_LINEAGE)",
                        latency_ms=0.3,
                    ),
                    AgentTrace(
                        agent="GraphNavigator",
                        tool="trace_decision_lineage",
                        cypher_executed=(
                            "MATCH path = (latest:Decision {id: 'ADR-061'})-[:SUPERSEDES*1..3]->(old:Decision) "
                            "OPTIONAL MATCH (latest)-[:TRIGGERED_BY]->(inc:Ticket) "
                            "RETURN path, inc"
                        ),
                        latency_ms=4.1,
                    ),
                ],
                citations=[
                    Citation(id=state["active_id"], label="Decision", title=state["active_title"], status="active"),
                    Citation(id=state["superseded_id"], label="Decision", title=state["superseded_title"], status="superseded"),
                    Citation(id="ADR-019", label="Decision", title="Kafka RPC Policy", status="superseded"),
                    Citation(id="SLACK-088", label="SlackThread", title="#arch-sync consensus", status="active"),
                ],
                subgraph=Subgraph(
                    nodes=[
                        SubgraphNode(id=state["active_id"], label=f"{state['active_id']} (HTTP/3)", type="Decision", status="active"),
                        SubgraphNode(id=state["superseded_id"], label=f"{state['superseded_id']} (gRPC)", type="Decision", status="superseded"),
                        SubgraphNode(id="ADR-019", label="ADR-019 (Kafka)", type="Decision", status="superseded"),
                        SubgraphNode(id="DOC-082", label="DOC-082 (Onboarding)", type="Document", status="outdated"),
                    ],
                    edges=[
                        SubgraphEdge(source=state["active_id"], target=state["superseded_id"], relationship="SUPERSEDES"),
                        SubgraphEdge(source=state["superseded_id"], target="ADR-019", relationship="SUPERSEDES"),
                        SubgraphEdge(source="DOC-082", target="ADR-019", relationship="REFERENCES"),
                    ],
                ),
            )

        # Baseline state (gRPC Streaming active, Kafka superseded)
        return AgentQueryResponse(
            answer=(
                "### 🛑 Temporal Decision Alert: `DOC-082` is OUTDATED\n\n"
                "**DO NOT use Kafka for synchronous RPC as suggested in `DOC-082`.**\n\n"
                "- **Active Decision:** **`ADR-051` (Adopt gRPC Streaming for Inter-Service RPC)** is the current enterprise standard.\n"
                "- **Why it changed:** `ADR-019` (Use Kafka for RPC) was superseded after SEV-1 incident **`INC-204`** caused a distributed deadlock, as documented in war room **`SLACK-088`** (#arch-sync).\n\n"
                "> **Provenance Chain:** `DOC-082` ➡️ `ADR-019` (superseded) ⬅️ `[:SUPERSEDES]` ⬅️ **`ADR-051`** (active)."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Intent: TEMPORAL_DECISION_LINEAGE)",
                    latency_ms=0.5,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="trace_decision_lineage",
                    cypher_executed=(
                        "MATCH (doc:Document {id: 'DOC-082'})-[:REFERENCES]->(old:Decision) "
                        "OPTIONAL MATCH (current:Decision)-[:SUPERSEDES]->(old) "
                        "OPTIONAL MATCH (current)-[:DECIDED_IN]->(st:SlackThread) "
                        "RETURN doc, old, current, st"
                    ),
                    latency_ms=3.7,
                ),
            ],
            citations=[
                Citation(id="ADR-051", label="Decision", title="Adopt gRPC Streaming", status="active", source_ref="SLACK-088"),
                Citation(id="ADR-019", label="Decision", title="Kafka Synchronous RPC", status="superseded", source_ref="INC-204"),
                Citation(id="DOC-082", label="Document", title="Engineering Onboarding Guide", status="outdated"),
                Citation(id="INC-204", label="Ticket", title="SEV-1 Kafka RPC Deadlock", status="resolved"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="ADR-051", label="ADR-051 (gRPC Streaming)", type="Decision", status="active"),
                    SubgraphNode(id="ADR-019", label="ADR-019 (Kafka RPC)", type="Decision", status="superseded"),
                    SubgraphNode(id="DOC-082", label="DOC-082 (Onboarding)", type="Document", status="outdated"),
                    SubgraphNode(id="INC-204", label="INC-204 (Deadlock Outage)", type="Ticket", status="resolved"),
                ],
                edges=[
                    SubgraphEdge(source="ADR-051", target="ADR-019", relationship="SUPERSEDES"),
                    SubgraphEdge(source="DOC-082", target="ADR-019", relationship="REFERENCES"),
                    SubgraphEdge(source="INC-204", target="ADR-051", relationship="TRIGGERED_DECISION"),
                ],
            ),
        )

    def _scenario_3_blast_radius(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 💥 4-Hop Cascading Blast Radius for `redis-session-store`\n\n"
                "An OOM crash on `redis-session-store` (Tier-0) causes a severe 4-hop cascade across **3 organizational departments**:\n\n"
                "1. **Direct Failure (Hop 1):** `auth-token-validator` (Auth & Identity)\n"
                "2. **Cascading Failure (Hop 2):** `checkout-orchestrator` (Payment & Billing)\n"
                "3. **Cascading Failure (Hop 3):** `stripe-webhook-worker` (Payment & Billing)\n"
                "4. **Perimeter Impact (Hop 4):** `frontend-gateway` (Frontend Experience)\n\n"
                "#### 🚨 Teams to Page Immediately:\n"
                "- **SRE & Infra:** Team Lead `person-12`\n"
                "- **Auth & Identity:** Team Lead `person-04`\n"
                "- **Payment & Billing:** Team Lead `person-08`"
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Intent: BLAST_RADIUS_ANALYSIS)",
                    latency_ms=0.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="calculate_blast_radius",
                    cypher_executed=(
                        "MATCH path = (root:System {id: 'redis-session-store'})<-[:DEPENDS_ON*1..4]-(downstream:System) "
                        "OPTIONAL MATCH (downstream)<-[:OWNS]-(t:Team) "
                        "RETURN path, t.name, t.lead_id"
                    ),
                    latency_ms=4.8,
                ),
            ],
            citations=[
                Citation(id="redis-session-store", label="System", title="Core Redis Session Cluster", status="active"),
                Citation(id="auth-token-validator", label="System", title="Auth Token Validator", status="active"),
                Citation(id="checkout-orchestrator", label="System", title="Checkout Orchestration Engine", status="active"),
                Citation(id="stripe-webhook-worker", label="System", title="Stripe Async Webhook Processor", status="active"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="redis-session-store", label="redis-session-store (Root)", type="System", status="active"),
                    SubgraphNode(id="auth-token-validator", label="auth-token-validator", type="System", status="active"),
                    SubgraphNode(id="checkout-orchestrator", label="checkout-orchestrator", type="System", status="active"),
                    SubgraphNode(id="stripe-webhook-worker", label="stripe-webhook-worker", type="System", status="active"),
                ],
                edges=[
                    SubgraphEdge(source="auth-token-validator", target="redis-session-store", relationship="DEPENDS_ON"),
                    SubgraphEdge(source="checkout-orchestrator", target="auth-token-validator", relationship="DEPENDS_ON"),
                    SubgraphEdge(source="stripe-webhook-worker", target="checkout-orchestrator", relationship="DEPENDS_ON"),
                ],
            ),
        )

    def _scenario_4_cuda_memory(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 🧠 Cross-Agent Incident Memory: CUDA Leak on `ml-inference-worker`\n\n"
                "FalkorDB recalled prior incident **`INC-045`** (occurred 4 months ago) and active runbook **`DOC-012`**.\n\n"
                "- **Verified Playbook (`playbook-003`):**\n"
                "  1. Flush PyTorch CUDA cache via `torch.cuda.empty_cache()`.\n"
                "  2. Check worker pod env for `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.\n"
                "  3. Gracefully drain GPU worker queue `gpu-batch-04`.\n\n"
                "> **Tenant Memory Coordination:** This playbook was verified by SRE Lead **Meera** in session `session-meera-102` and automatically promoted to shared memory for all agents."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Intent: PROCEDURAL_PLAYBOOK_RECALL)",
                    latency_ms=0.3,
                ),
                AgentTrace(
                    agent="MemoryScribe",
                    tool="sync_agent_memory",
                    cypher_executed=(
                        f"MATCH (p:Playbook {{id: 'playbook-003'}})-[:APPLIES_TO]->(s:System {{id: 'ml-inference-worker'}}) "
                        "RETURN p.trigger_signature, p.resolution_steps, p.success_count"
                    ),
                    latency_ms=2.1,
                ),
            ],
            citations=[
                Citation(id="playbook-003", label="Playbook", title="CUDA OOM Mitigation Playbook", status="active"),
                Citation(id="DOC-012", label="Document", title="GPU Worker Recovery Runbook", status="active"),
                Citation(id="INC-045", label="Ticket", title="SEV-2 PyTorch Memory Fragmentation", status="resolved"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="ml-inference-worker", label="ml-inference-worker", type="System", status="active"),
                    SubgraphNode(id="playbook-003", label="CUDA Playbook (Verified)", type="Playbook", status="active"),
                    SubgraphNode(id="DOC-012", label="Runbook DOC-012", type="Document", status="active"),
                ],
                edges=[
                    SubgraphEdge(source="playbook-003", target="ml-inference-worker", relationship="APPLIES_TO"),
                    SubgraphEdge(source="DOC-012", target="ml-inference-worker", relationship="GOVERNS"),
                ],
            ),
        )

    def _scenario_5_breaking_change(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 🚨 Undocumented API Breaking Change: `PR-398` ➡️ `INC-250`\n\n"
                "- **Catalyst:** **`PR-398`** (*'Refactor UserProfile DTO to v2 protobuf'*) merged into `user-profile-service` without bumping major semantic version.\n"
                "- **Victim Service:** `recommendation-service` consumes the user profile stream directly. The missing `user_tier` field caused a deserialization panic (**`INC-250`**).\n"
                "- **Author:** `person-22` (Junior Developer) merged without required review from `person-15` (API Steward).\n\n"
                "> **Fix:** Roll back `PR-398` or deploy hotfix `PR-401` restoring backward compatibility."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Intent: CODE_PROVENANCE_TRACING)",
                    latency_ms=0.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="trace_code_provenance",
                    cypher_executed=(
                        "MATCH (pr:PullRequest {id: 'PR-398'})-[:MODIFIES]->(s:System) "
                        "MATCH (consumer:System)-[:DEPENDS_ON]->(s) "
                        "OPTIONAL MATCH (inc:Ticket)-[:CAUSED_BY]->(pr) "
                        "RETURN pr, s, consumer, inc"
                    ),
                    latency_ms=3.5,
                ),
            ],
            citations=[
                Citation(id="PR-398", label="PullRequest", title="Refactor UserProfile DTO", status="merged"),
                Citation(id="INC-250", label="Ticket", title="SEV-2 Recommendation Engine Crash", status="open"),
                Citation(id="user-profile-service", label="System", title="User Profile Service", status="active"),
                Citation(id="recommendation-service", label="System", title="Recommendation Engine", status="active"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="PR-398", label="PR-398 (Breaking)", type="PullRequest", status="merged"),
                    SubgraphNode(id="user-profile-service", label="user-profile-service", type="System", status="active"),
                    SubgraphNode(id="recommendation-service", label="recommendation-service", type="System", status="active"),
                    SubgraphNode(id="INC-250", label="INC-250 (Crash)", type="Ticket", status="open"),
                ],
                edges=[
                    SubgraphEdge(source="PR-398", target="user-profile-service", relationship="MODIFIES"),
                    SubgraphEdge(source="recommendation-service", target="user-profile-service", relationship="DEPENDS_ON"),
                    SubgraphEdge(source="PR-398", target="INC-250", relationship="CAUSED_BY"),
                ],
            ),
        )

    def _scenario_generic(self, user_id: str, query: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                f"### 🌐 NexusBrain Graph Intelligence Response\n\n"
                f"Your query: *\"{query}\"*\n\n"
                "Traversed the enterprise knowledge graph across **1,077 nodes** and **4,103 edges** in `company_brain`.\n"
                "- System topology, ticket provenance, and architectural decisions verified.\n"
                "- Cross-referenced with isolated tenant memory graph `memory_tenant_{user_id}`.\n"
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="classify_intent",
                    cypher_executed="N/A (Generic intent)",
                    latency_ms=0.5,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="semantic_subgraph_lookup",
                    cypher_executed="MATCH (n) WHERE n.name =~ '(?i).*' RETURN n LIMIT 5",
                    latency_ms=2.8,
                ),
            ],
            citations=[
                Citation(id="company_brain", label="Graph", title="7bit Cloud Knowledge Graph", status="active"),
            ],
            subgraph=Subgraph(
                nodes=[
                    SubgraphNode(id="company_brain", label="Company Brain", type="Graph", status="active"),
                    SubgraphNode(id=f"tenant_{user_id}", label=f"Tenant: {user_id}", type="TenantGraph", status="active"),
                ],
                edges=[
                    SubgraphEdge(source=f"tenant_{user_id}", target="company_brain", relationship="QUERIES"),
                ],
            ),
        )


mock_bridge = MockContractBridge()
