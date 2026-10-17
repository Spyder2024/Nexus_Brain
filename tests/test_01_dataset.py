"""Gate 1: Synthetic Dataset Integrity Test Suite.

Verifies:
1. File existence for all 8 raw JSON files, edges.json, and graph_bundle.json.
2. Scale threshold: Total nodes >= 1000, total edges >= 3000.
3. Referential integrity: Every source_id and target_id in edges exists in the node dictionary (zero dangling pointers).
4. Golden Scenario presence: Asserts exact IDs and relationships for all 5 Golden Scenarios.
5. Pydantic validation: Asserts that all loaded entities validate cleanly against their Pydantic v2 schemas.
"""

import json
from pathlib import Path
from typing import Dict, List, Set
import pytest

from src.config import DATA_RAW_DIR
from src.schema.models import (
    Decision,
    Document,
    GraphBundle,
    GraphEdge,
    Person,
    PullRequest,
    SlackThread,
    System,
    Team,
    Ticket,
)


@pytest.fixture(scope="module")
def raw_data_dir() -> Path:
    """Fixture providing raw data directory."""
    assert DATA_RAW_DIR.exists(), f"Raw data directory does not exist: {DATA_RAW_DIR}"
    return DATA_RAW_DIR


@pytest.fixture(scope="module")
def loaded_raw_files(raw_data_dir: Path) -> Dict[str, List[dict]]:
    """Loads all 8 raw entity files and edges into memory."""
    filenames = [
        "teams.json",
        "people.json",
        "systems.json",
        "tickets.json",
        "pull_requests.json",
        "slack_threads.json",
        "documents.json",
        "decisions.json",
        "edges.json",
    ]
    data = {}
    for fname in filenames:
        fpath = raw_data_dir / fname
        assert fpath.exists(), f"Required dataset file missing: {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            data[fname] = json.load(f)
    return data


# -----------------------------------------------------------------------------
# Check 1: File Existence
# -----------------------------------------------------------------------------
def test_raw_files_existence(raw_data_dir: Path):
    """Verify teams.json, people.json, systems.json, tickets.json, pull_requests.json,
    slack_threads.json, documents.json, decisions.json, edges.json, and graph_bundle.json exist."""
    required_files = [
        "teams.json",
        "people.json",
        "systems.json",
        "tickets.json",
        "pull_requests.json",
        "slack_threads.json",
        "documents.json",
        "decisions.json",
        "edges.json",
        "graph_bundle.json",
    ]
    for filename in required_files:
        p = raw_data_dir / filename
        assert p.is_file(), f"File {filename} is missing in {raw_data_dir}"
        assert p.stat().st_size > 0, f"File {filename} is empty"


# -----------------------------------------------------------------------------
# Check 2: Scale Thresholds
# -----------------------------------------------------------------------------
def test_dataset_scale_thresholds(loaded_raw_files: Dict[str, List[dict]]):
    """Assert total nodes >= 1000 and total edges >= 3000."""
    node_files = [
        "teams.json",
        "people.json",
        "systems.json",
        "tickets.json",
        "pull_requests.json",
        "slack_threads.json",
        "documents.json",
        "decisions.json",
    ]
    total_nodes = sum(len(loaded_raw_files[f]) for f in node_files)
    total_edges = len(loaded_raw_files["edges.json"])

    assert total_nodes >= 1000, f"Expected total nodes >= 1000, got {total_nodes}"
    assert total_edges >= 3000, f"Expected total edges >= 3000, got {total_edges}"
    assert total_nodes == 1077, f"Expected exactly 1077 generated nodes, got {total_nodes}"
    assert total_edges == 4103, f"Expected exactly 4103 generated edges, got {total_edges}"


# -----------------------------------------------------------------------------
# Check 3: Referential Integrity (Zero Dangling Pointers)
# -----------------------------------------------------------------------------
def test_referential_integrity(loaded_raw_files: Dict[str, List[dict]]):
    """Assert every source_id and target_id in edges exists in the node dictionary."""
    node_files = [
        "teams.json",
        "people.json",
        "systems.json",
        "tickets.json",
        "pull_requests.json",
        "slack_threads.json",
        "documents.json",
        "decisions.json",
    ]
    all_node_ids: Set[str] = set()
    for f in node_files:
        for node in loaded_raw_files[f]:
            assert "id" in node, f"Node missing 'id' field in {f}"
            assert node["id"] not in all_node_ids, f"Duplicate node ID found: {node['id']}"
            all_node_ids.add(node["id"])

    edges = loaded_raw_files["edges.json"]
    dangling_sources = []
    dangling_targets = []

    for edge in edges:
        s_id = edge["source_id"]
        t_id = edge["target_id"]
        if s_id not in all_node_ids:
            dangling_sources.append(s_id)
        if t_id not in all_node_ids:
            dangling_targets.append(t_id)

    assert len(dangling_sources) == 0, f"Found dangling edge sources: {dangling_sources[:5]}"
    assert len(dangling_targets) == 0, f"Found dangling edge targets: {dangling_targets[:5]}"


# -----------------------------------------------------------------------------
# Check 4: Golden Scenario Presence Assertions
# -----------------------------------------------------------------------------
def test_golden_scenario_1_shadow_ownership(loaded_raw_files: Dict[str, List[dict]]):
    """Scenario 1: Elena Rostova (person-19, SRE) resolved >= 18 SEV-1s and authored >= 25 PRs on auth-service."""
    tickets = loaded_raw_files["tickets.json"]
    prs = loaded_raw_files["pull_requests.json"]
    systems = loaded_raw_files["systems.json"]

    auth_service = next((s for s in systems if s["id"] == "auth-service"), None)
    assert auth_service is not None, "auth-service missing"
    assert auth_service["primary_maintainer_id"] == "person-04", "Official maintainer must be person-04"

    p19_auth_sev1_tickets = [
        t for t in tickets
        if t["assignee_id"] == "person-19"
        and t["affected_system_id"] == "auth-service"
        and t["severity"] == "SEV-1"
        and t["status"] == "resolved"
    ]
    p19_auth_prs = [
        pr for pr in prs
        if pr["author_id"] == "person-19" and pr["system_id"] == "auth-service"
    ]

    assert len(p19_auth_sev1_tickets) >= 18, f"Expected >= 18 SEV-1s for person-19 on auth-service, got {len(p19_auth_sev1_tickets)}"
    assert len(p19_auth_prs) >= 25, f"Expected >= 25 PRs for person-19 on auth-service, got {len(p19_auth_prs)}"


def test_golden_scenario_2_temporal_decision_flip(loaded_raw_files: Dict[str, List[dict]]):
    """Scenario 2: ADR-051 supersedes ADR-018, contradicted by outdated DOC-082, discussed in SLACK-088 after INC-204."""
    decisions = {d["id"]: d for d in loaded_raw_files["decisions.json"]}
    documents = {d["id"]: d for d in loaded_raw_files["documents.json"]}
    threads = {t["id"]: t for t in loaded_raw_files["slack_threads.json"]}
    tickets = {t["id"]: t for t in loaded_raw_files["tickets.json"]}
    edges = loaded_raw_files["edges.json"]

    assert "ADR-051" in decisions, "ADR-051 must exist"
    assert "ADR-018" in decisions, "ADR-018 must exist"
    assert "DOC-082" in documents, "DOC-082 must exist"
    assert "SLACK-088" in threads, "SLACK-088 must exist"
    assert "INC-204" in tickets, "INC-204 must exist"

    # Status assertions
    assert decisions["ADR-051"]["status"] == "active"
    assert decisions["ADR-018"]["status"] == "superseded"
    assert documents["DOC-082"]["status"] == "outdated"
    assert threads["SLACK-088"]["transcript"] is not None and len(threads["SLACK-088"]["transcript"]) > 0

    # Edge assertions
    has_supersedes = any(
        e["source_id"] == "ADR-051" and e["target_id"] == "ADR-018" and e["relation_type"] == "SUPERSEDES"
        for e in edges
    )
    has_contradicts = any(
        e["source_id"] == "DOC-082" and e["target_id"] == "ADR-051" and e["relation_type"] == "CONTRADICTS"
        for e in edges
    )
    has_triggered_ticket = any(
        e["source_id"] == "INC-204" and e["target_id"] == "ADR-051" and e["relation_type"] == "TRIGGERED_DECISION"
        for e in edges
    )
    has_triggered_slack = any(
        e["source_id"] == "SLACK-088" and e["target_id"] == "ADR-051" and e["relation_type"] == "TRIGGERED_DECISION"
        for e in edges
    )

    assert has_supersedes, "ADR-051 must have SUPERSEDES edge to ADR-018"
    assert has_contradicts, "DOC-082 must have CONTRADICTS edge to ADR-051"
    assert has_triggered_ticket, "INC-204 must have TRIGGERED_DECISION edge to ADR-051"
    assert has_triggered_slack, "SLACK-088 must have TRIGGERED_DECISION edge to ADR-051"


def test_golden_scenario_3_cascading_blast_radius(loaded_raw_files: Dict[str, List[dict]]):
    """Scenario 3: 4-hop chain: stripe-webhook-worker -> checkout-orchestrator -> auth-token-validator -> redis-session-store,
    with catalyst incident INC-119."""
    edges = loaded_raw_files["edges.json"]
    tickets = {t["id"]: t for t in loaded_raw_files["tickets.json"]}

    depends_on = {(e["source_id"], e["target_id"]) for e in edges if e["relation_type"] == "DEPENDS_ON"}

    assert ("stripe-webhook-worker", "checkout-orchestrator") in depends_on
    assert ("checkout-orchestrator", "auth-token-validator") in depends_on
    assert ("auth-token-validator", "redis-session-store") in depends_on

    assert "INC-119" in tickets
    inc_119 = tickets["INC-119"]
    assert inc_119["affected_system_id"] == "stripe-webhook-worker"
    assert inc_119["root_cause_system_id"] == "redis-session-store"


def test_golden_scenario_4_cross_agent_memory(loaded_raw_files: Dict[str, List[dict]]):
    """Scenario 4: Runbook DOC-012 links to both historical INC-045 and active recurrence INC-249."""
    edges = loaded_raw_files["edges.json"]
    documents = {d["id"]: d for d in loaded_raw_files["documents.json"]}
    tickets = {t["id"]: t for t in loaded_raw_files["tickets.json"]}

    assert "DOC-012" in documents
    assert "INC-045" in tickets
    assert "INC-249" in tickets

    guides = {(e["source_id"], e["target_id"]) for e in edges if e["relation_type"] == "GUIDES_RESOLUTION_OF"}
    assert ("DOC-012", "INC-045") in guides, "DOC-012 must guide resolution of INC-045"
    assert ("DOC-012", "INC-249") in guides, "DOC-012 must guide resolution of INC-249"


def test_golden_scenario_5_breaking_change(loaded_raw_files: Dict[str, List[dict]]):
    """Scenario 5: PR-398 modified user-profile-service causing unmarshaling crash INC-250 on recommendation-service."""
    prs = {p["id"]: p for p in loaded_raw_files["pull_requests.json"]}
    tickets = {t["id"]: t for t in loaded_raw_files["tickets.json"]}
    systems = {s["id"]: s for s in loaded_raw_files["systems.json"]}

    assert "PR-398" in prs
    assert "INC-250" in tickets
    assert "recommendation-service" in systems
    assert "user-profile-service" in systems

    pr_398 = prs["PR-398"]
    assert pr_398["system_id"] == "user-profile-service"

    inc_250 = tickets["INC-250"]
    assert inc_250["affected_system_id"] == "recommendation-service"
    assert inc_250["root_cause_system_id"] == "user-profile-service"


# -----------------------------------------------------------------------------
# Check 5: Pydantic v2 Schema Validation
# -----------------------------------------------------------------------------
def test_pydantic_v2_schema_validation(loaded_raw_files: Dict[str, List[dict]], raw_data_dir: Path):
    """Validate that every entity in raw files conforms strictly to Pydantic v2 models."""
    for item in loaded_raw_files["teams.json"]:
        Team.model_validate(item)

    for item in loaded_raw_files["people.json"]:
        Person.model_validate(item)

    for item in loaded_raw_files["systems.json"]:
        System.model_validate(item)

    for item in loaded_raw_files["tickets.json"]:
        Ticket.model_validate(item)

    for item in loaded_raw_files["pull_requests.json"]:
        PullRequest.model_validate(item)

    for item in loaded_raw_files["slack_threads.json"]:
        SlackThread.model_validate(item)

    for item in loaded_raw_files["documents.json"]:
        Document.model_validate(item)

    for item in loaded_raw_files["decisions.json"]:
        Decision.model_validate(item)

    for item in loaded_raw_files["edges.json"]:
        GraphEdge.model_validate(item)

    # Validate unified bundle
    with open(raw_data_dir / "graph_bundle.json", "r", encoding="utf-8") as f:
        bundle_data = json.load(f)
    bundle = GraphBundle.model_validate(bundle_data)
    assert len(bundle.teams) == 8
    assert len(bundle.people) == 65
    assert len(bundle.systems) == 24
    assert len(bundle.tickets) == 250
    assert len(bundle.pull_requests) == 400
    assert len(bundle.slack_threads) == 180
    assert len(bundle.documents) == 90
    assert len(bundle.decisions) == 60
    assert len(bundle.edges) == 4103
