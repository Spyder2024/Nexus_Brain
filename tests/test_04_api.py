"""Test Suite for Phase 4 NexusBrain API (FastAPI TestClient in mock mode).

Validates all 8 requirements specified in DEV_B_SPEC_v2.md Section 3:
1. /health returns quickly with mode.
2. All 5 presets return payloads that parse as TRD model with non-empty agent_trace.
3. Preset #2 cites ADR-051 active and ADR-019 superseded.
4. /mutate then Preset #2 shows new ADR active and ADR-051 superseded.
5. Repeat /mutate on same id -> 409 Conflict.
6. /reset restores original Preset #2 result.
7. /memory/riya has playbook-003 in shared_playbooks and none of Meera's turns.
8. CORS preflight from *.vercel.app origin succeeds.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Force mock mode for API tests
os.environ["NEXUS_MODE"] = "mock"

from src.api.server import app
from src.schema.models import AgentQueryResponse

client = TestClient(app)


def test_01_health_returns_quickly_with_mode():
    """1. /health returns quickly with mode and awake status."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "awake"
    assert data["mode"] in ("live", "mock")
    assert "timestamp" in data
    assert "falkordb_connected" in data


def test_02_all_5_presets_return_valid_trd_contract():
    """2. All 5 presets return payloads that parse as TRD model with non-empty agent_trace."""
    presets = [
        ("meera", "Who actually knows the most about auth-service outages?"),
        ("meera", "Can I use Kafka for synchronous RPC as written in Onboarding Doc DOC-082?"),
        ("meera", "What is the blast radius if redis-session-store experiences an OOM crash?"),
        ("meera", "How do we resolve the recurring CUDA memory leak in ml-inference-worker?"),
        ("meera", "Why did recommendation-service crash with a deserialization error after PR-398?"),
    ]

    for user_id, query in presets:
        res = client.post("/api/v1/query", json={"user_id": user_id, "query": query})
        assert res.status_code == 200, f"Failed on query: {query}"
        data = res.json()

        # Strict validation against TRD.md Section 6 Pydantic schema
        parsed = AgentQueryResponse.model_validate(data)
        assert len(parsed.agent_trace) > 0, f"agent_trace empty for query: {query}"
        assert len(parsed.citations) > 0, f"citations empty for query: {query}"
        assert len(parsed.subgraph.nodes) > 0, f"subgraph empty for query: {query}"


def test_03_preset_2_cites_adr051_active_and_adr019_superseded():
    """3. Preset #2 cites ADR-051 active and ADR-019 superseded."""
    # Reset first to ensure baseline state
    client.post("/api/v1/reset")

    res = client.post(
        "/api/v1/query",
        json={"user_id": "meera", "query": "Can I use Kafka for synchronous RPC as written in DOC-082?"},
    )
    assert res.status_code == 200
    data = res.json()

    c_dict = {c["id"]: c["status"] for c in data["citations"]}
    assert "ADR-051" in c_dict, "ADR-051 missing from citations"
    assert c_dict["ADR-051"] == "active"

    assert "ADR-019" in c_dict, "ADR-019 missing from citations"
    assert c_dict["ADR-019"] == "superseded"


def test_04_mutate_then_preset_2_shows_new_adr_active_and_adr051_superseded():
    """4. /mutate then Preset #2 shows the new ADR active and ADR-051 superseded."""
    # Mutate knowledge state
    mutate_res = client.post(
        "/api/v1/mutate",
        json={
            "user_id": "meera",
            "source_type": "SlackThread",
            "channel": "#arch-sync",
            "system_name": "auth-service",
            "new_decision_title": "Move auth-service RPC to HTTP/3 QUIC",
            "supersedes_decision_id": "ADR-051",
            "rationale": "Envoy proxy bug INC-299 causing gRPC stream resets.",
        },
    )
    assert mutate_res.status_code == 200
    mut_data = mutate_res.json()
    new_adr_id = mut_data["new_decision"]["id"]
    assert new_adr_id.startswith("ADR-")
    assert mut_data["superseded_decision"]["status"] == "superseded"

    # Now re-query Preset #2
    res = client.post(
        "/api/v1/query",
        json={"user_id": "meera", "query": "Can I use Kafka for synchronous RPC as written in DOC-082?"},
    )
    assert res.status_code == 200
    data = res.json()

    c_dict = {c["id"]: c["status"] for c in data["citations"]}
    assert new_adr_id in c_dict, f"New ADR {new_adr_id} not active in citations"
    assert c_dict[new_adr_id] == "active"
    assert "ADR-051" in c_dict
    assert c_dict["ADR-051"] == "superseded"


def test_05_repeat_mutate_on_same_id_returns_409():
    """5. Repeat /mutate on the same id -> 409 Conflict."""
    # ADR-051 was already superseded in test_04
    res = client.post(
        "/api/v1/mutate",
        json={
            "user_id": "meera",
            "source_type": "SlackThread",
            "channel": "#arch-sync",
            "system_name": "auth-service",
            "new_decision_title": "Another protocol switch",
            "supersedes_decision_id": "ADR-051",
            "rationale": "Attempting to supersede an already-superseded node.",
        },
    )
    assert res.status_code == 409
    err = res.json()
    assert "error" in err
    assert err["error"]["code"] == "CONFLICT"


def test_06_reset_restores_original_preset_2_result():
    """6. /reset restores original Preset #2 result."""
    reset_res = client.post("/api/v1/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["reseeded"] is True

    # Check Preset #2 again
    res = client.post(
        "/api/v1/query",
        json={"user_id": "meera", "query": "Can I use Kafka for synchronous RPC as written in DOC-082?"},
    )
    assert res.status_code == 200
    data = res.json()
    c_dict = {c["id"]: c["status"] for c in data["citations"]}
    assert c_dict.get("ADR-051") == "active"
    assert c_dict.get("ADR-019") == "superseded"


def test_07_memory_riya_has_shared_playbook_and_no_meera_turns():
    """7. /memory/riya has playbook-003 in shared_playbooks and none of Meera's turns."""
    res_riya = client.get("/api/v1/memory/riya")
    assert res_riya.status_code == 200
    riya_mem = res_riya.json()

    assert riya_mem["tenant_graph"] == "memory_tenant_riya"
    # Riya should have 0 of Meera's private turns
    assert len(riya_mem["turns"]) == 0

    # Riya should inherit shared playbook-003
    shared_ids = [pb["id"] for pb in riya_mem["shared_playbooks"]]
    assert "playbook-003" in shared_ids

    # Meera should have turns
    res_meera = client.get("/api/v1/memory/meera")
    assert res_meera.status_code == 200
    meera_mem = res_meera.json()
    assert len(meera_mem["turns"]) > 0


def test_08_cors_preflight_from_vercel_origin_succeeds():
    """8. CORS preflight from *.vercel.app origin succeeds."""
    res = client.options(
        "/api/v1/query",
        headers={
            "Origin": "https://nexus-brain-preview-git-main.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers
    assert res.headers["access-control-allow-origin"] == "https://nexus-brain-preview-git-main.vercel.app"
