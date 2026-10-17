# Handoff to Dev A (Dev B Contract Alignment)

*Created per `DEV_B_SPEC_v2.md` Section 2.*

## 1. Resolved Contract Alignments
1. **Tenant Multigraph ID Convention:**
   - Standardized to `memory_tenant_{user_id}` where `user_id` is one of: `meera`, `kabir`, `riya`.
   - Examples: `memory_tenant_meera`, `memory_tenant_kabir`, `memory_tenant_riya`.
2. **Scenario #1 Subject-Matter Expert:**
   - Confirmed as **Kavya (`person-19`)** (Staff SRE, 18 SEV-1s resolved, 26 PRs authored).
   - `person-04` (Devon Vance) is the official lead for `team-auth`.
   - Meera is the SRE Lead persona querying the system, not the shadow expert.
3. **ADR-019 Provenance:**
   - `source_ref` is `INC-204` (the deadlock outage) and discussed in `SLACK-088`.

## 2. API Endpoints Contract Implemented by Dev B
- `GET  /api/v1/health` -> `{"status":"awake", "falkordb_connected": bool, "seeded": bool, "mode": "live"|"mock", "timestamp": str}`
- `GET  /api/v1/stats?user_id=meera` -> `{"mode": str, "nodes": int, "edges": int, "graphs": list[str], "active_tenant_graph": str, "avg_query_ms": float}`
- `POST /api/v1/query` -> `AgentQueryResponse` strictly matching TRD.md Section 6.
- `POST /api/v1/mutate` -> Expects `{user_id, source_type, channel, system_name, new_decision_title, supersedes_decision_id, rationale}`. Server automatically increments next free ADR ID (e.g. `ADR-061`). Returns `{"new_decision": {...}, "superseded_decision": {...}, "subgraph": {...}, "latency_ms": float, "cypher_executed": str}`. Returns 409 Conflict if target ADR is not active.
- `GET  /api/v1/memory/{user_id}` -> `{"tenant_graph": str, "turns": list, "playbooks": list, "shared_playbooks": list}`.
- `POST /api/v1/reset` -> Idempotent re-seed of Golden Scenarios. Supports optional `X-Admin-Token` header if `ADMIN_TOKEN` is configured.

## 3. Requested Dev A Additions (Non-blocking)
- **`list_turns(user_id: str)` & `list_playbooks(user_id: str)`:**
  `LiveBackend` will call these when reading `/api/v1/memory/{user_id}`.
  While awaiting direct methods in `GraphTools` / `MemoryScribe`, `LiveBackend` queries the multigraph via Cypher directly or falls back to stored session turns.
