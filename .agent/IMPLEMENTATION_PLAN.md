# Implementation Plan (IMPLEMENTATION_PLAN.md): NexusBrain

## Team Allocation (2-Person Parallel Architecture)
- **Developer A (Graph & Multi-Agent Architect):** Owns `src/schema/`, `src/data_gen/`, `src/graph/`, `src/agents/`.
- **Developer B (UI, API & Pitch Lead):** Owns `src/api/`, `src/ui/`, `README.md`, Demo Video & Blog Post.

---

## Phase 1: Project Scaffolding & Synthetic Enterprise Dataset (Dev A)
- [x] **1.1:** Create directory structure (`data/raw`, `src/schema`, `src/data_gen`, `src/graph`, `src/agents`, `src/api`, `src/ui`, `tests`).
- [x] **1.2:** Implement Pydantic v2 schemas in `src/schema/models.py` matching `TRD.md` Section 4.
- [x] **1.3:** Implement `EnterpriseDataGenerator(seed=42)` in `src/data_gen/company_generator.py` generating ~1,200+ nodes and ~4,000+ edges with all 5 planted Golden Demo Scenarios.
- [x] **1.4:** Export generated datasets to `data/raw/*.json` and verify counts.

## Phase 2: FalkorDB Ingestion & Deterministic Cypher Engine (Dev A)
- [x] **2.1:** Configure `docker-compose.yml` for `falkordb/falkordb:latest` (ports `6379` and `3000`).
- [x] **2.2:** Build `FalkorDBLoader` (`src/graph/loader.py`) using `UNWIND` batch Cypher queries for sub-second ingestion into `company_brain` and index creation on `id`, `name`, and `status`.
- [x] **2.3:** Build `GraphTools` (`src/graph/tools.py`) implementing the 5 deterministic Cypher methods (`find_shadow_expert`, `trace_decision_lineage`, `calculate_blast_radius`, `mutate_knowledge_state`, `sync_agent_memory`).

## Phase 3: Multi-Agent Coordinator & Tenant Memory (Dev A)
- [ ] **3.1:** Implement `AgentCoordinator` (`src/agents/coordinator.py`) orchestrating `RouterAgent`, `GraphNavigator`, and `MemoryScribe`.
- [ ] **3.2:** Ensure `AgentCoordinator.handle_query(user_id, query)` returns the exact JSON contract defined in `TRD.md` Section 6 (with deterministic fallback if LLM API key is rate-limited).

## Phase 4: FastAPI Backend & Mock Contract Bridge (Dev B)
- [ ] **4.1:** Build `src/api/server.py` with endpoints:
  - `POST /api/v1/query` (calls `AgentCoordinator.handle_query`)
  - `POST /api/v1/mutate` (calls `GraphTools.mutate_knowledge_state`)
  - `GET /api/v1/stats` (returns live FalkorDB node/edge counts and tenant graphs)
  - `POST /api/v1/reset` (re-seeds Golden Scenarios for clean demo takes)

## Phase 5: Split-Screen Visual Command Center UI (Dev B)
- [ ] **5.1:** Build `src/ui/app.py` implementing the 3-zone layout defined in `APP_FLOW.md`.
- [ ] **5.2:** Wire the 5 One-Click Golden Scenario Preset Buttons and Citation Badges (`active` vs `superseded`).
- [ ] **5.3:** Integrate interactive graph visualization (`streamlit-agraph` / PyVis) color-coded by node type and status.
- [ ] **5.4:** Build Tab 2 (Live Knowledge Mutator) and Tab 3 (Multi-Tenant Memory Inspector).

## Phase 6: Verification, README & Submission Polish (Dev A + Dev B)
- [ ] **6.1:** Run full test suite in `.agent/TESTING.md`.
- [ ] **6.2:** Finalize `README.md` with architecture diagram, Cypher query showcase, and 1-command local setup guide.