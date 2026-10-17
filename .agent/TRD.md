# Technical Requirements Document (TRD): NexusBrain

## 1. System Overview
**NexusBrain** is a Graph-Native Organizational Brain and Multi-Agent Memory Coordinator built on **FalkorDB**. It unifies fragmented company silos (People, Teams, Microservices, Tickets, PRs, Slack Threads, Docs, and Architectural Decisions) into a connected, bi-temporal knowledge graph while maintaining isolated episodic/procedural memory per user session.

- **Target Hackathon Tracks:** Track 03 (Company Brain) + Track 02 (Agent Memory & Coordination)
- **Primary Database:** FalkorDB (`falkordb/falkordb:latest` via Docker on ports `6379` and `3000`)

---

## 2. Technical Stack & Hardware Constraints
- **OS:** Windows 11 | **Runtime:** Python 3.12
- **Hardware Ceiling:** 16GB System RAM, 6GB GPU VRAM (keep batch sizes memory-safe)
- **Graph Engine:** `falkordb>=1.0.8` (Python client)
- **Data Validation:** `pydantic>=2.0`
- **Agent Orchestration:** Modular OOP Agent Coordinator + LangGraph / Gemini 2.5 Flash (or OpenAI/Ollama fallback)
- **Backend API:** FastAPI + Uvicorn (`localhost:8000`)
- **Frontend UI:** Streamlit + `streamlit-agraph` (or React/Cytoscape via REST API)

---

## 3. Multigraph Topology in FalkorDB
One FalkorDB instance hosts multiple isolated graphs using `db.select_graph()`:
1. **`company_brain` (Shared Enterprise Graph):** Stores organizational entities, code/ticket provenance, and bi-temporal architectural decisions.
2. **`memory_tenant_{user_id}` (Isolated Per-User Episodic & Procedural Graph):** Stores persistent conversation turns, extracted user preferences, and learned troubleshooting playbooks (`TaskPattern -> ToolAction`).

---

## 4. Graph Schema Specification

### 4.1 Node Labels & Key Properties (`company_brain`)
- `(:Team {id, name, department, lead_id, slack_channel})`
- `(:Person {id, name, role, seniority, team_id, skills, joined_date, active})`
- `(:System {id, name, tier, language, repo_url, owner_team_id, primary_maintainer_id})`
- `(:Ticket {id, title, type, severity, status, created_at, resolved_at, reporter_id, assignee_id, affected_system_id, root_cause_system_id, summary})`
- `(:PullRequest {id, title, author_id, system_id, linked_ticket_id, merged_at, commit_summary})`
- `(:SlackThread {id, channel, started_at, linked_ticket_id, linked_decision_id, transcript})`
- `(:Document {id, title, doc_type, author_id, system_id, last_updated, status, content})`
- `(:Decision {id, title, topic, status, decided_at, invalidated_at, author_id, system_id, source_slack_id, source_ticket_id, rationale})`

### 4.2 Node Labels (`memory_tenant_{user_id}`)
- `(:Session {id, user_id, started_at})`
- `(:Turn {id, session_id, role, content, timestamp, referenced_node_ids})`
- `(:Playbook {id, trigger_signature, resolution_steps, verified_by_ticket_id, success_count})`

### 4.3 Directed Edge Relationships
- **Organizational & Ownership:** `(:Person)-[:MEMBER_OF]->(:Team)`, `(:Team)-[:OWNS]->(:System)`, `(:Person)-[:MAINTAINS]->(:System)`
- **System Topology:** `(:System)-[:DEPENDS_ON {criticality}]->(:System)`
- **Operational Provenance:** `(:Ticket)-[:AFFECTS]->(:System)`, `(:Ticket)-[:CAUSED_BY]->(:System)`, `(:Person)-[:RESOLVED]->(:Ticket)`, `(:PullRequest)-[:IMPLEMENTS]->(:Decision)`, `(:PullRequest)-[:MODIFIES]->(:System)`, `(:Person)-[:AUTHORED]->(:PullRequest)`
- **Temporal Knowledge Evolution:** `(:Decision)-[:SUPERSEDES {reason, timestamp}]->(:Decision)`, `(:Decision)-[:DECIDED_IN]->(:SlackThread)`, `(:Decision)-[:TRIGGERED_BY]->(:Ticket)`, `(:Document)-[:GUIDES_RESOLUTION_OF]->(:Ticket)`
- **Agent Memory Handoffs:** `(:Session)-[:HAS_TURN]->(:Turn)`, `(:Turn)-[:EXTRACTED_FACT]->(:Decision)`, `(:Playbook)-[:APPLIES_TO]->(:System)`

---

## 5. Multi-Agent Architecture & Deterministic Graph Tools

Agents must never run unvalidated raw LLM Cypher strings. They invoke 5 deterministic OOP methods in `src/graph/tools.py`:

1. **`find_shadow_expert(system_name: str)`:** Traverses `(:Person)-[:AUTHORED|RESOLVED]->(:PullRequest|:Ticket)-[:MODIFIES|:AFFECTS]->(:System)` weighted by recency and severity to identify both official owners and actual high-activity subject-matter experts.
2. **`trace_decision_lineage(topic_or_system: str)`:** Follows `(:Decision {status: 'active'})-[:SUPERSEDES*0..5]->(:Decision)` along with linked `(:SlackThread)` and `(:Ticket)` nodes to explain *what* is current, *what* is outdated, and *why* it changed.
3. **`calculate_blast_radius(system_name: str)`:** Executes `MATCH p = (s:System {name: $name})<-[:DEPENDS_ON*1..4]-(downstream:System)<-[:OWNS]-(t:Team) RETURN p` to compute cascading failure paths and affected team leads.
4. **`mutate_knowledge_state(event_payload: dict)`:** Temporal Scribe tool that ingests a new Slack thread/PR/Incident, marks contradicted `(:Decision)` or `(:Document)` nodes as `status = 'superseded'` (`invalidated_at = now`), and links the new active node via `[:SUPERSEDES]`.
5. **`sync_agent_memory(user_id: str, turn_data: dict)`:** Reads/writes episodic history and procedural playbooks from/to `memory_tenant_{user_id}`.

---

## 6. Strict API Contract (Backend <-> Frontend Handshake)
All agent queries (`POST /api/v1/query`) MUST return this exact JSON schema:

```json
{
  "answer": "Markdown-formatted answer with inline [ID] citations.",
  "tenant_graph": "memory_tenant_sre_lead",
  "agent_trace": [
    {
      "agent": "RouterAgent | GraphNavigator | MemoryScribe",
      "tool": "trace_decision_lineage",
      "cypher_executed": "MATCH p = (d:Decision)...",
      "latency_ms": 3.8
    }
  ],
  "citations": [
    {
      "id": "ADR-042",
      "label": "Decision",
      "title": "Adopt gRPC Streaming",
      "status": "active",
      "source_ref": "SLACK-088"
    }
  ],
  "subgraph": {
    "nodes": [
      {"id": "ADR-042", "label": "Adopt gRPC", "type": "Decision", "status": "active"}
    ],
    "edges": [
      {"source": "ADR-042", "target": "ADR-019", "relationship": "SUPERSEDES"}
    ]
  }
}