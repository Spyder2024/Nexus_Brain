"""Gate 2: FalkorDB Graph & Deterministic Cypher Tool Verification Suite.

Verifies:
1. Connection & Multigraph Isolation:
   - Connects to FalkorDB on configured port.
   - Asserts company_brain has >= 1000 nodes and >= 3000 edges.
   - Verifies multigraph isolation between memory_tenant_test_a and memory_tenant_test_b.
2. Latency Benchmarks:
   - Asserts all 5 deterministic Cypher tools execute in < 50ms locally.
3. Golden Scenario Assertions:
   - Scenario 1 (Shadow Expert): Elena Rostova (person-19) identified over official maintainer Liam Chen (person-04).
   - Scenario 2 (Decision Lineage): Active ADR-051 superseding ADR-018 with linked INC-204 and SLACK-088.
   - Scenario 3 (Blast Radius): redis-session-store cascading across >= 3 systems and multiple teams.
   - Scenario 4 (Live Mutation Round-Trip): Mutates knowledge state to ADR-099 and verifies active/superseded transition.
"""

import time
import pytest
from src.config import get_falkordb_client, settings
from src.graph.loader import FalkorDBLoader
from src.graph.tools import GraphTools


@pytest.fixture(scope="module")
def falkordb_client():
    """FalkorDB client fixture."""
    client = get_falkordb_client()
    # Verify ping
    g = client.select_graph(settings.COMPANY_GRAPH_NAME)
    res = g.query("RETURN 1 AS ping")
    assert len(res.result_set) > 0, "Could not ping FalkorDB"
    return client


@pytest.fixture(scope="module")
def graph_tools(falkordb_client):
    """GraphTools suite fixture."""
    g = falkordb_client.select_graph(settings.COMPANY_GRAPH_NAME)
    return GraphTools(company_graph=g, client=falkordb_client)


# -----------------------------------------------------------------------------
# Test 1: Connection & Scale in FalkorDB
# -----------------------------------------------------------------------------
def test_falkordb_connection_and_scale(falkordb_client):
    """Verify company_brain graph has >= 1000 nodes and >= 3000 edges."""
    g = falkordb_client.select_graph(settings.COMPANY_GRAPH_NAME)

    res_nodes = g.query("MATCH (n) RETURN count(n) AS cnt")
    total_nodes = res_nodes.result_set[0][0]

    res_edges = g.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
    total_edges = res_edges.result_set[0][0]

    assert total_nodes >= 1000, f"Expected >= 1000 nodes, found {total_nodes}"
    assert total_edges >= 3000, f"Expected >= 3000 edges, found {total_edges}"
    assert total_nodes == 1077, f"Expected exactly 1077 nodes, found {total_nodes}"
    assert total_edges == 4103, f"Expected exactly 4103 edges, found {total_edges}"


# -----------------------------------------------------------------------------
# Test 2: Multigraph Tenant Isolation
# -----------------------------------------------------------------------------
def test_multigraph_tenant_isolation(falkordb_client):
    """Verify nodes created in memory_tenant_test_a DO NOT leak into memory_tenant_test_b."""
    tenant_a_name = "memory_tenant_test_a"
    tenant_b_name = "memory_tenant_test_b"

    graph_a = falkordb_client.select_graph(tenant_a_name)
    graph_b = falkordb_client.select_graph(tenant_b_name)

    # Clean existing test tenants
    try:
        graph_a.delete()
        graph_a = falkordb_client.select_graph(tenant_a_name)
    except Exception:
        pass
    try:
        graph_b.delete()
        graph_b = falkordb_client.select_graph(tenant_b_name)
    except Exception:
        pass

    # Create isolated marker node in Tenant A
    marker_id = "test-node-isolated-alpha"
    graph_a.query("CREATE (n:TestSession {id: $mid, owner: 'UserA'})", {"mid": marker_id})

    # Assert exists in Tenant A
    res_a = graph_a.query("MATCH (n:TestSession {id: $mid}) RETURN count(n)", {"mid": marker_id})
    assert res_a.result_set[0][0] == 1, "Marker node must exist in Tenant A"

    # Assert DOES NOT exist in Tenant B
    res_b = graph_b.query("MATCH (n:TestSession {id: $mid}) RETURN count(n)", {"mid": marker_id})
    assert res_b.result_set[0][0] == 0, "Tenant B must be strictly isolated and not contain Tenant A node"

    # Teardown test graphs
    try:
        graph_a.delete()
        graph_b.delete()
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Test 3: Tool 1 - Shadow Expert Discovery
# -----------------------------------------------------------------------------
def test_tool_find_shadow_expert(graph_tools: GraphTools):
    """Scenario 1: Calling find_shadow_expert('auth-service') must identify
    Liam Chen as official maintainer and Elena Rostova as top actual contributor."""
    res = graph_tools.find_shadow_expert("auth-service")

    assert res["latency_ms"] < 50.0, f"Query exceeded 50ms: {res['latency_ms']}ms"
    assert res["official_owner"]["id"] == "person-04", "Official maintainer must be person-04"
    assert "Liam Chen" in res["official_owner"]["name"]

    shadow = res["shadow_expert"]
    assert shadow is not None, "Shadow expert must be found"
    assert shadow["person_id"] == "person-19", "Shadow expert must be Elena Rostova (person-19)"
    assert "Elena Rostova" in shadow["name"]
    assert shadow["resolved_tickets"] >= 15, f"Expected >= 15 resolved tickets, got {shadow['resolved_tickets']}"
    assert shadow["prs_authored"] >= 20, f"Expected >= 20 PRs authored, got {shadow['prs_authored']}"

    # Visual subgraph contract
    subgraph = res["subgraph"]
    assert len(subgraph["nodes"]) > 0
    assert len(subgraph["edges"]) > 0


# -----------------------------------------------------------------------------
# Test 4: Tool 2 - Temporal Decision Lineage
# -----------------------------------------------------------------------------
def test_tool_trace_decision_lineage(graph_tools: GraphTools):
    """Scenario 2: Calling trace_decision_lineage('auth-service') returns active ADR-051
    superseding ADR-018, triggered by INC-204 & SLACK-088, contradicted by DOC-082."""
    res = graph_tools.trace_decision_lineage("auth-service")

    assert res["latency_ms"] < 50.0, f"Query exceeded 50ms: {res['latency_ms']}ms"
    active_d = res["active_decision"]
    assert active_d is not None, "Active decision must be found"
    assert active_d["id"] == "ADR-051", f"Expected active decision ADR-051, got {active_d['id']}"
    assert active_d["status"] == "active"

    superseded_ids = [s["id"] for s in res["superseded_chain"]]
    assert "ADR-018" in superseded_ids, "ADR-018 must be in superseded chain"

    ticket_ids = [t["id"] for t in res["linked_tickets"]]
    assert "INC-204" in ticket_ids, "INC-204 must be linked"

    thread_ids = [st["id"] for st in res["linked_threads"]]
    assert "SLACK-088" in thread_ids, "SLACK-088 must be linked"

    doc_ids = [doc["id"] for doc in res["contradicting_documents"]]
    assert "DOC-082" in doc_ids, "Outdated DOC-082 must be linked via CONTRADICTS"


# -----------------------------------------------------------------------------
# Test 5: Tool 3 - Blast Radius Computation
# -----------------------------------------------------------------------------
def test_tool_calculate_blast_radius(graph_tools: GraphTools):
    """Scenario 3: Calling calculate_blast_radius('redis-session-store') computes
    cascading failure path affecting at least 3 downstream systems across multiple teams."""
    res = graph_tools.calculate_blast_radius("redis-session-store")

    assert res["latency_ms"] < 50.0, f"Query exceeded 50ms: {res['latency_ms']}ms"
    assert res["root_system"]["id"] == "redis-session-store"

    downstream_ids = [d["id"] for d in res["downstream_systems"]]
    assert "auth-token-validator" in downstream_ids
    assert "checkout-orchestrator" in downstream_ids
    assert "stripe-webhook-worker" in downstream_ids
    assert res["downstream_systems_count"] >= 3

    assert len(res["affected_teams"]) >= 2
    team_ids = [t["id"] for t in res["affected_teams"]]
    assert "team-payment-billing" in team_ids or "team-auth-identity" in team_ids


# -----------------------------------------------------------------------------
# Test 6: Tool 4 - Live Knowledge Mutation Round-Trip
# -----------------------------------------------------------------------------
def test_tool_mutate_knowledge_state_roundtrip(graph_tools: GraphTools, falkordb_client):
    """Scenario 4: Call mutate_knowledge_state() with new decision ADR-099 superseding ADR-051.
    Re-query trace_decision_lineage and verify active/superseded transition."""
    # 1. Mutate state
    mut_res = graph_tools.mutate_knowledge_state({
        "decision_id": "ADR-099",
        "title": "Migrate auth-service RPC to HTTP/3 and Envoy sidecars",
        "system_id": "auth-service",
        "supersedes_id": "ADR-051",
        "rationale": "Mitigating Envoy connection pool exhaustion under peak load.",
        "author_id": "person-19",
    })

    assert mut_res["latency_ms"] < 50.0, f"Mutation exceeded 50ms: {mut_res['latency_ms']}ms"
    assert mut_res["status"] == "success"
    assert mut_res["new_decision_id"] == "ADR-099"
    assert mut_res["superseded_decision_id"] == "ADR-051"

    # 2. Re-query trace_decision_lineage
    lineage_res = graph_tools.trace_decision_lineage("auth-service")
    assert lineage_res["active_decision"]["id"] == "ADR-099"
    assert lineage_res["active_decision"]["status"] == "active"

    superseded_ids = [s["id"] for s in lineage_res["superseded_chain"]]
    assert "ADR-051" in superseded_ids, "ADR-051 must now be in superseded chain"

    # Clean up / reset graph back to pristine state for future test idempotency
    loader = FalkorDBLoader()
    loader.load_all_from_raw()


# -----------------------------------------------------------------------------
# Test 7: Tool 5 - Tenant Memory Sync
# -----------------------------------------------------------------------------
def test_tool_sync_agent_memory(graph_tools: GraphTools, falkordb_client):
    """Tool 5: Sync episodic conversation turns and procedural playbooks in user tenant graph."""
    user_id = "meera_sre"
    turn_payload = {
        "session_id": "session-meera-01",
        "turn_id": "turn-test-101",
        "role": "assistant",
        "content": "Applied procedural runbook DOC-012 to clear PyTorch CUDA fragmented tensors on ml-inference-worker.",
        "referenced_node_ids": ["DOC-012", "ml-inference-worker", "INC-249"],
        "playbook": {
            "id": "playbook-cuda-oom",
            "trigger_signature": "PyTorch CUDA OOM on GPU shard 4",
            "resolution_steps": [
                "kubectl rollout restart deployment/ml-inference-worker",
                "curl -X POST /admin/cuda/empty_cache",
            ],
            "verified_by_ticket_id": "INC-249",
        },
    }

    res = graph_tools.sync_agent_memory(user_id=user_id, turn_data=turn_payload)

    assert res["latency_ms"] < 50.0, f"Memory sync exceeded 50ms: {res['latency_ms']}ms"
    assert res["tenant_graph"] == "memory_tenant_meera_sre"
    assert res["turns_count"] >= 1
    assert len(res["playbooks"]) >= 1

    pb = res["playbooks"][0]
    assert "playbook-cuda-oom" in pb["id"]
    assert pb["trigger_signature"] == "PyTorch CUDA OOM on GPU shard 4"

    # Teardown test tenant
    try:
        falkordb_client.select_graph(res["tenant_graph"]).delete()
    except Exception:
        pass
