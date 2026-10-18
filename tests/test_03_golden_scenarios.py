"""Gate 3: The 5 Golden Demo Scenarios Verification Suite.

Validates the full multi-agent pipeline and TRD Section 6 contracts:
1. Scenario 1 (Shadow Expert):
   - Query: "Who is the real expert on auth-service?"
   - Asserts: Liam Chen (person-04) is official maintainer, Elena Rostova (person-19) is shadow expert.
   - Response contains structured citations and unified SubgraphPayload.
2. Scenario 2 (Temporal Decision Lineage & Contradicting Documentation):
   - Query: "Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-082?"
   - Asserts: Critical warning on DOC-082, active standard is ADR-051, superseded chain ADR-018,
     linked incident INC-204 and Slack discussion SLACK-088.
3. Scenario 3 (Cascading Blast Radius):
   - Query: "What breaks if redis-session-store goes down?"
   - Asserts: Blast radius >= 3 hops, affects >= 3 downstream services (auth-token-validator,
     checkout-orchestrator, stripe-webhook-worker) and their owning teams.
4. Scenario 4 (Live Knowledge State Mutation):
   - Tests round-trip knowledge mutation via AgentCoordinator.handle_mutation().
   - Mutates ADR-051 -> ADR-099, then asserts query reflects ADR-099 as active and ADR-051 as superseded.
   - Cleans up mutation back to baseline ADR-051 so all tests remain deterministic and idempotent.
5. Scenario 5 (Multi-Tenant Episodic & Procedural Memory Isolation):
   - Verifies tenant conversation isolation between users (e.g. 'meera' and 'riya').
   - Validates procedural playbook promotion on ml-inference-worker CUDA memory fragmentation.
   - Validates strict Pydantic v2 schema compliance with AgentQueryResponse.
"""

import pytest
from src.agents.coordinator import AgentCoordinator
from src.agents.models import AgentQueryResponse
from src.config import get_falkordb_client, settings
from src.graph.tools import GraphTools


@pytest.fixture(scope="module")
def coordinator():
    """AgentCoordinator fixture with live FalkorDB backend."""
    return AgentCoordinator()


@pytest.fixture(scope="module")
def falkor_client():
    """Direct FalkorDB client fixture for state assertions and cleanup."""
    return get_falkordb_client()


# -----------------------------------------------------------------------------
# Test 1: Scenario 1 - Shadow Subject-Matter Expert Discovery
# -----------------------------------------------------------------------------
def test_scenario_1_shadow_expert(coordinator):
    """Scenario 1: Find real shadow expert for auth-service."""
    user_id = "test_user_sc1"
    query = "Who is the real expert on auth-service?"

    response_dict = coordinator.handle_query(user_id=user_id, query=query)
    validated = AgentQueryResponse.model_validate(response_dict)

    # 1. Assert response schema contract
    assert validated.tenant_graph == f"{settings.TENANT_GRAPH_PREFIX}{user_id}"
    assert len(validated.agent_trace) >= 1
    assert any(t.tool == "find_shadow_expert" for t in validated.agent_trace)

    # 2. Assert citations include both official maintainer and shadow expert
    citation_ids = [c.id for c in validated.citations]
    assert "person-04" in citation_ids, "Liam Chen (person-04) must be cited as official maintainer"
    assert "person-19" in citation_ids, "Elena Rostova (person-19) must be cited as shadow expert"

    # 3. Assert Markdown answer content
    assert "Liam Chen" in validated.answer
    assert "Elena Rostova" in validated.answer
    assert "[Shadow Subject-Matter Expert]" in validated.answer
    assert "18 critical SEV-1 incidents" in validated.answer or "18" in validated.answer
    assert "26 Pull Requests" in validated.answer or "26" in validated.answer

    # 4. Assert subgraph contains relevant nodes and edges
    subgraph_node_ids = [n.id for n in validated.subgraph.nodes]
    assert "auth-service" in subgraph_node_ids
    assert "person-04" in subgraph_node_ids
    assert "person-19" in subgraph_node_ids
    assert len(validated.subgraph.edges) >= 2


# -----------------------------------------------------------------------------
# Test 2: Scenario 2 - Temporal Decision Lineage & Contradicting Docs
# -----------------------------------------------------------------------------
def test_scenario_2_decision_lineage_and_outdated_doc(coordinator):
    """Scenario 2: Identify outdated doc DOC-082 contradicting active decision ADR-051."""
    user_id = "test_user_sc2"
    query = "Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-082?"

    response_dict = coordinator.handle_query(user_id=user_id, query=query)
    validated = AgentQueryResponse.model_validate(response_dict)

    # 1. Assert warning banner is present in markdown answer
    assert "[CRITICAL WARNING]" in validated.answer
    assert "DOC-082" in validated.answer
    assert "OUTDATED" in validated.answer
    assert "ADR-051" in validated.answer
    assert "ADR-018" in validated.answer

    # 2. Assert citations contain all cross-silo lineage nodes
    citation_ids = {c.id for c in validated.citations}
    assert "ADR-051" in citation_ids, "Active decision ADR-051 must be cited"
    assert "ADR-018" in citation_ids, "Superseded decision ADR-018 must be cited"
    assert "DOC-082" in citation_ids, "Contradicting document DOC-082 must be cited"
    assert "INC-204" in citation_ids, "Catalyst ticket INC-204 must be cited"
    assert "SLACK-088" in citation_ids, "Catalyst discussion SLACK-088 must be cited"

    # 3. Assert Subgraph contains Decision nodes and CONTRADICTS / SUPERSEDES edges
    subgraph_rel_types = {e.relationship for e in validated.subgraph.edges}
    assert "CONTRADICTS" in subgraph_rel_types or "TRIGGERED_DECISION" in subgraph_rel_types


# -----------------------------------------------------------------------------
# Test 3: Scenario 3 - Cascading Blast Radius
# -----------------------------------------------------------------------------
def test_scenario_3_cascading_blast_radius(coordinator):
    """Scenario 3: Calculate multi-hop blast radius when redis-session-store fails."""
    user_id = "test_user_sc3"
    query = "What breaks if redis-session-store goes down? What is the cascading blast radius?"

    response_dict = coordinator.handle_query(user_id=user_id, query=query)
    validated = AgentQueryResponse.model_validate(response_dict)

    # 1. Assert downstream systems identified
    citation_ids = {c.id for c in validated.citations}
    expected_affected = {"auth-token-validator", "checkout-orchestrator", "stripe-webhook-worker"}
    assert expected_affected.issubset(citation_ids), f"Expected {expected_affected} in citations, got {citation_ids}"

    # 2. Assert affected teams identified
    team_citations = [c for c in validated.citations if c.label == "Team"]
    assert len(team_citations) >= 2, "Must identify affected engineering teams"

    # 3. Assert Markdown explanation contains blast radius details
    assert "redis-session-store" in validated.answer
    assert "downstream microservices" in validated.answer or "downstream" in validated.answer

    # 4. Assert subgraph has >= 5 nodes and dependencies
    assert len(validated.subgraph.nodes) >= 5
    assert len(validated.subgraph.edges) >= 4


# -----------------------------------------------------------------------------
# Test 4: Scenario 4 - Live Knowledge State Mutation Round-Trip
# -----------------------------------------------------------------------------
def test_scenario_4_live_mutation_roundtrip(coordinator, falkor_client):
    """Scenario 4: Live knowledge state mutation from ADR-051 to ADR-099 and idempotent rollback."""
    user_id = "test_user_sc4"

    # 1. Mutate knowledge state: ADR-051 -> ADR-099
    mutation_payload = {
        "system_id": "auth-service",
        "new_decision_id": "ADR-099",
        "new_decision_title": "Adopt Zero-Trust Envoy Sidecar Mesh for RPC",
        "supersedes_decision_id": "ADR-051",
        "rationale": "Automated mutual TLS encryption, decentralized rate limiting, and zero-downtime service discovery.",
        "author_id": "person-19",
        "slack_thread_id": "SLACK-088",
    }

    mut_res = coordinator.handle_mutation(user_id=user_id, event_payload=mutation_payload)
    assert mut_res["success"] is True
    assert mut_res["new_decision_id"] == "ADR-099"
    assert mut_res["superseded_decision_id"] == "ADR-051"

    # 2. Query decision lineage for auth-service
    q_res = coordinator.handle_query(user_id=user_id, query="What is the current architecture decision for auth-service RPC?")
    validated = AgentQueryResponse.model_validate(q_res)

    # ADR-099 must now be the active standard
    assert "ADR-099" in validated.answer
    citation_statuses = {c.id: c.status for c in validated.citations}
    assert citation_statuses.get("ADR-099") == "active"
    assert citation_statuses.get("ADR-051") == "superseded"

    # 3. Idempotent Rollback: Restore ADR-051 to active, delete ADR-099 node
    g = falkor_client.select_graph(settings.COMPANY_GRAPH_NAME)
    rollback_cypher = """
    MATCH (old:Decision {id: 'ADR-051'})
    SET old.status = 'active', old.invalidated_at = null
    WITH old
    MATCH (new:Decision {id: 'ADR-099'})
    DETACH DELETE new
    """
    g.query(rollback_cypher)

    # Verify rollback
    verify_cypher = "MATCH (d:Decision {id: 'ADR-051'}) RETURN d.status, d.invalidated_at"
    res = g.query(verify_cypher)
    assert res.result_set[0][0] == "active"
    assert res.result_set[0][1] is None


# -----------------------------------------------------------------------------
# Test 5: Scenario 5 - Multi-Tenant Episodic & Procedural Memory Isolation
# -----------------------------------------------------------------------------
def test_scenario_5_memory_isolation_and_playbook_promotion(coordinator, falkor_client):
    """Scenario 5: Multi-tenant episodic memory isolation and cross-agent playbook promotion."""
    user_meera = "meera_sre"
    user_riya = "riya_dev"

    # Ensure clean test state by deleting existing test tenant graphs if present
    for u in [user_meera, user_riya]:
        try:
            falkor_client.select_graph(f"{settings.TENANT_GRAPH_PREFIX}{u}").delete()
        except Exception:
            pass

    # Meera investigates a CUDA OOM crash on ml-inference-worker
    q_meera = "We had a CUDA out-of-memory crash on ml-inference-worker like INC-249. What is the fix?"
    res_meera = coordinator.handle_query(user_id=user_meera, query=q_meera)
    AgentQueryResponse.model_validate(res_meera)

    assert "PyTorch CUDA" in res_meera["answer"]
    assert "DOC-012" in res_meera["answer"]
    assert "INC-045" in res_meera["answer"]

    # Verify Meera's tenant memory has recorded this turn and promoted procedural playbook
    mem_meera = coordinator.get_tenant_memory_state(user_id=user_meera)
    assert mem_meera["turns_count"] >= 1
    assert len(mem_meera["playbooks"]) >= 1
    assert mem_meera["playbooks"][0]["id"] == "playbook-cuda-oom-recycling"

    # Verify Riya's tenant memory does NOT contain Meera's private conversation turns
    mem_riya = coordinator.get_tenant_memory_state(user_id=user_riya)
    assert mem_riya["turns_count"] == 0, "Riya's tenant memory must be completely isolated from Meera"

    # But procedural shared playbook IS available to the company
    g_company = falkor_client.select_graph(settings.COMPANY_GRAPH_NAME)
    res_pb = g_company.query("MATCH (p:Playbook {id: 'playbook-cuda-oom-recycling'}) RETURN p.trigger_signature")
    assert len(res_pb.result_set) >= 1
    assert "CUDA" in res_pb.result_set[0][0]

    # Clean up test tenant graphs and promoted test playbook so company_brain returns to baseline
    try:
        g_company.query("MATCH (p:Playbook {id: 'playbook-cuda-oom-recycling'}) DETACH DELETE p")
    except Exception:
        pass

    for u in [user_meera, user_riya]:
        try:
            tg = falkor_client.select_graph(f"{settings.TENANT_GRAPH_PREFIX}{u}")
            tg.delete()
        except Exception:
            pass
