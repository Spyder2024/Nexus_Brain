"""Mock Contract Bridge for NexusBrain.

Provides deterministic responses strictly matching DEV_B_SPEC_v2.md and TRD.md.
Used in mock mode or as a zero-failure fallback for live deployments.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from src.schema.models import (
    AgentQueryResponse,
    AgentTrace,
    Citation,
    Subgraph,
    SubgraphNode,
    SubgraphEdge,
)


class ConflictError(Exception):
    """Raised when trying to mutate or supersede a node that is not in active state."""
    pass


class MockBackend:
    """Mock implementation of the NexusBrain backend."""

    def __init__(self) -> None:
        self.reset_state()

    def reset_state(self) -> Dict[str, Any]:
        """Reset internal state to pristine Golden Scenarios."""
        self.next_adr_counter = 61
        self.active_decisions: Dict[str, Dict[str, Any]] = {
            "ADR-051": {
                "id": "ADR-051",
                "title": "Migrate auth-service RPC to gRPC Streaming",
                "topic": "Inter-Service RPC Protocol",
                "status": "active",
                "decided_at": "2026-08-15T14:30:00Z",
                "system_id": "auth-service",
                "source_ref": "SLACK-088",
                "rationale": "Kafka caused head-of-line blocking and deadlock during INC-204.",
            }
        }
        self.superseded_decisions: Dict[str, Dict[str, Any]] = {
            "ADR-019": {
                "id": "ADR-019",
                "title": "Use Kafka for synchronous inter-service RPC",
                "topic": "Inter-Service RPC Protocol",
                "status": "superseded",
                "decided_at": "2025-11-10T09:00:00Z",
                "invalidated_at": "2026-08-15T14:30:00Z",
                "system_id": "auth-service",
                "source_ref": "INC-204",
                "rationale": "Initial MVP prototype standard.",
            }
        }
        self.supersedes_links: List[tuple[str, str]] = [("ADR-051", "ADR-019")]

        # Isolated tenant turns
        self.tenant_turns: Dict[str, List[Dict[str, Any]]] = {
            "meera": [
                {
                    "turn_id": "turn_m1",
                    "role": "user",
                    "content": "Investigate ml-inference-worker recurring CUDA leaks.",
                    "timestamp": "2026-10-17T18:00:00Z",
                },
                {
                    "turn_id": "turn_m2",
                    "role": "assistant",
                    "content": "Applied playbook-003: flush torch CUDA cache and configure expandable_segments.",
                    "timestamp": "2026-10-17T18:01:00Z",
                },
            ],
            "kabir": [
                {
                    "turn_id": "turn_k1",
                    "role": "user",
                    "content": "Check data pipeline latency downstream of Kafka.",
                    "timestamp": "2026-10-17T19:00:00Z",
                }
            ],
            "riya": [],  # Clean slate for new hire
        }

        # Shared procedural playbooks
        self.shared_playbooks = [
            {
                "id": "playbook-003",
                "trigger_signature": "CUDA out-of-memory / PyTorch memory fragmentation",
                "system_id": "ml-inference-worker",
                "resolution_steps": [
                    "torch.cuda.empty_cache()",
                    "export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
                    "Gracefully restart GPU worker pod",
                ],
                "verified_by": "meera",
                "verified_by_ticket_id": "INC-045",
                "success_count": 4,
            }
        ]

        return {"reseeded": True, "nodes": 1077, "edges": 4103}

    def ping_falkordb(self) -> bool:
        """Simulated FalkorDB ping."""
        return True

    def get_stats(self, user_id: str = "meera") -> Dict[str, Any]:
        """Return system and tenant stats."""
        return {
            "mode": "mock",
            "nodes": 1077,
            "edges": 4103,
            "graphs": [
                "company_brain",
                "memory_tenant_meera",
                "memory_tenant_kabir",
                "memory_tenant_riya",
            ],
            "active_tenant_graph": f"memory_tenant_{user_id}",
            "avg_query_ms": 3.8,
        }

    def get_memory(self, user_id: str) -> Dict[str, Any]:
        """Return isolated episodic memory turns and shared playbooks."""
        normalized_user = user_id.replace("memory_tenant_", "").split("_")[0]
        turns = self.tenant_turns.get(normalized_user, [])
        return {
            "tenant_graph": f"memory_tenant_{normalized_user}",
            "turns": turns,
            "playbooks": self.shared_playbooks if normalized_user == "meera" else [],
            "shared_playbooks": self.shared_playbooks,
        }

    def mutate_knowledge(
        self,
        user_id: str,
        source_type: str,
        channel: str,
        system_name: str,
        new_decision_title: str,
        supersedes_decision_id: str,
        rationale: str,
    ) -> Dict[str, Any]:
        """Mutate knowledge graph state by creating a new active ADR and superseding the target."""
        t0 = time.perf_counter()

        # Check if target ADR exists and is active
        if supersedes_decision_id not in self.active_decisions:
            if supersedes_decision_id in self.superseded_decisions:
                raise ConflictError(
                    f"Decision '{supersedes_decision_id}' is already superseded. Only currently active decisions can be superseded."
                )
            raise ConflictError(
                f"Target decision '{supersedes_decision_id}' not found in active decisions."
            )

        old_adr = self.active_decisions.pop(supersedes_decision_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        old_adr["status"] = "superseded"
        old_adr["invalidated_at"] = now_iso
        self.superseded_decisions[supersedes_decision_id] = old_adr

        new_id = f"ADR-{self.next_adr_counter:03d}"
        self.next_adr_counter += 1

        new_adr = {
            "id": new_id,
            "title": new_decision_title,
            "topic": old_adr.get("topic", "Inter-Service RPC Protocol"),
            "status": "active",
            "decided_at": now_iso,
            "system_id": system_name,
            "source_ref": channel,
            "rationale": rationale,
        }
        self.active_decisions[new_id] = new_adr
        self.supersedes_links.append((new_id, supersedes_decision_id))

        latency_ms = round((time.perf_counter() - t0) * 1000 + 2.5, 2)
        cypher = (
            f"MATCH (old:Decision {{id: '{supersedes_decision_id}', status: 'active'}})\n"
            f"SET old.status = 'superseded', old.invalidated_at = '{now_iso}'\n"
            f"CREATE (new:Decision {{id: '{new_id}', title: '{new_decision_title}', status: 'active'}})\n"
            f"CREATE (new)-[:SUPERSEDES {{reason: '{rationale[:30]}...'}}]->(old)\n"
            f"RETURN new, old"
        )

        subgraph_nodes = [
            SubgraphNode(id=new_id, label=f"{new_id}: {new_decision_title[:24]}", type="Decision", status="active"),
            SubgraphNode(id=old_adr["id"], label=f"{old_adr['id']}: {old_adr['title'][:24]}", type="Decision", status="superseded"),
        ]
        subgraph_edges = [
            SubgraphEdge(source=new_id, target=old_adr["id"], relationship="SUPERSEDES"),
        ]

        return {
            "new_decision": new_adr,
            "superseded_decision": old_adr,
            "subgraph": Subgraph(nodes=subgraph_nodes, edges=subgraph_edges),
            "latency_ms": latency_ms,
            "cypher_executed": cypher,
        }

    def handle_query(self, user_id: str, query: str, session_id: Optional[str] = "sess_01") -> AgentQueryResponse:
        """Route to one of the 5 Golden Scenarios or dynamic query."""
        normalized_user = user_id.replace("memory_tenant_", "").split("_")[0]
        q_lower = query.lower()

        # Log to tenant memory
        self.tenant_turns.setdefault(normalized_user, []).append({
            "turn_id": f"turn_{int(time.time()*1000)}",
            "role": "user",
            "content": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if any(w in q_lower for w in ["shadow", "knows the most", "who actually knows", "outages", "expert"]):
            return self._scenario_1_shadow_expert(normalized_user)

        if any(w in q_lower for w in ["kafka", "rpc", "doc-082", "doc-004", "onboarding doc", "adr"]):
            return self._scenario_2_decision_lineage(normalized_user)

        if any(w in q_lower for w in ["blast", "radius", "redis", "cascade", "downstream", "oom"]):
            return self._scenario_3_blast_radius(normalized_user)

        if any(w in q_lower for w in ["cuda", "memory leak", "ml-inference", "recurring", "playbook"]):
            return self._scenario_4_cuda_memory(normalized_user)

        if any(w in q_lower for w in ["pr-398", "breaking", "recommendation", "deserialization", "panic"]):
            return self._scenario_5_breaking_change(normalized_user)

        return self._scenario_generic(normalized_user, query)

    def _scenario_1_shadow_expert(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 🔍 Subject-Matter Expert & Ownership Analysis for `auth-service`\n\n"
                "- **Official Owner:** **`person-04` (Devon Vance)** is listed in the organization graph as Team Lead for *Auth & Identity* ([Team: team-auth]).\n"
                "- **Shadow Expert:** **`person-19` (Kavya Rao - Staff SRE)** is the true operational domain expert. Graph traversal reveals `person-19` has **resolved 18 critical SEV-1 incidents** and **authored 26 PRs** touching `auth-service` over the last 90 days.\n\n"
                "#### ⚠️ Cascading Blast Radius\n"
                "If `auth-service` experiences degradation, **3 downstream tier-0/tier-1 services** are directly impacted:\n"
                "1. `checkout-orchestrator` (Payment & Billing)\n"
                "2. `user-profile-service` (Core Platform)\n"
                "3. `gateway-proxy` (Frontend Experience)\n\n"
                "> **Recommendation:** Page **`person-19` (Kavya Rao)** directly for incident triage rather than the official org lead."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="find_shadow_expert",
                    cypher_executed="MATCH (s:System {id: 'auth-service'})<-[:OWNS]-(t:Team)<-[:LEADS]-(lead:Person)...",
                    latency_ms=0.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="find_shadow_expert",
                    cypher_executed=(
                        "MATCH (s:System {id: 'auth-service'})<-[:OWNS]-(t:Team)<-[:LEADS]-(lead:Person) "
                        "OPTIONAL MATCH (p:Person)-[:RESOLVED]->(tk:Ticket {severity: 'SEV-1'})-[:AFFECTS]->(s) "
                        "RETURN lead.name, p.name, count(tk) ORDER BY count(tk) DESC LIMIT 5"
                    ),
                    latency_ms=3.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="calculate_blast_radius",
                    cypher_executed="MATCH (s:System {id: 'auth-service'})<-[:DEPENDS_ON*1..3]-(downstream:System) RETURN downstream",
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
                    SubgraphNode(id="person-04", label="Devon Vance (Official Lead)", type="Person", status="active"),
                    SubgraphNode(id="person-19", label="Kavya Rao (Staff SRE Expert)", type="Person", status="active"),
                    SubgraphNode(id="team-auth", label="Auth & Identity", type="Team", status="active"),
                    SubgraphNode(id="checkout-orchestrator", label="checkout-orchestrator", type="System", status="active"),
                ],
                edges=[
                    SubgraphEdge(source="team-auth", target="auth-service", relationship="OWNS"),
                    SubgraphEdge(source="person-04", target="team-auth", relationship="LEADS"),
                    SubgraphEdge(source="person-19", target="auth-service", relationship="RESOLVED_SEV1"),
                    SubgraphEdge(source="checkout-orchestrator", target="auth-service", relationship="DEPENDS_ON"),
                ],
            ),
        )

    def _scenario_2_decision_lineage(self, user_id: str) -> AgentQueryResponse:
        # Determine latest active ADR for auth_rpc
        latest_active_id = "ADR-051"
        for adr_id, adr_data in self.active_decisions.items():
            if adr_data.get("system_id") == "auth-service" or adr_data.get("topic") == "Inter-Service RPC Protocol":
                latest_active_id = adr_id
                break

        latest_active = self.active_decisions[latest_active_id]
        is_mutated = latest_active_id != "ADR-051"

        if is_mutated:
            answer = (
                f"### 🛑 Temporal Decision Alert: `DOC-082` & Prior ADRs are SUPERSEDED\n\n"
                f"**DO NOT follow `DOC-082` (Kafka RPC) or `ADR-051` (gRPC Streaming).**\n\n"
                f"- **Current Active Standard:** **`{latest_active_id}` ({latest_active['title']})**.\n"
                f"- **Why it changed:** `ADR-051` was superseded due to: *{latest_active.get('rationale')}*.\n"
                f"- **Historical Root:** Original Kafka RPC (`ADR-019`) was superseded after deadlock incident `INC-204` ([Slack: SLACK-088]).\n\n"
                f"> **Active Policy Citation:** [{latest_active_id}] status: ACTIVE."
            )
            citations = [
                Citation(id=latest_active_id, label="Decision", title=latest_active["title"], status="active", source_ref=latest_active.get("source_ref")),
                Citation(id="ADR-051", label="Decision", title="Migrate auth-service RPC to gRPC Streaming", status="superseded", source_ref="SLACK-088"),
                Citation(id="ADR-019", label="Decision", title="Use Kafka for synchronous inter-service RPC", status="superseded", source_ref="INC-204"),
                Citation(id="DOC-082", label="Document", title="Engineering Onboarding Guide", status="outdated"),
            ]
            subgraph_nodes = [
                SubgraphNode(id=latest_active_id, label=f"{latest_active_id} (Active)", type="Decision", status="active"),
                SubgraphNode(id="ADR-051", label="ADR-051 (Superseded)", type="Decision", status="superseded"),
                SubgraphNode(id="ADR-019", label="ADR-019 (Kafka)", type="Decision", status="superseded"),
                SubgraphNode(id="DOC-082", label="DOC-082 (Onboarding)", type="Document", status="outdated"),
            ]
            subgraph_edges = [
                SubgraphEdge(source=latest_active_id, target="ADR-051", relationship="SUPERSEDES"),
                SubgraphEdge(source="ADR-051", target="ADR-019", relationship="SUPERSEDES"),
                SubgraphEdge(source="DOC-082", target="ADR-019", relationship="REFERENCES"),
            ]
        else:
            answer = (
                "### 🛑 Temporal Decision Alert: `DOC-082` is OUTDATED\n\n"
                "**DO NOT use Kafka for synchronous RPC as suggested in `DOC-082`.**\n\n"
                "- **Active Decision:** **`ADR-051` (Migrate auth-service RPC to gRPC Streaming)** is the current enterprise standard ([Status: active]).\n"
                "- **Why it changed:** `ADR-019` (Use Kafka for synchronous inter-service RPC) was superseded after SEV-1 incident **`INC-204`** caused a distributed deadlock, as documented in war room **`SLACK-088`** (#arch-sync).\n\n"
                "> **Provenance Chain:** `DOC-082` ➡️ `ADR-019` (superseded) ⬅️ `[:SUPERSEDES]` ⬅️ **`ADR-051`** (active)."
            )
            citations = [
                Citation(id="ADR-051", label="Decision", title="Migrate auth-service RPC to gRPC Streaming", status="active", source_ref="SLACK-088"),
                Citation(id="ADR-019", label="Decision", title="Use Kafka for synchronous inter-service RPC", status="superseded", source_ref="INC-204"),
                Citation(id="DOC-082", label="Document", title="Engineering Onboarding Guide", status="outdated"),
                Citation(id="INC-204", label="Ticket", title="SEV-1 Kafka RPC Deadlock", status="resolved"),
            ]
            subgraph_nodes = [
                SubgraphNode(id="ADR-051", label="ADR-051 (gRPC Streaming)", type="Decision", status="active"),
                SubgraphNode(id="ADR-019", label="ADR-019 (Kafka RPC)", type="Decision", status="superseded"),
                SubgraphNode(id="DOC-082", label="DOC-082 (Onboarding)", type="Document", status="outdated"),
                SubgraphNode(id="INC-204", label="INC-204 (Deadlock Outage)", type="Ticket", status="resolved"),
            ]
            subgraph_edges = [
                SubgraphEdge(source="ADR-051", target="ADR-019", relationship="SUPERSEDES"),
                SubgraphEdge(source="DOC-082", target="ADR-019", relationship="REFERENCES"),
                SubgraphEdge(source="INC-204", target="ADR-051", relationship="TRIGGERED_DECISION"),
            ]

        return AgentQueryResponse(
            answer=answer,
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="trace_decision_lineage",
                    cypher_executed="N/A (Intent: TEMPORAL_DECISION_LINEAGE)",
                    latency_ms=0.5,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="trace_decision_lineage",
                    cypher_executed=(
                        "MATCH (doc:Document {id: 'DOC-082'})-[:REFERENCES]->(old:Decision) "
                        "OPTIONAL MATCH (current:Decision {status: 'active'})-[:SUPERSEDES*1..3]->(old) "
                        "OPTIONAL MATCH (current)-[:DECIDED_IN]->(st:SlackThread) "
                        "RETURN doc, old, current, st"
                    ),
                    latency_ms=3.7,
                ),
            ],
            citations=citations,
            subgraph=Subgraph(nodes=subgraph_nodes, edges=subgraph_edges),
        )

    def _scenario_3_blast_radius(self, user_id: str) -> AgentQueryResponse:
        return AgentQueryResponse(
            answer=(
                "### 💥 4-Hop Cascading Blast Radius for `redis-session-store`\n\n"
                "An OOM eviction storm on `redis-session-store` (Tier-0) causes a severe 4-hop cascade across **3 organizational departments**:\n\n"
                "1. **Direct Failure (Hop 1):** `auth-token-validator` (Auth & Identity)\n"
                "2. **Cascading Failure (Hop 2):** `checkout-orchestrator` (Payment & Billing)\n"
                "3. **Cascading Failure (Hop 3):** `stripe-webhook-worker` (Payment & Billing)\n"
                "4. **Perimeter Impact (Hop 4):** `frontend-gateway` (Frontend Experience)\n\n"
                "#### 🚨 Department Leads to Page Immediately:\n"
                "- **SRE & Infra:** Team Lead `person-12`\n"
                "- **Auth & Identity:** Team Lead `person-04`\n"
                "- **Payment & Billing:** Team Lead `person-08`"
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="calculate_blast_radius",
                    cypher_executed="N/A (Intent: BLAST_RADIUS_ANALYSIS)",
                    latency_ms=0.4,
                ),
                AgentTrace(
                    agent="GraphNavigator",
                    tool="calculate_blast_radius",
                    cypher_executed=(
                        "MATCH path = (root:System {id: 'redis-session-store'})<-[:DEPENDS_ON*1..4]-(downstream:System) "
                        "OPTIONAL MATCH (downstream)<-[:OWNS]-(t:Team)<-[:LEADS]-(lead:Person) "
                        "RETURN path, t.name, lead.name"
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
                "  3. Gracefully restart GPU worker queue `gpu-batch-04`.\n\n"
                "> **Tenant Memory Coordination:** This playbook was verified by SRE Lead **Meera** in `memory_tenant_meera` and automatically promoted to shared memory for all agents."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="sync_agent_memory",
                    cypher_executed="N/A (Intent: PROCEDURAL_PLAYBOOK_RECALL)",
                    latency_ms=0.3,
                ),
                AgentTrace(
                    agent="MemoryScribe",
                    tool="sync_agent_memory",
                    cypher_executed=(
                        "MATCH (p:Playbook {id: 'playbook-003'})-[:APPLIES_TO]->(s:System {id: 'ml-inference-worker'}) "
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
                "> **Remediation:** Roll back `PR-398` or deploy hotfix `PR-401` restoring backward compatibility."
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
                    tool="trace_code_provenance",
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
                f"### 🌐 NexusBrain Company Brain Intelligence\n\n"
                f"Query: *\"{query}\"*\n\n"
                "Traversed enterprise graph across **1,077 nodes** and **4,103 edges** in `company_brain`.\n"
                "- System topology, ticket provenance, and architectural decisions verified.\n"
                f"- Integrated with isolated tenant graph `memory_tenant_{user_id}`.\n"
            ),
            tenant_graph=f"memory_tenant_{user_id}",
            agent_trace=[
                AgentTrace(
                    agent="RouterAgent",
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


mock_backend = MockBackend()
mock_bridge = mock_backend
