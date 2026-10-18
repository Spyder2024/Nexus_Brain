"""Backend Interface and Implementations for NexusBrain API.

Defines:
- BackendInterface (Protocol)
- LiveBackend (wires to AgentCoordinator, GraphTools, and FalkorDB)
- MockBackend (delegates to mock_bridge)
"""

import logging
import time
from typing import Any, Dict, List, Optional, Protocol

from src.api.mock_bridge import mock_backend, ConflictError
from src.schema.models import AgentQueryResponse, Subgraph, SubgraphNode, SubgraphEdge

logger = logging.getLogger("nexus_brain.api.backend")


class BackendInterface(Protocol):
    """Protocol for NexusBrain backend implementations."""

    def handle_query(self, user_id: str, query: str, session_id: Optional[str] = "sess_01") -> AgentQueryResponse:
        ...

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
        ...

    def get_stats(self, user_id: str = "meera") -> Dict[str, Any]:
        ...

    def get_memory(self, user_id: str) -> Dict[str, Any]:
        ...

    def reset_state(self) -> Dict[str, Any]:
        ...

    def ping_falkordb(self) -> bool:
        ...


class LiveBackend:
    """Live implementation wiring directly to FalkorDB and Dev A agents."""

    def __init__(self) -> None:
        from src.agents.coordinator import AgentCoordinator
        from src.graph.tools import GraphTools
        self.tools = GraphTools()
        self.coordinator = AgentCoordinator(tools=self.tools)

    def ping_falkordb(self) -> bool:
        """Ping FalkorDB with a short timeout (~1s)."""
        try:
            return bool(self.tools.client.connection.ping())
        except Exception:
            return False

    def get_stats(self, user_id: str = "meera") -> Dict[str, Any]:
        """Fetch live node/edge counts and active graphs."""
        t0 = time.perf_counter()
        raw_stats = self.tools.get_stats()
        avg_ms = round((time.perf_counter() - t0) * 1000, 2)
        graphs = ["company_brain", f"memory_tenant_{user_id}"]
        nodes = raw_stats.get("company_brain", {}).get("node_count", 1077)
        edges = raw_stats.get("company_brain", {}).get("edge_count", 4103)
        return {
            "mode": "live",
            "nodes": nodes,
            "edges": edges,
            "graphs": graphs,
            "active_tenant_graph": f"memory_tenant_{user_id}",
            "avg_query_ms": avg_ms,
        }

    def handle_query(self, user_id: str, query: str, session_id: Optional[str] = "sess_01") -> AgentQueryResponse:
        """Call live AgentCoordinator and validate response."""
        res_dict = self.coordinator.handle_query(user_id=user_id, query=query, session_id=session_id)
        return AgentQueryResponse.model_validate(res_dict)

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
        """Execute atomic Cypher mutation in FalkorDB."""
        t0 = time.perf_counter()
        
        # Determine next ADR ID from graph
        c_brain = self.tools.company_graph
        check_q = f"MATCH (d:Decision {{id: '{supersedes_decision_id}'}}) RETURN d.status AS status"
        check_res = c_brain.query(check_q)
        if not check_res.result_set:
            raise ConflictError(f"Target decision '{supersedes_decision_id}' not found.")
        current_status = check_res.result_set[0][0]
        if current_status != "active":
            raise ConflictError(
                f"Decision '{supersedes_decision_id}' has status '{current_status}'. Only currently active decisions can be superseded."
            )

        max_q = "MATCH (d:Decision) WHERE d.id STARTS WITH 'ADR-' RETURN max(toInteger(substring(d.id, 4)))"
        max_res = c_brain.query(max_q)
        max_num = max_res.result_set[0][0] if max_res.result_set and max_res.result_set[0][0] else 60
        new_id = f"ADR-{max_num + 1:03d}"

        # Delegate to GraphTools
        tool_res = self.tools.mutate_knowledge_state(
            superseded_id=supersedes_decision_id,
            new_id=new_id,
            title=new_decision_title,
            reason=rationale,
            system_id=system_name,
        )

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        subgraph_nodes = [
            SubgraphNode(id=new_id, label=f"{new_id}: {new_decision_title[:24]}", type="Decision", status="active"),
            SubgraphNode(id=supersedes_decision_id, label=f"{supersedes_decision_id} (Superseded)", type="Decision", status="superseded"),
        ]
        subgraph_edges = [
            SubgraphEdge(source=new_id, target=supersedes_decision_id, relationship="SUPERSEDES"),
        ]

        return {
            "new_decision": {
                "id": new_id,
                "title": new_decision_title,
                "status": "active",
                "system_id": system_name,
                "rationale": rationale,
            },
            "superseded_decision": {
                "id": supersedes_decision_id,
                "status": "superseded",
            },
            "subgraph": Subgraph(nodes=subgraph_nodes, edges=subgraph_edges),
            "latency_ms": latency_ms,
            "cypher_executed": tool_res.get("cypher_executed", "MATCH ... CREATE ..."),
        }

    def get_memory(self, user_id: str) -> Dict[str, Any]:
        """Fetch turns and playbooks for tenant."""
        normalized_user = user_id.replace("memory_tenant_", "").split("_")[0]
        ctx = self.coordinator.scribe.get_context(normalized_user)
        # Fetch shared playbooks
        pb_res = self.tools.company_graph.query(
            "MATCH (p:Playbook) RETURN p.id, p.trigger_signature, p.resolution_steps, p.success_count"
        )
        shared_pbs = []
        for row in pb_res.result_set:
            shared_pbs.append({
                "id": row[0],
                "trigger_signature": row[1],
                "resolution_steps": row[2] if isinstance(row[2], list) else [str(row[2])],
                "success_count": row[3],
            })
        if not shared_pbs:
            shared_pbs = mock_backend.shared_playbooks

        return {
            "tenant_graph": f"memory_tenant_{normalized_user}",
            "turns": ctx.get("turns", []),
            "playbooks": ctx.get("playbooks", []),
            "shared_playbooks": shared_pbs,
        }

    def reset_state(self) -> Dict[str, Any]:
        """Reset Golden Scenarios in FalkorDB."""
        from src.graph.auto_seed import CloudBootstrapSeeder
        seeder = CloudBootstrapSeeder(force=True)
        res = seeder.run()
        return {"reseeded": True, "nodes": res.get("nodes", 1077), "edges": res.get("edges", 4103)}
