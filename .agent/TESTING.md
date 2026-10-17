# Testing & Verification Protocol (TESTING.md): NexusBrain

Every phase must pass its corresponding verification gate before marking tasks complete in `IMPLEMENTATION_PLAN.md`. Run tests via `pytest tests/ -v`.

---

## Gate 1: Synthetic Dataset Integrity (`tests/test_01_dataset.py`)
1. **File Existence:** Verify `teams.json`, `people.json`, `systems.json`, `tickets.json`, `pull_requests.json`, `slack_threads.json`, `documents.json`, and `decisions.json` exist in `data/raw/`.
2. **Scale Threshold:** Total nodes $\ge 1000$, total edges $\ge 3000$.
3. **Referential Integrity:** Every `source_id` and `target_id` in edges must exist in the node dictionary (zero dangling pointers).
4. **Golden Scenario Presence:** Assert the exact IDs for all 5 Golden Scenarios exist in `data/raw/`.

---

## Gate 2: FalkorDB Graph & Cypher Tool Verification (`tests/test_02_falkordb.py`)
1. **Connection & Multigraph Isolation:**
   - Connect to `localhost:6379`.
   - Verify `company_brain` graph has $\ge 1000$ nodes (`MATCH (n) RETURN count(n)`).
   - Verify creating a node in `memory_tenant_test_a` does NOT appear in `memory_tenant_test_b`.
2. **Latency Benchmark:**
   - All 5 deterministic Cypher tool queries must execute in `< 50ms` locally.

---

## Gate 3: The 5 Golden Demo Scenario Assertions (`tests/test_03_golden_scenarios.py`)
1. **Scenario 1 (Shadow Expert):** Calling `find_shadow_expert("auth-service")` must return `Person_04` as `official_owner` AND `Person_19` as `top_contributor` with $\ge 15$ resolved tickets/PRs.
2. **Scenario 2 (Temporal Decision Lineage):** Calling `trace_decision_lineage("auth-service")` must return an active `Decision` node linked via `[:SUPERSEDES]` to at least one `superseded` `Decision` node, plus its source `SlackThread` and `Ticket`.
3. **Scenario 3 (4-Hop Blast Radius):** Calling `calculate_blast_radius("redis-session-store")` must return a dependency path of length $\ge 3$ affecting at least 3 distinct downstream `System` nodes and their owning `Team` nodes.
4. **Scenario 4 (Live Mutation Round-Trip):**
   - Query current active decision for `auth-service` (`ADR-051`).
   - Call `mutate_knowledge_state()` with new decision `ADR-099` superseding `ADR-051`.
   - Re-query `trace_decision_lineage("auth-service")` and assert `ADR-099` is `active` and `ADR-051` is now `superseded` with a non-null `invalidated_at` timestamp.
5. **Scenario 5 (API Contract Validation):** Calling `AgentCoordinator.handle_query()` must validate cleanly against the Pydantic response model (`answer`, `tenant_graph`, `agent_trace`, `citations`, `subgraph.nodes`, `subgraph.edges`).